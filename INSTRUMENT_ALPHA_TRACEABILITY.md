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
| B-12 | **Detector calibration measured** | Requires human annotation | UNVERIFIED |

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
| X-04 | TS and Python **controlled vocabulary** agree with each other (NOT domain object shapes — see M-13) | `TypeScript and Python agree with each other...` | PASS |
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

| ID | Requirement | Verification | Status |
|---|---|---|---|
| Y-01 | One accessible article representation | `tests/artifact.test.mjs` | PASS |
| Y-02 | Overlay `aria-hidden` | Executed | PASS |
| Y-03 | Keyboard route through findings | Runtime browser check required | UNVERIFIED |
| Y-04 | Visible focus | Runtime browser check required | UNVERIFIED |
| Y-05 | Dialog naming | Runtime browser check required | UNVERIFIED |
| Y-06 | Initial focus on open | Runtime browser check required | UNVERIFIED |
| Y-07 | Tab focus trap | Runtime browser check required | UNVERIFIED |
| Y-08 | Shift+Tab trap | Runtime browser check required | UNVERIFIED |
| Y-09 | Escape closes | Runtime browser check required | UNVERIFIED |
| Y-10 | Focus restoration | Runtime browser check required | UNVERIFIED |
| Y-11 | Non-color mechanism meaning | Runtime browser check required | UNVERIFIED |
| Y-12 | Textual pressure/confidence | Rendered as text; `tests/artifact.test.mjs` structure | PASS |
| Y-13 | Minimum touch targets | Runtime browser check required | UNVERIFIED |
| Y-14 | Reduced Motion | Runtime browser check required | UNVERIFIED |
| Y-15 | Status/error announcements | Runtime browser check required | UNVERIFIED |
| Y-16 | Screen-reader session | Runtime browser check required | UNVERIFIED |

## Independent pre-merge review closure

