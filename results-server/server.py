#!/usr/bin/env python3
"""Lightweight file browser API for Clipper results."""

import json
import os
import mimetypes
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote

RESULTS_DIR = Path(os.environ.get("RESULTS_DIR", "/data/results"))
PORT = 5680

class ResultsHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = unquote(self.path)

        if path == "/api/files":
            self.send_file_list()
        elif path.startswith("/files/"):
            self.serve_file(path[7:])  # strip /files/
        else:
            # Serve index.html for root and any other path
            self.serve_index()

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

        mime_type = mimetypes.guess_type(str(filepath))[0] or "application/octet-stream"
        size = filepath.stat().st_size

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(size))
        self.send_header("Accept-Ranges", "bytes")

        # Allow range requests for video seeking
        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            try:
                range_spec = range_header[6:]
                start_str, end_str = range_spec.split("-", 1)
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else size - 1
                end = min(end, size - 1)
                length = end - start + 1

                self.send_response(206)
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                self.send_header("Content-Length", str(length))
                self.send_header("Content-Type", mime_type)
                self.end_headers()

                with open(filepath, "rb") as f:
                    f.seek(start)
                    self.wfile.write(f.read(length))
                return
            except (ValueError, IndexError):
                pass

        self.end_headers()
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)

    def serve_index(self):
        index_path = RESULTS_DIR / "index.html"
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
