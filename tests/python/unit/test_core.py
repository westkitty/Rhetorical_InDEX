"""Unit tests: document model, voice, scoring, validation, coverage, schema."""
from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.rhetoric import vocabulary as vocab  # noqa: E402
from services.rhetoric import scoring, voice  # noqa: E402
from services.rhetoric.document import (  # noqa: E402
    article_from_passages,
    compute_content_hash,
    normalize_text,
    segment,
)
from services.rhetoric.models import (  # noqa: E402
    AnalysisRun,
    Finding,
    batch_passages,
    dedupe_findings,
)
from services.rhetoric.validation import (  # noqa: E402
    DetectorRejection,
    resolve_span,
    validate_finding_payload,
)


def make_finding(**overrides):
    base = dict(
        finding_id="f1", analysis_run_id="r1", article_id="a1", passage_id="a1:p0000",
        mechanism_id="loaded_language", family="intrinsic_linguistic", excerpt="draconian",
        start_char=0, end_char=9, occurrence_index=0, pressure="P3", confidence="High",
        state="confirmed", voice_class="reporter", triggered_criteria=("c",),
    )
    base.update(overrides)
    return Finding(**base)


class DocumentModelTests(unittest.TestCase):
    def test_segmentation_preserves_structure_not_flattened(self):
        article = segment(
            "# Council Approves Plan\n\n"
            "The council met.\n\n"
            "> We object to this.\n\n"
            "- first item\n- second item\n"
        )
        kinds = [p.passage_type for p in article.passages]
        self.assertIn("heading", kinds)
        self.assertIn("paragraph", kinds)
        self.assertIn("blockquote", kinds)
        self.assertEqual(kinds.count("list_item"), 2)

    def test_content_hash_is_deterministic_and_input_sensitive(self):
        a = segment("The council approved the plan today.")
        b = segment("The council approved the plan today.")
        c = segment("The council rejected the plan today.")
        self.assertEqual(a.content_hash, b.content_hash)
        self.assertNotEqual(a.content_hash, c.content_hash)
        self.assertEqual(len(a.content_hash), 64, "content hash must be SHA-256 hex")

    def test_content_hash_covers_structure_not_only_words(self):
        same_words_different_structure = compute_content_hash(
            [("heading", "Budget cuts announced")]
        )
        as_paragraph = compute_content_hash([("paragraph", "Budget cuts announced")])
        self.assertNotEqual(same_words_different_structure, as_paragraph)

    def test_passage_ids_are_stable_and_addressable(self):
        article = segment("First para.\n\nSecond para.", article_id="art-fixed")
        self.assertEqual(
            [p.passage_id for p in article.passages], ["art-fixed:p0000", "art-fixed:p0001"]
        )
        self.assertEqual(article.passage("art-fixed:p0001").text, "Second para.")

    def test_normalization_does_not_rewrite_quotes_or_dashes(self):
        # Rewriting these would break exact-excerpt round-tripping.
        text = normalize_text("He said “no” — firmly.")
        self.assertIn("“", text)
        self.assertIn("—", text)

    def test_empty_input_is_rejected_not_silently_accepted(self):
        for bad in ("", "   ", "\n\n\n"):
            with self.assertRaises(ValueError):
                segment(bad)

    def test_span_coordinates_are_passage_local(self):
        article = article_from_passages("art-x", [("paragraph", "alpha beta"), ("paragraph", "gamma delta")])
        second = article.passages[1]
        self.assertEqual(second.text[0:5], "gamma")


class VoiceTests(unittest.TestCase):
    def _passage(self, text, kind="paragraph"):
        return article_from_passages("art-v", [(kind, text)]).passages[0]

    def test_quoted_span_is_attributed_to_speaker_not_outlet(self):
        passage = self._passage('The mayor said "this is an outrageous betrayal" on Tuesday.')
        start = passage.text.index("outrageous")
        result, _ = voice.classify(passage, start, start + len("outrageous betrayal"))
        self.assertEqual(result, "quoted_speaker")
        self.assertFalse(voice.is_outlet_voice(result))

    def test_unquoted_span_is_outlet_voice(self):
        passage = self._passage("The council approved a draconian scheme yesterday.")
        start = passage.text.index("draconian")
        result, _ = voice.classify(passage, start, start + len("draconian scheme"))
        self.assertTrue(voice.is_outlet_voice(result))

    def test_span_straddling_a_quote_boundary_is_uncertain(self):
        passage = self._passage('Officials called it "a reckless move" in a statement.')
        start = passage.text.index("it")
        end = passage.text.index("reckless") + len("reckless")
        result, _ = voice.classify(passage, start, end)
        self.assertEqual(result, "uncertain")

    def test_unbalanced_quotes_yield_uncertain_not_a_confident_guess(self):
        passage = self._passage('The report said "the plan is draconian and unworkable')
        start = passage.text.index("draconian")
        result, _ = voice.classify(passage, start, start + len("draconian"))
        self.assertIn(result, {"uncertain", "quoted_speaker"})

    def test_heading_is_headline_voice(self):
        passage = self._passage("Draconian Scheme Approved", kind="heading")
        result, _ = voice.classify(passage, 0, len("Draconian"))
        self.assertEqual(result, "headline")

    def test_out_of_bounds_span_raises(self):
        passage = self._passage("short text")
        with self.assertRaises(ValueError):
            voice.classify(passage, 0, 999)


