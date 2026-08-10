# Adversarial Review — Instrument Alpha completion program

Two independent passes were run against the Level 3 detector and supporting
subsystems. Every defect below was found by attacking the implementation, not by
reading its documentation. All are fixed, and each carries a regression test
that was verified to fail when the fix is reverted.

## Pass One — attacking the new implementation

### D-001 — Canonical agentless passive silently missed (Major, fixed)

**Attack:** run the taxonomy's own worked example through the detector.

**Finding:** `Mistakes were made` produced no `agent_suppression` finding. The
passive pattern matched only participles ending `ed|en|wn|ht|pt`, so every
irregular participle (`made`, `done`, `sent`, `told`, `built`, `held`, …) was
invisible. This is a recall failure in exactly the rhetoric the mechanism
exists to catch, and it would have been baked into the first benchmark as an
apparently "hard" case.

**Fix:** explicit irregular-participle alternation in `candidates._PASSIVE`;
removed `given`/`seen`/`used` from the stative exclusion list.

**Regression:** `test_canonical_agentless_passive_is_caught`.

### D-002 — One rhetorical move double-counted (Moderate, fixed)

**Attack:** feed a sentence matching two presupposition generators.

**Finding:** `refused to explain why they allowed X` produced two overlapping
`presupposition` findings (factive-wh and factive-allowed) for a single
rhetorical move. This inflates pressure profiles and would corrupt span metrics
against a human benchmark that marked it once.

**Fix:** `models.collapse_nested_same_mechanism` — collapses same-mechanism
containment only. Different mechanisms on identical or overlapping spans are
preserved, because that is the multi-tag case the product depends on.

**Regression:** `test_nested_same_mechanism_spans_collapse_to_one`,
`test_partially_overlapping_same_mechanism_spans_both_survive`,
`test_identical_spans_different_mechanisms_are_preserved`.

### D-003 — Exclusion window crossed sentence boundaries (Major, fixed)

**Attack:** place an agentless passive and a by-agent passive in adjacent
sentences.

**Finding:** `Mistakes were made during the review. The report was published by
the department.` produced **no** agent-suppression finding. The by-agent
exclusion searched a fixed 40-character window past the match, which ran into
the *next* sentence and found `by the department` there. A by-agent phrase in an
unrelated sentence was suppressing a legitimate finding.

**Fix:** `candidates._sentence_bounded_window` truncates exclusion lookahead at
the first sentence terminator.

**Regression:** `test_by_agent_in_a_later_sentence_does_not_suppress_this_one`,
plus `test_by_agent_clause_is_not_flagged_as_agent_suppression` proving the
exclusion still works when it should.

## Pass Two — fresh eyes, discarding Pass One's conclusions

Pass Two re-read the finished code as if written by someone else, and asked
specifically: *what could still pass the tests while being wrong?*

### D-004 — Coverage could report 100% while a passage was never analyzed (Major, fixed)

**Attack:** append the same passage id to `processed_passage_ids` twice.

**Finding:** `coverage_ratio` returned `1.0` for a two-passage article where only
one passage was analyzed, because the ratio counted list length rather than
distinct passages. `assert_coverage_invariant` passed, because it compared sets
and duplicates collapsed. A UI trusting `coverageRatio` would have displayed
"100% coverage" for a partial scan — precisely the "partial state masquerading
as complete" failure the design exists to prevent.

**Fix:** `coverage_ratio` and `is_complete_coverage` count distinct passages;
`assert_coverage_invariant` now rejects duplicates and unknown passage ids.

**Regression:** `test_duplicate_processed_append_cannot_inflate_coverage_to_complete`,
`test_coverage_cannot_reference_a_passage_outside_the_article`.

### D-005 — A provider bug destroyed the entire analysis (Major, fixed)

**Attack:** supply a provider whose `verify` raises `RuntimeError`.

**Finding:** the exception propagated out of `analyze_article`, so one buggy or
hostile provider aborted the whole run with a traceback instead of producing a
usable partial result. Only `ProviderUnavailable` was handled.

**Fix:** the passage loop catches any exception, records a `DetectorFailure`
with `stage="provider_error"` and the exception type, marks the passage failed
and lets the run finalize as partial/failed. The error is recorded, never
swallowed.

**Regression:** `test_provider_bug_degrades_the_run_instead_of_crashing_it`,
`test_partial_provider_bug_keeps_good_passages`.

### D-006 — Ordinary sentences misclassified as captions (Moderate, fixed)

**Attack:** segment a paragraph beginning with a caption keyword.

**Finding:** `Photo opportunities were limited for the draconian scheme rollout.`
was classified as a `caption`, which routes voice provenance to
`document_material` — a wrong attribution of the outlet's own prose to quoted
document material.

**Fix:** the caption pattern now requires a delimiter (`:`/`.`/`—`) or figure
number after the keyword.

**Regression:** `test_sentence_beginning_with_a_caption_keyword_is_not_a_caption`,
`test_genuine_captions_are_still_recognized`.

## Test-the-tests

Guards were temporarily removed to confirm the suite detects their absence.
Each mutation was reverted immediately.

| Mutation | Expected | Result |
|---|---|---|
| Remove `criteriaTriggered` requirement (allow taxonomy backfill) | suite fails | **1 failure** |
| Remove the uncertain → confidence cap | suite fails | **2 failures** |
| Remove nested same-mechanism collapse | suite fails | **1 failure** |
| Add a rogue value to `schema.json` `voiceClass` | both parity suites fail | **Node + Python both failed** |

The suite is therefore capable of detecting drift in the guarantees it claims to
protect, rather than passing vacuously.

## Product-level adversarial review

Attacking the concept rather than the code:

