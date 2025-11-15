#!/usr/bin/env python3
"""
Parse the VarCon text file into a CSV consumable by build_crosswalk.py.

Usage:
    uv run python scripts/parse_varcon.py
Requires:
    data/raw/varcon.txt  (extracted from the VarCon tarball)
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "raw" / "varcon.txt"
OUTPUT_PATH = ROOT / "data" / "raw" / "scowl_varcon.csv"

REGION_TO_COLUMN = {
    "A": "en_US",
    "B": "en_GB",
    "Z": "en_GB",  # VarCon's OED/ise spellings count as British
    "C": "en_CA",
}

PRIORITY = {
    "": 0,
    ".": 0,
    "v": 1,
    "V": 2,
    "-": 3,
    "x": 4,
}


def clean_word(word: str) -> str:
    word = word.strip()
    if not word:
        return ""
    if "|" in word:
        word = word.split("|", 1)[0].strip()
    if "#" in word:
        word = word.split("#", 1)[0].strip()
    return word


def parse_line(line: str) -> List[Tuple[str, str, int]]:
    variants: List[Tuple[str, str, int]] = []
    for fragment in line.split("/"):
        fragment = fragment.strip()
        if not fragment or ":" not in fragment:
            continue
        region_part, word_part = fragment.split(":", 1)
        word = clean_word(word_part)
        if not word:
            continue
        for token in region_part.strip().split():
            region = token[:1]
            indicator = token[1:]
            if region not in REGION_TO_COLUMN:
                continue
            variants.append((region, word, PRIORITY.get(indicator, 4)))
    return variants


def main() -> None:
    if not INPUT_PATH.exists():
        raise SystemExit(f"Missing {INPUT_PATH}. Download VarCon and place varcon.txt there.")

    rows: List[Dict[str, str]] = []
    current_lemma = ""

    with INPUT_PATH.open(encoding="latin-1") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#"):
                head = line[1:].strip()
                head = head.split("<", 1)[0].strip()
                head = head.split("(", 1)[0].strip()
                head = head.split("|", 1)[0].strip()
                current_lemma = head
                continue

            variants = parse_line(line)
            if not variants:
                continue

            best: Dict[str, Tuple[int, str]] = {}
            for region, word, priority in variants:
                column = REGION_TO_COLUMN[region]
                entry = best.get(column)
                if entry is None or priority < entry[0]:
                    best[column] = (priority, word)

            en_us = best.get("en_US", (5, ""))[1]
            en_gb = best.get("en_GB", (5, ""))[1]
            en_ca = best.get("en_CA", (5, ""))[1]
            if not (en_us and en_gb):
                continue
            if en_us.lower() != en_us or en_gb.lower() != en_gb:
                continue

            rows.append(
                {
                    "lemma": en_us or current_lemma,
                    "en_US": en_us,
                    "en_GB": en_gb,
                    "en_AU": "",
                    "en_CA": en_ca,
                    "notes": "",
                }
            )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["lemma", "en_US", "en_GB", "en_AU", "en_CA", "notes"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"[varcon] Parsed {len(rows)} rows → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
