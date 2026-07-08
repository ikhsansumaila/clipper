import json
import os
import sys
import tempfile

class CheckpointManager:
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

    def __init__(self, filepath="/home/ubuntu/clipper/output/temp/state.json"):
        self.filepath = filepath
        self.dirpath = os.path.dirname(filepath)
        
        if self.dirpath and not os.path.exists(self.dirpath):
            os.makedirs(self.dirpath, exist_ok=True)

    def _read_data(self):
        if not os.path.exists(self.filepath):
            return None
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: File {self.filepath} korup.")
            return None

    def _write_data(self, data):
        fd, temp_path = tempfile.mkstemp(dir=self.dirpath, text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, self.filepath)

    def initialize(self, video_id="", url=""):
        """Inisialisasi file JSON. Otomatis reset jika mendeteksi URL video baru."""
        data = self._read_data()
        
        # CEK URL BENTROK: Jika file JSON sudah ada, tapi URL-nya beda dengan URL saat ini
        if data is not None:
            saved_url = data.get("url", "")
            if saved_url and url and saved_url != url:
                print(f"⚠️ URL baru terdeteksi!\n   Lama: {saved_url}\n   Baru: {url}")
                print("🔄 Mereset file state.json secara otomatis...")
                data = None  # Mengubah data menjadi None akan memicu pembuatan ulang di bawah
            elif saved_url and url and saved_url == url:
                # Cek jika stage terakhir sudah selesai
                if data.get("stages", {}).get(self.LAST_STAGE, {}).get("status") == "completed":
                    print("🔄 Proses untuk URL ini sudah selesai sepenuhnya. Mereset stage mulai dari 3_director_analysis...")
                    if "stages" not in data:
                        data["stages"] = {}
                    for stage in [self.STAGE_DIRECTOR_ANALYSIS, self.STAGE_CUT_VIDEO, self.STAGE_ADD_CAPTION]:
                        data["stages"][stage] = {"status": "pending"}
                    self._write_data(data)
            elif not saved_url and url:
                # Jika URL lama kosong (mungkin file corrupt), reset juga
                data = None

        # BUAT BARU / OVERWRITE JIKA DATA = NONE
        if data is None:
            data = {
                "video_id": video_id,
                "url": url,
                "global_status": "in_progress",
                "paths": {},
                "stages": {
                    stage_name: {"status": "pending"}
                    for stage_name in self.STAGES
                }
            }
            self._write_data(data)
            
        return data

    def get_state(self):
        return self._read_data()

    def update_stage(self, stage_name, status, **kwargs):
        data = self._read_data()
        if data and stage_name in data.get("stages", {}):
            data["stages"][stage_name]["status"] = status
            for key, value in kwargs.items():
                data["stages"][stage_name][key] = value
            self._write_data(data)

    def update_path(self, path_key, path_value):
        data = self._read_data()
        if data:
            if "paths" not in data:
                data["paths"] = {}
            data["paths"][path_key] = path_value
            self._write_data(data)

    def is_completed(self, stage_name):
        """Cek apakah sebuah tahapan sudah selesai."""
        data = self._read_data()
        if data and stage_name in data.get("stages", {}):
            return data["stages"][stage_name].get("status") == "completed"
        return False

    def reset(self):
        """Menghapus file checkpoint untuk mereset seluruh status."""
        if os.path.exists(self.filepath):
            try:
                os.remove(self.filepath)
                print(f"✅ Checkpoint direset: {self.filepath} telah dihapus.")
            except Exception as e:
                print(f"⚠️ Gagal menghapus checkpoint: {e}")
        else:
            print("ℹ️ File checkpoint tidak ditemukan, tidak ada yang perlu direset.")

    def run_stage(self, stage_name, task_function):
        """
        Menjalankan fungsi utama. Otomatis cek status, ubah ke in_progress,
        tangkap error, dan simpan hasil (return dict) ke checkpoint.
        """
        # 1. Cek apakah sudah selesai
        data = self._read_data()
        if data and stage_name in data.get("stages", {}) and data["stages"][stage_name].get("status") == "completed":
            print(f"[{stage_name}] Sudah selesai sebelumnya. Melewati proses ini...")
            return True # Keluar dari fungsi dengan sukses

        # 2. Tandai sedang berjalan
        print(f"[{stage_name}] Memulai proses...")
        self.update_stage(stage_name, "in_progress")

        try:
            # 3. Jalankan fungsi utama skrip kamu
            # Fungsi kamu harus me-return dictionary (opsional) untuk disimpan di JSON
            result = task_function()
            
            # 4. Tandai selesai dan simpan data tambahan jika ada
            if isinstance(result, dict):
                # Jika result punya key 'paths', simpan path-nya terpisah
                if "paths" in result:
                    for k, v in result["paths"].items():
                        self.update_path(k, v)
                    del result["paths"]
                
                # Simpan sisa data ke dalam stage
                self.update_stage(stage_name, "completed", **result)
            else:
                self.update_stage(stage_name, "completed")
            
            print(f"[{stage_name}] Proses berhasil!")
            return True

        except Exception as e:
            # 5. Tangkap error, simpan di JSON, lalu beri sinyal EXIT 1 ke n8n
            print(f"[{stage_name}] GAGAL: {str(e)}")
            self.update_stage(stage_name, "failed", error=str(e))
            sys.exit(1)