| Risk | Assessment |
|---|---|
| Does pressure read as deception? | Mitigated in copy: "Pressure, not factuality" on the profile card; methodology view states pressure is not factuality, side, moral worth or harm. |
| Does confidence read as *factual* confidence? | Partly mitigated by wording. **Residual risk** — see Known Limitations. |
| Does "omission" sound more certain than the evidence? | Mitigated: omissions carry `uncertaintyNotes`, are capped by the weakest grounding alignment, and synthetic sets are labelled. |
| Does Compare privilege majority framing? | No ranking by source count exists. Coverage consensus is explicitly not truth, asserted in `test_coverage_consensus_is_explicitly_not_truth`. |
| Does primary evidence get privileged beyond its status? | Mitigated: `authenticity_state` defaults to `unverified`; `verified` requires an explicit basis or construction raises. |
| Does quoted rhetoric appear to be the outlet's? | Mitigated: `voice.classify` returns `quoted_speaker`, and `uncertain` where a span straddles a quote boundary. |
| Does the profile become a hidden bias score? | Mitigated structurally: `test_profile_exposes_no_single_summarizing_number` fails if any scalar summary is added. |
| Does anything imply an ideological axis? | `test_no_political_axis_anywhere_in_the_vocabulary` scans schema + taxonomy for ideological vocabulary. |

## Residual issues not fixed in this pass

Recorded rather than silently carried; see `KNOWN_LIMITATIONS.md`.

- Claim alignment is a **lexical baseline**, not semantic. (Superseded by the
  M-01 closure below: bounded numeric/temporal/polarity divergence guards were
  added, and `compatible` no longer grounds an omission. It still misses
  paraphrase.)
- Voice classification does not resolve *which* speaker a quote belongs to.
- The Level 3 detector is not reachable from the browser build; that requires a
  service boundary which remains deliberately deferred.
- 21 of 32 prototype-parity rows are UNVERIFIED for want of a browser in this
  environment.

---

# Independent pre-merge review closure (commit `6c52220` → this commit)

An independent pre-merge review returned **NOT MERGE READY** with one Major
blocker and six bounded findings. All are closed below.

## M-01 (Major, merge blocker) — contradiction converted into evidentiary support

**Reproduced:** `align_pair` classified factually contradictory claims as
`compatible` / Medium / usable, because its only semantic guard was a
negation-word regex. Peers asserting *"city spending rose 12 percent"* let the
system emit a Material Omission asserting the target omitted *"rose 40
percent"* — a figure **no source stated** — credited to two named sources.

**Repair:**
1. New `services/comparison/divergence.py`: deterministic, bounded, inspectable
   conflict detection — numeric (percent / currency / clock / scaled integers,
   normalized so `12%` == `12 percent`, `$2 million` == `$2,000,000`), temporal
   (weekday / month-day / year), polarity (10 explicit antonym families), and
   negation. Highly polysemous tokens are deliberately excluded.
2. `align_pair` runs divergence checks **before** any agreement relation may be
   assigned. Any conflict → `uncertain` / Low / non-usable. Explicit negation →
   `contradictory`.
3. `is_usable_for_omission` narrowed from
   `{same_proposition, compatible, more_specific, less_specific}` to
   **`same_proposition` only**, and additionally requires zero divergences. The
   specificity relations are token-count comparisons, not entailment checks —
   and the direction is counter-intuitive (`more_specific` means the *candidate*
   exceeds the peer, exactly when the peer does not establish it).
4. `evaluate_candidate_omission` skips any supporting claim that diverges from
   the candidate, reports why, and asserts a closing invariant: every accepted
   grounding alignment must be divergence-free and usable. A future loosening of
   `is_usable_for_omission` still cannot emit an omission whose sources
   contradict it.

**Result:** all three reproductions now fail closed at `presence_elsewhere`; the
genuine-omission positive control still passes.

## Other findings

| ID | Repair | Result |
|---|---|---|
| **O-01** | Added `tools/check_traceability.py`: parses every ID-prefixed row, counts statuses, compares to the declared summary, exits non-zero on drift. Totals regenerated from the rows, not hand-typed. | Closed — machine-verified |
| **O-02** | `KNOWN_LIMITATIONS.md` rewritten to describe the actual guards, name what they do **not** cover, and state the fail-closed bias plus its accepted conservative false negatives. Removed the false claim that the ambiguous band was the safeguard. | Closed |
| **O-03** | Removed tier-derived certainty from `HeuristicDetectorProvider`. Confidence now rises with the count of **independently satisfied positive criteria**; confusable-neighbour overlap lowers it. Rhetorical severity no longer feeds detection certainty. | Closed — P4+Medium and P3+Medium now reachable end-to-end |
| **O-04** | A line with unbalanced quote marks can no longer satisfy the heading heuristic. Additionally, a span inside quotation marks **within a heading** now resolves to `quoted_speaker`, not `headline`. | Closed |
| **N-01** | Python parity module renamed `SchemaLoadIntegrityTests` and documented as a load-integrity check, not a parity proof; the load-bearing TS↔Python detector is named explicitly. Added independent behavioral expectations that fail when a required value is removed. | Closed |
| **N-02** | Parity matrix normalized to exactly one primary status per row; structural presence moved to the Evidence column. Totals recomputed: **9 PASS / 0 FAIL / 23 UNVERIFIED** (was an inconsistent 11/21). The checker rejects multi-status rows. | Closed |
| **N-03** | `_BY_AGENT` given an explicit non-agent stop-list plus a numeric guard and a duration pattern, so "by Tuesday", "by three weeks" and "by 20 percent" no longer read as named agents. | Closed |

## Test-the-tests (all mutations reverted)

| Mutation | Result |
|---|---|
| Allow `compatible` to ground an omission | **2 failures** |
| Disable the divergence gate in `align_pair` | **2 failures** |
| Remove numeric divergence detection | **5 failures** |
| Remove polarity divergence detection | **2 failures** |
| Remove the omission conflicting-claim skip | **1 failure** |
| Revert the unbalanced-quote heading guard | **2 failures** |
| Revert the temporal-`by` guard | **1 failure** |
| Reinstate tier-derived certainty | **1 failure** |
| Remove a required voice class from `schema.json` | **2 failures** (Python) |
| Add a rogue voice class to `schema.json` | **2 failures** (Node cross-language) |

## Accepted residual behavior

