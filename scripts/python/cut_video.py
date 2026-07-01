import json
import subprocess
import sys

VIDEO_PATH = "/home/ubuntu/clipper/output/temp/source.mp4"
FINAL_CUT_PATH = "/home/ubuntu/clipper/output/temp/final-cut.mp4"
JSON_PATH = "/home/ubuntu/clipper/output/temp/director-cut.json"


def cut_video():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    start_time = str(data["start"])
    end_time = str(data["end"])

    # Efek blur diringankan sedikit (15:15) agar CPU tidak ngos-ngosan
    blur_filter = (
        "split[original][copy];"
        "[copy]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=15:15[blurred];"
        "[original]scale=1080:-1[fg];"
        "[blurred][fg]overlay=(W-w)/2:(H-h)/2"
    )

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-ss", start_time,
        "-to", end_time,
        "-i", VIDEO_PATH,
        "-vf", blur_filter,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "copy",
        FINAL_CUT_PATH
    ]

    print(f"Memotong video dari detik {start_time} ke {end_time} dengan kecepatan Turbo...")
    subprocess.run(ffmpeg_cmd, check=True)
    print("✅ Video Shorts berhasil dibuat dengan cepat!")


if __name__ == "__main__":
    try:
        cut_video()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)