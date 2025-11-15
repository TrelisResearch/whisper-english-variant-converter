# License Notes

All source code in this repository is released under the MIT License (see `LICENSE`).

## Data sources

| Source | License | Location |
| --- | --- | --- |
| uk2us | MIT | `data/raw/uk2us.csv` |
| Breame (spellings + lexical) | MIT | `data/raw/breame_spellings.csv`, `data/raw/breame_meanings.csv` |
| SCOWL + VarCon | Permissive / Public Domain | `data/raw/scowl_varcon.csv` |

Derived tables live in `data/derived/` and are also copied into
`src/english_variant_converter/data/` so they ship with the package. GPL-licensed
references (e.g., Hyperreality's American–British Translator) are never copied into the
repo; they are only referenced externally for QA and test oracles.