- `"$2 million"` vs `"$2,000,000"` — same fact, correctly **no conflict**, but
  token overlap (0.60) falls below `same_proposition`, so it cannot ground an
  omission. A conservative false negative, pinned by
  `test_equivalent_value_written_differently_fails_closed`.
- **P4 + Low confidence is not reachable** in the current heuristic provider
  (`Z-35`, UNVERIFIED). Recorded rather than forced with contrived input.

---

# Pre-calibration hardening pass

A post-merge source audit raised 15 Major (M-01 … M-15) and 11 Moderate
(O-01 … O-11) findings. All were reproduced with executable tests before repair.

## The central defect: M-01

`align_pair` treated *high lexical overlap with no detected divergence* as
`same_proposition`, which was usable to ground a Material Omission. Because
Jaccard is a bag of words, it cannot see semantic role — five of six
contradictory pairs were usable, including:

| A | B | Old result |
|---|---|---|
| "…treatment **caused** infertility…" | "…treatment **prevented** infertility…" | `same_proposition`, usable |
| "injured **12** and killed **40**" | "injured **40** and killed **12**" | `same_proposition`, usable |
| "moved **from Tuesday to Thursday**" | "moved **from Thursday to Tuesday**" | `same_proposition`, usable |
| "the **company** sued the **regulator**" | "the **regulator** sued the **company**" | `same_proposition`, usable |
| "platforms **must** retain metadata" | "platforms **may** retain metadata" | `same_proposition`, usable |

Extending an antonym list could never fix this: the number and time cases have
*identical token sets*.

**Repair.** `same_proposition` now requires **exact identity after
presentation-level normalization** (`divergence.canonical_proposition`): case,
unicode, whitespace, terminal punctuation and numeric surface form only. Word
order is preserved because order carries role. Everything else is at most
`compatible` and is never usable. Divergence detection still runs, but is no
longer load-bearing for identity — it downgrades further, never upgrades.

Cost: paraphrase no longer grounds omissions. Accepted deliberately.

## All findings

| ID | Status | Repair |
|---|---|---|
| M-01 | CLOSED | Exact normalized propositional identity; divergence demoted to a downgrade-only signal |
| M-02 | CLOSED | Tri-state `assess_independence`; omission requires CONFIRMED mutual independence |
| M-03 | CLOSED | Supporting/target claims must belong to the exact ComparisonSet; source/article mapping enforced |
| M-04 | CLOSED | `parse_instant` — timezone-aware ISO-8601, naive and malformed rejected |
| M-05 | CLOSED | `reportable_state(confidence, applies)`; only `applies=="yes"` can confirm |
| M-06 | CLOSED | Criteria must be verbatim members of the mechanism's taxonomy record; strict array/number parsing; one canonical semantic validator |
| M-07 | CLOSED | Relation confidence caps claim state |
| M-08 | CLOSED | Corroboration counts distinct evidence items, never relation rows |
| M-09 | CLOSED | `benchmarks/scripts/validate_corpus.py`; invalid adjudicated files are FATAL |
| M-10 | CLOSED | Taxonomy corrected (quoted speech is not an exclusion) + version bump to `1.1.0-alpha0` |
| M-11 | CLOSED | `voiceClass` now blocks auto-merge |
| M-12 | CLOSED | `annotatorSubmissions[]` / `annotations[]` / `resolutions[]` preserve original positions |
| M-13 | CLOSED | Parity claim rescoped to *controlled vocabulary*; domain-shape divergence documented |
| M-14 | CLOSED | Pressure scorer reconciled with the taxonomy rubric; every example is a golden test |
| M-15 | CLOSED | Level 2 derives voice from quotation structure instead of hardcoding `reporter` |
| O-01 | CLOSED | Bounded genuine-binary exclusion |
| O-02 | CLOSED | Change-of-state presupposition path was dead; provider now fires the taxonomy criterion that names it |
| O-03 | CLOSED | Level 2 irregular participles + temporal-`by` parity |
| O-04 | CLOSED | Zero findings reports no peak, not P1 |
| O-05 | CLOSED | Maximum-cardinality matching; order-independent metrics |
| O-06 | CLOSED | Run id covers taxonomy + provider version |
| O-07 | CLOSED | Article identity separated from content identity |
| O-08 | CLOSED | Batch status tracks passage outcomes, not finding count |
| O-09 | CLOSED | Provider faults attributed by call site, not filename |
| O-10 | CLOSED | Curly single quotes handled; apostrophes unaffected |
| O-11 | CLOSED | Exclusion signals are candidate-local (enclosing sentence) |
| QA infra | CLOSED | `runtime_qa.py` portable browser discovery; accurate failure message |

## Mutation evidence (all reverted)

| Guard mutated | Result |
|---|---|
| M-01 identity gate accepts high overlap | **9 failures** |
| M-02 unknown counted as independent | **4 failures** |
| M-03 comparison-set membership disabled | **1 failure** |
| M-04 string chronology restored | **1 failure + 1 error** |
| M-05 uncertain may confirm | **5 failures** |
| M-06 arbitrary criteria accepted | **3 failures** |
| M-09 corpus span round-trip disabled | **2 failures** |
| M-09 stale-taxonomy rejection disabled | **1 failure** |
| M-09 voiceClass requirement disabled | **2 failures** |
| M-09 two-annotator requirement disabled | **1 failure** |

The first run of the corpus mutations (before the validator had test coverage)
left the suite green. That gap was found by mutation testing, not by review, and
16 corpus-integrity tests were added in response.

## Second sweep

Attacked after the repairs, as if by someone else: normalization collapse
(only terminal punctuation, which is in scope), omission provenance (0 of 5
contradictory pairs could credit a source), span integrity under hostile HTML,
coverage honesty under partial failure, taxonomy/implementation drift, benchmark
order-independence, calibration language, artifact reproducibility, and network
/ secret introduction. **No new Critical or Major defect was found.**

---

# Final pre-calibration blocker closure (commit `03e744a` → this commit)

