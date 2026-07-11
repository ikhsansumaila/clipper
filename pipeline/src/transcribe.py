from faster_whisper import WhisperModel

import os
import sys

# Batasi thread agar tidak rakus RAM
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

def transcribe_video():
    VIDEO_PATH = "/home/ubuntu/clipper/output/temp/source.mp4"
    # VIDEO_PATH = "/home/ubuntu/clipper/output/temp/audio.wav"
    TXT_PATH = "/home/ubuntu/clipper/output/temp/transcript.txt"

    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(VIDEO_PATH, beam_size=5)

    with open(TXT_PATH, "w", encoding="utf-8") as f:
        for s in segments:
            f.write(f"[{s.start:.1f} - {s.end:.1f}] {s.text}\n")

    print("✅ Transkripsi selesai dan disimpan ke transcript.txt")


def main():
    try:
        print("Sedang transkripsi...")
        transcribe_video()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # PENTING: Ini akan membersihkan memori saat skrip selesai, 
        # sukses maupun gagal.
        print("Membersihkan memori...")
        sys.exit(0) 

if __name__ == "__main__":
    main()
