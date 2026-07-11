import os

# ==========================================
# 1. API KEYS & CREDENTIALS
# ==========================================
# Disarankan tetap menggunakan environment variables untuk API key produksi
# agar tidak terekspos jika kode dibagikan, tapi bisa kamu hardcode untuk testing.
SUPADATA_API_KEY = os.getenv("SUPADATA_API_KEY", "fallback_api_key_if_needed")
SUPADATA_BASE_URL = "https://api.supadata.ai/v1"
AI_AGENT_API_KEY = os.getenv("AI_AGENT_API_KEY", "fallback_ai_key_if_needed")
# Menggunakan host.docker.internal karena script berjalan di dalam container Docker.
# host.docker.internal akan merujuk ke OS host (tempat OmniRoute/9router berjalan).
AI_AGENT_API_ENDPOINT = os.getenv("AI_AGENT_API_ENDPOINT", "fallback_endpoint_if_needed")  # Contoh: "https://api.openai.com/v1/chat/completions"
AI_AGENT_MODEL_NAME = os.getenv("AI_AGENT_MODEL_NAME", "fallback_model_name_if_needed")  # Contoh: "gpt-4o-mini"

# ==========================================
# 2. STRUKTUR DIREKTORI UTAMA
# ==========================================
# Cukup ubah BASE_DIR jika project dipindah ke server/folder lain
BASE_DIR = os.getenv("WORKING_DIR", os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMP_DIR = os.path.join(DATA_DIR, "temp")

# ==========================================
# 3. FILE PATHS (STATE, HISTORY, I/O)
# ==========================================
STATE_FILE = os.path.join(DATA_DIR, "db", "state.json")
HISTORY_FILE = os.path.join(DATA_DIR, "db", "history.json")
DIRECTOR_CUT_FILE = os.path.join(TEMP_DIR, "director-cut.json")
FINAL_CUT_VIDEO_FILE = os.path.join(TEMP_DIR, "final-cut.mp4")
SUBS_FILE = os.path.join(TEMP_DIR, "subs.srt")
RESULTS_DIR = os.path.join(DATA_DIR, "results")

# ==========================================
# 4. PENGATURAN APLIKASI (APP SETTINGS)
# ==========================================
MAX_HISTORY_CLIPS = 20
MIN_CLIP_DURATION = 30  # Durasi minimal klip (detik)
MAX_CLIP_DURATION = 120  # Durasi maksimal klip (detik)


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