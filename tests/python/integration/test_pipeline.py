"""Integration tests: full Level 3 detector pipeline."""
from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.rhetoric import vocabulary as vocab  # noqa: E402
from services.rhetoric.document import article_from_passages, segment  # noqa: E402
from services.rhetoric.pipeline import (  # noqa: E402
    DETECTOR_VERSION,
    analyze_article,
    analyze_text,
    pressure_profile,
)
from services.rhetoric.providers import (  # noqa: E402
    HeuristicDetectorProvider,
    MockDetectorProvider,
    ModelDetectorProvider,
    ProviderUnavailable,
    Verdict,
)

ARTICLE = """Draconian Housing Scheme Advances

The council approved a draconian, reckless scheme on Tuesday that will siphon funds from repairs.

Officials refused to explain why they allowed the backlog to grow. Mistakes were made during the review.

Members must either approve the levy or watch the district collapse entirely.

The audit was published by the finance office after a Category 4 storm.

"This is an outrageous betrayal," said tenant representative Dana Whitfield.
"""


class EndToEndTests(unittest.TestCase):
    def setUp(self):
        self.result = analyze_text(ARTICLE, started_at="t0", completed_at="t1")

    def test_run_is_complete_and_coverage_is_total(self):
        self.assertEqual(self.result.run.status, "complete")
        self.assertTrue(self.result.run.is_complete_coverage)
        self.assertEqual(self.result.run.coverage_ratio, 1.0)
        self.result.run.assert_coverage_invariant()

    def test_all_four_mechanisms_fire_on_representative_text(self):
        found = {f.mechanism_id for f in self.result.findings}
        self.assertEqual(found, set(vocab.INTRINSIC_ALPHA_SLICE), f"got {found}")

    def test_every_finding_round_trips_to_its_exact_span(self):
        for finding in self.result.findings:
            passage = self.result.article.passage(finding.passage_id)
            self.assertEqual(
                passage.text[finding.start_char:finding.end_char],
                finding.excerpt,
                finding.finding_id,
            )

    def test_every_finding_references_the_run_and_carries_versions(self):
        for finding in self.result.findings:
            self.assertEqual(finding.analysis_run_id, self.result.run.run_id)
            self.assertEqual(finding.taxonomy_version, vocab.taxonomy_version())
            self.assertEqual(finding.detector_version, DETECTOR_VERSION)

    def test_every_finding_carries_detector_votes_and_factor_traces(self):
        for finding in self.result.findings:
            self.assertTrue(finding.detector_votes, finding.finding_id)
            self.assertTrue(finding.pressure_factors, finding.finding_id)
            self.assertTrue(finding.confidence_factors, finding.finding_id)
            self.assertTrue(finding.triggered_criteria, finding.finding_id)

    def test_triggered_criteria_come_from_the_taxonomy_record(self):
        """Criteria must be real taxonomy text, not free-form invention."""
        for finding in self.result.findings:
            record = vocab.mechanism(finding.mechanism_id)
            allowed = set(record["positiveCriteria"])
            for criterion in finding.triggered_criteria:
                self.assertIn(criterion, allowed, f"{finding.mechanism_id}: {criterion!r}")

    def test_quoted_rhetoric_is_not_attributed_to_the_outlet(self):
        quoted = [f for f in self.result.findings if "outrageous" in f.excerpt]
        self.assertTrue(quoted, "expected a finding on the quoted material")
        for finding in quoted:
            self.assertEqual(finding.voice_class, "quoted_speaker")

    def test_by_agent_clause_is_not_flagged_as_agent_suppression(self):
        suppression = [f for f in self.result.findings if f.mechanism_id == "agent_suppression"]
        self.assertFalse(
            [f for f in suppression if "published" in f.excerpt],
            "'was published by the finance office' names its actor",
        )

    def test_canonical_agentless_passive_is_caught(self):
        """Regression: the taxonomy's own example, missed by ed/en-only matching."""
        suppression = [f for f in self.result.findings if f.mechanism_id == "agent_suppression"]
        self.assertTrue(
            any("were made" in f.excerpt for f in suppression),
            f"'Mistakes were made' must be detected; got {[f.excerpt for f in suppression]}",
        )

    def test_no_material_omission_from_intrinsic_scan(self):
        for finding in self.result.findings:
            self.assertNotIn(finding.mechanism_id, vocab.CROSS_DOCUMENT_MECHANISMS)

    def test_profile_is_decomposable_and_has_no_master_score(self):
        profile = pressure_profile(self.result.findings)
        self.assertEqual(
            sum(profile["byPressure"].values()), profile["totalFindings"]
        )
        for forbidden in ("biasScore", "trustScore", "truthScore", "propagandaScore", "harmScore", "overall"):
            self.assertNotIn(forbidden, profile)

    def test_analysis_is_deterministic_for_identical_input(self):
        again = analyze_text(ARTICLE, started_at="t0", completed_at="t1")
        self.assertEqual(self.result.run.run_id, again.run.run_id)
        self.assertEqual(
            [f.finding_id for f in self.result.findings],
            [f.finding_id for f in again.findings],
        )


