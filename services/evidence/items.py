"""Evidence items, relations and evidence-bounded claim states."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from services.rhetoric import vocabulary as vocab

_SUPPORTS = "supports"
_CONTRADICTS = "contradicts"
_CONTEXTUALIZES = "contextualizes"
_RELATION_TYPES = frozenset({_SUPPORTS, _CONTRADICTS, _CONTEXTUALIZES})

_DIRECTNESS_WEIGHT = {"direct": 3, "contextual": 2, "derivative": 1}
_AUTHENTICITY_WEIGHT = {"verified": 3, "unverified": 1, "disputed": 0}


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    evidence_type: str
    title: str
    directness: str
    authenticity_state: str = "unverified"
    authenticity_basis: str | None = None
    description: str | None = None
    provenance_uri: str | None = None
    observed_at: str | None = None
    effective_from: str | None = None
    excerpt_text: str | None = None
    completeness: str = "unknown"
    is_synthetic: bool = False

    def __post_init__(self) -> None:
        if self.directness not in vocab.EVIDENCE_DIRECTNESS:
            raise ValueError(f"invalid evidence directness: {self.directness!r}")
        if self.authenticity_state not in vocab.AUTHENTICITY_STATE:
            raise ValueError(f"invalid authenticity state: {self.authenticity_state!r}")
        if self.authenticity_state == "verified" and not self.authenticity_basis:
            # Rule 11: primary evidence is not automatically true. Declaring
            # something verified requires saying HOW it was verified.
            raise ValueError(
                "authenticity_state='verified' requires an explicit authenticity_basis; "
                "evidence may not be globally labelled authenticated"
            )

    @property
    def display_label(self) -> str:
        """Honest, non-privileging label for UI use."""
        base = {
            "verified": "authenticated primary evidence",
            "unverified": "primary evidence — authenticity unverified",
            "disputed": "disputed primary evidence",
        }[self.authenticity_state]
        if self.directness != "direct":
            base = base.replace("primary evidence", f"{self.directness} evidence")
        return ("synthetic — " + base) if self.is_synthetic else base

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidenceId": self.evidence_id,
            "evidenceType": self.evidence_type,
            "title": self.title,
            "directness": self.directness,
            "authenticityState": self.authenticity_state,
            "authenticityBasis": self.authenticity_basis,
            "description": self.description,
            "provenanceUri": self.provenance_uri,
            "observedAt": self.observed_at,
            "effectiveFrom": self.effective_from,
            "excerptText": self.excerpt_text,
            "completeness": self.completeness,
            "isSynthetic": self.is_synthetic,
            "displayLabel": self.display_label,
        }


@dataclass(frozen=True)
class EvidenceRelation:
    relation_id: str
    claim_id: str
    evidence_id: str
    relation_type: str
    confidence: str
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.relation_type not in _RELATION_TYPES:
            raise ValueError(f"invalid evidence relation type: {self.relation_type!r}")
        if self.confidence not in vocab.CONFIDENCE:
            raise ValueError(f"invalid evidence relation confidence: {self.confidence!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "relationId": self.relation_id,
            "claimId": self.claim_id,
            "evidenceId": self.evidence_id,
            "relationType": self.relation_type,
            "confidence": self.confidence,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class EvidenceStrength:
    evidence_id: str
    score: int
    rationale: tuple[str, ...]


def rank_evidence(items: Sequence[EvidenceItem]) -> list[EvidenceStrength]:
    """Rank by evidentiary characteristics only.

    Deliberately absent from this function: how many outlets cited the item, how
    popular the account is, and whether it agrees with the dominant narrative. A
    contrarian authenticated primary document must be able to outrank a widely
    repeated derivative one — and a widely repeated one must not gain strength
    from repetition.
    """
    ranked: list[EvidenceStrength] = []
    for item in items:
        rationale: list[str] = []
        score = 0

        directness_points = _DIRECTNESS_WEIGHT[item.directness]
        score += directness_points
        rationale.append(f"directness={item.directness} (+{directness_points})")

        authenticity_points = _AUTHENTICITY_WEIGHT[item.authenticity_state]
        score += authenticity_points
        rationale.append(f"authenticity={item.authenticity_state} (+{authenticity_points})")

        if item.completeness == "complete":
            score += 1
            rationale.append("completeness=complete (+1)")
        elif item.completeness in {"partial", "excerpt"}:
            rationale.append(f"completeness={item.completeness} (+0)")
        else:
            rationale.append("completeness=unknown (+0)")

        if item.is_synthetic:
            rationale.append("synthetic fixture material — not real-world evidence")

        ranked.append(EvidenceStrength(item.evidence_id, score, tuple(rationale)))

    return sorted(ranked, key=lambda s: (-s.score, s.evidence_id))


def claim_state_for(
    relations: Iterable[EvidenceRelation],
    evidence_by_id: dict[str, EvidenceItem],
    *,
    retrieval_complete: bool = True,
) -> str:
    """Derive a claim state that the evidence can actually support.

    A claim never becomes ``supported_by_direct_evidence`` on the strength of
    unverified material, and contradiction is never silently outvoted by
    supporting volume — contested is the honest answer when both exist.
    """
    if not retrieval_complete:
        return "retrieval_incomplete"

    relations = list(relations)
    if not relations:
        return "unverified"

    supporting = [r for r in relations if r.relation_type == _SUPPORTS]
    contradicting = [r for r in relations if r.relation_type == _CONTRADICTS]

    def has_authenticated_direct(rels: Sequence[EvidenceRelation]) -> bool:
        for relation in rels:
            item = evidence_by_id.get(relation.evidence_id)
            if item is None:
                continue
            if item.directness == "direct" and item.authenticity_state == "verified":
                return True
        return False

    if supporting and contradicting:
        return "contested"

    if contradicting:
        return "contradicted_by_evidence" if has_authenticated_direct(contradicting) else "contested"

    if has_authenticated_direct(supporting):
        return "supported_by_direct_evidence"

    if len(supporting) >= 2:
        # Corroborated is explicitly weaker than direct support, and repetition
        # alone never promotes it further.
        return "corroborated"

    return "unverified"