| ID | Requirement | Verification | Status |
|---|---|---|---|
| Z-01 | Numeric conflict blocks agreement | `test_numeric_conflict_is_not_usable_and_not_compatible` | PASS |
| Z-02 | Numeric formatting variants remain equivalent | `test_numeric_formatting_equivalence_still_aligns`, `test_thousands_separator_is_equivalent` | PASS |
| Z-03 | Currency scale conflict detected | `test_currency_scale_conflict_detected` | PASS |
| Z-04 | Clock-time conflict detected | `test_clock_time_conflict_detected` | PASS |
| Z-05 | Weekday conflict blocks agreement | `test_date_conflict_is_not_usable` | PASS |
| Z-06 | Same weekday is not a conflict | `test_same_weekday_is_not_a_conflict` | PASS |
| Z-07 | Calendar-date conflict detected | `test_calendar_date_conflict_detected` | PASS |
| Z-08 | Year conflict detected | `test_year_conflict_detected` | PASS |
| Z-09 | Antonym/polarity conflict blocks agreement | `test_polarity_pairs_detected`, `test_antonym_conflict_is_not_usable` | PASS |
| Z-10 | Direction conflict blocks agreement | `test_direction_conflict_is_not_usable` | PASS |
| Z-11 | Approval conflict blocks agreement | `test_approval_conflict_is_not_usable` | PASS |
| Z-12 | Permission conflict blocks agreement | `test_permission_conflict_is_not_usable` | PASS |
| Z-13 | Explicit negation remains contradictory | `test_explicit_negation_remains_contradictory` | PASS |
| Z-14 | One-sided detail is not a conflict | `test_one_sided_detail_is_not_a_conflict` | PASS |
| Z-15 | Ordinary rewording produces no false conflict | `test_no_divergence_on_ordinary_rewording` | PASS |
| Z-16 | Identical claims still align and remain usable | `test_identical_claims_still_align_and_remain_usable` | PASS |
| Z-17 | Only `same_proposition` may ground an omission | `test_specificity_relations_are_not_usable_for_omission`, `test_ordinary_compatible_wording_without_conflict_is_still_not_omission_grounds` | PASS |
| Z-18 | Numeric conflict cannot produce a Material Omission | `test_numeric_conflict_cannot_produce_a_material_omission` | PASS |
| Z-19 | Antonym conflict cannot produce a Material Omission | `test_antonym_conflict_cannot_produce_a_material_omission` | PASS |
| Z-20 | Date conflict cannot produce a Material Omission | `test_date_conflict_cannot_produce_a_material_omission` | PASS |
| Z-21 | No source credited with a claim it did not make | `test_no_source_is_ever_credited_with_a_claim_it_did_not_make` | PASS |
| Z-22 | Genuine omission still accepted after the fix | `test_genuine_omission_is_still_accepted` | PASS |
| Z-23 | Grounding alignments are divergence-free (invariant) | `evaluate_candidate_omission` invariant; asserted in `test_genuine_omission_is_still_accepted` | PASS |
| Z-24 | Temporal/measurement `by` does not name an agent | `test_temporal_and_measurement_by_phrases_do_not_name_an_agent` | PASS |
| Z-25 | Real named agents still excluded | `test_real_named_agents_are_still_excluded` | PASS |
| Z-26 | Unbalanced quote is not classified as a heading | `test_unbalanced_opening_quote_is_not_a_heading`, `test_unbalanced_curly_quote_is_not_a_heading` | PASS |
| Z-27 | Unbalanced quote never attributed to the outlet | `test_unbalanced_quote_never_attributes_to_the_outlet` | PASS |
| Z-28 | Quoted material in a heading belongs to the speaker | `test_quoted_material_inside_a_heading_belongs_to_the_speaker` | PASS |
| Z-29 | Ordinary heading remains outlet headline voice | `test_ordinary_heading_is_still_outlet_headline_voice` | PASS |
| Z-30 | High pressure with non-High confidence is reachable | `test_high_pressure_with_non_high_confidence_is_reachable` | PASS |
| Z-31 | Low pressure with High confidence is reachable | `test_low_pressure_with_high_confidence_is_reachable` | PASS |
| Z-32 | Provider does not raise certainty for rhetorical tier | `test_provider_does_not_raise_certainty_for_rhetorical_tier` | PASS |
| Z-33 | QA matrix summaries match their rows | `tools/check_traceability.py`; `test_all_qa_matrices_are_internally_consistent` | PASS |
| Z-34 | Every QA row carries exactly one primary status | same checker rejects multi-status rows | PASS |
| Z-35 | P4 + Low confidence reachable in the shipped heuristic | Not constructible without contrived input; documented in `KNOWN_LIMITATIONS.md` | UNVERIFIED |

## Pre-calibration hardening

