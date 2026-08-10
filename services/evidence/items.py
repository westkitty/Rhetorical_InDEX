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

    def usable(relation: EvidenceRelation) -> bool:
        """Whether a relation is strong enough to move claim state.

        Review finding M-07: the relation between evidence and proposition is
        ITSELF epistemic evidence. A Low-confidence link to an authenticated
        document says "we are not sure this document is even about this claim",
        which cannot license `supported_by_direct_evidence`. Weak links are
        retained for display but may not promote state.
        """
        return vocab.confidence_rank(relation.confidence) >= 2

    def authenticated_direct(rels: Sequence[EvidenceRelation]) -> list[EvidenceRelation]:
        out = []
        for relation in rels:
            item = evidence_by_id.get(relation.evidence_id)
            if item is None:
                continue
            if item.directness == "direct" and item.authenticity_state == "verified":
                out.append(relation)
        return out

    def distinct_items(rels: Sequence[EvidenceRelation]) -> set[str]:
        """Review finding M-08: corroboration counts EVIDENCE ITEMS, never relation rows.

        Two relations pointing at the same document are one piece of evidence
        cited twice. Counting rows would let duplicated bookkeeping manufacture
        corroboration out of a single source.
        """
        return {r.evidence_id for r in rels if r.evidence_id in evidence_by_id}

    strong_supporting = [r for r in supporting if usable(r)]
    strong_contradicting = [r for r in contradicting if usable(r)]

    # Contradiction is never outvoted by supporting volume.
    if strong_supporting and strong_contradicting:
        return "contested"
    if supporting and contradicting:
        return "contested"

    if strong_contradicting:
        return "contradicted_by_evidence" if authenticated_direct(strong_contradicting) else "contested"
    if contradicting:
        # Only weak contradiction: not confident enough to assert contradiction,
        # but not clean either.
        return "contested"

    if authenticated_direct(strong_supporting):
        return "supported_by_direct_evidence"

    if len(distinct_items(strong_supporting)) >= 2:
        # Corroborated is explicitly weaker than direct support, and repetition
        # alone never promotes it further. Independence between the items is NOT
        # represented in the current model, so this is the ceiling: the state
        # says "several distinct items agree", not "several independent sources
        # agree". See KNOWN_LIMITATIONS.
        return "corroborated"

    return "unverified"
