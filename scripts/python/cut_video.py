import json
import subprocess

VIDEO_PATH = "/home/ubuntu/clipper/output/temp/video.mp4"
SHORTS_PATH = "/home/ubuntu/clipper/output/temp/shorts.mp4"
JSON_PATH = "/home/ubuntu/clipper/output/temp/cut.json"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

start_time = str(data["start"])
end_time = str(data["end"])

ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-i", VIDEO_PATH,
    "-ss", start_time,
    "-to", end_time,
    "-vf", "crop=ih*(9/16):ih", 
    "-c:v", "libx264",
    "-preset", "fast",
    "-c:a", "copy",
    SHORTS_PATH
]

# Eksekusi FFmpeg
subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)