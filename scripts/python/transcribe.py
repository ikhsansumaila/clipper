from faster_whisper import WhisperModel
import os

# VIDEO_PATH = "/home/ubuntu/clipper/output/temp/video.mp4"
VIDEO_PATH = "/home/ubuntu/clipper/output/temp/audio.wav"
TXT_PATH = "/home/ubuntu/clipper/output/temp/transcript.txt"

# model = WhisperModel("base", device="cpu", compute_type="int8")
# segments, _ = model.transcribe(VIDEO_PATH, beam_size=5)


# Ganti "base" menjadi "large-v3"
model = WhisperModel("large-v3", device="cpu", compute_type="int8")

# Tambahkan argumen initial_prompt
segments, _ = model.transcribe(
    VIDEO_PATH, 
    beam_size=5, 
    language=None, # Set None agar Whisper mendeteksi bahasa otomatis
    initial_prompt="Transcribe the speech accurately, keeping the original language, including technical terms or mixed language if present."
)

with open(TXT_PATH, "w", encoding="utf-8") as f:
    for s in segments:
        f.write(f"[{s.start:.1f} - {s.end:.1f}] {s.text}\n")

print("✅ Transkripsi selesai dan disimpan ke transcript.txt")