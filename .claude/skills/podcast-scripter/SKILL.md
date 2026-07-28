---
name: podcast-scripter
description: Turn papers/<slug>/paper.md into a two-presenter dialog script (papers/<slug>/podcast/script.json) in the multi-part render_audio input shape. Coordinator plans parts and personas, fans out one Sonnet writer subagent per part, reviews drafts against the persona-rotation rule, stitches the final script in one invocation. Use when the user asks to write a podcast script, script a paper, run podcast-scripter, or turn a paper.md into dialog.
---

# podcast-scripter — plan parts, fan out writers, own the rotation gate

This skill is the middle of the pipeline: `paper.md` in, renderable dialog
script out. The invoking session acts as **coordinator** — it plans parts
from the paper's sections, picks the per-paper persona rotation dimension,
writes the persona briefs, and spawns one Sonnet writer subagent per part
per [PIPELINE-DECISIONS §"Scripter model tier"](../../../PIPELINE-DECISIONS.md).
The writers turn assigned paragraphs into dialog lines; the coordinator
reviews, stitches, and writes one `script.json`.

Whole paper, one invocation. There is **no resume routine** — the legacy
`podcast_generation_state.json` dance was a length-limit workaround, not a
design (see [PIPELINE-DECISIONS §"Generation cadence"](../../../PIPELINE-DECISIONS.md)).
Length is handled by fanning out more subagents, never by writing state
files and asking the user to re-invoke.

## When to invoke

- "write the podcast script for <slug>"
- "script <slug>"
- "run podcast-scripter on <slug>"
- "turn paper.md into a dialog"

## Inputs

1. **Slug** — the paper must already be through `pdf-to-markdown`:
   `papers/<slug>/paper.md`, `paper.md.sha256`, and `paper.spans.json`
   must exist. If they don't, stop and point at
   [pdf-to-markdown](../pdf-to-markdown/SKILL.md) first.
2. **`paper.spans.json`** — prefer the `sections` annotation when present
   (added by the section-identification pass). Sections are the natural
   part boundaries. If `sections` is absent, fall back to planning from
   markdown headings in `paper.md` directly — note the fallback to the
   user, since heading-based boundaries are less reliable on OCR'd papers.
3. **`paper.meta.json` → `license`** — the script is a derivative and
   inherits the paper's license. Two rules from
   [PIPELINE-DECISIONS §"Licensing of derivatives"](../../../PIPELINE-DECISIONS.md):
   - **CC BY-NC-SA 4.0** papers (currently ODESteer and RLHF Shallow
     Alignment): before writing `script.json`, create or update
     `papers/<slug>/podcast/LICENSE.md` following the pattern in
     [output/odesteer/LICENSE.md](../../../output/odesteer/LICENSE.md),
     and check whether [NOTICES.md](../../../NOTICES.md) needs a new
     attribution layer.
   - **License field missing** — stop and ask. Don't guess, don't default
     to CC BY; the derivative chain downstream (audio) inherits whatever
     lands here.
4. **Optional `highlights.json`** — if present, `must-read` tiers get
   fuller dialog coverage and `skip` tiers get compressed or dropped.
   Absence is fine; plan from sections alone.
5. **Target size** — legacy papers ran 5–18 parts. Default: derive from
   paragraph count at roughly 3–7 paragraphs per part, splitting at
   section boundaries, aiming for ~2–5 minutes of dialog per part
   (~20–30 lines). The user can override part count or total length;
   record any override in the report-back so a regen can reproduce it.

## Steps Claude takes

1. **Verify the checksum.** `paper.md.sha256` must match the actual hash
   of `paper.md`, and `paper.spans.json.paper_md_sha256` must agree. A
   mismatch means the working copy moved under the pinned artifacts —
   stop and report; re-annotation is upstream's job, not this skill's.
2. **Plan parts (coordinator, session model).** Walk sections (or
   headings) and assign contiguous paragraph-id ranges to parts. Every
   paragraph should be assigned exactly once — coverage gaps are how
   papers get silently misrepresented. Front-load an intro beat in part 1
   (title, authors, year, why-this-paper) and a wrap-up beat in the last
   part.
3. **Pick the rotation dimension and cast the voices (coordinator).**
   Choose one dimension from
   [PIPELINE-DECISIONS §"Two-presenter podcast persona rotation"](../../../PIPELINE-DECISIONS.md)
   — math/engineering vs. social theory, autistic vs. allistic framing,
   ADHD-analogies vs. by-the-text, expert vs. generalist, skeptic vs.
   enthusiast, or a blend that fits the paper — and decide **which voice
   takes which side**. Either voice can take either side; check what
   recent papers used and vary. Get exact installed voice names from
   paper-coach's `list_voices` MCP tool (e.g. "Microsoft David Desktop",
   "Microsoft Zira Desktop" — the `Desktop` suffix varies by machine, so
   don't hardcode from memory). Write one **persona brief** per speaker:
   2–4 sentences covering their side of the dimension, their register,
   and what kinds of lines they own. The briefs become the `persona`
   fields in the output.
