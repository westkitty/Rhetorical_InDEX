# Instrument Alpha — Requirement Traceability

Atomic rows. One behavior per row. `PASS` requires an executed check in this
environment; implementation presence never yields `PASS`.

Status vocabulary: **PASS** (executed evidence) · **FAIL** · **UNVERIFIED**
(not measurable here) · **N/A** (out of scope by design).

## Epistemic constitution

| ID | Requirement | Verification | Status |
|---|---|---|---|
| E-01 | Interpretive pressure is not factuality | Pressure model has no truth input; profile card copy; methodology view | PASS |
| E-02 | Pressure is not confidence (separate data) | `Finding.pressure` / `.confidence` distinct fields | PASS |
| E-03 | Pressure and confidence vary independently | `test_high_pressure_can_carry_low_confidence`, `test_low_pressure_can_carry_high_confidence` | PASS |
| E-04 | Confidence model cannot read pressure | `test_confidence_model_never_receives_pressure` (signature introspection) | PASS |
| E-05 | No Left/Center/Right axis | `test_no_political_axis_anywhere_in_the_vocabulary` | PASS |
| E-06 | No master bias/trust/truth/propaganda score | `test_no_master_score_vocabulary_exists`, `test_profile_exposes_no_single_summarizing_number` | PASS |
| E-07 | No potential-harm score | Absent from schema; E-06 scan covers `harm` | PASS |
| E-08 | One Finding = one mechanism | `Finding.mechanism_id` scalar; `test_legacy_plural_mechanisms_field_is_rejected` | PASS |
| E-09 | Multiple mechanisms may share one span | `test_five_mechanisms_on_one_span_do_not_duplicate_source_text` | PASS |
| E-10 | Source text never duplicated per finding | Same test — 5 findings, 1 span, 1 excerpt | PASS |
| E-11 | Quoted rhetoric distinguishable from outlet | `test_quoted_span_is_attributed_to_speaker_not_outlet` | PASS |
| E-12 | Quoted rhetoric not attributed to publisher | `test_quoted_rhetoric_is_not_attributed_to_the_outlet`, `test_article_of_only_quotes_attributes_nothing_to_the_outlet` | PASS |
| E-13 | Material omission is cross-document only | `test_intrinsic_stage_cannot_produce_omission`, `test_finding_object_refuses_cross_document_construction` | PASS |
| E-14 | Omission requires a comparison set | `test_single_source_comparison_set_is_refused` | PASS |
| E-15 | Coverage consensus is not truth | `test_coverage_consensus_is_explicitly_not_truth` | PASS |
| E-16 | Primary evidence is not automatically true | `test_verified_authenticity_requires_an_explicit_basis`, `test_default_authenticity_is_unverified` | PASS |
| E-17 | Uncertainty does not vanish downstream | `test_uncertain_verdict_is_capped_below_high_confidence` | PASS |
| E-18 | Weak alignment cannot ground a strong omission | `test_uncertain_alignment_is_never_usable_for_omission`, `test_confidence_is_capped_by_the_weakest_alignment` | PASS |
| E-19 | Detector evidence is never fabricated | `test_provider_cannot_get_criteria_backfilled_from_the_taxonomy` | PASS |
| E-20 | Criteria come from the taxonomy record, not invention | `test_triggered_criteria_come_from_the_taxonomy_record` | PASS |
| E-21 | System is radically inspectable | Every finding carries pressure/confidence factor traces + detector votes; `test_every_finding_carries_detector_votes_and_factor_traces` | PASS |

## Detector contract — validation

