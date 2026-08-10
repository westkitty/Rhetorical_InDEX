"""Material Omission — cross-document only, behind hard gates.

Epistemic constitution rule 9: material omission is cross-document. Rule 12:
uncertainty must not silently disappear downstream. Rule 10: coverage consensus
is not truth.

This module refuses to produce an omission unless ALL of the following hold:

  1. a ComparisonSet exists and contains at least ``MIN_SUPPORTING_SOURCES``
     sources other than the target;
  2. the proposition is actually present in the comparison material, via an
     alignment that is confident enough to be usable;
  3. the proposition is genuinely ABSENT from the target article — established
     by alignment against the target's own claims, not by keyword absence;
  4. the fact was knowable at the target's publication time (later developments
     are not omissions);
  5. the supporting sources are not all one syndicated origin — ten copies of
     one wire story is one source, not ten.

Any failure raises ``OmissionRejection`` with the specific gate that failed.
Refusing to emit is the correct behaviour, not a bug.

Emitted confidence is CAPPED by the weakest link in the chain. An omission can
never be more confident than the alignment that established presence elsewhere.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from services.rhetoric import vocabulary as vocab

from .claims import Claim, ClaimAlignment, align_pair
from .dependence import SourceDependency, independent_source_count

MIN_SUPPORTING_SOURCES = 2


class OmissionRejection(ValueError):
    """A candidate omission failed a gate and was refused."""

    def __init__(self, gate: str, reason: str) -> None:
        super().__init__(f"[{gate}] {reason}")
        self.gate = gate
        self.reason = reason


@dataclass(frozen=True)
class ComparisonSet:
    comparison_set_id: str
    target_article_id: str
    member_article_ids: tuple[str, ...]
    provenance_kind: str  # "synthetic_fixture" | "retrieved"
    claims_by_article: dict[str, tuple[Claim, ...]] = field(default_factory=dict)
    source_of_article: dict[str, str] = field(default_factory=dict)
    published_at_by_article: dict[str, str] = field(default_factory=dict)
    dependencies: tuple[SourceDependency, ...] = ()

    def __post_init__(self) -> None:
        if self.provenance_kind not in {"synthetic_fixture", "retrieved"}:
            raise ValueError(f"invalid comparison set provenance: {self.provenance_kind!r}")
        if self.target_article_id in self.member_article_ids:
            raise ValueError("target article must not also be listed as a comparison member")

    @property
    def is_synthetic(self) -> bool:
        return self.provenance_kind == "synthetic_fixture"

    @property
    def peer_count(self) -> int:
        return len(self.member_article_ids)

    def to_dict(self) -> dict[str, Any]:
        return {
            "comparisonSetId": self.comparison_set_id,
            "targetArticleId": self.target_article_id,
            "memberArticleIds": list(self.member_article_ids),
            "provenanceKind": self.provenance_kind,
            "isSynthetic": self.is_synthetic,
        }


@dataclass(frozen=True)
class MaterialOmission:
    omission_id: str
    target_article_id: str
    comparison_set_id: str
    missing_proposition: str
    supporting_source_ids: tuple[str, ...]
    supporting_article_ids: tuple[str, ...]
    dimension: str
    rationale: str
    confidence: str
    knowable_at_timestamp: str
    grounding_alignments: tuple[ClaimAlignment, ...] = ()
    evidence_item_ids: tuple[str, ...] = ()
    is_synthetic: bool = False
    uncertainty_notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.dimension not in vocab.OMISSION_DIMENSION:
            raise ValueError(f"invalid omission dimension: {self.dimension!r}")
        if self.confidence not in vocab.CONFIDENCE:
            raise ValueError(f"invalid omission confidence: {self.confidence!r}")
        if len(self.supporting_source_ids) < MIN_SUPPORTING_SOURCES:
            raise ValueError(
                "a MaterialOmission requires at least "
                f"{MIN_SUPPORTING_SOURCES} independent supporting sources"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "omissionId": self.omission_id,
            "targetArticleId": self.target_article_id,
            "comparisonSetId": self.comparison_set_id,
            "missingProposition": self.missing_proposition,
            "supportingSourceIds": list(self.supporting_source_ids),
            "supportingArticleIds": list(self.supporting_article_ids),
            "dimension": self.dimension,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "knowableAtTimestamp": self.knowable_at_timestamp,
            "groundingAlignments": [a.to_dict() for a in self.grounding_alignments],
            "evidenceItemIds": list(self.evidence_item_ids),
            "isSynthetic": self.is_synthetic,
            "uncertaintyNotes": list(self.uncertainty_notes),
        }


def _cap_confidence(*levels: str) -> str:
    """The chain is only as confident as its weakest link."""
    return min(levels, key=vocab.confidence_rank)


def evaluate_candidate_omission(
    *,
    comparison_set: ComparisonSet,
    candidate_proposition: str,
    supporting_claims: Sequence[Claim],
    target_claims: Sequence[Claim],
    dimension: str,
    target_published_at: str,
    knowable_at: str,
    rationale: str,
    evidence_item_ids: Iterable[str] = (),
) -> MaterialOmission:
    """Evaluate one candidate omission against every gate. Raises on refusal."""
    notes: list[str] = []

    # Gate 1 — a real comparison set must exist.
    if comparison_set.peer_count < MIN_SUPPORTING_SOURCES:
        raise OmissionRejection(
            "comparison_set",
            f"comparison set has {comparison_set.peer_count} peer article(s); "
            f"at least {MIN_SUPPORTING_SOURCES} are required",
        )

    if not supporting_claims:
        raise OmissionRejection(
            "presence_elsewhere", "no supporting claims were supplied from comparison sources"
        )

    # Gate 2 — the proposition must actually be present elsewhere, established
    # by usable alignment rather than assumed.
    probe = Claim(
        claim_id="claim-omission-probe",
        normalized_proposition=candidate_proposition,
        source_assertions=supporting_claims[0].source_assertions,
    )
    presence_alignments: list[ClaimAlignment] = []
    supporting_source_ids: list[str] = []
    supporting_article_ids: list[str] = []
    conflicting: list[str] = []

    for claim in supporting_claims:
        alignment = align_pair(probe, claim)
        if alignment.divergences:
            # A supporting claim that factually contradicts the candidate can
            # never be evidence FOR it. Recorded so the refusal is explainable.
            conflicting.append(
                f"{claim.claim_id}: {'; '.join(alignment.divergences)}"
            )
            continue
        if alignment.is_usable_for_omission:
            presence_alignments.append(alignment)
            for assertion in claim.source_assertions:
                supporting_source_ids.append(assertion.source_id)
                supporting_article_ids.append(assertion.article_id)

    if not presence_alignments:
        reason = "no comparison claim aligned to the candidate proposition with usable confidence"
        if conflicting:
            reason += (
                "; supporting claims factually diverge from the candidate proposition "
                f"({' | '.join(conflicting)}) and cannot establish it"
            )
        raise OmissionRejection("presence_elsewhere", reason)

    # Invariant (M-01): every accepted grounding alignment must be free of
    # detected factual divergence AND usable. Belt-and-braces: if a future edit
    # loosens is_usable_for_omission, this still refuses to emit an omission
    # whose supporting sources contradict the proposition being asserted.
    for alignment in presence_alignments:
        if alignment.divergences or not alignment.is_usable_for_omission:
            raise OmissionRejection(
                "presence_elsewhere",
                "internal invariant violated: a grounding alignment was not a "
                "divergence-free, usable match for the candidate proposition",
            )

    supporting_source_ids = list(dict.fromkeys(supporting_source_ids))
    supporting_article_ids = list(dict.fromkeys(supporting_article_ids))

    if len(supporting_source_ids) < MIN_SUPPORTING_SOURCES:
        raise OmissionRejection(
            "supporting_sources",
            f"only {len(supporting_source_ids)} distinct supporting source(s); "
            f"at least {MIN_SUPPORTING_SOURCES} are required",
        )

    # Gate 3 — the proposition must genuinely be ABSENT from the target.
    for claim in target_claims:
        alignment = align_pair(probe, claim)
        if alignment.relation in {"same_proposition", "compatible", "more_specific"} and \
                vocab.confidence_rank(alignment.confidence) >= 2:
            raise OmissionRejection(
                "absence_in_target",
                "the target article already expresses this proposition "
                f"(relation={alignment.relation}, overlap={alignment.overlap_score:.2f})",
            )
        if alignment.relation == "uncertain":
            notes.append(
                "A target claim overlaps this proposition ambiguously "
                f"(overlap={alignment.overlap_score:.2f}); absence is not fully certain."
            )

    # Gate 4 — later developments are not omissions.
    if knowable_at > target_published_at:
        raise OmissionRejection(
            "chronology",
            f"fact became knowable at {knowable_at}, after target publication "
            f"at {target_published_at}; this is a later development, not an omission",
        )

    # Gate 5 — syndicated duplicates are not independent corroboration.
    independent = independent_source_count(supporting_source_ids, comparison_set.dependencies)
    if independent < MIN_SUPPORTING_SOURCES:
        raise OmissionRejection(
            "source_independence",
            f"{len(supporting_source_ids)} supporting sources reduce to {independent} "
            "independent origin(s) once syndication/shared-source links are applied",
        )
    if independent < len(supporting_source_ids):
        notes.append(
            f"{len(supporting_source_ids)} supporting sources reduce to {independent} "
            "independent origins; corroboration is weaker than the raw count suggests."
        )

    # Confidence is capped by the weakest alignment in the grounding chain.
    weakest_alignment = _cap_confidence(*(a.confidence for a in presence_alignments))
    confidence = weakest_alignment

    if comparison_set.is_synthetic:
        notes.append(
            "Comparison set is synthetic fixture material, not retrieved coverage. "
            "This omission demonstrates the mechanism; it is not a finding about the real world."
        )
    if independent == MIN_SUPPORTING_SOURCES:
        confidence = _cap_confidence(confidence, "Medium")
        notes.append("Confidence capped at Medium: corroborated by the minimum independent sources only.")

    notes.append(
        "Coverage consensus is not truth: other sources carrying this proposition "
        "does not establish that it is correct, only that this article omits it."
    )

    omission_id = "om-" + hashlib.sha256(
        f"{comparison_set.target_article_id}|{candidate_proposition}".encode()
    ).hexdigest()[:16]

    return MaterialOmission(
        omission_id=omission_id,
        target_article_id=comparison_set.target_article_id,
        comparison_set_id=comparison_set.comparison_set_id,
        missing_proposition=candidate_proposition,
        supporting_source_ids=tuple(supporting_source_ids),
        supporting_article_ids=tuple(supporting_article_ids),
        dimension=dimension,
        rationale=rationale,
        confidence=confidence,
        knowable_at_timestamp=knowable_at,
        grounding_alignments=tuple(presence_alignments),
        evidence_item_ids=tuple(evidence_item_ids),
        is_synthetic=comparison_set.is_synthetic,
        uncertainty_notes=tuple(notes),
    )


def detect_material_omissions(
    *,
    comparison_set: ComparisonSet,
    candidates: Sequence[dict[str, Any]],
    target_claims: Sequence[Claim],
    target_published_at: str,
) -> tuple[list[MaterialOmission], list[OmissionRejection]]:
    """Evaluate candidate omissions. Returns (accepted, rejections).

    Rejections are returned rather than swallowed, so the UI can honestly say
    "considered and refused" instead of silently showing nothing.
    """
    accepted: list[MaterialOmission] = []
    rejected: list[OmissionRejection] = []

    for candidate in candidates:
        try:
            accepted.append(
                evaluate_candidate_omission(
                    comparison_set=comparison_set,
                    candidate_proposition=candidate["proposition"],
                    supporting_claims=candidate["supportingClaims"],
                    target_claims=target_claims,
                    dimension=candidate["dimension"],
                    target_published_at=target_published_at,
                    knowable_at=candidate["knowableAt"],
                    rationale=candidate["rationale"],
                    evidence_item_ids=candidate.get("evidenceItemIds", ()),
                )
            )
        except OmissionRejection as rejection:
            rejected.append(rejection)

    return accepted, rejected


def assert_not_intrinsic(source_stage: str) -> None:
    """Guard: material omission may never originate in an intrinsic scan."""
    if source_stage in {"intrinsic_analysis", "local_preview", "single_document"}:
        raise OmissionRejection(
            "cross_document_only",
            f"material omission cannot be emitted from stage {source_stage!r}; "
            "it requires a comparison set",
        )
