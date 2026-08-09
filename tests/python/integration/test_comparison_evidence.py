"""Integration tests: claim alignment, Material Omission gates, evidence."""
from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.comparison import (  # noqa: E402
    Claim,
    ComparisonSet,
    OmissionRejection,
    SourceAssertion,
    SourceDependency,
    align_pair,
    detect_material_omissions,
    independent_source_count,
)
from services.comparison.omission import (  # noqa: E402
    assert_not_intrinsic,
    evaluate_candidate_omission,
)
from services.evidence import (  # noqa: E402
    EvidenceItem,
    EvidenceRelation,
    claim_state_for,
    rank_evidence,
)

WARRANT = "Section 4(b) requires a magistrate-issued judicial warrant before regulators inspect private message content"


def assertion(source_id, name, article_id, excerpt):
    return SourceAssertion(
        source_id=source_id, source_name=name, article_id=article_id,
        passage_id=f"{article_id}:p0000", excerpt=excerpt,
    )


def claim(claim_id, proposition, assertions):
    return Claim(
        claim_id=claim_id, normalized_proposition=proposition, source_assertions=tuple(assertions)
    )


class ClaimAlignmentTests(unittest.TestCase):
    def test_identical_propositions_align_as_same(self):
        a = claim("c1", WARRANT, [assertion("s1", "A", "art-1", "x")])
        b = claim("c2", WARRANT, [assertion("s2", "B", "art-2", "y")])
        self.assertEqual(align_pair(a, b).relation, "same_proposition")

    def test_unrelated_propositions_are_not_forced_into_a_match(self):
        a = claim("c1", WARRANT, [assertion("s1", "A", "art-1", "x")])
        b = claim("c2", "The stadium roof was repaired last autumn", [assertion("s2", "B", "art-2", "y")])
        self.assertEqual(align_pair(a, b).relation, "unrelated")

    def test_ambiguous_overlap_yields_uncertain_and_low_confidence(self):
        # Substantial lexical overlap, materially different propositions
        # ("must obtain a warrant" vs "may inspect"). A lexical baseline cannot
        # tell these apart, and saying so is the correct behaviour.
        a = claim("c1", "regulators must obtain a judicial warrant to inspect message content",
                  [assertion("s1", "A", "art-1", "x")])
        b = claim("c2", "regulators may inspect platform message content under the statute",
                  [assertion("s2", "B", "art-2", "y")])
        alignment = align_pair(a, b)
        self.assertEqual(alignment.relation, "uncertain")
        self.assertEqual(alignment.confidence, "Low")
        self.assertFalse(alignment.is_usable_for_omission)

    def test_negation_mismatch_is_flagged_contradictory_not_agreement(self):
        a = claim("c1", "the statute requires a judicial warrant for content inspection", [assertion("s1", "A", "art-1", "x")])
        b = claim("c2", "the statute does not require a judicial warrant for content inspection", [assertion("s2", "B", "art-2", "y")])
        alignment = align_pair(a, b)
        self.assertEqual(alignment.relation, "contradictory")
        self.assertFalse(alignment.is_usable_for_omission)

    def test_uncertain_alignment_is_never_usable_for_omission(self):
        a = claim("c1", "alpha beta gamma delta epsilon", [assertion("s1", "A", "art-1", "x")])
        b = claim("c2", "alpha beta zeta eta theta iota", [assertion("s2", "B", "art-2", "y")])
        alignment = align_pair(a, b)
        if alignment.relation == "uncertain":
            self.assertFalse(alignment.is_usable_for_omission)


class SourceDependenceTests(unittest.TestCase):
    def test_syndicated_sources_collapse_to_one_origin(self):
        deps = [SourceDependency(("wire", "paper_a"), "syndication", "High"),
                SourceDependency(("wire", "paper_b"), "syndication", "High")]
        self.assertEqual(independent_source_count(["wire", "paper_a", "paper_b"], deps), 1)

    def test_independent_reporting_does_not_collapse(self):
        deps = [SourceDependency(("a", "b"), "independent_reporting", "High")]
        self.assertEqual(independent_source_count(["a", "b"], deps), 2)

    def test_unknown_dependence_does_not_manufacture_independence(self):
        deps = [SourceDependency(("a", "b"), "unknown", "Low")]
        # Unknown does not collapse, but it is also never *claimed* as
        # independent — describe_independence reports it explicitly.
        from services.comparison.dependence import describe_independence
        described = describe_independence(["a", "b"], deps)
        self.assertEqual(described["unknownRelationships"], 1)
        self.assertIn("not", described["note"])