class ScoringIndependenceTests(unittest.TestCase):
    """Pressure and confidence must be able to vary independently."""

    def test_high_pressure_can_carry_low_confidence(self):
        # Post-M-14 the rubric grades by dominance, so P4 requires dominant
        # density or dehumanizing vocabulary rather than one severe word.
        pressure = scoring.score_pressure(
            "loaded_language",
            {
                "peak_tier": "severe", "term_count": 3,
                "tiers": ["severe", "strong", "strong"],
                "terms": ["draconian", "reckless", "brutal"],
                "passage_density": 0.5,
            },
        )
        confidence = scoring.score_confidence(
            generator="grammatical.presupp_change_of_state_v1",
            features={"construction": "change_of_state", "technical_context": True},
            voice_certainty=0.3, verdict_certainty=0.2, agreeing_votes=0, total_votes=1,
        )
        self.assertEqual(pressure.value, "P4")
        self.assertEqual(confidence.value, "Low")

    def test_low_pressure_can_carry_high_confidence(self):
        pressure = scoring.score_pressure(
            "presupposition", {"construction": "change_of_state", "embeds_disputed_premise": False, "span_words": 3},
        )
        confidence = scoring.score_confidence(
            generator="lexical.loaded_v1", features={},
            voice_certainty=0.95, verdict_certainty=0.95, agreeing_votes=1, total_votes=1,
        )
        self.assertEqual(pressure.value, "P1")
        self.assertEqual(confidence.value, "High")

    def test_confidence_model_never_receives_pressure(self):
        import inspect
        signature = inspect.signature(scoring.score_confidence)
        self.assertNotIn("pressure", signature.parameters)

    def test_pressure_uses_mechanism_specific_rubric(self):
        # Same feature bag, different mechanism -> different rubric, so a shared
        # generic severity scale would be detectable here.
        anchor = scoring.pressure_anchor("agent_suppression", "P3")
        self.assertIn("actor", anchor.lower())
        self.assertNotEqual(
            scoring.pressure_anchor("false_dilemma", "P3"),
            scoring.pressure_anchor("agent_suppression", "P3"),
        )

    def test_every_mechanism_and_level_has_an_anchor(self):
        for mechanism_id in vocab.INTRINSIC_ALPHA_SLICE:
            for level in vocab.PRESSURE_ORDER:
                self.assertTrue(scoring.pressure_anchor(mechanism_id, level).strip())

    def test_reportable_state_uses_two_thresholds(self):
        self.assertEqual(scoring.reportable_state("Low"), "candidate")
        self.assertEqual(scoring.reportable_state("Medium"), "confirmed")
        self.assertEqual(scoring.reportable_state("High"), "confirmed")

    def test_unknown_mechanism_pressure_raises_rather_than_defaulting(self):
        with self.assertRaises(ValueError):
            scoring.score_pressure("appeal_to_fear", {})


class SpanResolutionTests(unittest.TestCase):
    def setUp(self):
        self.article = article_from_passages(
            "art-s",
            [("paragraph", "The reckless plan, the reckless plan again, was approved.")],
        )
        self.passage = self.article.passages[0]

    def test_unique_excerpt_resolves(self):
        resolved = resolve_span(self.passage, excerpt="was approved")
        self.assertEqual(
            self.passage.text[resolved.start_char:resolved.end_char], "was approved"
        )

    def test_repeated_excerpt_without_locator_is_rejected(self):
        with self.assertRaises(DetectorRejection) as ctx:
            resolve_span(self.passage, excerpt="reckless plan")
        self.assertIn("ambiguous", str(ctx.exception))

    def test_repeated_excerpt_with_valid_locator_resolves(self):
        first = resolve_span(self.passage, excerpt="reckless plan", occurrence_index=0)
        second = resolve_span(self.passage, excerpt="reckless plan", occurrence_index=1)
        self.assertLess(first.start_char, second.start_char)

    def test_out_of_range_locator_is_rejected(self):
        with self.assertRaises(DetectorRejection):
            resolve_span(self.passage, excerpt="reckless plan", occurrence_index=7)

    def test_coordinate_excerpt_mismatch_is_rejected(self):
        with self.assertRaises(DetectorRejection):
            resolve_span(self.passage, excerpt="totally different", start_char=0, end_char=3)

    def test_inverted_and_out_of_bounds_spans_are_rejected(self):
        with self.assertRaises(DetectorRejection):
            resolve_span(self.passage, excerpt=None, start_char=10, end_char=4)
        with self.assertRaises(DetectorRejection):
            resolve_span(self.passage, excerpt=None, start_char=0, end_char=9999)
        with self.assertRaises(DetectorRejection):
            resolve_span(self.passage, excerpt=None, start_char=-1, end_char=5)

    def test_absent_excerpt_is_rejected(self):
        with self.assertRaises(DetectorRejection):
            resolve_span(self.passage, excerpt="this phrase is not present")

    def test_boolean_is_not_accepted_as_an_integer_locator(self):
        with self.assertRaises(DetectorRejection):
            resolve_span(self.passage, excerpt="reckless plan", occurrence_index=True)


