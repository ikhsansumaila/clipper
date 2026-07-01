import os
import sys
import requests

API_KEY = os.getenv("SUPADATA_API_KEY", "")
BASE_URL = "https://api.supadata.ai/v1"
TXT_PATH = "/home/ubuntu/clipper/output/temp/transcript.txt"
URL_FILE_PATH = "/home/ubuntu/clipper/output/temp/video_url.txt"


def transcribe_supadata():
    # 1. Membaca URL dari file video_url.txt
    with open(URL_FILE_PATH, "r", encoding="utf-8") as file:
        video_url = file.read().strip()

    if not video_url:
        raise ValueError(f"File {URL_FILE_PATH} kosong. Tidak ada URL yang bisa diproses.")

    # Proteksi: Buat folder jika belum ada (untuk output transcript.txt)
    os.makedirs(os.path.dirname(TXT_PATH), exist_ok=True)

    headers = {
        "x-api-key": API_KEY
    }
    params = {
        "url": video_url,
        "text": "false",
        "lang": "id"
    }

    print(f"🚀 Meminta transkrip langsung (sync) dari Supadata untuk: {video_url}")

    response = requests.get(f"{BASE_URL}/transcript", headers=headers, params=params)
    response.raise_for_status()
    result_data = response.json()

    # Ekstrak daftar array/list dari struktur JSON Supadata
    if "content" in result_data:
        content_list = result_data["content"]
    elif "result" in result_data and isinstance(result_data["result"], dict) and "content" in result_data["result"]:
        content_list = result_data["result"]["content"]
    else:
        raise ValueError(f"Struktur JSON tidak dikenali atau kosong. Hasil mentah: {result_data}")

    # Simpan ke File .txt
    print("✅ Data lirik berhasil diambil. Menyusun file txt...")
    with open(TXT_PATH, "w", encoding="utf-8") as f:
        for chunk in content_list:
            text = chunk.get("text", "").strip()
            offset_ms = chunk.get("offset", 0)
            duration_ms = chunk.get("duration", 0)
            start_sec = offset_ms / 1000.0
            end_sec = (offset_ms + duration_ms) / 1000.0
            f.write(f"[{start_sec:.2f} - {end_sec:.2f}] {text}\n")

    print(f"🎉 SUKSES! File transcript berhasil dibuat di: {TXT_PATH}")


if __name__ == "__main__":
    try:
        transcribe_supadata()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)