4. **Fan out writer subagents — one per part, `model: "sonnet"`.**
   Spawn them in parallel via the `Agent` tool. Writers target Sonnet per
   [PIPELINE-DECISIONS §"Scripter model tier"](../../../PIPELINE-DECISIONS.md);
   the coordinator stays on the session model. Each writer's prompt is
   self-contained and carries:
   - The part's paragraph text, **with the `<!-- p:N -->` anchor ids
     visible** so the writer can tag lines without guessing.
   - Both persona briefs and which voice speaks which persona.
   - `part_of: {n, total}` and one line of adjacent-part context
     (what the previous part ended on, what the next part covers) so
     transitions don't repeat or contradict.
   - Hard requirements, stated as requirements: every line carries
     `source_paragraphs` (integer ids from the anchors it draws on); no
     facts that aren't in the assigned paragraphs; conversational
     register, not read-aloud prose; roughly N lines (from the plan);
     both speakers ask *and* explain — neither voice is the designated
     question-asker.
   - Output format: a JSON array of
     `{"voice": "...", "text": "...", "source_paragraphs": [int]}`.
5. **Review each draft against the rotation rule (coordinator).** This
   skill is the **first gate**; `script-to-audio` re-checks before render
   with block-with-override, but a draft that fails here should never
   reach that gate. Count questions and explanatory cues per voice. If
   Zira-asks/David-explains is the constant pattern for more than roughly
   half the lines — as it is in the legacy
   [input/great_plea/part_01.json](../../../input/great_plea/part_01.json),
   which is the specimen of the bug — that draft is a **regen, not a
   good-enough**. Regenerate with a sharpened brief (name the failure:
   "Zira asked 9 of 11 questions; give her the explanatory lines on
   sections X and Y"). Also check: every line has non-empty
   `source_paragraphs` within the part's assigned range, and no
   fabricated claims (spot-check lines against the paragraphs they cite).
6. **Stitch into one `script.json` (coordinator).** Multi-part
   render_audio input shape per
   [PIPELINE-DECISIONS §"render_audio I/O contract"](../../../PIPELINE-DECISIONS.md):
   ```json
   {
     "paper_slug": "<slug>",
     "speaker_a": {"voice": "Microsoft David Desktop", "persona": "<brief A>"},
     "speaker_b": {"voice": "Microsoft Zira Desktop", "persona": "<brief B>"},
     "parts": [
       {
         "part_of": {"n": 1, "total": 5},
         "pause_between_ms": 600,
         "rate": 0,
         "lines": [
           {"voice": "Microsoft David Desktop",
            "text": "...",
            "source_paragraphs": [1, 2]}
         ]
       }
     ]
   }
   ```
   Reference the paper by `paper_slug`, never by path. Per-part
   `pause_between_ms` / `rate` are optional overrides — omit unless the
   plan calls for them.
7. **Write to `papers/<slug>/podcast/script.json`.** This matches the
   [SKILLS-PLAN §1](../../../SKILLS-PLAN.md) layout and means
   `script-to-audio`'s conventional `out_dir` (`papers/<slug>/podcast/`)
   has the renderer **augment this same file in place** — the output
   contract is input-shape-plus-additions (`start_ms`/`end_ms`, `wav`,
   `rendered_utc`), so the overwrite is lossless and the player reads one
   file whether or not the render has happened yet. Don't invent a
   separate pre-render filename.
8. **Report back** with the file path, part count, per-part line counts,
   the rotation dimension chosen and which voice took which side, the
   license carried (and LICENSE.md written, if BY-NC-SA), and a nudge
   toward [script-to-audio](../script-to-audio/SKILL.md).

## Failure modes to recognize

- **`paper.md` or `paper.spans.json` missing** — the paper hasn't been
  through `pdf-to-markdown`. Stop and point there; don't scrape the PDF
  yourself.
- **No `sections` annotation in `paper.spans.json`** — fall back to
  heading-based part planning from `paper.md`. Tell the user; suggest
  running the section-annotation pass if the headings look unreliable.
- **Writer draft fails rotation review** — regen that part with a
  sharpened brief naming the specific failure. Escalate the writer to the
  coordinator's tier only after repeated failure on the same part —
  escalation is an exception path, not the default.
- **License missing from `paper.meta.json`** — stop and ask before
  writing any output. The script inherits the license; producing an
  unlicensed derivative is worse than a delay.
- **Context-bust on a huge paper** — the answer is always *more, smaller
  parts* (thinner paragraph ranges per writer), never a resume state
  file. If even the coordinator's planning pass strains, plan from the
  section list alone without reading full paragraph bodies — the writers
  read the bodies, not the coordinator.
- **Writer emits lines without `source_paragraphs` or citing paragraphs
  outside its range** — schema violation, regen. Don't patch ids in by
  hand; a writer that lost track of anchors has probably also drifted
  from the text.

## What this skill explicitly does *not* do

- Render audio. That's [script-to-audio](../script-to-audio/SKILL.md) —
  it re-checks rotation and calls paper-coach's `render_audio`.
- Generate `highlights.json` (that's `highlights-overlay`) or
  `graph.cypher` (that's `paper-to-cypher`, and it's a stretch goal —
  never block scripting on it).
- Edit `paper.md`. The working copy is immutable; if the markdown is
  wrong, that's an upstream re-extraction, which invalidates everything
  pinned to the old sha.
- Resolve voice-name variants. Emit the names `list_voices` reported;
  the renderer's substring fallback handles the rest.
