# DEV-LOG

A running log of what's been built, why, and what the formats look like.
Append-only — newest entries on top. Each entry: date, what changed, why.

---

## Current Pipeline (as of 2026-06-01)

```
  Paper PDF (manual)
        │
        ▼  (manual transcription per input/paper_json_spec.md)
  input/<paper>_paper.json          ← faithful-summary paragraphs, global int IDs
        │
        ▼  init_podcast.py
  podcast_generation_state.json     ← paper-agnostic "what to generate next"
  output/<paper>/manifest.json      ← per-paper index of parts
        │
        ▼  (Claude Desktop scheduled prompt, reads state file)
  input/<paper>/part_NN.json        ← two-voice dialog, lines tagged source_paragraphs
        │
        ▼  dialog_to_audio.py
  output/<paper>/part_NN_<ts>.wav
  output/<paper>/part_NN_<ts>_timestamps.json
        │
        ▼  server.py + podcast_player.html
  Split-pane web player: paper-left, dialog-right, scroll-synced by source_paragraphs
```

### Component map

| File | Role |
|---|---|
| `input/paper_json_spec.md` | Canonical spec for paper JSON: meta + sections + paragraphs with global integer IDs |
| `input/<paper>_paper.json` | Single paper, conforming to spec |
| `input/<paper>/prompt_template.txt` | Per-paper podcast-generation prompt with `{...}` variables |
| `init_podcast.py` | Splits a paper into planned parts, writes `podcast_generation_state.json` + initial manifest |
| `podcast_generation_state.json` | Paper-agnostic generation state (only one active paper at a time) |
| `dialog_to_audio.py` | Renders a dialog JSON to WAV + per-line timestamps using Windows SAPI voices |
| `output/<paper>/manifest.json` | Index of generated parts (paragraphs covered, audio + timestamp paths, status) |
| `server.py` | Local server: serves players, manifest + state endpoints |
| `podcast_player.html` | Split-pane player: paper text left, dialog right, sync via `source_paragraphs` |
| `dialog_player.html` | Original single-pane dialog player (kept for parity) |
| `panda_reader.html` + `dyslexia.{css,js}` | Skim-helper reader for paper text (font, spacing, bionic-style emphasis) |
| `index.html` + `app.js` + `style.css` | Landing page |
| `PLAN.md` | Original design doc — schemas, lifecycle, stretch goals (full-paper TTS, Reading tab) |

### Data contracts in one place

**Paragraph IDs are globally sequential integers**, starting at 1, no gaps,
shared across all sections of a paper. They are the join key for everything:
- Dialog lines reference them via `source_paragraphs: [int]`
- Timestamps pass them through unchanged
- Player uses them to scroll the paper pane in sync with audio

**One paper at a time per state file.** Multi-paper simultaneous tracking is
out of scope by design — create a new state file to switch.

**Status values** in `podcast_generation_state.json`: `ready`, `generating`,
`complete`, `error`.

### Papers processed so far

| Paper | Parts | Notes |
|---|---|---|
| great_plea | 17 | First paper end-to-end |
| responsible_ux | 18 | |
| odesteer | 12 | Dialog JSONs live under `output/odesteer/dialog_part_*.json` (early variant of input layout) |
| identifiability | 6 | Same dialog-under-output variant |
| roadmap_to_pluralistic_alignment | — | input/output dirs exist; not audited here |
| steering_awareness | 5 | Most recent; state file marks `complete` |

### Known quirks (not bugs to fix without intent)

- `steering_awareness` state shows `current_part: 6, total_planned_parts: 5` —
  generator overshoots by one before flipping `status` to `complete`. Harmless
  given empty `remaining_paragraph_ids`.
- Two on-disk layouts for dialog inputs: newer papers under `input/<paper>/part_NN.json`,
  earlier `odesteer`/`identifiability` under `output/<paper>/dialog_part_NN.json`.
  The newer layout (PLAN.md §6) is canonical.
- Pipeline starts from manually-authored paper JSON. PDF → JSON is an unautomated
  gap — see SKILLS-PLAN.md for the proposed replacement that starts from PDF.

---

## Entries

### 2026-06-02 — shared TTS library extracted; infrastructure step 1 done

Lifted Voice Coach's `Speaker.cs` into a new path-referenced library
at [`../ai-verbal-coaching/shared/Tts/Tts.csproj`](../ai-verbal-coaching/shared/Tts/Tts.csproj).
This was the gating first step from [SKILLS-PLAN.md §9](SKILLS-PLAN.md):
every subsequent `paper-coach` milestone (server scaffold,
`render_audio`, `script-to-audio` skill) was blocked on a stable
shared TTS, and now that library exists. The full extraction lives
in the sibling repo's commit `a84f36a`; this repo has no code yet,
only doc/status updates.

