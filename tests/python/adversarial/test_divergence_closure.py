"""Closure regressions for independent pre-merge review findings.

M-01 is the merge blocker: `align_pair` could classify factually contradictory
claims as `compatible`, and `compatible` was sufficient to satisfy the Material
Omission presence gate — letting the system emit an omission asserting a
proposition its own supporting sources contradicted.

The governing rule these tests enforce: unresolved contradiction may never be
converted into evidentiary support. Fail closed.
"""
from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.comparison import (  # noqa: E402
    Claim,
    ComparisonSet,
    SourceAssertion,
    SourceDependency,
    align_pair,
)
from services.comparison.divergence import detect_divergence  # noqa: E402
from services.comparison.omission import (  # noqa: E402
    OmissionRejection,
    evaluate_candidate_omission,
)
from services.rhetoric import analyze_text  # noqa: E402
from services.rhetoric.document import segment  # noqa: E402


def _assertion(source_id="s", article="art-x"):
    return SourceAssertion(source_id, source_id.title(), article, f"{article}:p0000", "excerpt")


def claim(claim_id: str, proposition: str, source_id="s", article="art-x") -> Claim:
    return Claim(
        claim_id=claim_id,
        normalized_proposition=proposition,
        source_assertions=(_assertion(source_id, article),),
    )


class DivergenceDetectionTests(unittest.TestCase):
    """The bounded, inspectable conflict checks themselves."""

    def _kinds(self, a: str, b: str) -> set[str]:
        return {d.kind for d in detect_divergence(a, b)}

    def test_percent_conflict_detected(self):
        self.assertIn("numeric", self._kinds("spending rose 12 percent", "spending rose 40 percent"))

    def test_percent_formatting_variants_are_equivalent(self):
        self.assertNotIn("numeric", self._kinds("spending rose 12 percent", "spending rose 12%"))

    def test_thousands_separator_is_equivalent(self):
        self.assertNotIn("numeric", self._kinds("1,000 residents applied", "1000 residents applied"))

    def test_currency_scale_conflict_detected(self):
        self.assertIn("numeric", self._kinds("the fund holds $2 million", "the fund holds $20 million"))

    def test_currency_scale_expansion_is_equivalent(self):
        self.assertNotIn("numeric", self._kinds("the fund holds $2 million", "the fund holds $2,000,000"))

    def test_clock_time_conflict_detected(self):
        self.assertIn("numeric", self._kinds("the vote closes at 5 p.m.", "the vote closes at 8 p.m."))

    def test_weekday_conflict_detected(self):
        self.assertIn("temporal", self._kinds("the hearing is Tuesday", "the hearing is Thursday"))

    def test_same_weekday_is_not_a_conflict(self):
        self.assertNotIn("temporal", self._kinds("the hearing is Tuesday", "the hearing is on Tuesday"))

    def test_calendar_date_conflict_detected(self):
        self.assertIn("temporal", self._kinds("filed on March 3", "filed on March 5"))

    def test_year_conflict_detected(self):
        self.assertIn("temporal", self._kinds("the rule takes effect in 2024", "the rule takes effect in 2025"))

    def test_polarity_pairs_detected(self):
        for a, b in (
            ("the policy will help residents", "the policy will harm residents"),
            ("the budget will increase next year", "the budget will decrease next year"),
            ("the council approved the plan", "the council rejected the plan"),
            ("the rule allows inspections", "the rule prohibits inspections"),
            ("the group supports the measure", "the group opposes the measure"),
        ):
            self.assertIn("polarity", self._kinds(a, b), f"{a!r} vs {b!r}")

    def test_negation_still_detected(self):
        self.assertIn("negation", self._kinds("regulators require a warrant", "regulators do not require a warrant"))

    def test_no_divergence_on_ordinary_rewording(self):
        self.assertEqual(
            self._kinds(
                "the council approved the housing budget on Tuesday",
                "the council approved the housing budget Tuesday",
            ),
            set(),
        )

    def test_one_sided_detail_is_not_a_conflict(self):
        # One claim stating a figure the other omits is missing detail, not
        # contradiction, and must not be flagged as divergence.
        self.assertNotIn("numeric", self._kinds("spending rose", "spending rose 12 percent"))