| ID | Requirement | Verification | Status |
|---|---|---|---|
| H-01 | Absence of divergence is not propositional identity | `test_no_role_swap_can_ground_an_omission` (11 swap classes) | PASS |
| H-02 | `same_proposition` requires exact normalized identity | `test_identity_requires_exact_normalized_match` | PASS |
| H-03 | Presentation-equivalent values still recognized | `test_presentation_equivalence_is_still_recognized` | PASS |
| H-04 | High overlap without identity is never usable | `test_high_overlap_without_identity_is_never_usable` | PASS |
| H-05 | Absent dependency data is unresolved, not independent | `test_absent_dependency_data_is_unresolved_not_independent` | PASS |
| H-06 | `unknown` dependence is unresolved | `test_unknown_link_is_unresolved` | PASS |
| H-07 | Low-confidence independence claim is not confirmed | `test_low_confidence_independence_claim_is_not_confirmed` | PASS |
| H-08 | Confirmed independent reporting counts | `test_confirmed_independent_reporting_counts` | PASS |
| H-09 | Syndication collapses origins | `test_syndication_is_dependent` | PASS |
| H-10 | Partial dependence graph fails closed | `test_partial_graph_fails_closed` | PASS |
| H-11 | Omission refused without confirmed independence | `test_unconfirmed_independence_is_refused` | PASS |
| H-12 | Supporting claims must belong to the comparison set | `test_foreign_supporting_article_is_refused` | PASS |
| H-13 | Target article cannot corroborate its own omission | `test_target_article_cannot_corroborate_itself` | PASS |
| H-14 | Source/article mapping conflicts rejected | `test_source_article_mismatch_is_refused` | PASS |
| H-15 | Target claims must belong to the target article | `test_foreign_target_claim_is_refused` | PASS |
| H-16 | Chronology compares instants, not strings | `test_chronology_uses_instants_not_strings` | PASS |
| H-17 | Same instant in different offsets accepted | `test_same_instant_in_different_offsets_is_accepted` | PASS |
| H-18 | Naive timestamps rejected | `test_naive_timestamp_is_refused` | PASS |
| H-19 | Malformed timestamps rejected | `test_malformed_timestamp_is_refused` | PASS |
| H-20 | Uncertain verdict is never confirmed | `test_uncertain_verdict_is_always_candidate` | PASS |
| H-21 | `applies=yes` can still be confirmed | `test_yes_verdict_can_still_be_confirmed` | PASS |
| H-22 | Invented criteria rejected | `test_invented_criterion_is_rejected` | PASS |
| H-23 | Criteria from another mechanism rejected | `test_criterion_from_another_mechanism_is_rejected` | PASS |
| H-24 | Exclusion criterion in positive list rejected | `test_exclusion_criterion_in_positive_list_is_rejected` | PASS |
| H-25 | Every shipped finding cites only taxonomy criteria | `test_every_shipped_finding_cites_only_taxonomy_criteria` | PASS |
| H-26 | Model response arrays are real arrays | `test_string_where_array_expected_is_rejected` | PASS |
| H-27 | Model numeric edge cases rejected (bool/NaN/Inf/range) | `test_numeric_edge_cases_are_rejected` | PASS |
| H-28 | Unknown enum / extra properties rejected | `test_unknown_applies_and_extra_properties_are_rejected` | PASS |
| H-29 | Low-confidence relation cannot promote claim state | `test_low_confidence_relation_cannot_promote_to_direct_support` | PASS |
| H-30 | Low-confidence contradiction is contested only | `test_low_confidence_contradiction_is_contested_not_contradicted` | PASS |
| H-31 | Duplicate relations to one item do not corroborate | `test_duplicate_relations_to_one_item_do_not_corroborate` | PASS |
| H-32 | Two distinct usable items corroborate | `test_two_distinct_items_corroborate` | PASS |
| H-33 | Corpus: excerpt must round-trip | `test_excerpt_must_round_trip_against_its_passage` | PASS |
| H-34 | Corpus: stale taxonomy version rejected | `test_stale_taxonomy_version_is_rejected` | PASS |
| H-35 | Corpus: span bounds validated | `test_span_bounds_are_validated` | PASS |
| H-36 | Corpus: boolean coordinates rejected | `test_boolean_coordinates_are_rejected` | PASS |
| H-37 | Corpus: unknown/cross-document mechanisms rejected | `test_unknown_and_cross_document_mechanisms_are_rejected` | PASS |
| H-38 | Corpus: voiceClass required | `test_missing_voice_class_is_rejected` | PASS |
| H-39 | Corpus: duplicate ids/ordinals rejected | `test_duplicate_annotation_ids_and_passage_ordinals_are_rejected` | PASS |
| H-40 | Corpus: two independent annotators required | `test_single_annotator_document_cannot_be_adjudicated` | PASS |
| H-41 | Corpus: original submissions preserved | `test_original_submissions_must_be_preserved_from_two_annotators` | PASS |
| H-42 | Corpus: unresolved `unresolvable` cannot be adjudicated | `test_unresolved_unresolvable_cannot_be_adjudicated` | PASS |
| H-43 | Corpus: invalid adjudicated file is fatal, not skipped | `test_invalid_adjudicated_document_is_fatal_not_skipped` | PASS |
| H-44 | Corpus: non-adjudicated files ignored, not errors | `test_non_adjudicated_documents_are_ignored_not_errors` | PASS |
| H-45 | Repository corpus remains EMPTY | `test_repository_corpus_remains_empty_and_valid` | PASS |
| H-46 | Quoted loading detected and attributed to speaker | `test_quoted_loading_is_detected_and_attributed_to_the_speaker` | PASS |
| H-47 | Taxonomy no longer excludes quoted speech | `test_taxonomy_no_longer_excludes_quoted_speech` | PASS |
| H-48 | Annotation guide matches taxonomy version | `test_annotation_guide_matches_the_taxonomy_version` | PASS |
| H-49 | Taxonomy pressure examples are executable goldens | `test_taxonomy_examples_agree_with_the_scorer` | PASS |
| H-50 | Genuine binary is not a false dilemma | `test_o01_genuine_binary_is_not_a_false_dilemma` | PASS |
| H-51 | Change-of-state presupposition path is live | `test_o02_change_of_state_presupposition_is_live` | PASS |
| H-52 | Run id changes with taxonomy/provider version | `test_o06_run_id_changes_with_taxonomy_and_provider_version` | PASS |
| H-53 | Article identity separates content from source | `test_o07_identical_text_from_different_publishers_gets_distinct_article_ids` | PASS |
| H-54 | Batch with a successful zero-finding passage is partial | `test_o08_batch_with_a_successful_zero_finding_passage_is_partial` | PASS |
| H-55 | Provider vs internal faults distinguished | `test_o09_provider_faults_and_internal_faults_are_distinguished` | PASS |
| H-56 | Curly single quotes are quoted speech | `test_o10_curly_single_quotes_are_quoted_speech` | PASS |
| H-57 | Apostrophes are not quotation | `test_o10_apostrophes_are_not_quotation` | PASS |
| H-58 | Exclusions are candidate-local | `test_o11_exclusions_are_candidate_local_not_whole_passage` | PASS |
| H-59 | Benchmark matching is maximum-cardinality | `test_maximum_cardinality_beats_greedy` | PASS |
| H-60 | Benchmark matching is order-independent | `test_matching_is_deterministic` | PASS |
| H-61 | Level 2 quoted rhetoric is not outlet voice | `tests/local-preview-voice.test.mjs` | PASS |
| H-62 | Level 2 catches "Mistakes were made" | `tests/local-preview-voice.test.mjs` | PASS |
| H-63 | Level 2 temporal `by` does not suppress findings | `tests/local-preview-voice.test.mjs` | PASS |
| H-64 | Zero findings shows no peak pressure | `tests/local-preview-voice.test.mjs` | PASS |
| H-65 | `qa:runtime` fails with an actionable message, not a Linux path | Executed: exits 2 with install instructions | PASS |
| H-66 | Numeric proposition identity is exact (Decimal, not lossy float) | `test_adjacent_and_near_neighbor_numbers_remain_distinct` | PASS |
| H-67 | Formatting-equivalent numeric propositions still canonicalize equal | `test_formatting_equivalent_pairs_canonicalize_equal` | PASS |
| H-68 | Canonicalization marker re-processing is prevented (idempotent) | `test_canonicalization_is_idempotent` | PASS |
| H-69 | No nested or scientific-notation markers survive canonicalization | `test_no_nested_or_scientific_notation_markers_survive` | PASS |
| H-70 | Adjacent numeric values never collide across magnitudes | `test_deterministic_property_adjacent_values_never_collide` | PASS |
| H-71 | Word order still carries semantic role after the exact-identity fix | `test_word_order_still_carries_role_after_the_fix` | PASS |
| H-72 | Unicode NFD/NFC forms remain equivalent under exact identity | `test_unicode_nfd_and_nfc_forms_are_equivalent` | PASS |
| H-73 | Adjacent currency values cannot ground a Material Omission | `test_adjacent_currency_values_cannot_ground_an_omission` | PASS |
| H-74 | Adjacent plain integers cannot ground a Material Omission | `test_adjacent_plain_integers_cannot_ground_an_omission` | PASS |
| H-75 | Identity gate alone rejects false matches with divergence detection disabled | `test_identity_gate_alone_rejects_even_with_divergence_detection_disabled` | PASS |
| H-76 | Genuinely identical large numbers still ground a well-formed omission | `test_genuinely_identical_large_numbers_still_ground_a_well_formed_omission` | PASS |
| H-77 | `annotatorSubmissions` is required for adjudicated documents | `test_missing_annotator_submissions_is_rejected` | PASS |
| H-78 | Empty `annotatorSubmissions` is rejected, not silently bypassed | `test_empty_annotator_submissions_is_rejected` | PASS |
| H-79 | Two zero-proposal submissions is a valid hard negative | `test_two_zero_proposal_submissions_is_a_valid_hard_negative` | PASS |
| H-80 | Three zero-proposal submissions is valid | `test_three_zero_proposal_submissions_is_valid` | PASS |
| H-81 | One finding plus one zero-proposal submission is valid | `test_one_finding_plus_one_zero_proposal_submission_is_valid` | PASS |
| H-82 | Duplicate `submissionId` is rejected | `test_duplicate_submission_id_is_rejected` | PASS |
| H-83 | An annotator submitting twice is rejected | `test_annotator_submitting_twice_is_rejected` | PASS |
| H-84 | `annotatorIds` must agree with preserved submission records | `test_annotator_ids_must_agree_with_submission_records` | PASS |
| H-85 | Duplicate `proposalId` across different submissions is rejected | `test_duplicate_proposal_id_across_different_submissions_is_rejected` | PASS |
| H-86 | Preserved proposal excerpt must round-trip against its passage | `test_proposal_excerpt_must_round_trip` | PASS |
| H-87 | Preserved proposal missing `voiceClass` is rejected | `test_proposal_missing_voice_class_is_rejected` | PASS |
| H-88 | Preserved proposal with unknown mechanism is rejected | `test_proposal_unknown_mechanism_is_rejected` | PASS |
| H-89 | A resolution referencing an unknown proposal is rejected | `test_resolution_referencing_unknown_proposal_is_rejected` | PASS |
| H-90 | Worked example carries two real structured submissions | `test_worked_example_carries_two_structured_submissions` | PASS |
| H-91 | `evaluate.py` treats malformed adjudicated material as fatal, not skipped | `test_evaluate_treats_malformed_adjudicated_material_as_fatal` | PASS |
| H-92 | Preserved submissions recover every inter-annotator agreement dimension | `test_preserved_submissions_recover_every_agreement_dimension` | PASS |

