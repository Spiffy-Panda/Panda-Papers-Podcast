# Productivity & Reading Helper — Project Context

## What this is

A local toolkit for working through academic papers: PDF → Markdown working
copy → cross-paper openCypher graph + skim-highlight overlay + two-voice
podcast script → audio with persona-distinct voices. The whole flow is
**interactive** — the user (Panda) drives it via chat, the director skill
calls tools, intermediate artifacts are reviewed before the next step.

Audio rendering and voice infrastructure are **shared with the sibling
project [`ai-verbal-coaching`](../ai-verbal-coaching/)** (Voice Coach) via a
path-referenced C# library at `../ai-verbal-coaching/shared/Tts/Tts.csproj`.
This implies both repos live under the same parent directory (`UW Winter 26/`).

See [PLAN.md](PLAN.md) for the original (paper-JSON-era) design;
[SKILLS-PLAN.md](SKILLS-PLAN.md) for the current PDF-era architecture;
[DEV-LOG.md](DEV-LOG.md) for session history (read the top entry to load
recent context).

## Who's using this

Panda (Brian / Panda Notarianni, handle `cptspiffypanda`). HCDE graduate
student at UW, Graduate Certificate in Human-Centered AI. Active research
interest: AI alignment, mechanistic interpretability, activation steering.

**Accessibility / preferences that matter for any UI in this project:**

- Dyslexic. **Always** use sans-serif typography in rendered HTML —
  Atkinson Hyperlegible (preferred) or Lexend. Fall back to system sans-serif.
- Avoid tight letter-spacing. Avoid serif fonts for body or headings unless
  explicitly requested.
- Generous line-height (≥1.5).
- `panda_reader.html` is named after this need — the highlights overlay
  (from `highlights-overlay` SKILL.md) is meant to layer on top.

## Hardware / environment

- Windows desktop, NVIDIA Titan XP (12 GB VRAM, Pascal, CUDA capable).
- Existing Claude Desktop setup with custom MCP servers (Gmail, Obsidian,
  Godot). Copilot key remapped via AutoHotkey to open Claude Desktop.
- Active in C#/.NET (Voice Coach, Godot 4.6.1 Mono, ElectronicSpice,
  Autonome). Polyglot is the comfortable mode, not a stretch.

## Architecture (target end state)

```
┌──────────────────┐   MCP (Streamable HTTP)   ┌─────────────────────┐
│  Claude Code     │◄──────────────────────────►│  paper-coach C#     │
│  (chat driver)   │   :6000/mcp                │  - MCP endpoint     │
└──────────────────┘                            │  - Workspace verbs  │
        │                                       │  - Audio rendering  │
        │                                       └─────────┬───────────┘
        ▼ shells subprocess / HTTP                        │
┌──────────────────┐                              HTTP    │
│  pdf-sidecar     │◄─────────────────────────────────────┤
│  (Python FastAPI │                                      │
│   :6001)         │                                      ▼
└──────────────────┘                            ┌─────────────────────┐
                                                │  shared/Tts (C#)    │
                                                │  - Speaker (SAPI)   │
                                                │  - NaturalSpeaker   │
                                                │    (WinRT neural)   │
                                                └─────────────────────┘
                                                  (sibling repo)
```

The C# server is the orchestrator and MCP host. The Python sidecar exists
only where Python has a real ecosystem advantage (PDF→MD via `pymupdf4llm`,
`marker-pdf`). TTS is C# because System.Speech and Windows.Media.SpeechSynthesis
are first-class there.

## Coding conventions for this project

- **C#**: minimal API style (top-level statements in `Program.cs`), nullable
  reference types enabled, async by default for I/O. Targets
  `net9.0-windows10.0.19041.0` so WinRT projections are available.
- **Python**: type hints on public functions, FastAPI conventions.
- **HTML/CSS/JS**: vanilla, no frameworks for now. Sans-serif fonts as noted
  above. Single-file pages where reasonable.
- **No telemetry, no cloud calls.** Papers and audio stay local.
- Comments explain *why*, not *what*.

## DEV-LOG.md format

Reverse-chronological session journal. Newest entries on top. Write before
every commit. The audience is a future Claude session (or yourself a week
from now) reading the top of the file to load context — not someone running
`git log`. Commit messages describe one diff in imperative tense; DEV-LOG
entries describe an arc across one or more commits in narrative tense: what
was tried, what was abandoned, what this unblocks downstream, what's
deferred. A single entry will often span 2–4 commits when they belong to one
coherent push. Capture things commits structurally cannot: hypotheses ruled
out, cross-refs to design notes, follow-up affordances ("the next slice
should…"), policy checks (license/fair-use/security). Format:
`## YYYY-MM-DD — <slug>` headers, newest on top, markdown links to other
docs encouraged. Headline sentence often duplicates the commit summary —
that's fine; DEV-LOG is the index a fresh agent reads to orient.

Convention lifted from `../ai-verbal-coaching/CLAUDE.md` and applied here
going forward. Existing terser entries stay.

## Claude Code integration

This repo will register a project-scope MCP server at
`http://localhost:6000/mcp` via `.mcp.json` once `paper-coach` is
implemented. Boot order: start `pdf-sidecar` (port 6001) and `paper-coach`
(port 6000) via `start-servers.bat`, then start Claude Code in this repo. If
`.mcp.json` is new or changed, Claude Code may prompt to trust the server.

The `paper-coach` MCP tools (see [SKILLS-PLAN.md §2.1](SKILLS-PLAN.md)) are
how the director skill navigates: `list_papers`, `find_papers`, `select`,
`extract`, `render_audio`, `list_voices`, etc. LLM-driven worker skills
(highlights, cypher, scripter) call these tools to read/write artifacts.

## Running the project (target — once servers exist)

```powershell
# From repo root:
.\start-servers.bat
# Opens two PowerShell windows, tees logs to logs\*.log.
# paper-coach on :6000, pdf-sidecar on :6001.
```

Quick reference for current (Python-only) artifacts during the transition:

```powershell
# Existing podcast player (paper-JSON era):
python server.py     # serves podcast_player.html + manifest/state endpoints
```