class AlignmentClosureTests(unittest.TestCase):
    """High-overlap conflicts must never read as agreement."""

    def _align(self, a: str, b: str):
        return align_pair(claim("a", a), claim("b", b))

    def test_numeric_conflict_is_not_usable_and_not_compatible(self):
        al = self._align("city spending rose 12 percent last year", "city spending rose 40 percent last year")
        self.assertNotIn(al.relation, {"compatible", "same_proposition", "more_specific", "less_specific"})
        self.assertFalse(al.is_usable_for_omission)
        self.assertEqual(al.confidence, "Low")
        self.assertTrue(al.divergences)

    def test_antonym_conflict_is_not_usable(self):
        al = self._align("the policy will help residents", "the policy will harm residents")
        self.assertFalse(al.is_usable_for_omission)
        self.assertNotEqual(al.relation, "compatible")

    def test_direction_conflict_is_not_usable(self):
        al = self._align("the budget will increase sharply", "the budget will decrease sharply")
        self.assertFalse(al.is_usable_for_omission)

    def test_approval_conflict_is_not_usable(self):
        al = self._align("the council approved the housing plan", "the council rejected the housing plan")
        self.assertFalse(al.is_usable_for_omission)

    def test_permission_conflict_is_not_usable(self):
        al = self._align("the statute allows warrantless inspection", "the statute prohibits warrantless inspection")
        self.assertFalse(al.is_usable_for_omission)

    def test_date_conflict_is_not_usable(self):
        al = self._align("the hearing is scheduled for Tuesday", "the hearing is scheduled for Thursday")
        self.assertFalse(al.is_usable_for_omission)

    def test_explicit_negation_remains_contradictory(self):
        al = self._align("regulators require a judicial warrant", "regulators do not require a judicial warrant")
        self.assertEqual(al.relation, "contradictory")
        self.assertFalse(al.is_usable_for_omission)

    def test_numeric_formatting_equivalence_still_aligns(self):
        al = self._align("city spending rose 12 percent last year", "city spending rose 12% last year")
        self.assertEqual(al.relation, "same_proposition")
        self.assertTrue(al.is_usable_for_omission)

    def test_identical_claims_still_align_and_remain_usable(self):
        text = "section 4b requires a magistrate-issued judicial warrant"
        al = self._align(text, text)
        self.assertEqual(al.relation, "same_proposition")
        self.assertTrue(al.is_usable_for_omission)

    def test_specificity_relations_are_not_usable_for_omission(self):
        # Token-count specificity is not an entailment check; excluded until one exists.
        al = self._align(
            "the council approved the budget on Tuesday by seven votes",
            "the council approved the budget",
        )
        self.assertIn(al.relation, {"more_specific", "less_specific", "compatible", "uncertain"})
        self.assertFalse(al.is_usable_for_omission)

    def test_ordinary_compatible_wording_without_conflict_is_still_not_omission_grounds(self):
        al = self._align(
            "the council approved the housing budget after debate",
            "the council approved the housing budget following debate",
        )
        self.assertFalse(
            al.is_usable_for_omission and al.relation != "same_proposition",
            "only same_proposition may ground an omission",
        )

    def test_equivalent_value_written_differently_is_now_recognized(self):
        """Superseded by the M-01 identity gate — and improved.

        Previously this pair was an accepted conservative FALSE NEGATIVE: same
        fact, no divergence, but token overlap fell below the old 0.80
        `same_proposition` threshold. Canonical numeric normalization now makes
        `$2 million` and `$2,000,000` normalize to the same proposition, so the
        pair is correctly recognized as identical rather than merely refused.
        """
        al = self._align("the fund holds $2 million", "the fund holds $2,000,000")
        self.assertEqual(al.divergences, (), "no conflict should be detected")
        self.assertEqual(al.relation, "same_proposition")
        self.assertTrue(al.is_usable_for_omission)

    def test_unrelated_claims_remain_unrelated(self):
        al = self._align("the council approved the housing budget", "ticket prices rose at the stadium")
        self.assertEqual(al.relation, "unrelated")
        self.assertFalse(al.is_usable_for_omission)


