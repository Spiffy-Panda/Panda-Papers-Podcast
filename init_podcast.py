"""
Initialize a podcast generation project from a paper JSON file.

Usage:
    python init_podcast.py input/great_plea_paper.json

Creates:
  - podcast_generation_state.json   (root-level generation state)
  - output/<tag>/manifest.json      (part index)
  - input/<tag>/                    (directory for future dialog JSONs)
  - input/<tag>/prompt_template.txt (copied from template)
"""

import sys
import os
import json
import math

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def split_paragraphs_into_parts(sections, min_per_part=3, max_per_part=7):
    """Split paper paragraphs into podcast parts respecting section boundaries.

    Strategy: accumulate sections into a current batch. Flush when adding the
    next section would exceed max. Small sections get merged together.
    After initial split, merge any undersized trailing parts back.
    """
    parts = []
    current_paras = []
    current_sections = []

    section_title_map = {s["id"]: s["title"] for s in sections}

    for section in sections:
        sec_paras = section["paragraphs"]
        sec_id = section["id"]

        # If adding this section would exceed max and we already have enough, flush first
        if current_paras and len(current_paras) + len(sec_paras) > max_per_part and len(current_paras) >= min_per_part:
            parts.append({
                "paragraph_ids": [p["id"] for p in current_paras],
                "section_ids": list(current_sections),
                "section_titles": [section_title_map[sid] for sid in current_sections],
            })
            current_paras = []
            current_sections = []

        current_paras.extend(sec_paras)
        if sec_id not in current_sections:
            current_sections.append(sec_id)

        # If we've hit or exceeded max, flush (splitting large sections)
        while len(current_paras) > max_per_part:
            chunk = current_paras[:max_per_part]
            parts.append({
                "paragraph_ids": [p["id"] for p in chunk],
                "section_ids": list(current_sections),
                "section_titles": [section_title_map[sid] for sid in current_sections],
            })
            current_paras = current_paras[max_per_part:]
            # Keep sections tag for continuation

    # Flush remainder
    if current_paras:
        parts.append({
            "paragraph_ids": [p["id"] for p in current_paras],
            "section_ids": list(current_sections),
            "section_titles": [section_title_map[sid] for sid in current_sections],
        })

    # Merge undersized trailing parts (< min_per_part) into previous part
    merged = []
    for part in parts:
        if merged and len(part["paragraph_ids"]) < min_per_part:
            prev = merged[-1]
            prev["paragraph_ids"].extend(part["paragraph_ids"])
            for sid in part["section_ids"]:
                if sid not in prev["section_ids"]:
                    prev["section_ids"].append(sid)
                    prev["section_titles"].append(section_title_map[sid])
        else:
            merged.append(part)

    return merged


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Initialize podcast generation from a paper JSON.")
    parser.add_argument("paper_json", help="Path to the paper JSON file")
    parser.add_argument("--tag", default=None, help="Project tag (default: derived from filename)")
    parser.add_argument("--speaker-a", default="Microsoft David", help="Voice for speaker A")
    parser.add_argument("--speaker-b", default="Microsoft Zira", help="Voice for speaker B")
    parser.add_argument("--min-paras", type=int, default=3, help="Min paragraphs per part")
    parser.add_argument("--max-paras", type=int, default=7, help="Max paragraphs per part")
    parser.add_argument("--target-lines", type=int, default=25, help="Target dialog lines per part")
    args = parser.parse_args()

    with open(args.paper_json, "r", encoding="utf-8") as f:
        paper = json.load(f)

    tag = args.tag or os.path.splitext(os.path.basename(args.paper_json))[0].replace("_paper", "")
    meta = paper["meta"]
    sections = paper["sections"]

    # Collect all paragraph IDs
    all_para_ids = []
    for sec in sections:
        for p in sec["paragraphs"]:
            all_para_ids.append(p["id"])

    # Split into parts
    part_splits = split_paragraphs_into_parts(sections, args.min_paras, args.max_paras)
    total_parts = len(part_splits)

    print(f"Paper: {meta['title']}")
    print(f"Tag: {tag}")
    print(f"Total paragraphs: {len(all_para_ids)}")
    print(f"Planned parts: {total_parts}")
    for i, part in enumerate(part_splits):
        print(f"  Part {i+1}: paragraphs {part['paragraph_ids']} ({', '.join(part['section_titles'])})")

    # Create directories
    input_dir = os.path.join(SCRIPT_DIR, "input", tag)
    output_dir = os.path.join(SCRIPT_DIR, "output", tag)
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Build manifest
    manifest = {
        "paper_source": args.paper_json,
        "parts": []
    }
    for i, part in enumerate(part_splits):
        part_num = i + 1
        manifest["parts"].append({
            "part_number": part_num,
            "title": f"Part {part_num}: {', '.join(part['section_titles'])}",
            "covers_paragraphs": part["paragraph_ids"],
            "covers_sections": part["section_ids"],
            "dialog_input": f"input/{tag}/part_{part_num:02d}.json",
            "timestamps_file": f"output/{tag}/part_{part_num:02d}_timestamps.json",
            "audio_file": f"output/{tag}/part_{part_num:02d}.wav",
            "status": "planned"
        })

    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\nManifest: {manifest_path}")

    # Build state file
    paper_source_rel = args.paper_json.replace("\\", "/")
    state = {
        "paper_source": paper_source_rel,
        "prompt_template": f"input/{tag}/prompt_template.txt",
        "output_dir": f"output/{tag}",
        "manifest": f"output/{tag}/manifest.json",
        "speaker_a": {"name": "Host", "voice": args.speaker_a},
        "speaker_b": {"name": "Guest", "voice": args.speaker_b},
        "target_lines_per_part": args.target_lines,
        "paragraphs_per_part": [args.min_paras, args.max_paras],
        "pause_between_ms": 600,
        "rate": 0,
        "paper_overview": f"{meta['title']} by {', '.join(meta['authors'])} ({meta['year']}). Published in {meta['journal']}.",
        "current_part": 1,
        "total_planned_parts": total_parts,
        "last_generated_part": 0,
        "last_part_summary": "",
        "last_part_final_lines": [],
        "remaining_paragraph_ids": all_para_ids,
        "parts_plan": [
            {
                "part_number": i + 1,
                "paragraph_ids": part["paragraph_ids"],
                "section_ids": part["section_ids"],
                "section_titles": part["section_titles"]
            }
            for i, part in enumerate(part_splits)
        ],
        "status": "ready"
    }

    state_path = os.path.join(SCRIPT_DIR, "podcast_generation_state.json")
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    print(f"State: {state_path}")

    # Copy prompt template if not already there
    template_dest = os.path.join(input_dir, "prompt_template.txt")
    template_src = os.path.join(SCRIPT_DIR, "input", tag, "prompt_template.txt")
    if not os.path.exists(template_dest):
        print(f"Prompt template will be created at: {template_dest}")
        print("  (Run this script, then check the template file)")

    print("\nDone! Next steps:")
    print(f"  1. Review/edit {state_path}")
    print(f"  2. Add a paper_overview to the state file")
    print(f"  3. Use the prompt template to generate Part 1")


if __name__ == "__main__":
    main()
