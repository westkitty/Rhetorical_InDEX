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
from services.comparison.divergence import (  # noqa: E402
    canonical_identity_key,
    canonical_proposition,
    propositions_are_identical,
)
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
    """propositions_are_identical (backed by canonical_identity_key) must be
    EXACT, never lossy float formatting and never string-collidable.

    Finding A-01 (final pre-calibration audit): %g float formatting collapsed
    2_000_000 and 2_000_001 to the same 6-significant-digit string, and
    sequential in-place `.sub()` calls let a later regex re-match digits
    inside an already-generated marker.

    canonical_proposition() is diagnostic-only now (see B-02 below); these
    tests exercise the LOAD-BEARING functions, propositions_are_identical and
    canonical_identity_key, directly wherever the distinction matters.
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
                self.assertNotEqual(canonical_identity_key(a), canonical_identity_key(b), label)

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

    def test_no_scientific_notation_in_numeric_tokens_or_diagnostic_rendering(self):
        for text in ("$2,000,000", "$2,000,001", "999999999999", "12.0001%"):
            for kind, value in canonical_identity_key(text):
                if kind != "text":
                    self.assertNotIn("e+", value, f"scientific notation leaked into token {value!r}")
                    self.assertNotIn("e-", value, f"scientific notation leaked into token {value!r}")
            canon = canonical_proposition(text)
            self.assertNotIn("e+", canon, f"scientific notation leaked into {canon!r}")
            self.assertNotIn("e-", canon, f"scientific notation leaked into {canon!r}")

    def test_deterministic_property_adjacent_values_never_collide(self):
        """identity_key(n) != identity_key(n + 1) across several magnitudes,
        fixed deterministic data only — no randomized fuzzing."""
        magnitudes = (1, 99, 1_000, 999_999, 1_000_000, 2_000_000, 999_999_999_999)
        for n in magnitudes:
            with self.subTest(n=n):
                low = canonical_identity_key(f"the total was {n}")
                high = canonical_identity_key(f"the total was {n + 1}")
                self.assertNotEqual(low, high, f"{n} and {n + 1} collided")

    def test_long_digit_run_with_no_percent_sign_does_not_hang(self):
        """Fresh-sweep finding: _NUM_PERCENT's mandatory trailing suffix
        (`%` / "percent") with no lookbehind guard caused catastrophic
        backtracking on a long digit run that never satisfies it — O(n^2),
        observed ~9s at 10,000 digits and effectively unbounded beyond that.
        This must stay linear: a 100,000-digit non-percent number is well
        within a single JSON string field and must not be a DoS vector."""
        import time

        big = "9" * 100_000
        start = time.time()
        canonical_identity_key(f"the total was {big}")
        elapsed = time.time() - start
        self.assertLess(elapsed, 2.0, f"took {elapsed:.2f}s — regressed to quadratic behavior")

    def test_many_numbers_in_one_document_does_not_hang(self):
        """Fresh-sweep finding: `_already_consumed`'s linear scan over the
        growing `consumed` list made canonical_identity_key O(k^2) in the
        NUMBER of numeric matches, independent of the percent-regex fix
        above — a realistic long article with hundreds of dates/currency/
        percentages (exactly the input this system exists to process) took
        multiple seconds. Fixed with bisect for O(log k) overlap checks."""
        import time

        paragraph = (
            "The council approved $2,000,000 in funding on Tuesday, "
            "a 12 percent increase over last year. "
        )
        text = paragraph * 4000  # several thousand numeric matches
        start = time.time()
        canonical_identity_key(text)
        elapsed = time.time() - start
        self.assertLess(elapsed, 3.0, f"took {elapsed:.2f}s — regressed to quadratic behavior")


class C01NumericCommaGrammarTests(unittest.TestCase):
    """C-01: only genuine thousands grouping may have its commas stripped.

    The old body pattern `\\d[\\d,]*` accepted any digit/comma arrangement and
    then stripped every comma, so structurally different source text collapsed
    onto the same number — "1,2,3" became 123, "1,00" became 100, "12,34,567"
    became 1234567. A malformed or entirely different numeral could therefore
    establish `same_proposition` with an unrelated clean integer.
    """

    MALFORMED_VS_CLEAN = (
        ("digit-by-digit commas", "scores were 1,2,3", "scores were 123"),
        ("two-digit group", "code 1,00", "code 100"),
        ("lakh-style grouping", "value 12,34,567", "value 1234567"),
        ("currency, digit-by-digit", "total $1,2,3", "total $123"),
        ("percent, digit-by-digit", "rate 1,2,3%", "rate 123%"),
        ("doubled comma", "count 1,,000", "count 1000"),
        ("four-digit lead group", "n 1234,567", "n 1234567"),
        ("leading comma", "x ,1000", "x 1000"),
    )

    WELL_FORMED_EQUIVALENT = (
        ("thousands", "n 1,000", "n 1000"),
        ("millions", "n 1,234,567", "n 1234567"),
        ("currency vs scale word", "f $2,000,000", "f $2 million"),
        ("percent", "r 12.0%", "r 12 percent"),
        ("grouped with fraction", "d 1,234.50", "d 1234.5"),
    )

    def test_malformed_grouping_never_matches_a_clean_integer(self):
        for label, malformed, clean in self.MALFORMED_VS_CLEAN:
            with self.subTest(label):
                self.assertFalse(
                    propositions_are_identical(malformed, clean),
                    f"{label}: {malformed!r} collapsed onto {clean!r}",
                )

    def test_well_formed_grouping_still_normalizes(self):
        for label, a, b in self.WELL_FORMED_EQUIVALENT:
            with self.subTest(label):
                self.assertTrue(propositions_are_identical(a, b), f"{label}: {a!r} vs {b!r}")

    def test_malformed_grouping_is_not_reflowed_into_one_clean_token(self):
        """The comma must survive as literal text rather than being silently
        dropped — otherwise a different reflowed integer could restore the same
        false identity by another route."""
        for malformed in ("1,2,3", "1,00", "12,34,567", "1,,000", "1234,567"):
            with self.subTest(malformed):
                key = canonical_identity_key(f"n {malformed}")
                numeric = [t for t in key if t[0] != "text"]
                commas = [t for t in key if t[0] == "text" and "," in t[1]]
                self.assertGreater(len(numeric), 1, f"{malformed!r} became a single numeric token")
                self.assertTrue(commas, f"{malformed!r} lost its comma entirely: {key}")

    def test_no_malformed_form_collides_with_any_clean_integer(self):
        """Exhaustive cross-product over the attack set: the security-relevant
        invariant is that malformed text can never reach a CLEAN integer, which
        is what would let it ground a false Material Omission."""
        malformed = ("1,2,3", "1,00", "12,34,567", "1,,000", "1234,567", ",1000", "1,0", "0,1", "12,3", "1,2")
        clean = ("1", "10", "100", "1000", "10000", "100000", "1234567", "0", "7")
        for m in malformed:
            for c in clean:
                with self.subTest(malformed=m, clean=c):
                    self.assertFalse(propositions_are_identical(f"n {m}", f"n {c}"))

    def test_malformed_grouping_cannot_ground_an_omission_without_divergence(self):
        """End to end, with detect_divergence forced to a no-op: the strict
        grammar alone must refuse the false match."""
        import services.comparison.claims as claims_module

        original = claims_module.detect_divergence
        claims_module.detect_divergence = lambda a, b: []
        try:
            comparison_set = ComparisonSet(
                comparison_set_id="cs", target_article_id="art-sn",
                member_article_ids=("art-tw", "art-pj"), provenance_kind="retrieved",
                source_of_article={"art-tw": "techwire", "art-pj": "policy"},
                dependencies=(SourceDependency(("techwire", "policy"), "independent_reporting", "High"),),
            )
            supporting = [
                claim("f1", "the fund contains 1,2,3 units", "techwire", "art-tw"),
                claim("f2", "the fund contains 1,2,3 units", "policy", "art-pj"),
            ]
            with self.assertRaises(OmissionRejection) as ctx:
                evaluate_candidate_omission(
                    comparison_set=comparison_set,
                    candidate_proposition="the fund contains 123 units",
                    supporting_claims=supporting,
                    target_claims=[claim("ct", "the town budget passed", "sentinel", "art-sn")],
                    dimension="Scale", target_published_at="2026-07-12T10:00:00Z",
                    knowable_at="2026-07-10T09:00:00Z", rationale="x",
                )
            self.assertEqual(ctx.exception.gate, "presence_elsewhere")
        finally:
            claims_module.detect_divergence = original

    def test_leading_zeros_remain_numeric_equality(self):
        """Documented consequence, not a defect: leading zeros are presentation
        only, so "007" == "7". This is why two malformed forms that reduce to
        the same token sequence ("1,00" and "1,0" -> 1 , 0) compare equal to
        each other — neither can reach a clean integer, which is the invariant
        that actually matters."""
        self.assertTrue(propositions_are_identical("n 007", "n 7"))
        self.assertTrue(propositions_are_identical("n 1,00", "n 1,0"))
        self.assertFalse(propositions_are_identical("n 1,00", "n 100"))


class B01ArbitraryPrecisionScalingTests(unittest.TestCase):
    """B-01: Decimal scale multiplication must never round under the ambient
    context precision (28 significant digits by default), regardless of how
    many digits the source numeral has.
    """

    SCALES = ("hundred", "thousand", "million", "billion", "trillion")

    def _adjacent(self, digits, scale):
        low = "1" + "2" * (digits - 1)
        high = low[:-1] + "3"
        a = f"the fund holds ${low} {scale}"
        b = f"the fund holds ${high} {scale}"
        return a, b

    def test_30_digit_adjacent_values_remain_distinct_at_every_scale(self):
        for scale in self.SCALES:
            with self.subTest(scale=scale):
                a, b = self._adjacent(30, scale)
                self.assertFalse(propositions_are_identical(a, b), f"{scale}: {a!r} vs {b!r}")

    def test_50_digit_adjacent_values_remain_distinct_at_every_scale(self):
        for scale in self.SCALES:
            with self.subTest(scale=scale):
                a, b = self._adjacent(50, scale)
                self.assertFalse(propositions_are_identical(a, b), f"{scale}: {a!r} vs {b!r}")

    def test_100_digit_adjacent_values_remain_distinct_at_every_scale(self):
        for scale in self.SCALES:
            with self.subTest(scale=scale):
                a, b = self._adjacent(100, scale)
                self.assertFalse(propositions_are_identical(a, b), f"{scale}: {a!r} vs {b!r}")

    def test_large_decimal_fractions_remain_distinct(self):
        a = "the rate was 123456789012345678901234567890.123456 percent"
        b = "the rate was 123456789012345678901234567890.123457 percent"
        self.assertFalse(propositions_are_identical(a, b))

    def test_exact_scaling_matches_manual_multiplication(self):
        from decimal import Decimal
        from services.comparison.divergence import _scale_exact

        coefficient = Decimal("123456789012345678901234567890")
        for word, multiplier in (
            ("hundred", 100), ("thousand", 1_000), ("million", 1_000_000),
            ("billion", 1_000_000_000), ("trillion", 1_000_000_000_000),
        ):
            with self.subTest(word):
                expected = int(coefficient) * multiplier
                self.assertEqual(int(_scale_exact(coefficient, multiplier)), expected)

    def test_presentation_equivalents_still_match_at_huge_magnitude(self):
        a = "the fund holds $2 trillion"
        b = "the fund holds $2,000,000,000,000"
        self.assertTrue(propositions_are_identical(a, b))

    def test_no_two_distinct_accepted_values_round_to_equal(self):
        """Direct probe of the previously-broken path: multiplying a
        30-digit coefficient by every supported scale must never round."""
        from decimal import Decimal, getcontext
        from services.comparison.divergence import _scale_exact

        self.assertEqual(getcontext().prec, 28, "ambient context assumed default for this test")
        coeff_a = Decimal("1" * 30)
        coeff_b = Decimal("1" * 29 + "2")
        for _, multiplier in (
            ("hundred", 100), ("thousand", 1_000), ("million", 1_000_000),
            ("billion", 1_000_000_000), ("trillion", 1_000_000_000_000),
        ):
            self.assertNotEqual(_scale_exact(coeff_a, multiplier), _scale_exact(coeff_b, multiplier))


class B02TypedIdentityInjectionTests(unittest.TestCase):
    """B-02: raw source text must never impersonate a numeric identity token."""

    def test_injection_using_whatever_the_diagnostic_rendering_CURRENTLY_produces(self):
        """Format-independent version of the injection attack: rather than
        hardcoding a guess at canonical_proposition's marker syntax (which
        could silently drift and stop testing anything real — verified this
        happened once already: a mutation that made identity compare
        RENDERED STRINGS passed cleanly against the guillemet-based tests
        below, because the live rendering format had since changed to
        square brackets), this discovers the current format by calling
        canonical_proposition itself and embeds exactly that text. This test
        must fail identity regardless of what canonical_proposition's syntax
        happens to be today or after any future change to it."""
        rendered = canonical_proposition("1000")
        fake = f"the value is {rendered}"
        real = "the value is 1000"
        self.assertFalse(propositions_are_identical(real, fake), f"rendered marker was {rendered!r}")

    def test_literal_marker_text_does_not_equal_a_real_number(self):
        self.assertFalse(propositions_are_identical("1000", "«num:x1000»"))

    def test_literal_currency_marker_text_does_not_equal_a_real_currency(self):
        self.assertFalse(propositions_are_identical("$2 million", "«currency:x2000000»"))

    def test_multiple_injected_fake_markers_do_not_establish_identity(self):
        a = "the total is 1000 and the rate is 12%"
        b = "the total is «num:x1000» and the rate is «percent:x12»"
        self.assertFalse(propositions_are_identical(a, b))

    def test_nested_fake_marker_text_does_not_establish_identity(self):
        a = "the count reached 12345678"
        b = "the count reached «num:x«num:x12345678»»"
        self.assertFalse(propositions_are_identical(a, b))

    def test_fake_marker_embedded_alongside_the_real_matching_number_still_differs(self):
        # Same real number present in both, but b also carries extra fake
        # marker text — token sequences must still differ in length/content.
        a = "the fund holds $2,000,000"
        b = "the fund holds $2,000,000 «currency:x2000000»"
        self.assertFalse(propositions_are_identical(a, b))

    def test_diagnostic_rendering_is_not_load_bearing_and_not_reused_for_comparison(self):
        """canonical_proposition may legitimately render two non-identical
        propositions to visually similar strings — that is fine, because
        nothing compares its output. Only canonical_identity_key is load-bearing."""
        a = "1000"
        b = "«num:x1000»"
        self.assertFalse(propositions_are_identical(a, b))
        # The diagnostic renderer is still internally idempotent (documented,
        # not a safety requirement) — verify that property holds too.
        once = canonical_proposition(a)
        twice = canonical_proposition(once)
        self.assertEqual(once, twice)

    def test_role_swaps_remain_different_under_typed_identity(self):
        self.assertFalse(propositions_are_identical(
            "injured 12 and killed 40", "injured 40 and killed 12"))
        self.assertFalse(propositions_are_identical(
            "moved Tuesday to Thursday", "moved Thursday to Tuesday"))

    def test_formatting_equivalent_real_numbers_still_match_under_typed_identity(self):
        self.assertTrue(propositions_are_identical("$2 million", "$2,000,000"))
        self.assertTrue(propositions_are_identical("12%", "12 percent"))

    def test_marker_injection_cannot_ground_a_material_omission_with_divergence_disabled(self):
        """End-to-end: even with detect_divergence forced to a no-op, injected
        marker text must not let a fabricated proposition pass the identity
        gate and support a Material Omission."""
        import services.comparison.claims as claims_module

        original = claims_module.detect_divergence
        claims_module.detect_divergence = lambda a, b: []
        try:
            target = [claim("ct", "the town budget passed unanimously", "sentinel", "art-sn")]
            comparison_set = ComparisonSet(
                comparison_set_id="cs", target_article_id="art-sn",
                member_article_ids=("art-tw", "art-pj"), provenance_kind="retrieved",
                source_of_article={"art-tw": "techwire", "art-pj": "policy"},
                dependencies=(SourceDependency(("techwire", "policy"), "independent_reporting", "High"),),
            )
            supporting = [
                claim("f1", "the fund contains «currency:x2000000»", "techwire", "art-tw"),
                claim("f2", "the fund contains «currency:x2000000»", "policy", "art-pj"),
            ]
            with self.assertRaises(OmissionRejection) as ctx:
                evaluate_candidate_omission(
                    comparison_set=comparison_set,
                    candidate_proposition="the fund contains $2,000,000",
                    supporting_claims=supporting, target_claims=target,
                    dimension="Scale", target_published_at="2026-07-12T10:00:00Z",
                    knowable_at="2026-07-10T09:00:00Z", rationale="x",
                )
            self.assertEqual(ctx.exception.gate, "presence_elsewhere")
        finally:
            claims_module.detect_divergence = original


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

    def test_presence_disagreement_cannot_auto_merge(self):
        """C-02: one annotator proposing a finding the other did NOT propose is
        a presence disagreement (ADJUDICATION.md §3) and requires adjudication.

        This previously passed: the grounding check accepted a gold annotation
        that matched ANY ONE proposal fingerprint, which silently promoted a
        single annotator's opinion to consensus gold."""
        annotation = self._annotation()
        doc = self._document(
            annotations=[annotation],
            annotatorSubmissions=[
                self._submission("annotator-a", proposals=[self._proposal("annotator-a", annotation)]),
                self._submission("annotator-b", proposals=[]),
            ],
        )
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("no machine-readable provenance" in e for e in report.errors), report.errors)

    def test_presence_disagreement_is_valid_once_adjudicated(self):
        annotation = self._annotation()
        doc = self._document(
            annotations=[annotation],
            annotatorSubmissions=[
                self._submission("annotator-a", proposals=[self._proposal("annotator-a", annotation)]),
                self._submission("annotator-b", proposals=[]),
            ],
            resolutions=[{
                "decision": "uphold_a", "adjudicatorId": "adjudicator-c",
                "proposalIds": ["p-annotator-a"],
                "resultingAnnotationIds": [annotation["annotationId"]],
            }],
        )
        report = self._validate(doc)
        self.assertTrue(report.valid, report.errors)

    def test_unexplained_positive_gold_after_two_empty_submissions_is_rejected(self):
        """B-04: a gold annotation with no matching proposal and no resolution
        record is ungrounded — a third-party adjudicator may not silently add
        a finding neither annotator proposed."""
        annotation = self._annotation()
        doc = self._document(
            annotations=[annotation],
            annotatorSubmissions=[
                self._submission("annotator-a", proposals=[]),
                self._submission("annotator-b", proposals=[]),
            ],
        )
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("no machine-readable provenance" in e for e in report.errors), report.errors)

    def test_explicit_adjudicator_add_resolution_grounds_unproposed_positive_gold(self):
        """B-04 policy: an adjudicator MAY add an unproposed finding, but only
        via an explicit adjudicator_add resolution naming who and why."""
        annotation = self._annotation()
        doc = self._document(
            annotations=[annotation],
            annotatorSubmissions=[
                self._submission("annotator-a", proposals=[]),
                self._submission("annotator-b", proposals=[]),
            ],
            resolutions=[{
                "decision": "adjudicator_add",
                "adjudicatorId": "adjudicator-c",
                "resultingAnnotationIds": [annotation["annotationId"]],
                "proposalIds": [],
                "note": "Adjudicator independently identified this span during final review.",
            }],
        )
        report = self._validate(doc)
        self.assertTrue(report.valid, report.errors)

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

    def test_proposal_cross_document_mechanism_is_rejected(self):
        doc = self._document(annotatorSubmissions=[
            self._submission("annotator-a", proposals=[
                self._proposal("annotator-a", mechanismId="material_omission")]),
            self._submission("annotator-b", proposals=[]),
        ])
        self.assertFalse(self._validate(doc).valid)

    def _malformed_proposal_doc(self, **over):
        return self._document(annotatorSubmissions=[
            self._submission("annotator-a", proposals=[self._proposal("annotator-a", **over)]),
            self._submission("annotator-b", proposals=[]),
        ])

    # B-03: one regression per malformed proposal shape from the audit's
    # explicit attack list. Every case must be rejected — none may silently
    # skip validation because a field has the wrong type.

    def test_proposal_id_not_string_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(proposalId=123)).valid)

    def test_proposal_id_empty_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(proposalId="")).valid)

    def test_proposal_ordinal_bool_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(passageOrdinal=True)).valid)

    def test_proposal_ordinal_string_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(passageOrdinal="0")).valid)

    def test_proposal_ordinal_negative_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(passageOrdinal=-1)).valid)

    def test_proposal_ordinal_nonexistent_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(passageOrdinal=999)).valid)

    def test_proposal_start_char_bool_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(startChar=True)).valid)

    def test_proposal_end_char_bool_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(endChar=True)).valid)

    def test_proposal_start_char_string_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(startChar="23")).valid)

    def test_proposal_end_char_string_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(endChar="49")).valid)

    def test_proposal_negative_start_char_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(startChar=-1)).valid)

    def test_proposal_end_not_greater_than_start_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(startChar=30, endChar=30)).valid)

    def test_proposal_end_exceeds_passage_length_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(endChar=9999)).valid)

    def test_proposal_excerpt_non_string_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(excerpt=12345)).valid)

    def test_proposal_invalid_pressure_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(pressure="P9")).valid)

    def test_proposal_invalid_reviewer_confidence_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(reviewerConfidence="Certain")).valid)

    def test_proposal_invalid_voice_class_is_rejected(self):
        self.assertFalse(self._validate(self._malformed_proposal_doc(voiceClass="publisher")).valid)

    def test_resolution_referencing_unknown_proposal_is_rejected(self):
        doc = self._document(resolutions=[{
            "decision": "drop", "adjudicatorId": "adjudicator-c", "proposalIds": ["nonexistent-proposal"],
        }])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("unknown proposalId" in e for e in report.errors))

    def test_ghost_proposal_reference_is_rejected_even_when_no_real_proposals_exist(self):
        """B-04 root cause: `if proposal_ids and pid not in proposal_ids` let a
        ghost reference through whenever proposal_ids was EMPTY. Reproduce that
        exact precondition — two zero-proposal submissions — and confirm the
        ghost reference is still caught."""
        doc = self._document(
            annotations=[],
            annotatorSubmissions=[
                self._submission("annotator-a", proposals=[]),
                self._submission("annotator-b", proposals=[]),
            ],
            resolutions=[{
                "decision": "drop", "adjudicatorId": "adjudicator-c", "proposalIds": ["ghost-proposal"],
            }],
        )
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("unknown proposalId" in e for e in report.errors), report.errors)

    def test_resolution_referencing_unknown_gold_annotation_is_rejected(self):
        doc = self._document(resolutions=[{
            "decision": "uphold_a", "adjudicatorId": "adjudicator-c",
            "proposalIds": ["p-annotator-a"], "resultingAnnotationIds": ["ghost-annotation"],
        }])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("references unknown gold annotation" in e for e in report.errors))

    def test_drop_resolution_with_a_resulting_annotation_is_rejected(self):
        doc = self._document(resolutions=[{
            "decision": "drop", "adjudicatorId": "adjudicator-c",
            "proposalIds": ["p-annotator-b"], "resultingAnnotationIds": ["a1"],
        }])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(
            any("allows at most 0 resulting gold" in e for e in report.errors), report.errors)

    def test_removed_singular_resulting_annotation_id_is_rejected(self):
        """C-03: the singular field cannot represent a `split`, which produces
        more than one gold annotation. It is rejected outright rather than
        silently ignored, so an old-format record can never look grounded."""
        doc = self._document(resolutions=[{
            "decision": "uphold_a", "adjudicatorId": "adjudicator-c",
            "proposalIds": ["p-annotator-a"], "resultingAnnotationId": "a1",
        }])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("removed singular" in e for e in report.errors), report.errors)

    def test_duplicate_resolution_id_is_rejected(self):
        doc = self._document(resolutions=[
            {"resolutionId": "res-1", "decision": "drop", "adjudicatorId": "adjudicator-c",
             "proposalIds": ["p-annotator-b"]},
            {"resolutionId": "res-1", "decision": "drop", "adjudicatorId": "adjudicator-c",
             "proposalIds": ["p-annotator-a"]},
        ])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("duplicate resolutionId" in e for e in report.errors))

    def test_resolution_missing_adjudicator_id_is_rejected(self):
        doc = self._document(resolutions=[{"decision": "drop", "proposalIds": ["p-annotator-b"]}])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("adjudicatorId" in e for e in report.errors))

    def test_resolutions_field_wrong_type_is_rejected_cleanly(self):
        """Fresh-sweep finding: `data.get('resolutions', []) or []` type-confused
        a non-empty string into an iterable of records — enumerate() over a
        string yields characters, producing one bogus error per character
        instead of a single clear type error."""
        doc = self._document(resolutions="not a list")
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertEqual(report.errors, ["resolutions must be an array"])

    def test_adjudicator_add_with_nonempty_proposal_ids_is_rejected(self):
        annotation = self._annotation()
        doc = self._document(annotations=[annotation], resolutions=[{
            "decision": "adjudicator_add", "adjudicatorId": "adjudicator-c",
            "resultingAnnotationIds": [annotation["annotationId"]],
            "proposalIds": ["p-annotator-a"], "note": "should not claim a proposal origin",
        }])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("allows at most 0 proposalId" in e for e in report.errors), report.errors)

    def test_adjudicator_add_without_note_is_rejected(self):
        annotation = self._annotation()
        doc = self._document(annotations=[annotation], resolutions=[{
            "decision": "adjudicator_add", "adjudicatorId": "adjudicator-c",
            "resultingAnnotationIds": [annotation["annotationId"]], "proposalIds": [],
        }])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("requires a non-empty note or rationale" in e for e in report.errors))

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
            # C-02: the annotators disagree on mechanism, pressure AND voice, so
            # this is emphatically not an auto-merge — it needs an adjudicator
            # decision, which is exactly what makes the disagreement recoverable.
            resolutions=[{
                "decision": "uphold_a", "adjudicatorId": "adjudicator-c",
                "proposalIds": ["p-annotator-a"],
                "resultingAnnotationIds": [annotation_a["annotationId"]],
            }],
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