| H-93 | Arbitrary-precision decimal scaling never rounds (30/50/100-digit adjacent values, all scales) | `test_30_digit_adjacent_values_remain_distinct_at_every_scale` (+50/100) | PASS |
| H-94 | Exact scaling matches manual bigint multiplication | `test_exact_scaling_matches_manual_multiplication` | PASS |
| H-95 | Presentation equivalents still match at huge magnitude | `test_presentation_equivalents_still_match_at_huge_magnitude` | PASS |
| H-96 | Literal marker text cannot impersonate a real numeric identity token | `test_literal_marker_text_does_not_equal_a_real_number` | PASS |
| H-97 | Injection using whatever the diagnostic rendering CURRENTLY produces still fails identity | `test_injection_using_whatever_the_diagnostic_rendering_CURRENTLY_produces` | PASS |
| H-98 | Marker injection cannot ground a Material Omission with divergence disabled | `test_marker_injection_cannot_ground_a_material_omission_with_divergence_disabled` | PASS |
| H-99 | Every malformed proposal shape (type/bounds) from the attack list is rejected (17 cases) | `M09CorpusIntegrityTests` proposal-validation methods | PASS |
| H-100 | Ghost proposal reference rejected even when zero real proposals exist | `test_ghost_proposal_reference_is_rejected_even_when_no_real_proposals_exist` | PASS |
| H-101 | Unexplained positive gold after two empty submissions is rejected | `test_unexplained_positive_gold_after_two_empty_submissions_is_rejected` | PASS |
| H-102 | Explicit adjudicator_add resolution grounds unproposed positive gold | `test_explicit_adjudicator_add_resolution_grounds_unproposed_positive_gold` | PASS |
| H-103 | `drop` resolution carrying a resultingAnnotationId is rejected | `test_drop_resolution_with_resulting_annotation_id_is_rejected` | PASS |
| H-104 | Duplicate `resolutionId` is rejected | `test_duplicate_resolution_id_is_rejected` | PASS |
| H-105 | Resolution missing `adjudicatorId` is rejected | `test_resolution_missing_adjudicator_id_is_rejected` | PASS |
| H-106 | JSON Schema conditionally requires annotatorIds/annotatorSubmissions for adjudicated documents | `test_adjudicated_conditionally_requires_annotator_fields` | PASS |
| H-107 | Schema `decision` enum matches the Python validator's | `test_decision_enum_matches_the_python_validator` | PASS |
| H-108 | Structured submission/proposal/resolution records reject unknown properties | `test_structured_records_reject_additional_properties` | PASS |
| H-109 | `resolutions` field of the wrong type is rejected cleanly, not character-iterated | `test_resolutions_field_wrong_type_is_rejected_cleanly` | PASS |
| H-110 | Long digit run with no percent sign does not hang (regex backtracking DoS closed) | `test_long_digit_run_with_no_percent_sign_does_not_hang` | PASS |
| H-111 | Many numbers in one document does not hang (O(k²) overlap-check DoS closed) | `test_many_numbers_in_one_document_does_not_hang` | PASS |

