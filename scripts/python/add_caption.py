import json
import os
import re
import shlex
import sys
import config
from checkpoint_manager import CheckpointManager


def add_caption():
    cm = CheckpointManager()
    state = cm.get_state() or {}
    
    # 1. Baca data potongan dari director-cut.json
    with open(config.DIRECTOR_CUT_FILE, "r") as f:
        cut_data = json.load(f)
        start_offset = float(cut_data["start"])

    # 2. Baca transkrip, filter, dan geser waktunya
    transcript_path = state.get("paths", {}).get("transcript")
    if not transcript_path or not os.path.exists(transcript_path):
        # Fallback
        transcript_path = config.TRANSCRIPT_FILE
        
    new_srt_lines = []
    with open(transcript_path, "r") as f:
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
    with open(config.SUBS_FILE, "w") as f:
        f.writelines(new_srt_lines)

    # 4. Ambil title dari director-cut.json
    video_title = cut_data["title"]
    video_title = re.sub(r'[^\w\-]', '_', video_title)
    video_title = re.sub(r'_+', '_', video_title).strip('_')

    # 5. Burn subtitle ke video
    result_file = f"{config.RESULTS_DIR}/{video_title}.mp4"
    print(f"Burning subtitle ke video dan menyimpan sebagai: {result_file}")

    # Fontsize dikecilkan, Alignment=2 (bawah tengah), MarginV (jarak dari bawah)
    # try on simulator:
    # https://ffmpeg-subtitle-simulator.vercel.app/
    cmd = (f"ffmpeg -y -i {config.FINAL_CUT_VIDEO_FILE} "
        f"-vf \"subtitles={config.SUBS_FILE}:force_style='FontName=Arial Bold,FontSize=8,PrimaryColour=&H1BDBF8&,OutlineColour=&H000000&,BackColour=&H4D000000&,Bold=1,Italic=0,BorderStyle=3,Outline=1,Shadow=1,MarginV=75,Alignment=2'\" "
        f"-c:a copy {shlex.quote(result_file)}"
    )
    os.system(cmd)

    # 6. Generate Thumbnail otomatis
    print("Membentuk thumbnail video...")
    thumb_dir = f"{config.RESULTS_DIR}/thumbs"
    os.makedirs(thumb_dir, exist_ok=True)
    thumb_file = f"{thumb_dir}/{video_title}.jpg"
    thumb_cmd = f"ffmpeg -y -i {shlex.quote(result_file)} -ss 00:00:01 -vframes 1 -vf \"scale=480:-1\" -q:v 3 {shlex.quote(thumb_file)} 2>/dev/null"
    os.system(thumb_cmd)

    return {
        "paths": {
            "final_video": result_file
        }
    }


if __name__ == "__main__":
    try:
        cm = CheckpointManager()
        # Jalankan stage terakhir
        success = cm.run_stage(config.STAGE_ADD_CAPTION, add_caption)
        
        # # JIKA SEMUA STAGE SUKSES, RESET CHECKPOINT-NYA
        # if success:
        #     print("🎉 Semua proses selesai! Membersihkan file checkpoint...")
        #     cm.reset()
            
        #     # Opsi Tambahan: Kamu juga bisa menambahkan kode di sini untuk 
        #     # menghapus file-file temporary lain (seperti source.mp4, audio.wav) 
        #     # agar hardisk server kamu tidak penuh.

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)