# SKILLS-PLAN

Plan for a skill suite that takes paper PDFs and produces, on demand and under
human direction, (a) a Markdown working copy, (b) a cross-paper openCypher
graph, (c) a highlight overlay for skimming, (d) a podcast script, and
(e) audio with distinct personas — coordinated by an **interactive** director
that exposes its verbs as MCP tools.

Architecture is modeled on the sibling project
[`ai-verbal-coaching`](../ai-verbal-coaching/) (Voice Coach) — C# ASP.NET
server as orchestrator + MCP host, Python sidecars where Python's ecosystem
genuinely wins. Voice Coach's `Speaker.cs` is extracted into a shared TTS
library that both projects reference.

---

## §0. Decisions locked in (2026-06-02)

- **Paragraph anchor: `<!-- p:N -->` HTML comments** on their own line,
  immediately preceding each paragraph. Regex: `/<!-- p:(\d+) -->/g`. Paired
  with a byte-offset sidecar `paper.spans.json` for char-count joins.
- **Paper MD is immutable once written.** `paper.md.sha256` pins every
  downstream artifact. Edit MD → checksum changes → downstream invalidates.
- **Graph language: openCypher.** No `apoc.*` or vendor extensions in emitted
  files. Forward-compatible with ISO GQL.
- **Polyglot split (validated by Voice Coach):**
  - **C#** for orchestration, MCP host, Windows APIs (SAPI/WinRT), filesystem
    verbs, anything stateful.
  - **Python sidecars** where the ecosystem is unique — PDF extraction
    (`pymupdf4llm` / `marker-pdf`), audio post-processing if it comes up.
  - **SKILL.md files** for LLM-driven work where Claude reads MD and writes
    JSON (highlights, cypher, scripter) — no code, just instructions.
- **Director is an MCP server** (`paper-coach`), not a shell-verb skill. Verbs
  become `[McpServerTool]`s. Mirrors Voice Coach's `VoiceCoachTools.cs` pattern.
- **Shared TTS library.** Voice Coach's `Speaker.cs` moves to
  `../ai-verbal-coaching/shared/Tts/Tts.csproj`. Both projects path-reference
  it. SAPI lives there today; WinRT (`Windows.Media.SpeechSynthesis`)
  `NaturalSpeaker.cs` is added there for neural voices.
- **Ports.** `paper-coach` server on **6000**, `pdf-sidecar` Python on **6001**.
  Avoids collision with Voice Coach (5000/5001) so both can run side-by-side.

---

## §1. Repo layout (target)

```
ProductivityAndReadingHelper/
├── .mcp.json                       # project-scope MCP, points at :6000/mcp
├── start-servers.bat               # two PowerShell windows, tee'd logs
├── kill-servers.bat
├── logs/
│   ├── paper-coach.log
│   └── pdf-sidecar.log
├── CLAUDE.md                       # NEW (this commit)
├── DEV-LOG.md
├── SKILLS-PLAN.md                  # this file
├── PLAN.md                         # original design doc, preserved
├── README.md                       # NEW, two-terminal run instructions
│
├── server/                         # C# ASP.NET minimal API, port 6000
│   ├── PaperCoach.Server.csproj    # net9.0-windows10.0.19041.0
│   ├── Program.cs
│   ├── Services/                   # one file per concern
│   │   ├── PaperCatalog.cs         # scans papers/, returns metadata
│   │   ├── Workspace.cs            # session state under papers/_workspace/
│   │   ├── Extractor.cs            # MD-section extraction, checksum-aware
│   │   └── AudioRenderer.cs        # wraps shared TTS, writes WAVs per part
│   ├── Mcp/PaperCoachTools.cs      # [McpServerTool] verbs
│   └── wwwroot/                    # reader UI (panda_reader successor)
│
├── pdf-sidecar/                    # Python FastAPI, port 6001
│   ├── venv/
│   ├── requirements.txt
│   └── server.py                   # POST /extract → paper.md + spans + images
│
├── scripts/                        # one-off Python utilities
│   └── json_paper_to_md.py         # migration tool for existing paper JSON
│
├── .claude/
│   └── skills/                     # SKILL.md files (LLM-driven workers)
│       ├── paper-director/SKILL.md
│       ├── pdf-to-markdown/SKILL.md
│       ├── paper-to-cypher/SKILL.md
│       ├── highlights-overlay/SKILL.md
│       ├── podcast-scripter/SKILL.md
│       └── script-to-audio/SKILL.md
│
└── papers/                         # the data
    ├── <slug>/
    │   ├── source.pdf
    │   ├── paper.md
    │   ├── paper.md.sha256
    │   ├── paper.spans.json
    │   ├── paper.images/
    │   ├── paper.meta.json
    │   ├── graph.cypher
    │   ├── highlights.json
    │   └── podcast/
    │       ├── script.json
    │       ├── part_NN.wav
    │       ├── part_NN.timestamps.json
    │       └── manifest.json
    └── _workspace/<session-id>/
        ├── session.json
        ├── composed.md
        ├── composed.md.sha256
        ├── composed.spans.json
        ├── highlights.json
        └── podcast/
```