| H-112 | Malformed comma grouping cannot establish numeric identity with a clean integer | `test_malformed_grouping_never_matches_a_clean_integer` | PASS |
| H-113 | No malformed numeric form collides with any clean integer (exhaustive cross-product) | `test_no_malformed_form_collides_with_any_clean_integer` | PASS |
| H-114 | Malformed grouping is not reflowed into a single clean numeric token | `test_malformed_grouping_is_not_reflowed_into_one_clean_token` | PASS |
| H-115 | Well-formed thousands grouping still normalizes | `test_well_formed_grouping_still_normalizes` | PASS |
| H-116 | Malformed grouping cannot ground an omission with divergence disabled | `test_malformed_grouping_cannot_ground_an_omission_without_divergence` | PASS |
| H-117 | Auto-merge requires ≥2 independent annotators agreeing | `test_identical_proposals_from_two_annotators_auto_merge` / `test_only_one_preserved_proposal_cannot_auto_merge` | PASS |
| H-118 | Presence disagreement requires adjudication | `test_presence_disagreement_requires_adjudication` | PASS |
| H-119 | Pressure disagreement cannot auto-merge | `test_pressure_disagreement_cannot_auto_merge` | PASS |
| H-120 | Voice disagreement cannot auto-merge | `test_voice_disagreement_cannot_auto_merge` | PASS |
| H-121 | Auto-merged gold span must equal the protocol-defined intersection | `test_gold_that_is_not_the_intersection_is_rejected` | PASS |
| H-122 | Span IoU below threshold cannot auto-merge | `test_iou_below_threshold_cannot_auto_merge` | PASS |
| H-123 | Three-annotator consensus policy is explicit and tested | `test_three_annotator_consensus_uses_intersection_over_all` | PASS |
| H-124 | `merge` cannot have empty `proposalIds` | `test_merge_with_empty_proposal_ids_is_rejected` | PASS |
| H-125 | `merge` must draw on ≥2 distinct annotators | `test_merge_from_a_single_annotator_is_rejected` | PASS |
| H-126 | `split` represents multiple resulting gold annotations | `test_valid_split_produces_two_gold_annotations` / `test_split_with_one_result_is_rejected` | PASS |
| H-127 | Resolution cardinality is decision-specific | `test_cardinality_table_covers_every_gold_producing_decision` | PASS |
| H-128 | Removed singular `resultingAnnotationId` is rejected outright | `test_removed_singular_resulting_annotation_id_is_rejected` | PASS |
| H-129 | Each gold annotation is grounded exactly once | `test_two_resolutions_cannot_claim_the_same_gold_annotation` | PASS |
| H-130 | Schema resolution cardinality matches the Python table | `test_schema_resolution_cardinality_matches_the_python_table` | PASS |
| H-131 | Schema requires ≥2 unique annotatorIds | `test_schema_requires_two_unique_annotator_ids` | PASS |
| H-132 | Schema documents the Python-only semantic boundary honestly | `test_schema_documents_the_python_only_semantic_boundary` | PASS |

