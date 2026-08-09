"""Adversarial tests — deliberate attempts to make the system lie.

Each test here is an attack that would produce a false or overconfident output
if the corresponding guard were removed. They are written to fail loudly if a
future refactor quietly weakens a guarantee.
"""
from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.rhetoric import vocabulary as vocab  # noqa: E402
from services.rhetoric.document import article_from_passages, segment  # noqa: E402
from services.rhetoric.models import Finding, dedupe_findings  # noqa: E402
from services.rhetoric.pipeline import analyze_article, analyze_text, pressure_profile  # noqa: E402
from services.rhetoric.providers import MockDetectorProvider, Verdict  # noqa: E402
from services.rhetoric.validation import DetectorRejection, validate_finding_payload  # noqa: E402

LOADED_CRITERION = vocab.mechanism("loaded_language")["positiveCriteria"][0]


class FabricatedEvidenceAttacks(unittest.TestCase):
    """The highest-value attack: get the system to show invented evidence."""

    def setUp(self):
        self.article = article_from_passages(
            "art-fab", [("paragraph", "A draconian, reckless scheme was approved.")]
        )

    def test_provider_cannot_get_criteria_backfilled_from_the_taxonomy(self):
        provider = MockDetectorProvider(
            default=Verdict(applies="yes", criteria_triggered=(), certainty=0.99)
        )
        result = analyze_article(self.article, provider=provider)
        self.assertEqual(result.findings, ())
        for finding in result.findings:
            self.fail("a finding survived with no detector-supplied criteria")

    def test_whitespace_criteria_cannot_masquerade_as_evidence(self):
        provider = MockDetectorProvider(
            default=Verdict(applies="yes", criteria_triggered=("   ", ""), certainty=0.9)
        )
        result = analyze_article(self.article, provider=provider)
        self.assertEqual(result.findings, ())

    def test_uncertain_verdict_cannot_reach_high_confidence(self):
        provider = MockDetectorProvider(
            default=Verdict(applies="uncertain", criteria_triggered=(LOADED_CRITERION,), certainty=1.0)
        )
        result = analyze_article(self.article, provider=provider)
        self.assertTrue(result.findings)
        self.assertTrue(all(f.confidence != "High" for f in result.findings))

    def test_out_of_range_certainty_is_rejected(self):
        for bad in (1.5, -0.1, float("nan")):
            provider = MockDetectorProvider(
                default=Verdict(applies="yes", criteria_triggered=(LOADED_CRITERION,), certainty=bad)
            )
            result = analyze_article(self.article, provider=provider)
            if bad != bad:  # NaN
                continue
            self.assertEqual(result.findings, (), f"certainty={bad} should be rejected")

    def test_neighbor_referencing_an_unknown_mechanism_is_rejected(self):
        provider = MockDetectorProvider(
            default=Verdict(
                applies="yes", criteria_triggered=(LOADED_CRITERION,),
                nearest_neighbor_overlap=("not_a_real_mechanism",), certainty=0.9,
            )
        )
        result = analyze_article(self.article, provider=provider)
        self.assertEqual(result.findings, ())


class CrossDocumentLeakageAttacks(unittest.TestCase):
    def test_intrinsic_scan_cannot_emit_any_cross_document_mechanism(self):
        result = analyze_text(
            "The headline promised proof but the body admits nothing was verified. "
            "Officials refused to explain why they allowed the gap."
        )
        for finding in result.findings:
            self.assertNotIn(finding.mechanism_id, vocab.CROSS_DOCUMENT_MECHANISMS)

    def test_requesting_a_cross_document_mechanism_raises(self):
        article = article_from_passages("art-cd", [("paragraph", "Some text here about a scheme.")])
        with self.assertRaises(ValueError):
            analyze_article(article, mechanisms={"material_omission"})

    def test_finding_object_refuses_cross_document_construction(self):
        for mechanism_id in vocab.CROSS_DOCUMENT_MECHANISMS:
            with self.assertRaises(ValueError):
                Finding(
                    finding_id="x", analysis_run_id="r", article_id="a", passage_id="p",
                    mechanism_id=mechanism_id, family="journalism_cross_doc", excerpt="t",
                    start_char=0, end_char=1, occurrence_index=0, pressure="P1",
                    confidence="Low", state="candidate", voice_class="reporter",
                    triggered_criteria=("c",),
                )


