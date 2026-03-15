"""
Simple HTTP server that serves static files and adds a /api/list-timestamps endpoint
that returns JSON files from a target directory (defaults to output/).
"""

import os
import sys
import json
import signal
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver

PORT = 8847
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")


class DialogServer(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/list-timestamps":
            self.handle_list_timestamps(parsed)
            return

        if parsed.path == "/api/list-podcasts":
            self.handle_list_podcasts()
            return

        if parsed.path == "/api/podcast-state":
            self.handle_podcast_state()
            return

        if parsed.path == "/api/podcast-manifest":
            self.handle_podcast_manifest(parsed)
            return

        if parsed.path == "/api/paper":
            self.handle_paper(parsed)
            return

        # Serve audio files with Range support (needed for seeking)
        if parsed.path.endswith(('.wav', '.mp3', '.ogg', '.m4a')):
            self.handle_audio(parsed.path)
            return

        # Serve static files normally
        super().do_GET()

    def handle_list_timestamps(self, parsed):
        params = parse_qs(parsed.query)
        folder = params.get("folder", ["output"])[0]

        # Resolve folder relative to project root
        target = os.path.normpath(os.path.join(SCRIPT_DIR, folder))

        # Safety: must be under SCRIPT_DIR
        if not target.startswith(SCRIPT_DIR):
            self.send_json(400, {"error": "Invalid folder path"})
            return

        if not os.path.isdir(target):
            self.send_json(404, {"error": f"Folder not found: {folder}"})
            return

        # Find all *_timestamps.json files
        files = []
        for fname in sorted(os.listdir(target), reverse=True):
            if fname.endswith("_timestamps.json"):
                fpath = os.path.join(target, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    files.append({
                        "filename": fname,
                        "path": f"{folder}/{fname}",
                        "tag": data.get("tag", ""),
                        "generated": data.get("generated", ""),
                        "duration": data.get("total_duration_formatted", ""),
                        "line_count": len(data.get("lines", [])),
                    })
                except (json.JSONDecodeError, OSError):
                    pass

        self.send_json(200, {"folder": folder, "files": files})

    def handle_list_podcasts(self):
        """Scan output/ for subfolders containing manifest.json, return list with paper titles."""
        output_dir = os.path.join(SCRIPT_DIR, "output")
        podcasts = []
        if os.path.isdir(output_dir):
            for name in sorted(os.listdir(output_dir)):
                folder = os.path.join(output_dir, name)
                manifest_file = os.path.join(folder, "manifest.json")
                if os.path.isdir(folder) and os.path.isfile(manifest_file):
                    try:
                        with open(manifest_file, "r", encoding="utf-8") as f:
                            mdata = json.load(f)

                        # Normalize parts: support both array and dict formats
                        raw_parts = mdata.get("parts", [])
                        if isinstance(raw_parts, dict):
                            parts_list = []
                            for k, v in sorted(raw_parts.items(), key=lambda x: int(x[0])):
                                v["part_number"] = int(k)
                                if "covers_paragraphs" not in v and "paragraphs" in v:
                                    v["covers_paragraphs"] = v["paragraphs"]
                                parts_list.append(v)
                            raw_parts = parts_list

                        # Try to read paper title from paper_source
                        title = mdata.get("paper_title", name)  # fallback to paper_title or folder name
                        paper_source = mdata.get("paper_source")
                        if not paper_source:
                            # Auto-detect: look for input/{name}_paper.json
                            guessed = f"input/{name}_paper.json"
                            guessed_path = os.path.normpath(os.path.join(SCRIPT_DIR, guessed))
                            if os.path.isfile(guessed_path):
                                paper_source = guessed
                        if paper_source:
                            paper_path = os.path.normpath(os.path.join(SCRIPT_DIR, paper_source))
                            if paper_path.startswith(SCRIPT_DIR) and os.path.isfile(paper_path):
                                with open(paper_path, "r", encoding="utf-8") as pf:
                                    pdata = json.load(pf)
                                title = pdata.get("meta", {}).get("title", title)
                        generated_count = sum(1 for p in raw_parts if isinstance(p, dict) and p.get("status") == "generated")
                        total_count = len(raw_parts)
                        podcasts.append({
                            "folder": name,
                            "manifest_path": f"output/{name}/manifest.json",
                            "paper_source": paper_source,
                            "title": title,
                            "generated_parts": generated_count,
                            "total_parts": total_count,
                        })
                    except Exception:
                        pass
        self.send_json(200, {"podcasts": podcasts})

    def handle_podcast_state(self):
        state_path = os.path.join(SCRIPT_DIR, "podcast_generation_state.json")
        if not os.path.isfile(state_path):
            self.send_json(404, {"error": "No podcast_generation_state.json found"})
            return
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.send_json(200, data)

    def handle_podcast_manifest(self, parsed):
        params = parse_qs(parsed.query)
        manifest_path = params.get("path", [None])[0]
        if not manifest_path:
            # Try to read from state file
            state_path = os.path.join(SCRIPT_DIR, "podcast_generation_state.json")
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                manifest_path = state.get("manifest")
        if not manifest_path:
            self.send_json(400, {"error": "No manifest path provided or found in state"})
            return
        full_path = os.path.normpath(os.path.join(SCRIPT_DIR, manifest_path))
        if not full_path.startswith(SCRIPT_DIR):
            self.send_json(400, {"error": "Invalid path"})
            return
        if not os.path.isfile(full_path):
            self.send_json(404, {"error": f"Manifest not found: {manifest_path}"})
            return
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Normalize parts: convert dict-keyed format to array format
        raw_parts = data.get("parts", [])
        if isinstance(raw_parts, dict):
            parts_list = []
            for k, v in sorted(raw_parts.items(), key=lambda x: int(x[0])):
                v["part_number"] = int(k)
                if "covers_paragraphs" not in v and "paragraphs" in v:
                    v["covers_paragraphs"] = v.pop("paragraphs")
                parts_list.append(v)
            data["parts"] = parts_list

        # Ensure every part has a part_number
        for i, p in enumerate(data.get("parts", [])):
            if "part_number" not in p:
                p["part_number"] = i + 1

        # Auto-detect paper_source if missing
        if "paper_source" not in data:
            # Derive folder name from manifest path
            rel = os.path.relpath(full_path, SCRIPT_DIR).replace("\\", "/")
            parts = rel.split("/")
            if len(parts) >= 2:
                folder_name = parts[1]  # output/{folder}/manifest.json
                guessed = f"input/{folder_name}_paper.json"
                guessed_path = os.path.normpath(os.path.join(SCRIPT_DIR, guessed))
                if os.path.isfile(guessed_path):
                    data["paper_source"] = guessed

        self.send_json(200, data)

    def handle_paper(self, parsed):
        params = parse_qs(parsed.query)
        paper_path = params.get("path", [None])[0]
        if not paper_path:
            state_path = os.path.join(SCRIPT_DIR, "podcast_generation_state.json")
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                paper_path = state.get("paper_source")
        if not paper_path:
            self.send_json(400, {"error": "No paper path provided or found in state"})
            return
        full_path = os.path.normpath(os.path.join(SCRIPT_DIR, paper_path))
        if not full_path.startswith(SCRIPT_DIR):
            self.send_json(400, {"error": "Invalid path"})
            return
        if not os.path.isfile(full_path):
            self.send_json(404, {"error": f"Paper not found: {paper_path}"})
            return
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.send_json(200, data)

    def handle_audio(self, path):
        """Serve audio files with HTTP Range support for seeking."""
        # Translate URL path to filesystem path
        file_path = os.path.normpath(os.path.join(SCRIPT_DIR, path.lstrip('/')))
        if not file_path.startswith(SCRIPT_DIR) or not os.path.isfile(file_path):
            self.send_error(404, "File not found")
            return

        file_size = os.path.getsize(file_path)
        ext = os.path.splitext(file_path)[1].lower()
        content_type = {
            '.wav': 'audio/wav', '.mp3': 'audio/mpeg',
            '.ogg': 'audio/ogg', '.m4a': 'audio/mp4',
        }.get(ext, 'application/octet-stream')

        range_header = self.headers.get('Range')
        if range_header:
            # Parse Range: bytes=start-end
            range_spec = range_header.replace('bytes=', '')
            parts = range_spec.split('-')
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else file_size - 1
            end = min(end, file_size - 1)
            length = end - start + 1

            self.send_response(206)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(length))
            self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            with open(file_path, 'rb') as f:
                f.seek(start)
                self.wfile.write(f.read(length))
        else:
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(file_size))
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())

    def send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Quieter logging
        if "/api/" in str(args[0]):
            print(f"  API: {args[0]}")


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True
    allow_reuse_port = True


import threading

class ThreadedHTTPServer(ReusableHTTPServer):
    """Handle requests in separate threads so large audio files don't block API calls."""
    def process_request(self, request, client_address):
        t = threading.Thread(target=self.process_request_thread, args=(request, client_address))
        t.daemon = True
        t.start()

    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)


def get_lan_ip():
    """Get the machine's LAN IP address."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    os.chdir(SCRIPT_DIR)
    HOST = "0.0.0.0"
    server = ThreadedHTTPServer((HOST, PORT), DialogServer)

    def shutdown_handler(sig, frame):
        print(f"\nReceived signal {sig}, shutting down.")
        server.shutdown()
        server.server_close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    lan_ip = get_lan_ip()
    print(f"Dialog server running on {HOST}:{PORT}")
    print(f"  Local:           http://localhost:{PORT}/")
    print(f"  LAN:             http://{lan_ip}:{PORT}/")
    print(f"  Podcast Player:  http://{lan_ip}:{PORT}/podcast_player.html")
    print(f"  Panda Reader:    http://{lan_ip}:{PORT}/panda_reader.html")
    print(f"  Dialog Player:   http://{lan_ip}:{PORT}/dialog_player.html")
    print(f"  PID: {os.getpid()}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
