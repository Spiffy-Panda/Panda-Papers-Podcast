---
name: script-to-audio
description: Render a podcast audioscript (multi-part script.json or legacy single-part part_NN.json) to per-part WAV files plus inline timestamps via paper-coach's render_audio MCP tool on :6000. Use when the user asks to render audio for a script, synth a podcast, run script-to-audio, or otherwise turn a dialog JSON into WAV. Enforces the persona-rotation rule from PIPELINE-DECISIONS §2 before rendering.
---

# script-to-audio — call render_audio, enforce persona rotation

This skill takes a podcast audioscript and produces per-part WAV files with
timestamps inlined into the output script. The heavy lifting (SAPI synth,
WAV concat, gap insertion, voice resolution) lives in
[paper-coach's render_audio](../../../server/Services/AudioRenderer.cs); this
skill is the persona-rotation gatekeeper and the result reviewer.

## When to invoke

- "render audio for <slug>"
- "synth the podcast"
- "run script-to-audio on <path>"
- "make the WAVs for part_01" (single-part legacy mode)

## Inputs

1. **script_path** — repo-relative or absolute. Two shapes both accepted by
   the tool (see [PIPELINE-DECISIONS §5](../../../PIPELINE-DECISIONS.md)):
   - Multi-part `script.json` with top-level `parts: [...]` — what
     `podcast-scripter` emits in the new pipeline.
   - Single-part `input/<slug>/part_NN.json` — legacy shape, useful for
     re-rendering on-disk parts under the new layout.
2. **out_dir** — where WAVs and the inline-timestamped output script land.
   Convention for the new pipeline: `papers/<slug>/podcast/`. For
   re-rendering a legacy part to verify a Speaker change, use a temp dir
   under `logs/` (gitignored) — don't pollute `output/<slug>/` with a
   renderer-version-skew copy of a file already there.

## Steps Claude takes

1. **Confirm paper-coach is up.** `GET http://localhost:6000/api/health` —
   expect `{ok: true, root: <repo>}`. If down, ask the user to run
   `start-servers.bat` (Window 1). The render itself is an MCP `tools/call`
   so confirm the MCP layer too if the health probe surprises you.
2. **Read the script and check persona rotation BEFORE rendering.** This is
   the design call this skill owns; render_audio is voice-agnostic and will
   happily emit hours of Zira-asks/David-explains pattern. Specifically:
   - Walk the lines for the part(s) being rendered. Count question marks
     and explanatory cues ("So...", "Right.", "Yeah, and...") by voice.
   - **Hard rule from
     [PIPELINE-DECISIONS §2](../../../PIPELINE-DECISIONS.md): never always
     Zira-as-learner / David-as-expert.** If for the whole script Zira asks
     more questions than David and David has more explanatory lines than
     Zira, the script reinforces a gender-norm pattern and is a regen, not
     a "good enough." Stop and tell the user: "this script puts Zira on
     the learner side throughout — paragraph X, paragraph Y, paragraph Z.
     Regenerate via `podcast-scripter` with a different rotation
     dimension, or override if this is the intended per-paper choice."
   - The user can override (`"yes, render anyway, the inversion comes in
     the next part"`). Don't refuse — just don't silently render an
     anti-pattern.
   - If `speaker_a` and `speaker_b` already describe distinct personas
     (e.g. one autistic-framed and one allistic-framed), the question-vs-
     explainer skew is allowed — the rotation dimension is something
     other than learner/expert. Look at the persona text and judge.
3. **Call `render_audio` via the paper-coach MCP.** Args:
   ```
   tools/call render_audio {
     "script_path": "<resolved>",
     "out_dir": "<out_dir>",
     "persona_profile": null
   }
   ```
   `persona_profile` is reserved and ignored by the renderer; pass null
   unless the user asks otherwise.
4. **Verify the response.** Expect `ok: true` with `script_path`,
   `wav_paths`, `total_duration_ms`, `parts_rendered`. If `ok: false`,
   report the `error` / `reason` verbatim and stop. Common failure modes:
   - `script_not_found` — path resolution issue. Resolve repo-relative
     against the repo root and retry.
   - `script_malformed` — JSON parse error or root isn't an object.
     Surface the file and the parser message to the user.
   - `part_empty` — a part with no lines. Probably scripter output bug;
     report part index and stop.
5. **Spot-check the output.** Open the rendered script (`<out_dir>/script.json`
   for multi-part, `<out_dir>/part_NN.json` for single-part) and verify:
   - Each line gained `start_ms` / `end_ms` (numbers, monotonically
     non-decreasing across each part).
   - Each part gained `wav` and `total_duration_ms`.
   - Root gained `rendered_utc` and `total_duration_ms`.
   - Each `wav_paths` entry exists on disk and has non-zero size.
6. **Report back** with the WAV paths, the total duration formatted
   `MM:SS`, and (if multi-part) part count. Optionally suggest opening one
   in the legacy player (still on :8847) for an audition.

## Voice resolution — don't second-guess the renderer

The renderer's voice resolver does exact match first, then substring fall-
back against installed SAPI voices. Legacy scripts saying `"Microsoft David"`
pick up `"Microsoft David Desktop"` automatically. Don't pre-rewrite voice
names in the script before calling — let the renderer do it. If the user
asks "is this voice installed?", call `list_voices` (also an MCP tool on
paper-coach) and check against the SAPI list.

## Re-rendering is fine

Output WAV names are stable (`part_NN.wav`, no timestamp suffix), so a
re-render overwrites cleanly. The rendered script's `rendered_utc` field
is the freshness signal. Don't worry about colliding with the legacy
output/ tree — that lives under a different convention.

## What this skill explicitly does *not* do

- Generate the script. That's `podcast-scripter`. This skill consumes a
  script and turns it into audio.
- Edit the script's content. Persona rotation enforcement is a *block-
  before-render* check, not a rewrite — fixing a bad rotation goes back
  through `podcast-scripter`.
- Stream to speakers. The renderer writes files; there's no live
  playback path.
- Mix multiple parts into one combined WAV. Each part stays separate by
  design — the player (legacy or future) handles part transitions.
