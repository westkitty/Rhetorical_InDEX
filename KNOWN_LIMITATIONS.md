# Known Limitations

Written to be read *against* the rest of the documentation. If any other file in
this repository contradicts this one, this file is correct and the other file is
a bug.

## The headline limitation

**No detector in this repository has been calibrated.** There is no benchmark
result, no precision figure, no recall figure, no accuracy claim. The benchmark
machinery exists and is self-tested; the corpus is empty because no human has
annotated anything.

Everything the system outputs is a **candidate for human review**.

## Detector levels and what each can be trusted for

| Level | What it is | Trust |
|---|---|---|
| 1 — Experience Prototype (`Rhetorical_InDEX.html`) | Deterministic synthetic demonstration | Demonstrates interaction. Not an instrument. |
| 2 — Local Preview (`apps/web`) | Regex heuristics on pasted text, in-browser | Unbenchmarked. Candidates only. Non-authoritative. |
| 3 — Instrument Alpha (`services/rhetoric`) | Taxonomy-governed pipeline with strict validation | Structurally complete, **uncalibrated**. Not reachable from the browser build. |

Level 3 is not wired into the web UI. Doing so requires a service boundary, and
network exposure remains deliberately deferred. The browser build runs Level 2
and says so on screen.

## Coverage of the taxonomy

**4 of 12 mechanisms are implemented** at Level 3: loaded language,
presupposition, agent suppression, false dilemma. The other eight are defined in
the taxonomy but have no detector. Requesting one raises rather than returning
an empty result that could be misread as "none found".

## Capability status

| Capability | State |
|---|---|
| Intrinsic rhetorical analysis | Implemented, uncalibrated |
| Exact-span localization + occurrence disambiguation | Implemented, tested |
| Voice provenance | Implemented; does not identify *which* speaker |
| Pressure / confidence separation | Implemented, tested |
| Coverage accounting, partial states | Implemented, tested |
| Long-document batching | Implemented, tested to 601 passages |
| Claim alignment | Lexical baseline **plus bounded numeric/temporal/polarity/negation divergence guards** — see below |
| Material omission | Architecture + gates implemented; no real comparison data |
| Evidence model | Architecture only; no retrieval, no authentication |
| Source dependence | Model implemented; no real dependency data |
| Compare / Event Record | Synthetic fixture only |
| Fact checking | **Does not exist.** Architecture ≠ fact checker. |
| URL ingestion | Not implemented, deliberately deferred |
| Network access | None, anywhere |

## Specific weaknesses

### Claim alignment is primarily lexical, with bounded divergence guards
`services/comparison/claims.align_pair` scores similarity with content-token
Jaccard overlap. On top of that, `services/comparison/divergence.py` applies
**deterministic, bounded, high-value conflict checks** before any high-overlap
pair may be treated as agreement:

- **numeric** — percent, currency, clock time and scaled integers, with
  normalization so `12%` == `12 percent`, `1,000` == `1000`, `$2 million` ==
  `$2,000,000`
- **temporal** — weekday, month + day, year
- **polarity** — a small explicit antonym list (direction, benefit, approval,
  permission, stance, safety, legality, presence, gain, sequence)
- **negation** — explicit negation markers

Any detected conflict forces `uncertain` / Low confidence and is **not usable
for Material Omission**. Explicit negation yields `contradictory`.

**This is not general contradiction detection and not a semantic entailment
engine.** It will still miss:

- paraphrase with little lexical overlap (aligns as `unrelated`)
- antonyms outside the bounded pair list
- unit conversions (miles vs kilometres)
- contradictions requiring world knowledge
- numeric conflicts expressed only in prose ("doubled" vs "halved")

The design bias is **fail-closed**: an undetected divergence stays `uncertain`,
never `compatible`. Nothing an undetected conflict can do will turn it into
positive evidence of agreement.

