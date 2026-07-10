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
    
    Args:
        url: URL yang akan dicari
    
    Returns:
        "found" jika URL ada, "not_found" jika tidak ada
    """
    history_file = config.HISTORY_FILE
    
    # Cek apakah file ada
    if not os.path.exists(history_file):
        return "not_found"
    
    # Baca history.json dan cek kecocokan URL
    try:
        with open(history_file, "r") as f:
            history = json.load(f)
            # Cek di setiap entry apakah video_url cocok
            for entry in history:
                if entry.get("video_url") == url:
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
