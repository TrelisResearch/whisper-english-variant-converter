from __future__ import annotations

import csv
from dataclasses import dataclass
from importlib import resources
from typing import Dict, Optional, Set, Tuple


@dataclass(frozen=True)
class ExceptionPolicyResult:
    action: str  # "skip", "conditional", or ""
    value: Optional[str] = None


class ExceptionPolicies:
    def __init__(self) -> None:
        self._skip_pairs: Set[Tuple[str, str]] = set()
        self._conditional_pairs: Dict[Tuple[str, str], str] = {}
        self._load()

    def _load(self) -> None:
        try:
            base = resources.files("english_variant_converter") / "data" / "exceptions"
            path = base / "spelling_exceptions.csv"
            with path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    us = (row.get("en_US") or "").strip().lower()
                    gb = (row.get("en_GB") or "").strip().lower()
                    if not us or not gb:
                        continue
                    policy = (row.get("policy") or "").strip().lower()
                    key = (us, gb)
                    if policy == "skip":
                        self._skip_pairs.add(key)
                    elif policy.startswith("conditional:"):
                        rule = policy.split(":", 1)[1]
                        self._conditional_pairs[key] = rule
        except FileNotFoundError:
            return

    def classify(self, original: str, candidate: str) -> ExceptionPolicyResult:
        key = (original.lower(), candidate.lower())
        reverse_key = (key[1], key[0])

        if key in self._skip_pairs or reverse_key in self._skip_pairs:
            return ExceptionPolicyResult(action="skip")

        rule = self._conditional_pairs.get(key)
        if rule is None:
            rule = self._conditional_pairs.get(reverse_key)
        if rule:
            return ExceptionPolicyResult(action="conditional", value=rule)
        return ExceptionPolicyResult(action="")

    def allow_conditional(
        self, rule: str, prev_word: Optional[str], next_word: Optional[str]
    ) -> bool:
        if rule == "check_noun":
            return self._allow_check_context(prev_word, next_word)
        # Future conditional rules can be added here.
        return False

    @staticmethod
    def _allow_check_context(
        prev_word: Optional[str], next_word: Optional[str]
    ) -> bool:
        articles = {
            "a",
            "an",
            "the",
            "this",
            "that",
            "these",
            "those",
            "my",
            "your",
            "his",
            "her",
            "its",
            "our",
            "their",
            "another",
            "any",
            "each",
            "every",
        }
        cheque_context = {
            "book",
            "books",
            "account",
            "accounts",
            "payment",
            "payments",
            "deposit",
            "deposits",
            "number",
            "numbers",
            "stub",
            "stubs",
            "cheque",
            "cheques",
            "checkbook",
            "checkbooks",
        }
        if prev_word in articles:
            return True
        if next_word in cheque_context:
            return True
        return False


exception_policies = ExceptionPolicies()