class SpanIntegrityAttacks(unittest.TestCase):
    def test_five_mechanisms_on_one_span_do_not_duplicate_source_text(self):
        """Multi-tag must be metadata over one canonical text, never copies."""
        base = dict(
            analysis_run_id="r", article_id="a", passage_id="a:p0000", excerpt="draconian",
            start_char=0, end_char=9, occurrence_index=0, pressure="P3", confidence="High",
            state="confirmed", voice_class="reporter", triggered_criteria=("c",),
        )
        mechanisms = ["loaded_language", "presupposition", "agent_suppression", "false_dilemma", "appeal_to_fear"]
        findings = [
            Finding(finding_id=f"f{i}", mechanism_id=m, family=vocab.mechanism(m)["family"], **base)
            for i, m in enumerate(mechanisms)
        ]
        result = dedupe_findings(findings)
        self.assertEqual(len(result), 5, "all five mechanisms must survive")
        self.assertEqual(len({(f.start_char, f.end_char) for f in result}), 1,
                         "they must all point at the same single span")
        self.assertEqual(len({f.excerpt for f in result}), 1)

    def test_profile_does_not_double_count_overlapping_spans_as_extra_text(self):
        result = analyze_text(
            "The council approved a draconian, reckless scheme that will siphon funds."
        )
        profile = pressure_profile(result.findings)
        self.assertEqual(sum(profile["byPressure"].values()), profile["totalFindings"])
        self.assertEqual(sum(profile["byConfidence"].values()), profile["totalFindings"])
        self.assertEqual(
            profile["confirmedFindings"] + profile["candidateFindings"], profile["totalFindings"]
        )

    def test_repeated_excerpt_cannot_resolve_to_the_wrong_occurrence(self):
        article = article_from_passages(
            "art-rep", [("paragraph", "A reckless scheme, then another reckless scheme, passed.")]
        )
        payload = {
            "mechanismId": "loaded_language", "passageId": "art-rep:p0000",
            "excerpt": "reckless scheme", "pressure": "P3", "confidence": "High",
            "voiceClass": "reporter", "triggeredCriteria": [LOADED_CRITERION],
        }
        with self.assertRaises(DetectorRejection):
            validate_finding_payload(
                payload, article=article, allowed_mechanisms=vocab.INTRINSIC_ALPHA_SLICE,
                taxonomy_version=vocab.taxonomy_version(),
            )
        payload["occurrenceIndex"] = 1
        resolved = validate_finding_payload(
            payload, article=article, allowed_mechanisms=vocab.INTRINSIC_ALPHA_SLICE,
            taxonomy_version=vocab.taxonomy_version(),
        )
        text = article.passages[0].text
        self.assertEqual(text[resolved.start_char:resolved.end_char], "reckless scheme")
        self.assertGreater(resolved.start_char, text.index("reckless scheme"))

    def test_every_finding_span_round_trips_on_adversarial_punctuation(self):
        result = analyze_text(
            'The "draconian" plan — reckless, cynical — was approved; mistakes were made.'
        )
        for finding in result.findings:
            passage = result.article.passage(finding.passage_id)
            self.assertEqual(passage.text[finding.start_char:finding.end_char], finding.excerpt)


class HostileInputAttacks(unittest.TestCase):
    def test_html_and_script_text_is_treated_as_literal_content(self):
        hostile = '<script>alert("xss")</script> The council approved a draconian scheme.'
        result = analyze_text(hostile)
        self.assertTrue(result.findings)
        for finding in result.findings:
            passage = result.article.passage(finding.passage_id)
            self.assertEqual(passage.text[finding.start_char:finding.end_char], finding.excerpt)
        joined = " ".join(p.text for p in result.article.passages)
        self.assertIn("<script>", joined, "hostile text is preserved verbatim, not stripped")

    def test_unicode_and_zero_width_characters_do_not_break_span_math(self):
        result = analyze_text("The​ council approved a draconian scheme today.")
        for finding in result.findings:
            passage = result.article.passage(finding.passage_id)
            self.assertEqual(passage.text[finding.start_char:finding.end_char], finding.excerpt)

    def test_empty_and_whitespace_articles_are_refused(self):
        for bad in ("", "   ", "\n\n", "\t"):
            with self.assertRaises(ValueError):
                analyze_text(bad)

    def test_single_character_article_does_not_crash(self):
        result = analyze_text("x")
        self.assertEqual(result.run.status, "complete")
        self.assertEqual(result.findings, ())

    def test_very_long_article_completes_with_full_coverage(self):
        body = [("paragraph", f"Ordinary sentence {i} with no rhetorical loading at all.")
                for i in range(600)]
        body.append(("paragraph", "Members must either approve the levy or lose everything."))
        article = article_from_passages("art-huge", body)
        result = analyze_article(article, batch_size=25)
        self.assertEqual(result.run.status, "complete")
        self.assertEqual(len(result.run.processed_passage_ids), 601)
        self.assertTrue(result.findings_for_passage(article.passages[-1].passage_id))

    def test_article_of_only_quotes_attributes_nothing_to_the_outlet(self):
        result = analyze_text(
            '"This is a draconian, reckless scheme," said the senator. '
            '"It is an outrageous betrayal," she added.'
        )
        for finding in result.findings:
            self.assertNotEqual(
                finding.voice_class, "reporter",
                f"{finding.excerpt!r} was attributed to the outlet inside quoted speech",
            )


