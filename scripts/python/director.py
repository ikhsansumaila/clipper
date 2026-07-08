import json
import os
import subprocess
import sys
from checkpoint_manager import CheckpointManager

API_KEY = os.getenv("MIHAKIDS_AI_API_KEY", "")
API_ENDPOINT = "http://localhost:20128/v1/chat/completions"
AI_MODEL_NAME = "mihan-high-providers"
# TXT_PATH = "/home/ubuntu/clipper/output/temp/transcript.txt"
JSON_PATH = "/home/ubuntu/clipper/output/temp/director-cut.json"


def director():
    cm = CheckpointManager()
    state = cm.get_state()
    
    # Ambil lokasi file transkrip dari tahapan sebelumnya
    transcript_path = state["paths"].get("transcript")

    # 1. Membaca transkrip
    print("Membaca transkrip dan menghubungi mihankids AI...")
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    prompt = f"""
    data Transkrip:
    {transcript}

    Anda adalah produser video Shorts dan TikTok profesional yang ahli dalam mencari momen viral dari sebuah percakapan.
    1. Analisis transkrip tersebut dan cari 1 momen atau kutipan yang paling menarik, emosional, kontroversial, atau memiliki potensi viral paling tinggi.
    2. Batasi durasi potongan video antara 30 hingga 59 detik.
    3. Berikan judul potongan video yang menarik dan relevan dengan momen tersebut.
    3. Wajib balas HANYA dengan format JSON murni tanpa markdown, Berikut adalah contoh struktur data transkrip beserta timestamp detiknya:
    {{"start": 12.5, "end": 45.0, "reason": "Karena bagian ini lucunya natural", "title": "Momen Lucu yang Bikin Ngakak"}}
    """

    # 2. Menyiapkan payload JSON
    payload = {
        "model": AI_MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "stream": False,
    }

    # 3. Menjalankan curl via subprocess
    print(f"Menghubungi mihankids AI via curl...")
    curl_cmd = [
        "curl", "-s", API_ENDPOINT,
        "-H", f"Authorization: Bearer {API_KEY}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload)
    ]

    result = subprocess.run(curl_cmd, capture_output=True, text=True)

    # 4. Parsing respon
    response_data = json.loads(result.stdout)
    content = response_data['choices'][0]['message']['content']
    # Membersihkan markdown jika ada
    clean_json = content.replace('```json', '').replace('```', '').strip()

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        f.write(clean_json)

    print("✅ Sukses! Hasil disimpan ke director-cut.json")

    # Mengubah teks JSON bersih menjadi dictionary Python
    ai_result = json.loads(clean_json)

    # (Opsional tapi sangat disarankan) 
    # Menambahkan lokasi file director-cut.json ke dalam Checkpoint paths
    ai_result["paths"] = {
        "director_cut": JSON_PATH
    }

    # Return hasil analisis AI agar otomatis masuk ke Checkpoint JSON
    return ai_result


if __name__ == "__main__":
    try:
        cm = CheckpointManager()
        cm.run_stage(CheckpointManager.STAGE_DIRECTOR_ANALYSIS, director)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)