class FindingPayloadValidationTests(unittest.TestCase):
    def setUp(self):
        self.article = article_from_passages(
            "art-p", [("paragraph", "A draconian scheme was approved without debate.")]
        )
        self.valid = {
            "mechanismId": "loaded_language",
            "passageId": "art-p:p0000",
            "excerpt": "draconian scheme",
            "pressure": "P3",
            "confidence": "High",
            "voiceClass": "reporter",
            "triggeredCriteria": ["Contains strongly evaluative adjectives."],
            "taxonomyVersion": vocab.taxonomy_version(),
        }
        self.allowed = vocab.INTRINSIC_ALPHA_SLICE

    def _validate(self, payload):
        return validate_finding_payload(
            payload, article=self.article, allowed_mechanisms=self.allowed,
            taxonomy_version=vocab.taxonomy_version(),
        )

    def test_valid_payload_resolves(self):
        resolved = self._validate(dict(self.valid))
        self.assertEqual(resolved.excerpt, "draconian scheme")

    def test_missing_criteria_is_rejected_and_not_backfilled(self):
        """The single most dangerous shortcut: never substitute taxonomy text."""
        for bad in (None, [], "", ["   "], [123]):
            payload = dict(self.valid)
            payload["triggeredCriteria"] = bad
            with self.assertRaises(DetectorRejection):
                self._validate(payload)

    def test_cross_document_mechanism_is_rejected(self):
        for mechanism_id in ("material_omission", "selective_quotation", "headline_body_mismatch"):
            payload = dict(self.valid)
            payload["mechanismId"] = mechanism_id
            with self.assertRaises(DetectorRejection):
                self._validate(payload)

    def test_mechanism_outside_implemented_slice_is_rejected(self):
        payload = dict(self.valid)
        payload["mechanismId"] = "appeal_to_fear"  # real taxonomy id, not implemented
        with self.assertRaises(DetectorRejection):
            self._validate(payload)

    def test_legacy_plural_mechanisms_field_is_rejected(self):
        payload = dict(self.valid)
        payload["mechanisms"] = ["loaded_language", "appeal_to_fear"]
        with self.assertRaises(DetectorRejection):
            self._validate(payload)

    def test_invalid_vocabulary_values_are_rejected(self):
        for field, bad in (("pressure", "P9"), ("confidence", "Certain"), ("voiceClass", "robot")):
            payload = dict(self.valid)
            payload[field] = bad
            with self.assertRaises(DetectorRejection):
                self._validate(payload)

    def test_unknown_passage_is_rejected(self):
        payload = dict(self.valid)
        payload["passageId"] = "art-p:p9999"
        with self.assertRaises(DetectorRejection):
            self._validate(payload)

    def test_unknown_taxonomy_or_schema_version_is_rejected(self):
        payload = dict(self.valid)
        payload["taxonomyVersion"] = "9.9.9-nope"
        with self.assertRaises(DetectorRejection):
            self._validate(payload)
        payload = dict(self.valid)
        payload["detectorSchemaVersion"] = "0.0.0-nope"
        with self.assertRaises(DetectorRejection):
            self._validate(payload)


