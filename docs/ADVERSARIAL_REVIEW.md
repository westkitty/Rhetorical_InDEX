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
