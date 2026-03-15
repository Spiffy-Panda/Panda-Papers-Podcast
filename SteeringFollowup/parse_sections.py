"""
Parse ODESteer_paragraphs.json into a sectioned JSON structure.
Handles section headers that are:
  - Standalone paragraphs ("1Introduction", "Appendix BNotations")
  - Embedded at the end of a paragraph ("...threshold 4.2.1Unifying Input Reading")
  - Embedded mid-paragraph due to single-\n splits in the source
    ("...0.992 ±0.002 6Experiments", "...0.116 ±0.006 7Conclusion")
"""

import json
import re

INPUT = "C:/Users/Brian/Documents/UW Winter 26/ProductivityAndReadingHelper/SteeringFollowup/ODESteer_paragraphs.json"
OUTPUT = "C:/Users/Brian/Documents/UW Winter 26/ProductivityAndReadingHelper/SteeringFollowup/ODESteer_sections.json"

with open(INPUT, "r", encoding="utf-8") as f:
    paragraphs = json.load(f)

# =====================================================================
# Section header patterns
# =====================================================================

# Numbered: "1Introduction", "4.2.1Unifying Input Reading"
NUMBERED_SEC = re.compile(r'^(\d+(?:\.\d+)*)\s*([A-Z].+)$')

# Named standalone sections (must be roughly the entire paragraph)
NAMED_SECS = {
    "abstract": "Abstract",
    "acknowledgments": "Acknowledgments",
    "ethics statement": "Ethics Statement",
    "reproducibility statement": "Reproducibility Statement",
}

# Appendix top-level: "Appendix BNotations"
APPENDIX_SEC = re.compile(r'^Appendix\s+([A-Z])\s*(.*)$')

# Appendix subsection: "C.3Settings of ODEs", "D.1Settings of Base Models"
APPENDIX_SUBSEC = re.compile(r'^([A-Z]\.\d+)\s*([A-Z].*)$')

# ---- Embedded patterns (at end of a paragraph) ----
# Numbered subsection: "...threshold 4.2.1Unifying Input Reading"
EMB_NUMBERED = re.compile(r'^(.+?)\s(\d+(?:\.\d+)+)\s*([A-Z][a-zA-Z].{5,})$')
# Appendix: "...trajectories. Appendix DDetailed Experimental Setup"
EMB_APPENDIX = re.compile(r'^(.+?[.\s])Appendix\s+([A-Z])\s*([A-Z].{3,})$')
# Appendix subsection: "...RealToxicityPrompts E.1Generation Quality..."
EMB_APPENDIX_SUB = re.compile(r'^(.+?)\s([A-Z]\.\d+)\s*([A-Z].{5,})$')
# Top-level numbered section embedded after table data:
#   "...0.992 ±0.002 6Experiments" or "...0.006 7Conclusion"
EMB_TOPLEVEL = re.compile(r'^(.+?)\s(\d+)\s*([A-Z][a-z].{3,})$')


def detect_header(text):
    """Check if an entire paragraph is a section header."""
    # Appendix top-level
    m = APPENDIX_SEC.match(text)
    if m:
        letter = m.group(1)
        rest = m.group(2).strip()
        return ("appendix-" + letter, "Appendix " + letter + (": " + rest if rest else ""))

    # Appendix subsection
    m = APPENDIX_SUBSEC.match(text)
    if m:
        return (m.group(1), m.group(2).strip())

    # Numbered section — only if the paragraph is short (header-like, not body text)
    # and the title part looks like a real heading (starts with a capitalized word,
    # not something like "1University of Illinois...")
    m = NUMBERED_SEC.match(text)
    if m and len(text) < 120:
        return (m.group(1), m.group(2).strip())

    # Named sections (only if the paragraph is short — just the heading)
    text_lower = text.strip().lower()
    for key, name in NAMED_SECS.items():
        if text_lower == key or (text_lower.startswith(key) and len(text.strip()) <= len(key) + 5):
            return (key.replace(" ", "-"), name)

    return None


def detect_embedded(text):
    """Check if a paragraph ends with an embedded section header.
    Returns (before_text, section_id, title) or None."""

    # Embedded appendix top-level
    m = EMB_APPENDIX.search(text)
    if m:
        before = m.group(1).strip()
        letter = m.group(2)
        rest = m.group(3).strip()
        return (before, "appendix-" + letter, "Appendix " + letter + ": " + rest)

    # Embedded appendix subsection
    m = EMB_APPENDIX_SUB.search(text)
    if m:
        before = m.group(1).strip()
        return (before, m.group(2), m.group(3).strip())

    # Embedded numbered subsection (multi-level like 4.2.1)
    m = EMB_NUMBERED.search(text)
    if m:
        before = m.group(1).strip()
        return (before, m.group(2), m.group(3).strip())

    # Embedded top-level numbered section (e.g. "...data 6Experiments")
    m = EMB_TOPLEVEL.search(text)
    if m:
        before = m.group(1).strip()
        num = m.group(2)
        title = m.group(3).strip()
        # Sanity check: the number should be a plausible section number (1-20)
        if 1 <= int(num) <= 20:
            return (before, num, title)

    return None