What the sibling commit did, summarized:

- `Speaker.cs` moved into `shared/Tts/`, namespace
  `VoiceCoach.Server.Services` → `Tts`. `SpeakResult` record moved
  with it.
- New `shared/Tts/Tts.csproj` using `Microsoft.NET.Sdk` (not `.Web`),
  targets `net9.0-windows`, depends on `System.Speech` and
  `Microsoft.Extensions.Logging.Abstractions`. The Logging package
  is the catch — Web SDK pulled it implicitly via ImplicitUsings;
  library SDK doesn't, so explicit pkg ref + explicit
  `using Microsoft.Extensions.Logging;` at the top of Speaker.cs.
- Voice Coach's `VoiceCoach.Server.csproj` swapped its direct
  `System.Speech` package ref for a `<ProjectReference>` to the new
  library. `Program.cs` and `VoiceCoachTools.cs` got `using Tts;`.
- `dotnet build` succeeded, 0 warnings — both `Tts.dll` and
  `VoiceCoach.Server.dll` produced.

[STATUS.json](STATUS.json) updated: infrastructure entry
"shared TTS library" goes `not-started 0%` → `complete 100%`, and
its dependent ("paper-coach C# server") loses its only listed
blocker. Next infrastructure piece on the chain is now unblocked.

Runtime validation gate is still half-open: build green ≠
`speak_to_user` still works at runtime. The user runs
`.\start-servers.bat` in the sibling repo and invokes the MCP tool
from Claude Desktop to close the second half of the gate. Surfaced
as `next_actions[0]` in STATUS.json so it doesn't get lost.

Held off on:

- Bumping the shared library's `TargetFramework` from
  `net9.0-windows` to `net9.0-windows10.0.19041.0`. The bump is
  required once `NaturalSpeaker.cs` (WinRT neural voices) lands;
  doing it preemptively would have conflated a framework retarget
  with the mechanical move and muddied the validation. Bump arrives
  with the NaturalSpeaker.cs commit.

What this unblocks:

- Build order step 2: scaffold `paper-coach` server with one MCP
  tool (`list_papers`) to validate the MCP attach path against this
  repo's not-yet-existent `.mcp.json`. Single relative
  `<ProjectReference Include="..\..\ai-verbal-coaching\shared\Tts\Tts.csproj" />`
  is all that's needed to pull SAPI in.
- Steps 3-9 from SKILLS-PLAN.md remain in their planned order.

Sibling-commit note: the sibling commit bundled the extraction with
some unrelated 2026-05-07 WIP that was sitting uncommitted in that
repo (start-servers.bat, SpeechSession.cs, two DEV-LOG entries
about PowerShell quirks). Mixed scope, flagged in that repo's
DEV-LOG entry. Doesn't affect this repo.

### 2026-06-02 — /start dashboard skill + STATUS.json source of truth

Added a `/start` slash-skill that renders a terminal-style project dashboard
on demand. Four sections: papers in flight (live disk scan), skills
(readiness from declared file), infrastructure (declared), and a short
"what's next" with three actions. ASCII box at 72 columns, sans-serif-safe
since chat is monospaced; falls back to a plain table if alignment breaks
in an unexpected renderer.

Two files landed:

- **[STATUS.json](STATUS.json)** at repo root — single declarative source
  of truth for skill + infrastructure readiness. Schema-versioned. Each
  entry has phase (`planned` / `scaffolded` / `functional` / `complete`),
  rough percent, blockers, optional notes. Phase icons declared inline so
  the dashboard reads them rather than the skill hardcoding them.
  Hand-edited as work lands — no auto-update, on purpose; phase calls
  are subjective and should stay human.
- **[.claude/skills/start/SKILL.md](.claude/skills/start/SKILL.md)** — the
  skill itself. Triggers on `/start`, `/status`, `/welcome`, and
  natural-language asks for project state. Includes a skeleton showing the
  exact target style + alignment, and rules for live paper-state
  computation: `M/N parts` where M counts rendered WAVs across both legacy
  (`output/<slug>/`) and new (`papers/<slug>/podcast/`) layouts, and N
  reads from `input/<slug>/part_*.json` count or
  `podcast_generation_state.json`. Subcommands `status` / `fresh` /
  `resume` are documented; the skill explicitly does NOT hardcode skill or
  infra rows — those come from STATUS.json so adding a skill is a
  STATUS.json edit, not a skill edit.

