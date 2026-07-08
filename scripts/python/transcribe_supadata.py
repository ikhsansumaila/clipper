import json
import os
import sys
import time
import requests
from checkpoint_manager import CheckpointManager

# ==========================================
# KONFIGURASI & PATHS
# ==========================================
API_KEY = os.getenv("SUPADATA_API_KEY", "")
BASE_URL = "https://api.supadata.ai/v1"
TXT_PATH = "/home/ubuntu/clipper/output/temp/transcript.txt"
URL_FILE_PATH = "/home/ubuntu/clipper/output/temp/video_url.txt"


def transcribe_supadata():
    """Fungsi utama untuk mengambil transkrip dari Supadata."""
    
    # Proteksi API Key
    if not API_KEY:
        raise ValueError("SUPADATA_API_KEY tidak ditemukan di environment variables!")

    # 1. Ambil URL langsung dari Checkpoint Manager
    cm = CheckpointManager()
    state = cm.get_state()
    video_url = state.get("url")

    if not video_url:
        raise ValueError("URL video tidak ditemukan di file Checkpoint (state.json).")

    # 2. Persiapan request ke API
    os.makedirs(os.path.dirname(TXT_PATH), exist_ok=True)
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    params = {
        "url": video_url,
        "text": "false",
        "lang": "id"
    }

    print(f"🚀 Meminta transkrip langsung (sync) dari Supadata untuk: {video_url}")

    response = requests.get(f"{BASE_URL}/transcript", headers=headers, params=params)

    # DEBUG: tampilkan hasil mentah dari request Supadata
    # print("========== DEBUG SUPADATA RESPONSE ==========")
    # print(f"Status Code: {response.status_code}")
    # print(f"Response Text: {response.text}")
    # print("=============================================")

    response.raise_for_status()
    result_data = response.json()

    if "jobId" in result_data:
        job_id = result_data["jobId"]
        print(f"🔄 Mendapatkan jobId: {job_id}, memulai polling...")
        
        max_retries = 60
        for i in range(max_retries):
            poll_response = requests.get(f"{BASE_URL}/transcript/{job_id}", headers={"x-api-key": API_KEY})
            poll_response.raise_for_status()
            poll_data = poll_response.json()
            
            status = poll_data.get("status")
            if status == "completed":
                print("✅ Transkrip selesai diproses!")
                result_data = poll_data
                break
            elif status == "failed":
                raise ValueError(f"Transkrip gagal diproses oleh Supadata. Hasil: {poll_data}")
            else:
                print(f"⏳ Status: {status}. Menunggu 5 detik... ({i+1}/{max_retries})")
                time.sleep(5)
        else:
            raise TimeoutError("Waktu tunggu transkrip habis (timeout).")

    # DEBUG: tampilkan hasil JSON yang sudah diparse
    # print("========== DEBUG SUPADATA JSON ==========")
    # print(json.dumps(result_data, indent=2, ensure_ascii=False))
    # print("=========================================")

    # 3. Ekstrak data dari struktur JSON Supadata
    if "content" in result_data:
        content_list = result_data["content"]
    elif "result" in result_data and isinstance(result_data["result"], dict) and "content" in result_data["result"]:
        content_list = result_data["result"]["content"]
    else:
        raise ValueError(f"Struktur JSON tidak dikenali atau kosong. Hasil mentah: {result_data}")

    # 4. Simpan ke format .txt dengan timestamp
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

    # 5. Kembalikan data untuk dicatat di Checkpoint
    return {
        "provider": "supadata",
        "paths": {
            "transcript": TXT_PATH
        }
    }


if __name__ == "__main__":
    try:
        cm = CheckpointManager()

        # 1. BACA URL DARI FILE TXT (DARI n8n)
        current_url = ""
        if os.path.exists(URL_FILE_PATH):
            with open(URL_FILE_PATH, "r", encoding="utf-8") as file:
                current_url = file.read().strip()

        # 2. INISIALISASI CHECKPOINT
        # URL akan otomatis masuk ke state.json di tahap ini
        cm.initialize(url=current_url)

        # 3. UPDATE STATUS STAGE 1 (DOWNLOAD VIA n8n)
        if not cm.is_completed(CheckpointManager.STAGE_DOWNLOAD):
            print(f"[{CheckpointManager.STAGE_DOWNLOAD}] Video sudah di-download oleh n8n. Mencatat ke Checkpoint...")
            cm.update_stage(CheckpointManager.STAGE_DOWNLOAD, "completed", method="n8n_wget")
            
            # Catat juga lokasi file video asli
            cm.update_path("source_video", "/home/ubuntu/clipper/output/temp/source.mp4")

        # 4. JALANKAN PROSES TRANSKRIP
        cm.run_stage(CheckpointManager.STAGE_TRANSCRIBE, transcribe_supadata)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)