A subsequent independent falsification audit of the hardening branch — one
that explicitly distrusted the hardening report, the test counts and the
"READY FOR MERGE" conclusion — reproduced two further Major defects that the
pass above did not catch. Both are closed here.

## A-01 (Major) — canonical_proposition was not exact

`canonical_proposition` formatted normalized numbers with float `%g`, and
substituted currency/percent/plain markers into the SAME string in three
sequential in-place `.sub()` passes. Two independent failures compounded:

- `%g` rounds to 6 significant digits: `2_000_000` and `2_000_001` both
  format as `"2e+06"`.
- because later regexes scanned the already-substituted text, a generated
  marker like `«currency:2e+06»` could itself be re-matched — `_NUM_PLAIN`
  caught the `"06"` inside it — corrupting the marker further.

Net effect: `$2,000,000` and `$2,000,001` canonicalized to the same string,
so `propositions_are_identical` returned `True` for genuinely different
numeric facts. `detect_divergence` (a separate, exact-float check) still
caught the specific case tested, which is why this did not fully collapse in
practice — but that made it a coincidence of the divergence gate, not a
property of the identity gate, which is exactly the thing M-01 was supposed
to fix and document as exact.

**Repair.** Numeric substitution now uses `Decimal`, not `float` — exact
arbitrary-precision arithmetic with fixed-point (`%f`-style) rendering, never
scientific notation. All three numeric patterns are matched against the
ORIGINAL text once, with non-overlapping spans tracked explicitly, then
assembled into a fresh output string — nothing is ever re-scanned. Each
marker also glues a word character directly against its leading digit
(`«num:x1000»`), which defeats `_NUM_PLAIN`'s negative lookbehind on any later
pass, making `canonical_proposition` idempotent:
`canonical_proposition(canonical_proposition(x)) == canonical_proposition(x)`.

Verified end-to-end with divergence detection monkeypatched to a no-op: the
identity gate alone still refuses `$2,000,000` vs `$2,000,001` as
`same_proposition`, so the fix does not depend on the secondary check that
happened to catch the original case.

## A-02 (Major) — empty annotatorSubmissions bypassed the M-12 guarantee

`validate_corpus.py` counted *distinct annotators appearing in non-empty
proposals* (`if proposals: submitting = {...}`). An adjudicated document with
`annotatorSubmissions: []`, or the field omitted entirely, made `proposals`
falsy, which skipped the two-annotator preservation check outright. A document
with zero preserved original annotator positions passed validation — the
exact thing M-12 exists to prevent.

The deeper problem was the data model, not just the guard: a flat list of
individual proposals has no way to represent "this annotator reviewed the
article and independently found nothing" as distinct from "this annotator's
work was never recorded" — both look like zero entries in the list. The
existing benchmark-harness test fixture had already worked around this by
fabricating a fake positive proposal for hard-negative documents just to keep
the flat list non-empty, which is a symptom of the same defect.

**Repair.** `annotatorSubmissions[]` is now one RECORD per annotator
(`submissionId`, `annotatorId`, `proposals[]`), not one entry per proposal.
The record's existence — not the non-emptiness of its `proposals` array — is
what is counted and required (`>= 2` distinct annotator records,
`submissionId` and `proposalId` globally unique, `annotatorId` set agreeing
with `annotatorIds`, every nested proposal fully validated and round-tripped
against its passage). A hard negative — two annotators, two records, both
`proposals: []`, `annotations: []` — is now representable and valid. A
missing, empty, or single-annotator `annotatorSubmissions` is rejected
regardless of anything else in the document. `benchmarks/corpus/_example.json`
now carries two real structured submissions, including one genuine
independent disagreement (`euphemism_dysphemism` vs `loaded_language` on
"siphon") and one genuine independent miss, so the worked example actually
demonstrates the mechanism it documents instead of omitting it.

## Mutation evidence (all reverted)

| Guard mutated | Result |
|---|---|
| A-01 numeric canonicalization reverted to lossy `%g` | **13 failures** |
| A-01 divergence detection (`detect_divergence`) disabled entirely | **13 failures — all pre-existing tests of divergence detection itself; every A-01 identity/omission test still passed**, confirming the identity gate does not depend on divergence detection |
| A-01 sequential in-place `.sub()` restored, guarded marker format kept | **0 failures** — see note below |
| A-02 `annotatorSubmissions: []` accepted (guard reverted to `if proposals:`-equivalent) | **2 failures** |
| A-02 submission-record requirement removed entirely | **2 failures** |
| A-02 empty `proposals[]` rejected (hard-negative regression) | **4 failures, 1 error** |

Note on the sequential-`.sub()` mutation: restoring the old in-place
substitution order while keeping the new guarded marker format
(`«num:x1000»`, word character glued to the leading digit) did **not**
reproduce the original corruption. This is a genuine, useful negative result:
it shows the word-character marker guard — not the single-pass
non-overlapping-span architecture — is what actually makes re-scanning safe.
The single pass is kept regardless, as better engineering (one deterministic
scan instead of three), but the report does not claim it is independently
load-bearing for this defect, because the mutation just proved it isn't.

## Second sweep

Repeated the second-sweep attack surface against the A-01/A-02 delta
specifically: adjacent-large-integer collisions, many-significant-digit and
trailing-zero decimals, multiple/repeated numbers in one proposition, marker
idempotence, two/three zero-proposal submissions, one-empty-one-positive,
duplicate submission/proposal ids, annotator/submission mismatches,
resolutions referencing unknown or wrong proposals, and re-running the
role-swap and near-neighbor-numeric Material Omission attacks from the first
hardening pass. No new Critical or Major defect was found in this delta.

---

# Edge-invariant closure (this commit)

A subsequent independent audit reproduced five further Major defects in the
A-01/A-02 fix itself, none of which the second sweep above caught, plus
found three additional performance/robustness defects during its own fresh
sweep. All eight are closed here.

## B-01 — Decimal scaling was still lossy at large magnitude

