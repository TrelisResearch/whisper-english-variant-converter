## Spelling Normalisation Edge Cases

Context from our current pipeline (uk2us + Breame + VarCon → crosswalk → tokenizer → rules):

- We only manipulate isolated alphabetic tokens (URLs, emails, code spans, etc. are skipped).
- The converter defaults to `mode="spelling_only"`; the lexical table is a small curated list you can opt into.
- Tokens are lowercased internally, mapped via the crosswalk, then re-inflected to match casing (ALL CAPS, Title Case, lowercase).

Within that scope, here are the main classes of edge cases and potential mitigation strategies. No code changes have been made yet; this document is a design discussion.

---

### 1. Risk of changing meaning (context issues)

- **Homographs / POS-sensitive forms**
  - `practice` (noun) vs `practise` (verb) in UK style.
  - `tire` (verb) vs `tyre` (wheel).
  - Our token-level normaliser can’t disambiguate; it will swap every occurrence according to the crosswalk.
- **Proper names and quoted titles**
  - Company names, book titles, product names (e.g. “The Color Purple”, “Center for Economic Studies”).
  - Titles or quoted strings might be intentionally US-style; we might be misquoting when we "correct" them.

**Mitigation ideas**
1. **Context-aware pattern filters**: Skip tokens inside quotation marks, Title Case sequences, or brand name lists.
2. **POS-aware substitution**: For specific pairs (practice/practise), run a lightweight POS tagger or simple heuristic (e.g., `practice` followed by a noun stays as the noun). This increases complexity and latency.
3. **User-supplied allow/deny lists**: Provide config hooks so users can exempt specific tokens (product names, project names) from normalisation.

---

### 2. Domain and formatting problems

- **Links and handles**: `color.com`, `support@color.org`, `#ColorFest`.
  - Already mitigated by tokenizer heuristics (`://`, `@`, `#`), but any gaps could break links.
- **Code / CLI flags / file paths**
  - Tokens like `--color=auto` or `C:\Users\Forrest`.
  - Already skipped because they contain non-alphabetic characters, but mixed cases (e.g., `Color` in code comments) might slip through.

**Mitigation ideas**
1. Continue to improve token heuristics (e.g., skip tokens containing digits or underscores).
2. Provide explicit markers (custom spans) that callers can wrap around text that must remain untouched.

---

### 3. Style consistency and evaluation workflow

- **Implicit style guide**: We currently enforce -ise/-our because that’s what uk2us/Breame map to, but some UK organisations prefer -ize (Oxford style). Need to document our stance or make it configurable (e.g., toggle VarCon’s Z entries).
- **Original vs normalised text**: Post-processing hides the raw Whisper output. For debugging, model comparison, or finetuning, you often want both.

**Mitigation ideas**
1. **Configurable dialect profiles**: e.g., `profile="guardian"` vs `profile="oxford"`, controlling which rows from VarCon are applied.
2. **Dual storage**: Always persist both `raw_text` and `normalized_text`. Treat the normaliser as a reversible post-process.
3. **Stats logging**: Keep swap counts per transcript so you can review how aggressive the normaliser was.

---

### 4. Limits of spelling-only normalisation

- **Lexical differences**: `apartment↔flat`, `truck↔lorry`, `cookie↔biscuit` need curated data and user opt-in.
- **Punctuation & quotation**: US vs UK quotes (“double” vs ‘single’), Oxford comma, etc., are beyond spelling and require style-specific rewriters.
- **Overall “tone”**: Even with perfect spelling swaps, transcripts can still feel American in word choice and punctuation.

**Mitigation ideas**
1. **Custom lexical lists**: Let users maintain `data/raw/breame_meanings.csv` or another source for safe lexical swaps; default to off.
2. **Style-aware grammar tools**: Optionally run the output through a UK-style grammar checker (e.g., LanguageTool with en-GB rules) after spelling conversion.
3. **Transparency**: Document what the normaliser does *not* handle so downstream teams don’t overpromise (“British English Whisper” still needs additional processing).

---

### Summary of current stance

- Token-level spelling swaps only (6.3k US↔UK entries after dedup). Lowercase-only VarCon parsing avoids proper-noun bleed.
- Lexical swaps require explicit opt-in (`mode="spelling_and_lexical"`) and currently cover a handful of curated pairs.
- Tokenizer skips obvious protected spans (URLs, emails, hashtags, code-ish tokens) but can still touch verbs vs nouns or quoted titles.

### Potential next steps (if we decide to improve)

1. **Exception lists / configuration**: Provide CLI flags or config files to control which pairs are applied, or to exempt specific tokens.
2. **Context heuristics**: Start with simple rules (e.g., skip Title Case tokens, skip tokens within quotes) to reduce mis-corrections in names/titles.
3. **Profile support**: Expose VarCon filters (choose between B vs Z columns) to align with Oxford vs Guardian spelling preferences.
4. **POS tagging**: For high-impact pairs (practice/practise), integrate a lightweight POS tagger to apply correct variants.
5. **Extended lexical coverage**: If we want true UK phrasing, invest in a larger lexical dataset and possibly translation penalties.

These items can be referenced in `build.md` and prioritised as needed once we decide how far beyond pure spelling swaps we want to go.
