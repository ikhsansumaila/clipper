import json
import os
import subprocess

API_ENDPOINT = "http://localhost:20128/v1/chat/completions"
API_KEY = "sk-146e5da1add4eb5b-aj2sg2-3a043914"
AI_MODEL_NAME = "mihan-high-providers"
TXT_PATH = "/home/ubuntu/clipper/output/temp/transcript.txt"
JSON_PATH = "/home/ubuntu/clipper/output/temp/cut.json"

# 1. Membaca transkrip
print("Membaca transkrip dan menghubungi mihankids AI...")
with open(TXT_PATH, "r", encoding="utf-8") as f:
    transcript = f.read()

prompt = f"""
data Transkrip:
{transcript}

Anda adalah produser video Shorts dan TikTok profesional yang ahli dalam mencari momen viral dari sebuah percakapan.
1. Analisis transkrip tersebut dan cari 1 momen atau kutipan yang paling menarik, emosional, kontroversial, atau memiliki potensi viral paling tinggi.
2. Batasi durasi potongan video antara 30 hingga 59 detik.
3. Wajib balas HANYA dengan format JSON murni tanpa markdown, Berikut adalah contoh struktur data transkrip beserta timestamp detiknya:
{{"start": 12.5, "end": 45.0, "reason": "Karena bagian ini lucunya natural"}}
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
print("Menghubungi mihankids AI via curl...")
curl_cmd = [
    "curl", "-s", API_ENDPOINT,
    "-H", f"Authorization: Bearer {API_KEY}",
    "-H", "Content-Type: application/json",
    "-d", json.dumps(payload)
]

result = subprocess.run(curl_cmd, capture_output=True, text=True)

# 4. Parsing respon
try:
    response_data = json.loads(result.stdout)
    content = response_data['choices'][0]['message']['content']
    # Membersihkan markdown jika ada
    clean_json = content.replace('```json', '').replace('```', '').strip()
    
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        f.write(clean_json)
        
    print(f"✅ Sukses! Hasil disimpan ke cut.json")
except Exception as e:
    print(f"❌ Error saat curl atau parsing: {e}")
    print(f"Respon mentah: {result.stdout}")