class C02AutoMergeConsensusTests(unittest.TestCase):
    """C-02: auto-merge without a resolution is TWO-ANNOTATOR CONSENSUS.

    Gold matching one proposal fingerprint proves only that one annotator
    proposed it. ADJUDICATION.md §2 requires agreement on mechanism, passage,
    pressure and voice with span IoU >= 0.8, and §3 escalates everything else.
    """

    TEXT = "The council approved a draconian, reckless scheme on Tuesday."
    SPAN = "draconian, reckless scheme"

    def _p(self, who, **over):
        start = self.TEXT.index(self.SPAN)
        base = {
            "proposalId": f"p-{who}", "mechanismId": "loaded_language", "passageOrdinal": 0,
            "startChar": start, "endChar": start + len(self.SPAN),
            "pressure": "P3", "reviewerConfidence": "High", "voiceClass": "reporter",
        }
        base.update(over)
        base["excerpt"] = self.TEXT[base["startChar"]:base["endChar"]]
        return base

    def _a(self, **over):
        start = self.TEXT.index(self.SPAN)
        base = {
            "annotationId": "a1", "mechanismId": "loaded_language", "passageOrdinal": 0,
            "startChar": start, "endChar": start + len(self.SPAN),
            "pressure": "P3", "reviewerConfidence": "High", "voiceClass": "reporter",
        }
        base.update(over)
        base["excerpt"] = self.TEXT[base["startChar"]:base["endChar"]]
        return base

    def _doc(self, submissions, annotations, resolutions=None, annotator_ids=None):
        doc = {
            "articleId": "t1", "genre": "straight_news",
            "taxonomyVersion": vocab.taxonomy_version(), "adjudicationStatus": "adjudicated",
            "annotatorIds": annotator_ids or ["annotator-a", "annotator-b"],
            "passages": [{"ordinal": 0, "passageType": "paragraph", "text": self.TEXT}],
            "annotations": annotations,
            "annotatorSubmissions": submissions,
        }
        if resolutions is not None:
            doc["resolutions"] = resolutions
        return doc

    def _sub(self, who, proposals):
        return {"submissionId": f"sub-{who}", "annotatorId": who, "proposals": proposals}

    def _validate(self, document):
        from validate_corpus import validate_document
        return validate_document(document, path="t.json", expected_taxonomy=vocab.taxonomy_version())

    def test_identical_proposals_from_two_annotators_auto_merge(self):
        doc = self._doc(
            [self._sub("annotator-a", [self._p("annotator-a")]),
             self._sub("annotator-b", [self._p("annotator-b")])],
            [self._a()],
        )
        self.assertTrue(self._validate(doc).valid, self._validate(doc).errors)

    def test_presence_disagreement_requires_adjudication(self):
        doc = self._doc(
            [self._sub("annotator-a", [self._p("annotator-a")]),
             self._sub("annotator-b", [])],
            [self._a()],
        )
        self.assertFalse(self._validate(doc).valid)

    def test_pressure_disagreement_cannot_auto_merge(self):
        doc = self._doc(
            [self._sub("annotator-a", [self._p("annotator-a", pressure="P2")]),
             self._sub("annotator-b", [self._p("annotator-b", pressure="P4")])],
            [self._a(pressure="P2")],
        )
        self.assertFalse(self._validate(doc).valid)

    def test_voice_disagreement_cannot_auto_merge(self):
        doc = self._doc(
            [self._sub("annotator-a", [self._p("annotator-a", voiceClass="reporter")]),
             self._sub("annotator-b", [self._p("annotator-b", voiceClass="quoted_speaker")])],
            [self._a()],
        )
        self.assertFalse(self._validate(doc).valid)

    def test_mechanism_disagreement_cannot_auto_merge(self):
        doc = self._doc(
            [self._sub("annotator-a", [self._p("annotator-a")]),
             self._sub("annotator-b", [self._p("annotator-b", mechanismId="presupposition")])],
            [self._a()],
        )
        self.assertFalse(self._validate(doc).valid)

    def test_iou_above_threshold_merges_to_the_intersection(self):
        end = self.TEXT.index(self.SPAN) + len(self.SPAN)
        doc = self._doc(
            [self._sub("annotator-a", [self._p("annotator-a")]),
             self._sub("annotator-b", [self._p("annotator-b", endChar=end + 3)])],
            [self._a()],  # gold == intersection == annotator-a's narrower span
        )
        self.assertTrue(self._validate(doc).valid, self._validate(doc).errors)

    def test_gold_that_is_not_the_intersection_is_rejected(self):
        end = self.TEXT.index(self.SPAN) + len(self.SPAN)
        doc = self._doc(
            [self._sub("annotator-a", [self._p("annotator-a")]),
             self._sub("annotator-b", [self._p("annotator-b", endChar=end + 3)])],
            [self._a(endChar=end + 3)],  # gold == the WIDER span, not the intersection
        )
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("intersection" in e for e in report.errors), report.errors)

    def test_iou_below_threshold_cannot_auto_merge(self):
        end = self.TEXT.index(self.SPAN) + len(self.SPAN)
        doc = self._doc(
            [self._sub("annotator-a", [self._p("annotator-a")]),
             self._sub("annotator-b", [self._p("annotator-b", endChar=end + 30)])],
            [self._a()],
        )
        self.assertFalse(self._validate(doc).valid)

    def test_only_one_preserved_proposal_cannot_auto_merge(self):
        doc = self._doc(
            [self._sub("annotator-a", [self._p("annotator-a")]),
             self._sub("annotator-b", [])],
            [self._a()],
        )
        self.assertFalse(self._validate(doc).valid)

    def test_three_annotator_consensus_uses_intersection_over_all(self):
        """Explicit policy for >2 annotators: every matching proposal joins the
        agreeing set, all pairs must clear the IoU bar, and the merged span is
        the intersection over the whole set."""
        start = self.TEXT.index(self.SPAN)
        end = start + len(self.SPAN)
        doc = self._doc(
            [self._sub("annotator-a", [self._p("annotator-a")]),
             self._sub("annotator-b", [self._p("annotator-b", endChar=end + 2)]),
             self._sub("annotator-c", [self._p("annotator-c", startChar=start - 1)])],
            [self._a()],  # intersection: max start, min end -> annotator-a's span
            annotator_ids=["annotator-a", "annotator-b", "annotator-c"],
        )
        self.assertTrue(self._validate(doc).valid, self._validate(doc).errors)

    def test_span_iou_helper_is_correct(self):
        from validate_corpus import _span_iou

        self.assertEqual(_span_iou((0, 10), (0, 10)), 1.0)
        self.assertEqual(_span_iou((0, 10), (10, 20)), 0.0)   # touching, no overlap
        self.assertEqual(_span_iou((0, 10), (20, 30)), 0.0)   # disjoint
        self.assertAlmostEqual(_span_iou((0, 10), (0, 20)), 0.5)