Sibling repo (Voice Coach) gains a new top-level directory:

```
ai-verbal-coaching/
├── shared/
│   └── Tts/
│       ├── Tts.csproj              # net9.0-windows10.0.19041.0
│       ├── Speaker.cs              # MOVED from server/Services/
│       └── NaturalSpeaker.cs       # NEW — WinRT neural voices
├── server/VoiceCoach.Server.csproj # now <ProjectReference> shared/Tts/Tts.csproj
└── … (unchanged)
```

This-project's `PaperCoach.Server.csproj` references the shared library by
relative path:

```xml
<ProjectReference Include="..\..\ai-verbal-coaching\shared\Tts\Tts.csproj" />
```

Implies sibling-repo expectation: both projects live under the same parent
directory (`UW Winter 26/`). Document in `CLAUDE.md`.

---

## §2. The two servers

### §2.1 `paper-coach` (C#, port 6000) — MCP host + orchestration

Modeled on `VoiceCoach.Server`. Same packages
(`ModelContextProtocol.AspNetCore`, `Microsoft.NET.Sdk.Web`), same minimal-API
shape, same `[McpServerToolType]` + `[McpServerTool]` pattern in
`Mcp/PaperCoachTools.cs`.

MCP tools exposed (the director's verb set):

| Tool | Description |
|---|---|
| `list_papers()` | Read `papers/*/paper.meta.json` and return slugs + metadata. |
| `find_papers(criteria)` | Filter by author, year, concept name (queries `graph.cypher` if present). |
| `inspect_paper(slug, sections?)` | Return metadata + section list, optionally section bodies. |
| `start_session(name?)` | Create `papers/_workspace/<session-id>/session.json`. Returns the session id. |
| `select(session, slugs[])` | Set/extend a session's working selection. `+slug` / `-slug` to delta. |
| `extract(session, slugs[], sections[], into)` | Pull named sections (e.g. `["abstract","conclusion"]`) from selected papers into a composed MD. Writes `composed.md`, `composed.spans.json`, `composed.md.sha256`. |
| `combine(session, files[], into)` | Concatenate existing MDs into a new composed MD. |
| `render_audio(script_path, persona_profile, out_dir)` | Render `script.json` to per-part WAV + timestamps via shared TTS library. |
| `list_voices()` | Enumerate available SAPI + WinRT voices (lifted from Voice Coach). |
| `session_status(session)` | Freshness table: what artifacts exist, what's stale relative to inputs. |

The tools are deterministic file-I/O verbs. LLM-driven stages (pdf-to-md
*invocation*, highlights, cypher, scripter) are SKILL.md files that Claude
runs, calling these tools to read/write artifacts and the `pdf-sidecar` for
PDF work.

### §2.2 `pdf-sidecar` (Python FastAPI, port 6001) — PDF extraction

Modeled on `whisper-sidecar/server.py`. FastAPI, single concern:

```
POST /extract
  multipart: pdf=<file>, slug=<string>
  returns: { paper_md, spans, images_dir, meta }
```

Reasons for Python here are real — `pymupdf4llm`, `marker-pdf`, `pdfplumber`
are the LLM-tuned PDF→MD ecosystem and they're Python-only. The sidecar is
called by paper-coach (which writes the returned artifacts under `papers/<slug>/`)
rather than directly by Claude.

---

## §3. SKILL.md: `paper-director`

**Role.** The conductor. Maintains a chat session, responds to the user's
"find / select / extract / run / review / branch" intents by calling
paper-coach MCP tools, hands control back after each step.

**Trigger.** "Find me papers about X", "make a podcast from the conclusions
of A, B, C", "drop paper D and add E".

**Pattern.** Read SKILL.md → Claude knows to call `paper-coach.list_papers`,
`paper-coach.select`, etc., in response to natural-language requests.
Workspace state lives in `session.json` so a follow-up message can resume.

**Example session.**

```
user: find papers about pluralistic alignment
dir:  [calls list_papers + filters] 3 matches — roadmap_to_pluralistic_alignment
      (2024), responsible_ux (2023), great_plea (2023, weak match)
user: select the first two, pull abstract + conclusion of each into one md
dir:  [calls start_session, select, extract]
      wrote papers/_workspace/<session-id>/composed.md (4+3 paragraphs, sha abc123)
user: run highlights on it
dir:  [invokes highlights-overlay skill on composed.md, writes highlights.json]
user: write a podcast script, ~20 lines, one part
dir:  [invokes podcast-scripter on composed.md + highlights.json]
user: render audio, academic-duo persona
dir:  [calls render_audio with the persona profile, writes part_01.wav]
```

The director does NOT auto-pipeline all five stages. "Make a podcast from
paper X" still surfaces each intermediate artifact for review unless the user
says "non-interactive" / "just do it".

---

## §4. SKILL.md: `pdf-to-markdown`

**Role.** Drive `pdf-sidecar` to convert a PDF, then verify the output meets
the anchor + spans + checksum contract.

**Steps Claude takes.**
1. Resolve slug; ensure `papers/<slug>/source.pdf` exists.
2. POST to `pdf-sidecar:6001/extract`. Receive paper.md + spans + meta.
3. Write `paper.md`, `paper.spans.json`, `paper.meta.json`, `paper.md.sha256`.
4. Spot-check: regex `/<!-- p:(\d+) -->/g` matches once per paragraph;
   IDs are sequential from 1; spans byte ranges align.
5. If checks fail, report and stop. Don't silently retry.

**Outputs.** As in §1.

**Replaces** the manual `input/<paper>_paper.json` step from the original
`paper_json_spec.md`. A `scripts/json_paper_to_md.py` migration tool converts
existing paper JSON without re-OCR.

---

## §5. SKILL.md: `paper-to-cypher`

**Role.** Extract entities + relationships from an MD (paper or composed)
and emit **openCypher** that, when concatenated with other papers', forms a
cross-paper graph.

**Inputs.** Path to MD + sibling `*.spans.json` + `*.sha256` + (if real
paper) `paper.meta.json` + the `papers/` corpus for cross-linking.

**Schema (initial — refine after first 3 papers).**

Nodes: `(:Paper {slug,title,year,doi})`, `(:Author {name})`,
`(:Concept {name,normalized})`, `(:Claim {text,paper_sha,paragraph_id})`,
`(:Citation {raw,doi})`.

Edges: `AUTHORED`, `DEFINES`, `MENTIONS`, `MAKES_CLAIM`, `CITES`, `ABOUT`.

**Steps Claude takes.**
1. Verify MD checksum.
2. Walk paragraphs via spans. Identify candidate entities by section
   (definitions in intro/methods, claims in results, citations in references).
3. Normalize concept names (alias map under
   `.claude/skills/paper-to-cypher/aliases.json`).
4. Emit `MERGE` (idempotent), never `CREATE`.
5. Cross-link: read other papers' `paper.meta.json` and `graph.cypher`;
   MERGE against existing concept/author/DOI matches.
6. Write `<dir>/graph.cypher`.

**Notes.** openCypher only — no `apoc.*`. Schema constraints
(`CREATE CONSTRAINT`) live in a separate corpus-root `graph.schema.cypher`,
not per-paper.

---

## §6. SKILL.md: `highlights-overlay`

**Role.** Per-span markup the reader UI uses for fast skim.

**Output (`<dir>/highlights.json`).**

```json
{
  "source_md": "papers/<slug>/paper.md",
  "source_sha": "abc123…",
  "spans": [
    { "paragraph": 4, "start": 0, "end": 120, "tier": "must-read",
      "reason": "stated research question" }
  ]
}
```

**Tiers.** `must-read`, `should-read`, `skim`, `skip`.

**Steps Claude takes.**
1. Verify MD checksum.
2. Walk paragraphs via spans. Classify each span by section + linguistic cues
   ("We propose…", numeric findings → must-read; "Prior work…" → skim).
3. Sub-paragraph split only when a paragraph mixes tiers.
4. Optionally include a `bionic` field per span for the existing
   `panda_reader.html` dyslexia overlay.

**UI side (future, not this skill's job).** `panda_reader.html` consumes
`highlights.json` + MD, renders the overlay. Tracked separately.

---

## §7. SKILL.md: `podcast-scripter`

**Role.** Generate the two-voice dialog script from an MD + highlights,
broken into parts.

**Inputs.** MD + spans + sha; optional `highlights.json` (must-read tiers
get fuller coverage); optional `graph.cypher` (concept links → analogies);
optional previously-generated parts for continuity.

**Output (`<dir>/podcast/script.json`).** Per-part array, dialog lines tagged
with `voice`, `persona`, `text`, `source_paragraphs` (integer IDs from the
anchor regex).

**Steps Claude takes.**
1. Verify checksums.
2. Plan parts using `init_podcast.py`'s heuristics (3-7 paragraphs/part, ~25
   lines, split at section boundaries) — port the logic, don't reinvent.
3. For each part, assemble prompt similar to the existing
   `input/<paper>/prompt_template.txt`, feeding highlights tier so the model
   knows where to spend time.
4. Generate, validate against schema, append to `script.json`.
5. Idempotent: skip parts whose inputs (MD sha, highlights sha) haven't
   changed.

**Replaces** `init_podcast.py` + per-paper `prompt_template.txt` + the Claude
Desktop scheduled prompt. State-file lifecycle collapses into the idempotency
check.

---

## §8. SKILL.md: `script-to-audio`

**Role.** Invoke paper-coach's `render_audio` MCP tool against a script.

**Steps Claude takes.**
1. Resolve script path + persona profile name.
2. Call `render_audio(script_path, persona_profile, out_dir)`.
3. Verify per-part WAVs + timestamps exist.

**The actual work** happens in C#:

- `server/Services/AudioRenderer.cs` reads `script.json`, dispatches each
  line to the persona's engine via the shared TTS library.
- `shared/Tts/Speaker.cs` (lifted from Voice Coach) handles SAPI 5.
  Modifications: `SetOutputToWaveFile` instead of `SetOutputToDefaultAudioDevice`;
  hook `SpeakProgress` events for per-word/per-sentence timestamps so
  `source_paragraphs` survives end-to-end.
- `shared/Tts/NaturalSpeaker.cs` (new) handles WinRT
  (`Windows.Media.SpeechSynthesis`) for OneCore/neural voices (Aria, Guy,
  Jenny). Requires the csproj's `net9.0-windows10.0.19041.0` target for the
  WinRT projection.

Persona profile (JSON, named or path):

```json
{
  "host":    { "engine": "sapi5", "voice": "Microsoft David Desktop", "rate": 0 },
  "guest":   { "engine": "winrt", "voice": "Microsoft Aria Online (Natural)" },
  "narrator":{ "engine": "winrt", "voice": "Microsoft Guy Online (Natural)", "rate": -1 }
}
```

A single script can mix engines per-line.

---

## §9. Build order

1. **Extract shared TTS** — move Voice Coach's `Speaker.cs` to
   `../ai-verbal-coaching/shared/Tts/`, add csproj, update Voice Coach's
   project reference. Confirm Voice Coach still builds and `speak_to_user`
   still works. **Validation gate before anything else.**
2. **Scaffold `paper-coach` server** — `dotnet new web`, add MCP package, add
   the shared TTS project reference, stub one tool (`list_papers`).
   Validate MCP attaches from this repo's `.mcp.json`.
3. **Scaffold `pdf-sidecar`** — FastAPI, single `/extract` endpoint with a
   minimum-viable extractor (pymupdf4llm). Validate one paper round-trips.
4. **Implement `pdf-to-markdown` SKILL.md** end-to-end on one paper.
5. **Add `NaturalSpeaker.cs`** to shared TTS. Implement `render_audio` +
   `script-to-audio` SKILL.md. Render an existing dialog JSON for parity.
6. **Implement `podcast-scripter`** — replaces `init_podcast.py`. Verify
   parity on an existing paper.
7. **`highlights-overlay`** — independent, can land in parallel with 6.
8. **`paper-to-cypher`** — last; schema benefits from ≥3 papers in MD form.
9. **`paper-director`** — once 4-8 are usable individually, wrap them. Verb
   set will sharpen with actual use.

---

## §10. Migration from the current pipeline

- `input/<paper>_paper.json` files stay. `scripts/json_paper_to_md.py` emits
  `paper.md` + `paper.spans.json` + `paper.meta.json` from spec'd JSON, so
  papers that already work skip re-OCR.
- `output/<paper>/` artifacts stay until each paper re-runs through the new
  pipeline. Nothing is deleted automatically.
- `podcast_player.html` and `server.py` (the existing Python `server.py`, not
  paper-coach) keep working against the old layout for now. Reader-UI
  migration to `papers/<slug>/` happens after `panda_reader.html` adopts
  `highlights.json`.
