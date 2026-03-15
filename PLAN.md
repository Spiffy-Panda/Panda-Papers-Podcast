# Podcast-from-Paper System: Requirements & Plan

## 1. Data Model

### 1.1 Podcast Manifest (`output/great_plea/manifest.json`)
- Top-level file that indexes all podcast parts for the paper
- Schema:
```json
{
  "paper_source": "input/great_plea_paper.json",
  "parts": [
    {
      "part_number": 1,
      "title": "Introduction to GREAT PLEA",
      "covers_paragraphs": [1, 2, 3, 4, 5],
      "covers_sections": ["abstract", "introduction"],
      "dialog_input": "input/great_plea/part_01.json",
      "timestamps_file": "output/great_plea/part_01_timestamps.json",
      "audio_file": "output/great_plea/part_01.wav",
      "status": "generated"
    }
  ]
}
```

### 1.2 Extended Dialog Input (e.g. `input/great_plea/part_01.json`)
- Extends existing dialog JSON with paragraph mapping:
```json
{
  "pause_between_ms": 600,
  "rate": 0,
  "part_number": 1,
  "paper_source": "input/great_plea_paper.json",
  "lines": [
    {
      "voice": "Microsoft David",
      "text": "So today we're diving into this fascinating framework...",
      "source_paragraphs": [1]
    },
    {
      "voice": "Microsoft Zira",
      "text": "Right, the GREAT PLEA framework was developed...",
      "source_paragraphs": [1, 2]
    }
  ]
}
```

### 1.3 Extended Timestamps Output
- Existing timestamp schema, plus `source_paragraphs` carried through from input:
```json
{
  "lines": [
    {
      "index": 0,
      "voice": "Microsoft David",
      "text": "...",
      "start_ms": 0.0,
      "end_ms": 5693.5,
      "duration_ms": 5693.5,
      "source_paragraphs": [1]
    }
  ]
}
```

## 2. Podcast Player UI

### 2.1 Layout: Split-Pane View
- **Left pane**: The paper text, reconstructed from `great_plea_paper.json`. Section headings rendered as headers, paragraphs rendered in reading order. Each paragraph tagged with its `id` as a data attribute.
- **Right pane**: The existing dialog player (conversation panel + controls), loaded with the current part's timestamps/audio.
- **Bottom bar**: Part selector (Part 1, Part 2, ...) with status indicators. Click to load a different part.

### 2.2 Scroll Sync (Paper tracks Podcast)
- As audio plays and the active dialog line changes, the paper pane auto-scrolls to the paragraph(s) referenced by `source_paragraphs`.
- Active paragraphs get a highlight style (e.g. left border accent, light background).
- Previously-covered paragraphs get a subtle "read" style (dimmed or checkmarked).
- Upcoming paragraphs remain in default style.

### 2.3 Bidirectional Navigation
- Clicking a paragraph in the paper pane jumps to the first dialog line that references it.
- Clicking a dialog line in the conversation pane scrolls the paper pane to the referenced paragraph(s).

### 2.4 Part Transitions
- When a part finishes playing, prompt the user: "Continue to Part N+1?" with autoplay option.
- Part selector shows: part title, covered sections, duration, and generation status.

## 3. Paper Reconstruction View

### 3.1 Rendering
- Parse `great_plea_paper.json` sections and paragraphs.
- Render: paper title + authors (from `meta`) at top, then each section with `<h2>` title and `<p id="para-{id}">` for each paragraph.

### 3.2 Coverage Overlay
- Visual indicator per paragraph showing which podcast part covers it.
- Paragraphs not yet covered by any generated part show as "uncovered" (e.g. faded or with a "not yet covered" tag).

## 4. Generation Pipeline

### 4.1 `dialog_to_audio.py` Changes
- Accept `source_paragraphs` field in input lines, pass it through to timestamps output unchanged.
- No other changes needed.

### 4.2 Manifest Management
- A script or server endpoint to initialize the manifest from the paper JSON.
- A script or endpoint to register a newly generated part.

## 5. Podcast Generation Prompt Template

### 5.1 Purpose
- A reusable prompt template that an LLM uses to generate one part's dialog JSON at a time.
- Designed to produce dialog at the right granularity.

