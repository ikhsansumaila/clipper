import os
import requests

def send_notification(message):
    BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
    CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID")

    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
    headers = {
        "Authorization": f"Bot {BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "content": message
    }

    try:
        # Mengirim HTTP POST request dengan timeout 10 detik
        response = requests.post(url, headers=headers, json=payload, timeout=10)

        # Memicu HTTPError jika status code 4xx (Client Error) atau 5xx (Server Error)
        response.raise_for_status()

        # Jika berhasil (status code 200/201)
        print("✅ Pesan berhasil terkirim!")
        print("Detail Response:", response.json())

    except requests.exceptions.HTTPError as err:
        print(f"❌ Error HTTP ({response.status_code}): {err}")
        # Menampilkan pesan error spesifik dari API Discord jika ada
        try:
            print("Detail Error dari Discord:", response.json())
        except Exception:
            print("Response Text:", response.text)

    except requests.exceptions.ConnectionError:
        print("❌ Error Koneksi: Gagal terhubung ke server Discord (Cek koneksi internet).")

    except requests.exceptions.Timeout:
        print("❌ Error Timeout: Request melebihi batas waktu penantian.")

    except requests.exceptions.RequestException as err:
        print(f"❌ Terjadi kesalahan request lainnya: {err}")

    except Exception as err:
        print(f"❌ Terjadi kesalahan tak terduga: {err}")

if __name__ == "__main__":
    send_notification("Halo, ini adalah pesan dari server")