class C03ResolutionCardinalityTests(unittest.TestCase):
    """C-03: each decision has a deterministic proposal/result cardinality.

    Without this, `merge` with an empty `proposalIds` grounded arbitrary gold
    with no proposal origin — a silent backdoor around `adjudicator_add`.
    """

    def _validate(self, document):
        from validate_corpus import validate_document
        return validate_document(document, path="t.json", expected_taxonomy=vocab.taxonomy_version())

    TEXT = "The council approved a draconian, reckless scheme on Tuesday."
    SPAN = "draconian, reckless scheme"

    def _p(self, pid, **over):
        start = self.TEXT.index(self.SPAN)
        base = {
            "proposalId": pid, "mechanismId": "loaded_language", "passageOrdinal": 0,
            "startChar": start, "endChar": start + len(self.SPAN),
            "pressure": "P3", "reviewerConfidence": "High", "voiceClass": "reporter",
        }
        base.update(over)
        base["excerpt"] = self.TEXT[base["startChar"]:base["endChar"]]
        return base

    def _a(self, aid="a1", **over):
        start = self.TEXT.index(self.SPAN)
        base = {
            "annotationId": aid, "mechanismId": "loaded_language", "passageOrdinal": 0,
            "startChar": start, "endChar": start + len(self.SPAN),
            "pressure": "P3", "reviewerConfidence": "High", "voiceClass": "reporter",
        }
        base.update(over)
        base["excerpt"] = self.TEXT[base["startChar"]:base["endChar"]]
        return base

    def _doc(self, submissions, annotations, resolutions):
        return {
            "articleId": "t1", "genre": "straight_news",
            "taxonomyVersion": vocab.taxonomy_version(), "adjudicationStatus": "adjudicated",
            "annotatorIds": ["annotator-a", "annotator-b"],
            "passages": [{"ordinal": 0, "passageType": "paragraph", "text": self.TEXT}],
            "annotations": annotations,
            "annotatorSubmissions": submissions,
            "resolutions": resolutions,
        }

    def _sub(self, who, proposals):
        return {"submissionId": f"sub-{who}", "annotatorId": who, "proposals": proposals}

    def _both_empty(self):
        return [self._sub("annotator-a", []), self._sub("annotator-b", [])]

    def _one_each(self):
        return [self._sub("annotator-a", [self._p("p1")]),
                self._sub("annotator-b", [self._p("p2")])]

    def test_merge_with_empty_proposal_ids_is_rejected(self):
        doc = self._doc(self._both_empty(), [self._a()], [{
            "decision": "merge", "adjudicatorId": "c",
            "proposalIds": [], "resultingAnnotationIds": ["a1"]}])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("requires at least 2 proposalId" in e for e in report.errors), report.errors)

    def test_uphold_with_empty_proposal_ids_is_rejected(self):
        doc = self._doc(self._both_empty(), [self._a()], [{
            "decision": "uphold_a", "adjudicatorId": "c",
            "proposalIds": [], "resultingAnnotationIds": ["a1"]}])
        self.assertFalse(self._validate(doc).valid)

    def test_drop_with_empty_proposal_ids_is_rejected(self):
        doc = self._doc(self._both_empty(), [], [{
            "decision": "drop", "adjudicatorId": "c",
            "proposalIds": [], "resultingAnnotationIds": []}])
        self.assertFalse(self._validate(doc).valid)

    def test_merge_from_a_single_annotator_is_rejected(self):
        doc = self._doc(
            [self._sub("annotator-a", [self._p("p1"), self._p("p2", startChar=4, endChar=11)]),
             self._sub("annotator-b", [])],
            [self._a()],
            [{"decision": "merge", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["a1"]}])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("distinct annotator" in e for e in report.errors), report.errors)

    def test_valid_merge_from_two_annotators(self):
        """A real merge is one the annotators could NOT auto-merge — here they
        disagree on pressure, so the adjudicator reconciles. (Identical
        proposals would already be an auto-merge, and layering a resolution on
        top of that is conflicting provenance under D-03, not a valid merge.)"""
        end = self.TEXT.index(self.SPAN) + len(self.SPAN)
        doc = self._doc(
            [self._sub("annotator-a", [self._p("p1", pressure="P2")]),
             self._sub("annotator-b", [self._p("p2", pressure="P4", endChar=end + 4)])],
            [self._a(pressure="P3")],
            [{"decision": "merge", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["a1"]}])
        self.assertTrue(self._validate(doc).valid, self._validate(doc).errors)

    def test_split_with_one_result_is_rejected(self):
        doc = self._doc(self._one_each(), [self._a()], [{
            "decision": "split", "adjudicatorId": "c",
            "proposalIds": ["p1"], "resultingAnnotationIds": ["a1"]}])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("requires at least 2 resulting" in e for e in report.errors), report.errors)

    def test_split_with_zero_results_is_rejected(self):
        doc = self._doc(self._one_each(), [self._a()], [{
            "decision": "split", "adjudicatorId": "c",
            "proposalIds": ["p1"], "resultingAnnotationIds": []}])
        self.assertFalse(self._validate(doc).valid)

    def test_valid_split_produces_two_gold_annotations(self):
        """D-01: both results must stay inside the source region — a split
        divides the cited span, it does not create findings elsewhere."""
        start = self.TEXT.index(self.SPAN)
        end = start + len(self.SPAN)
        doc = self._doc(
            [self._sub("annotator-a", [self._p("p1")]), self._sub("annotator-b", [])],
            [self._a(endChar=start + 9),
             self._a(aid="a2", startChar=start + 11, endChar=end, mechanismId="presupposition")],
            [{"decision": "split", "adjudicatorId": "c",
              "proposalIds": ["p1"], "resultingAnnotationIds": ["a1", "a2"]}])
        self.assertTrue(self._validate(doc).valid, self._validate(doc).errors)

    def test_valid_drop_grounds_nothing(self):
        doc = self._doc(
            [self._sub("annotator-a", [self._p("p1")]), self._sub("annotator-b", [])],
            [],
            [{"decision": "drop", "adjudicatorId": "c",
              "proposalIds": ["p1"], "resultingAnnotationIds": []}])
        self.assertTrue(self._validate(doc).valid, self._validate(doc).errors)

    def test_valid_adjudicator_add(self):
        doc = self._doc(self._both_empty(), [self._a()], [{
            "decision": "adjudicator_add", "adjudicatorId": "c", "proposalIds": [],
            "resultingAnnotationIds": ["a1"], "note": "adjudicator saw it on final review"}])
        self.assertTrue(self._validate(doc).valid, self._validate(doc).errors)

    def test_two_resolutions_cannot_claim_the_same_gold_annotation(self):
        """Isolates the duplicate-provenance case: the two proposals disagree on
        pressure, so there is no auto-merge origin competing for the error and
        the failure must be the duplicate link itself."""
        doc = self._doc(
            [self._sub("annotator-a", [self._p("p1", pressure="P2")]),
             self._sub("annotator-b", [self._p("p2", pressure="P4")])],
            [self._a(pressure="P2")], [
                {"decision": "uphold_a", "adjudicatorId": "c",
                 "proposalIds": ["p1"], "resultingAnnotationIds": ["a1"]},
                {"decision": "uphold_b", "adjudicatorId": "c",
                 "proposalIds": ["p2"], "resultingAnnotationIds": ["a1"]}])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("claimed by 2 resolutions" in e for e in report.errors), report.errors)

    def test_duplicate_ids_within_one_resolution_are_rejected(self):
        doc = self._doc(self._one_each(), [self._a(), self._a(aid="a2", startChar=4, endChar=11)], [{
            "decision": "split", "adjudicatorId": "c",
            "proposalIds": ["p1"], "resultingAnnotationIds": ["a1", "a1"]}])
        report = self._validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("more than once" in e for e in report.errors), report.errors)

    def test_cardinality_table_covers_every_gold_producing_decision(self):
        from validate_corpus import RESOLUTION_CARDINALITY, VALID_RESOLUTION_DECISIONS

        # `unresolvable` is rejected outright in an adjudicated document, so it
        # deliberately has no cardinality entry.
        self.assertEqual(
            set(RESOLUTION_CARDINALITY) | {"unresolvable"}, VALID_RESOLUTION_DECISIONS)