The same bias produces **conservative false negatives**, which are accepted
deliberately. `"the fund holds $2 million"` and `"the fund holds $2,000,000"`
assert the identical fact and are correctly found to have *no conflict*, but
their token overlap (0.60) falls below the `same_proposition` threshold, so the
pair is not usable to ground an omission. Refusing a true statement is a cost we
take; asserting a false one is not.

Separately, **only `same_proposition` may ground a Material Omission**. The
specificity relations (`more_specific`, `less_specific`) are excluded because
they are token-count comparisons, not entailment checks — and the direction is
counter-intuitive: `align_pair(candidate, peer)` reports `more_specific` when
the *candidate* exceeds the peer, which is exactly when the peer does **not**
establish it.

### Confidence may still read as factual confidence
"Confidence: High" means *the detector is confident this rhetorical mechanism is
present*. It does **not** mean the sentence is true or false. Copy mitigates
this, but the word carries unavoidable connotation. Unresolved.

### Heuristic candidate generation is lexicon-bound
Level 3's candidate generators use curated word lists and grammatical patterns.
They will miss loaded language outside the lexicon and fire on unusual-but-
legitimate constructions. The lexicons are ideologically symmetric by
construction, but they are not exhaustive, and no measurement of their coverage
exists.

### Voice classification does not attribute to a named speaker
The system can tell you a span is `quoted_speaker`; it cannot yet tell you
*whose* quote it is.

### Material omission has never run on real data
The gates are implemented and adversarially tested, but every test uses
synthetic fixtures. Behavior against real coverage is unmeasured.

### Segmentation is heuristic
Passage typing (heading / blockquote / list item / caption) infers structure
from plain text. It will mis-type unusual formatting. Three known mis-typings
were found and fixed across adversarial review passes (caption keywords,
unbalanced-quote fragments read as headings); others likely remain.

### Pressure/confidence: P4 with Low confidence is not reachable
Pressure and confidence are structurally independent (`score_confidence` takes
no pressure argument) and the shipped heuristic pipeline now reaches P4+Medium,
P3+Medium, P2+High, P1+Low and P1+Medium. It does **not** reach P4+Low: the
generators that produce P4 pressure are the same lexical matches the provider is
most certain about. This is a property of the current heuristic provider, not of
the model; a future provider with genuinely uncertain high-pressure detections
would produce it. Recorded as `Z-35` (UNVERIFIED) rather than forced with
contrived input.

### The `by`-agent test is a bounded stop-list
Agent-suppression exclusion distinguishes real agents ("by the department") from
temporal, duration and measurement adjuncts ("by Tuesday", "by three weeks", "by
20 percent") using an explicit non-agent stop-list plus a numeric guard. An
unusual non-agent noun outside that list will still read as a named agent and
over-exclude. Bounded and inspectable by design, not a parser.

## Verification gaps in this environment

Playwright and Chromium are unavailable on this host, so **no runtime browser
check was executed in this pass**. Consequently:

- 23 of 32 prototype-parity rows are `UNVERIFIED` (`tests/prototype-parity/PARITY_MATRIX.md`)
- accessibility behaviors (focus trap, focus restoration, Escape, keyboard route)
  are source-supported but **runtime-unverified**
- responsive/touch behavior is **runtime-unverified**
- `qa/runtime-results.json` and `qa/screens/*.png` are **stale**, produced against
  artifact `8b3086f5…` while the current artifact is `1a5ebc36…`

Never verified in any pass: Safari/iPadOS, Firefox, a real screen-reader session.

## What would remove these limitations

1. Human annotation of a pilot corpus → run `benchmarks/scripts/evaluate.py` → first real calibration numbers.
2. A browser environment → run `npm run qa:runtime` → convert UNVERIFIED parity rows.
3. A service boundary → make Level 3 reachable from the UI.
4. Real comparison data → exercise omission gates against non-synthetic coverage.
5. A retrieval + authentication layer → make the evidence architecture operational.
