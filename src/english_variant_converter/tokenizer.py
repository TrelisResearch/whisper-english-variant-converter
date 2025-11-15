from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List

PROTECTED_WORD_MARKERS = ("http://", "https://", "ftp://", "www.")
PROTECTED_PREVIOUS_MARKERS = ("://", "@", "#")
TOKEN_PATTERN = re.compile(r"[A-Za-z]+|[^A-Za-z]+")


@dataclass
class Token:
    text: str
    is_word: bool
    is_protected: bool = False


def _should_protect(
    chunk: str,
    previous_chunk: str | None,
    next_chunk: str | None,
) -> bool:
    lower_chunk = chunk.lower()
    if any(marker in lower_chunk for marker in PROTECTED_WORD_MARKERS):
        return True

    if chunk[:1].isupper() and not chunk[1:].islower():
        return True

    prev_trimmed = (previous_chunk or "").strip()
    if any(prev_trimmed.endswith(marker) for marker in PROTECTED_PREVIOUS_MARKERS):
        return True

    next_chunk = next_chunk or ""
    if next_chunk and not next_chunk[0].isspace() and next_chunk.startswith("@"):
        return True

    return False


def tokenize(text: str) -> List[Token]:
    chunks = TOKEN_PATTERN.findall(text)
    tokens: List[Token] = []
    for idx, chunk in enumerate(chunks):
        is_word = chunk.isalpha()
        if not is_word:
            tokens.append(Token(text=chunk, is_word=False, is_protected=False))
            continue

        prev_chunk = chunks[idx - 1] if idx > 0 else None
        next_chunk = chunks[idx + 1] if (idx + 1) < len(chunks) else None
        protected = _should_protect(chunk, prev_chunk, next_chunk)
        tokens.append(Token(text=chunk, is_word=True, is_protected=protected))
    return tokens