class _CorpusProvenanceFixture(unittest.TestCase):
    """Shared fixture for the D-01/D-02/D-03 provenance closure.

    The passage carries two clearly distinct rhetorical regions so an attack
    can point a resolution at gold that has nothing to do with its sources.
    """

    TEXT = ("The council approved a draconian, reckless scheme on Tuesday "
            "or watch the district collapse entirely.")
    LOADED = "draconian, reckless scheme"
    DILEMMA = "watch the district collapse"

    @property
    def LS(self):
        return self.TEXT.index(self.LOADED)

    @property
    def LE(self):
        return self.LS + len(self.LOADED)

    @property
    def FS(self):
        return self.TEXT.index(self.DILEMMA)

    @property
    def FE(self):
        return self.FS + len(self.DILEMMA)

    def p(self, pid, **over):
        base = {
            "proposalId": pid, "mechanismId": "loaded_language", "passageOrdinal": 0,
            "startChar": self.LS, "endChar": self.LE,
            "pressure": "P3", "reviewerConfidence": "High", "voiceClass": "reporter",
        }
        base.update(over)
        base["excerpt"] = self.TEXT[base["startChar"]:base["endChar"]]
        return base

    def a(self, aid="a1", **over):
        base = {
            "annotationId": aid, "mechanismId": "loaded_language", "passageOrdinal": 0,
            "startChar": self.LS, "endChar": self.LE,
            "pressure": "P3", "reviewerConfidence": "High", "voiceClass": "reporter",
        }
        base.update(over)
        base["excerpt"] = self.TEXT[base["startChar"]:base["endChar"]]
        return base

    def sub(self, who, proposals):
        return {"submissionId": f"sub-{who}", "annotatorId": who, "proposals": proposals}

    def doc(self, submissions, annotations, resolutions=None, annotator_ids=None):
        document = {
            "articleId": "t1", "genre": "straight_news",
            "taxonomyVersion": vocab.taxonomy_version(), "adjudicationStatus": "adjudicated",
            "annotatorIds": annotator_ids if annotator_ids is not None else ["a", "b"],
            "passages": [{"ordinal": 0, "passageType": "paragraph", "text": self.TEXT}],
            "annotations": annotations,
            "annotatorSubmissions": submissions,
        }
        if resolutions is not None:
            document["resolutions"] = resolutions
        return document

    def validate(self, document):
        from validate_corpus import validate_document
        return validate_document(document, path="t.json", expected_taxonomy=vocab.taxonomy_version())


