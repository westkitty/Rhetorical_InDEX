"""Pre-calibration hardening regressions (M-01 … M-15, O-01 … O-11).

Each class corresponds to a finding from the post-merge source audit. Every test
here fails if its repair is reverted — verified by mutation, recorded in the
hardening report.

Governing rule: a conservative false negative is acceptable; an unsupported
confident claim is not.
"""
from __future__ import annotations

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "benchmarks" / "scripts"))

from services.comparison import (  # noqa: E402
    Claim,
    ComparisonSet,
    SourceAssertion,
    SourceDependency,
    align_pair,
)
from services.comparison.dependence import assess_independence  # noqa: E402
from services.comparison.divergence import canonical_proposition, propositions_are_identical  # noqa: E402
from services.comparison.omission import (  # noqa: E402
    OmissionRejection,
    evaluate_candidate_omission,
    parse_instant,
)
from services.evidence import EvidenceItem, EvidenceRelation, claim_state_for  # noqa: E402
from services.rhetoric import analyze_text, scoring, vocabulary as vocab  # noqa: E402
from services.rhetoric.document import article_from_passages, derive_article_id  # noqa: E402
from services.rhetoric.models import make_run_id  # noqa: E402
from services.rhetoric.pipeline import analyze_article  # noqa: E402
from services.rhetoric.providers import (  # noqa: E402
    DetectorProvider,
    MockDetectorProvider,
    ModelDetectorProvider,
    Verdict,
)

LOADED = vocab.mechanism("loaded_language")
CRIT = LOADED["positiveCriteria"][0]
EXCL = LOADED["exclusionCriteria"][0]
WARRANT = "Section 4b requires a magistrate-issued judicial warrant before content inspection"


def _a(source: str, article: str) -> SourceAssertion:
    return SourceAssertion(source, source.title(), article, f"{article}:p0000", "excerpt")


def claim(cid: str, proposition: str, source: str = "s", article: str = "art-x") -> Claim:
    return Claim(claim_id=cid, normalized_proposition=proposition, source_assertions=(_a(source, article),))


class M01PropositionalIdentityTests(unittest.TestCase):
    """Absence of detected divergence is NOT evidence of propositional identity."""

    SWAPS = (
        ("caused vs prevented",
         "The vaccine study found the treatment caused infertility in laboratory mice during the trial",
         "The vaccine study found the treatment prevented infertility in laboratory mice during the trial"),
        ("number role swap",
         "The blast injured 12 people and killed 40 people",
         "The blast injured 40 people and killed 12 people"),
        ("temporal role swap",
         "The meeting was moved from Tuesday to Thursday",
         "The meeting was moved from Thursday to Tuesday"),
        ("subject/object swap",
         "The company sued the regulator over the fine",
         "The regulator sued the company over the fine"),
        ("actor/victim swap",
         "Police detained the protester near the plaza",
         "The protester detained police near the plaza"),
        ("modal must vs may",
         "Platforms must retain user metadata under the statute",
         "Platforms may retain user metadata under the statute"),
        ("modal can vs cannot",
         "Regulators can inspect message content under the statute",
         "Regulators cannot inspect message content under the statute"),
        ("quantifier all vs some",
         "All committee members endorsed the revised budget",
         "Some committee members endorsed the revised budget"),
        ("opened vs closed",
         "The agency opened the investigation in March",
         "The agency closed the investigation in March"),
        ("gained vs lost",
         "The district gained four hundred residents last year",
         "The district lost four hundred residents last year"),
        ("unseen antonym (allowed/blocked)",
         "The board allowed the transfer of surplus funds",
         "The board blocked the transfer of surplus funds"),
    )

    def test_no_role_swap_can_ground_an_omission(self):
        for label, a, b in self.SWAPS:
            with self.subTest(label):
                alignment = align_pair(claim("a", a), claim("b", b))
                self.assertFalse(
                    alignment.is_usable_for_omission,
                    f"{label}: contradictory pair became usable ({alignment.relation})",
                )
                self.assertNotEqual(alignment.relation, "same_proposition", label)

    def test_identity_requires_exact_normalized_match(self):
        self.assertTrue(propositions_are_identical(
            "The Council Approved  the Plan.", "the council approved the plan"))
        self.assertFalse(propositions_are_identical(
            "the council approved the plan", "the plan approved the council"))

    def test_presentation_equivalence_is_still_recognized(self):
        for a, b in (
            ("city spending rose 12 percent last year", "city spending rose 12% last year"),
            ("the fund holds $2 million", "the fund holds $2,000,000"),
            ("1,000 residents applied", "1000 residents applied"),
        ):
            with self.subTest(a):
                alignment = align_pair(claim("a", a), claim("b", b))
                self.assertEqual(alignment.relation, "same_proposition")
                self.assertTrue(alignment.is_usable_for_omission)

    def test_identical_propositions_still_accepted(self):
        alignment = align_pair(claim("a", WARRANT), claim("b", WARRANT))
        self.assertEqual(alignment.relation, "same_proposition")
        self.assertTrue(alignment.is_usable_for_omission)

    def test_high_overlap_without_identity_is_never_usable(self):
        alignment = align_pair(
            claim("a", "the council approved the housing budget after long debate"),
            claim("b", "the council approved the housing budget following long debate"),
        )
        self.assertFalse(alignment.is_usable_for_omission)


