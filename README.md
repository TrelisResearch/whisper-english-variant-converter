# english-variant-converter

Convert transcripts or free-form English text between spelling variants (US, UK, AU, CA, ...).

- **Library API**: `english_variant_converter.convert(text, source="en_US", target="en_GB")`
- **CLI**: `uv run evc --from en_US --to en_GB < input.txt > output.txt`
- **Swap stats**: add `--stats` (table) or `--stats json` for machine-readable QA outputs.

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

./whisper.cpp/build/bin/whisper-cli -m whisper.cpp/models/ggml-large-v3-turbo-q8_0.bin -f samples/uk_english-uk_accent.mp3 --output-file samples/transcripts/uk_english-uk_accent -otxt -ovtt -osrt
```

Once you have a transcript file, run it through the converter. Examples:

```bash
cd whisper-english-variant-converter

# Convert the default TXT transcript produced by Whisper.
uv run evc --from en_US --to en_GB --stats table \
  < samples/jfk.wav.txt \
  > samples/jfk_uk.txt

# Convert a VTT file (generated via `whisper-cli ... -ovtt samples/jfk.vtt`).
uv run evc --from en_US --to en_GB \
  < samples/jfk.vtt \
  > samples/jfk_uk.vtt
```

If you prefer streaming everything in a single pipeline, force Whisper to emit the
transcript on stdout and pipe it directly:

```bash
./build/bin/whisper-cli -m models/ggml-large-v3-turbo-q8_0.bin \
  -f samples/jfk.wav \
  -otxt - \
  2>whisper.log \
  | uv run evc --from en_US --to en_GB --stats table \
  > samples/jfk_uk.txt
```

The `--stats table` flag prints swap statistics to stderr while the converted transcript
lands in `samples/jfk_uk.txt`. Use `--stats json` for machine-readable QA logs. For VTT
streaming, swap `-otxt -` with `-ovtt -`.
