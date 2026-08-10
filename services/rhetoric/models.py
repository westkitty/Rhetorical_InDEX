"""Finding and AnalysisRun.

AnalysisRun is created BEFORE analysis begins and owns coverage truth. The UI
derives scan state from it and must never independently decide that a scan was
"complete" — that is how a partial scan silently becomes a confident one.

Coverage is explicit and reconciled: every passage is in exactly one of
processed / failed / unprocessed, and the invariant is asserted, not assumed.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from . import vocabulary as vocab
from .validation import DetectorFailure


@dataclass(frozen=True)
class Finding:
    finding_id: str
    analysis_run_id: str
    article_id: str
    passage_id: str
    mechanism_id: str
    family: str
    excerpt: str
    start_char: int
    end_char: int
    occurrence_index: int
    pressure: str
    confidence: str
    state: str
    voice_class: str
    triggered_criteria: tuple[str, ...]
    failed_criteria: tuple[str, ...] = ()
    nearest_neighbors: tuple[str, ...] = ()
    pressure_factors: tuple[str, ...] = ()
    confidence_factors: tuple[str, ...] = ()
    detector_votes: tuple[dict[str, Any], ...] = ()
    alternate_interpretation: str | None = None
    taxonomy_version: str = ""
    detector_version: str = ""

    def __post_init__(self) -> None:
        if self.mechanism_id in vocab.CROSS_DOCUMENT_MECHANISMS:
            raise ValueError(
                f"{self.mechanism_id!r} is cross-document and cannot exist as an intrinsic Finding"
            )
        if self.pressure not in vocab.PRESSURE:
            raise ValueError(f"invalid pressure: {self.pressure!r}")
        if self.confidence not in vocab.CONFIDENCE:
            raise ValueError(f"invalid confidence: {self.confidence!r}")
        if self.voice_class not in vocab.VOICE:
            raise ValueError(f"invalid voice class: {self.voice_class!r}")
        if self.state not in vocab.FINDING_STATE:
            raise ValueError(f"invalid finding state: {self.state!r}")
        if self.end_char <= self.start_char:
            raise ValueError("inverted or empty finding span")
        if not self.triggered_criteria:
            raise ValueError("a Finding must carry at least one triggered criterion")

    @property
    def span_key(self) -> tuple[str, str, int, int]:
        return (self.passage_id, self.mechanism_id, self.start_char, self.end_char)

    def to_dict(self) -> dict[str, Any]:
        return {
            "findingId": self.finding_id,
            "analysisRunId": self.analysis_run_id,
            "articleId": self.article_id,
            "passageId": self.passage_id,
            "mechanismId": self.mechanism_id,
            "family": self.family,
            "excerpt": self.excerpt,
            "startChar": self.start_char,
            "endChar": self.end_char,
            "occurrenceIndex": self.occurrence_index,
            "pressure": self.pressure,
            "confidence": self.confidence,
            "state": self.state,
            "voiceClass": self.voice_class,
            "triggeredCriteria": list(self.triggered_criteria),
            "failedCriteria": list(self.failed_criteria),
            "nearestNeighbors": list(self.nearest_neighbors),
            "pressureFactors": list(self.pressure_factors),
            "confidenceFactors": list(self.confidence_factors),
            "detectorVotes": [dict(v) for v in self.detector_votes],
            "alternateInterpretation": self.alternate_interpretation,
            "taxonomyVersion": self.taxonomy_version,
            "detectorVersion": self.detector_version,
        }


@dataclass
class AnalysisRun:
    run_id: str
    article_id: str
    content_hash: str
    taxonomy_version: str
    detector_version: str
    provider: dict[str, str]
    all_passage_ids: tuple[str, ...]
    status: str = "processing"
    processed_passage_ids: list[str] = field(default_factory=list)
    failed_passage_ids: list[str] = field(default_factory=list)
    started_at: str | None = None
    completed_at: str | None = None
    batches: list[dict[str, Any]] = field(default_factory=list)
    failures: list[DetectorFailure] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    finding_count: int = 0
    rejected_candidate_count: int = 0

    @property
    def unprocessed_passage_ids(self) -> tuple[str, ...]:
        handled = set(self.processed_passage_ids) | set(self.failed_passage_ids)
        return tuple(pid for pid in self.all_passage_ids if pid not in handled)

    @property
    def coverage_ratio(self) -> float:
        # Counted over DISTINCT passages. A duplicate append must never be able
        # to report 100% coverage while a passage was in fact never analyzed —
        # that is partial state masquerading as complete.
        if not self.all_passage_ids:
            return 0.0
        known = set(self.all_passage_ids)
        covered = len({pid for pid in self.processed_passage_ids if pid in known})
        return covered / len(known)

    @property
    def is_complete_coverage(self) -> bool:
        return (
            not self.failed_passage_ids
            and not self.unprocessed_passage_ids
            and set(self.processed_passage_ids) == set(self.all_passage_ids)
        )

    def assert_coverage_invariant(self) -> None:
        """Every passage is in exactly one bucket. Asserted, not assumed."""
        processed = set(self.processed_passage_ids)
        failed = set(self.failed_passage_ids)
        unprocessed = set(self.unprocessed_passage_ids)

        if len(processed) != len(self.processed_passage_ids):
            raise AssertionError(
                "processed_passage_ids contains duplicates; coverage accounting "
                "would overstate how much of the article was analyzed"
            )
        if len(failed) != len(self.failed_passage_ids):
            raise AssertionError("failed_passage_ids contains duplicates")
        unknown = (processed | failed) - set(self.all_passage_ids)
        if unknown:
            raise AssertionError(f"coverage references passages not in this article: {sorted(unknown)}")
        overlap = (processed & failed) | (processed & unprocessed) | (failed & unprocessed)
        if overlap:
            raise AssertionError(f"passages in multiple coverage buckets: {sorted(overlap)}")
        union = processed | failed | unprocessed
        if union != set(self.all_passage_ids):
            missing = set(self.all_passage_ids) - union
            extra = union - set(self.all_passage_ids)
            raise AssertionError(f"coverage buckets do not partition passages (missing={sorted(missing)}, extra={sorted(extra)})")

    def finalize(self, *, completed_at: str | None = None) -> None:
        self.assert_coverage_invariant()
        if not self.processed_passage_ids and (self.failed_passage_ids or self.all_passage_ids):
            self.status = "failed"
        elif self.is_complete_coverage:
            self.status = "complete"
        else:
            self.status = "partial"
        self.completed_at = completed_at
        if self.status not in vocab.ANALYSIS_RUN_STATUS:
            raise ValueError(f"invalid analysis run status: {self.status!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "runId": self.run_id,
            "articleId": self.article_id,
            "contentHash": self.content_hash,
            "taxonomyVersion": self.taxonomy_version,
            "detectorVersion": self.detector_version,
            "provider": dict(self.provider),
            "status": self.status,
            "startedAt": self.started_at,
            "completedAt": self.completed_at,
            "allPassageIds": list(self.all_passage_ids),
            "processedPassageIds": list(self.processed_passage_ids),
            "failedPassageIds": list(self.failed_passage_ids),
            "unprocessedPassageIds": list(self.unprocessed_passage_ids),
            "coverageRatio": round(self.coverage_ratio, 4),
            "isCompleteCoverage": self.is_complete_coverage,
            "batches": [dict(b) for b in self.batches],
            "failures": [f.to_dict() for f in self.failures],
            "warnings": list(self.warnings),
            "findingCount": self.finding_count,
            "rejectedCandidateCount": self.rejected_candidate_count,
        }


def make_run_id(
    *,
    content_hash: str,
    detector_version: str,
    provider_id: str,
    taxonomy_version: str,
    provider_version: str,
    salt: str = "",
) -> str:
    """Deterministic run id covering every semantically relevant analysis input.

    Review finding O-06: taxonomy version and provider version were absent, so
    two runs whose results could legitimately differ — different taxonomy
    definitions, different provider build — shared one identity. Run ids (and
    the finding ids derived from them) must change when the analysis inputs
    change, or cached/compared results silently conflate different analyses.

    Still derived purely from inputs: no clock, no RNG, fully reproducible.
    """
    payload = "|".join(
        (content_hash, detector_version, taxonomy_version, provider_id, provider_version, salt)
    )
    return f"run-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:20]}"


def make_finding_id(
    *, run_id: str, passage_id: str, mechanism_id: str, start: int, end: int, occurrence: int
) -> str:
    payload = f"{run_id}|{passage_id}|{mechanism_id}|{start}|{end}|{occurrence}"
    return f"fnd-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:20]}"


def batch_passages(passage_ids: Sequence[str], batch_size: int) -> list[tuple[str, ...]]:
    """Deterministic batching that never splits a passage.

    Passage boundaries are preserved so span coordinates stay passage-local and
    a batch failure loses whole passages rather than half a sentence.
    """
    if batch_size < 1:
        raise ValueError("batch size must be >= 1")
    return [tuple(passage_ids[i:i + batch_size]) for i in range(0, len(passage_ids), batch_size)]


def dedupe_findings(findings: Iterable[Finding]) -> list[Finding]:
    """Collapse duplicates by stable identity, preserving multi-tag output.

    Identity is (passage, mechanism, start, end). Two different mechanisms on
    the same span are NOT duplicates — that is the multi-tag case the product
    depends on — so mechanism participates in the key.

    When the same identity appears twice (e.g. produced in overlapping context
    batches), the surviving record keeps the higher confidence and merges
    detector votes, so overlap cannot inflate counts.
    """
    by_key: dict[tuple[str, str, int, int], Finding] = {}
    for finding in findings:
        existing = by_key.get(finding.span_key)
        if existing is None:
            by_key[finding.span_key] = finding
            continue
        keep, drop = (
            (finding, existing)
            if vocab.confidence_rank(finding.confidence) > vocab.confidence_rank(existing.confidence)
            else (existing, finding)
        )
        merged_votes = list(keep.detector_votes)
        for vote in drop.detector_votes:
            if vote not in merged_votes:
                merged_votes.append(vote)
        by_key[finding.span_key] = Finding(**{**keep.__dict__, "detector_votes": tuple(merged_votes)})

    return collapse_nested_same_mechanism(by_key.values())


def collapse_nested_same_mechanism(findings: Iterable[Finding]) -> list[Finding]:
    """Collapse same-mechanism spans where one fully contains another.

    Two generators can detect the same rhetorical move at different
    granularities — e.g. "refused to explain why they allowed X" (factive-wh)
    and "allowed X" (factive-allowed). Emitting both would double-count one
    move, inflating pressure profiles and corrupting span-accuracy metrics
    against a human benchmark that marked it once.

    Containment is only collapsed WITHIN a mechanism. Two different mechanisms
    on overlapping or identical spans are preserved: that is the multi-tag case
    the product is built around, and merging it would violate the rule that one
    Finding represents one mechanism.

    Survivor: higher confidence wins; on a tie the longer span wins, because the
    fuller construction is the more diagnostic annotation target.
    """
    ordered = sorted(
        findings,
        key=lambda f: (f.passage_id, f.mechanism_id, f.start_char, -(f.end_char - f.start_char)),
    )
    dropped: set[str] = set()

    for i, outer in enumerate(ordered):
        if outer.finding_id in dropped:
            continue
        for inner in ordered[i + 1:]:
            if inner.finding_id in dropped:
                continue
            if inner.passage_id != outer.passage_id or inner.mechanism_id != outer.mechanism_id:
                continue
            if inner.start_char >= outer.end_char:
                break
            contains = outer.start_char <= inner.start_char and inner.end_char <= outer.end_char
            contained = inner.start_char <= outer.start_char and outer.end_char <= inner.end_char
            if not (contains or contained):
                continue
            outer_rank = vocab.confidence_rank(outer.confidence)
            inner_rank = vocab.confidence_rank(inner.confidence)
            if inner_rank > outer_rank:
                loser = outer
            elif outer_rank > inner_rank:
                loser = inner
            else:
                outer_len = outer.end_char - outer.start_char
                inner_len = inner.end_char - inner.start_char
                loser = inner if outer_len >= inner_len else outer
            dropped.add(loser.finding_id)
            if loser.finding_id == outer.finding_id:
                break

    survivors = [f for f in ordered if f.finding_id not in dropped]
    return sorted(survivors, key=lambda f: (f.passage_id, f.start_char, f.end_char, f.mechanism_id))