| H-133 | Uphold result must derive from (exactly preserve) the cited proposal | `test_false_uphold_producing_a_different_finding_is_rejected` | PASS |
| H-134 | Uphold may differ only in reviewerConfidence | `test_uphold_may_differ_in_reviewer_confidence` | PASS |
| H-135 | Merge result must derive from the cited proposals (passage, mechanism, overlap) | `test_false_merge_producing_an_unrelated_mechanism_is_rejected` / `test_merge_relocating_the_finding_is_rejected` | PASS |
| H-136 | Split results remain tied to the source passage and region | `test_false_split_producing_findings_elsewhere_is_rejected` | PASS |
| H-137 | Valid uphold / merge / split are still accepted | `test_valid_uphold_preserving_the_proposal_exactly` / `test_valid_merge_reconciles_a_real_disagreement` / `test_valid_split_divides_the_source_region` | PASS |
| H-138 | Third-annotator pressure dissent blocks auto-merge | `test_two_agree_one_pressure_dissent_fails` | PASS |
| H-139 | Third-annotator voice dissent blocks auto-merge | `test_two_agree_one_voice_dissent_fails` | PASS |
| H-140 | Third-annotator mechanism dissent blocks auto-merge | `test_two_agree_one_mechanism_dissent_fails` | PASS |
| H-141 | Every declared annotator must participate in an auto-merge | `test_two_agree_one_absent_fails` | PASS |
| H-142 | Ambiguous multi-proposal cluster from one annotator escalates | `test_an_annotator_with_two_matching_proposals_is_ambiguous_and_fails` | PASS |
| H-143 | Unanimous 3/3 agreement still auto-merges | `test_three_of_three_agree_passes` | PASS |
| H-144 | Auto-merge + resolution on the same gold is rejected | `test_auto_merge_plus_resolution_is_conflicting_provenance` | PASS |
| H-145 | Gold with neither origin is rejected | `test_neither_origin_is_ungrounded` | PASS |
| H-146 | Adjudicator cannot be an original annotator | `test_original_annotator_cannot_adjudicate` | PASS |
| H-147 | Independent third adjudicator is accepted | `test_independent_third_adjudicator_is_accepted` | PASS |
| H-148 | annotatorIds strictly validated (duplicate/non-string/empty/bool/arity/type) | `StrictAnnotatorIdsTests` | PASS |

