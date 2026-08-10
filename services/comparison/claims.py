"""Atomic claims and claim alignment.

The unit of cross-source comparison is the proposition, not the article. That
is what makes "same claim, different telling" possible: hold the proposition
fixed and let the rhetorical packaging vary.

Alignment is deliberately conservative. Nothing is forced into
``same_proposition``: a weak lexical overlap yields ``uncertain``, and
``uncertain`` propagates. A downstream stage may not upgrade it.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from services.rhetoric import vocabulary as vocab

from .divergence import describe, detect_divergence, has_negation_conflict

_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'-]*")
_STOPWORDS = frozenset(
    """a an the and or but if then than that this these those of in on at to for from by with
    without into over under is are was were be been being will would shall should may might can
    could must has have had do does did not no nor it its as such about after before during
    while when where which who whom whose what how why""".split()
)


@dataclass(frozen=True)
class SourceAssertion:
    """One source's exact wording of a claim. Never paraphrased away."""

    source_id: str
    source_name: str
    article_id: str
    passage_id: str | None
    excerpt: str
    published_at: str | None = None
    pressure: str | None = None
    mechanism_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.pressure is not None and self.pressure not in vocab.PRESSURE:
            raise ValueError(f"invalid pressure on source assertion: {self.pressure!r}")
        for mechanism_id in self.mechanism_ids:
            if mechanism_id not in vocab.mechanism_ids():
                raise ValueError(f"unknown mechanism on source assertion: {mechanism_id!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "sourceId": self.source_id,
            "sourceName": self.source_name,
            "articleId": self.article_id,
            "passageId": self.passage_id,
            "excerpt": self.excerpt,
            "publishedAt": self.published_at,
            "pressure": self.pressure,
            "mechanismIds": list(self.mechanism_ids),
        }


@dataclass(frozen=True)
class Claim:
    claim_id: str
    normalized_proposition: str
    source_assertions: tuple[SourceAssertion, ...]
    attribution: str | None = None
    speaker: str | None = None
    first_known_timestamp: str | None = None
    state: str = "unverified"
    evidence_item_ids: tuple[str, ...] = ()
    extraction_confidence: str = "Medium"

    def __post_init__(self) -> None:
        if self.state not in vocab.CLAIM_STATE:
            raise ValueError(f"invalid claim state: {self.state!r}")
        if self.extraction_confidence not in vocab.CONFIDENCE:
            raise ValueError(f"invalid extraction confidence: {self.extraction_confidence!r}")
        if not self.source_assertions:
            raise ValueError("a Claim must carry at least one source assertion")

    @property
    def source_ids(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(a.source_id for a in self.source_assertions))

    def to_dict(self) -> dict[str, Any]:
        return {
            "claimId": self.claim_id,
            "normalizedProposition": self.normalized_proposition,
            "attribution": self.attribution,
            "speaker": self.speaker,
            "firstKnownTimestamp": self.first_known_timestamp,
            "state": self.state,
            "evidenceItemIds": list(self.evidence_item_ids),
            "extractionConfidence": self.extraction_confidence,
            "sourceAssertions": [a.to_dict() for a in self.source_assertions],
        }


@dataclass(frozen=True)
class ClaimAlignment:
    alignment_id: str
    claim_a: str
    claim_b: str
    relation: str
    confidence: str
    overlap_score: float
    rationale: str
    divergences: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.relation not in vocab.ALIGNMENT_RELATION:
            raise ValueError(f"invalid alignment relation: {self.relation!r}")
        if self.confidence not in vocab.CONFIDENCE:
            raise ValueError(f"invalid alignment confidence: {self.confidence!r}")

    @property
    def is_usable_for_omission(self) -> bool:
        """Only `same_proposition` may ground a Material Omission.

        Narrowed from the previous {same_proposition, compatible, more_specific,
        less_specific} after review finding M-01, which showed bare `compatible`
        letting contradictory peer claims satisfy the presence gate.

        The specificity relations are excluded deliberately, and the direction
        matters: `align_pair(probe, peer)` returns `more_specific` when the
        *probe* (the candidate proposition) carries more content than the peer —
        precisely the case where the peer does NOT establish the candidate. The
        mirror case, `less_specific`, is arguably defensible but requires a real
        containment/entailment check rather than a token-count comparison, so it
        stays excluded until such a check exists. Omission gating fails closed.
        """
        return (
            self.relation == "same_proposition"
            and vocab.confidence_rank(self.confidence) >= 2
            and not self.divergences
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "alignmentId": self.alignment_id,
            "claimA": self.claim_a,
            "claimB": self.claim_b,
            "relation": self.relation,
            "confidence": self.confidence,
            "overlapScore": round(self.overlap_score, 4),
            "rationale": self.rationale,
            "divergences": list(self.divergences),
            "usableForOmission": self.is_usable_for_omission,
        }