class A01ExactNumericIdentityTests(unittest.TestCase):
    """canonical_proposition must be EXACT, never lossy float formatting.

    Finding A-01 (final pre-calibration audit): %g float formatting collapsed
    2_000_000 and 2_000_001 to the same 6-significant-digit string, and
    sequential in-place `.sub()` calls let a later regex re-match digits
    inside an already-generated marker. Both are fixed by exact Decimal
    arithmetic and a single non-overlapping-span substitution pass.
    """

    EQUIVALENT = (
        ("scale word vs digits", "the fund holds $2 million", "the fund holds $2,000,000"),
        ("percent vs percent word", "spending rose 12%", "spending rose 12 percent"),
        ("trailing decimal zero", "spending rose 12.0%", "spending rose 12 percent"),
        ("comma grouping", "1,000 residents applied", "1000 residents applied"),
        ("trailing decimal zero, plain", "the rate is 1.20", "the rate is 1.2"),
        ("case", "The Council Approved the Plan.", "the council approved the plan"),
        ("whitespace", "the  council   approved the plan", "the council approved the plan"),
        ("terminal punctuation", "the council approved the plan.", "the council approved the plan!"),
    )

    NON_EQUIVALENT = (
        ("adjacent large currency", "the fund contains $2,000,000", "the fund contains $2,000,001"),
        ("adjacent large plain integer", "the report cites 1000000 affected accounts",
         "the report cites 1000001 affected accounts"),
        ("adjacent large currency, 7 digits", "the fund contains $1,234,567", "the fund contains $1,234,568"),
        ("adjacent large plain, 8 digits", "the count reached 12345678", "the count reached 12345679"),
        ("decimal precision", "the rate was 12 percent", "the rate was 12.0001 percent"),
        ("zero vs near-zero", "the margin was 0 percent", "the margin was 0.0001 percent"),
        ("million boundary", "the total was 999999", "the total was 1000000"),
        ("trillion boundary", "the total was 999999999999", "the total was 1000000000000"),
    )

    ROLE_SWAPS = (
        ("number role swap", "injured 12 and killed 40", "injured 40 and killed 12"),
        ("temporal role swap", "moved Tuesday to Thursday", "moved Thursday to Tuesday"),
    )

    def test_formatting_equivalent_pairs_canonicalize_equal(self):
        for label, a, b in self.EQUIVALENT:
            with self.subTest(label):
                self.assertTrue(propositions_are_identical(a, b), f"{label}: {a!r} vs {b!r}")

    def test_unicode_nfd_and_nfc_forms_are_equivalent(self):
        import unicodedata
        composed = unicodedata.normalize("NFC", "the café reopened")
        decomposed = unicodedata.normalize("NFD", "the café reopened")
        self.assertNotEqual(composed, decomposed, "test fixture must actually differ at the byte level")
        self.assertTrue(propositions_are_identical(composed, decomposed))

    def test_adjacent_and_near_neighbor_numbers_remain_distinct(self):
        for label, a, b in self.NON_EQUIVALENT:
            with self.subTest(label):
                self.assertFalse(propositions_are_identical(a, b), f"{label}: {a!r} vs {b!r}")
                self.assertNotEqual(canonical_proposition(a), canonical_proposition(b), label)

    def test_word_order_still_carries_role_after_the_fix(self):
        for label, a, b in self.ROLE_SWAPS:
            with self.subTest(label):
                self.assertFalse(propositions_are_identical(a, b), label)

    def test_canonicalization_is_idempotent(self):
        """A generated marker must never be re-tokenized by a second pass —
        this is what the previous sequential `.sub()` bug violated."""
        for text in (
            "the fund contains $2,000,001",
            "$2,000,000 and 12% and 1,000 dollars owed by Tuesday at 3:00pm",
            "spending rose 12.0% while the count reached 999999999999",
        ):
            with self.subTest(text):
                once = canonical_proposition(text)
                twice = canonical_proposition(once)
                self.assertEqual(once, twice, f"not idempotent: {once!r} -> {twice!r}")

    def test_no_nested_or_scientific_notation_markers_survive(self):
        for text in ("$2,000,000", "$2,000,001", "999999999999", "12.0001%"):
            canon = canonical_proposition(text)
            self.assertNotIn("e+", canon, f"scientific notation leaked into {canon!r}")
            self.assertNotIn("e-", canon, f"scientific notation leaked into {canon!r}")
            # A correctly-formed marker never contains a second guillemet pair
            # nested inside the first (the old bug's signature).
            self.assertEqual(canon.count("«"), canon.count("»"), canon)

    def test_deterministic_property_adjacent_values_never_collide(self):
        """canonical(n) != canonical(n + 1) across several magnitudes, fixed
        deterministic data only — no randomized fuzzing."""
        magnitudes = (1, 99, 1_000, 999_999, 1_000_000, 2_000_000, 999_999_999_999)
        for n in magnitudes:
            with self.subTest(n=n):
                low = canonical_proposition(f"the total was {n}")
                high = canonical_proposition(f"the total was {n + 1}")
                self.assertNotEqual(low, high, f"{n} and {n + 1} collided")


class M02IndependenceTests(unittest.TestCase):
    """Unknown dependence is not independence."""

    def test_absent_dependency_data_is_unresolved_not_independent(self):
        assessment = assess_independence(["a", "b"], [])
        self.assertEqual(assessment.confirmed_independent_count, 1)
        self.assertTrue(assessment.has_unresolved)

    def test_unknown_link_is_unresolved(self):
        assessment = assess_independence(["a", "b"], [SourceDependency(("a", "b"), "unknown", "Low")])
        self.assertEqual(assessment.confirmed_independent_count, 1)

    def test_low_confidence_independence_claim_is_not_confirmed(self):
        assessment = assess_independence(
            ["a", "b"], [SourceDependency(("a", "b"), "independent_reporting", "Low")])
        self.assertEqual(assessment.confirmed_independent_count, 1)

    def test_confirmed_independent_reporting_counts(self):
        assessment = assess_independence(
            ["a", "b"], [SourceDependency(("a", "b"), "independent_reporting", "High")])
        self.assertEqual(assessment.confirmed_independent_count, 2)

    def test_syndication_is_dependent(self):
        assessment = assess_independence(
            ["a", "b"], [SourceDependency(("a", "b"), "syndication", "High")])
        self.assertTrue(assessment.dependent_pairs)
        self.assertEqual(assessment.confirmed_independent_count, 1)

    def test_partial_graph_fails_closed(self):
        # a-b confirmed independent, b-c unknown: only a pair is provable.
        assessment = assess_independence(
            ["a", "b", "c"],
            [SourceDependency(("a", "b"), "independent_reporting", "High")],
        )
        self.assertEqual(assessment.confirmed_independent_count, 2)
        self.assertTrue(assessment.has_unresolved)

    def test_duplicate_source_ids_do_not_inflate(self):
        assessment = assess_independence(["a", "a", "b"], [])
        self.assertEqual(assessment.source_ids, ("a", "b"))