`value *= Decimal(multiplier)` uses the ambient Decimal *context*'s
precision (28 significant digits by default) for the multiplication itself.
A 30-digit coefficient times `1_000_000` rounds to 28 significant digits, so
`123456789012345678901234567890` and `...67891` (last digit different) both
round to the same product — the exact "arithmetic makes distinct values
equal" failure A-01 was supposed to eliminate, just pushed from 6 significant
digits (the old `%g` bug) to 28.

**Repair.** `_scale_exact` operates directly on the Decimal's
`(sign, digits, exponent)` tuple using Python's arbitrary-precision `int` for
the multiplication itself — exact at any magnitude, with no ambient context
and nothing to misconfigure. Verified with no collisions at 30, 50, and 100
digits across every supported scale word.

## B-02 — The marker string itself was the vulnerability

`canonical_proposition("1000")` and `canonical_proposition("«num:x1000»")`
canonicalized to the same string — literal source text containing marker
syntax (coincidentally, or via deliberate injection) impersonated a real
numeric token. The A-01 hardening had made the marker format harder to
corrupt via re-scanning, but never addressed that a STRING-shaped identity
representation is inherently collidable with source text, which is made of
the same characters.

**Repair.** `canonical_identity_key` returns a tuple of typed
`(kind, value)` tokens — `("text", ...)` vs `("currency"|"percent"|"num", ...)`
— compared by `propositions_are_identical` directly. A `"text"` token can
never equal a `"num"` token regardless of its string content, because tuple
equality requires the kind to match, not the printable characters.
`canonical_proposition` is now diagnostic-only, documented as such, and nothing
compares its output. A format-independent regression test discovers whatever
the diagnostic rendering currently produces and confirms injecting exactly
that text still fails identity — this caught a real gap in the original,
format-hardcoded injection tests during mutation testing (see below).

## B-03 — Proposal field validation had silent skip paths

`validate_corpus.py`'s proposal validation used combined
`if _is_int(x) and _is_int(y) and ...:` guards with no `else` branch — a
wrong-typed `passageOrdinal` (bool, string), `startChar`/`endChar`, or
`excerpt` made the whole condition false and validation for that field simply
never ran, with zero errors reported. Rewritten to mirror the `annotations[]`
block's explicit per-condition branching, so every failure mode has its own
`err()` call and nothing falls through silently. 17 regressions added, one
per malformed shape in the audit's attack list.

## B-04 — Gold provenance was unenforced

Two defects: `if proposal_ids and pid not in proposal_ids` let a resolution
reference a nonexistent proposal whenever the document had zero real
proposals (exactly the hard-negative precondition); and nothing stopped
`annotations[]` from containing a finding with no proposal match and no
resolution record at all — gold that traced to nothing.

**Policy chosen** (documented in ADJUDICATION.md §7b): a gold annotation is
valid only if it exactly restates a preserved proposal (uncontested
auto-merge, needs no resolution) or is named by a resolution's
`resultingAnnotationId`. A new `adjudicator_add` decision lets a third-party
adjudicator add an unproposed finding, but only with a named adjudicator,
empty `proposalIds`, and a non-empty rationale — never silently. Every
resolution now requires `adjudicatorId`; `drop` may not carry a
`resultingAnnotationId`; `resolutionId` and `proposalId` stay globally
unique. The worked example's existing "siphon" disagreement now has a real
`resolutions[]` record instead of only a free-text `resolvedAs`.

## B-05 — Schema did not match the executable contract

`_schema.json` never conditionally required `annotatorIds` /
`annotatorSubmissions` for `adjudicationStatus: "adjudicated"`, and the
`resolutions` item schema still described the pre-B-04 shape. Added a Draft
2020-12 `if`/`then` conditional, brought the `decision` enum and
`adjudicatorId` requirement in line with the validator, and set
`additionalProperties: false` on the structured submission/proposal/
resolution records to catch misspellings. `proposals` deliberately keeps no
`minItems`, so hard negatives stay schema-valid. No `jsonschema` dependency
was added (none was already present); parity is instead tested by reading
the schema's own JSON and asserting specific facts against the validator's
module-level constants (`VALID_RESOLUTION_DECISIONS`, `MIN_ANNOTATORS`).

## Three further defects found during this closure's own fresh sweep

Not requested by name, but directly adjacent to B-01/B-02's numeric-matching
code and found by genuinely trying to falsify rather than re-reading the new
tests:

- **`resolutions` field type confusion.** `data.get("resolutions", []) or []`
  let a non-empty string silently type-confuse into "an iterable of
  records" — `enumerate()` over a string yields its *characters*, producing
  one bogus per-character error instead of one clear type error. Still
  correctly invalid, but noisy and conceptually wrong. Fixed with an explicit
  `isinstance` check.
- **`_NUM_PERCENT` catastrophic backtracking (DoS).** The regex's mandatory
  trailing suffix (`%` / "percent") with no lookbehind guard meant a long
  digit run with no percent sign anywhere forced the engine to backtrack
  through the entire run at every starting position — O(n²), measured at
  ~9.5s for a 10,000-digit non-percent number, extrapolating to minutes for
  the 100,000-digit inputs B-01 explicitly made first-class. Fixed with a
  `(?<!\d)` lookbehind (stops retrying inside an already-failed digit run)
  plus an atomic group around the digit-matching (stops intra-match
  backtracking); confirmed linear from 10,000 to 1,000,000 digits.
