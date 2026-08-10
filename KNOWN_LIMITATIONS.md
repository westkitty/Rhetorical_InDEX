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

### Claim alignment: identity is exact, everything else fails closed

`services/comparison/claims.align_pair` no longer treats high lexical overlap as
evidence of propositional identity. **Absence of detected divergence is not
affirmative evidence that two propositions are the same** — a bag-of-words score
cannot see semantic role, so "injured 12 and killed 40" scored a perfect 1.00
against "injured 40 and killed 12".

`same_proposition` — the ONLY relation that can ground a Material Omission —
now requires **exact identity after presentation-level normalization**
(`services/comparison/divergence.canonical_proposition`): case, unicode form,
whitespace, terminal punctuation, and numeric surface form (`12%` == `12
percent`, `1,000` == `1000`, `$2 million` == `$2,000,000`). Word order is
deliberately preserved, because order carries role.

Everything else — however similar — is at most `compatible` and is **never
usable for omission**. Bounded numeric / temporal / polarity / negation
divergence checks (`divergence.py`) still run and downgrade a pair further to
`uncertain` or `contradictory`, and they surface conflicts for display, but they
are no longer load-bearing for identity.

**Consequences, stated plainly:**

- Paraphrase is not recognized. "The council backed the plan" and "The council
  supported the plan" are different propositions to this system.
- Any true statement worded differently by two sources will fail to ground an
  omission. That is a deliberate, large class of false negatives.
- This is NOT semantic entailment and NOT general contradiction detection.

Refusing a true omission is an acceptable cost. Asserting a false one is not.

### Source independence is tri-state and must be earned

`assess_independence` classifies every source pair as **confirmed independent**,
**dependent**, or **unresolved**. Material Omission requires *confirmed* mutual
independence between at least two supporting sources.

- No dependency data at all -> unresolved -> **refused**
- `unknown` relationship -> unresolved -> **refused**
- `independent_reporting` at Low confidence -> unresolved -> **refused**
- `independent_reporting` at Medium/High -> confirmed
- syndication / quotation / citation / shared source -> dependent -> **refused**

Absence of evidence of dependence is not evidence of independence. In practice
this means an omission cannot be produced at all until someone has explicitly
recorded the source-dependence relationships — which is correct, and which is
why the synthetic fixture now carries them.

Bounded semantics: `quotation` and `citation` collapse two sources into one
origin *for corroboration purposes*, because a source repeating another's
reporting is not a second witness. They do not assert anything broader about the
outlets themselves.

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

### Pressure/confidence: P4 with Low confidence is still not reachable
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