class MaterialOmissionGateTests(unittest.TestCase):
    def setUp(self):
        self.supporting = [
            claim("c-tw", WARRANT, [assertion("techwire", "Tech Wire", "art-tw", "...")]),
            claim("c-pj", WARRANT, [assertion("policy", "Policy Journal", "art-pj", "...")]),
        ]
        self.comparison_set = ComparisonSet(
            comparison_set_id="cs-1",
            target_article_id="art-sentinel",
            member_article_ids=("art-tw", "art-pj"),
            provenance_kind="synthetic_fixture",
        )

    def _evaluate(self, **overrides):
        kwargs = dict(
            comparison_set=self.comparison_set,
            candidate_proposition=WARRANT,
            supporting_claims=self.supporting,
            target_claims=[],
            dimension="Responsibility",
            target_published_at="2026-07-12T10:30:00Z",
            knowable_at="2026-07-10T09:00:00Z",
            rationale="Omitting the warrant requirement misleads readers about regulator powers.",
        )
        kwargs.update(overrides)
        return evaluate_candidate_omission(**kwargs)

    def test_well_grounded_omission_is_accepted(self):
        omission = self._evaluate()
        self.assertEqual(omission.dimension, "Responsibility")
        self.assertGreaterEqual(len(omission.supporting_source_ids), 2)
        self.assertTrue(omission.grounding_alignments)

    def test_single_source_comparison_set_is_refused(self):
        thin = ComparisonSet(
            comparison_set_id="cs-thin", target_article_id="art-sentinel",
            member_article_ids=("art-tw",), provenance_kind="synthetic_fixture",
        )
        with self.assertRaises(OmissionRejection) as ctx:
            self._evaluate(comparison_set=thin)
        self.assertEqual(ctx.exception.gate, "comparison_set")

    def test_proposition_already_present_in_target_is_refused(self):
        present = [claim("c-target", WARRANT, [assertion("sentinel", "Sentinel", "art-sentinel", "...")])]
        with self.assertRaises(OmissionRejection) as ctx:
            self._evaluate(target_claims=present)
        self.assertEqual(ctx.exception.gate, "absence_in_target")

    def test_later_development_is_not_an_omission(self):
        with self.assertRaises(OmissionRejection) as ctx:
            self._evaluate(knowable_at="2026-07-20T00:00:00Z")
        self.assertEqual(ctx.exception.gate, "chronology")

    def test_syndicated_supporting_sources_are_refused_as_corroboration(self):
        syndicated = ComparisonSet(
            comparison_set_id="cs-syn", target_article_id="art-sentinel",
            member_article_ids=("art-tw", "art-pj"), provenance_kind="synthetic_fixture",
            dependencies=(SourceDependency(("techwire", "policy"), "syndication", "High"),),
        )
        with self.assertRaises(OmissionRejection) as ctx:
            self._evaluate(comparison_set=syndicated)
        self.assertEqual(ctx.exception.gate, "source_independence")

    def test_unrelated_supporting_claims_are_refused(self):
        unrelated = [
            claim("c-x", "The stadium roof was repaired", [assertion("a", "A", "art-a", "...")]),
            claim("c-y", "Ticket prices rose in spring", [assertion("b", "B", "art-b", "...")]),
        ]
        with self.assertRaises(OmissionRejection) as ctx:
            self._evaluate(supporting_claims=unrelated)
        self.assertEqual(ctx.exception.gate, "presence_elsewhere")

    def test_synthetic_comparison_set_is_labelled_on_the_omission(self):
        omission = self._evaluate()
        self.assertTrue(omission.is_synthetic)
        self.assertTrue(
            any("synthetic" in note.lower() for note in omission.uncertainty_notes)
        )

    def test_confidence_is_capped_by_the_weakest_alignment(self):
        omission = self._evaluate()
        weakest = min(
            (a.confidence for a in omission.grounding_alignments),
            key=lambda c: {"Low": 1, "Medium": 2, "High": 3}[c],
        )
        self.assertLessEqual(
            {"Low": 1, "Medium": 2, "High": 3}[omission.confidence],
            {"Low": 1, "Medium": 2, "High": 3}[weakest],
        )

    def test_coverage_consensus_is_explicitly_not_truth(self):
        omission = self._evaluate()
        self.assertTrue(
            any("not truth" in note.lower() for note in omission.uncertainty_notes)
        )

    def test_intrinsic_stage_cannot_produce_omission(self):
        for stage in ("intrinsic_analysis", "local_preview", "single_document"):
            with self.assertRaises(OmissionRejection):
                assert_not_intrinsic(stage)

    def test_detect_returns_rejections_rather_than_swallowing_them(self):
        accepted, rejected = detect_material_omissions(
            comparison_set=self.comparison_set,
            candidates=[
                {
                    "proposition": WARRANT, "supportingClaims": self.supporting,
                    "dimension": "Responsibility", "knowableAt": "2026-07-10T09:00:00Z",
                    "rationale": "ok",
                },
                {
                    "proposition": WARRANT, "supportingClaims": self.supporting,
                    "dimension": "Responsibility", "knowableAt": "2027-01-01T00:00:00Z",
                    "rationale": "later development",
                },
            ],
            target_claims=[],
            target_published_at="2026-07-12T10:30:00Z",
        )
        self.assertEqual(len(accepted), 1)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0].gate, "chronology")


