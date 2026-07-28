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

        if parsed.path == "/api/part-timestamps":
            self.handle_part_timestamps(parsed)
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

    # ---- New-pipeline (papers/<slug>/) bridge helpers -------------------
    #
    # The new pipeline stores one script.json with inlined timestamps and
    # stable part_NN.wav names (PIPELINE-DECISIONS "render_audio I/O
    # contract"), not the legacy manifest + per-part *_timestamps.json
    # sibling files. Rather than teach podcast_player.html a second set of
    # shapes, these helpers synthesize the legacy shapes on the fly so the
    # player frontend stays untouched until the new reader UI lands
    # (SKILLS-PLAN section 10).

    @staticmethod
    def _safe_slug(slug):
        return bool(slug) and all(c.isalnum() or c == "_" for c in slug)

    @staticmethod
    def _fmt_duration(ms):
        total_s = ms / 1000.0
        return f"{int(total_s // 60)}:{total_s % 60:06.3f}"

    def load_new_paper(self, slug):
        """Load script/meta/spans for a papers/<slug>/ paper, or None."""
        if not self._safe_slug(slug):
            return None
        base = os.path.join(SCRIPT_DIR, "papers", slug)
        script_path = os.path.join(base, "podcast", "script.json")
        if not os.path.isfile(script_path):
            return None
        out = {"slug": slug, "base": base}
        with open(script_path, "r", encoding="utf-8") as f:
            out["script"] = json.load(f)
        for key, fname in (("meta", "paper.meta.json"), ("spans", "paper.spans.json")):
            p = os.path.join(base, fname)
            if os.path.isfile(p):
                with open(p, "r", encoding="utf-8") as f:
                    out[key] = json.load(f)
        return out

    def new_manifest_parts(self, paper):
        """Synthesize legacy-shaped manifest parts from a new script.json."""
        slug = paper["slug"]
        sections = (paper.get("spans") or {}).get("sections") or []
        parts = []
        for part in paper["script"].get("parts", []):
            n = part.get("part_of", {}).get("n", len(parts) + 1)
            covered = sorted({pid for line in part.get("lines", [])
                              for pid in (line.get("source_paragraphs") or [])})
            cov = set(covered)
            sec_titles = [s["title"] for s in sections
                          if cov & set(s.get("paragraph_ids", []))]
            if len(sec_titles) > 1:
                title = f"{sec_titles[0]} → {sec_titles[-1]}"
            elif sec_titles:
                title = sec_titles[0]
            else:
                title = f"Part {n}"
            rendered = bool(part.get("wav")) and any(
                "start_ms" in line for line in part.get("lines", []))
            parts.append({
                "part_number": n,
                "title": title,
                "covers_paragraphs": covered,
                "status": "generated" if rendered else "pending",
                # Relative (no leading slash): the player prepends "/" and
                # later takes dirname("api/") as the audio folder, which the
                # "../papers/..." audio_file below walks back out of.
                "timestamps_file": f"api/part-timestamps?slug={slug}&part={n}",
            })
        return parts

    def handle_part_timestamps(self, parsed):
        """Legacy-shaped timestamps view of one part of a new script.json."""
        params = parse_qs(parsed.query)
        slug = params.get("slug", [None])[0]
        try:
            part_num = int(params.get("part", ["0"])[0])
        except ValueError:
            part_num = 0
        paper = self.load_new_paper(slug)
        if not paper:
            self.send_json(404, {"error": f"No new-pipeline podcast for slug: {slug}"})
            return
        part = next((p for p in paper["script"].get("parts", [])
                     if p.get("part_of", {}).get("n") == part_num), None)
        if not part:
            self.send_json(404, {"error": f"Part {part_num} not found for {slug}"})
            return
        lines = []
        for i, line in enumerate(part.get("lines", [])):
            start = line.get("start_ms", 0)
            end = line.get("end_ms", start)
            lines.append({
                "index": i,
                "voice": line.get("voice", ""),
                "text": line.get("text", ""),
                "start_ms": start,
                "end_ms": end,
                "duration_ms": end - start,
                "source_paragraphs": line.get("source_paragraphs", []),
            })
        total = part.get("total_duration_ms", lines[-1]["end_ms"] if lines else 0)
        self.send_json(200, {
            "source": f"papers/{slug}/podcast/script.json",
            # Resolved by the player against the timestamps_file's "api/"
            # folder, so walk back to the repo root explicitly.
            "audio_file": f"../papers/{slug}/podcast/{part.get('wav', '')}",
            "tag": f"part_{part_num:02d}",
            "generated": paper["script"].get("rendered_utc", ""),
            "total_duration_ms": total,
            "total_duration_formatted": self._fmt_duration(total),
            "lines": lines,
        })

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

        # New-pipeline papers: papers/<slug>/podcast/script.json
        papers_dir = os.path.join(SCRIPT_DIR, "papers")
        if os.path.isdir(papers_dir):
            for name in sorted(os.listdir(papers_dir)):
                paper = None
                try:
                    paper = self.load_new_paper(name)
                except Exception:
                    pass
                if not paper:
                    continue
                parts = self.new_manifest_parts(paper)
                title = (paper.get("meta") or {}).get("title", name)
                podcasts.append({
                    "folder": name,
                    "manifest_path": f"papers/{name}/podcast/script.json",
                    "paper_source": f"papers/{name}",
                    "title": title,
                    "generated_parts": sum(1 for p in parts if p["status"] == "generated"),
                    "total_parts": len(parts),
                })
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

        # New-pipeline path: papers/<slug>/podcast/script.json → synthesize
        norm = manifest_path.replace("\\", "/").strip("/")
        np_parts = norm.split("/")
        if len(np_parts) == 4 and np_parts[0] == "papers" and np_parts[2:] == ["podcast", "script.json"]:
            paper = self.load_new_paper(np_parts[1])
            if not paper:
                self.send_json(404, {"error": f"Manifest not found: {manifest_path}"})
                return
            meta = paper.get("meta") or {}
            self.send_json(200, {
                "paper_title": meta.get("title", np_parts[1]),
                "paper_authors": ", ".join(meta.get("authors", [])),
                "paper_source": f"papers/{np_parts[1]}",
                "total_parts": len(paper["script"].get("parts", [])),
                "parts": self.new_manifest_parts(paper),
            })
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

        # New-pipeline path: papers/<slug> → synthesize legacy paper JSON
        # ({meta, sections[].paragraphs[]}) from paper.meta.json + the
        # byte-offset spans over the immutable paper.md.
        norm = paper_path.replace("\\", "/").strip("/")
        np_parts = norm.split("/")
        if len(np_parts) == 2 and np_parts[0] == "papers":
            paper = self.load_new_paper(np_parts[1])
            if not paper:
                self.send_json(404, {"error": f"Paper not found: {paper_path}"})
                return
            md_path = os.path.join(paper["base"], "paper.md")
            spans = paper.get("spans") or {}
            try:
                with open(md_path, "rb") as f:
                    md = f.read()
            except OSError:
                self.send_json(404, {"error": f"paper.md missing for {np_parts[1]}"})
                return
            by_id = {p["id"]: p for p in spans.get("paragraphs", [])}

            def para_text(pid):
                span = by_id.get(pid)
                if not span:
                    return ""
                text = md[span["start_offset"]:span["end_offset"]].decode("utf-8", "replace")
                # Reader-pane cleanup only — paper.md itself stays pristine.
                return text.replace("**", "").lstrip("# ").strip()

            sections = []
            for sec in spans.get("sections", []) or [{"id": 1, "title": "Paper", "paragraph_ids": sorted(by_id)}]:
                paras = [{"id": pid, "text": para_text(pid)}
                         for pid in sec.get("paragraph_ids", [])]
                # Drop empties and the section's own heading paragraph —
                # the pane already renders the section title.
                title = sec.get("title", "")
                paras = [p for p in paras
                         if p["text"] and p["text"].casefold() != title.casefold()]
                if paras:
                    sections.append({"id": sec.get("id"), "title": sec.get("title", ""), "paragraphs": paras})
            meta = paper.get("meta") or {}
            self.send_json(200, {
                "meta": {
                    "title": meta.get("title", np_parts[1]),
                    "authors": meta.get("authors", []),
                    "year": meta.get("year", ""),
                },
                "sections": sections,
            })
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
