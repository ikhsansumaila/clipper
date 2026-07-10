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
import json
import os
import sys

import config


def check_url_exists(url: str) -> str:
    """
    Mengecek apakah URL sudah ada di history.json.
    Jika ada (reclip), langsung update state.json dengan path file lama
    agar tahap selanjutnya (transcribe, director, dsb) menggunakan file yang benar.
    """
    history_file = config.HISTORY_FILE
    
    if not os.path.exists(history_file):
        return "not_found"
    
    try:
        with open(history_file, "r") as f:
            history = json.load(f)
            for entry in history:
                if entry.get("video_url") == url:
                    video_title = entry.get("video_title")
                    
                    # === FOUND! SETUP STATE UNTUK RECLIP ===
                    from checkpoint_manager import CheckpointManager
                    cm = CheckpointManager()
                    
                    source_dir = os.path.join(config.BASE_DIR, "source")
                    new_source = os.path.join(source_dir, f"{video_title}.mp4")
                    new_transcript = os.path.join(source_dir, f"{video_title}.txt")
                    
                    # Buat state.json baru khusus untuk reclip video ini
                    state = {
                        "video_id": "", 
                        "url": url,
                        "global_status": "in_progress",
                        "paths": {
                            "source_video": new_source,
                            "transcript": new_transcript
                        },
                        "stages": {
                            config.STAGE_DOWNLOAD: {"status": "completed"},
                            config.STAGE_TRANSCRIBE: {"status": "completed"},
                            config.STAGE_DIRECTOR_ANALYSIS: {"status": "pending"},
                            config.STAGE_CUT_VIDEO: {"status": "pending"},
                            config.STAGE_ADD_CAPTION: {"status": "pending"}
                        }
                    }
                    cm._write_data(state)
                    # =======================================
                    
                    return "found"
            return "not_found"
    except Exception as e:
        print(f"Error membaca history.json: {e}", file=sys.stderr)
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
    
    result = check_url_exists(args.url)
    print(result)
    
    # Return exit code 0 untuk both cases, hanya print hasil
    sys.exit(0)


if __name__ == "__main__":
    main()
