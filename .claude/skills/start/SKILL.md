---
name: start
description: Render a terminal-style project welcome/status dashboard showing in-flight papers, skill readiness, infrastructure progress, and suggested next actions. Trigger on /start, /status, /welcome, or natural-language asks like "show project status", "what's the state of the project", "what should I work on next", "dashboard". Optional subcommands: status (dashboard only, skip next-actions), fresh (recommend a new paper from PDF), resume (jump into the highest-priority in-flight paper).
---

# /start — Project Dashboard

Render a terminal-style welcome screen for the Productivity & Reading Helper
project. The dashboard combines a live scan of paper artifacts on disk with
declared readiness from [STATUS.json](../../../STATUS.json).

## What to render

A single ASCII box, 72 columns wide, with four sections in order:

1. **PAPERS IN FLIGHT** — every paper detected on disk, with progress bar
   and a short state label.
2. **SKILLS** — each entry in `STATUS.json` `skills`, alphabetical except
   `start` first. Phase icon, percent bar, name, blockers (if any).
3. **INFRASTRUCTURE** — each entry in `STATUS.json` `infrastructure`,
   in the order declared.
4. **WHAT'S NEXT** — items from `STATUS.json` `next_actions` (1-3 lines).
   Omit this section if subcommand is `status`.

End with a short `Try:` block listing follow-up commands.

## How to compute paper state (live, every render)

For each candidate paper slug (union of `input/*_paper.json` stems,
`input/<slug>/` dirs, `output/<slug>/` dirs, and `papers/<slug>/` if
present):

1. **Planned parts (N)** — count of `input/<slug>/part_*.json` files; if
   that path doesn't exist, fall back to count of
   `output/<slug>/dialog_part_*.json`; if neither, N is `?`.
2. **Rendered parts (M)** — count of `output/<slug>/part_*.wav` (the new
   pipeline goes under `papers/<slug>/podcast/part_*.wav`, check both).
3. **State label:**
   - If `podcast_generation_state.json` references this paper AND its
     `status` is `complete`, label `complete`.
   - Else if M ≥ N and N is not `?`, label `complete`.
   - Else if M > 0, label `in progress`.
   - Else if N != `?`, label `pending`.
   - Else label `unknown`.

Render `M/N parts` and a 10-cell progress bar (`M/N` filled). When N is `?`,
show `M/?` and a bar based on `min(M, 10)` filled cells.

## ASCII style

- Outer frame: `╔ ╗ ╚ ╝ ═ ║` corners and edges, `╠ ╣` for section dividers.
- Inner section underlines: a row of `─` directly under each section title.
- Progress bars: exactly 10 cells, `█` filled, `░` empty, wrapped in `[ ]`.
  Example: `[██████░░░░]`.
- Phase icons from `STATUS.json.phases[*].icon` (`·` planned/not-started,
  `▸` scaffolded, `▶` functional, `✓` complete).
- Sans-serif assumption — the user's terminal/chat is monospaced;
  proportional spacing would break alignment. If output appears misaligned in
  the user's renderer, fall back to a plain markdown table.
- 2-space left padding inside the box. Column alignment matters; pad names
  with spaces so progress bars line up vertically within each section.

## Skeleton (copy and fill in)

```
╔══════════════════════════════════════════════════════════════════════╗
║  PRODUCTIVITY & READING HELPER                              v0.1     ║
║  paper podcast pipeline                                    2026-06-02 ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  PAPERS IN FLIGHT                                                    ║
║  ────────────────                                                    ║
║  great_plea                  17/17  [██████████]  complete           ║
║  responsible_ux              18/18  [██████████]  complete           ║
║  odesteer                    12/12  [██████████]  complete           ║
║  identifiability              6/?   [██████░░░░]  in progress        ║
║  steering_awareness           5/5   [██████████]  complete           ║
║  roadmap_to_pluralistic_…     0/?   [░░░░░░░░░░]  pending            ║
║                                                                      ║
║  SKILLS                                                              ║
║  ──────                                                              ║
║  ▶  start              [██████████]  functional                      ║
║  ·  paper-director     [░░░░░░░░░░]  planned     ← paper-coach       ║
║  ·  pdf-to-markdown    [░░░░░░░░░░]  planned     ← pdf-sidecar       ║
║  ·  paper-to-cypher    [░░░░░░░░░░]  planned                         ║
║  ·  highlights-overlay [░░░░░░░░░░]  planned                         ║
║  ·  podcast-scripter   [░░░░░░░░░░]  planned                         ║
║  ·  script-to-audio    [░░░░░░░░░░]  planned     ← shared TTS        ║
║                                                                      ║
║  INFRASTRUCTURE                                                      ║
║  ──────────────                                                      ║
║  ✓  legacy pipeline                       [██████████]  100%         ║
║  ✓  design docs                           [██████████]  100%         ║
║  ·  shared TTS library                    [░░░░░░░░░░]    0%         ║
║  ·  paper-coach C# server                 [░░░░░░░░░░]    0%         ║
║  ·  pdf-sidecar Python                    [░░░░░░░░░░]    0%         ║
║  ·  papers/<slug>/ layout                 [░░░░░░░░░░]    0%         ║
║  ·  .mcp.json + start-servers.bat         [░░░░░░░░░░]    0%         ║
║                                                                      ║
║  WHAT'S NEXT                                                         ║
║  ───────────                                                         ║
║  → Extract shared TTS to ../ai-verbal-coaching/shared/Tts/           ║
║  → Scaffold paper-coach with one MCP tool (list_papers)              ║
║  → Pick a small paper to bring up first under the new pipeline       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

Try:
  /start status     dashboard only, no next-actions section
  /start fresh      walk me through bringing up a new paper from PDF
  /start resume     jump into the highest-priority in-flight paper
```

The skeleton is a target, not a literal — recompute paper rows from disk on
every invocation. Skill + infrastructure rows are read from `STATUS.json`;
do NOT hardcode them in this skill.

## Subcommand behavior

- **(none)** — full dashboard above.
- **`status`** — same dashboard, omit WHAT'S NEXT and the Try: block.
- **`fresh`** — render dashboard, then propose three small/quick papers to
  start with (favor those with `paper.md` already implied by short `input/`
  trees), and walk the user through PDF intake conversationally.
- **`resume`** — render dashboard, then pick the paper with state
  `in progress` and the highest M/N ratio; offer to pick up where the user
  left off (e.g. "identifiability is at 6/?; want to plan more parts, render
  the next one, or audit what's there?").

## Truncation rules

- Paper slugs longer than 28 characters get truncated with `…` to keep
  columns aligned.
- Blockers list is shown abbreviated as `← <first blocker>` after the
  phase label; if there are multiple blockers, append `(+N more)`.
- If `STATUS.json` has fewer skills/infra rows than the skeleton shows,
  shrink the section — don't pad with placeholders.

## When STATUS.json is stale

If the dashboard would show all-zero progress but the user has been
clearly working (DEV-LOG.md has recent entries beyond the
`last_updated` date in STATUS.json), surface a one-line nudge at the
bottom: `⚠ STATUS.json may be stale — last updated 2026-06-02, latest
DEV-LOG entry is YYYY-MM-DD.` The user updates STATUS.json by hand; the
nudge prompts them rather than auto-editing.