Staleness check baked in: if STATUS.json's `last_updated` predates the
top DEV-LOG entry, the dashboard appends a one-line nudge prompting the
user to hand-update. Avoids the silent-staleness trap without taking
phase calls out of the user's hands.

What this unblocks:

- A fresh Claude Code session can type `/start` and orient itself in
  seconds — papers, skills, blockers, suggested next move. The
  alternative was making every new session re-read three docs.
- `/start fresh` and `/start resume` give the HITL director a known
  entry point for the two most-common intents (new paper / continue an
  in-flight one) without `paper-director` itself being implemented yet.
  Once paper-director lands, those subcommands hand off to it.

Deferred / open:

- The dashboard skeleton in SKILL.md uses example paper counts
  (great_plea 17/17 etc.). The numbers are intentionally placeholder —
  the skill's render rules compute them fresh each time. If the example
  drifts from reality nobody cares; it's documentation, not output.
- No "papers/<slug>/" directory exists yet — all paper state will be
  scanned from the legacy `input/<slug>/` + `output/<slug>/` layouts
  until the new pipeline lands. The skill checks both paths so the
  transition is seamless.
- Could eventually add a `/start audit` mode that scans for partial
  states (e.g. dialog JSONs without corresponding WAVs, or vice versa).
  Not built; logged for later if it matters.

### 2026-06-02 — adopted Voice Coach architecture; shared TTS; MCP director

Surveyed the sibling project `../ai-verbal-coaching/` (Voice Coach) at the
user's direction, since "we'll include voice and tts from it." It turns out
to be the empirical validation of the polyglot recommendation I'd just made
on language choice: C# ASP.NET minimal API as orchestrator + MCP host
(`server/`), Python FastAPI sidecar where Python's ecosystem genuinely wins
(`whisper-sidecar/`), static UI under `wwwroot/`, project-scope MCP via
`.mcp.json` over Streamable HTTP. Voice Coach's `Speaker.cs` (121 LOC) is
production-quality SAPI 5 with voice enumeration cached at startup,
default-voice fallback, async + cancellation, speed→rate mapping. We adopt
the same shape here and lift `Speaker.cs` into a new shared library
`../ai-verbal-coaching/shared/Tts/Tts.csproj` that both projects path-reference.

Material plan changes captured in [SKILLS-PLAN.md](SKILLS-PLAN.md):

- **`paper-director` is now an MCP server (`paper-coach`)**, not a
  shell-verb skill. Verbs (`list_papers`, `find_papers`, `select`,
  `extract`, `combine`, `render_audio`, `list_voices`, `session_status`)
  become `[McpServerTool]`s mirroring `VoiceCoachTools.cs`. Cleaner than
  text commands — Claude calls tools, gets typed results back. Sibling's
  `.mcp.json` pattern (Streamable HTTP, project scope) is the template.
- **Shared TTS library at `../ai-verbal-coaching/shared/Tts/`.** Voice
  Coach's `Speaker.cs` moves there, voice-coach project-references it,
  paper-coach adds a relative `<ProjectReference>` upward. Implies both
  repos live under one parent directory — documented in CLAUDE.md.
- **WinRT neural voices** (`Windows.Media.SpeechSynthesis`) added as a
  sibling `NaturalSpeaker.cs` in the shared library, opt-in per persona.
  Requires bumping the csproj target to `net9.0-windows10.0.19041.0` for
  the WinRT projection — flagged as a Voice Coach change too if they want
  Aria/Jenny in their flow.
- **Polyglot split codified.** C# for orchestration / MCP / Windows APIs /
  stateful verbs. Python sidecars only where the ecosystem is unique
  (PDF→MD via `pymupdf4llm`/`marker-pdf`). SKILL.md files for LLM-driven
  worker stages (highlights, cypher, scripter) — no code, just instructions.
- **Ports: 6000 (paper-coach) + 6001 (pdf-sidecar)** to avoid collision
  with Voice Coach's 5000/5001 so both can run side-by-side.
- **`script-to-audio` skill** becomes a thin SKILL.md that invokes the
  paper-coach `render_audio` MCP tool; the actual rendering lives in
  `server/Services/AudioRenderer.cs` over the shared TTS library.
  `Speaker.cs` needs two tweaks for our use case: render to file
  (`SetOutputToWaveFile` instead of `SetOutputToDefaultAudioDevice`) and
  `SpeakProgress` event hooks so per-line timestamps with
  `source_paragraphs` survive end-to-end.