def content_tokens(text: str) -> frozenset[str]:
    return frozenset(
        token.lower() for token in _WORD.findall(text) if token.lower() not in _STOPWORDS
    )


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def align_pair(claim_a: Claim, claim_b: Claim) -> ClaimAlignment:
    """Deterministic, conservative alignment of two claims.

    A lexical baseline plus bounded factual-divergence guards. It is NOT
    semantic understanding: anything short of strong overlap returns
    `uncertain`, and — since review finding M-01 — any detected numeric,
    temporal or polarity conflict blocks a high-overlap pair from being treated
    as agreement, no matter how similar the wording.

    The governing rule is that unresolved contradiction may never become
    evidentiary support. When a conflict is detected but cannot be adjudicated,
    the answer is `uncertain`, not `compatible`.
    """
    text_a = claim_a.normalized_proposition
    text_b = claim_b.normalized_proposition
    tokens_a = content_tokens(text_a)
    tokens_b = content_tokens(text_b)
    overlap = _jaccard(tokens_a, tokens_b)

    divergences = detect_divergence(text_a, text_b)
    divergence_labels = tuple(f"{d.kind}: {d.detail}" for d in divergences)

    alignment_id = "align-" + hashlib.sha256(
        f"{claim_a.claim_id}|{claim_b.claim_id}".encode()
    ).hexdigest()[:16]

    if overlap < 0.20:
        return ClaimAlignment(
            alignment_id=alignment_id, claim_a=claim_a.claim_id, claim_b=claim_b.claim_id,
            relation="unrelated", confidence="Medium", overlap_score=overlap,
            rationale=f"content-token overlap {overlap:.2f} is below the relatedness floor",
            divergences=divergence_labels,
        )

    if overlap < 0.45:
        return ClaimAlignment(
            alignment_id=alignment_id, claim_a=claim_a.claim_id, claim_b=claim_b.claim_id,
            relation="uncertain", confidence="Low", overlap_score=overlap,
            rationale=(
                f"content-token overlap {overlap:.2f} is ambiguous; a lexical baseline "
                "cannot establish propositional identity at this level"
            ),
            divergences=divergence_labels,
        )

    # From here overlap is high. Divergence checks run BEFORE any agreement
    # relation can be assigned — this is the M-01 guard.
    if has_negation_conflict(divergences):
        return ClaimAlignment(
            alignment_id=alignment_id, claim_a=claim_a.claim_id, claim_b=claim_b.claim_id,
            relation="contradictory", confidence="Low", overlap_score=overlap,
            rationale=(
                f"high overlap ({overlap:.2f}) with differing negation polarity; "
                "flagged for review rather than treated as agreement"
            ),
            divergences=divergence_labels,
        )

    if divergences:
        return ClaimAlignment(
            alignment_id=alignment_id, claim_a=claim_a.claim_id, claim_b=claim_b.claim_id,
            relation="uncertain", confidence="Low", overlap_score=overlap,
            rationale=(
                f"high overlap ({overlap:.2f}) masks a factual conflict "
                f"({describe(divergences)}); shared vocabulary is not agreement, and the "
                "conflict cannot be adjudicated lexically"
            ),
            divergences=divergence_labels,
        )

    if overlap >= 0.80:
        return ClaimAlignment(
            alignment_id=alignment_id, claim_a=claim_a.claim_id, claim_b=claim_b.claim_id,
            relation="same_proposition", confidence="Medium", overlap_score=overlap,
            rationale=(
                f"content-token overlap {overlap:.2f} indicates the same proposition, "
                "with no numeric, temporal, polarity or negation conflict detected"
            ),
            divergences=divergence_labels,
        )

    # Strict superset of content tokens reads as a specificity relation.
    if tokens_a > tokens_b:
        relation = "more_specific"
    elif tokens_b > tokens_a:
        relation = "less_specific"
    else:
        relation = "compatible"

    return ClaimAlignment(
        alignment_id=alignment_id, claim_a=claim_a.claim_id, claim_b=claim_b.claim_id,
        relation=relation, confidence="Medium", overlap_score=overlap,
        rationale=f"content-token overlap {overlap:.2f} with {relation} token coverage",
        divergences=divergence_labels,
    )


def align_claims(
    target: Sequence[Claim], others: Sequence[Claim]
) -> list[ClaimAlignment]:
    """Align every target claim against every other claim.

    All relations are returned, including `unrelated` and `uncertain`. Callers
    must filter deliberately; nothing is dropped here, so an audit can always
    see what the aligner actually concluded.
    """
    out: list[ClaimAlignment] = []
    for claim_a in target:
        for claim_b in others:
            if claim_a.claim_id == claim_b.claim_id:
                continue
            out.append(align_pair(claim_a, claim_b))
    return out


def make_claim_id(proposition: str) -> str:
    return "claim-" + hashlib.sha256(proposition.strip().lower().encode()).hexdigest()[:16]
