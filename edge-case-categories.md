## Categorising High-Risk Swaps

Using the consolidated list (`edge-case-final.md`), I’ve grouped items into:

1. **Skip (never swap)** — we should exclude these from the crosswalk entirely; swapping them nearly always breaks meaning.
2. **Always swap** — despite lingering concerns (e.g., `color→colour`), we still want to convert these because the benefit outweighs the risk.
3. **Conditional** — swaps that need simple criteria (regex/heuristics) before applying; default to “skip” until the criteria passes.

### 1. Skip (never swap)

- `check/checked/checks/checking ↔ cheque/chequed/cheques/chequing`
- `practice/practise` family (noun vs verb)
- `license/licence` (verb vs noun)
- `meter/metre` (device vs unit)
- `disk/disc` (computing)
- `draft/draught` family (verb vs noun)
- `snowplow/plow` family (verb usage)
- `siphon/syphon` (scientific spelling already accepted in UK)
- `tire/tyre` family (verb vs noun)
- `ton/tonne` (imperial vs metric)
- `ass/ass ↔ arse` (donkey vs insult)
- `bark/barque` (verb vs ship)
- `curb/kerb` (verb vs curb-stone)
- `drought/drouth` (archaic form)
- `gibe/jibe`
- `sake/saki` (idiom vs drink)
- `orang/ourang` (short form for orangutan)
- `story/storey` (narrative vs building floor)
- `siphon/syphon` derivatives (repeat for completeness)
- `plowboy/plowshare` etc. (same reasoning as plow)
- `snowplow's/snowplows` etc. (already covered)
- `phonies/phoneys` (acceptable to leave as US spelling)
- `specialty/speciality` (industry-specific; skip until configurable)
- `whiskey/whisky` family (brand-dependent)
- `flier/flyer` (symmetric mapping; leave alone)
- `filter/philtre` (philtre is archaic)
- `naught/nought` (idiom vs zero)

These can go straight into `data/exceptions/spelling_exceptions.csv` and be skipped automatically.

### 2. Always swap

- `color/colour` family (unless we add per-brand exceptions later).
- `organize/organise`, `realize/realise`, etc. (no ambiguity; safe to keep swapping).
- `neighbor/neighbour`, `favor/favour` (if we accept the UK style wholesale; only revisit if product names require exceptions).

### 3. Conditional swaps

Use simple heuristics or config flags:

- `check/cheque`: swap only when the token is clearly a noun (e.g., preceded by “a/the” and followed by “check” context words like “book,” “account,” or numerals). Otherwise keep the verb as “check.”
- `specialty/speciality`: allow swap when we know the domain (e.g., medical transcripts); skip elsewhere.
- `phonies/phoneys`: style preference; treat as optional.
- `plow/plough`: apply when context indicates a noun (“snowplough”); skip for verbs (“plow through”).
- `siphon/syphon`: swap only if the domain is non-scientific (or let the user opt out via config).
- `willful/wilful`: swap only if the customer opts into UK legal style; otherwise keep US spelling.

Implementation idea:
- Extend `data/exceptions/spelling_exceptions.csv` with a `policy` column (`skip`, `swap`, `conditional`).
- Conditional entries would point to simple heuristics (regex, adjacency checks) implemented in the normalizer.

Once we agree on the policy, I’ll update the CSV to mark each entry as `skip` or `configurable`, and wire the build/runtime logic accordingly.
