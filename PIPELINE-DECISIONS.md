# Pipeline Design Decisions

Living document for the *what* and *why* of pipeline choices that don't
fit cleanly into [PLAN.md](PLAN.md) (paper-JSON-era architecture) or
[SKILLS-PLAN.md](SKILLS-PLAN.md) (PDF-era architecture). Those describe
shape and build order; this describes rules and rationale.

Linked from [CLAUDE.md](CLAUDE.md). Update when a decision changes;
record reversed decisions in [DEV-LOG.md](DEV-LOG.md) too.

---

## Audioscript schema: carry forward the legacy shape, lightly polished

The new pipeline does **not** need a redesigned audioscript schema.
The legacy pair —

- `input/<slug>/part_NN.json` (dialog lines, each tagged
  `source_paragraphs: [int]`)
- `output/<slug>/part_NN_<ts>_timestamps.json` (same lines plus
  `start_ms` / `end_ms` from the renderer)

— already implements the line ↔ paragraph ↔ audio-time mapping
("syncpoints") that the player needs. That triangle is the contract.

Four cosmetic polish items to apply during the port (cheap because
the call sites are getting rewritten anyway):

1. **Split voice and persona.** Legacy mashes them as
   `"speaker_a": "Microsoft David - Systems and signal processing..."`.
   New: `{"voice": "Microsoft David", "persona": "Systems and signal..."}`.
2. **Reference paper by slug, not path.**
   `paper_source: "input/foo_paper.json"` → `paper_slug: "foo"`.
3. **Inline timestamps into the script** after rendering — one fewer
   sibling file for the player to load.
4. **Inline `part_of: {n, total}`** — currently implicit; tracked
   separately in `manifest.json` today.

Functional schema is settled; these are ergonomic.

## Two-presenter podcast persona rotation (anti-gender-norm rule)

**Hard rule.** Never always cast Microsoft Zira as the curious learner
and Microsoft David as the expert/explainer. That pattern reinforces
gender norms (female voice asking male voice for understanding) and is
a bug, not a feature.

Vary the personas across one or more dimensions per paper (or per part
within a paper), with **either voice taking either side**:

- applied math / engineering vs. social theory / humanities
- autistic vs. allistic framing
- ADHD-style analogies vs. by-the-text faithful summary
- domain expert vs. generalist
- skeptical / adversarial vs. enthusiastic / extending
- or any blend that fits the paper

The dialog JSON file records the per-paper persona choices. The
legacy `speaker_a` / `speaker_b` text fields are already personality
descriptions (not just voice ids) — keep that, just split voice from
persona per the schema polish above.

The four deleted `input/<slug>/prompt_template.txt` files (gone in
`6b76633`) had the "Speaker A explainer / Speaker B learner" framing
hardcoded — that template was the locus of the bug, and the actual
generated dialogs worked around it by overriding per-paper. The
content that survives them moves into `podcast-scripter`'s
`SKILL.md`, with this rotation rule replacing the stale section.

When reviewing generated dialog, check that Zira is not always the
question-asker. If she is, regenerate.

## Generation cadence: one-shot per paper, subagents for length

Target shape: `podcast-scripter` is invoked once per paper and produces
all dialog JSONs in one pass. No `current_part` /
`status: ready|generating|complete` resume routine.

If a paper is long enough to bust context: **fan out subagents** (one
per part or per batch-N), not a state-file resume loop. The legacy
batched-6 cadence and the `podcast_generation_state.json` resume
routine were length-limit workarounds, not design choices. Subagent
isolation also helps with the persona rotation rule (separate context
per part eases lens variation when that's the chosen rotation
dimension).

The legacy `podcast_generation_state.json` file continues to exist
for the six already-rendered papers. Don't repurpose that name for
new-pipeline state — fresh artifact path under `papers/<slug>/`.

## Cypher work is a stretch goal

`paper-to-cypher`, `graph.cypher`, openCypher concept search via
`find_papers(concept=…)` — all stretch. Don't block primary pipeline
work on them. Non-graph paths ship first; graph paths get a clearly
labeled TODO branch.

`paper-coach`'s `find_papers` MCP tool already implements this
correctly: criteria filter (author/year/title/slug) is functional,
concept-via-graph is unimplemented and called out as such in the
tool description. Future skills that *could* query the graph should
follow the same pattern.

Reflects [SKILLS-PLAN.md §9](SKILLS-PLAN.md)'s build-order point that
paper-to-cypher schema only stabilizes after ≥3 papers exist in MD
form anyway.

## Licensing of derivatives (per-paper, important)

Most tracked papers are CC BY 4.0. **Two are CC BY-NC-SA 4.0** and
require ShareAlike on any derivative produced from them:

- **ODESteer** (arXiv:2602.17560), Zhao et al.
- **RLHF Shallow Alignment** (arXiv:2603.04851), Young

Derivatives for those two — re-segmented JSON, dialog scripts,
synthesized audio — carry CC BY-NC-SA 4.0 by Brian Notarianni.
Before publishing new artifacts under any path for those papers:

1. Update [NOTICES.md](NOTICES.md) if a new attribution layer applies.
2. Update or create a folder-level `LICENSE.md` matching the pattern
   in [SteeringFollowup/LICENSE.md](SteeringFollowup/LICENSE.md) and
   [output/odesteer/LICENSE.md](output/odesteer/LICENSE.md).

The full reasoning (sublicense passthrough rejected; copyright
assignment unilateral and unavailable; two-layer pattern chosen) is in
the [2026-06-02 license-audit DEV-LOG entry](DEV-LOG.md).

Other tracked papers are CC BY 4.0 and only need upstream attribution
carried forward in `NOTICES.md`.

---

*New decisions: add a section here; if it materially changes how a
worker skill behaves, also link from [CLAUDE.md](CLAUDE.md)'s
"Pipeline design decisions" section. Reversed or superseded decisions
should be retained with a strikethrough header and a pointer to the
DEV-LOG entry that retired them — future readers need to know what
was tried and rejected, not just what's current.*