### 5.2 Template Inputs
| Variable | Description |
|----------|-------------|
| `{paper_title}` | Paper title from meta |
| `{paper_authors}` | Authors list |
| `{full_paper_context}` | Brief overall summary of the paper |
| `{part_number}` | Which part this is |
| `{total_planned_parts}` | Total number of parts planned |
| `{previous_part_summary}` | 2-3 sentence summary of what the previous part covered |
| `{previous_part_last_lines}` | Last 3-5 dialog lines from the previous part |
| `{paragraphs_to_cover}` | The actual paragraph texts (with IDs) to cover |
| `{section_titles}` | Section titles being covered |
| `{target_line_count}` | Suggested dialog line count (e.g. 20-35) |
| `{speaker_a}` | Speaker A voice |
| `{speaker_b}` | Speaker B voice |

### 5.3 Template Structure
```
You are writing Part {part_number} of {total_planned_parts} of a two-person
podcast discussing the paper "{paper_title}" by {paper_authors}.

PAPER OVERVIEW:
{full_paper_context}

CONTINUITY — PREVIOUS PART ENDED WITH:
{previous_part_summary}

Last lines of dialog:
{previous_part_last_lines}

YOUR TASK — COVER THESE PARAGRAPHS:
{paragraphs_to_cover}

RULES:
- Output valid JSON matching the dialog input schema (see below).
- Each dialog line MUST include "source_paragraphs" mapping it to
  the paragraph ID(s) it discusses.
- Cover ALL listed paragraphs. Do not skip any.
- Target {target_line_count} dialog lines. If you need more to avoid
  losing detail, go up to 1.5x that number.
- Speaker A ({speaker_a}) is the "explainer" — they've read the paper
  and present the ideas clearly.
- Speaker B ({speaker_b}) is the "curious learner" — they ask smart
  questions, request clarifications, and make analogies.
- Avoid reading the paper verbatim. Rephrase in conversational language.
- When a paragraph contains a list or taxonomy, have the speakers
  discuss 2-3 items in detail and briefly acknowledge the rest.
- Start Part 1 with a natural podcast intro. Start subsequent parts
  with a brief recap transition ("Last time we talked about...").
- End each part with a natural handoff: hint at what's coming next.

OUTPUT SCHEMA:
{
  "pause_between_ms": 600,
  "rate": 0,
  "part_number": {part_number},
  "paper_source": "input/great_plea_paper.json",
  "lines": [
    {
      "voice": "{speaker_a}" or "{speaker_b}",
      "text": "...",
      "source_paragraphs": [<paragraph IDs>]
    }
  ]
}
```

### 5.4 Granularity Guidance
- **Target**: 3-7 paragraphs per part (adjustable per section density).
- **Dense paragraphs** (definitions, taxonomies): 1-3 per part.
- **Narrative paragraphs** (intro, conclusion): 5-7 per part.
- **Line count target**: ~25 dialog lines per part (~3-5 min audio at normal speed).
- **Splitting heuristic**: Each part should cover a coherent subtopic. Prefer splitting at section boundaries. Never split mid-paragraph.

## 6. File Organization

```
podcast_generation_state.json          # ROOT — generation state
input/
  great_plea_paper.json
  great_plea/
    prompt_template.txt
    part_01.json
    part_02.json
    ...
output/
  great_plea/
    manifest.json
    part_01.wav
    part_01_timestamps.json
    ...
    full_paper.wav                     # (stretch) single-voice TTS
    full_paper_timestamps.json         # (stretch)
podcast_player.html                    # Split-pane player
dialog_player.html                     # Original player (unchanged)
dialog_to_audio.py                     # Extended with paragraph passthrough
server.py                             # Extended with new endpoints
```

## 7. Non-Requirements (Explicit Exclusions)
- The web app does not invoke LLMs — Claude Desktop's scheduler handles generation via the static prompt.
- The state file is paper-agnostic. To switch papers, create a new state file. Multi-paper simultaneous tracking is out of scope for v1.
- No streaming/progressive audio — each part is fully generated before playback.
- No user editing of the paper text — read-only, reconstructed from JSON.
- No mobile-responsive layout in v1 — desktop split-pane only.

## 8. Podcast Generation State File

### 8.1 Location & Purpose
- `podcast_generation_state.json` in project root
- Paper-agnostic — works for any paper
- Single source of truth for "what to generate next" and "what's been done"
- Designed to be consumed by a static Claude Desktop scheduled prompt