class OmissionGateTests(unittest.TestCase):
    """M-02 / M-03 / M-04 gates, exercised end to end."""

    TARGET = [claim("ct", "the stadium roof was repaired", "sentinel", "art-sn")]

    def _set(self, **over):
        base = dict(
            comparison_set_id="cs", target_article_id="art-sn",
            member_article_ids=("art-tw", "art-pj"), provenance_kind="retrieved",
            source_of_article={"art-tw": "techwire", "art-pj": "policy"},
            dependencies=(SourceDependency(("techwire", "policy"), "independent_reporting", "High"),),
        )
        base.update(over)
        return ComparisonSet(**base)

    def _support(self, proposition=WARRANT):
        return [claim("f1", proposition, "techwire", "art-tw"),
                claim("f2", proposition, "policy", "art-pj")]

    def _evaluate(self, **over):
        kwargs = dict(
            comparison_set=self._set(), candidate_proposition=WARRANT,
            supporting_claims=self._support(), target_claims=self.TARGET,
            dimension="Responsibility", target_published_at="2026-07-12T10:00:00Z",
            knowable_at="2026-07-10T09:00:00Z", rationale="x",
        )
        kwargs.update(over)
        return evaluate_candidate_omission(**kwargs)

    def test_well_formed_omission_is_accepted(self):
        omission = self._evaluate()
        self.assertEqual(len(omission.supporting_source_ids), 2)

    def test_unconfirmed_independence_is_refused(self):
        with self.assertRaises(OmissionRejection) as ctx:
            self._evaluate(comparison_set=self._set(dependencies=()))
        self.assertEqual(ctx.exception.gate, "source_independence")

    def test_foreign_supporting_article_is_refused(self):
        foreign = [claim("f1", WARRANT, "techwire", "art-FOREIGN"),
                   claim("f2", WARRANT, "policy", "art-pj")]
        with self.assertRaises(OmissionRejection) as ctx:
            self._evaluate(supporting_claims=foreign)
        self.assertEqual(ctx.exception.gate, "comparison_set_membership")

    def test_target_article_cannot_corroborate_itself(self):
        selfsupport = [claim("f1", WARRANT, "sentinel", "art-sn"),
                       claim("f2", WARRANT, "policy", "art-pj")]
        with self.assertRaises(OmissionRejection) as ctx:
            self._evaluate(supporting_claims=selfsupport)
        self.assertEqual(ctx.exception.gate, "comparison_set_membership")

    def test_source_article_mismatch_is_refused(self):
        mismatched = [claim("f1", WARRANT, "WRONG", "art-tw"),
                      claim("f2", WARRANT, "policy", "art-pj")]
        with self.assertRaises(OmissionRejection) as ctx:
            self._evaluate(supporting_claims=mismatched)
        self.assertEqual(ctx.exception.gate, "comparison_set_membership")

    def test_foreign_target_claim_is_refused(self):
        with self.assertRaises(OmissionRejection) as ctx:
            self._evaluate(target_claims=[claim("ct", "x", "other", "art-OTHER")])
        self.assertEqual(ctx.exception.gate, "comparison_set_membership")

    def test_chronology_uses_instants_not_strings(self):
        # 09:00-05:00 is 14:00Z — LATER than 13:00Z despite comparing earlier lexically.
        with self.assertRaises(OmissionRejection) as ctx:
            self._evaluate(target_published_at="2026-07-10T13:00:00Z",
                           knowable_at="2026-07-10T09:00:00-05:00")
        self.assertEqual(ctx.exception.gate, "chronology")

    def test_same_instant_in_different_offsets_is_accepted(self):
        self._evaluate(target_published_at="2026-07-10T13:00:00Z",
                       knowable_at="2026-07-10T08:00:00-05:00")

    def test_earlier_instant_with_lexically_later_text_is_accepted(self):
        self._evaluate(target_published_at="2026-07-10T13:00:00Z",
                       knowable_at="2026-07-10T20:00:00+09:00")

    def test_equal_instant_is_accepted(self):
        self._evaluate(target_published_at="2026-07-10T13:00:00Z",
                       knowable_at="2026-07-10T13:00:00Z")

    def test_naive_timestamp_is_refused(self):
        with self.assertRaises(OmissionRejection):
            self._evaluate(knowable_at="2026-07-10T09:00:00")

    def test_malformed_timestamp_is_refused(self):
        with self.assertRaises(OmissionRejection):
            self._evaluate(knowable_at="not-a-date")

    def test_parse_instant_normalizes_to_utc(self):
        self.assertEqual(
            parse_instant("2026-07-10T08:00:00-05:00", field="t"),
            parse_instant("2026-07-10T13:00:00Z", field="t"),
        )


class A01EndToEndOmissionTests(unittest.TestCase):
    """A-01, exercised through the real omission gate, not just the identity function.

    Section 5 of the audit's remediation instructions requires that the
    identity gate reject a false match EVEN WITH divergence detection
    disabled — otherwise the fix is only as strong as a second, coincidental
    mechanism, which is exactly what the audit found was previously true.
    """

    TARGET = [claim("ct", "the town budget passed unanimously", "sentinel", "art-sn")]

    def _set(self, **over):
        base = dict(
            comparison_set_id="cs", target_article_id="art-sn",
            member_article_ids=("art-tw", "art-pj"), provenance_kind="retrieved",
            source_of_article={"art-tw": "techwire", "art-pj": "policy"},
            dependencies=(SourceDependency(("techwire", "policy"), "independent_reporting", "High"),),
        )
        base.update(over)
        return ComparisonSet(**base)

    def _evaluate(self, candidate_proposition, supporting_proposition, **over):
        supporting_claims = [
            claim("f1", supporting_proposition, "techwire", "art-tw"),
            claim("f2", supporting_proposition, "policy", "art-pj"),
        ]
        kwargs = dict(
            comparison_set=self._set(), candidate_proposition=candidate_proposition,
            supporting_claims=supporting_claims, target_claims=self.TARGET,
            dimension="Scale", target_published_at="2026-07-12T10:00:00Z",
            knowable_at="2026-07-10T09:00:00Z", rationale="x",
        )
        kwargs.update(over)
        return evaluate_candidate_omission(**kwargs)

    def test_adjacent_currency_values_cannot_ground_an_omission(self):
        with self.assertRaises(OmissionRejection) as ctx:
            self._evaluate("the fund contains $2,000,000", "the fund contains $2,000,001")
        self.assertEqual(ctx.exception.gate, "presence_elsewhere")

    def test_adjacent_plain_integers_cannot_ground_an_omission(self):
        with self.assertRaises(OmissionRejection) as ctx:
            self._evaluate(
                "the report cites 1000000 affected accounts",
                "the report cites 999999 affected accounts",
            )
        self.assertEqual(ctx.exception.gate, "presence_elsewhere")

    def test_identity_gate_alone_rejects_even_with_divergence_detection_disabled(self):
        """Mutation-style check inline: with detect_divergence forced to return
        nothing, the false match must STILL be refused. If disabling divergence
        makes the false identity usable, the identity repair is incomplete."""
        import services.comparison.claims as claims_module

        original = claims_module.detect_divergence
        claims_module.detect_divergence = lambda a, b: []
        try:
            with self.assertRaises(OmissionRejection) as ctx:
                self._evaluate("the fund contains $2,000,000", "the fund contains $2,000,001")
            self.assertEqual(ctx.exception.gate, "presence_elsewhere")
        finally:
            claims_module.detect_divergence = original
            self.assertIs(claims_module.detect_divergence, original)

    def test_genuinely_identical_large_numbers_still_ground_a_well_formed_omission(self):
        """Sanity check: the fix must not have become so strict that true
        identity stops working."""
        omission = self._evaluate("the fund contains $2,000,000", "the fund contains $2,000,000")
        self.assertEqual(len(omission.supporting_source_ids), 2)


