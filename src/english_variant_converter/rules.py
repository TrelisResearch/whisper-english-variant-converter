from __future__ import annotations

from functools import lru_cache
from typing import Dict, Optional

from .data_loader import VARIANT_FIELDS, load_crosswalk
from .exception_policies import exception_policies

SUPPORTED_VARIANTS = ("en_US", "en_GB", "en_AU", "en_CA")
SUPPORTED_MODES = ("spelling_only", "spelling_and_lexical")


def _normalize(word: str) -> str:
    return word.lower()


def _detect_case(token: str) -> str:
    if token.isupper():
        return "upper"
    if token.islower():
        return "lower"
    if token[:1].isupper() and token[1:].islower():
        return "title"
    return "mixed"


def _apply_case(word: str, pattern: str) -> str:
    if pattern == "upper":
        return word.upper()
    if pattern == "lower":
        return word.lower()
    if pattern == "title":
        return word[:1].upper() + word[1:].lower()
    return word


@lru_cache(maxsize=None)
def _build_mapping(source: str, target: str, mode: str) -> Dict[str, str]:
    if source == target:
        return {}

    mapping: Dict[str, str] = {}

    def ingest(rows):
        for row in rows:
            src = row.get(source, "").strip()
            dst = row.get(target, "").strip()
            if not src or not dst:
                continue
            src_norm = _normalize(src)
            dst_norm = dst.lower()
            if src_norm == dst_norm:
                continue
            mapping[src_norm] = dst_norm

    ingest(load_crosswalk("spelling_only"))
    if mode == "spelling_and_lexical":
        ingest(load_crosswalk("lexical_choice"))
    return mapping


def convert_token(token: str, source: str, target: str, mode: str = "spelling_only") -> str:
    if source not in SUPPORTED_VARIANTS or target not in SUPPORTED_VARIANTS:
        raise ValueError(f"Unsupported variant(s): {source}, {target}")
    if mode not in SUPPORTED_MODES:
        raise ValueError(f"Unsupported mode '{mode}'")
    if not token or source == target:
        return token

    mapping = _build_mapping(source, target, mode)
    normalized = _normalize(token)
    replacement = mapping.get(normalized)
    if not replacement:
        return token

    pattern = _detect_case(token)
    return _apply_case(replacement, pattern)


def is_swap_allowed(
    original: str,
    candidate: str,
    prev_word: Optional[str],
    next_word: Optional[str],
) -> bool:
    policy = exception_policies.classify(original, candidate)
    if policy.action == "skip":
        return False
    if policy.action == "conditional":
        prev_norm = (prev_word or "").lower() or None
        next_norm = (next_word or "").lower() or None
        return exception_policies.allow_conditional(policy.value or "", prev_norm, next_norm)
    return True
