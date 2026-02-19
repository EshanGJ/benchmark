"""
update_question_types.py

Reads question_types.json and updates the `question_type` field for every
matching question across ALL sets and ALL paper files — no arguments needed.

How it works:
  - question_types.json maps each type (FITB, U, W, QA, C, M) to a set of
    question numbers (test_number values) that apply to EVERY paper in that set.
  - This script finds all paper .json files in each set directory and, for each
    question whose test_number matches the mapping, updates its question_type.

Run:
    python update_question_types.py
"""

import json
import os
import glob
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTION_TYPES_PATH = os.path.join(BASE_DIR, "question_types.json")
TEST_DIR = os.path.join(BASE_DIR, "data", "test")


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build_set_mappings(qt_data: dict) -> dict[str, dict[int, str]]:
    """
    Returns a dict keyed by set_key (e.g. "Set 1") whose value is
    a dict of {test_number (int) -> question_type (str)}.

    The numbers in question_types.json are the test_number values
    (question section numbers) that appear in EVERY paper of that set.
    """
    mappings: dict[str, dict[int, str]] = {}

    for entry in qt_data["data"]:
        qt = entry.get("question_type") or entry.get("major_question_type", "")
        if not qt:
            continue

        for set_key, test_numbers in entry["sets"].items():
            if not test_numbers:
                continue  # null → skip

            if set_key not in mappings:
                mappings[set_key] = {}

            for tn in test_numbers:
                try:
                    mappings[set_key][int(tn)] = qt
                except (ValueError, TypeError):
                    pass

    return mappings


def update_all() -> None:
    qt_data = load_json(QUESTION_TYPES_PATH)
    set_mappings = build_set_mappings(qt_data)

    total_files = 0
    total_questions = 0

    for set_key, tn_to_type in sorted(set_mappings.items()):
        # "Set 1" → "set 1"
        set_folder = os.path.join(TEST_DIR, set_key.lower())
        if not os.path.isdir(set_folder):
            print(f"  SKIP (folder not found): {set_folder}", file=sys.stderr)
            continue

        paper_files = sorted(glob.glob(os.path.join(set_folder, "*.json")))
        if not paper_files:
            print(f"  SKIP (no json files): {set_folder}", file=sys.stderr)
            continue

        print(f"\n{'-'*60}")
        print(f"{set_key}  |  {len(paper_files)} papers  |  mapping: {tn_to_type}")
        print(f"{'-'*60}")

        for paper_path in paper_files:
            paper_name = os.path.basename(paper_path)
            data = load_json(paper_path)
            questions = data.get("questions", [])
            changed = False

            for q in questions:
                raw_tn = q.get("test_number", "")
                try:
                    tn = int(raw_tn)
                except (ValueError, TypeError):
                    continue  # blank / non-numeric test_number — skip

                if tn in tn_to_type:
                    new_type = tn_to_type[tn]
                    old_type = q.get("question_type", "")
                    if old_type != new_type:
                        q["question_type"] = new_type
                        print(f"  {paper_name}  q{tn:>2}: '{old_type}' -> '{new_type}'")
                        total_questions += 1
                        changed = True

            if changed:
                save_json(paper_path, data)
                total_files += 1

    print(f"\n{'='*60}")
    print(f"Done. Updated {total_questions} question(s) across {total_files} file(s).")


if __name__ == "__main__":
    update_all()