class D01SemanticResolutionGroundingTests(_CorpusProvenanceFixture):
    """D-01: a resolution must be shown to DERIVE its gold from the proposals
    it cites. Cardinality and reference-existence only prove it points at real
    records — not that the result has anything to do with them.
    """

    def test_false_uphold_producing_a_different_finding_is_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1")]), self.sub("b", [])],
            [self.a(mechanismId="false_dilemma", startChar=self.FS, endChar=self.FE)],
            [{"decision": "uphold_a", "adjudicatorId": "c",
              "proposalIds": ["p1"], "resultingAnnotationIds": ["a1"]}])
        report = self.validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("does not substitute a different finding" in e for e in report.errors),
                        report.errors)

    def test_uphold_differing_only_in_pressure_is_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1")]), self.sub("b", [])],
            [self.a(pressure="P1")],
            [{"decision": "uphold_a", "adjudicatorId": "c",
              "proposalIds": ["p1"], "resultingAnnotationIds": ["a1"]}])
        self.assertFalse(self.validate(doc).valid)

    def test_uphold_may_differ_in_reviewer_confidence(self):
        """reviewerConfidence is a per-annotator epistemic report, not a
        property of the phenomenon being upheld."""
        doc = self.doc(
            [self.sub("a", [self.p("p1", reviewerConfidence="Low")]), self.sub("b", [])],
            [self.a(reviewerConfidence="High")],
            [{"decision": "uphold_a", "adjudicatorId": "c",
              "proposalIds": ["p1"], "resultingAnnotationIds": ["a1"]}])
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_valid_uphold_preserving_the_proposal_exactly(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1")]), self.sub("b", [])],
            [self.a()],
            [{"decision": "uphold_a", "adjudicatorId": "c",
              "proposalIds": ["p1"], "resultingAnnotationIds": ["a1"]}])
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_false_merge_producing_an_unrelated_mechanism_is_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", pressure="P2")]),
             self.sub("b", [self.p("p2", pressure="P4")])],
            [self.a(mechanismId="presupposition", startChar=self.FS, endChar=self.FE)],
            [{"decision": "merge", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["a1"]}])
        self.assertFalse(self.validate(doc).valid)

    def test_merge_relocating_the_finding_is_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", pressure="P2")]),
             self.sub("b", [self.p("p2", pressure="P4")])],
            [self.a(pressure="P3", startChar=0, endChar=11)],
            [{"decision": "merge", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["a1"]}])
        report = self.validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(
            any("does not overlap the common source intersection" in e for e in report.errors),
            report.errors)

    def test_merge_of_different_mechanisms_is_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", pressure="P2")]),
             self.sub("b", [self.p("p2", pressure="P4", mechanismId="presupposition")])],
            [self.a(pressure="P3")],
            [{"decision": "merge", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["a1"]}])
        self.assertFalse(self.validate(doc).valid)

    def test_valid_merge_reconciles_a_real_disagreement(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", pressure="P2")]),
             self.sub("b", [self.p("p2", pressure="P4", endChar=self.LE + 4)])],
            [self.a(pressure="P3")],
            [{"decision": "merge", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["a1"]}])
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_false_split_producing_findings_elsewhere_is_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1")]), self.sub("b", [])],
            [self.a(startChar=self.FS, endChar=self.FE, mechanismId="false_dilemma"),
             self.a(aid="a2", startChar=0, endChar=11, mechanismId="presupposition")],
            [{"decision": "split", "adjudicatorId": "c",
              "proposalIds": ["p1"], "resultingAnnotationIds": ["a1", "a2"]}])
        report = self.validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(
            any("not wholly contained in any connected cited-source coverage" in e for e in report.errors),
            report.errors)

    def test_valid_split_divides_the_source_region(self):
        """A split MAY yield different mechanismIds — it may not relocate."""
        doc = self.doc(
            [self.sub("a", [self.p("p1")]), self.sub("b", [])],
            [self.a(endChar=self.LS + 9),
             self.a(aid="a2", startChar=self.LS + 11, endChar=self.LE, mechanismId="presupposition")],
            [{"decision": "split", "adjudicatorId": "c",
              "proposalIds": ["p1"], "resultingAnnotationIds": ["a1", "a2"]}])
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)


class _SpanProvenanceFixture(unittest.TestCase):
    """Two passages with widely separated marked regions (0..10 and 90..100)
    so an attack can place a result in the GAP between real source spans, and
    so identical coordinates exist on two different passages."""

    P0 = "A" * 10 + " " * 79 + "B" * 10 + "  end."
    P1 = "C" * 10 + " " * 79 + "D" * 10 + "  end."

    def _text(self, ordinal):
        return self.P0 if ordinal == 0 else self.P1

    def p(self, pid, ordinal, start, end, mechanism="loaded_language", **over):
        base = {
            "proposalId": pid, "mechanismId": mechanism, "passageOrdinal": ordinal,
            "startChar": start, "endChar": end, "excerpt": self._text(ordinal)[start:end],
            "pressure": "P3", "reviewerConfidence": "High", "voiceClass": "reporter",
        }
        base.update(over)
        return base

    def a(self, aid, ordinal, start, end, mechanism="loaded_language", **over):
        base = {
            "annotationId": aid, "mechanismId": mechanism, "passageOrdinal": ordinal,
            "startChar": start, "endChar": end, "excerpt": self._text(ordinal)[start:end],
            "pressure": "P3", "reviewerConfidence": "High", "voiceClass": "reporter",
        }
        base.update(over)
        return base

    def sub(self, who, proposals):
        return {"submissionId": f"sub-{who}", "annotatorId": who, "proposals": proposals}

    def doc(self, submissions, annotations, resolutions):
        return {
            "articleId": "t1", "genre": "straight_news",
            "taxonomyVersion": vocab.taxonomy_version(), "adjudicationStatus": "adjudicated",
            "annotatorIds": ["a", "b"],
            "passages": [
                {"ordinal": 0, "passageType": "paragraph", "text": self.P0},
                {"ordinal": 1, "passageType": "paragraph", "text": self.P1},
            ],
            "annotations": annotations,
            "annotatorSubmissions": submissions,
            "resolutions": resolutions,
        }

    def validate(self, document):
        from validate_corpus import validate_document
        return validate_document(document, path="t.json", expected_taxonomy=vocab.taxonomy_version())