- **`_already_consumed` O(k²) in match count.** The non-overlapping-span
  tracking added for B-02 checked each new numeric match against every
  previously-accepted span with a linear scan — fine for a handful of
  numbers, but a realistic long article with hundreds of dates/currency/
  percentages (exactly this system's real input shape) took multiple
  seconds, worsening quadratically. Fixed by keeping `consumed` sorted via
  `bisect.insort` and using `bisect.bisect_right` for O(log k) lookups;
  confirmed linear from 500 to 8,000 repetitions.

## Mutation evidence (all reverted)

| Guard mutated | Result |
|---|---|
| B-01 `_scale_exact` reverted to context-bound `Decimal *=` | **15 failures** |
| B-02 identity compares `canonical_proposition` strings instead of the typed key | **0 failures against the pre-existing guillemet-based tests — caught only by the new format-independent test (1 failure)**, itself a finding: hardcoding an attack payload's format is fragile |
| B-03 proposal ordinal/start/end validation reverted to combined-condition silent-skip | **1 failure** — the excerpt-type case; most other cases are independently caught by B-04's gold-grounding check as a side effect (real defense-in-depth, not full per-field mutation isolation) |
| B-04 `if proposal_ids and pid not in proposal_ids` restored | **1 failure** |
| B-04 gold-provenance grounding check disabled entirely | **1 failure** |
| `resolutions` type check removed | **1 failure** (reproduces the per-character noise) |
| `_NUM_PERCENT` lookbehind/atomic-group guard removed | 100,000-digit input did not complete in 20s (timed out) |
| `_already_consumed` bisect reverted to linear scan | **1 failure** (4,000-repetition document took 3.2s, over the 3.0s budget) |

## Fresh sweep

§8's numeric identity attack matrix (adjacent values at 10⁰ through 10¹⁰⁰,
every scale word, every numeric kind, literal-marker injection, role/from-to
swaps, formatting equivalents) and §7's corpus coherence attack matrix (13
cases spanning hard negatives, ghost references, malformed resolutions, and
malformed proposal types) were run as explicit adversarial probes, not just
re-derived from the new unit tests — every case behaved exactly as required.
The three defects above were found in this same pass. No further Critical or
Major defect was found.

---

# Consensus and numeric-grammar closure (this commit)

A further independent source review found three Major defects that every
previous pass — including two adversarial sweeps over this exact code — had
missed, plus an adjacent schema-parity gap.

## C-01 — the comma grammar was too permissive

The numeric body pattern was `\d[\d,]*`, accepting ANY arrangement of digits
and commas, after which canonicalization stripped every comma. Structurally
different source text therefore collapsed onto the same value:

| Source | Canonicalized as | Same as |
|---|---|---|
| `1,2,3` | 123 | `123` |
| `1,00` | 100 | `100` |
| `12,34,567` | 1234567 | `1234567` |
| `1,,000` | 1000 | `1000` |
| `1234,567` | 1234567 | `1234567` |

All of these established `same_proposition` with an unrelated clean integer.
Comma-stripping is only meaning-preserving for genuine thousands grouping;
anywhere else the comma is a separator, not decoration. This survived B-01
and B-02 because both were about *arithmetic* and *representation* — neither
questioned whether the lexer should have accepted the token in the first
place.

**Repair.** `_NUM_BODY` is now `(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?` —
ungrouped digits, or correct thousands grouping, either optionally followed by
a fraction. The grouped alternative is tried first so `1,234,567` matches
whole rather than stranding after `1`. Malformed forms are no longer one
numeric token: they split into separate numerals with the comma surviving as
literal text, so they cannot be silently reflowed into a different clean
integer either. Verified by exhaustive cross-product: **zero** collisions
between 10 malformed forms and 9 clean integers.

*Honest limitation:* two malformed forms can still equal each other when they
reduce to the same token sequence (`1,00` and `1,0` both give `1 , 0`, because
`00` and `0` are numerically equal — the same reason `007` == `7`). Neither
can reach a clean integer, which is the invariant that actually gates a false
Material Omission, so this is recorded rather than papered over.

## C-02 — "auto-merge" was not consensus

The grounding check accepted a gold annotation if it matched **any one**
preserved proposal fingerprint. That is not agreement; it is evidence that a
single annotator proposed it. Under that rule all of the following passed
silently, each of which ADJUDICATION.md §3 explicitly escalates:

- annotator A proposes X, annotator B proposes nothing, gold = X
  (**presence disagreement**)
- A says P2, B says P4 on the same span, gold = P2 (**pressure disagreement**)
- A says `reporter`, B says `quoted_speaker`, gold = A (**voice disagreement**)

The validator was, in effect, promoting one annotator's opinion to consensus
gold and calling it §2 auto-merge.

**Repair.** Proposals are now retained with their annotator, pressure and
voice. `_auto_merge_span` implements the actual §2 contract: at least
`MIN_ANNOTATORS` distinct annotators agreeing on mechanism, passage, pressure
and voice, **every** pair clearing IoU ≥ 0.8, and the gold span equal to the
intersection. Anything else falls through to "resolution required". The
three-or-more-annotator policy is defined explicitly (agreeing set = all
matching proposals; intersection over the whole set) rather than left
ambiguous, and is tested.

## C-03 — resolution decisions were under-constrained

`decision: "merge"` with `proposalIds: []` grounded arbitrary gold with no
proposal origin at all — a silent backdoor around `adjudicator_add`, which
exists precisely to make that case explicit and attributable. Nothing
constrained how many proposals or results any decision could carry, and
`split` — which the protocol defines as producing *two* annotations — was
represented by a **singular** `resultingAnnotationId` that structurally
could not express it.

**Repair.** `resultingAnnotationIds` is now an array; the singular key is
rejected outright so an old-format record can never look grounded. Per-decision
cardinality is enforced from one table (`RESOLUTION_CARDINALITY`), `merge`
additionally requires proposals from ≥ 2 *distinct* annotators, and each gold
annotation must be claimed by exactly one resolution. The real corpus is
EMPTY, so this was migrated outright with no backwards-compatibility path —
the safe moment to do it.

## Schema parity

`_schema.json` now carries `annotatorIds` `minItems: 2` / `uniqueItems`,
per-decision `proposalIds` / `resultingAnnotationIds` cardinality as five
`allOf` conditionals, `adjudicator_add`'s rationale requirement, and
`additionalProperties: false` on structured records. A test asserts the
schema's cardinality equals `RESOLUTION_CARDINALITY` field by field, so the
two cannot drift.

Parity is claimed for the **structural** contract only. The schema's own
description now names the checks that remain Python-only — cross-reference
resolution, id uniqueness, excerpt round-tripping, taxonomy membership,
`merge`'s distinct-annotator rule, the auto-merge consensus computation, and
exactly-once grounding — and states plainly that a schema-valid document is
not necessarily a corpus-valid one.