class M05UncertaintyTests(unittest.TestCase):
    """An explicitly uncertain verdict may never become confirmed."""

    ARTICLE = article_from_passages("art-u", [("paragraph", "A draconian, reckless scheme passed today.")])

    def test_uncertain_verdict_is_always_candidate(self):
        for certainty in (0.5, 0.9, 0.99, 1.0):
            with self.subTest(certainty=certainty):
                result = analyze_article(self.ARTICLE, provider=MockDetectorProvider(
                    default=Verdict(applies="uncertain", criteria_triggered=(CRIT,), certainty=certainty)))
                self.assertTrue(result.findings)
                for finding in result.findings:
                    self.assertEqual(finding.state, "candidate")

    def test_yes_verdict_can_still_be_confirmed(self):
        result = analyze_article(self.ARTICLE, provider=MockDetectorProvider(
            default=Verdict(applies="yes", criteria_triggered=(CRIT,), certainty=0.95)))
        self.assertTrue(any(f.state == "confirmed" for f in result.findings))

    def test_reportable_state_requires_applies_yes(self):
        self.assertEqual(scoring.reportable_state("High", "uncertain"), "candidate")
        self.assertEqual(scoring.reportable_state("Medium", "uncertain"), "candidate")
        self.assertEqual(scoring.reportable_state("Medium", "yes"), "confirmed")
        self.assertEqual(scoring.reportable_state("Low", "yes"), "candidate")


class M06CriteriaMembershipTests(unittest.TestCase):
    """Criteria come from the taxonomy record, not invention."""

    ARTICLE = article_from_passages("art-c", [("paragraph", "A draconian, reckless scheme passed today.")])
    WRONG_MECHANISM_CRIT = vocab.mechanism("false_dilemma")["positiveCriteria"][0]

    def _findings(self, verdict):
        return analyze_article(self.ARTICLE, provider=MockDetectorProvider(default=verdict)).findings

    def test_invented_criterion_is_rejected(self):
        self.assertEqual(self._findings(Verdict(applies="yes", criteria_triggered=("invented",), certainty=0.9)), ())

    def test_criterion_from_another_mechanism_is_rejected(self):
        self.assertEqual(
            self._findings(Verdict(applies="yes", criteria_triggered=(self.WRONG_MECHANISM_CRIT,), certainty=0.9)), ())

    def test_exclusion_criterion_in_positive_list_is_rejected(self):
        self.assertEqual(self._findings(Verdict(applies="yes", criteria_triggered=(EXCL,), certainty=0.9)), ())

    def test_invented_failed_criterion_is_rejected(self):
        self.assertEqual(
            self._findings(Verdict(applies="yes", criteria_triggered=(CRIT,), criteria_failed=("nope",), certainty=0.9)), ())

    def test_duplicate_criteria_are_rejected(self):
        self.assertEqual(self._findings(Verdict(applies="yes", criteria_triggered=(CRIT, CRIT), certainty=0.9)), ())

    def test_valid_taxonomy_criteria_are_accepted(self):
        self.assertTrue(self._findings(
            Verdict(applies="yes", criteria_triggered=(CRIT,), criteria_failed=(EXCL,), certainty=0.9)))

    def test_every_shipped_finding_cites_only_taxonomy_criteria(self):
        result = analyze_text(
            'The mayor said "this draconian, reckless scheme" would either pass or destroy the city. '
            "Mistakes were made. Officials refused to explain why they allowed the delay."
        )
        self.assertTrue(result.findings)
        for finding in result.findings:
            record = vocab.mechanism(finding.mechanism_id)
            for criterion in finding.triggered_criteria:
                self.assertIn(criterion, record["positiveCriteria"])
            for criterion in finding.failed_criteria:
                self.assertIn(criterion, record["exclusionCriteria"])