### 8.2 Schema
```json
{
  "paper_source": "input/great_plea_paper.json",
  "prompt_template": "input/great_plea/prompt_template.txt",
  "output_dir": "output/great_plea",
  "manifest": "output/great_plea/manifest.json",
  "speaker_a": { "name": "Host", "voice": "Microsoft David" },
  "speaker_b": { "name": "Guest", "voice": "Microsoft Zira" },
  "target_lines_per_part": 25,
  "paragraphs_per_part": [3, 7],
  "pause_between_ms": 600,
  "rate": 0,
  "paper_overview": "A 2023 paper proposing the GREAT PLEA framework...",
  "current_part": 3,
  "total_planned_parts": 12,
  "last_generated_part": 2,
  "last_part_summary": "We discussed Reliability and how it relates to...",
  "last_part_final_lines": [
    { "voice": "Microsoft David", "text": "Next time we'll get into Equity..." },
    { "voice": "Microsoft Zira", "text": "Can't wait, that's a big one." }
  ],
  "remaining_paragraph_ids": [22, 23, 24, 25, 26, 27],
  "status": "ready"
}
```

### 8.3 Status Values
- `"ready"` — next part can be generated
- `"generating"` — generation in progress (prevents double-runs)
- `"complete"` — all parts generated
- `"error"` — last generation failed

### 8.4 Lifecycle
1. **Init**: Script reads paper JSON, splits paragraphs into planned parts, writes initial state with `current_part: 1`.
2. **Before generation**: Scheduled prompt reads this file to assemble all template variables.
3. **After generation**: Dialog JSON saved, audio generated, state file updated — `current_part` increments, summaries refreshed, consumed paragraph IDs removed.
4. **Completion**: When `remaining_paragraph_ids` is empty, status flips to `"complete"`.

## 9. Claude Desktop Scheduled Prompt Integration

### 9.1 Static Prompt Design
The scheduled prompt is fixed text — it cannot contain dynamic variables. It tells Claude *where to look*, not *what the values are*.

### 9.2 Prompt Content
```
You are a podcast generation assistant.

1. Read the file `podcast_generation_state.json` in the project root.
2. If status is not "ready", stop and report why.
3. Read the prompt template file at the path in `prompt_template`.
4. Read the paper source file at the path in `paper_source`.
5. Using the state file fields, fill in all template variables and
   generate the next part's dialog JSON.
6. Save the dialog JSON to the appropriate input path.
7. Run `dialog_to_audio.py` to generate the audio and timestamps.
8. Update `podcast_generation_state.json`:
   - Increment `current_part`
   - Update `last_generated_part`, `last_part_summary`,
     `last_part_final_lines`
   - Remove covered paragraph IDs from `remaining_paragraph_ids`
   - Update the manifest file
   - Set status back to "ready" (or "complete" if done)
```

## 10. Full-Paper TTS Player (STRETCH GOAL)

### 10.1 Purpose
- Render the entire paper as a single TTS audio file, seekable by paragraph.
- Displayed as a second player alongside (or tabbed with) the podcast player.

### 10.2 Generation
- New script or mode in `dialog_to_audio.py` that takes the paper JSON directly, reads each paragraph with a single voice, inserts pauses between sections/paragraphs, outputs one WAV + one timestamps JSON.

### 10.3 Timestamps Schema
```json
{
  "source": "input/great_plea_paper.json",
  "audio_file": "output/great_plea/full_paper.wav",
  "type": "paper_tts",
  "lines": [
    {
      "index": 0,
      "paragraph_id": 1,
      "section_id": "abstract",
      "section_title": "Abstract",
      "text": "In 2020, the U.S. Department of Defense...",
      "start_ms": 0.0,
      "end_ms": 12400.0,
      "duration_ms": 12400.0
    }
  ]
}
```

### 10.4 UI
- Same paper-text left pane, shared with podcast player.
- Tab or toggle at top: **"Podcast" | "Paper Reading"**
- Paper Reading mode uses a single-speaker variant of the existing player.

## Implementation Order

1. Extend `dialog_to_audio.py` to pass through `source_paragraphs`
2. Create initialization script (splits paper into parts, creates state file + manifest)
3. Write the prompt template file
4. Generate Part 1 dialog manually with the template, validate pipeline end-to-end
5. Build `podcast_player.html` — split-pane layout with paper reconstruction + dialog player
6. Add scroll sync and bidirectional navigation
7. Add part selector and transitions
8. Extend `server.py` with manifest/state endpoints
9. (Stretch) Add full-paper TTS generation mode
10. (Stretch) Add Paper Reading tab to player
