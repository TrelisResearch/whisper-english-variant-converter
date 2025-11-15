## english-variant-converter Build Guide

A succinct reference for building and extending the english-variant-converter library + CLI that normalises English spelling variants (US, UK, AU, CA, etc.). The initial focus is spelling-only replacements (e.g. `color → colour`), with an opt-in lexical translation mode (e.g. `apartment ↔ flat`) planned for later versions and Whisper ASR pipelines.

> **uv everywhere**: all Python-related commands (install, run, lint, test) should use [uv](https://github.com/astral-sh/uv). Examples below use `uv run ...` so environments stay reproducible without activating virtualenvs manually.

### Licensing snapshot

| Source | License | Can we vendor it? | Notes |
| --- | --- | --- | --- |
| uk2us | MIT | ✅ Yes | Include attribution (NOTICE/README) |
| Breame | MIT | ✅ Yes | Provides spelling + meaning-difference tables |
| SCOWL + VarCon | Custom permissive / PD | ✅ Yes | Author explicitly permits non-GPL reuse |
| Hyperreality American–British Translator | GPL-3.0 | ❌ No (directly) | Treat purely as inspiration/tests; do not ingest data |

The guidance below reflects this table: we vendor uk2us + Breame now, layer SCOWL/VarCon for multi-variant support, and only reference Hyperreality as an external oracle.

---

## 1. Goals

### v0 – US ↔ UK spelling normaliser
- Provide a canonical crosswalk of US/UK spelling pairs.
- Ship a Python API `convert(text, source="en_US", target="en_GB")`.
- Ship a CLI `evc --from en_US --to en_GB < input.txt > output.txt`.
- Guard Rails for Whisper output: avoid URLs/emails/code snippets and try to keep proper nouns unchanged via simple heuristics.

### v1 – Multi-variant spelling (US, UK, AU, CA)
- Extend the crosswalk with SCOWL/VarCon data to cover `en_AU` and `en_CA`.
- Keep the API surface the same; expose `SUPPORTED_VARIANTS` for CLI and API validation.

### v2 – Optional lexical “translation”
- Provide an opt-in mode `mode="spelling_and_lexical"` that can flip lexical choices (e.g. `truck ↔ lorry`).
- Keep lexical replacements disabled by default for Whisper compatibility.

### Planned Whisper integrations
- Example notebooks/docs for Whisper.cpp + Whisper Turbo pipelines (local/offline).
- Example docs for a Whisper server (ctranslate2 backend).
- Integration material lives under `examples/` or documentation; no binaries bundled.

---

## 2. Repository Layout

```
english-variant-converter/
├── BUILD.md
├── README.md
├── pyproject.toml
├── src/
│   └── english_variant_converter/
│       ├── __init__.py
│       ├── api.py          # public convert() API
│       ├── rules.py        # core conversion logic + lookup tables
│       ├── tokenizer.py    # text segmentation that skips protected spans
│       └── data_loader.py  # loads derived crosswalks
├── data/
│   ├── raw/                # raw downloaded inputs (not shipped to PyPI)
│   └── derived/
│       ├── spelling_crosswalk.csv
│       └── lexical_crosswalk.csv   # future
├── scripts/
│   ├── build_crosswalk.py  # ingest raw → derived CSV/JSON
│   └── verify_crosswalk.py # consistency checks
├── examples/
│   ├── basic_usage.ipynb
│   ├── cli_examples.md
│   ├── whisper_cpp_pipeline.md
│   └── whisper_server_pipeline.md
└── tests/
    ├── test_api.py
    ├── test_rules.py
    └── test_whisper_like_text.py
```

---

## 3. Data Sources and Crosswalk Build

### 3.1 Canonical data model
- `variant_id`: unique row id.
- `lemma`: base form or word key.
- `en_US`, `en_GB`, `en_AU`, `en_CA`: variant spellings (populate AU/CA once SCOWL data lands).
- `notes`: optional metadata (`practice/practise noun/verb` kind of hints).
- `source`: `uk2us`, `breame`, `scowl`, `manual`, etc. (reference-only datasets like Hyperreality stay outside the repo).
- `type`: `"spelling_only"` or `"lexical_choice"`.
- v0 primarily uses `en_US`, `en_GB`, `type="spelling_only"`.

### 3.2 Source ingestion steps

#### Source 1 – uk2us (R package)
1. Install the package in R and dump the crosswalk once:
   ```r
   library(uk2us)
   write.csv(ukus_crosswalk, "data/raw/ukus_crosswalk.csv", row.names = FALSE)
   ```
2. Commit the CSV under `data/raw/`.
3. `scripts/build_crosswalk.py` should load the CSV, map columns (`uk → en_GB`, `us → en_US`), and mark `type="spelling_only"`, `source="uk2us"`.

#### Source 2 – Breame
1. Add Breame as a dev dependency or vendor its raw word lists.
2. Extract spelling-only entries (ignore meaning differences for v0).
3. Merge rows that are missing in the `(en_US, en_GB)` pair set; mark `source="breame"`, `type="spelling_only"`.
4. For v2 lexical conversions, reuse Breame’s “meaning difference” lists (also MIT) as the basis for `type="lexical_choice"` entries, keeping them opt-in.

#### Source 3 – SCOWL / VarCon (v1+)
1. Download SCOWL + VarCon into `data/raw/scowl/`.
2. Extend the build script (even if initially as TODOs) to:
   - detect entries with variant labels across US/UK/CA/AU.
   - populate the multi-variant columns once ready.

> **Reference-only sources**: Projects like Hyperreality (GPL-3) are useful for verifying coverage, but we do not copy their data. Use them offline to cross-check pairs or as test oracles in CI without importing their tables.

### 3.3 Building derived tables
`scripts/build_crosswalk.py` flow:
1. Load each raw source with normalised columns.
2. Merge them into a single table, deduplicating on `(en_US, en_GB)`.
3. Aggregate source provenance (list or joined string) when rows come from multiple sources.
4. Emit:
   - `data/derived/spelling_crosswalk.csv`
   - (later) `data/derived/lexical_crosswalk.csv`

To rebuild everything:

```bash
uv run python scripts/build_crosswalk.py
uv run python scripts/verify_crosswalk.py
```

---

## 4. Core Library Implementation

### 4.1 Tokenisation / segmentation
- Goal: touch only words that truly need conversion; leave URLs, emails, handles, code blocks, etc. alone.
- `tokenizer.py` should emit a sequence of tokens with metadata (`is_word`, `is_protected`, original text).
- Suggested heuristics:
  - treat alphabetic sequences as words; everything else as separators.
  - mark tokens containing `://`, `@`, or `#` as protected.
  - optionally recognise backtick/code-fence blocks for later enhancements.

### 4.2 Conversion rules (`rules.py`)
- Load `spelling_crosswalk.csv` at import time (or lazily) into bidirectional dictionaries:
  - `map_en_US_to_en_GB`, `map_en_GB_to_en_US`, etc.
- `convert_token(token, source, target, mode)` should:
  1. Detect the case style (lower, Title, upper) and remember it.
  2. Lookup the lowercase form in the appropriate mapping (and optional lexical tables when `mode="spelling_and_lexical"`).
  3. Reapply the original casing to the replacement.
  4. Return the untouched token when no mapping exists.

### 4.3 Public API (`api.py`)

```python
from .rules import convert_token
from .tokenizer import tokenize

SUPPORTED_VARIANTS = ["en_US", "en_GB"]  # extend once AU/CA are ready

def convert(
    text: str,
    source: str = "en_US",
    target: str = "en_GB",
    mode: str = "spelling_only",
) -> str:
    assert source in SUPPORTED_VARIANTS
    assert target in SUPPORTED_VARIANTS
    if source == target:
        return text

    tokens = tokenize(text)
    converted_tokens = []
    for token in tokens:
        if token.is_word and not token.is_protected:
            converted_tokens.append(
                convert_token(token.text, source=source, target=target, mode=mode)
            )
        else:
            converted_tokens.append(token.text)
    return "".join(converted_tokens)
```

---

## 5. CLI
- Provide an entry point (e.g. `cli.py` or `__main__.py`) wired via `pyproject.toml`:
  ```toml
  [project.scripts]
  evc = "english_variant_converter.cli:main"
  ```
- CLI sketch:

```python
import argparse
import sys

from .api import SUPPORTED_VARIANTS, convert

def main():
    parser = argparse.ArgumentParser(
        description="Convert between English spelling variants."
    )
    parser.add_argument("--from", dest="source", default="en_US",
                        choices=SUPPORTED_VARIANTS)
    parser.add_argument("--to", dest="target", default="en_GB",
                        choices=SUPPORTED_VARIANTS)
    parser.add_argument("--mode", default="spelling_only",
                        choices=["spelling_only", "spelling_and_lexical"])
    args = parser.parse_args()

    text = sys.stdin.read()
    result = convert(text, source=args.source, target=args.target, mode=args.mode)
    sys.stdout.write(result)
```

Invoke the CLI via uv as well: `uv run evc --from en_US --to en_GB < input.txt > output.txt`.

### Swap statistics / QA
- Add an optional code path (e.g. `convert(..., return_stats=False)` or a helper like `convert_with_stats`) that returns both the converted text and a summary of replacements made.
- Stats payload can include fields such as total tokens, number of converted tokens, list of `(source_word, target_word, count)` pairs, and skipped/protected tokens.
- Expose the same capability in the CLI via `--stats` to print a compact table (or JSON when `--stats json`) so users can spot-check transcripts with very few or many changes without reading the full text.
- Persist stats if needed by piping `uv run evc ... --stats json > swaps.json` for bulk QA or regression tracking.

---

## 6. Testing

### Unit tests (`tests/`)
- `test_api.py`
  - round-trip conversions (US → UK → US).
  - case-preservation assertions (`Color`, `COLOR`, etc.).
- `test_rules.py`
  - token-level conversions for each direction and mode.
- `test_whisper_like_text.py`
  - ensures URLs/emails/code blocks stay untouched and that heuristics mimic Whisper output quirks.

Add integration-style tests later for CLI pipelines once the Whisper examples are implemented. Use `uv run pytest` (or targeted invocations) so dependencies resolve via uv without extra setup. Tests that rely on GPL datasets must download them at runtime and avoid committing them to the repo.