class SentenceBoundaryRegressionTests(unittest.TestCase):
    def test_by_agent_in_a_later_sentence_does_not_suppress_this_one(self):
        """Regression for the cross-sentence exclusion-window defect."""
        result = analyze_text(
            "Mistakes were made during the review. The report was published by the department."
        )
        suppression = [f for f in result.findings if f.mechanism_id == "agent_suppression"]
        self.assertEqual(len(suppression), 1)
        self.assertIn("were made", suppression[0].excerpt)


class LongDocumentTests(unittest.TestCase):
    def _long_article(self, paragraphs=120):
        body = [("paragraph", f"Routine sentence number {i} about ordinary municipal process.")
                for i in range(paragraphs)]
        # A known mechanism at the very end, to prove tail coverage.
        body.append(("paragraph", "Members must either approve the levy or lose everything."))
        return article_from_passages("art-long", body)

    def test_mechanism_at_end_of_long_document_is_still_found(self):
        article = self._long_article()
        result = analyze_article(article, batch_size=25)
        last_passage = article.passages[-1].passage_id
        tail = result.findings_for_passage(last_passage)
        self.assertTrue(tail, "a mechanism in the final passage must not be lost to batching")
        self.assertEqual(result.run.status, "complete")

    def test_batching_covers_every_passage_exactly_once(self):
        article = self._long_article(80)
        result = analyze_article(article, batch_size=17)
        batched = [pid for batch in result.run.batches for pid in batch["passageIds"]]
        self.assertEqual(batched, list(article.passage_ids))
        self.assertEqual(len(batched), len(set(batched)))

    def test_batch_size_does_not_change_findings(self):
        article = self._long_article(40)
        small = analyze_article(article, batch_size=3)
        large = analyze_article(article, batch_size=1000)
        self.assertEqual(
            [f.span_key for f in small.findings], [f.span_key for f in large.findings]
        )


class PartialFailureTests(unittest.TestCase):
    def test_provider_failure_on_one_passage_yields_partial_not_complete(self):
        article = article_from_passages(
            "art-pf",
            [
                ("paragraph", "The council approved a draconian, reckless scheme."),
                ("paragraph", "Members must either approve the levy or watch it collapse."),
                ("paragraph", "Officials refused to explain why they allowed the delay."),
            ],
        )
        failing = MockDetectorProvider(
            default=Verdict(applies="yes", criteria_triggered=("Contains strongly evaluative adjectives or verbs with heavy emotional connotation.",), certainty=0.8),
            raise_on_passage={"art-pf:p0001"},
        )
        result = analyze_article(article, provider=failing)

        self.assertEqual(result.run.status, "partial")
        self.assertFalse(result.run.is_complete_coverage)
        self.assertIn("art-pf:p0001", result.run.failed_passage_ids)
        self.assertTrue(result.run.failures)
        self.assertTrue(result.run.warnings, "partial coverage must warn")
        # Findings from the successful passages are retained, not discarded.
        self.assertTrue(result.findings)
        self.assertFalse(result.findings_for_passage("art-pf:p0001"))
        result.run.assert_coverage_invariant()

    def test_total_provider_failure_yields_failed_and_no_findings(self):
        article = article_from_passages("art-tf", [("paragraph", "A draconian, reckless scheme.")])
        provider = MockDetectorProvider(raise_on_passage={"art-tf:p0000"})
        result = analyze_article(article, provider=provider)
        self.assertEqual(result.run.status, "failed")
        self.assertEqual(result.findings, ())

    def test_partial_run_never_reports_complete_coverage(self):
        article = article_from_passages(
            "art-pc",
            [("paragraph", "A draconian scheme."), ("paragraph", "Another draconian scheme.")],
        )
        provider = MockDetectorProvider(raise_on_passage={"art-pc:p0001"})
        result = analyze_article(article, provider=provider)
        payload = result.run.to_dict()
        self.assertFalse(payload["isCompleteCoverage"])
        self.assertNotEqual(payload["status"], "complete")
        self.assertLess(payload["coverageRatio"], 1.0)


