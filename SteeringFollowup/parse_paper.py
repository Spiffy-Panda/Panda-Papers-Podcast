import json
import re
import sys

INPUT = "C:/Users/Brian/Documents/UW Winter 26/ProductivityAndReadingHelper/SteeringFollowup/ODESteer_arXiv_2602.17560.txt"
OUTPUT = "C:/Users/Brian/Documents/UW Winter 26/ProductivityAndReadingHelper/SteeringFollowup/ODESteer_paragraphs.json"

with open(INPUT, "r", encoding="utf-8") as f:
    text = f.read()

# The file uses literal \n (backslash-n) instead of real newlines.
# Split on double literal \n\n for paragraph boundaries.
paragraphs_raw = text.split("\\n\\n")

paragraphs = []
idx = 1
for p in paragraphs_raw:
    # Replace remaining literal \n with spaces
    cleaned = p.replace("\\n", " ")
    # Collapse multiple whitespace into single space
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip()
    if not cleaned:
        continue
    paragraphs.append({"id": idx, "text": cleaned})
    idx += 1

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(paragraphs, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(paragraphs)} paragraphs to {OUTPUT}")