class E01SplitSpanProvenanceTests(_SpanProvenanceFixture):
    """E-01: split provenance must be per-span and per-passage.

    The previous check built ONE global bounding hull — min(start)..max(end)
    across all sources, ignoring passage — so sources at 0..10 and 90..100
    produced a "region" of 0..100 that blessed an unrelated result at 40..50
    sitting in the gap between them.
    """

    def test_single_source_split_into_two_overlapping_results(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 0, 10)]), self.sub("b", [])],
            [self.a("g1", 0, 0, 5), self.a("g2", 0, 5, 10, mechanism="presupposition")],
            [{"decision": "split", "adjudicatorId": "c",
              "proposalIds": ["p1"], "resultingAnnotationIds": ["g1", "g2"]}])
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_result_in_the_gap_between_disjoint_sources_is_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 0, 10)]), self.sub("b", [self.p("p2", 0, 90, 100)])],
            [self.a("g1", 0, 40, 50), self.a("g2", 0, 0, 10)],
            [{"decision": "split", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["g1", "g2"]}])
        report = self.validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(
            any("not wholly contained in any connected cited-source coverage" in e for e in report.errors),
            report.errors)

    def test_cross_passage_coordinate_collision_is_rejected(self):
        """The hull discarded passage, so coordinates from passage 1 could
        numerically bless a result on passage 0 that overlapped nothing."""
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 0, 10)]), self.sub("b", [self.p("p2", 1, 90, 100)])],
            [self.a("g1", 0, 40, 50), self.a("g2", 0, 0, 10)],
            [{"decision": "split", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["g1", "g2"]}])
        self.assertFalse(self.validate(doc).valid)

    def test_every_result_tied_to_an_actual_source_passes(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 0, 10)]), self.sub("b", [self.p("p2", 0, 90, 100)])],
            [self.a("g1", 0, 0, 10), self.a("g2", 0, 90, 100)],
            [{"decision": "split", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["g1", "g2"]}])
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_cited_proposal_represented_by_no_result_is_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 0, 10)]), self.sub("b", [self.p("p2", 0, 90, 100)])],
            [self.a("g1", 0, 0, 5), self.a("g2", 0, 5, 10, mechanism="presupposition")],
            [{"decision": "split", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["g1", "g2"]}])
        report = self.validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(
            any("no resulting gold annotation overlaps it" in e for e in report.errors),
            report.errors)

    def test_split_may_produce_different_mechanisms(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 0, 10)]), self.sub("b", [])],
            [self.a("g1", 0, 0, 5, mechanism="false_dilemma"),
             self.a("g2", 0, 5, 10, mechanism="presupposition")],
            [{"decision": "split", "adjudicatorId": "c",
              "proposalIds": ["p1"], "resultingAnnotationIds": ["g1", "g2"]}])
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)


class F01SplitContainmentTests(_SpanProvenanceFixture):
    """F-01: split results must be WHOLLY CONTAINED in a connected component of
    the actual cited source coverage on their own passage.

    Overlap is not containment: a source at 50..60 "overlapped" a result of
    0..55, licensing fifty characters of text no annotator ever marked.
    """

    def _split(self, sources, annotations, proposal_ids, result_ids):
        return self.doc(
            [self.sub("a", sources), self.sub("b", [])], annotations,
            [{"decision": "split", "adjudicatorId": "c",
              "proposalIds": proposal_ids, "resultingAnnotationIds": result_ids}])

    def test_coverage_components_merge_overlapping_and_touching_spans(self):
        from validate_corpus import _coverage_components

        self.assertEqual(_coverage_components([(0, 10), (8, 20), (40, 50)]), [(0, 20), (40, 50)])
        self.assertEqual(_coverage_components([(0, 10), (10, 20)]), [(0, 20)])
        self.assertEqual(_coverage_components([(0, 10), (90, 100)]), [(0, 10), (90, 100)])
        self.assertEqual(_coverage_components([]), [])

    def test_results_contained_in_a_single_source_pass(self):
        doc = self._split(
            [self.p("p1", 0, 10, 30)],
            [self.a("g1", 0, 10, 18), self.a("g2", 0, 18, 30, mechanism="presupposition")],
            ["p1"], ["g1", "g2"])
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_results_contained_in_a_connected_two_source_component_pass(self):
        """10..25 and 20..35 connect into 10..35; results inside that pass."""
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 10, 25)]), self.sub("b", [self.p("p2", 0, 20, 35)])],
            [self.a("g1", 0, 10, 22), self.a("g2", 0, 22, 35, mechanism="presupposition")],
            [{"decision": "split", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["g1", "g2"]}])
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_result_extending_before_the_source_is_rejected(self):
        doc = self._split(
            [self.p("p1", 0, 50, 60)],
            [self.a("g1", 0, 0, 55), self.a("g2", 0, 55, 60, mechanism="presupposition")],
            ["p1"], ["g1", "g2"])
        report = self.validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(
            any("not wholly contained in any connected cited-source coverage" in e
                for e in report.errors), report.errors)

    def test_result_extending_after_the_source_is_rejected(self):
        doc = self._split(
            [self.p("p1", 0, 50, 60)],
            [self.a("g1", 0, 50, 55), self.a("g2", 0, 55, 100, mechanism="presupposition")],
            ["p1"], ["g1", "g2"])
        self.assertFalse(self.validate(doc).valid)

    def test_result_bridging_two_disconnected_components_is_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 0, 10)]), self.sub("b", [self.p("p2", 0, 90, 100)])],
            [self.a("g1", 0, 5, 95), self.a("g2", 0, 90, 100, mechanism="presupposition")],
            [{"decision": "split", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["g1", "g2"]}])
        self.assertFalse(self.validate(doc).valid)

    def test_result_in_the_unmarked_gap_is_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 0, 10)]), self.sub("b", [self.p("p2", 0, 90, 100)])],
            [self.a("g1", 0, 40, 50), self.a("g2", 0, 0, 10)],
            [{"decision": "split", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["g1", "g2"]}])
        self.assertFalse(self.validate(doc).valid)

    def test_cross_passage_coordinate_collision_is_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 0, 10)]), self.sub("b", [self.p("p2", 1, 90, 100)])],
            [self.a("g1", 0, 40, 50), self.a("g2", 0, 0, 10)],
            [{"decision": "split", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["g1", "g2"]}])
        self.assertFalse(self.validate(doc).valid)

    def test_cited_proposal_with_no_result_is_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 0, 10)]), self.sub("b", [self.p("p2", 0, 90, 100)])],
            [self.a("g1", 0, 0, 5), self.a("g2", 0, 5, 10, mechanism="presupposition")],
            [{"decision": "split", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["g1", "g2"]}])
        report = self.validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(
            any("no resulting gold annotation overlaps it" in e for e in report.errors),
            report.errors)


class F02DuplicateGoldTests(_SpanProvenanceFixture):
    """F-02: one semantic occurrence produces exactly one gold annotation.

    The semantic key is (passageOrdinal, startChar, endChar, mechanismId).
    Pressure, voice and reviewerConfidence are deliberately excluded: differing
    on them is a disagreement adjudication must resolve down to one gold
    occurrence, not a licence to record the finding twice and have every
    metric count it twice.
    """

    def _add(self, rid, note):
        return {"decision": "adjudicator_add", "adjudicatorId": "c", "proposalIds": [],
                "resultingAnnotationIds": [rid], "note": note}

    def _two_gold(self, g1, g2, resolutions=None):
        return self.doc(
            [self.sub("a", []), self.sub("b", [])], [g1, g2],
            resolutions if resolutions is not None
            else [self._add(g1["annotationId"], "x"), self._add(g2["annotationId"], "y")])

    def test_identical_semantic_key_under_different_ids_is_rejected(self):
        report = self.validate(self._two_gold(self.a("g1", 0, 50, 60), self.a("g2", 0, 50, 60)))
        self.assertFalse(report.valid)
        self.assertTrue(
            any("duplicates the semantic gold key" in e for e in report.errors), report.errors)

    def test_duplicate_differing_only_in_pressure_is_rejected(self):
        doc = self._two_gold(
            self.a("g1", 0, 50, 60, pressure="P2"), self.a("g2", 0, 50, 60, pressure="P4"))
        self.assertFalse(self.validate(doc).valid)

    def test_duplicate_differing_only_in_voice_is_rejected(self):
        doc = self._two_gold(
            self.a("g1", 0, 50, 60, voiceClass="reporter"),
            self.a("g2", 0, 50, 60, voiceClass="quoted_speaker"))
        self.assertFalse(self.validate(doc).valid)

    def test_duplicate_differing_only_in_reviewer_confidence_is_rejected(self):
        doc = self._two_gold(
            self.a("g1", 0, 50, 60, reviewerConfidence="Low"),
            self.a("g2", 0, 50, 60, reviewerConfidence="High"))
        self.assertFalse(self.validate(doc).valid)

    def test_duplicate_produced_through_a_split_is_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 50, 60)]), self.sub("b", [])],
            [self.a("g1", 0, 50, 60), self.a("g2", 0, 50, 60)],
            [{"decision": "split", "adjudicatorId": "c",
              "proposalIds": ["p1"], "resultingAnnotationIds": ["g1", "g2"]}])
        self.assertFalse(self.validate(doc).valid)

    def test_duplicate_produced_through_two_resolutions_is_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 50, 60, pressure="P2")]),
             self.sub("b", [self.p("p2", 0, 50, 60, pressure="P4")])],
            [self.a("g1", 0, 50, 60, pressure="P2"), self.a("g2", 0, 50, 60, pressure="P4")],
            [{"decision": "uphold_a", "adjudicatorId": "c",
              "proposalIds": ["p1"], "resultingAnnotationIds": ["g1"]},
             {"decision": "uphold_b", "adjudicatorId": "c",
              "proposalIds": ["p2"], "resultingAnnotationIds": ["g2"]}])
        self.assertFalse(self.validate(doc).valid)

    def test_duplicate_produced_through_adjudicator_add_records_is_rejected(self):
        self.assertFalse(
            self.validate(self._two_gold(self.a("g1", 0, 50, 60), self.a("g2", 0, 50, 60))).valid)

    def test_same_span_different_mechanisms_is_valid_multi_tagging(self):
        doc = self._two_gold(
            self.a("g1", 0, 50, 60, mechanism="loaded_language"),
            self.a("g2", 0, 50, 60, mechanism="presupposition"))
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_same_mechanism_different_spans_is_valid(self):
        doc = self._two_gold(self.a("g1", 0, 0, 10), self.a("g2", 0, 90, 100))
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_partially_overlapping_occurrences_are_valid(self):
        doc = self._two_gold(self.a("g1", 0, 0, 10), self.a("g2", 0, 5, 15))
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_same_span_and_mechanism_on_different_passages_is_valid(self):
        doc = self._two_gold(self.a("g1", 0, 0, 10), self.a("g2", 1, 0, 10))
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)


