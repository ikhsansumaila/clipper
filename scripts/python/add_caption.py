import json
import os
import re
import shlex
import sys


def add_caption():
    # 1. Baca data potongan dari director-cut.json
    with open("/home/ubuntu/clipper/output/temp/director-cut.json", "r") as f:
        cut_data = json.load(f)
        start_offset = float(cut_data["start"])

    # 2. Baca transkrip, filter, dan geser waktunya
    new_srt_lines = []
    with open("/home/ubuntu/clipper/output/temp/transcript.txt", "r") as f:
        lines = f.readlines()

    def format_time(t):
        h, m = int(t // 3600), int((t % 3600) // 60)
        s, ms = int(t % 60), int((t % 1) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    index = 1
    for line in lines:
        if not line.strip():
            continue
        time_part = line.split(']')[0].replace('[', '')
        start, end = map(float, time_part.split('-'))
        text = line.split(']', 1)[1].strip()

        # Hanya ambil teks yang masuk dalam rentang start dan end dari director-cut.json
        if start >= start_offset and end <= (start_offset + (cut_data["end"] - start_offset)):
            # Geser waktu (dikurangi start_offset agar video dimulai dari 00:00)
            adj_start = start - start_offset
            adj_end = end - start_offset
            new_srt_lines.append(f"{index}\n{format_time(adj_start)} --> {format_time(adj_end)}\n{text}\n\n")
            index += 1

    # 3. Simpan file .srt yang sudah disesuaikan
    with open("/home/ubuntu/clipper/output/temp/subs.srt", "w") as f:
        f.writelines(new_srt_lines)

    # 4. Ambil title dari director-cut.json
    video_title = cut_data["title"]
    video_title = re.sub(r'[^\w\-]', '_', video_title)
    video_title = re.sub(r'_+', '_', video_title).strip('_')

    # 5. Burn subtitle ke video
    output_path = f"/home/ubuntu/clipper/output/results/{video_title}.mp4"
    print(f"Burning subtitle ke video dan menyimpan sebagai: {output_path}")
    cmd = (
        "ffmpeg -y -i /home/ubuntu/clipper/output/temp/final-cut.mp4 "
        "-vf \"subtitles=/home/ubuntu/clipper/output/temp/subs.srt:force_style='Fontsize=12,PrimaryColour=&H00FFFF&'\" "
        f"-c:a copy {shlex.quote(output_path)}"
    )
    os.system(cmd)


if __name__ == "__main__":
    try:
        add_caption()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)