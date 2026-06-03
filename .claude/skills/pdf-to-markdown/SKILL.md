---
name: pdf-to-markdown
description: Drive pdf-sidecar (FastAPI :6001) to convert a paper PDF into the new pipeline's paper.md + paper.spans.json + paper.md.sha256 under papers/<slug>/. Use when the user asks to intake a new paper, ingest a PDF, run pdf-to-markdown, or otherwise turn a source.pdf into the markdown working copy. Verifies the anchor/spans/checksum contract before declaring success.
---

# pdf-to-markdown — drive the sidecar, verify the contract

This skill converts one paper's PDF into the new-pipeline working copy. It
calls [pdf-sidecar](../../../pdf-sidecar/server.py) over HTTP — the sidecar
owns PyMuPDF, this skill owns the slug, the layout, and the checksum
discipline.

Doesn't replace the LLM-driven semantic markup pass. Section identification
(where Abstract ends, where Introduction begins, etc.), table fidelity, and
footnote handling are out of scope here — they come later in a follow-up
skill that reads `paper.md` and annotates `paper.spans.json` with section
ranges. This skill produces the *byte-accurate* markdown that downstream
work pins against.

## When to invoke

- "intake the PDF at <path>"
- "add this paper to the pipeline"
- "run pdf-to-markdown on <slug>"
- "extract <slug>.pdf"

## Inputs

1. **PDF path** — absolute or repo-relative. If the user dropped the file
   under `papers/<slug>/source.pdf`, that's the path to use; otherwise
   verify with the user and (optionally) suggest copying it under
   `papers/<slug>/` so future runs find it canonically.
2. **Slug** — short identifier (snake_case). If the user didn't supply one,
   propose one from the PDF filename or the paper title (skim the first
   page text via a one-off `pymupdf.open(path).load_page(0).get_text()`
   if needed, but most often the user already has a slug in mind).
3. **License** — ask the user before extraction if it's not already in
   `papers/<slug>/paper.meta.json`. CC BY-NC-SA papers carry a derivative
   obligation per [PIPELINE-DECISIONS.md §4](../../../PIPELINE-DECISIONS.md);
   the answer should land in `paper.meta.json` *before* downstream
   artifacts that would inherit the license get produced.

## Steps Claude takes

1. **Confirm pdf-sidecar is up.** `GET http://localhost:6001/api/health` —
   expect `{ok: true, root: <repo>}`. If down, ask the user to run
   `start-servers.bat` (the sidecar's the Window 2 process). Don't try to
   spawn it from this skill.
2. **Pick `out_dir`.** Default to `papers/<slug>/`. If the slug already has
   a `paper.md`, ask the user whether to overwrite — `pdf-to-markdown` is
   idempotent in shape but the sha will change, invalidating any downstream
   artifacts that pinned the previous hash.
3. **POST to `/extract`.** Body:
   ```json
   {"pdf_path": "<resolved path>", "slug": "<slug>", "out_dir": "papers/<slug>"}
   ```
   `extract_images` defaults false. Expect a response of:
   ```json
   {
     "ok": true,
     "paper_md": "papers/<slug>/paper.md",
     "paper_md_sha256": "...",
     "paper_spans": "papers/<slug>/paper.spans.json",
     "paragraph_count": N
   }
   ```
4. **Spot-check the contract.** Read the produced files and verify:
   - Each line matching `/<!-- p:(\d+) -->/` has a sequential id starting
     from 1 with no gaps.
   - `paragraph_count` matches the number of anchor lines.
   - `paper.md.sha256` matches the actual hash of `paper.md` (Python
     `hashlib.sha256(open(path,'rb').read()).hexdigest()`).
   - For two random paragraph ids, the `paper.spans.json` offsets actually
     bracket the corresponding paragraph text in `paper.md` when read as
     UTF-8 bytes.
   - If any check fails, report the discrepancy and stop. Don't silently
     retry — the sidecar is supposed to be deterministic; a failure is a
     bug in the sidecar or a corrupted input PDF, not something to paper
     over.
5. **Write `paper.meta.json` if missing.** Minimum shape (from
   [input/paper_json_spec.md](../../../input/paper_json_spec.md)):
   ```json
   {
     "title": "...",
     "authors": ["..."],
     "year": YYYY,
     "doi": "...",
     "source_url": "...",
     "license": "CC BY 4.0" | "CC BY-NC-SA 4.0" | other
   }
   ```
   Pull title/authors/year/DOI from the user, or from a first-page
   regex if unambiguous. Don't fabricate fields.
6. **Report back** with the four file paths, the paragraph count, the
   sha (first 8 chars is enough for chat), and a one-line nudge toward the
   next skill (highlights-overlay or podcast-scripter).

## Idempotence and re-runs

`paper.md` is immutable per [SKILLS-PLAN.md §0](../../../SKILLS-PLAN.md) —
if you re-extract the same PDF you'll get a different sha (line endings,
PyMuPDF version), which invalidates every downstream artifact that pinned
the previous hash. Treat re-extraction as a deliberate user choice, not a
silent retry path.

## Failure modes to recognize

- **404 from sidecar (`pdf not found`)** — the path didn't resolve. Most
  often the user passed a relative path that's not relative to the repo
  root. Resolve it once via `os.path.abspath` and retry, or surface the
  resolved path so the user sees what was searched.
- **500 from sidecar with `pymupdf4llm not installed`** — the venv at
  `pdf-sidecar/.venv` is missing or incomplete. Tell the user to re-run
  `pdf-sidecar/.venv/Scripts/pip install -r pdf-sidecar/requirements.txt`.
- **Paragraph IDs not sequential** — bug in the sidecar's
  `_anchor_paragraphs` post-processor; report and stop.
- **Empty `paragraph_count`** — usually a scanned PDF with no embedded
  text. OCR is out of scope for this skill; tell the user and suggest
  `marker-pdf` as the upgrade path (see `pdf-sidecar/requirements.txt`
  comment).

## What this skill explicitly does *not* do

- Section identification. The next skill reads `paper.md` and adds
  section boundaries to `paper.spans.json`.
- Image extraction. `extract_images` is a reserved field in the sidecar
  request; lights up in a follow-up commit.
- Migrating existing `input/<slug>_paper.json` files. That's
  `scripts/json_paper_to_md.py` territory (planned, not built yet).