class E02MergeSpanProvenanceTests(_SpanProvenanceFixture):
    """E-02: a merge reconciles ONE shared occurrence.

    Overlapping the gold against each source independently was not enough:
    two disjoint findings (0..10 and 90..100) both overlap a bridging gold of
    5..95, so the old check accepted a span swallowing 80 characters of
    unrelated text between them.
    """

    def test_two_overlapping_sources_reconcile(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 0, 10, pressure="P2")]),
             self.sub("b", [self.p("p2", 0, 4, 14, pressure="P4")])],
            [self.a("g1", 0, 4, 10)],
            [{"decision": "merge", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["g1"]}])
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_two_disjoint_sources_cannot_be_merged(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 0, 10, pressure="P2")]),
             self.sub("b", [self.p("p2", 0, 90, 100, pressure="P4")])],
            [self.a("g1", 0, 5, 95)],
            [{"decision": "merge", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["g1"]}])
        report = self.validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("no common overlap" in e for e in report.errors), report.errors)

    def test_three_sources_without_a_common_intersection_are_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 0, 10, pressure="P2"),
                            self.p("p3", 0, 8, 20, pressure="P1")]),
             self.sub("b", [self.p("p2", 0, 15, 25, pressure="P4")])],
            [self.a("g1", 0, 8, 20)],
            [{"decision": "merge", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2", "p3"], "resultingAnnotationIds": ["g1"]}])
        self.assertFalse(self.validate(doc).valid)

    def test_three_sources_with_a_common_intersection_pass(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 0, 12, pressure="P2"),
                            self.p("p3", 0, 2, 14, pressure="P1")]),
             self.sub("b", [self.p("p2", 0, 4, 16, pressure="P4")])],
            [self.a("g1", 0, 4, 12)],
            [{"decision": "merge", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2", "p3"], "resultingAnnotationIds": ["g1"]}])
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_gold_extending_beyond_the_source_hull_is_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", 0, 0, 10, pressure="P2")]),
             self.sub("b", [self.p("p2", 0, 4, 14, pressure="P4")])],
            [self.a("g1", 0, 0, 100)],
            [{"decision": "merge", "adjudicatorId": "c",
              "proposalIds": ["p1", "p2"], "resultingAnnotationIds": ["g1"]}])
        report = self.validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(
            any("extending outside the cited source spans" in e for e in report.errors),
            report.errors)


class AutoMergeOccurrenceLocalityTests(_SpanProvenanceFixture):
    """Non-blocking cleanup: the auto-merge cluster is occurrence-local.

    Matching on mechanism/passage/pressure/voice alone swept in every OTHER
    occurrence of the same mechanism in the same passage, so a passage with two
    distinct P3/reporter loaded_language findings gave each annotator two
    "matching" proposals per gold and was rejected as ambiguous — a false
    ambiguity between findings that were never in competition.
    """

    def test_two_distinct_occurrences_in_one_passage_both_auto_merge(self):
        doc = {
            "articleId": "t1", "genre": "straight_news",
            "taxonomyVersion": vocab.taxonomy_version(), "adjudicationStatus": "adjudicated",
            "annotatorIds": ["a", "b"],
            "passages": [{"ordinal": 0, "passageType": "paragraph", "text": self.P0}],
            "annotations": [self.a("g1", 0, 0, 10), self.a("g2", 0, 90, 100)],
            "annotatorSubmissions": [
                self.sub("a", [self.p("p1", 0, 0, 10), self.p("p2", 0, 90, 100)]),
                self.sub("b", [self.p("p3", 0, 0, 10), self.p("p4", 0, 90, 100)]),
            ],
        }
        report = self.validate(doc)
        self.assertTrue(report.valid, report.errors)

    def test_genuinely_ambiguous_overlapping_proposals_still_escalate(self):
        """Occurrence-locality must not weaken the D-02 ambiguity guard: two
        proposals from the SAME annotator both overlapping the same gold remain
        an unresolvable cluster."""
        doc = {
            "articleId": "t1", "genre": "straight_news",
            "taxonomyVersion": vocab.taxonomy_version(), "adjudicationStatus": "adjudicated",
            "annotatorIds": ["a", "b"],
            "passages": [{"ordinal": 0, "passageType": "paragraph", "text": self.P0}],
            "annotations": [self.a("g1", 0, 0, 10)],
            "annotatorSubmissions": [
                self.sub("a", [self.p("p1", 0, 0, 10), self.p("p2", 0, 2, 10)]),
                self.sub("b", [self.p("p3", 0, 0, 10)]),
            ],
        }
        self.assertFalse(self.validate(doc).valid)


class D02UnanimousAutoMergeTests(_CorpusProvenanceFixture):
    """D-02: auto-merge requires EVERY declared annotator to participate.

    "At least two agreed" silently erased the third annotator's dissent.
    """

    def test_two_of_two_agree_passes(self):
        doc = self.doc([self.sub("a", [self.p("p1")]), self.sub("b", [self.p("p2")])], [self.a()])
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_two_of_two_disagree_fails(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", pressure="P2")]),
             self.sub("b", [self.p("p2", pressure="P4")])],
            [self.a(pressure="P2")])
        self.assertFalse(self.validate(doc).valid)

    def test_three_of_three_agree_passes(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1")]), self.sub("b", [self.p("p2")]), self.sub("c", [self.p("p3")])],
            [self.a()], annotator_ids=["a", "b", "c"])
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_two_agree_one_absent_fails(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1")]), self.sub("b", [self.p("p2")]), self.sub("c", [])],
            [self.a()], annotator_ids=["a", "b", "c"])
        self.assertFalse(self.validate(doc).valid)

    def test_two_agree_one_pressure_dissent_fails(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1")]), self.sub("b", [self.p("p2")]),
             self.sub("c", [self.p("p3", pressure="P4")])],
            [self.a()], annotator_ids=["a", "b", "c"])
        self.assertFalse(self.validate(doc).valid)

    def test_two_agree_one_voice_dissent_fails(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1")]), self.sub("b", [self.p("p2")]),
             self.sub("c", [self.p("p3", voiceClass="quoted_speaker")])],
            [self.a()], annotator_ids=["a", "b", "c"])
        self.assertFalse(self.validate(doc).valid)

    def test_two_agree_one_mechanism_dissent_fails(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1")]), self.sub("b", [self.p("p2")]),
             self.sub("c", [self.p("p3", mechanismId="presupposition")])],
            [self.a()], annotator_ids=["a", "b", "c"])
        self.assertFalse(self.validate(doc).valid)

    def test_three_spans_one_breaking_iou_fails(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1")]), self.sub("b", [self.p("p2")]),
             self.sub("c", [self.p("p3", endChar=self.LE + 30)])],
            [self.a()], annotator_ids=["a", "b", "c"])
        self.assertFalse(self.validate(doc).valid)

    def test_an_annotator_with_two_matching_proposals_is_ambiguous_and_fails(self):
        """An ambiguous cluster cannot be resolved deterministically, so it
        escalates rather than picking one arbitrarily."""
        doc = self.doc(
            [self.sub("a", [self.p("p1"), self.p("p1b", endChar=self.LE + 2)]),
             self.sub("b", [self.p("p2")])],
            [self.a()])
        self.assertFalse(self.validate(doc).valid)


class D03ExactlyOneProvenanceTests(_CorpusProvenanceFixture):
    """D-03: every gold annotation has exactly one recorded origin."""

    def test_auto_merge_with_zero_resolutions_is_valid(self):
        doc = self.doc([self.sub("a", [self.p("p1")]), self.sub("b", [self.p("p2")])], [self.a()])
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_no_auto_merge_with_one_resolution_is_valid(self):
        doc = self.doc(
            [self.sub("a", []), self.sub("b", [])], [self.a()],
            [{"decision": "adjudicator_add", "adjudicatorId": "c", "proposalIds": [],
              "resultingAnnotationIds": ["a1"], "note": "adjudicator saw it"}])
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_neither_origin_is_ungrounded(self):
        doc = self.doc([self.sub("a", []), self.sub("b", [])], [self.a()])
        report = self.validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("no machine-readable provenance" in e for e in report.errors), report.errors)

    def test_auto_merge_plus_resolution_is_conflicting_provenance(self):
        """The exact D-03 attack: gold both annotators clearly proposed,
        relabelled as an adjudicator_add ("nobody proposed this")."""
        doc = self.doc(
            [self.sub("a", [self.p("p1")]), self.sub("b", [self.p("p2")])], [self.a()],
            [{"decision": "adjudicator_add", "adjudicatorId": "c", "proposalIds": [],
              "resultingAnnotationIds": ["a1"], "note": "added by adjudicator"}])
        report = self.validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("CONFLICTING provenance" in e for e in report.errors), report.errors)

    def test_duplicate_resolution_links_are_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1", pressure="P2")]),
             self.sub("b", [self.p("p2", pressure="P4")])],
            [self.a(pressure="P2")],
            [{"decision": "uphold_a", "adjudicatorId": "c",
              "proposalIds": ["p1"], "resultingAnnotationIds": ["a1"]},
             {"decision": "uphold_b", "adjudicatorId": "c",
              "proposalIds": ["p2"], "resultingAnnotationIds": ["a1"]}])
        report = self.validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("claimed by 2 resolutions" in e for e in report.errors), report.errors)


