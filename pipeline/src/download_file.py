"""
download_file.py
================
Download file dari URL dan simpan ke disk.
Dirancang untuk dipanggil dari n8n via Execute Command node.

Usage:
    python3 download_file.py --url "https://example.com/video.mp4"
    python3 download_file.py --url "https://example.com/video.mp4" --output "/path/to/output.mp4"

Jika --output tidak diberikan, file akan disimpan ke config.SOURCE_VIDEO_FILE
(default: /home/ubuntu/clipper/output/temp/source.mp4).
"""

import argparse
import json
import os
import sys

import requests

import config
from checkpoint_manager import CheckpointManager


def download_file(url: str, output_path: str) -> dict:
    """
    Download file dari URL dengan streaming dan simpan ke output_path.

    Returns:
        dict dengan keys: path, size, content_type
    """
    # Pastikan direktori tujuan ada
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Hapus file lama jika ada (berjaga-jaga untuk retry dari n8n)
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"🗑️  File lama dihapus: {output_path}", file=sys.stderr)

    print(f"⬇️  Downloading: {url}", file=sys.stderr)
    print(f"📁 Output: {output_path}", file=sys.stderr)

    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "unknown")
    total_size = response.headers.get("Content-Length")
    total_size = int(total_size) if total_size else None

    downloaded = 0
    chunk_size = 8192

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    pct = (downloaded / total_size) * 100
                    print(f"\r   Progress: {downloaded}/{total_size} bytes ({pct:.1f}%)", end="", flush=True, file=sys.stderr)
                else:
                    print(f"\r   Downloaded: {downloaded} bytes", end="", flush=True, file=sys.stderr)

    print(file=sys.stderr)  # newline setelah progress

    # Validasi file berhasil ditulis
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"File gagal ditulis ke: {output_path}")

    file_size = os.path.getsize(output_path)
    if file_size == 0:
        os.remove(output_path)
        raise ValueError("File yang didownload kosong (0 bytes), menghapus file.")

    print(f"✅ Download selesai! Size: {file_size} bytes, Type: {content_type}", file=sys.stderr)

    return {
        "path": output_path,
        "size": file_size,
        "content_type": content_type,
    }


def do_download(url: str, output_path: str):
    """
    Wrapper untuk download_file yang mengembalikan format
    yang compatible dengan CheckpointManager.run_stage().
    """
    result = download_file(url, output_path)

    # Return format sesuai konvensi CheckpointManager:
    # - key "paths" akan disimpan terpisah di state.json bagian "paths"
    # - key lainnya disimpan di dalam stage data
    return {
        "paths": {
            "source_video": result["path"],
        },
        "method": "python_requests",
        "size": result["size"],
        "content_type": result["content_type"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Download file dari URL dan simpan ke disk (untuk n8n Execute Command)"
    )
    parser.add_argument(
        "--original_url",
        required=True,
        help="URL youtube asli (untuk dicatat di state.json)",
    )
    parser.add_argument(
        "--download_url",
        required=True,
        help="URL file yang akan didownload",
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Judul file yang akan didownload",
    )

    args = parser.parse_args()
    original_url = args.original_url
    download_url = args.download_url
    title = args.title
    source_dir = os.path.join(config.DATA_DIR, "source")
    output_path = f"{source_dir}/{title}.mp4"  # default

    cm = CheckpointManager()
    # Jalankan download via CheckpointManager agar stage 1_download
    # otomatis di-update di state.json (pending → in_progress → completed)
    cm.run_stage(
        config.STAGE_DOWNLOAD,
        lambda: do_download(download_url, output_path),
    )

    # Inisialisasi history.json dengan data video baru
    cm.init_history(video_title=title, video_url=original_url)

    # Print JSON result ke stdout agar n8n bisa parse
    state = cm.get_state()
    download_stage = state.get("stages", {}).get(config.STAGE_DOWNLOAD, {})
    print(json.dumps(download_stage, indent=2))


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.RequestException as e:
        print(f"❌ Network/HTTP Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