class CoverageAndReconciliationTests(unittest.TestCase):
    def _run(self, passage_ids):
        return AnalysisRun(
            run_id="r1", article_id="a1", content_hash="h", taxonomy_version="t",
            detector_version="d", provider={"kind": "mock"}, all_passage_ids=tuple(passage_ids),
        )

    def test_complete_coverage_yields_complete(self):
        run = self._run(["p0", "p1"])
        run.processed_passage_ids.extend(["p0", "p1"])
        run.finalize()
        self.assertEqual(run.status, "complete")
        self.assertTrue(run.is_complete_coverage)

    def test_partial_coverage_yields_partial_not_complete(self):
        run = self._run(["p0", "p1", "p2"])
        run.processed_passage_ids.append("p0")
        run.failed_passage_ids.append("p1")
        run.finalize()
        self.assertEqual(run.status, "partial")
        self.assertFalse(run.is_complete_coverage)
        self.assertEqual(run.unprocessed_passage_ids, ("p2",))

    def test_total_failure_yields_failed(self):
        run = self._run(["p0", "p1"])
        run.failed_passage_ids.extend(["p0", "p1"])
        run.finalize()
        self.assertEqual(run.status, "failed")

    def test_coverage_buckets_partition_passages(self):
        run = self._run(["p0", "p1"])
        run.processed_passage_ids.append("p0")
        run.failed_passage_ids.append("p0")  # deliberately inconsistent
        with self.assertRaises(AssertionError):
            run.assert_coverage_invariant()

    def test_batching_never_splits_a_passage(self):
        batches = batch_passages([f"p{i}" for i in range(7)], 3)
        self.assertEqual([len(b) for b in batches], [3, 3, 1])
        flat = [pid for batch in batches for pid in batch]
        self.assertEqual(flat, [f"p{i}" for i in range(7)])

    def test_identical_spans_different_mechanisms_are_preserved(self):
        """Multi-tag is the product's core case and must survive dedupe."""
        findings = [
            make_finding(finding_id="f1", mechanism_id="loaded_language"),
            make_finding(finding_id="f2", mechanism_id="presupposition", family="framing_epistemic"),
        ]
        self.assertEqual(len(dedupe_findings(findings)), 2)

    def test_duplicate_identity_collapses_and_merges_votes(self):
        findings = [
            make_finding(finding_id="f1", confidence="Low", detector_votes=({"p": "a"},)),
            make_finding(finding_id="f2", confidence="High", detector_votes=({"p": "b"},)),
        ]
        result = dedupe_findings(findings)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].confidence, "High")
        self.assertEqual(len(result[0].detector_votes), 2)

    def test_nested_same_mechanism_spans_collapse_to_one(self):
        findings = [
            make_finding(finding_id="f1", start_char=0, end_char=40, excerpt="x" * 40),
            make_finding(finding_id="f2", start_char=10, end_char=25, excerpt="y" * 15),
        ]
        self.assertEqual(len(dedupe_findings(findings)), 1)

    def test_partially_overlapping_same_mechanism_spans_both_survive(self):
        # Not nested -> genuinely two instances, must not be silently merged.
        findings = [
            make_finding(finding_id="f1", start_char=0, end_char=20, excerpt="a" * 20),
            make_finding(finding_id="f2", start_char=15, end_char=35, excerpt="b" * 20),
        ]
        self.assertEqual(len(dedupe_findings(findings)), 2)


class FindingInvariantTests(unittest.TestCase):
    def test_cross_document_mechanism_cannot_be_constructed(self):
        with self.assertRaises(ValueError):
            make_finding(mechanism_id="material_omission")

    def test_finding_requires_at_least_one_criterion(self):
        with self.assertRaises(ValueError):
            make_finding(triggered_criteria=())

    def test_inverted_span_cannot_be_constructed(self):
        with self.assertRaises(ValueError):
            make_finding(start_char=10, end_char=2)


class SchemaContractTests(unittest.TestCase):
    def test_required_fields_declared_for_every_core_object(self):
        for name in (
            "Passage", "Article", "Finding", "AnalysisRun", "DetectorFailure",
            "Claim", "ClaimAlignment", "EvidenceItem", "MaterialOmission",
            "ComparisonSet", "SourceDependency",
        ):
            self.assertTrue(vocab.object_required_fields(name), name)

    def test_finding_contract_forbids_plural_mechanisms(self):
        required = vocab.object_required_fields("Finding")
        self.assertIn("mechanismId", required)
        self.assertNotIn("mechanisms", required)

    def test_cross_document_mechanisms_exist_in_taxonomy(self):
        self.assertTrue(vocab.CROSS_DOCUMENT_MECHANISMS <= vocab.mechanism_ids())

    def test_intrinsic_slice_excludes_all_cross_document_mechanisms(self):
        self.assertFalse(vocab.INTRINSIC_ALPHA_SLICE & vocab.CROSS_DOCUMENT_MECHANISMS)

    def test_no_master_score_vocabulary_exists(self):
        forbidden = {"bias", "trust", "truth", "propaganda", "harm", "politicalLean", "leftRight"}
        properties = set(vocab._schema()["properties"])
        self.assertFalse(properties & forbidden)


if __name__ == "__main__":
    unittest.main()