class AdjudicatorIndependenceTests(_CorpusProvenanceFixture):
    """ADJUDICATION.md §3: the adjudicator is a third person who has not
    annotated the document. Documented since the protocol was written, never
    enforced until now."""

    def test_original_annotator_cannot_adjudicate(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1")]), self.sub("b", [])], [self.a()],
            [{"decision": "uphold_a", "adjudicatorId": "a",
              "proposalIds": ["p1"], "resultingAnnotationIds": ["a1"]}])
        report = self.validate(doc)
        self.assertFalse(report.valid)
        self.assertTrue(any("independent third person" in e for e in report.errors), report.errors)

    def test_independent_third_adjudicator_is_accepted(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1")]), self.sub("b", [])], [self.a()],
            [{"decision": "uphold_a", "adjudicatorId": "c",
              "proposalIds": ["p1"], "resultingAnnotationIds": ["a1"]}])
        self.assertTrue(self.validate(doc).valid, self.validate(doc).errors)

    def test_empty_adjudicator_id_is_rejected(self):
        doc = self.doc(
            [self.sub("a", [self.p("p1")]), self.sub("b", [])], [self.a()],
            [{"decision": "uphold_a", "adjudicatorId": "   ",
              "proposalIds": ["p1"], "resultingAnnotationIds": ["a1"]}])
        self.assertFalse(self.validate(doc).valid)


class StrictAnnotatorIdsTests(_CorpusProvenanceFixture):
    """The Python validator is the load-bearing scoring gate; nothing in this
    pipeline executes the JSON Schema, so annotatorIds is enforced here to the
    same strictness the schema promises.

    The old check was `{a for a in annotators if isinstance(a, str)}` — it
    silently DISCARDED non-string entries and de-duplicated repeats before
    counting, so both ["a","b","b"] and ["a",7,"b"] passed.
    """

    def _doc_with_ids(self, ids):
        return self.doc(
            [self.sub("a", [self.p("p1")]), self.sub("b", [self.p("p2")])],
            [self.a()], annotator_ids=ids)

    def test_duplicate_annotator_ids_are_rejected(self):
        report = self.validate(self._doc_with_ids(["a", "b", "b"]))
        self.assertFalse(report.valid)
        self.assertTrue(any("duplicate entry" in e for e in report.errors), report.errors)

    def test_non_string_annotator_id_is_rejected(self):
        report = self.validate(self._doc_with_ids(["a", 7, "b"]))
        self.assertFalse(report.valid)
        self.assertTrue(any("must be a string" in e for e in report.errors), report.errors)

    def test_empty_annotator_id_is_rejected(self):
        self.assertFalse(self.validate(self._doc_with_ids(["a", "", "b"])).valid)

    def test_boolean_annotator_id_is_rejected(self):
        self.assertFalse(self.validate(self._doc_with_ids([True, "b"])).valid)

    def test_fewer_than_two_annotator_ids_is_rejected(self):
        self.assertFalse(self.validate(self._doc_with_ids(["a"])).valid)

    def test_non_array_annotator_ids_is_rejected(self):
        self.assertFalse(self.validate(self._doc_with_ids("a,b")).valid)

    def test_declared_ids_must_equal_submission_annotators(self):
        self.assertFalse(self.validate(self._doc_with_ids(["a", "z"])).valid)


class B05SchemaParityTests(unittest.TestCase):
    """B-05: benchmarks/corpus/_schema.json and validate_corpus.py's
    executable contract must agree.

    No `jsonschema` (or any other JSON Schema engine) dependency is installed
    in this repository and this task explicitly says not to add a heavyweight
    dependency merely to run schema tests. These tests instead do targeted,
    hand-rolled structural checks against the schema's own JSON — proving the
    specific facts that matter (conditional requirement present, decision
    enum matches the validator's, minItems matches MIN_ANNOTATORS, hard
    negatives aren't blocked by an accidental proposals minItems) — without a
    general-purpose validator.
    """

    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "benchmarks" / "corpus" / "_schema.json").read_text())

    def test_schema_is_valid_json(self):
        self.assertIsInstance(self.schema, dict)

    def test_adjudicated_conditionally_requires_annotator_fields(self):
        conditions = self.schema["allOf"]
        matched = [
            c for c in conditions
            if c.get("if", {}).get("properties", {}).get("adjudicationStatus", {}).get("const") == "adjudicated"
        ]
        self.assertEqual(len(matched), 1, "expected exactly one adjudicated-status conditional")
        required = set(matched[0]["then"]["required"])
        self.assertEqual(required, {"annotatorIds", "annotatorSubmissions"})

    def test_decision_enum_matches_the_python_validator(self):
        from validate_corpus import VALID_RESOLUTION_DECISIONS

        schema_enum = set(self.schema["properties"]["resolutions"]["items"]["properties"]["decision"]["enum"])
        self.assertEqual(schema_enum, VALID_RESOLUTION_DECISIONS)

    def test_resolution_requires_adjudicator_id(self):
        self.assertIn("adjudicatorId", self.schema["properties"]["resolutions"]["items"]["required"])

    def test_submissions_min_items_matches_min_annotators(self):
        from validate_corpus import MIN_ANNOTATORS

        self.assertEqual(self.schema["properties"]["annotatorSubmissions"]["minItems"], MIN_ANNOTATORS)

    def test_proposals_have_no_min_items_hard_negatives_stay_valid(self):
        proposals_schema = self.schema["properties"]["annotatorSubmissions"]["items"]["properties"]["proposals"]
        self.assertNotIn(
            "minItems", proposals_schema,
            "a nonzero minItems on proposals would make hard negatives schema-invalid",
        )

    def test_structured_records_reject_additional_properties(self):
        submission_item = self.schema["properties"]["annotatorSubmissions"]["items"]
        proposal_item = submission_item["properties"]["proposals"]["items"]
        resolution_item = self.schema["properties"]["resolutions"]["items"]
        for label, item in (
            ("annotatorSubmissions item", submission_item),
            ("proposals item", proposal_item),
            ("resolutions item", resolution_item),
        ):
            with self.subTest(label):
                self.assertFalse(item.get("additionalProperties", True), label)

    def test_worked_example_declares_the_fields_the_schema_requires_for_adjudicated_status(self):
        """A hand-rolled stand-in for full schema validation: confirm the
        worked example actually carries every field the conditional block
        requires, using the schema's own declared requirement list rather
        than a hardcoded duplicate of it."""
        example = json.loads((ROOT / "benchmarks" / "corpus" / "_example.json").read_text())
        self.assertEqual(example["adjudicationStatus"], "adjudicated")
        conditions = self.schema["allOf"]
        required = next(
            c["then"]["required"] for c in conditions
            if c.get("if", {}).get("properties", {}).get("adjudicationStatus", {}).get("const") == "adjudicated"
        )
        for field_name in required:
            self.assertIn(field_name, example, f"worked example is missing {field_name!r}")

    # ---- C-03 / schema-parity additions ----

    def _resolution_item(self):
        return self.schema["properties"]["resolutions"]["items"]

    def _conditional_for(self, decision):
        for block in self._resolution_item()["allOf"]:
            spec = block.get("if", {}).get("properties", {}).get("decision", {})
            if spec.get("const") == decision or decision in spec.get("enum", []):
                return block["then"]["properties"]
        self.fail(f"no schema conditional for decision {decision!r}")

    def test_schema_resolution_cardinality_matches_the_python_table(self):
        """Every decision's proposalIds/resultingAnnotationIds bounds in the
        schema must equal RESOLUTION_CARDINALITY, so the two contracts cannot
        drift apart silently."""
        from validate_corpus import RESOLUTION_CARDINALITY

        for decision, (min_p, max_p, min_r, max_r) in RESOLUTION_CARDINALITY.items():
            with self.subTest(decision):
                then = self._conditional_for(decision)
                proposals, results = then["proposalIds"], then["resultingAnnotationIds"]
                self.assertEqual(proposals.get("minItems", 0), min_p, f"{decision} proposal minItems")
                self.assertEqual(proposals.get("maxItems"), max_p, f"{decision} proposal maxItems")
                self.assertEqual(results.get("minItems", 0), min_r, f"{decision} result minItems")
                self.assertEqual(results.get("maxItems"), max_r, f"{decision} result maxItems")

    def test_schema_requires_resulting_annotation_ids_array_not_the_singular_field(self):
        item = self._resolution_item()
        self.assertIn("resultingAnnotationIds", item["required"])
        self.assertEqual(item["properties"]["resultingAnnotationIds"]["type"], "array")
        self.assertNotIn(
            "resultingAnnotationId", item["properties"],
            "the removed singular field must not reappear — it cannot represent a split",
        )

    def test_schema_requires_two_unique_annotator_ids(self):
        from validate_corpus import MIN_ANNOTATORS

        annotator_ids = self.schema["properties"]["annotatorIds"]
        self.assertEqual(annotator_ids["minItems"], MIN_ANNOTATORS)
        self.assertTrue(annotator_ids["uniqueItems"])
        self.assertEqual(annotator_ids["items"]["minLength"], 1)

    def test_schema_adjudicator_add_requires_a_rationale(self):
        for block in self._resolution_item()["allOf"]:
            if block.get("if", {}).get("properties", {}).get("decision", {}).get("const") == "adjudicator_add":
                required_one_of = {
                    tuple(option["required"]) for option in block["then"]["anyOf"]
                }
                self.assertEqual(required_one_of, {("note",), ("rationale",)})
                return
        self.fail("no adjudicator_add conditional in the schema")

    def test_schema_documents_the_python_only_semantic_boundary(self):
        """Parity is claimed only for the STRUCTURAL contract. The schema must
        say so rather than implying a schema-valid document is corpus-valid."""
        description = self.schema["description"]
        self.assertIn("SCHEMA/VALIDATOR BOUNDARY", description)
        self.assertIn("NOT necessarily a valid corpus document", description)