class EvidenceTests(unittest.TestCase):
    def test_verified_authenticity_requires_an_explicit_basis(self):
        with self.assertRaises(ValueError):
            EvidenceItem(
                evidence_id="e1", evidence_type="statute", title="Statute",
                directness="direct", authenticity_state="verified",
            )
        ok = EvidenceItem(
            evidence_id="e1", evidence_type="statute", title="Statute",
            directness="direct", authenticity_state="verified",
            authenticity_basis="Checked against the published register.",
        )
        self.assertEqual(ok.authenticity_state, "verified")

    def test_default_authenticity_is_unverified(self):
        item = EvidenceItem(evidence_id="e2", evidence_type="memo", title="Memo", directness="direct")
        self.assertEqual(item.authenticity_state, "unverified")
        self.assertIn("unverified", item.display_label)

    def test_ranking_uses_evidentiary_characteristics_not_popularity(self):
        contrarian = EvidenceItem(
            evidence_id="primary", evidence_type="statute", title="Primary text",
            directness="direct", authenticity_state="verified",
            authenticity_basis="register check", completeness="complete",
        )
        popular = EvidenceItem(
            evidence_id="derivative", evidence_type="summary", title="Widely cited summary",
            directness="derivative", authenticity_state="unverified",
        )
        ranked = rank_evidence([popular, contrarian])
        self.assertEqual(ranked[0].evidence_id, "primary")

    def test_claim_state_never_exceeds_the_evidence(self):
        unverified = EvidenceItem(evidence_id="e3", evidence_type="memo", title="Memo", directness="direct")
        relation = EvidenceRelation(
            relation_id="r1", claim_id="c1", evidence_id="e3", relation_type="supports", confidence="High"
        )
        state = claim_state_for([relation], {"e3": unverified})
        self.assertNotEqual(state, "supported_by_direct_evidence")

    def test_contradiction_is_not_outvoted_by_supporting_volume(self):
        evidence = {
            "s1": EvidenceItem(evidence_id="s1", evidence_type="a", title="a", directness="direct"),
            "s2": EvidenceItem(evidence_id="s2", evidence_type="b", title="b", directness="direct"),
            "c1": EvidenceItem(evidence_id="c1", evidence_type="c", title="c", directness="direct"),
        }
        relations = [
            EvidenceRelation("r1", "claim", "s1", "supports", "High"),
            EvidenceRelation("r2", "claim", "s2", "supports", "High"),
            EvidenceRelation("r3", "claim", "c1", "contradicts", "Medium"),
        ]
        self.assertEqual(claim_state_for(relations, evidence), "contested")

    def test_incomplete_retrieval_is_reported_not_hidden(self):
        self.assertEqual(claim_state_for([], {}, retrieval_complete=False), "retrieval_incomplete")

    def test_no_evidence_means_unverified(self):
        self.assertEqual(claim_state_for([], {}), "unverified")

    def test_synthetic_evidence_is_labelled_unmistakably(self):
        item = EvidenceItem(
            evidence_id="e9", evidence_type="statute", title="Demo statute",
            directness="direct", is_synthetic=True,
        )
        self.assertIn("synthetic", item.display_label.lower())


if __name__ == "__main__":
    unittest.main()
