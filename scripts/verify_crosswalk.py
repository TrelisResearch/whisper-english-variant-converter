#!/usr/bin/env python3
"""
Basic integrity checks for the derived crosswalk tables.

Usage:
    uv run python scripts/verify_crosswalk.py
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DERIVED_DIR = ROOT / "data" / "derived"
VARIANT_FIELDS = ("en_US", "en_GB", "en_AU", "en_CA")


def _load_rows(filename: str) -> list[dict[str, str]]:
    path = DERIVED_DIR / filename
    if not path.exists():
        print(f"[verify] Skipping {filename} (missing {path})")
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def ensure_consistent_pairs(rows: list[dict[str, str]]) -> list[str]:
    issues: list[str] = []
    for variant in ("en_US", "en_GB"):
        mapping: dict[str, str] = {}
        for row in rows:
            key = row.get(variant, "").strip().lower()
            if not key:
                continue
            counterpart_field = "en_GB" if variant == "en_US" else "en_US"
            counterpart_value = row.get(counterpart_field, "").strip().lower()
            previous = mapping.setdefault(key, counterpart_value)
            if previous and previous != counterpart_value:
                issues.append(
                    f"{variant} token '{key}' maps to both '{previous}' and '{counterpart_value}'"
                )
    return issues


def ensure_variant_presence(rows: list[dict[str, str]]) -> list[str]:
    issues: list[str] = []
    for row in rows:
        variants_present = any(row.get(field, "").strip() for field in VARIANT_FIELDS)
        if not variants_present:
            issues.append(f"{row.get('variant_id', '?')} lacks variant spellings")
    return issues


def run_checks() -> int:
    spelling_rows = _load_rows("spelling_crosswalk.csv")
    lexical_rows = _load_rows("lexical_crosswalk.csv")

    issues = []
    issues.extend(ensure_consistent_pairs(spelling_rows))
    issues.extend(ensure_variant_presence(spelling_rows + lexical_rows))

    if issues:
        print("[verify] Found issues:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    total = len(spelling_rows) + len(lexical_rows)
    print(f"[verify] OK: {len(spelling_rows)} spelling rows, {len(lexical_rows)} lexical rows (total {total})")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_checks())