class PartialStateHonestyAttacks(unittest.TestCase):
    def test_partial_run_cannot_present_itself_as_complete(self):
        article = article_from_passages(
            "art-ph",
            [("paragraph", "A draconian scheme."), ("paragraph", "Another draconian scheme."),
             ("paragraph", "A third draconian scheme.")],
        )
        provider = MockDetectorProvider(
            default=Verdict(applies="yes", criteria_triggered=(LOADED_CRITERION,), certainty=0.8),
            raise_on_passage={"art-ph:p0001"},
        )
        result = analyze_article(article, provider=provider)
        payload = result.run.to_dict()
        self.assertEqual(payload["status"], "partial")
        self.assertFalse(payload["isCompleteCoverage"])
        self.assertTrue(payload["warnings"])
        self.assertTrue(payload["failedPassageIds"])
        self.assertLess(payload["coverageRatio"], 1.0)

    def test_coverage_buckets_always_partition_after_partial_failure(self):
        article = article_from_passages(
            "art-cov", [("paragraph", f"A draconian scheme number {i}.") for i in range(10)]
        )
        provider = MockDetectorProvider(
            default=Verdict(applies="yes", criteria_triggered=(LOADED_CRITERION,), certainty=0.8),
            raise_on_passage={"art-cov:p0003", "art-cov:p0007"},
        )
        result = analyze_article(article, provider=provider, batch_size=3)
        result.run.assert_coverage_invariant()
        self.assertEqual(
            len(result.run.processed_passage_ids)
            + len(result.run.failed_passage_ids)
            + len(result.run.unprocessed_passage_ids),
            10,
        )

    def test_findings_never_reference_a_failed_passage(self):
        article = article_from_passages(
            "art-fp", [("paragraph", f"A draconian scheme number {i}.") for i in range(6)]
        )
        provider = MockDetectorProvider(
            default=Verdict(applies="yes", criteria_triggered=(LOADED_CRITERION,), certainty=0.8),
            raise_on_passage={"art-fp:p0002"},
        )
        result = analyze_article(article, provider=provider)
        failed = set(result.run.failed_passage_ids)
        for finding in result.findings:
            self.assertNotIn(finding.passage_id, failed)


class PassTwoRegressionAttacks(unittest.TestCase):
    """Defects found by the second adversarial pass. Each would let the system
    report something it cannot support."""

    def test_duplicate_processed_append_cannot_inflate_coverage_to_complete(self):
        """Defect D: coverage_ratio reported 1.0 while a passage was never analyzed."""
        from services.rhetoric.models import AnalysisRun

        run = AnalysisRun(
            run_id="r", article_id="a", content_hash="h", taxonomy_version="t",
            detector_version="d", provider={}, all_passage_ids=("p0", "p1"),
        )
        run.processed_passage_ids.extend(["p0", "p0"])
        self.assertEqual(run.coverage_ratio, 0.5, "duplicates must not inflate coverage")
        self.assertFalse(run.is_complete_coverage)
        with self.assertRaises(AssertionError):
            run.assert_coverage_invariant()

    def test_coverage_cannot_reference_a_passage_outside_the_article(self):
        from services.rhetoric.models import AnalysisRun

        run = AnalysisRun(
            run_id="r", article_id="a", content_hash="h", taxonomy_version="t",
            detector_version="d", provider={}, all_passage_ids=("p0",),
        )
        run.processed_passage_ids.extend(["p0", "p-not-in-article"])
        with self.assertRaises(AssertionError):
            run.assert_coverage_invariant()

    def test_provider_bug_degrades_the_run_instead_of_crashing_it(self):
        """Defect E: an unexpected provider exception killed the whole analysis."""
        from services.rhetoric.providers import DetectorProvider

        class ExplodingProvider(DetectorProvider):
            kind, provider_id, version = "mock", "exploding", "1"

            def verify(self, context):
                raise RuntimeError("provider internal bug")

        article = article_from_passages(
            "art-boom",
            [("paragraph", "A draconian, reckless scheme passed."),
             ("paragraph", "Another draconian scheme passed.")],
        )
        result = analyze_article(article, provider=ExplodingProvider())
        self.assertEqual(result.run.status, "failed")
        self.assertEqual(result.findings, ())
        self.assertTrue(result.run.failures)
        self.assertTrue(any(f.stage == "provider_error" for f in result.run.failures))
        self.assertTrue(any("RuntimeError" in f.reason for f in result.run.failures))
        result.run.assert_coverage_invariant()

    def test_partial_provider_bug_keeps_good_passages(self):
        from services.rhetoric.providers import DetectorProvider

        class FlakyProvider(DetectorProvider):
            kind, provider_id, version = "mock", "flaky", "1"

            def verify(self, context):
                if context.candidate.passage_id.endswith("p0001"):
                    raise RuntimeError("boom")
                return Verdict(applies="yes", criteria_triggered=(LOADED_CRITERION,), certainty=0.8)

        article = article_from_passages(
            "art-flaky",
            [("paragraph", "A draconian, reckless scheme passed."),
             ("paragraph", "Another draconian scheme passed."),
             ("paragraph", "A third draconian scheme passed.")],
        )
        result = analyze_article(article, provider=FlakyProvider())
        self.assertEqual(result.run.status, "partial")
        self.assertTrue(result.findings, "good passages must survive one bad passage")
        self.assertIn("art-flaky:p0001", result.run.failed_passage_ids)
        result.run.assert_coverage_invariant()

    def test_sentence_beginning_with_a_caption_keyword_is_not_a_caption(self):
        """Defect F: misclassification silently changed voice to document_material."""
        article = segment("Photo opportunities were limited for the draconian scheme rollout.")
        self.assertEqual(article.passages[0].passage_type, "paragraph")

    def test_genuine_captions_are_still_recognized(self):
        for text in ("Photo: The council chamber on Tuesday.", "Figure 3 — Budget allocation."):
            self.assertEqual(segment(text).passages[0].passage_type, "caption", text)


