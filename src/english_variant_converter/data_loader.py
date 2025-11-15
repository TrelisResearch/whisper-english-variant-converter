from __future__ import annotations

import csv
from importlib import resources
from typing import Dict, List

VARIANT_FIELDS = ("en_US", "en_GB", "en_AU", "en_CA")

DATA_FILES = {
    "spelling_only": "spelling_crosswalk.csv",
    "lexical_choice": "lexical_crosswalk.csv",
}

_CACHE: Dict[str, List[dict[str, str]]] = {}


def _load_from_package(filename: str) -> List[dict[str, str]]:
    data_pkg = resources.files("english_variant_converter") / "data"
    path = data_pkg / filename
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_crosswalk(kind: str) -> List[dict[str, str]]:
    if kind not in DATA_FILES:
        raise ValueError(f"Unknown crosswalk kind '{kind}'")
    if kind not in _CACHE:
        _CACHE[kind] = _load_from_package(DATA_FILES[kind])
    return _CACHE[kind]
