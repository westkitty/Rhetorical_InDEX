"""Stage 10: strict structured-output validation.

The governing rule is REJECT, NEVER REPAIR.

If a provider returns a verdict with missing or malformed ``criteriaTriggered``,
this module raises. It does NOT substitute the mechanism's taxonomy criteria to
make the record well-formed, because doing so would manufacture detector
evidence: the finding drawer would then show a user a criterion that no detector
actually asserted. That is the single most dangerous available shortcut in this
codebase, and it is explicitly forbidden.

Every rejection produces a ``DetectorFailure`` carrying the stage and reason, so
a rejected candidate is visible in the AnalysisRun rather than silently absent.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import vocabulary as vocab
from .document import Article, Passage

DETECTOR_SCHEMA_VERSION = "1.0.0"
_ALLOWED_APPLIES = frozenset({"yes", "no", "uncertain"})


class DetectorRejection(ValueError):
    """A structurally or semantically invalid detector output."""

    def __init__(self, reason: str, *, stage: str, passage_id: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.stage = stage
        self.passage_id = passage_id


@dataclass(frozen=True)
class DetectorFailure:
    passage_id: str
    stage: str
    reason: str
    mechanism_id: str | None = None
    excerpt: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "passageId": self.passage_id,
            "stage": self.stage,
            "reason": self.reason,
            "mechanismId": self.mechanism_id,
            "excerpt": self.excerpt,
        }


@dataclass(frozen=True)
class ResolvedSpan:
    passage_id: str
    start_char: int
    end_char: int
    excerpt: str
    occurrence_index: int


def _require_nonempty_string_list(value: Any, field_name: str, stage: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise DetectorRejection(f"{field_name} must be a list", stage=stage)
    if len(value) == 0:
        raise DetectorRejection(f"{field_name} must not be empty", stage=stage)
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise DetectorRejection(f"{field_name} entries must be non-empty strings", stage=stage)
    return tuple(value)


def validate_verdict(verdict: Any, *, mechanism_id: str, passage_id: str) -> None:
    """Validate raw provider output before it may influence a Finding."""
    stage = "contextual_verification"

    applies = getattr(verdict, "applies", None)
    if applies not in _ALLOWED_APPLIES:
        raise DetectorRejection(
            f"invalid 'applies' value: {applies!r}", stage=stage, passage_id=passage_id
        )

    certainty = getattr(verdict, "certainty", None)
    if isinstance(certainty, bool) or not isinstance(certainty, (int, float)):
        raise DetectorRejection("certainty must be numeric", stage=stage, passage_id=passage_id)
    if not 0.0 <= float(certainty) <= 1.0:
        raise DetectorRejection(
            f"certainty out of range: {certainty!r}", stage=stage, passage_id=passage_id
        )

    record = vocab.mechanism(mechanism_id)
    allowed_positive = set(record["positiveCriteria"])
    allowed_exclusion = set(record["exclusionCriteria"])

    triggered = list(getattr(verdict, "criteria_triggered", ()) or [])
    if applies in {"yes", "uncertain"}:
        # A positive or partially positive verdict MUST carry its own evidence.
        # This is where fabrication would otherwise creep in.
        _require_nonempty_string_list(triggered, "criteriaTriggered", stage)

    # Review finding M-06: it is not enough for criteria to be non-empty
    # strings. They must be VERBATIM members of this mechanism's taxonomy
    # record. Otherwise a provider can invent a plausible-sounding criterion,
    # or borrow one from a different mechanism, and the finding drawer will
    # show a user a justification the taxonomy never authorized.
    # No fuzzy matching, no auto-repair — unknown criteria are rejected.
    for criterion in triggered:
        if criterion not in allowed_positive:
            if criterion in allowed_exclusion:
                raise DetectorRejection(
                    f"criteriaTriggered contains an EXCLUSION criterion for {mechanism_id!r}: "
                    f"{criterion!r}",
                    stage=stage, passage_id=passage_id,
                )
            raise DetectorRejection(
                f"criteriaTriggered contains a criterion that is not a positive criterion of "
                f"{mechanism_id!r}: {criterion!r}",
                stage=stage, passage_id=passage_id,
            )
    if len(set(triggered)) != len(triggered):
        raise DetectorRejection(
            "criteriaTriggered contains duplicate criteria", stage=stage, passage_id=passage_id
        )

    failed = getattr(verdict, "criteria_failed", ()) or ()
    if not isinstance(failed, (list, tuple)):
        raise DetectorRejection("criteriaFailed must be a list", stage=stage, passage_id=passage_id)
    for item in failed:
        if not isinstance(item, str) or not item.strip():
            raise DetectorRejection(
                "criteriaFailed entries must be non-empty strings", stage=stage, passage_id=passage_id
            )
        if item not in allowed_exclusion:
            raise DetectorRejection(
                f"criteriaFailed contains a criterion that is not an exclusion criterion of "
                f"{mechanism_id!r}: {item!r}",
                stage=stage, passage_id=passage_id,
            )
    if len(set(failed)) != len(failed):
        raise DetectorRejection(
            "criteriaFailed contains duplicate criteria", stage=stage, passage_id=passage_id
        )

    neighbors = getattr(verdict, "nearest_neighbor_overlap", ()) or ()
    known = vocab.mechanism_ids()
    for neighbor in neighbors:
        if neighbor not in known:
            raise DetectorRejection(
                f"nearestNeighborOverlap references unknown mechanism {neighbor!r}",
                stage=stage,
                passage_id=passage_id,
            )


def resolve_span(
    passage: Passage,
    *,
    excerpt: str | None,
    occurrence_index: int | None = None,
    start_char: int | None = None,
    end_char: int | None = None,
) -> ResolvedSpan:
    """Resolve an exact span, rejecting every ambiguous or invalid form.

    Two addressing modes are accepted and they must agree:
      * excerpt (+ occurrenceIndex when the excerpt repeats)
      * explicit start/end coordinates

    If both are supplied they are cross-checked; a mismatch is a rejection, not
    a preference for one of them.
    """
    stage = "span_localization"
    text = passage.text

    if start_char is not None or end_char is not None:
        if start_char is None or end_char is None:
            raise DetectorRejection(
                "both startChar and endChar are required when using coordinates",
                stage=stage, passage_id=passage.passage_id,
            )
        if isinstance(start_char, bool) or isinstance(end_char, bool):
            raise DetectorRejection("span coordinates must be integers", stage=stage, passage_id=passage.passage_id)
        if not isinstance(start_char, int) or not isinstance(end_char, int):
            raise DetectorRejection("span coordinates must be integers", stage=stage, passage_id=passage.passage_id)
        if start_char < 0:
            raise DetectorRejection("negative startChar", stage=stage, passage_id=passage.passage_id)
        if end_char <= start_char:
            raise DetectorRejection("inverted or empty span", stage=stage, passage_id=passage.passage_id)
        if end_char > len(text):
            raise DetectorRejection("span exceeds passage length", stage=stage, passage_id=passage.passage_id)

        resolved_text = text[start_char:end_char]
        if not resolved_text.strip():
            raise DetectorRejection("span resolves to whitespace", stage=stage, passage_id=passage.passage_id)
        if excerpt is not None and resolved_text != excerpt:
            raise DetectorRejection(
                "excerpt does not match the supplied coordinates",
                stage=stage, passage_id=passage.passage_id,
            )
        occurrences = _occurrences(text, resolved_text)
        return ResolvedSpan(
            passage_id=passage.passage_id,
            start_char=start_char,
            end_char=end_char,
            excerpt=resolved_text,
            occurrence_index=occurrences.index(start_char),
        )

    if not isinstance(excerpt, str) or not excerpt:
        raise DetectorRejection("missing exact text", stage=stage, passage_id=passage.passage_id)
    if not excerpt.strip():
        raise DetectorRejection("excerpt is whitespace only", stage=stage, passage_id=passage.passage_id)

    occurrences = _occurrences(text, excerpt)
    if not occurrences:
        raise DetectorRejection("exact text not found in passage", stage=stage, passage_id=passage.passage_id)

    if len(occurrences) > 1:
        if occurrence_index is None:
            raise DetectorRejection(
                f"ambiguous repeated excerpt ({len(occurrences)} occurrences) with no occurrenceIndex",
                stage=stage, passage_id=passage.passage_id,
            )
        if isinstance(occurrence_index, bool) or not isinstance(occurrence_index, int):
            raise DetectorRejection("occurrenceIndex must be an integer", stage=stage, passage_id=passage.passage_id)
        if not 0 <= occurrence_index < len(occurrences):
            raise DetectorRejection(
                f"occurrenceIndex {occurrence_index} out of range (0..{len(occurrences) - 1})",
                stage=stage, passage_id=passage.passage_id,
            )
        start = occurrences[occurrence_index]
        resolved_occurrence = occurrence_index
    else:
        if occurrence_index is not None:
            if isinstance(occurrence_index, bool) or not isinstance(occurrence_index, int):
                raise DetectorRejection("occurrenceIndex must be an integer", stage=stage, passage_id=passage.passage_id)
            if occurrence_index != 0:
                raise DetectorRejection(
                    "occurrenceIndex supplied for a unique excerpt must be 0",
                    stage=stage, passage_id=passage.passage_id,
                )
        start = occurrences[0]
        resolved_occurrence = 0

    return ResolvedSpan(
        passage_id=passage.passage_id,
        start_char=start,
        end_char=start + len(excerpt),
        excerpt=excerpt,
        occurrence_index=resolved_occurrence,
    )


def _occurrences(text: str, needle: str) -> list[int]:
    positions: list[int] = []
    cursor = 0
    while True:
        found = text.find(needle, cursor)
        if found < 0:
            return positions
        positions.append(found)
        cursor = found + 1


def validate_finding_payload(
    payload: dict[str, Any],
    *,
    article: Article,
    allowed_mechanisms: frozenset[str],
    taxonomy_version: str,
    detector_schema_version: str = DETECTOR_SCHEMA_VERSION,
) -> ResolvedSpan:
    """Validate a complete finding payload. Returns the resolved span.

    Rejects: unknown/cross-document mechanism, invalid pressure/confidence/
    voice, unknown passage, missing or non-round-tripping excerpt, ambiguous
    repeats, invalid occurrence selectors, out-of-range and inverted spans,
    empty or malformed criteria, and unknown taxonomy/schema versions.
    """
    stage = "finding_validation"

    if payload.get("detectorSchemaVersion", detector_schema_version) != detector_schema_version:
        raise DetectorRejection(
            f"unknown detector schema version: {payload.get('detectorSchemaVersion')!r}", stage=stage
        )
    if payload.get("taxonomyVersion", taxonomy_version) != taxonomy_version:
        raise DetectorRejection(
            f"unknown taxonomy version: {payload.get('taxonomyVersion')!r}", stage=stage
        )

    mechanism_id = payload.get("mechanismId")
    if mechanism_id not in vocab.mechanism_ids():
        raise DetectorRejection(f"unknown mechanism: {mechanism_id!r}", stage=stage)
    if mechanism_id in vocab.CROSS_DOCUMENT_MECHANISMS:
        raise DetectorRejection(
            f"cross-document mechanism {mechanism_id!r} cannot be emitted by an intrinsic scan",
            stage=stage,
        )
    if mechanism_id not in allowed_mechanisms:
        raise DetectorRejection(
            f"mechanism {mechanism_id!r} is outside this detector's implemented slice", stage=stage
        )

    if "mechanisms" in payload:
        raise DetectorRejection(
            "legacy plural 'mechanisms' field is prohibited; one finding = one mechanism", stage=stage
        )

    if payload.get("pressure") not in vocab.PRESSURE:
        raise DetectorRejection(f"invalid pressure: {payload.get('pressure')!r}", stage=stage)
    if payload.get("confidence") not in vocab.CONFIDENCE:
        raise DetectorRejection(f"invalid confidence: {payload.get('confidence')!r}", stage=stage)
    if payload.get("voiceClass") not in vocab.VOICE:
        raise DetectorRejection(f"invalid voice class: {payload.get('voiceClass')!r}", stage=stage)

    passage_id = payload.get("passageId")
    try:
        passage = article.passage(passage_id) if isinstance(passage_id, str) else None
    except KeyError:
        passage = None
    if passage is None:
        raise DetectorRejection(f"unknown passage: {passage_id!r}", stage=stage)

    _require_nonempty_string_list(payload.get("triggeredCriteria"), "triggeredCriteria", stage)

    return resolve_span(
        passage,
        excerpt=payload.get("excerpt"),
        occurrence_index=payload.get("occurrenceIndex"),
        start_char=payload.get("startChar"),
        end_char=payload.get("endChar"),
    )