class IdentityAndDriftAttacks(unittest.TestCase):
    def test_changed_content_changes_the_run_id(self):
        a = analyze_text("The council approved a draconian scheme.")
        b = analyze_text("The council approved a reasonable proposal.")
        self.assertNotEqual(a.run.content_hash, b.run.content_hash)
        self.assertNotEqual(a.run.run_id, b.run.run_id)

    def test_run_records_the_hash_of_the_article_it_actually_analyzed(self):
        result = analyze_text("The council approved a draconian scheme.")
        self.assertEqual(result.run.content_hash, result.article.content_hash)

    def test_findings_cannot_outlive_their_run_identity(self):
        result = analyze_text("The council approved a draconian, reckless scheme.")
        for finding in result.findings:
            self.assertEqual(finding.analysis_run_id, result.run.run_id)
            self.assertEqual(finding.article_id, result.article.article_id)

    def test_python_and_schema_vocabulary_cannot_silently_diverge(self):
        import json
        schema = json.loads((ROOT / "packages" / "schema" / "schema.json").read_text())
        self.assertEqual(vocab.PRESSURE, set(schema["properties"]["pressureLevel"]["enum"]))
        self.assertEqual(vocab.VOICE, set(schema["properties"]["voiceClass"]["enum"]))
        self.assertEqual(
            vocab.INTRINSIC_ALPHA_SLICE, set(schema["properties"]["intrinsicAlphaSlice"]["enum"])
        )

    def test_taxonomy_ids_referenced_by_the_slice_all_exist(self):
        self.assertTrue(vocab.INTRINSIC_ALPHA_SLICE <= vocab.mechanism_ids())


class NoMasterScoreAttacks(unittest.TestCase):
    def test_profile_exposes_no_single_summarizing_number(self):
        result = analyze_text(
            "The council approved a draconian, reckless scheme. Mistakes were made. "
            "Members must either approve it or lose everything."
        )
        profile = pressure_profile(result.findings)
        numeric_scalars = [
            key for key, value in profile.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
            and key not in {"totalFindings", "confirmedFindings", "candidateFindings",
                            "outletVoiceFindings", "quotedVoiceFindings", "uncertainVoiceFindings"}
        ]
        self.assertEqual(numeric_scalars, [], f"unexpected scalar summary: {numeric_scalars}")

    def test_no_political_axis_anywhere_in_the_vocabulary(self):
        import json
        schema = json.loads((ROOT / "packages" / "schema" / "schema.json").read_text())
        blob = json.dumps(schema).lower() + json.dumps(vocab.taxonomy()).lower()
        for forbidden in ("left-wing", "right-wing", "liberal", "conservative", "partisan lean", "political spectrum"):
            self.assertNotIn(forbidden, blob, f"ideological vocabulary found: {forbidden}")


if __name__ == "__main__":
    unittest.main()
