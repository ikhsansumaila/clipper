import json
import os
import subprocess
import sys
from checkpoint_manager import CheckpointManager

# VIDEO_PATH = "/home/ubuntu/clipper/output/temp/source.mp4"
FINAL_CUT_PATH = "/home/ubuntu/clipper/output/temp/final-cut.mp4"
# JSON_PATH = "/home/ubuntu/clipper/output/temp/director-cut.json"


def cut_video():
    cm = CheckpointManager()
    state = cm.get_state()

    # 1. AMBIL DATA DARI TAHAP SEBELUMNYA
    # Ambil lokasi file video asli yang dicatat di tahap 1
    paths = state.get("paths", {})
    source_video = paths.get("source_video")

    # Validasi keamanan (memastikan data tidak kosong)
    if not source_video or not os.path.exists(source_video):
        raise FileNotFoundError(f"Video sumber tidak ditemukan di: {source_video}")

    # Ambil start_time dan end_time hasil AI dari tahap 3
    director_data = state.get("stages", {}).get("3_director_analysis", {})
    start_time = director_data.get("start_time")
    end_time = director_data.get("end_time")

    if start_time is None or end_time is None:
        raise ValueError("Data start_time atau end_time dari AI belum tersedia di JSON!")

    # Hapus file output lama jika ada 
    # (Penting! Berjaga-jaga jika skrip ini sedang di-retry oleh n8n akibat timeout sebelumnya)
    if os.path.exists(FINAL_CUT_PATH):
        os.remove(FINAL_CUT_PATH)

    # Efek blur diringankan sedikit (15:15) agar CPU tidak ngos-ngosan
    blur_filter = (
        "split[original][copy];"
        "[copy]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=15:15[blurred];"
        "[original]scale=1080:-1[fg];"
        "[blurred][fg]overlay=(W-w)/2:(H-h)/2"
    )

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-ss", start_time,
        "-to", end_time,
        "-i", source_video,
        "-vf", blur_filter,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "copy",
        FINAL_CUT_PATH
    ]

    print(f"Memotong video dari detik {start_time} ke {end_time} dengan kecepatan Turbo...")
    subprocess.run(ffmpeg_cmd, check=True)
    print("✅ Video Shorts berhasil dibuat dengan cepat!")

    return {
        "paths": {
            "cut_video": FINAL_CUT_PATH
        }
    }


if __name__ == "__main__":
    try:
        cm = CheckpointManager()
        cm.run_stage("4_cut_video", cut_video)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)