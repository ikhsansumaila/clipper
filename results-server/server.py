#!/usr/bin/env python3
"""Lightweight file browser API for Clipper results."""

import json
import os
import mimetypes
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote
import urllib.request
import urllib.error
import discord_notif


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = Path(os.environ.get("STATIC_DIR", APP_DIR / "static"))
RESULTS_DIR = Path(os.environ.get("RESULTS_DIR", "/data/results"))
TEMP_DIR = Path(os.environ.get("TEMP_DIR", "/data/temp"))
# BASE_DIR adalah root project clipper — tempat state.json & history.json berada
# (dipindah dari output/temp sejak refactor config.py)
BASE_DIR = Path(os.environ.get("BASE_DIR", "/data/base"))
PORT = 5680
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL", "")
# DISCORD_BOT_ID = os.environ.get("DISCORD_BOT_ID", "")


class ResultsHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = unquote(self.path)

        if path in ("/api/files", "/results/api/files"):
            self.send_file_list()
        elif path in ("/api/state", "/results/api/state"):
            self.send_state()
        elif path in ("/api/history", "/results/api/history"):
            self.send_history()
        elif path.startswith("/files/"):
            self.serve_file(path[7:])  # strip /files/
        elif path.startswith("/results/files/"):
            self.serve_file(path[15:])  # strip /results/files/ prefix used by reverse proxy UI links
        elif path.startswith("/thumbs/"):
            self.serve_thumb(path[8:])
        elif path.startswith("/results/thumbs/"):
            self.serve_thumb(path[16:])
        elif path.startswith("/static/"):
            self.serve_static(path[8:])
        elif path.startswith("/results/static/"):
            self.serve_static(path[16:])
        else:
            # Serve index.html for root and any other path
            self.serve_index()


    def do_POST(self):
        path = unquote(self.path)
        if path in ("/api/reclip", "/results/api/reclip"):
            self.handle_reclip()
        else:
            self.send_error(404)

    def handle_reclip(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            url = data.get("url")
            if not url:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "Missing url"}')
                return
                
            if not N8N_WEBHOOK_URL:
            # or not DISCORD_BOT_ID:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'{"error": "Missing webhook config"}')
                return
                
            # Bentuk payload untuk di webhook n8n
            payload = {
                "author": "Web UI",
                "content": f"<@> {url}",
                # "channelId": "WebUI",
                # "replyMessageId": "0"
            }
            
            payload_bytes = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(N8N_WEBHOOK_URL, data=payload_bytes, headers={'Content-Type': 'application/json'})
            
            with urllib.request.urlopen(req) as response:
                pass # success

            # Kirim notifikasi ke Discord
            discord_notif.send_notification(f"Melakukan Reclip untuk Video: {url}")
                
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"success": true}')
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def send_file_list(self):
        files = []
        if RESULTS_DIR.exists():
            for f in RESULTS_DIR.iterdir():
                if f.is_file() and f.name != "index.html":
                    stat = f.stat()
                    files.append({
                        "name": f.name,
                        "size": stat.st_size,
                        "modified": stat.st_mtime * 1000,  # JS timestamp
                    })

        data = json.dumps(files).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def send_state(self):
        state_file = BASE_DIR / "state.json"
        
        if state_file.exists() and state_file.is_file():
            try:
                data = state_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception as e:
                pass
                
        # Send empty object if file doesn't exist or error
        data = b"{}"
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def send_history(self):
        history_file = BASE_DIR / "history.json"

        if history_file.exists() and history_file.is_file():
            try:
                data = history_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception:
                pass

        data = b"{}"
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def serve_file(self, filename):
        filepath = RESULTS_DIR / filename
        if not filepath.exists() or not filepath.is_file():
            self.send_error(404)
            return

        # Security: ensure path doesn't escape results dir
        try:
            filepath.resolve().relative_to(RESULTS_DIR.resolve())
        except ValueError:
            self.send_error(403)
            return

        self._send_file_content(filepath)

    def serve_thumb(self, filename):
        thumb_path = RESULTS_DIR / "thumbs" / filename
        if not thumb_path.exists() or not thumb_path.is_file():
            self.send_error(404)
            return
            
        try:
            thumb_path.resolve().relative_to(RESULTS_DIR.resolve())
        except ValueError:
            self.send_error(403)
            return
            
        self._send_file_content(thumb_path)

    def _send_file_content(self, filepath):
        mime_type = mimetypes.guess_type(str(filepath))[0] or "application/octet-stream"
        size = filepath.stat().st_size

        # Allow range requests for smooth video seeking
        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            try:
                range_spec = range_header[6:]
                start_str, end_str = range_spec.split("-", 1)
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else size - 1
                end = min(end, size - 1)
                if start < 0 or start >= size or end < start:
                    self.send_error(416)
                    return
                length = end - start + 1

                self.send_response(206)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                self.end_headers()

                with open(filepath, "rb") as f:
                    f.seek(start)
                    self.wfile.write(f.read(length))
                return
            except (ValueError, IndexError):
                pass

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)

    def serve_static(self, filename):
        filepath = STATIC_DIR / filename
        if not filepath.exists() or not filepath.is_file():
            self.send_error(404)
            return

        try:
            filepath.resolve().relative_to(STATIC_DIR.resolve())
        except ValueError:
            self.send_error(403)
            return

        self._send_file_content(filepath)

    def serve_index(self):
        index_path = STATIC_DIR / "index.html"
        if not index_path.exists():
            self.send_error(404)
            return

        data = index_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        # Quieter logging
        pass


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), ResultsHandler)
    print(f"Results server running on http://127.0.0.1:{PORT}")
    server.serve_forever()