class M06ModelResponseTests(unittest.TestCase):
    """Shape validation for untrusted model output."""

    def setUp(self):
        self.provider = ModelDetectorProvider()

    def test_string_where_array_expected_is_rejected(self):
        with self.assertRaises(ValueError):
            self.provider.parse_response(
                {"applies": "yes", "criteriaTriggered": "not a list", "criteriaFailed": [], "certainty": 0.8})

    def test_collection_confusion_cases_are_rejected(self):
        for payload in (
            {"applies": "yes", "criteriaTriggered": {"a": 1}, "criteriaFailed": [], "certainty": 0.5},
            {"applies": "yes", "criteriaTriggered": [1, 2], "criteriaFailed": [], "certainty": 0.5},
            {"applies": "yes", "criteriaTriggered": ["  "], "criteriaFailed": [], "certainty": 0.5},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.provider.parse_response(payload)

    def test_numeric_edge_cases_are_rejected(self):
        for certainty in (True, float("nan"), float("inf"), float("-inf"), 1.5, -0.1, "high"):
            with self.subTest(certainty=certainty), self.assertRaises(ValueError):
                self.provider.parse_response(
                    {"applies": "yes", "criteriaTriggered": ["x"], "criteriaFailed": [], "certainty": certainty})

    def test_unknown_applies_and_extra_properties_are_rejected(self):
        with self.assertRaises(ValueError):
            self.provider.parse_response(
                {"applies": "maybe", "criteriaTriggered": ["x"], "criteriaFailed": [], "certainty": 0.5})
        with self.assertRaises(ValueError):
            self.provider.parse_response(
                {"applies": "yes", "criteriaTriggered": ["x"], "criteriaFailed": [], "certainty": 0.5, "extra": 1})

    def test_well_formed_response_parses(self):
        verdict = self.provider.parse_response(
            {"applies": "yes", "criteriaTriggered": ["x"], "criteriaFailed": [], "certainty": 0.8})
        self.assertEqual(verdict.criteria_triggered, ("x",))


class M07M08EvidenceTests(unittest.TestCase):
    """Relation confidence caps state; corroboration counts items, not rows."""

    AUTH = EvidenceItem("e1", "statute", "S", directness="direct",
                        authenticity_state="verified", authenticity_basis="register check")
    AUTH2 = EvidenceItem("e2", "transcript", "T", directness="direct",
                         authenticity_state="verified", authenticity_basis="archive")
    UNVER1 = EvidenceItem("u1", "memo", "M", directness="direct")
    UNVER2 = EvidenceItem("u2", "note", "N", directness="direct")

    def test_low_confidence_relation_cannot_promote_to_direct_support(self):
        state = claim_state_for(
            [EvidenceRelation("r", "c", "e1", "supports", "Low")], {"e1": self.AUTH})
        self.assertNotEqual(state, "supported_by_direct_evidence")

    def test_medium_and_high_relations_may_promote(self):
        for confidence in ("Medium", "High"):
            with self.subTest(confidence):
                self.assertEqual(
                    claim_state_for([EvidenceRelation("r", "c", "e1", "supports", confidence)], {"e1": self.AUTH}),
                    "supported_by_direct_evidence")

    def test_low_confidence_contradiction_is_contested_not_contradicted(self):
        self.assertEqual(
            claim_state_for([EvidenceRelation("r", "c", "e1", "contradicts", "Low")], {"e1": self.AUTH}),
            "contested")

    def test_duplicate_relations_to_one_item_do_not_corroborate(self):
        self.assertNotEqual(
            claim_state_for(
                [EvidenceRelation("r1", "c", "u1", "supports", "High"),
                 EvidenceRelation("r2", "c", "u1", "supports", "High")], {"u1": self.UNVER1}),
            "corroborated")

    def test_two_distinct_items_corroborate(self):
        self.assertEqual(
            claim_state_for(
                [EvidenceRelation("r1", "c", "u1", "supports", "High"),
                 EvidenceRelation("r2", "c", "u2", "supports", "High")],
                {"u1": self.UNVER1, "u2": self.UNVER2}),
            "corroborated")

    def test_missing_evidence_id_does_not_corroborate(self):
        self.assertEqual(
            claim_state_for([EvidenceRelation("r1", "c", "GHOST", "supports", "High")], {"u1": self.UNVER1}),
            "unverified")

    def test_support_plus_contradiction_is_contested(self):
        self.assertEqual(
            claim_state_for(
                [EvidenceRelation("r1", "c", "e1", "supports", "High"),
                 EvidenceRelation("r2", "c", "e2", "contradicts", "Medium")],
                {"e1": self.AUTH, "e2": self.AUTH2}),
            "contested")


class M10TaxonomyAgreementTests(unittest.TestCase):
    """One canonical rule: taxonomy, detector and annotation guide agree."""

    def test_quoted_loading_is_detected_and_attributed_to_the_speaker(self):
        result = analyze_text('The mayor said "this is a draconian, reckless scheme" on Tuesday.')
        loaded = [f for f in result.findings if f.mechanism_id == "loaded_language"]
        self.assertTrue(loaded, "quoted rhetoric is still rhetoric and must be detected")
        for finding in loaded:
            self.assertEqual(finding.voice_class, "quoted_speaker")
            self.assertNotIn(
                "quoted", " ".join(finding.failed_criteria).lower(),
                "quoted speech must not be recorded as a failed exclusion",
            )

    def test_taxonomy_no_longer_excludes_quoted_speech(self):
        exclusions = " ".join(vocab.mechanism("loaded_language")["exclusionCriteria"]).lower()
        self.assertNotIn("direct verbatim quotes from an external actor", exclusions)

    def test_annotation_guide_matches_the_taxonomy_version(self):
        guide = (ROOT / "benchmarks" / "ANNOTATION_GUIDE.md").read_text()
        self.assertIn(vocab.taxonomy_version(), guide)


class M14PressureGoldenTests(unittest.TestCase):
    """Every taxonomy positive example is an executable pressure golden."""

    def test_taxonomy_examples_agree_with_the_scorer(self):
        taxonomy = json.loads((ROOT / "packages" / "taxonomy" / "taxonomy.json").read_text())
        checked = 0
        for mechanism in taxonomy["mechanisms"]:
            if mechanism["id"] not in vocab.INTRINSIC_ALPHA_SLICE:
                continue
            for example in mechanism.get("positiveExamples", []):
                expected = example.get("pressure")
                if not expected:
                    continue
                checked += 1
                observed = [
                    f.pressure for f in analyze_text(example["text"]).findings
                    if f.mechanism_id == mechanism["id"]
                ]
                self.assertIn(
                    expected, observed,
                    f"{mechanism['id']}: taxonomy example is labelled {expected} but the scorer "
                    f"produced {observed}. The taxonomy rubric is authoritative.",
                )
        self.assertGreaterEqual(checked, 4, "every implemented mechanism needs a pressure golden")


class ModerateFindingTests(unittest.TestCase):
    """O-01, O-02, O-04, O-06, O-07, O-08, O-09, O-10, O-11."""

    def test_o01_genuine_binary_is_not_a_false_dilemma(self):
        for text in ("The verdict is either guilty or not guilty under the statute.",
                     "The bill will either pass or fail in committee.",
                     "The claim is either true or not true."):
            with self.subTest(text):
                self.assertFalse(
                    [f for f in analyze_text(text).findings if f.mechanism_id == "false_dilemma"])

    def test_o01_real_false_dilemma_still_detected(self):
        self.assertTrue([
            f for f in analyze_text("Members must either approve the levy or lose everything.").findings
            if f.mechanism_id == "false_dilemma"])

    def test_o02_change_of_state_presupposition_is_live(self):
        findings = [f for f in analyze_text(
            "The agency still continues to expand its surveillance program.").findings
            if f.mechanism_id == "presupposition"]
        self.assertTrue(findings, "change-of-state generator must not be a dead path")
        for finding in findings:
            self.assertEqual(finding.state, "candidate", "weak construction stays a candidate")

    def test_o06_run_id_changes_with_taxonomy_and_provider_version(self):
        base = dict(content_hash="h", detector_version="d", provider_id="p",
                    taxonomy_version="1.0.0", provider_version="1")
        original = make_run_id(**base)
        self.assertNotEqual(original, make_run_id(**{**base, "taxonomy_version": "1.1.0"}))
        self.assertNotEqual(original, make_run_id(**{**base, "provider_version": "2"}))
        self.assertEqual(original, make_run_id(**base), "run id must stay deterministic")

    def test_o07_identical_text_from_different_publishers_gets_distinct_article_ids(self):
        a = analyze_text("Identical syndicated copy about the budget.", publisher="Paper A")
        b = analyze_text("Identical syndicated copy about the budget.", publisher="Paper B")
        self.assertNotEqual(a.article.article_id, b.article.article_id)
        self.assertEqual(a.article.content_hash, b.article.content_hash,
                         "content identity must still detect duplicate text")

    def test_o07_sourceless_local_paste_stays_content_derived_and_deterministic(self):
        self.assertEqual(derive_article_id("abc123"), derive_article_id("abc123"))
        a = analyze_text("A local paste with no provenance at all.")
        b = analyze_text("A local paste with no provenance at all.")
        self.assertEqual(a.article.article_id, b.article.article_id)

    def test_o08_batch_with_a_successful_zero_finding_passage_is_partial(self):
        article = article_from_passages("art-b", [
            ("paragraph", "A draconian, reckless scheme passed."),
            ("paragraph", "An ordinary neutral sentence about municipal process."),
        ])
        result = analyze_article(article, batch_size=10, provider=MockDetectorProvider(
            default=Verdict(applies="yes", criteria_triggered=(CRIT,), certainty=0.8),
            raise_on_passage={"art-b:p0000"}))
        self.assertEqual(result.run.batches[0]["status"], "partial")
        self.assertEqual(result.run.batches[0]["succeededPassages"], 1)

    def test_o09_provider_faults_and_internal_faults_are_distinguished(self):
        class ProviderBoom(DetectorProvider):
            kind, provider_id, version = "mock", "boom", "1"

            def verify(self, context):
                raise RuntimeError("provider outage")

        article = article_from_passages("art-p", [("paragraph", "A draconian scheme passed.")])
        result = analyze_article(article, provider=ProviderBoom())
        self.assertEqual([f.stage for f in result.run.failures], ["provider_error"])

    def test_o10_curly_single_quotes_are_quoted_speech(self):
        findings = analyze_text("‘This is an outrageous, draconian betrayal,’ the mayor declared.").findings
        self.assertTrue(findings)
        for finding in findings:
            self.assertEqual(finding.voice_class, "quoted_speaker")

    def test_o10_apostrophes_are_not_quotation(self):
        findings = analyze_text("The council's plan was called reckless and draconian.").findings
        self.assertTrue(findings)
        for finding in findings:
            self.assertNotEqual(finding.voice_class, "quoted_speaker")

    def test_o11_exclusions_are_candidate_local_not_whole_passage(self):
        result = analyze_text(
            "The council approved a draconian scheme. Separately, a Category 4 storm hit the coast.")
        loaded = [f for f in result.findings if f.mechanism_id == "loaded_language"]
        self.assertTrue(loaded)
        for finding in loaded:
            self.assertNotIn(
                "technical", " ".join(finding.pressure_factors).lower(),
                "an unrelated sentence must not apply the technical-context exclusion")

    def test_o11_same_sentence_exclusion_still_applies(self):
        result = analyze_text("The catastrophic earthquake was recorded at magnitude 7.")
        loaded = [f for f in result.findings if f.mechanism_id == "loaded_language"]
        self.assertTrue(loaded)
        self.assertTrue(any("technical" in " ".join(f.pressure_factors).lower() for f in loaded))


class O05MatchingTests(unittest.TestCase):
    """Benchmark matching must be optimal and order-independent."""

    def test_maximum_cardinality_beats_greedy(self):
        from evaluate import maximum_matching
        # Greedy would let prediction 0 take gold 0, stranding prediction 1.
        self.assertEqual(len(maximum_matching({0: [0, 1], 1: [0]})), 2)

    def test_contested_single_gold_yields_one_match(self):
        from evaluate import maximum_matching
        self.assertEqual(len(maximum_matching({0: [0], 1: [0]})), 1)

    def test_matching_is_deterministic(self):
        from evaluate import maximum_matching
        first = maximum_matching({0: [0, 1], 1: [0], 2: [1]})
        for _ in range(5):
            self.assertEqual(maximum_matching({0: [0, 1], 1: [0], 2: [1]}), first)


if __name__ == "__main__":
    unittest.main()


class M09CorpusIntegrityTests(unittest.TestCase):
    """Adjudicated gold must be validated before it can produce metrics.

    Mutation testing exposed that these checks had no test coverage: disabling
    the span round-trip and the stale-taxonomy rejection left the suite green.
    """

    TEXT = "The council approved a draconian, reckless scheme on Tuesday."
    SPAN = "draconian, reckless scheme"

    def _annotation(self, **over):
        start = self.TEXT.index(self.SPAN)
        base = {
            "annotationId": "a1", "passageOrdinal": 0,
            "startChar": start, "endChar": start + len(self.SPAN), "excerpt": self.SPAN,
            "mechanismId": "loaded_language", "pressure": "P3",
            "reviewerConfidence": "High", "voiceClass": "reporter",
        }
        base.update(over)
        return base

    def _proposal(self, who, annotation=None, **over):
        annotation = annotation or self._annotation()
        base = {
            "proposalId": f"p-{who}", "mechanismId": annotation["mechanismId"], "passageOrdinal": 0,
            "startChar": annotation["startChar"], "endChar": annotation["endChar"],
            "excerpt": annotation["excerpt"], "pressure": "P3",
            "reviewerConfidence": "High", "voiceClass": "reporter",
        }
        base.update(over)
        return base

    def _submission(self, who, proposals=None):
        return {"submissionId": f"sub-{who}", "annotatorId": who,
                "proposals": [self._proposal(who)] if proposals is None else proposals}

    def _document(self, **over):
        annotation = self._annotation()
        base = {
            "articleId": "t1", "genre": "straight_news",
            "taxonomyVersion": vocab.taxonomy_version(),
            "adjudicationStatus": "adjudicated",
            "annotatorIds": ["annotator-a", "annotator-b"],
            "passages": [{"ordinal": 0, "passageType": "paragraph", "text": self.TEXT}],
            "annotations": [annotation],
            "annotatorSubmissions": [
                self._submission("annotator-a"),
                self._submission("annotator-b"),
            ],
        }
        base.update(over)
        return base

    def _validate(self, document):
        from validate_corpus import validate_document
        return validate_document(document, path="t.json", expected_taxonomy=vocab.taxonomy_version())

    def test_valid_document_passes(self):
        self.assertTrue(self._validate(self._document()).valid)

    def test_excerpt_must_round_trip_against_its_passage(self):
        report = self._validate(self._document(annotations=[self._annotation(excerpt="totally wrong")]))
        self.assertFalse(report.valid)
        self.assertTrue(any("round-trip" in e for e in report.errors))

    def test_stale_taxonomy_version_is_rejected(self):
        report = self._validate(self._document(taxonomyVersion="1.0.0-alpha0"))
        self.assertFalse(report.valid)
        self.assertTrue(any("taxonomyVersion" in e for e in report.errors))

    def test_span_bounds_are_validated(self):
        for over in ({"startChar": 30, "endChar": 20}, {"endChar": 9999}, {"startChar": -1}):
            with self.subTest(over=over):
                self.assertFalse(self._validate(self._document(annotations=[self._annotation(**over)])).valid)

    def test_boolean_coordinates_are_rejected(self):
        self.assertFalse(self._validate(self._document(annotations=[self._annotation(startChar=True)])).valid)

    def test_unknown_and_cross_document_mechanisms_are_rejected(self):
        for mechanism in ("not_a_mechanism", "material_omission"):
            with self.subTest(mechanism):
                self.assertFalse(
                    self._validate(self._document(annotations=[self._annotation(mechanismId=mechanism)])).valid)

    def test_missing_voice_class_is_rejected(self):
        annotation = {k: v for k, v in self._annotation().items() if k != "voiceClass"}
        self.assertFalse(self._validate(self._document(annotations=[annotation])).valid)

    def test_duplicate_annotation_ids_and_passage_ordinals_are_rejected(self):
        self.assertFalse(
            self._validate(self._document(annotations=[self._annotation(), self._annotation()])).valid)
        self.assertFalse(self._validate(self._document(passages=[
            {"ordinal": 0, "passageType": "paragraph", "text": self.TEXT},
            {"ordinal": 0, "passageType": "paragraph", "text": "second"},
        ])).valid)

    def test_invalid_vocabulary_values_are_rejected(self):
        for over in ({"pressure": "P9"}, {"reviewerConfidence": "Certain"}, {"voiceClass": "publisher"}):
            with self.subTest(over=over):
                self.assertFalse(self._validate(self._document(annotations=[self._annotation(**over)])).valid)

    def test_plural_mechanisms_field_is_rejected(self):
        self.assertFalse(
            self._validate(self._document(annotations=[self._annotation(mechanisms=["loaded_language"])])).valid)

    def test_single_annotator_document_cannot_be_adjudicated(self):
        self.assertFalse(self._validate(self._document(annotatorIds=["only-one"])).valid)

    def test_original_submissions_must_be_preserved_from_two_annotators(self):
        single = [self._document()["annotatorSubmissions"][0]]
        self.assertFalse(self._validate(self._document(annotatorSubmissions=single)).valid)

    def test_missing_annotator_submissions_is_rejected(self):
        """A-02: the field being absent entirely must not read as zero errors."""
        doc = self._document()
        del doc["annotatorSubmissions"]
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("annotatorSubmissions" in e for e in report.errors))

    def test_empty_annotator_submissions_is_rejected(self):
        """A-02 root cause: `annotatorSubmissions: []` must never bypass preservation.

        The original bug was `if proposals:` — an empty top-level array made the
        preservation check itself not run, rather than run and fail. This must
        FAIL, and for the right reason (fewer than MIN_ANNOTATORS records), not
        pass by omission.
        """
        report = self._validate(self._document(annotatorSubmissions=[]))
        self.assertFalse(report.valid)
        self.assertTrue(any("distinct" in e and "annotator" in e for e in report.errors), report.errors)

    def test_two_zero_proposal_submissions_is_a_valid_hard_negative(self):
        """MUST PASS: two annotators, both independently found nothing."""
        doc = self._document(
            annotations=[],
            annotatorSubmissions=[
                self._submission("annotator-a", proposals=[]),
                self._submission("annotator-b", proposals=[]),
            ],
        )
        report = self._validate(doc)
        self.assertTrue(report.valid, report.errors)
        self.assertTrue(report.scored)

    def test_three_zero_proposal_submissions_is_valid(self):
        doc = self._document(
            annotatorIds=["annotator-a", "annotator-b", "annotator-c"],
            annotations=[],
            annotatorSubmissions=[
                self._submission("annotator-a", proposals=[]),
                self._submission("annotator-b", proposals=[]),
                self._submission("annotator-c", proposals=[]),
            ],
        )
        self.assertTrue(self._validate(doc).valid)

    def test_one_finding_plus_one_zero_proposal_submission_is_valid(self):
        annotation = self._annotation()
        doc = self._document(
            annotations=[annotation],
            annotatorSubmissions=[
                self._submission("annotator-a", proposals=[self._proposal("annotator-a", annotation)]),
                self._submission("annotator-b", proposals=[]),
            ],
        )
        self.assertTrue(self._validate(doc).valid)

    def test_both_submissions_empty_but_adjudication_still_positive_is_structurally_valid(self):
        """A third-party adjudicator finding something neither annotator flagged
        is a coherence question for the adjudication protocol, not something the
        corpus validator is positioned to reject."""
        annotation = self._annotation()
        doc = self._document(
            annotations=[annotation],
            annotatorSubmissions=[
                self._submission("annotator-a", proposals=[]),
                self._submission("annotator-b", proposals=[]),
            ],
        )
        self.assertTrue(self._validate(doc).valid)

    def test_duplicate_submission_id_is_rejected(self):
        doc = self._document(annotatorSubmissions=[
            self._submission("annotator-a", proposals=[])
            | {"submissionId": "dup"},
            self._submission("annotator-b", proposals=[])
            | {"submissionId": "dup"},
        ])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("duplicate submissionId" in e for e in report.errors))

    def test_annotator_submitting_twice_is_rejected(self):
        doc = self._document(annotatorSubmissions=[
            self._submission("annotator-a", proposals=[]) | {"submissionId": "sub-1"},
            self._submission("annotator-a", proposals=[]) | {"submissionId": "sub-2"},
        ])
        self.assertFalse(self._validate(doc).valid)

    def test_annotator_ids_must_agree_with_submission_records(self):
        doc = self._document(
            annotatorIds=["annotator-a", "annotator-c"],
            annotatorSubmissions=[
                self._submission("annotator-a", proposals=[]),
                self._submission("annotator-b", proposals=[]),
            ],
        )
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("does not match" in e for e in report.errors))

    def test_duplicate_proposal_id_across_different_submissions_is_rejected(self):
        annotation = self._annotation()
        doc = self._document(annotatorSubmissions=[
            self._submission("annotator-a", proposals=[
                self._proposal("annotator-a", annotation, proposalId="dup-prop")]),
            self._submission("annotator-b", proposals=[
                self._proposal("annotator-b", annotation, proposalId="dup-prop")]),
        ])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("duplicate proposalId" in e for e in report.errors))

    def test_proposal_excerpt_must_round_trip(self):
        doc = self._document(annotatorSubmissions=[
            self._submission("annotator-a", proposals=[
                self._proposal("annotator-a", excerpt="not the real text")]),
            self._submission("annotator-b", proposals=[]),
        ])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("round-trip" in e for e in report.errors))

    def test_proposal_missing_voice_class_is_rejected(self):
        annotation = self._annotation()
        broken = {k: v for k, v in self._proposal("annotator-a", annotation).items() if k != "voiceClass"}
        doc = self._document(annotatorSubmissions=[
            self._submission("annotator-a", proposals=[broken]),
            self._submission("annotator-b", proposals=[]),
        ])
        self.assertFalse(self._validate(doc).valid)

    def test_proposal_unknown_mechanism_is_rejected(self):
        doc = self._document(annotatorSubmissions=[
            self._submission("annotator-a", proposals=[
                self._proposal("annotator-a", mechanismId="not_a_mechanism")]),
            self._submission("annotator-b", proposals=[]),
        ])
        self.assertFalse(self._validate(doc).valid)

    def test_resolution_referencing_unknown_proposal_is_rejected(self):
        doc = self._document(resolutions=[{"decision": "drop", "proposalIds": ["nonexistent-proposal"]}])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("unknown proposalId" in e for e in report.errors))

    def test_worked_example_carries_two_structured_submissions(self):
        example = json.loads((ROOT / "benchmarks" / "corpus" / "_example.json").read_text())
        report = self._validate(example)
        self.assertTrue(report.valid, report.errors)
        self.assertEqual(len(example["annotatorSubmissions"]), 2)

    def test_evaluate_treats_malformed_adjudicated_material_as_fatal(self):
        """evaluate.py's loader must not silently skip a broken adjudicated file."""
        import tempfile
        from evaluate import load_corpus
        from validate_corpus import CorpusIntegrityError

        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp)
            (path / "broken.json").write_text(json.dumps(self._document(annotatorSubmissions=[])))
            with self.assertRaises(CorpusIntegrityError):
                load_corpus(path)

    def test_preserved_submissions_recover_every_agreement_dimension(self):
        """A-02 recoverability proof: the preserved data must be enough to later
        compute inter-annotator agreement on presence, mechanism, span, pressure
        and voice — without implementing the metric itself here."""
        annotation_a = self._annotation(mechanismId="loaded_language", pressure="P3", voiceClass="reporter")
        annotation_b = self._annotation(
            annotationId="a2", mechanismId="euphemism_dysphemism", pressure="P2", voiceClass="quoted_speaker")
        doc = self._document(
            annotations=[annotation_a],
            annotatorSubmissions=[
                self._submission("annotator-a", proposals=[
                    self._proposal("annotator-a", annotation_a, mechanismId="loaded_language",
                                   pressure="P3", voiceClass="reporter")]),
                self._submission("annotator-b", proposals=[
                    self._proposal("annotator-b", annotation_b, mechanismId="euphemism_dysphemism",
                                   pressure="P2", voiceClass="quoted_speaker")]),
            ],
        )
        report = self._validate(doc)
        self.assertTrue(report.valid, report.errors)

        by_annotator = {s["annotatorId"]: s for s in doc["annotatorSubmissions"]}
        self.assertEqual(set(by_annotator), {"annotator-a", "annotator-b"})  # identity
        for who, expected_mechanism, expected_pressure, expected_voice in (
            ("annotator-a", "loaded_language", "P3", "reporter"),
            ("annotator-b", "euphemism_dysphemism", "P2", "quoted_speaker"),
        ):
            proposals = by_annotator[who]["proposals"]
            self.assertEqual(len(proposals), 1)  # presence
            proposal = proposals[0]
            self.assertEqual(proposal["mechanismId"], expected_mechanism)  # mechanism
            self.assertEqual((proposal["startChar"], proposal["endChar"]), (23, 49))  # span
            self.assertEqual(proposal["pressure"], expected_pressure)  # pressure
            self.assertEqual(proposal["voiceClass"], expected_voice)  # voice
        self.assertNotEqual(
            by_annotator["annotator-a"]["proposals"][0]["mechanismId"],
            by_annotator["annotator-b"]["proposals"][0]["mechanismId"],
            "the disagreement itself must survive adjudication, not just the final gold pick",
        )

    def test_unresolved_unresolvable_cannot_be_adjudicated(self):
        report = self._validate(self._document(
            resolutions=[{"decision": "unresolvable", "proposalIds": ["p-annotator-a"]}]))
        self.assertFalse(report.valid)

    def test_non_adjudicated_documents_are_ignored_not_errors(self):
        for status in ("draft", "annotated", "disputed"):
            with self.subTest(status):
                report = self._validate(self._document(adjudicationStatus=status, annotatorIds=[]))
                self.assertTrue(report.valid)
                self.assertFalse(report.scored)

    def test_invalid_adjudicated_document_is_fatal_not_skipped(self):
        import tempfile
        from validate_corpus import CorpusIntegrityError, assert_corpus_valid

        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp)
            (path / "broken.json").write_text(
                json.dumps(self._document(annotations=[self._annotation(excerpt="wrong")])))
            with self.assertRaises(CorpusIntegrityError):
                assert_corpus_valid(path)

    def test_repository_corpus_remains_empty_and_valid(self):
        from validate_corpus import validate_corpus

        reports = validate_corpus(ROOT / "benchmarks" / "corpus")
        self.assertEqual([r for r in reports if r.scored], [],
                         "the repository benchmark corpus must remain EMPTY")