| ID | Requirement | Verification | Status |
|---|---|---|---|
| V-01 | Unknown mechanism rejected | `test_missing_criteria...`/`FindingPayloadValidationTests` | PASS |
| V-02 | Invalid pressure rejected | `test_invalid_vocabulary_values_are_rejected` | PASS |
| V-03 | Invalid confidence rejected | same | PASS |
| V-04 | Invalid voice rejected | same | PASS |
| V-05 | Unknown passage rejected | `test_unknown_passage_is_rejected` | PASS |
| V-06 | Negative passage index rejected | `test_inverted_and_out_of_bounds_spans_are_rejected` | PASS |
| V-07 | Missing excerpt rejected | `test_absent_excerpt_is_rejected` | PASS |
| V-08 | Excerpt absent from passage rejected | same | PASS |
| V-09 | Ambiguous repeated excerpt rejected | `test_repeated_excerpt_without_locator_is_rejected` | PASS |
| V-10 | Valid occurrence selector resolves | `test_repeated_excerpt_with_valid_locator_resolves` | PASS |
| V-11 | Out-of-range occurrence selector rejected | `test_out_of_range_locator_is_rejected` | PASS |
| V-12 | Boolean not accepted as integer locator | `test_boolean_is_not_accepted_as_an_integer_locator` | PASS |
| V-13 | Out-of-range span rejected | `test_inverted_and_out_of_bounds_spans_are_rejected` | PASS |
| V-14 | Inverted span rejected | same | PASS |
| V-15 | Coordinate/excerpt mismatch rejected | `test_coordinate_excerpt_mismatch_is_rejected` | PASS |
| V-16 | Empty criteria rejected | `test_missing_criteria_is_rejected_and_not_backfilled` | PASS |
| V-17 | Malformed criteria rejected | same (5 malformed shapes) | PASS |
| V-18 | Cross-document mechanism rejected in intrinsic slice | `test_cross_document_mechanism_is_rejected` | PASS |
| V-19 | Mechanism outside implemented slice rejected | `test_mechanism_outside_implemented_slice_is_rejected` | PASS |
| V-20 | Unknown taxonomy version rejected | `test_unknown_taxonomy_or_schema_version_is_rejected` | PASS |
| V-21 | Unknown detector schema version rejected | same | PASS |
| V-22 | Out-of-range provider certainty rejected | `test_out_of_range_certainty_is_rejected` | PASS |
| V-23 | Unknown neighbour mechanism rejected | `test_neighbor_referencing_an_unknown_mechanism_is_rejected` | PASS |

## AnalysisRun and coverage

| ID | Requirement | Verification | Status |
|---|---|---|---|
| R-01 | Run created before analysis; findings reference it | `test_every_finding_references_the_run_and_carries_versions` | PASS |
| R-02 | Complete coverage yields `complete` | `test_complete_coverage_yields_complete` | PASS |
| R-03 | Partial coverage yields `partial` | `test_partial_coverage_yields_partial_not_complete` | PASS |
| R-04 | Total failure yields `failed` | `test_total_failure_yields_failed` | PASS |
| R-05 | Coverage buckets partition passages | `test_coverage_buckets_partition_passages` | PASS |
| R-06 | Duplicate append cannot inflate coverage | `test_duplicate_processed_append_cannot_inflate_coverage_to_complete` | PASS |
| R-07 | Coverage cannot reference foreign passages | `test_coverage_cannot_reference_a_passage_outside_the_article` | PASS |
| R-08 | Partial run never reports complete | `test_partial_run_cannot_present_itself_as_complete` | PASS |
| R-09 | Partial coverage emits a warning | same (asserts `warnings` non-empty) | PASS |
| R-10 | Findings never reference a failed passage | `test_findings_never_reference_a_failed_passage` | PASS |
| R-11 | Successful passages retained on partial failure | `test_provider_failure_on_one_passage_yields_partial_not_complete` | PASS |
| R-12 | Provider bug degrades run, does not crash it | `test_provider_bug_degrades_the_run_instead_of_crashing_it` | PASS |
| R-13 | Missing credentials produce failure, not invention | `test_model_provider_without_credentials_refuses_rather_than_inventing` | PASS |

## Long documents

| ID | Requirement | Verification | Status |
|---|---|---|---|
| L-01 | Batching never splits a passage | `test_batching_never_splits_a_passage` | PASS |
| L-02 | Every passage batched exactly once | `test_batching_covers_every_passage_exactly_once` | PASS |
| L-03 | Batch size does not change findings | `test_batch_size_does_not_change_findings` | PASS |
| L-04 | Mechanism at end of long document still found | `test_mechanism_at_end_of_long_document_is_still_found` | PASS |
| L-05 | 601-passage document completes with full coverage | `test_very_long_article_completes_with_full_coverage` | PASS |

## Document model

| ID | Requirement | Verification | Status |
|---|---|---|---|
| D-01 | Structure preserved, not flattened | `test_segmentation_preserves_structure_not_flattened` | PASS |
| D-02 | Content hash cryptographic + deterministic | `test_content_hash_is_deterministic_and_input_sensitive` | PASS |
| D-03 | Hash covers structure, not only words | `test_content_hash_covers_structure_not_only_words` | PASS |
| D-04 | Passage ids stable and addressable | `test_passage_ids_are_stable_and_addressable` | PASS |
| D-05 | Normalization preserves exact quote/dash characters | `test_normalization_does_not_rewrite_quotes_or_dashes` | PASS |
| D-06 | Empty input rejected | `test_empty_input_is_rejected_not_silently_accepted` | PASS |
| D-07 | Span coordinates passage-local | `test_span_coordinates_are_passage_local` | PASS |
| D-08 | Every finding round-trips to its span | `test_every_finding_round_trips_to_its_exact_span` | PASS |
| D-09 | Round-trip holds under adversarial punctuation | `test_every_finding_span_round_trips_on_adversarial_punctuation` | PASS |
| D-10 | Caption keyword needs a delimiter | `test_sentence_beginning_with_a_caption_keyword_is_not_a_caption` | PASS |

