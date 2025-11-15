# english-variant-converter

Convert transcripts or free-form English text between spelling variants (US, UK, AU, CA, ...).

- **Library API**: `english_variant_converter.convert(text, source="en_US", target="en_GB")`
- **CLI**: `uv run evc --from en_US --to en_GB < input.txt > output.txt`
- **Swap stats**: add `--stats` (table) or `--stats json` for machine-readable QA outputs.
- **Default behavior**: `mode="spelling_only"` (lexical swaps are opt-in via `--mode spelling_and_lexical`).

## How it works

1. `scripts/build_crosswalk.py` ingests permissive sources (uk2us via R, Breame, SCOWL/VarCon) and emits a unified spelling vocabulary (~6.3k rows). VarCon entries are parsed via `scripts/parse_varcon.py`, which skips capitalized/proper-noun tokens so everyday words (e.g., “for”) don’t inherit spurious mappings. Entries are deduplicated in priority order (uk2us → Breame → VarCon) so each en_US/en_GB pair appears only once. An optional lexical vocabulary (default = curated handful of pairs) powers `mode="spelling_and_lexical"`.
2. These CSVs ship inside the package (`src/english_variant_converter/data/*.csv`).
3. At runtime, `rules.py` loads the CSVs into bidirectional maps and `tokenizer.py` splits Whisper-style text while protecting URLs, email handles, hashtags, code spans, and CamelCase names that should stay untouched.
4. `english_variant_converter.convert(...)` walks each token, applies mappings, and (optionally) returns stats showing how many swaps happened.

## Getting started

```bash
uv sync  # install deps declared in pyproject
uv run pytest
```

The project ships with a small default crosswalk built from the permissively licensed
uk2us + Breame datasets. To refresh the derived data after updating the raw CSVs, run:

```bash
uv run python scripts/build_crosswalk.py
uv run python scripts/verify_crosswalk.py
```

More context lives in [`build.md`](build.md).

## Using Whisper + the crosswalk

Example commands (based on a local `whisper.cpp` checkout):

```bash
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp

cmake -B build
cmake --build build -j --config Release

sh ./models/download-ggml-model.sh large-v3-turbo-q8_0

cd ../

./whisper.cpp/build/bin/whisper-cli -m whisper.cpp/models/ggml-large-v3-turbo-q8_0.bin -f samples/us_english-us_accent.mp3 --output-file samples/transcripts/us_english-us_accent -otxt -ovtt -osrt
```

Once you have a transcript file, run it through the converter. Examples:

```bash
cd whisper-english-variant-converter

BASE="samples/transcripts/us_english-us_accent"

uv run evc --from en_US --to en_GB --stats table \
  < "${BASE}.txt" \
  > "${BASE}-uk_transcription.txt"
```
```bash
# Convert a VTT file (generated via `whisper-cli ... -ovtt "${BASE}.vtt"`).
uv run evc --from en_US --to en_GB \
  < "${BASE}.vtt" \
  > "${BASE}-uk_transcription.vtt"
```
