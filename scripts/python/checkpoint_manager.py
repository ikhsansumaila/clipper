import json
import os
import sys
import tempfile
import config

class CheckpointManager:

    def __init__(self):
        self.dirpath = config.TEMP_DIR
        self.statefilepath = config.STATE_FILE

        # file history
        self.history_filepath = config.HISTORY_FILE
        
        if self.dirpath and not os.path.exists(self.dirpath):
            os.makedirs(self.dirpath, exist_ok=True)

    def _read_data(self):
        if not os.path.exists(self.statefilepath):
            return None
        try:
            with open(self.statefilepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: File {self.statefilepath} korup.")
            return None

    def _write_data(self, data):
        target_dir = os.path.dirname(self.statefilepath)
        os.makedirs(target_dir, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(dir=target_dir, text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, self.statefilepath)

    def initialize(self, video_id="", url=""):
        """Inisialisasi file JSON. Otomatis reset jika mendeteksi URL video baru."""
        data = self._read_data()
        
        # CEK URL BENTROK: Jika file JSON sudah ada, tapi URL-nya beda dengan URL saat ini
        if data is not None:
            saved_url = data.get("url", "")
            if saved_url and url and saved_url != url:
                print(f"⚠️ URL baru terdeteksi!\n   Lama: {saved_url}\n   Baru: {url}", file=sys.stderr)
                print("🔄 Mereset file state.json secara otomatis...", file=sys.stderr)
                data = None  # Mengubah data menjadi None akan memicu pembuatan ulang di bawah
            elif saved_url and url and saved_url == url:
                # Cek jika stage terakhir sudah selesai
                if data.get("stages", {}).get(config.LAST_STAGE, {}).get("status") == "completed":
                    print("🔄 Proses untuk URL ini sudah selesai sepenuhnya. Mereset stage mulai dari 3_director_analysis...", file=sys.stderr)
                    if "stages" not in data:
                        data["stages"] = {}
                    for stage in [config.STAGE_DIRECTOR_ANALYSIS, config.STAGE_CUT_VIDEO, config.STAGE_ADD_CAPTION]:
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
                    for stage_name in config.STAGES
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
        if os.path.exists(self.statefilepath):
            try:
                os.remove(self.statefilepath)
                print(f"✅ Checkpoint direset: {self.statefilepath} telah dihapus.")
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
            print(f"[{stage_name}] Sudah selesai sebelumnya. Melewati proses ini...", file=sys.stderr)
            return True # Keluar dari fungsi dengan sukses

        # 2. Tandai sedang berjalan
        print(f"[{stage_name}] Memulai proses...", file=sys.stderr)
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
            
            print(f"[{stage_name}] Proses berhasil!", file=sys.stderr)
            return True

        except Exception as e:
            # 5. Tangkap error, simpan di JSON, lalu beri sinyal EXIT 1 ke n8n
            print(f"[{stage_name}] GAGAL: {str(e)}", file=sys.stderr)
            self.update_stage(stage_name, "failed", error=str(e))
            sys.exit(1)

    # ==========================================
    # FUNGSI HISTORY (RIWAYAT KLIP)
    # ==========================================
    def _read_history(self):
        """Membaca file history.json."""
        if not os.path.exists(self.history_filepath):
            return []
        try:
            with open(self.history_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return data
        except json.JSONDecodeError:
            return []

    def _write_history(self, data):
        """Menulis ke file history.json dengan aman."""
        target_dir = os.path.dirname(self.history_filepath)
        os.makedirs(target_dir, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(dir=target_dir, text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, self.history_filepath)

    def init_history(self, video_title, video_url):
        """Inisialisasi history.json dengan video baru jika belum ada."""
        if not video_url:
            return
            
        history_list = self._read_history()
        
        # Cek apakah video sudah ada di history
        video_exists = any(item.get("video_url") == video_url for item in history_list)
        
        if not video_exists:
            new_entry = {
                "video_title": video_title,
                "video_url": video_url,
                "clip_data": []
            }
            history_list.append(new_entry)
            self._write_history(history_list)
            print(f"📝 History diinisialisasi untuk: {video_title}", file=sys.stderr)

    def add_history(self, video_url, new_clips):
        """Menambahkan klip ke history spesifik berdasarkan video_url, maksimal MAX_HISTORY_CLIPS klip terakhir."""
        if not new_clips:
            return

        history_list = self._read_history()

        # Cari index video yang sesuai
        video_index = -1
        for i, item in enumerate(history_list):
            if item.get("video_url") == video_url:
                video_index = i
                break

        # Jika tidak ketemu (fallback), buat entry baru dengan title kosong (sebaiknya init_history dipanggil duluan)
        if video_index == -1:
            history_list.append({"video_title": "Unknown Title", "video_url": video_url, "clip_data": []})
            video_index = len(history_list) - 1

        if isinstance(new_clips, dict):
            new_clips = [new_clips]

        # Tambahkan klip baru
        history_list[video_index]["clip_data"].extend(new_clips)

        # FITUR MAX 20: Ambil hanya 20 elemen terakhir dari list (menghapus yang paling lama)
        history_list[video_index]["clip_data"] = history_list[video_index]["clip_data"][-config.MAX_HISTORY_CLIPS:]

        self._write_history(history_list)

    def get_history(self, video_url=None):
        """Mengambil seluruh history (list) atau history spesifik untuk satu video."""
        history_list = self._read_history()
        if not video_url:
            return history_list
            
        for item in history_list:
            if item.get("video_url") == video_url:
                return item
        
        return {"video_title": "", "video_url": video_url, "clip_data": []}