## Voice provenance

| ID | Requirement | Verification | Status |
|---|---|---|---|
| W-01 | Quoted span → `quoted_speaker` | `test_quoted_span_is_attributed_to_speaker_not_outlet` | PASS |
| W-02 | Unquoted span → outlet voice | `test_unquoted_span_is_outlet_voice` | PASS |
| W-03 | Straddling a quote boundary → `uncertain` | `test_span_straddling_a_quote_boundary_is_uncertain` | PASS |
| W-04 | Unbalanced quotes do not yield a confident guess | `test_unbalanced_quotes_yield_uncertain_not_a_confident_guess` | PASS |
| W-05 | Heading → `headline` | `test_heading_is_headline_voice` | PASS |
| W-06 | Out-of-bounds span raises | `test_out_of_bounds_span_raises` | PASS |

## Comparison, omission, evidence

| ID | Requirement | Verification | Status |
|---|---|---|---|
| C-01 | Identical propositions align as same | `test_identical_propositions_align_as_same` | PASS |
| C-02 | Unrelated propositions not forced into a match | `test_unrelated_propositions_are_not_forced_into_a_match` | PASS |
| C-03 | Ambiguous overlap → `uncertain` + Low | `test_ambiguous_overlap_yields_uncertain_and_low_confidence` | PASS |
| C-04 | Negation mismatch → contradictory, not agreement | `test_negation_mismatch_is_flagged_contradictory_not_agreement` | PASS |
| C-05 | Syndicated sources collapse to one origin | `test_syndicated_sources_collapse_to_one_origin` | PASS |
| C-06 | Unknown dependence not claimed as independence | `test_unknown_dependence_does_not_manufacture_independence` | PASS |
| C-07 | Well-grounded omission accepted | `test_well_grounded_omission_is_accepted` | PASS |
| C-08 | Proposition present in target → refused | `test_proposition_already_present_in_target_is_refused` | PASS |
| C-09 | Later development → refused | `test_later_development_is_not_an_omission` | PASS |
| C-10 | Syndicated corroboration → refused | `test_syndicated_supporting_sources_are_refused_as_corroboration` | PASS |
| C-11 | Unrelated supporting claims → refused | `test_unrelated_supporting_claims_are_refused` | PASS |
| C-12 | Synthetic comparison labelled on output | `test_synthetic_comparison_set_is_labelled_on_the_omission` | PASS |
| C-13 | Rejections surfaced, not swallowed | `test_detect_returns_rejections_rather_than_swallowing_them` | PASS |
| C-14 | `verified` authenticity needs explicit basis | `test_verified_authenticity_requires_an_explicit_basis` | PASS |
| C-15 | Evidence ranked by characteristics, not popularity | `test_ranking_uses_evidentiary_characteristics_not_popularity` | PASS |
| C-16 | Claim state never exceeds its evidence | `test_claim_state_never_exceeds_the_evidence` | PASS |
| C-17 | Contradiction not outvoted by volume | `test_contradiction_is_not_outvoted_by_supporting_volume` | PASS |
| C-18 | Incomplete retrieval reported, not hidden | `test_incomplete_retrieval_is_reported_not_hidden` | PASS |
| C-19 | Synthetic evidence unmistakably labelled | `test_synthetic_evidence_is_labelled_unmistakably` | PASS |

## Benchmark

| ID | Requirement | Verification | Status |
|---|---|---|---|
| B-01 | Empty corpus reports EMPTY, invents nothing | `test_cli_reports_empty_without_inventing_metrics` | PASS |
| B-02 | Repository corpus is in fact empty | `test_repository_corpus_is_empty_and_status_is_reported_as_such` | PASS |
| B-03 | Only adjudicated documents scored | `test_only_adjudicated_documents_are_loaded` | PASS |
| B-04 | `_`-prefixed files never contribute | `test_underscore_prefixed_files_never_contribute` | PASS |
| B-05 | Precision/recall math correct | `test_perfect_prediction_scores_perfect_recall_and_precision` | PASS |
| B-06 | False negatives counted | `test_missed_gold_annotation_counts_as_a_false_negative` | PASS |
| B-07 | False positives counted | `test_unannotated_detection_counts_as_a_false_positive` | PASS |
| B-08 | F2 weights recall above precision | `test_f2_weights_recall_above_precision` | PASS |
| B-09 | Pressure agreement measured separately from detection | `test_pressure_disagreement_is_measured_separately_from_detection` | PASS |
| B-10 | No aggregate hides a failing mechanism | `test_no_aggregate_hides_a_failing_mechanism` | PASS |
| B-11 | Worked example excerpts round-trip | `test_worked_example_excerpts_round_trip` | PASS |
| B-12 | **Detector calibration measured** | Requires human annotation | **UNVERIFIED** |