## Mutation evidence (all reverted)

| Guard mutated | Result |
|---|---|
| C-01 permissive `\d[\d,]*` grammar restored | **20 failures** |
| C-02 any-single-proposal auto-merge restored | **6 failures** |
| C-02 pressure dropped from auto-merge criteria | **2 failures** |
| C-02 voice dropped from auto-merge criteria | **1 failure** |
| C-03 `merge` accepts zero proposals | **2 failures** |
| C-03 `split` accepts one result | **2 failures** |

## Focused sweep

Confined to the changed boundaries, as instructed. Auto-merge helper edge
cases (degenerate spans, proposals with absent pressure/voice, one annotator
listed twice, a third annotator whose span breaks the pairwise IoU bar) all
fail closed to "adjudication required". Numeric identity re-verified: zero
arbitrary-precision collisions at 30/50/100 digits across every scale word,
huge presentation equivalents still match, and the new grammar introduces no
backtracking pathology (100k-digit non-percent 0.005s; 20k-comma run 0.099s).
No new Critical or Major defect was found in these boundaries.

---

# Gold-provenance closure (this commit)

Three Major corpus-provenance defects plus a validation-parity gap. All three
sat *inside* code the previous closure had just rewritten and mutation-tested
— each is a case where a check verified that a link EXISTED without verifying
that it MEANT anything.

## D-01 — resolution links existed but were not semantically grounded

Cardinality, reference-existence and the distinct-annotator rule all passed
while the gold had nothing to do with the proposals cited. Reproduced before
fixing:

| Attack | Before |
|---|---|
| `uphold_a` citing a `loaded_language` proposal, producing a `false_dilemma` gold on an unrelated span | **accepted** |
| `merge` of two `loaded_language` proposals producing a `presupposition` gold elsewhere | **accepted** |
| `split` of one span producing two unrelated findings elsewhere in the passage | **accepted** |

An "uphold" that silently substitutes a different finding is not an uphold.

**Repair.** Per-decision source→result relationships are now enforced:
`uphold_*` must exactly preserve the cited proposal's mechanism, passage,
span, pressure and voice (`reviewerConfidence` excluded — it is a
per-annotator epistemic report, not a property of the phenomenon); `merge`
requires one shared passage and mechanism across sources, and gold that
overlaps **every** cited span; `split` requires every result to sit on a
source passage and overlap the source region (different mechanisms are
allowed, relocation is not).

## D-02 — three-plus-annotator dissent disappeared

The previous closure's "at least MIN_ANNOTATORS agreeing" rule was still
majority-flavoured. With three annotators, A and B agreeing auto-merged while
C's dissent — a different pressure, a different voice, or no proposal at all —
was silently discarded. That is precisely the calibration signal the corpus
exists to preserve, and unlike an escalated case it is lost invisibly and
permanently.

**Repair.** Auto-merge now requires **unanimity**: every annotator declared in
`annotatorIds` must contribute exactly one qualifying proposal, all agreeing
on mechanism/passage/pressure/voice, every pair at IoU ≥ 0.8, gold span equal
to the intersection across all participants. An annotator contributing two
matching proposals makes the cluster ambiguous and also escalates. Documented
in ADJUDICATION.md §2 as deliberately stricter than majority vote.

## D-03 — exactly-one provenance was documented, not enforced

The docs said gold grounded both by auto-merge and by resolution is an error.
The validator checked only the resolution side, so a document could label gold
that both annotators had proposed identically as an `adjudicator_add`
("nobody proposed this") — a false account of where the finding came from.

**Repair.** Both origins are computed for every annotation and checked against
a closed truth table: `(auto-merge, 0)` and `(no auto-merge, 1)` are the only
valid states; ungrounded, conflicting and duplicate provenance are each
rejected with their own message.

## Adjudicator independence and annotatorIds

ADJUDICATION.md §3 has always said the adjudicator is a third person who has
not annotated the document. Nothing enforced it, so an annotator could
adjudicate their own disagreement and manufacture consensus single-handed.
`adjudicatorId` must now be a non-empty string absent from `annotatorIds`.

`annotatorIds` was validated with `{a for a in annotators if isinstance(a, str)}`,
which **discarded** non-string entries and **de-duplicated** repeats before
counting — so `["a","b","b"]` and `["a",7,"b"]` both passed a check whose
stated purpose was "at least 2 distinct annotators". Since nothing in this
pipeline executes the JSON Schema, the Python validator now enforces what the
schema promises: an array of ≥ 2 unique non-empty strings, booleans rejected,
matching the preserved submission annotators exactly.

## Mutation evidence (all reverted)

| Guard mutated | Result |
|---|---|
| A. uphold may point to unrelated gold | **2 failures** |
| B. merge result unrelated to sources | **3 failures** |
| C. back to ≥2-of-N auto-merge consensus | **5 failures** |
| D. dual-provenance check skipped | **1 failure** |
| E. adjudicatorId allowed in annotatorIds | **1 failure** |
| F. duplicate annotatorIds allowed | **1 failure** |

## Focused sweep

Confined to the five named boundaries. Adjudicator-identity edges (non-string
id, id matching a submission annotator absent from `annotatorIds`), D-01 with
a source proposal that failed type validation (no record to derive from),
cross-passage split sources, hard-negative documents with zero gold, and the
auto-merge helper called with an empty or superset declared-annotator set all
fail closed. Three pre-existing test fixtures were themselves found to be
semantically incoherent by the new rules — a "valid merge" that was actually a
unanimous auto-merge with a redundant resolution, and a "valid split" placing
a result outside its source region — and were corrected rather than the rules
loosened. C-01 numeric regressions re-run unchanged. No new Critical or Major
defect was found in these boundaries.

---

# Span-provenance closure (this commit)

Two Major blockers, both the same shape as the D-round: a check confirmed a
span relationship EXISTED without confirming it was the *right* relationship.
Both lived in the D-01 code written one commit earlier.

## E-01 — split validated against a bounding hull, not real source spans