# =====================================================================
# Build sections
# =====================================================================
sections = []
current_section = {"id": "preamble", "title": "Preamble", "paragraphs": []}

for p in paragraphs:
    pid = p["id"]
    text = p["text"]

    # Whole paragraph is a header?
    header = detect_header(text)
    if header:
        if current_section["paragraphs"]:
            sections.append(current_section)
        current_section = {"id": header[0], "title": header[1], "paragraphs": []}
        continue

    # Special case: "References E. Almazrouei..." — header + content in same paragraph
    # The reference body may also end with an embedded "Appendix A..." header
    if text.startswith("References ") and len(text) > 50:
        if current_section["paragraphs"]:
            sections.append(current_section)
        ref_body = text[len("References "):].strip()
        current_section = {"id": "references", "title": "References", "paragraphs": []}
        # Check if ref_body ends with embedded Appendix header
        appendix_match = re.search(
            r'(.+?)\s+Appendix\s+contents\s+Appendix\s+([A-Z])\s*(.*)$', ref_body
        )
        if not appendix_match:
            appendix_match = re.search(
                r'(.+?)\s+Appendix\s+([A-Z])\s*([A-Z].{3,})$', ref_body
            )
        if appendix_match:
            actual_ref = appendix_match.group(1).strip()
            if actual_ref:
                current_section["paragraphs"].append({"id": pid, "text": actual_ref})
            sections.append(current_section)
            letter = appendix_match.group(2)
            rest = appendix_match.group(3).strip()
            current_section = {
                "id": "appendix-" + letter,
                "title": "Appendix " + letter + (": " + rest if rest else ""),
                "paragraphs": []
            }
        elif ref_body:
            current_section["paragraphs"].append({"id": pid, "text": ref_body})
        continue

    # Embedded header at end? (skip for first few paragraphs which are title/authors)
    embedded = detect_embedded(text) if pid > 3 else None
    if embedded:
        before_text, sec_id, sec_title = embedded
        if before_text:
            current_section["paragraphs"].append({"id": pid, "text": before_text})
        if current_section["paragraphs"]:
            sections.append(current_section)
        current_section = {"id": sec_id, "title": sec_title, "paragraphs": []}
        continue

    # Regular paragraph
    current_section["paragraphs"].append({"id": pid, "text": text})

if current_section["paragraphs"]:
    sections.append(current_section)

# =====================================================================
# Post-process: extract Abstract from preamble
# =====================================================================
if sections and sections[0]["id"] == "preamble":
    preamble = sections[0]["paragraphs"]
    new_preamble = []
    abstract_paras = []
    in_abstract = False
    for pp in preamble:
        # The abstract is the long paragraph(s) between title/authors and "1Introduction"
        if not in_abstract and len(pp["text"]) > 200:
            in_abstract = True
        if in_abstract:
            # Skip URL-only paragraphs
            if pp["text"].strip() in ("odesteer.github.io",):
                continue
            abstract_paras.append(pp)
        else:
            new_preamble.append(pp)

    if abstract_paras:
        sections[0]["paragraphs"] = new_preamble
        abstract_section = {"id": "abstract", "title": "Abstract", "paragraphs": abstract_paras}
        sections.insert(1, abstract_section)
        if not sections[0]["paragraphs"]:
            sections.pop(0)

# =====================================================================
# Post-process: clean up Appendix titles with embedded subsection headers
# e.g. "Appendix C: Implementation Details of ODESteer C.1Algorithm"
#   -> title becomes "Appendix C: Implementation Details of ODESteer"
#   and the next section (C.1) already exists from the subsection detection
# Also fix: "Appendix E: Additional Experimental Results E.1Generation..."
# =====================================================================
EMBEDDED_SUB_IN_TITLE = re.compile(r'^(.*?)\s+[A-Z]\.\d+.+$')
for s in sections:
    if s["id"].startswith("appendix-"):
        m = EMBEDDED_SUB_IN_TITLE.match(s["title"])
        if m:
            s["title"] = m.group(1).strip()
    # Also fix appendix-F style titles with embedded case study info
    if s["id"].startswith("F.") or s["id"].startswith("E."):
        # Truncate overly long titles (case study prompts got merged in)
        if len(s["title"]) > 80:
            s["title"] = s["title"][:80].rsplit(" ", 1)[0]

# =====================================================================
# Renumber paragraph IDs within each section (1-based)
# =====================================================================
for section in sections:
    for i, para in enumerate(section["paragraphs"], 1):
        para["id"] = i

result = {"sections": sections}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(sections)} sections to {OUTPUT}")
for s in sections:
    nparas = len(s["paragraphs"])
    print(f"  [{s['id']:20s}] {s['title'][:70]:70s} ({nparas} paras)")
