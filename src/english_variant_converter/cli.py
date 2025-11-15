from __future__ import annotations

import argparse
import json
import sys
from typing import Iterable

from .api import SUPPORTED_VARIANTS, convert


def _format_table(stats) -> str:
    lines = [
        f"Total word tokens: {stats.total_tokens}",
        f"Converted tokens: {stats.converted_tokens}",
        f"Protected tokens: {stats.protected_tokens}",
    ]
    if stats.swaps:
        lines.append("")
        lines.append("Swaps:")
        width = max(len(s.source) for s in stats.swaps)
        for swap in stats.swaps:
            lines.append(f"  {swap.source:<{width}} → {swap.target} ({swap.count})")
    else:
        lines.append("")
        lines.append("No swaps recorded.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evc", description="Convert English text between spelling variants."
    )
    parser.add_argument(
        "--from",
        dest="source",
        choices=SUPPORTED_VARIANTS,
        default="en_US",
        help="Source variant (default: en_US)",
    )
    parser.add_argument(
        "--to",
        dest="target",
        choices=SUPPORTED_VARIANTS,
        default="en_GB",
        help="Target variant (default: en_GB)",
    )
    parser.add_argument(
        "--mode",
        choices=["spelling_only", "spelling_and_lexical"],
        default="spelling_only",
        help="Whether to apply only spelling changes or also lexical substitutions.",
    )
    parser.add_argument(
        "--stats",
        choices=["table", "json"],
        help="Emit swap statistics to stderr (table or json).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    text = sys.stdin.read()
    if args.stats:
        converted, stats = convert(
            text,
            source=args.source,
            target=args.target,
            mode=args.mode,
            return_stats=True,
        )
        if args.stats == "json":
            print(json.dumps(stats.to_dict(), indent=2), file=sys.stderr)
        else:
            print(_format_table(stats), file=sys.stderr)
    else:
        converted = convert(text, source=args.source, target=args.target, mode=args.mode)

    sys.stdout.write(converted)


if __name__ == "__main__":
    main()
