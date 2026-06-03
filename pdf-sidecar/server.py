"""
pdf-sidecar — FastAPI service exposing PDF -> Markdown extraction on :6001.

Owns the parts of the pipeline where Python's ecosystem (PyMuPDF, transformers
for marker-pdf later, etc.) genuinely wins. Everything else lives in paper-coach
(the C# MCP server on :6000) — this sidecar is reachable from there over HTTP.

Endpoints:
    GET  /api/health    Liveness probe — start-servers.bat polls this.
    POST /extract       PDF -> paper.md + paper.spans.json (+ optional images).

The paper.md format matches SKILLS-PLAN.md §0:
    <!-- p:1 -->
    First paragraph text...

    <!-- p:2 -->
    Second paragraph text...

Anchors are HTML comments so any markdown renderer ignores them, but they're
easy to find with /<!-- p:(\\d+) -->/g. paper.spans.json carries byte offsets
into paper.md for char-count joins (highlight overlays, audio sync).
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


log = logging.getLogger("pdf-sidecar")

# Repo root resolution mirrors paper-coach (Program.cs): explicit env var wins
# so the launcher's working directory doesn't matter, fall back to cwd. The
# C# server uses PAPER_COACH_ROOT; share it here so start-servers.bat doesn't
# need a second variable for a sibling process under the same repo.
_repo_root_env = (
    os.environ.get("PAPER_COACH_ROOT")
    or os.environ.get("PDF_SIDECAR_ROOT")
    or os.getcwd()
)
REPO_ROOT = Path(_repo_root_env).resolve()

app = FastAPI(title="pdf-sidecar", version="0.1.0")


class ExtractRequest(BaseModel):
    """Input shape for /extract.

    pdf_path is resolved relative to REPO_ROOT if not absolute. out_dir
    defaults to papers/<slug>/ under REPO_ROOT, matching the new pipeline's
    on-disk layout (SKILLS-PLAN.md §1). Slug is mandatory because it picks
    the default out_dir and goes into paper.spans.json as the join key.
    """

    pdf_path: str = Field(..., description="Path to source PDF (abs or repo-relative).")
    slug: str = Field(..., description="Paper slug — used for default out_dir and span ids.")
    out_dir: Optional[str] = Field(
        default=None,
        description="Where paper.md / paper.spans.json / paper.images/ land. "
        "Defaults to papers/<slug>/ under repo root.",
    )
    extract_images: bool = Field(
        default=False,
        description="Reserved — pymupdf4llm image extraction lands in a "
        "follow-up commit; currently ignored.",
    )


class ExtractResponse(BaseModel):
    ok: bool
    paper_md: str
    paper_md_sha256: str
    paper_spans: str
    paragraph_count: int
    reason: Optional[str] = None


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "root": str(REPO_ROOT)}


@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest) -> ExtractResponse:
    """Render a PDF to paper.md + paper.spans.json under out_dir.

    The implementation is intentionally minimal for the scaffold pass:
    pymupdf4llm gives us markdown, we split on blank lines into paragraphs,
    prepend each with `<!-- p:N -->`, and record byte offsets in spans.
    Image extraction, footnote handling, table fidelity, and per-section
    metadata are deferred to the pdf-to-markdown SKILL.md round-trip.
    """

    pdf_abs = _resolve_under_root(req.pdf_path)
    if not pdf_abs.exists():
        raise HTTPException(status_code=404, detail=f"pdf not found: {pdf_abs}")

    out_dir = (
        _resolve_under_root(req.out_dir)
        if req.out_dir
        else REPO_ROOT / "papers" / req.slug
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # Import here so /api/health stays responsive even if pymupdf4llm fails
    # to import (e.g., wheel install half-done). Sidecar can report its own
    # liveness without the heavy dependency loaded.
    try:
        import pymupdf4llm  # type: ignore
    except ImportError as ex:
        raise HTTPException(
            status_code=500,
            detail=f"pymupdf4llm not installed in this venv ({ex}). "
            "See pdf-sidecar/requirements.txt.",
        ) from ex

    raw_md = pymupdf4llm.to_markdown(str(pdf_abs))
    anchored_md, paragraph_count, spans = _anchor_paragraphs(raw_md)

    paper_md_path = out_dir / "paper.md"
    paper_md_bytes = anchored_md.encode("utf-8")
    paper_md_path.write_bytes(paper_md_bytes)

    sha = hashlib.sha256(paper_md_bytes).hexdigest()
    (out_dir / "paper.md.sha256").write_text(sha + "\n", encoding="utf-8")

    spans_path = out_dir / "paper.spans.json"
    spans_doc = {
        "slug": req.slug,
        "paper_md_sha256": sha,
        "paragraphs": spans,
    }
    import json

    spans_path.write_text(
        json.dumps(spans_doc, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    log.info(
        "extracted %s -> %s (%d paragraphs, sha %s...)",
        pdf_abs, paper_md_path, paragraph_count, sha[:8],
    )

    return ExtractResponse(
        ok=True,
        paper_md=_relpath(paper_md_path),
        paper_md_sha256=sha,
        paper_spans=_relpath(spans_path),
        paragraph_count=paragraph_count,
        reason=None if req.extract_images is False
        else "extract_images is reserved for a follow-up commit; ignored.",
    )


# ---- helpers ---------------------------------------------------------------

# Blank-line paragraph split. pymupdf4llm emits markdown with double-newline
# paragraph separators; this is the same convention. Triple+ newlines collapse
# to one separator — preserves a single blank line between paragraphs in the
# anchored output without ballooning multi-blank runs into empty paragraphs.
_PARAGRAPH_SEP = re.compile(r"\n\s*\n+")


def _anchor_paragraphs(raw_md: str) -> tuple[str, int, list[dict]]:
    """Insert `<!-- p:N -->` anchors before each non-empty paragraph and
    track byte offsets for paper.spans.json.

    Each span is `{id, start_offset, end_offset}` where the offsets bracket
    the paragraph body (not the anchor line). Offsets are byte indices into
    the returned paper.md when encoded as UTF-8 — same encoding the C#
    Workspace.cs reader expects.
    """

    paragraphs = [p.strip() for p in _PARAGRAPH_SEP.split(raw_md)]
    paragraphs = [p for p in paragraphs if p]

    out_lines: list[str] = []
    spans: list[dict] = []
    byte_cursor = 0
    for idx, para in enumerate(paragraphs, start=1):
        anchor = f"<!-- p:{idx} -->\n"
        out_lines.append(anchor)
        byte_cursor += len(anchor.encode("utf-8"))

        body = para + "\n"
        start = byte_cursor
        out_lines.append(body)
        byte_cursor += len(body.encode("utf-8"))

        spans.append({
            "id": idx,
            "start_offset": start,
            "end_offset": byte_cursor - 1,  # exclude trailing newline
        })

        # Blank separator line between paragraphs (matches input style).
        out_lines.append("\n")
        byte_cursor += 1

    return "".join(out_lines), len(paragraphs), spans


def _resolve_under_root(rel_or_abs: str) -> Path:
    p = Path(rel_or_abs)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


def _relpath(p: Path) -> str:
    try:
        return str(p.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")
