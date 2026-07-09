import os

# ==========================================
# 1. API KEYS & CREDENTIALS
# ==========================================
# Disarankan tetap menggunakan environment variables untuk API key produksi
# agar tidak terekspos jika kode dibagikan, tapi bisa kamu hardcode untuk testing.
SUPADATA_API_KEY = os.getenv("SUPADATA_API_KEY", "fallback_api_key_if_needed")
SUPADATA_BASE_URL = "https://api.supadata.ai/v1"
AI_API_KEY = os.getenv("MIHAKIDS_AI_API_KEY", "fallback_ai_key_if_needed")
AI_API_ENDPOINT = "http://localhost:20128/v1/chat/completions"
AI_MODEL_NAME = "mihan-high-providers"

# ==========================================
# 2. STRUKTUR DIREKTORI UTAMA
# ==========================================
# Cukup ubah BASE_DIR jika project dipindah ke server/folder lain
BASE_DIR = "/home/ubuntu/clipper"
TEMP_DIR = os.path.join(BASE_DIR, "output", "temp")

# ==========================================
# 3. FILE PATHS (STATE, HISTORY, I/O)
# ==========================================
STATE_FILE = os.path.join(TEMP_DIR, "state.json")
HISTORY_FILE = os.path.join(TEMP_DIR, "history.json")
URL_FILE = os.path.join(TEMP_DIR, "video_url.txt")
TRANSCRIPT_FILE = os.path.join(TEMP_DIR, "transcript.txt")
DIRECTOR_CUT_FILE = os.path.join(TEMP_DIR, "director-cut.json")
SOURCE_VIDEO_FILE = os.path.join(TEMP_DIR, "source.mp4")
FINAL_CUT_VIDEO_FILE = os.path.join(TEMP_DIR, "final-cut.mp4")
SUBS_FILE = os.path.join(TEMP_DIR, "subs.srt")
RESULTS_DIR = os.path.join(BASE_DIR, "output", "results")

# ==========================================
# 4. PENGATURAN APLIKASI (APP SETTINGS)
# ==========================================
MAX_HISTORY_CLIPS = 20
MIN_CLIP_DURATION = 1  # Durasi minimal klip (menit)
MAX_CLIP_DURATION = 3  # Durasi maksimal klip (menit)


# ==========================================
# 5. STAGE NAMES (TAHAPAN PROSES)
# ==========================================
STAGE_DOWNLOAD = "1_download"
STAGE_TRANSCRIBE = "2_transcribe"
STAGE_DIRECTOR_ANALYSIS = "3_director_analysis"
STAGE_CUT_VIDEO = "4_cut_video"
STAGE_ADD_CAPTION = "5_add_caption"

STAGES = [
    STAGE_DOWNLOAD,
    STAGE_TRANSCRIBE,
    STAGE_DIRECTOR_ANALYSIS,
    STAGE_CUT_VIDEO,
    STAGE_ADD_CAPTION,
]

LAST_STAGE = STAGE_ADD_CAPTION