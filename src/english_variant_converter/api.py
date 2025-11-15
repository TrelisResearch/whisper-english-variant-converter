from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

from . import rules
from .tokenizer import Token, tokenize

SUPPORTED_VARIANTS = rules.SUPPORTED_VARIANTS


@dataclass
class SwapSummary:
    source: str
    target: str
    count: int


@dataclass
class ConversionStats:
    total_tokens: int
    converted_tokens: int
    protected_tokens: int
    swaps: Tuple[SwapSummary, ...]

    def to_dict(self) -> dict:
        return {
            "total_tokens": self.total_tokens,
            "converted_tokens": self.converted_tokens,
            "protected_tokens": self.protected_tokens,
            "swaps": [swap.__dict__ for swap in self.swaps],
        }


def _convert_internal(
    text: str,
    source: str,
    target: str,
    mode: str = "spelling_only",
) -> Tuple[str, ConversionStats]:
    tokens = tokenize(text)
    converted_chunks = []
    swaps: Dict[Tuple[str, str], int] = {}
    total_tokens = 0
    protected_tokens = 0
    converted_tokens = 0

    prev_word: Optional[str] = None
    for idx, token in enumerate(tokens):
        if not token.is_word:
            converted_chunks.append(token.text)
            continue

        total_tokens += 1
        if token.is_protected:
            protected_tokens += 1
            converted_chunks.append(token.text)
            prev_word = token.text.lower()
            continue

        next_word: Optional[str] = None
        future_idx = idx + 1
        while future_idx < len(tokens):
            future = tokens[future_idx]
            if future.is_word:
                next_word = future.text.lower()
                break
            future_idx += 1

        converted = rules.convert_token(token.text, source=source, target=target, mode=mode)
        if converted != token.text:
            if not rules.is_swap_allowed(token.text, converted, prev_word, next_word):
                converted = token.text
            else:
                converted_tokens += 1
                key = (token.text.lower(), converted.lower())
                swaps[key] = swaps.get(key, 0) + 1

        converted_chunks.append(converted)

        if not token.is_protected:
            prev_word = token.text.lower()

    stats = ConversionStats(
        total_tokens=total_tokens,
        converted_tokens=converted_tokens,
        protected_tokens=protected_tokens,
        swaps=tuple(SwapSummary(source=src, target=dst, count=count) for (src, dst), count in sorted(swaps.items())),
    )
    return "".join(converted_chunks), stats


def convert(
    text: str,
    source: str = "en_US",
    target: str = "en_GB",
    mode: str = "spelling_only",
    *,
    return_stats: bool = False,
):
    if return_stats:
        return _convert_internal(text, source=source, target=target, mode=mode)
    converted, _ = _convert_internal(text, source=source, target=target, mode=mode)
    return converted
