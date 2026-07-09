import os
import requests


def send_notification(message):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        print("DISCORD_WEBHOOK_URL belum diset")
        return False

    payload = {"content": message}

    print("Mengirim notifikasi ke Discord...")
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
    except requests.RequestException as exc:
        print(f"Gagal request ke Discord: {exc}")
        return False

    print(f"Discord response status: {response.status_code}")

    if response.status_code == 204:
        print("Pesan berhasil dikirim!")
        return True

    print(f"Gagal mengirim pesan. Body: {response.text}")
    return False

# if __name__ == "__main__":
#     send_notification("Halo, ini adalah pesan dari server")