class ProviderBoundaryTests(unittest.TestCase):
    def test_model_provider_without_credentials_refuses_rather_than_inventing(self):
        provider = ModelDetectorProvider(api_key=None, transport=None)
        self.assertFalse(provider.available())
        article = article_from_passages("art-mp", [("paragraph", "A draconian, reckless scheme.")])
        result = analyze_article(article, provider=provider)
        self.assertEqual(result.run.status, "failed")
        self.assertEqual(result.findings, ())
        self.assertTrue(
            any("unavailable" in f.reason for f in result.run.failures),
            "missing credentials must surface as an explicit failure",
        )

    def test_model_provider_builds_a_bounded_prompt(self):
        from services.rhetoric import candidates as candidates_module
        from services.rhetoric import context as context_module

        article = article_from_passages("art-pr", [("paragraph", "A draconian, reckless scheme passed.")])
        passage = article.passages[0]
        candidate = candidates_module.generate(passage, {"loaded_language"})[0]
        ctx = context_module.assemble(article, passage, candidate)

        prompt = ModelDetectorProvider().build_prompt(ctx)
        self.assertEqual(prompt["mechanism"]["id"], "loaded_language")
        self.assertIn("exactText", prompt["span"])
        self.assertIn("responseSchema", prompt)
        self.assertEqual(prompt["taxonomyVersion"], vocab.taxonomy_version())

    def test_model_response_parsing_rejects_malformed_payloads(self):
        provider = ModelDetectorProvider()
        good = provider.parse_response(
            {"applies": "yes", "criteriaTriggered": ["c"], "criteriaFailed": [], "certainty": 0.8}
        )
        self.assertEqual(good.applies, "yes")
        for bad in (
            {"criteriaTriggered": [], "criteriaFailed": [], "certainty": 0.5},
            {"applies": "yes", "criteriaTriggered": [], "criteriaFailed": [], "certainty": 2.0},
            {"applies": "yes", "criteriaTriggered": [], "criteriaFailed": [], "certainty": "high"},
            "not json at all",
        ):
            with self.assertRaises(ValueError):
                provider.parse_response(bad)

    def test_swapping_providers_does_not_widen_what_is_accepted(self):
        """A permissive provider must not bypass validation."""
        article = article_from_passages("art-sw", [("paragraph", "A draconian, reckless scheme passed.")])
        sloppy = MockDetectorProvider(
            default=Verdict(applies="yes", criteria_triggered=(), certainty=0.99)
        )
        result = analyze_article(article, provider=sloppy)
        self.assertEqual(result.findings, (), "verdict with no criteria must yield no findings")
        self.assertTrue(result.run.rejected_candidate_count > 0)
        self.assertTrue(any("criteriaTriggered" in f.reason for f in result.run.failures))


class UncertaintyPropagationTests(unittest.TestCase):
    def test_uncertain_verdict_is_capped_below_high_confidence(self):
        article = article_from_passages("art-un", [("paragraph", "A draconian, reckless scheme passed.")])
        provider = MockDetectorProvider(
            default=Verdict(
                applies="uncertain",
                criteria_triggered=("Contains strongly evaluative adjectives or verbs with heavy emotional connotation.",),
                certainty=0.99,
            )
        )
        result = analyze_article(article, provider=provider)
        self.assertTrue(result.findings)
        for finding in result.findings:
            self.assertNotEqual(finding.confidence, "High")
            self.assertTrue(
                any("uncertain" in factor for factor in finding.confidence_factors)
            )

    def test_uncertain_verdict_records_an_alternate_interpretation(self):
        article = article_from_passages("art-ua", [("paragraph", "A draconian, reckless scheme passed.")])
        provider = MockDetectorProvider(
            default=Verdict(
                applies="uncertain",
                criteria_triggered=("Contains strongly evaluative adjectives or verbs with heavy emotional connotation.",),
                criteria_failed=("Standard technical or legal terms with precise definitions.",),
                certainty=0.5,
            )
        )
        result = analyze_article(article, provider=provider)
        self.assertTrue(all(f.alternate_interpretation for f in result.findings))

    def test_no_alternate_interpretation_is_invented_when_none_exists(self):
        article = article_from_passages("art-na", [("paragraph", "A draconian, reckless scheme passed.")])
        provider = MockDetectorProvider(
            default=Verdict(
                applies="yes",
                criteria_triggered=("Contains strongly evaluative adjectives or verbs with heavy emotional connotation.",),
                certainty=0.9,
            )
        )
        result = analyze_article(article, provider=provider)
        self.assertTrue(result.findings)
        self.assertTrue(all(f.alternate_interpretation is None for f in result.findings))


if __name__ == "__main__":
    unittest.main()