The split check computed one global region, `min(start)..max(end)` across all
cited sources, **ignoring `passageOrdinal`**. Two consequences, both
reproduced before fixing:

| Attack | Before |
|---|---|
| sources 0..10 and 90..100 → result 40..50 (the gap between them) | **accepted** — hull was 0..100 |
| p1 on passage 0 (0..10), p2 on passage 1 (90..100) → result on passage 0 at 40..50 | **accepted** — hull discarded passage, so foreign coordinates vouched for it |

**Repair.** Provenance is now per-span and per-passage: every result must
overlap at least one *actual* cited proposal span on the same passage, and
every cited proposal must be overlapped by at least one result on its own
passage. No hull is computed. Unrelated gap text can never become a split
result, and a cited source no result represents is an incomplete split.

## E-02 — merge could bridge disjoint source findings

Overlapping the gold against each source independently is satisfied by a
bridging span: sources at 0..10 and 90..100 both overlap a gold of 5..95,
which swallows eighty characters of unrelated text and presents two separate
occurrences as one reconciled finding. Reproduced as **accepted**.

**Repair.** The sources themselves must share a non-empty common intersection
(`max(starts) < min(ends)`); the gold must overlap that intersection and must
not extend beyond the outer bounds of the cited spans. Disjoint cited spans
are separate occurrences requiring separate resolutions.

## Non-blocking cleanup taken: occurrence-local auto-merge

The auto-merge cluster matched on mechanism/passage/pressure/voice alone, so
every *other* occurrence of the same mechanism in the same passage joined the
cluster. A passage with two distinct P3/reporter `loaded_language` findings
therefore gave each annotator two "matching" proposals per gold and was
rejected as ambiguous — a false ambiguity between findings never in
competition. A proposal now only qualifies if it actually overlaps the gold it
is evidence for. Verified that this does **not** weaken the D-02 ambiguity
guard: two proposals from the same annotator both overlapping the same gold
still escalate.

## Non-blocking cleanup declined: generic `uphold`

Replacing `uphold_a`/`uphold_b` with a single `uphold` is defensible — `a`/`b`
has no stable meaning beyond two annotators, and `proposalIds` already
identifies the actual proposal. It was **not** done, deliberately: it is a
vocabulary migration touching `VALID_RESOLUTION_DECISIONS`,
`RESOLUTION_CARDINALITY`, the schema enum, the schema's per-decision
conditionals, the worked example, ADJUDICATION.md and the tests — not a
trivial edit, and the brief said not to let an optional cleanup expand the
task. The current naming costs documentation clarity, not correctness: the
validator treats both variants identically and the cardinality contract is the
same for each. Recorded here as a known cosmetic wart for a future pass.

## Mutation evidence (all reverted)

| Guard mutated | Result |
|---|---|
| E-01 bounding-hull split logic restored | **6 failures** |
| E-02 common-intersection requirement removed | **1 failure** |
| E-02 hull-containment requirement removed | **1 failure** |

Two pre-existing D-01 tests asserted on error-message text that the repairs
changed; both still rejected their documents correctly, and only the message
assertions were updated.

---

# Final gold span integrity closure (this commit)

Two blockers, both in the split/gold path hardened in the E-round.

## F-01 — split results extended beyond real source coverage

The E-01 repair replaced the bounding hull with per-source overlap checks, but
**overlap is not containment**. A cited source at 50..60 "overlapped" a result
of 0..55, licensing fifty characters of text no annotator ever marked; and two
sources at 0..10 and 90..100 each overlapped a bridging result of 5..95.

Reproduced before fixing: case A (`0..55` and `55..100` from a `50..60`
source) and case B (`5..95` from `0..10` + `90..100`) both **accepted**. Case C
(cross-passage collision) was already closed by E-01.

**Repair.** Cited source spans are reduced to connected coverage components
per passage — overlapping or touching intervals merge, disconnected regions
stay separate (`[(0,10),(8,20),(40,50)] -> [(0,20),(40,50)]`). Every split
result must be **wholly contained** in one component on its own passage
(`R.start >= C.start and R.end <= C.end`). No hull, no cross-passage
substitution. The reverse check — every cited proposal represented by at least
one result on its own passage — is retained.

## F-02 — duplicate semantic gold counted twice

Nothing stopped two `annotations[]` entries sharing
`(passageOrdinal, startChar, endChar, mechanismId)` under different
`annotationId`s. Every metric computed from the corpus would count that
finding twice, inflating support for whichever occurrence happened to be
duplicated. Reproduced as **accepted** via a split, via two `adjudicator_add`
records, and with the copies differing only in `pressure`.

**Repair.** A gold finding is identified by what it says about where, not by
its id. The semantic key is `(passageOrdinal, startChar, endChar,
mechanismId)`; duplicates are rejected regardless of differing
`annotationId`, `pressure`, `voiceClass` or `reviewerConfidence` — those are
disagreements adjudication must resolve down to one occurrence, not a licence
to keep both. Legitimate structure is untouched: the same span under two
different mechanisms is valid multi-tagging, and merely overlapping spans,
different spans, and identical spans on different passages all remain valid.

## Mutation evidence (all reverted)

| Guard mutated | Result |
|---|---|
| F-01 overlap-only split validation restored | **3 failures** |
| F-02 semantic duplicate validation disabled | **7 failures** |

Two pre-existing tests asserted on error text the repair changed; both still
rejected their documents correctly and only the message assertions moved.

## Final bounded falsification (corpus/gold integrity boundary only)

Ten attack questions, twelve probes, **all safe**: results outside every
coverage component, bridging disconnected components, cross-passage coordinate
substitution, a cited source vanishing from a split, the same semantic gold
twice, pressure/voice manufacturing copies, multi-tagging still working,
malformed adjudicated data reaching metrics (fatal, never scored),
disputed/draft documents entering metrics (never loaded), `unresolvable`
inside an adjudicated document, and gold with zero or two provenance origins.

**Critical remaining: 0. Major remaining: 0.** Bug sweeping stops here.