New top-level [CLAUDE.md](CLAUDE.md) authored, lifting from Voice Coach's:
user identity, dyslexia → sans-serif typography mandate
(Atkinson Hyperlegible / Lexend, line-height ≥1.5), hardware notes, polyglot
conventions, target architecture diagram, planned boot sequence. Adopted
Voice Coach's DEV-LOG format spec going forward — `## YYYY-MM-DD — <slug>`
headers, narrative tense, capturing hypotheses ruled out / what this
unblocks / what's deferred / policy checks. Existing terser entries below
are kept as-is.

Hypotheses ruled out:

- **Merging paper-coach into voice-coach.** Considered; rejected. Voice
  Coach is solidly scoped to live interview coaching (mic in, speakers out);
  paper-coach is batch-render to file. Conflating concerns muddies both.
  Shared library is the right seam, not shared server.
- **Calling Voice Coach's `speak_to_user` over MCP from paper-coach.**
  Rejected — `Speaker.cs` binds to default audio device, not a file. We'd
  have to extend Voice Coach with a `render_to_wav` tool, and at that point
  we're back to the library-extraction question anyway.
- **Inventing a `bin/tts.exe` standalone from scratch.** Rejected once
  Speaker.cs's quality was confirmed.

What this unblocks:

- Build order in [SKILLS-PLAN.md §9](SKILLS-PLAN.md) starts with the shared
  TTS extraction — once Voice Coach still builds + `speak_to_user` still
  works after the move, everything else can proceed against a stable
  library. That's a small, well-scoped first PR.

Deferred / open:

- The shared TTS extraction touches the sibling repo. Needs to land as a
  Voice Coach commit first, then paper-coach can reference it. Coordinate.
- `Speaker.cs` modifications for file rendering + `SpeakProgress`
  timestamps are net-new code. The 121 LOC lift is the floor, not the ceiling.
- `panda_reader.html` consuming `highlights.json` is a real UI task not yet
  scoped here.

Policy checks: none required for documentation-only changes. No third-party
content imported; cross-references to the sibling repo are to the user's
own code.

### 2026-06-02 — skills-plan decisions locked

Resolved the four open questions from the first draft of `SKILLS-PLAN.md`:

- **Paragraph anchor.** `<!-- p:N -->` HTML comments on their own line,
  immediately preceding each paragraph. Invisible in rendered MD, deterministic
  regex `/<!-- p:(\d+) -->/g`. Paired with a `paper.spans.json` byte-offset
  sidecar for char-count joins.
- **Paper MD is immutable once written.** A `paper.md.sha256` is the pinning
  key for every downstream artifact (highlights, script, cypher). Edit the MD
  → checksum changes → downstream invalidates.
- **TTS engines.** SAPI 5 stays default. WinRT
  (`Windows.Media.SpeechSynthesis`) added as opt-in for OneCore / neural
  voices. Persona profile picks engine per-voice; a single script can mix.
- **Graph language: openCypher.** Most-portable subset (Neo4j, Memgraph,
  Neptune, AGE). No `apoc.*` or vendor extensions in emitted files. Forward-
  compatible with ISO GQL when tooling matures.
- **Director redesigned as interactive HITL conductor**, not an auto-pipeline.
  Verb-driven (`find`, `select`, `extract`, `combine`, `run`, `review`,
  `branch`); maintains a session under `papers/_workspace/<session>/`. Composed
  MDs (e.g. abstracts + conclusions of N papers) are first-class — every
  worker skill accepts either a canonical `paper.md` or a composed one, both
  sharing the same anchor + checksum contract.

Skill count grew from 6 to 7 — `script-to-audio` split out of the original
"audio with personas" so engine dispatch lives in one place.

### 2026-06-01 — DEV-LOG added, skills plan drafted

Documented the current pipeline as a baseline before refactoring. Wrote
`SKILLS-PLAN.md` proposing a skill suite that starts from PDF and uses
Markdown (not JSON) as the intermediate paper representation. The shift is
substantial — flagged in the plan rather than started.

Pending working-tree change: added `Bash(gh repo:*)` permission to
`.claude/settings.local.json`. Not yet committed.

### 2026-03-08 — server.py extended

Server reached current size (~14k). Endpoints serve manifest + state and host
both players. No log entry written at the time; reconstructed from mtime.

### 2026-03-07 — podcast_player.html landed

Split-pane player implemented per PLAN.md §2: paper left, dialog right, scroll
sync via `source_paragraphs`, bidirectional click navigation, part selector.

### 2026-03-06 — initial pipeline up

`dialog_to_audio.py`, `init_podcast.py`, paper JSON spec, first paper
(`great_plea`) generated end-to-end in 17 parts. `panda_reader.html` +
dyslexia-friendly skim styling added the same day.
