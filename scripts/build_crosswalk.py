#!/usr/bin/env python3
"""
Convert permissively-licensed spelling sources into the derived crosswalk CSVs used by the
english-variant-converter package.

Usage:
    uv run python scripts/build_crosswalk.py
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
DERIVED_DIR = ROOT / "data" / "derived"
PACKAGE_DATA_DIR = ROOT / "src" / "english_variant_converter" / "data"

VARIANT_FIELDS = ("en_US", "en_GB", "en_AU", "en_CA")


@dataclass
class SourceSpec:
    name: str
    filename: str
    entry_type: str
    variant_map: Dict[str, str]
    lemma_field: str | None = None
    notes_field: str | None = None

    @property
    def path(self) -> Path:
        return ROOT / "data" / "raw" / self.filename


SOURCE_SPECS: List[SourceSpec] = [
    SourceSpec(
        name="uk2us",
        filename="uk2us.csv",
        entry_type="spelling_only",
        variant_map={"us": "en_US", "uk": "en_GB"},
    ),
    SourceSpec(
        name="breame_spellings",
        filename="breame_spellings.csv",
        entry_type="spelling_only",
        variant_map={"us": "en_US", "uk": "en_GB"},
    ),
    SourceSpec(
        name="breame_meanings",
        filename="breame_meanings.csv",
        entry_type="lexical_choice",
        variant_map={"us": "en_US", "uk": "en_GB"},
        notes_field="notes",
    ),
    SourceSpec(
        name="scowl_varcon",
        filename="scowl_varcon.csv",
        entry_type="spelling_only",
        variant_map={
            "en_US": "en_US",
            "en_GB": "en_GB",
            "en_AU": "en_AU",
            "en_CA": "en_CA",
        },
        lemma_field="lemma",
        notes_field="notes",
    ),
]
SOURCE_PRIORITY = {spec.name: idx for idx, spec in enumerate(SOURCE_SPECS)}


def read_source(spec: SourceSpec) -> List[Dict[str, str]]:
    if not spec.path.exists():
        print(f"[build] Skipping {spec.name} (missing {spec.path})")
        return []

    rows: List[Dict[str, str]] = []
    with spec.path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            normalized = {variant: "" for variant in VARIANT_FIELDS}
            for src_key, dst_key in spec.variant_map.items():
                normalized[dst_key] = raw.get(src_key, "").strip()

            lemma = ""
            if spec.lemma_field:
                lemma = raw.get(spec.lemma_field, "").strip()
            if not lemma:
                lemma = normalized.get("en_US") or normalized.get("en_GB") or raw.get(
                    "lemma", ""
                )
            lemma = lemma.strip()
            notes = raw.get(spec.notes_field, "").strip() if spec.notes_field else ""

            # Skip rows that do not provide both en_US and en_GB for spelling-only entries.
            if spec.entry_type == "spelling_only":
                us_value = normalized.get("en_US", "")
                gb_value = normalized.get("en_GB", "")
                if not (us_value and gb_value):
                    continue
                if us_value.lower() == gb_value.lower():
                    continue

            rows.append(
                {
                    "lemma": lemma or normalized.get("en_US") or normalized.get("en_GB"),
                    "source": spec.name,
                    "type": spec.entry_type,
                    "notes": notes,
                    "_priority": SOURCE_PRIORITY.get(spec.name, len(SOURCE_PRIORITY)),
                    **normalized,
                }
            )
    print(f"[build] Loaded {len(rows)} rows from {spec.name}")
    return rows


def deduplicate(rows: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    deduped: Dict[tuple, Dict[str, str]] = {}
    for row in rows:
        key = (
            row["type"],
            tuple((row.get(field, "") or "").lower() for field in VARIANT_FIELDS),
        )
        entry = deduped.get(key)
        if entry:
            entry["sources"].add(row["source"])
            if row.get("notes"):
                entry["notes_set"].add(row["notes"])
            continue
        entry = {
            **row,
            "sources": {row["source"]},
            "notes_set": {row["notes"]} if row.get("notes") else set(),
        }
        deduped[key] = entry

    output: List[Dict[str, str]] = []
    for idx, entry in enumerate(deduped.values(), start=1):
        entry["variant_id"] = f"{entry['type']}-{idx:05d}"
        entry["source"] = ";".join(sorted(entry.pop("sources")))
        notes_set = entry.pop("notes_set")
        entry["notes"] = " | ".join(sorted(notes_set)) if notes_set else ""
        output.append(entry)
    print(f"[build] Reduced to {len(output)} unique rows")
    return output


def collapse_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    def priority(row: Dict[str, str]) -> int:
        return row.get("_priority", len(SOURCE_PRIORITY))

    rows = sorted(rows, key=lambda r: (priority(r), r.get("lemma") or ""))
    seen_us: Dict[tuple, Dict[str, str]] = {}
    seen_gb: Dict[tuple, Dict[str, str]] = {}
    unique: List[Dict[str, str]] = []

    for row in rows:
        en_us = (row["type"], row.get("en_US", "").lower())
        en_gb = (row["type"], row.get("en_GB", "").lower())
        if not en_us[1] or not en_gb[1]:
            continue
        if en_us in seen_us or en_gb in seen_gb:
            continue
        unique.append(row)
        seen_us[en_us] = row
        seen_gb[en_gb] = row

    for row in unique:
        row.pop("_priority", None)

    return unique


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    if not rows:
        print(f"[build] No rows to write for {path.name}, skipping")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    header = ["variant_id", "lemma", "type", *VARIANT_FIELDS, "notes", "source"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in header})
    print(f"[build] Wrote {len(rows)} rows → {path}")


def copy_to_package(source_path: Path) -> None:
    PACKAGE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    destination = PACKAGE_DATA_DIR / source_path.name
    destination.write_bytes(source_path.read_bytes())
    print(f"[build] Synced {source_path.name} → {destination}")


def main() -> None:
    all_rows: List[Dict[str, str]] = []
    for spec in SOURCE_SPECS:
        all_rows.extend(read_source(spec))

    deduped_rows = deduplicate(all_rows)
    collapsed_rows = collapse_rows(deduped_rows)
    spelling_rows = [row for row in collapsed_rows if row["type"] == "spelling_only"]
    lexical_rows = [row for row in collapsed_rows if row["type"] == "lexical_choice"]

    spelling_path = DERIVED_DIR / "spelling_crosswalk.csv"
    lexical_path = DERIVED_DIR / "lexical_crosswalk.csv"

    write_csv(spelling_path, spelling_rows)
    write_csv(lexical_path, lexical_rows)

    if spelling_rows:
        copy_to_package(spelling_path)
    if lexical_rows:
        copy_to_package(lexical_path)


if __name__ == "__main__":
    main()