class FalseOmissionClosureTests(unittest.TestCase):
    """The exact reproduction from the independent review. Mandatory."""

    TARGET = [claim("ct", "the stadium roof was repaired in autumn", "sentinel", "art-sn")]

    def _comparison_set(self):
        # Post-hardening: membership mapping (M-03) and CONFIRMED independence
        # (M-02) are both required before an omission can be grounded.
        return ComparisonSet(
            "cs-1", "art-sn", ("art-tw", "art-pj"), "retrieved",
            source_of_article={"art-tw": "techwire", "art-pj": "policy"},
            dependencies=(SourceDependency(("techwire", "policy"), "independent_reporting", "High"),),
        )

    def _evaluate(self, candidate: str, peer: str, dimension="Scale"):
        return evaluate_candidate_omission(
            comparison_set=self._comparison_set(),
            candidate_proposition=candidate,
            supporting_claims=[
                claim("c1", peer, "techwire", "art-tw"),
                claim("c2", peer, "policy", "art-pj"),
            ],
            target_claims=self.TARGET,
            dimension=dimension,
            target_published_at="2026-07-12T10:00:00Z",
            knowable_at="2026-07-10T09:00:00Z",
            rationale="peer sources report this",
        )

    def test_numeric_conflict_cannot_produce_a_material_omission(self):
        """MANDATORY: peers say 12 percent; candidate asserts 40 percent."""
        with self.assertRaises(OmissionRejection) as ctx:
            self._evaluate(
                "city spending rose 40 percent last year",
                "city spending rose 12 percent last year",
            )
        self.assertEqual(ctx.exception.gate, "presence_elsewhere")
        self.assertIn("diverge", ctx.exception.reason)

    def test_antonym_conflict_cannot_produce_a_material_omission(self):
        with self.assertRaises(OmissionRejection) as ctx:
            self._evaluate(
                "the policy will harm local residents",
                "the policy will help local residents",
                dimension="Cause",
            )
        self.assertEqual(ctx.exception.gate, "presence_elsewhere")

    def test_date_conflict_cannot_produce_a_material_omission(self):
        with self.assertRaises(OmissionRejection) as ctx:
            self._evaluate(
                "the hearing is scheduled for Thursday",
                "the hearing is scheduled for Tuesday",
                dimension="Timeline",
            )
        self.assertEqual(ctx.exception.gate, "presence_elsewhere")

    def test_no_source_is_ever_credited_with_a_claim_it_did_not_make(self):
        """Nothing may attribute '40 percent' to sources that said '12 percent'."""
        try:
            omission = self._evaluate(
                "city spending rose 40 percent last year",
                "city spending rose 12 percent last year",
            )
        except OmissionRejection:
            return  # correct: nothing emitted, nothing attributed
        self.fail(
            f"omission emitted crediting {list(omission.supporting_source_ids)} with "
            f"{omission.missing_proposition!r}, which they did not assert"
        )

    def test_genuine_omission_is_still_accepted(self):
        """The fix must not close the gate on legitimate omissions."""
        warrant = "Section 4b requires a magistrate-issued judicial warrant before content inspection"
        omission = self._evaluate(warrant, warrant, dimension="Responsibility")
        self.assertEqual(omission.missing_proposition, warrant)
        self.assertGreaterEqual(len(omission.supporting_source_ids), 2)
        self.assertTrue(omission.grounding_alignments)
        for alignment in omission.grounding_alignments:
            self.assertFalse(alignment.divergences)
            self.assertTrue(alignment.is_usable_for_omission)


class AgentSuppressionByAgentClosureTests(unittest.TestCase):
    """N-03: temporal/duration `by` must not read as a named agent."""

    def _suppression(self, text: str) -> list[str]:
        return [f.excerpt for f in analyze_text(text).findings if f.mechanism_id == "agent_suppression"]

    def test_temporal_and_measurement_by_phrases_do_not_name_an_agent(self):
        for text in (
            "The decision was announced by Tuesday morning.",
            "The report was delayed by three weeks.",
            "The funds were cut by 20 percent.",
            "The vote was postponed by noon.",
            "The order was issued by tomorrow.",
            "The deadline was missed by two days.",
            "The rule was created by default.",
        ):
            self.assertTrue(self._suppression(text), f"should still flag suppression: {text!r}")

    def test_real_named_agents_are_still_excluded(self):
        for text in (
            "The report was published by the department.",
            "The order was issued by officials.",
            "The suspect was detained by police.",
            "The plan was approved by the committee.",
            "The study was conducted by researchers.",
            "The statement was released by the company.",
        ):
            self.assertFalse(self._suppression(text), f"agent is named, should be excluded: {text!r}")