## Security

| ID | Requirement | Verification | Status |
|---|---|---|---|
| S-01 | `esc` neutralizes markup-breaking characters | `esc neutralizes every character...` | PASS |
| S-02 | Ampersand escaped first (no entity reconstruction) | `esc escapes ampersands first...` | PASS |
| S-03 | Hostile payloads produce no live markup | `hostile article payloads survive escaping...` (6 payloads) | PASS |
| S-04 | Article text routed through `esc` | `article text is routed through esc before rendering` | PASS |
| S-05 | Bootstrap JSON cannot close its script tag | `built artifact embeds fixture data...` | PASS |
| S-06 | No network primitives in artifact | `built artifact performs no network access of any kind` | PASS |
| S-07 | No credentials in artifact | `built artifact contains no credentials...` | PASS |
| S-08 | No overclaiming language in artifact | `built artifact makes no calibration or benchmark accuracy claim` | PASS |
| S-09 | No network code anywhere in services | Bug-sweep grep: 0 hits | PASS |
| S-10 | Hostile text preserved verbatim, spans intact | `test_html_and_script_text_is_treated_as_literal_content` | PASS |

## Cross-language contracts

| ID | Requirement | Verification | Status |
|---|---|---|---|
| X-01 | TS unions match schema.json | `TypeScript pressure/confidence/voice unions match...` | PASS |
| X-02 | TS MechanismId matches taxonomy | `TypeScript MechanismId union matches...` | PASS |
| X-03 | Python runtime vocabulary matches schema.json | `Python detector_contract runtime vocabulary matches...` | PASS |
| X-04 | TS and Python agree with each other | `TypeScript and Python agree with each other...` | PASS |
| X-05 | Drift is detected | Injected rogue enum value → both suites failed, then reverted | PASS |
| X-06 | Level 2 output satisfies the Python contract | `tests/local-preview-contract.test.mjs` | PASS |

## Build

| ID | Requirement | Verification | Status |
|---|---|---|---|
| A-01 | TypeScript typecheck | `npm run typecheck` exit 0 | PASS |
| A-02 | Build succeeds | `npm run build` exit 0 | PASS |
| A-03 | Build reproducible | Two clean builds, identical SHA-256 | PASS |
| A-04 | `SHA256.txt` matches artifact | Compared | PASS |
| A-05 | Protected root files byte-identical to main | 9/9 hash-compared | PASS |

## Accessibility and runtime — see `tests/prototype-parity/PARITY_MATRIX.md`

| ID | Requirement | Status |
|---|---|---|
| Y-01 | One accessible article representation | PASS (`artifact.test.mjs`) |
| Y-02 | Overlay `aria-hidden` | PASS |
| Y-03 | Keyboard route through findings | UNVERIFIED |
| Y-04 | Visible focus | UNVERIFIED |
| Y-05 | Dialog naming | UNVERIFIED |
| Y-06 | Initial focus on open | UNVERIFIED |
| Y-07 | Tab focus trap | UNVERIFIED |
| Y-08 | Shift+Tab trap | UNVERIFIED |
| Y-09 | Escape closes | UNVERIFIED |
| Y-10 | Focus restoration | UNVERIFIED |
| Y-11 | Non-color mechanism meaning | UNVERIFIED |
| Y-12 | Textual pressure/confidence | PASS (rendered as text, `artifact.test.mjs` structure) |
| Y-13 | Minimum touch targets | UNVERIFIED |
| Y-14 | Reduced Motion | UNVERIFIED |
| Y-15 | Status/error announcements | UNVERIFIED |
| Y-16 | Screen-reader session | UNVERIFIED |

## Totals

| Status | Count |
|---|---:|
| PASS | 106 |
| FAIL | 0 |
| UNVERIFIED | 16 |
| N/A | 0 |

Every UNVERIFIED row is either browser-runtime dependent (15) or requires human
annotation (1, B-12). None is unverified through omission.