| H-149 | Split result in the gap between disjoint sources is rejected (no bounding hull) | `test_result_in_the_gap_between_disjoint_sources_is_rejected` | PASS |
| H-150 | Split cross-passage coordinate collision is rejected | `test_cross_passage_coordinate_collision_is_rejected` | PASS |
| H-151 | Every cited split source must be represented by a result on its own passage | `test_cited_proposal_represented_by_no_result_is_rejected` | PASS |
| H-152 | Valid single-source and multi-source splits still accepted | `test_single_source_split_into_two_overlapping_results` / `test_every_result_tied_to_an_actual_source_passes` | PASS |
| H-153 | Split may yield different mechanismIds | `test_split_may_produce_different_mechanisms` | PASS |
| H-154 | Merge of disjoint source spans is rejected (no bridging) | `test_two_disjoint_sources_cannot_be_merged` | PASS |
| H-155 | Merge requires a non-empty common source intersection | `test_three_sources_without_a_common_intersection_are_rejected` | PASS |
| H-156 | Merge gold may not extend beyond the cited source hull | `test_gold_extending_beyond_the_source_hull_is_rejected` | PASS |
| H-157 | Valid overlapping merges (2 and 3 sources) still accepted | `test_two_overlapping_sources_reconcile` / `test_three_sources_with_a_common_intersection_pass` | PASS |
| H-158 | Auto-merge clustering is occurrence-local (two findings per passage) | `test_two_distinct_occurrences_in_one_passage_both_auto_merge` | PASS |
| H-159 | Occurrence-locality does not weaken the ambiguity guard | `test_genuinely_ambiguous_overlapping_proposals_still_escalate` | PASS |

## Totals

| Status | Count |
|---|---:|
| PASS | 325 |
| FAIL | 0 |
| UNVERIFIED | 15 |
| N/A | 0 |

**These totals are machine-verified**, not hand-counted: `tools/check_traceability.py`
parses every ID-prefixed row, counts statuses, compares them to this summary and
exits non-zero on any drift. It also rejects rows carrying more than one primary
status, so structural presence can never be silently counted as an executed PASS.
The check runs in the test suite as
`test_all_qa_matrices_are_internally_consistent`.

Every UNVERIFIED row is browser-runtime dependent (13), requires human annotation
(B-12), or is an acknowledged heuristic limitation (Z-35). None is unverified
through omission.
