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
| Claim alignment | **Lexical baseline only** — see below |
| Material omission | Architecture + gates implemented; no real comparison data |
| Evidence model | Architecture only; no retrieval, no authentication |
| Source dependence | Model implemented; no real dependency data |
| Compare / Event Record | Synthetic fixture only |
| Fact checking | **Does not exist.** Architecture ≠ fact checker. |
| URL ingestion | Not implemented, deliberately deferred |
| Network access | None, anywhere |

## Specific weaknesses

### Claim alignment is lexical, not semantic
`services/comparison/claims.align_pair` uses content-token Jaccard overlap. It
will fail on paraphrase with low lexical overlap, and it cannot distinguish
propositions that share vocabulary but differ in meaning. It is honest about
this — it returns `uncertain` in the ambiguous band and `uncertain` is barred
from grounding an omission — but it is a baseline, not understanding.

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
from plain text. It will mis-type unusual formatting. Two known mis-typings were
found and fixed during adversarial review; others likely remain.

## Verification gaps in this environment

Playwright and Chromium are unavailable on this host, so **no runtime browser
check was executed in this pass**. Consequently:

- 21 of 32 prototype-parity rows are `UNVERIFIED` (`tests/prototype-parity/PARITY_MATRIX.md`)
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
