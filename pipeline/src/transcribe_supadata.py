import json
import os
import sys
import time
import requests
import config
from checkpoint_manager import CheckpointManager

def transcribe_supadata():
    """Fungsi utama untuk mengambil transkrip dari Supadata."""
    
    # Proteksi API Key
    if not config.SUPADATA_API_KEY:
        raise ValueError("SUPADATA_API_KEY tidak ditemukan di environment variables!")

    cm = CheckpointManager()
    state = cm.get_state() or {}
    
    video_url = state.get("url")

    if not video_url:
        raise ValueError("URL video tidak ditemukan di file Checkpoint (state.json).")

    # Ambil lokasi file source video
    source_video = state.get("paths", {}).get("source_video")
    if not source_video:
        # Fallback jika tidak ada di paths, tapi idealnya harus ada
        transcript_path = config.TRANSCRIPT_FILE
    else:
        # /path/to/Video.mp4 -> /path/to/Video.txt
        base_path = os.path.splitext(source_video)[0]
        transcript_path = f"{base_path}.txt"

    # Jika transkrip sudah pernah dibuat di path tersebut (caching)
    if os.path.exists(transcript_path):
        print(f"✅ Transkrip sudah ada di: {transcript_path}. Menggunakan yang sudah ada.")
        return {
            "provider": "supadata (cached)",
            "paths": {
                "transcript": transcript_path
            }
        }

    # 2. Persiapan request ke API
    os.makedirs(os.path.dirname(transcript_path), exist_ok=True)
    headers = {"x-api-key": config.SUPADATA_API_KEY, "Content-Type": "application/json"}
    params = {
        "url": video_url,
        "text": "false",
        "lang": "id"
    }

    print(f"🚀 Meminta transkrip langsung (sync) dari Supadata untuk: {video_url}")

    response = requests.get(f"{config.SUPADATA_BASE_URL}/transcript", headers=headers, params=params)

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
            poll_response = requests.get(f"{config.SUPADATA_BASE_URL}/transcript/{job_id}", headers={"x-api-key": config.SUPADATA_API_KEY})
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
    print("✅ Data script berhasil diambil. Menyusun file txt...")
    with open(transcript_path, "w", encoding="utf-8") as f:
        for chunk in content_list:
            # Hapus karakter enter (\n dan \r) dan ganti dengan spasi
            text = chunk.get("text", "").replace("\n", " ").replace("\r", " ").strip()
            offset_ms = chunk.get("offset", 0)
            duration_ms = chunk.get("duration", 0)
            
            start_sec = offset_ms / 1000.0
            end_sec = (offset_ms + duration_ms) / 1000.0
            
            f.write(f"[{start_sec:.2f} - {end_sec:.2f}] {text}\n")

    print(f"🎉 SUKSES! File transcript berhasil dibuat di: {transcript_path}")

    # 5. Kembalikan data untuk dicatat di Checkpoint
    return {
        "provider": "supadata",
        "paths": {
            "transcript": transcript_path
        }
    }


if __name__ == "__main__":
    try:
        cm = CheckpointManager()

        # Inisialisasi/reset checkpoint sudah dilakukan di check_url_exists.py 
        # saat menghasilkan "found" atau di download_file.py saat "not_found".
        state = cm.get_state() or {}
        
        # JALANKAN PROSES TRANSKRIP
        cm.run_stage(config.STAGE_TRANSCRIBE, transcribe_supadata)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)