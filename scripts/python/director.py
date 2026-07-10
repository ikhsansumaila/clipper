import json
import os
import subprocess
import sys
import config
from checkpoint_manager import CheckpointManager

def director():
    cm = CheckpointManager()
    state = cm.get_state() or {}
    
    # Ambil lokasi file transkrip dari tahapan sebelumnya
    transcript_path = state.get("paths", {}).get("transcript")

    # 1. Membaca transkrip
    print("Membaca transkrip dan menghubungi mihankids AI...")
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    # ==================================================
    # 2. BACA HISTORY DAN SIAPKAN INSTRUKSI TAMBAHAN
    # ==================================================
    video_url = state.get("url")
    history_data = cm.get_history(video_url)
    history_clips = history_data.get("clip_data", [])
    history_prompt = ""

    if history_clips:
        history_prompt = (
            "\n\nPENTING: Berikut adalah riwayat timestamp klip yang SUDAH PERNAH DIBUAT "
            "dari video ini. Anda DILARANG KERAS memilih momen yang beririsan atau "
            "tumpang tindih dengan durasi berikut:\n"
        )
        for i, clip in enumerate(history_clips):
            # Menggunakan get() ganda untuk berjaga-jaga jika format key berubah
            start = clip.get("start", clip.get("start", 0))
            end = clip.get("end", clip.get("end", 0))
            reason = clip.get("reason", "Tidak ada keterangan")
            
            history_prompt += f"- Klip {i+1}: {start} detik hingga {end} detik (Isi: {reason})\n"
            
        print(f"📌 Mengirimkan {len(history_clips)} riwayat klip ke AI agar tidak duplikat...")

    prompt = f"""
    data Transkrip:
    {transcript}
    {history_prompt}

    Anda adalah produser video Shorts dan TikTok profesional yang ahli dalam mencari momen viral dari sebuah percakapan.
    1. Analisis transkrip tersebut dan cari 1 momen atau kutipan yang paling menarik, emosional, kontroversial, atau memiliki potensi viral paling tinggi.
    2. Jangan mencari momen yang terlalu panjang, pilihlah momen yang singkat namun impactful.
    3. Jangan potong momen dengan ending yang tidak natural, pastikan momen tersebut memiliki awal dan akhir yang jelas.
    4. Batasi durasi potongan video antara {config.MIN_CLIP_DURATION} hingga {config.MAX_CLIP_DURATION}.
    5. Berikan judul potongan video yang menarik dan relevan dengan momen tersebut.
    6. Wajib balas HANYA dengan format JSON murni tanpa markdown, Berikut adalah contoh struktur data transkrip beserta timestamp detiknya:
    {{"start": 12.5, "end": 45.0, "reason": "Karena bagian ini lucunya natural", "title": "Momen Lucu yang Bikin Ngakak"}}
    """

    # 2. Menyiapkan payload JSON
    payload = {
        "model": config.AI_MODEL_NAME,
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
        "curl", "-s", config.AI_API_ENDPOINT,
        "-H", f"Authorization: Bearer {config.AI_API_KEY}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload)
    ]

    result = subprocess.run(curl_cmd, capture_output=True, text=True)

    # 4. Parsing respon
    response_data = json.loads(result.stdout)
    content = response_data['choices'][0]['message']['content']
    # Membersihkan markdown jika ada
    clean_json = content.replace('```json', '').replace('```', '').strip()

    with open(config.DIRECTOR_CUT_FILE, "w", encoding="utf-8") as f:
        f.write(clean_json)

    print("✅ Sukses! Hasil disimpan ke director-cut.json")

    # Mengubah teks JSON bersih menjadi dictionary Python
    ai_result = json.loads(clean_json)

    # 1. SIMPAN KE HISTORY
    # Menyimpan hasil AI ke history.json (otomatis dibatasi 20 per URL)
    print(f"Mencatat klip ke dalam history...")
    cm.add_history(video_url, ai_result)

    # (Opsional tapi sangat disarankan) 
    # Menambahkan lokasi file director-cut.json ke dalam Checkpoint paths
    ai_result["paths"] = {
        "director_cut": config.DIRECTOR_CUT_FILE
    }

    # Return hasil analisis AI agar otomatis masuk ke Checkpoint JSON
    return ai_result


if __name__ == "__main__":
    try:
        cm = CheckpointManager()
        cm.run_stage(config.STAGE_DIRECTOR_ANALYSIS, director)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)