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

- Claim alignment is a **lexical baseline**, not semantic. It is honest about
  this (returns `uncertain` below its threshold), but it will miss paraphrase.
- Voice classification does not resolve *which* speaker a quote belongs to.
- The Level 3 detector is not reachable from the browser build; that requires a
  service boundary which remains deliberately deferred.
- 21 of 32 prototype-parity rows are UNVERIFIED for want of a browser in this
  environment.
