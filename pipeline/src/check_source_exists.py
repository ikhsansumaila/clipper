"""
check_url_exists.py
==================
Mengecek apakah URL sudah pernah diproses sebelumnya.
Membaca dari file history.json dan mencari kecocokan video_url.
Dirancang untuk dipanggil dari n8n via Execute Command node.

Usage:
    python3 check_url_exists.py --url "https://example.com/video"

Output:
    Prints "found" jika URL ditemukan di history.json
    Prints "not_found" jika URL tidak ditemukan
"""

import argparse
import os
import sys
import config
from checkpoint_manager import CheckpointManager
cm = CheckpointManager()
source_dir = os.path.join(config.DATA_DIR, "source")

def get_video_title_from_history(url: str) -> str:
    """
    Mencari judul video berdasarkan URL di history.json.
    Jika ditemukan, mengembalikan judul video. Jika tidak, mengembalikan None.
    """
    history_data = cm.get_history(url)
    if history_data:
        return history_data.get("video_title")
    return None

def write_reclip_state(title: str, source_video: str):
    state = cm._read_data()
    state["paths"]["source_video"] = source_video
    state["stages"][config.STAGE_DOWNLOAD]["status"] = "completed"
    state["stages"][config.STAGE_DOWNLOAD]["method"] = "cached"
    
    transcript = os.path.join(source_dir, f"{title}.txt")
    if os.path.exists(transcript):
        state["paths"]["transcript"] = transcript
        state["stages"][config.STAGE_TRANSCRIBE]["status"] = "completed"
        state["stages"][config.STAGE_TRANSCRIBE]["method"] = "cached"

    cm._write_data(state)

def check_source_exists(url: str) -> str:
    """
    Mengecek apakah file video/transkrip sudah ada di folder data/source berdasarkan title.
    Jika file ditemukan, update state.json agar pipeline melanjutkan dari tahapan yang sesuai.
    """

    try:
        cm.initialize(url=url)
        if not os.path.exists(source_dir):
            os.makedirs(source_dir, exist_ok=True)
        
        title = get_video_title_from_history(url)
        if not title:
            print(f"URL tidak ditemukan di history.json: {url}", file=sys.stderr)
            return "not_found"

        source_video= os.path.join(source_dir, f"{title}.mp4")
        if os.path.exists(source_video):
            write_reclip_state(title, source_video)
            return "found"
        else:
            print(f"File video tidak ditemukan di: {source_video}", file=sys.stderr)
            return "not_found"
    except Exception as e:
        print(f"Error membaca source data: {e}", file=sys.stderr)
        return "not_found"


def main():
    parser = argparse.ArgumentParser(
        description="Mengecek apakah URL sudah pernah diproses"
    )
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="URL yang akan dicari"
    )

    args = parser.parse_args()
    
    result = check_source_exists(args.url)
    print(result)
    
    # Return exit code 0 untuk both cases, hanya print hasil
    sys.exit(0)


if __name__ == "__main__":
    main()