class QuoteVoiceClosureTests(unittest.TestCase):
    """O-04: end-to-end through analyze_text, not a hand-built Passage."""

    def _voices(self, text: str) -> set[str]:
        return {f.voice_class for f in analyze_text(text).findings}

    def test_unbalanced_opening_quote_is_not_a_heading(self):
        article = segment('The memo said "the plan is draconian and unworkable')
        self.assertEqual(article.passages[0].passage_type, "paragraph")

    def test_unbalanced_curly_quote_is_not_a_heading(self):
        article = segment('The memo said “the plan is draconian and unworkable')
        self.assertEqual(article.passages[0].passage_type, "paragraph")

    def test_unbalanced_quote_never_attributes_to_the_outlet(self):
        for text in (
            'The memo said "the plan is draconian and unworkable',
            'The memo said “the plan is draconian and unworkable',
        ):
            voices = self._voices(text)
            self.assertTrue(voices, f"expected findings for {text!r}")
            self.assertFalse(
                voices & {"reporter", "editorial", "headline"},
                f"quoted material attributed to outlet voice {voices} for {text!r}",
            )

    def test_quoted_material_inside_a_heading_belongs_to_the_speaker(self):
        voices = self._voices('Mayor Calls Plan "Draconian"')
        self.assertIn("quoted_speaker", voices)
        self.assertNotIn("headline", voices)

    def test_ordinary_heading_is_still_outlet_headline_voice(self):
        self.assertEqual(self._voices("Council Approves Draconian Scheme"), {"headline"})

    def test_ordinary_reporter_sentence_is_still_outlet_voice(self):
        self.assertEqual(self._voices("The council approved a draconian scheme yesterday."), {"reporter"})

    def test_balanced_quote_in_prose_is_speaker_voice(self):
        self.assertEqual(self._voices('Officials called it "a draconian scheme" on Tuesday.'), {"quoted_speaker"})


class PressureConfidenceDecouplingTests(unittest.TestCase):
    """O-03: confidence must not inherit rhetorical pressure via the provider."""

    CORPUS = (
        "A draconian, reckless, catastrophic scheme.",
        "The tyrannical regime siphons freedom.",
        "Officials refused to explain why they allowed the collapse.",
        "Mistakes were made.",
        "Shots were fired near the crowd.",
        "Either we act now or the city dies.",
        "A controversial proposal was noted.",
        "The plan still continues to expand.",
        "Members must either approve or lose everything, though a middle ground compromise exists.",
        "The catastrophic earthquake was recorded at magnitude 7.",
        '"This is an outrageous, draconian betrayal," said the senator.',
    )

    def _combinations(self):
        seen = set()
        for text in self.CORPUS:
            for finding in analyze_text(text).findings:
                seen.add((finding.pressure, finding.confidence))
        return seen

    def test_high_pressure_with_non_high_confidence_is_reachable(self):
        combos = self._combinations()
        high_pressure_lower_confidence = {
            c for c in combos if c[0] in ("P3", "P4") and c[1] != "High"
        }
        self.assertTrue(
            high_pressure_lower_confidence,
            f"pressure and confidence still collapse together; observed {sorted(combos)}",
        )

    def test_low_pressure_with_high_confidence_is_reachable(self):
        combos = self._combinations()
        self.assertTrue(
            {c for c in combos if c[0] in ("P1", "P2") and c[1] == "High"},
            f"observed {sorted(combos)}",
        )

    def test_provider_does_not_raise_certainty_for_rhetorical_tier(self):
        source = (ROOT / "services" / "rhetoric" / "providers.py").read_text()
        block = source[source.index('if mechanism_id == "loaded_language"'): source.index('elif mechanism_id == "presupposition"')]
        self.assertNotIn(
            "certainty += 0.2", block,
            "tier-derived certainty bonus reintroduced: pressure severity is not detection evidence",
        )


class TraceabilityConsistencyTests(unittest.TestCase):
    """O-01 / N-02: QA summaries must match their own rows."""

    def test_all_qa_matrices_are_internally_consistent(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import check_traceability

        for result in check_traceability.run():
            self.assertEqual(
                result["problems"], [],
                f"{result['document']} has malformed status rows: {result['problems']}",
            )
            self.assertEqual(
                result["mismatches"], [],
                f"{result['document']} summary disagrees with its rows: {result['mismatches']}",
            )


if __name__ == "__main__":
    unittest.main()
