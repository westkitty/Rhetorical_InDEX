#!/usr/bin/env python3
"""Benchmark corpus integrity validator.

Review finding M-09: `adjudicationStatus == "adjudicated"` was treated as
sufficient to score a document. It is not. Malformed gold data silently
corrupts every metric computed from it, and because a benchmark is the thing we
will use to judge the detector, corrupt gold is worse than no gold.

Two outcomes are deliberately distinguished:

  * NOT adjudicated (draft / annotated / disputed)  -> ignored by the metric
    loader. Normal, not an error.
  * adjudicated BUT invalid                          -> FATAL corpus-integrity
    error. Never silently skipped, because silently skipping a broken gold file
    makes the corpus look smaller rather than broken.

Usage:
    python3 benchmarks/scripts/validate_corpus.py [--corpus DIR] [--json]

Exit codes: 0 = every adjudicated document valid (possibly zero of them),
            1 = at least one adjudicated document is invalid.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.rhetoric import vocabulary as vocab  # noqa: E402
from services.rhetoric.pipeline import IMPLEMENTED_MECHANISMS  # noqa: E402

VALID_STATUS = {"draft", "annotated", "disputed", "adjudicated"}
VALID_GENRE = {"straight_news", "analysis", "opinion", "press_release", "other"}
SCORED_STATUS = "adjudicated"
MIN_ANNOTATORS = 2

# B-05: module-level so a schema-parity test can assert these agree with
# benchmarks/corpus/_schema.json's `decision` enum, rather than the two
# drifting apart silently.
VALID_RESOLUTION_DECISIONS = {
    "uphold_a", "uphold_b", "merge", "drop", "split", "adjudicator_add", "unresolvable",
}
# C-03: per-decision cardinality as
# (min proposalIds, max proposalIds, min resulting gold, max resulting gold).
# `None` means unbounded. Without these, `merge` with an empty `proposalIds`
# grounded arbitrary gold with no proposal origin — a silent backdoor around
# `adjudicator_add`, which exists precisely to make that case explicit.
RESOLUTION_CARDINALITY: dict[str, tuple[int, int | None, int, int | None]] = {
    "uphold_a": (1, 1, 1, 1),
    "uphold_b": (1, 1, 1, 1),
    "merge": (2, None, 1, 1),
    "drop": (1, None, 0, 0),
    "split": (1, None, 2, None),
    "adjudicator_add": (0, 0, 1, 1),
}

# ADJUDICATION.md §2 auto-merge threshold.
AUTO_MERGE_MIN_IOU = 0.8


def _span_iou(a: tuple[int, int], b: tuple[int, int]) -> float:
    """Intersection-over-union of two half-open character spans."""
    overlap = min(a[1], b[1]) - max(a[0], b[0])
    if overlap <= 0:
        return 0.0
    union = max(a[1], b[1]) - min(a[0], b[0])
    return overlap / union if union > 0 else 0.0


def _auto_merge_span(
    annotation: dict, proposals: list[dict[str, Any]], declared_annotators: set[str]
) -> tuple[int, int] | None:
    """The protocol-defined merged span, if this gold annotation is a genuine
    UNANIMOUS auto-merge; ``None`` if adjudication was required instead.

    ADJUDICATION.md §2: annotations merge WITHOUT adjudication only when they
    share mechanism, passage, pressure and voice, and their spans overlap at
    IoU >= AUTO_MERGE_MIN_IOU. The merged span is the INTERSECTION — the text
    every annotator agreed carries the mechanism.

    Review finding D-02: requiring merely "at least MIN_ANNOTATORS agreeing
    annotators" silently erased dissent once a document had three or more
    annotators. A and B agreeing while C proposed a different pressure, a
    different voice, or nothing at all still auto-merged on the strength of
    A+B — discarding exactly the disagreement the corpus exists to preserve.

    The policy is therefore UNANIMITY, deliberately stricter than majority
    vote: EVERY annotator declared in ``annotatorIds`` must contribute
    EXACTLY ONE qualifying proposal to the consensus cluster. Any of

      * an annotator with no matching proposal (absence / presence dissent)
      * an annotator with more than one matching proposal (ambiguous cluster)
      * a pressure, voice or mechanism difference (those proposals simply do
        not qualify, so their annotator ends up absent)
      * any proposal pair below the IoU threshold

    means adjudication is required. At Alpha, conservative escalation is
    preferable to silently erasing a dissenting annotator.
    """
    if not declared_annotators:
        return None

    mechanism = annotation.get("mechanismId")
    ordinal = annotation.get("passageOrdinal")
    pressure = annotation.get("pressure")
    voice = annotation.get("voiceClass")

    qualifying = [
        p for p in proposals
        if p["mechanismId"] == mechanism
        and p["passageOrdinal"] == ordinal
        and p["pressure"] == pressure
        and p["voiceClass"] == voice
    ]

    # Every declared annotator must appear exactly once in the cluster.
    by_annotator: dict[str, list[dict[str, Any]]] = {}
    for proposal in qualifying:
        by_annotator.setdefault(proposal["annotatorId"], []).append(proposal)
    if set(by_annotator) != declared_annotators:
        return None
    if any(len(group) != 1 for group in by_annotator.values()):
        return None

    spans = [(p["startChar"], p["endChar"]) for p in qualifying]
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            if _span_iou(spans[i], spans[j]) < AUTO_MERGE_MIN_IOU:
                return None

    return (max(s[0] for s in spans), min(s[1] for s in spans))


def _spans_overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return min(a[1], b[1]) > max(a[0], b[0])


@dataclass
class DocumentReport:
    path: str
    adjudication_status: str | None = None
    scored: bool = False
    errors: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "adjudicationStatus": self.adjudication_status,
            "scored": self.scored,
            "valid": self.valid,
            "errors": list(self.errors),
        }


def _is_int(value: Any) -> bool:
    """Booleans are ints in Python; gold coordinates must not be booleans."""
    return isinstance(value, int) and not isinstance(value, bool)


def validate_document(data: Any, *, path: str, expected_taxonomy: str) -> DocumentReport:
    report = DocumentReport(path=path)
    err = report.errors.append

    if not isinstance(data, dict):
        err("document is not a JSON object")
        return report

    status = data.get("adjudicationStatus")
    report.adjudication_status = status if isinstance(status, str) else None
    if status not in VALID_STATUS:
        err(f"adjudicationStatus must be one of {sorted(VALID_STATUS)}, got {status!r}")
        return report

    # Non-adjudicated documents are simply not scored; they are not errors.
    report.scored = status == SCORED_STATUS
    if not report.scored:
        return report

    for required in ("articleId", "genre", "taxonomyVersion", "passages", "annotations"):
        if required not in data:
            err(f"missing required field: {required}")
    if report.errors:
        return report

    if not isinstance(data["articleId"], str) or not data["articleId"].strip():
        err("articleId must be a non-empty string")
    if data["genre"] not in VALID_GENRE:
        err(f"genre must be one of {sorted(VALID_GENRE)}, got {data['genre']!r}")

    # Stale taxonomy versions must never contribute to current metrics: an
    # annotation made against a different definition is measuring something else.
    if data["taxonomyVersion"] != expected_taxonomy:
        err(
            f"taxonomyVersion {data['taxonomyVersion']!r} does not match the current "
            f"taxonomy {expected_taxonomy!r}; re-adjudicate before scoring"
        )

    passages = data["passages"]
    if not isinstance(passages, list) or not passages:
        err("passages must be a non-empty array")
        return report

    texts: dict[int, str] = {}
    seen_ordinals: set[int] = set()
    for index, passage in enumerate(passages):
        if not isinstance(passage, dict):
            err(f"passages[{index}] is not an object")
            continue
        ordinal = passage.get("ordinal")
        if not _is_int(ordinal) or ordinal < 0:
            err(f"passages[{index}].ordinal must be a non-negative integer, got {ordinal!r}")
            continue
        if ordinal in seen_ordinals:
            err(f"duplicate passage ordinal {ordinal}")
            continue
        seen_ordinals.add(ordinal)
        if passage.get("passageType") not in vocab.PASSAGE_TYPE:
            err(f"passages[{index}].passageType invalid: {passage.get('passageType')!r}")
        text = passage.get("text")
        if not isinstance(text, str) or not text.strip():
            err(f"passages[{index}].text must be non-empty")
            continue
        texts[ordinal] = text

    if seen_ordinals and sorted(seen_ordinals) != list(range(len(seen_ordinals))):
        err(f"passage ordinals must be contiguous from 0, got {sorted(seen_ordinals)}")

    annotations = data["annotations"]
    if not isinstance(annotations, list):
        err("annotations must be an array")
        return report

    seen_ids: set[str] = set()
    annotation_records: dict[str, dict] = {}
    for index, ann in enumerate(annotations):
        label = f"annotations[{index}]"
        if not isinstance(ann, dict):
            err(f"{label} is not an object")
            continue
        if "mechanisms" in ann:
            err(f"{label} uses the prohibited plural 'mechanisms' field")

        ann_id = ann.get("annotationId")
        if not isinstance(ann_id, str) or not ann_id.strip():
            err(f"{label}.annotationId must be a non-empty string")
        elif ann_id in seen_ids:
            err(f"duplicate annotationId {ann_id!r}")
        else:
            seen_ids.add(ann_id)
            annotation_records[ann_id] = ann

        mechanism = ann.get("mechanismId")
        if mechanism not in vocab.mechanism_ids():
            err(f"{label}.mechanismId unknown: {mechanism!r}")
        elif mechanism in vocab.CROSS_DOCUMENT_MECHANISMS:
            err(f"{label}.mechanismId {mechanism!r} is cross-document and cannot be annotated intrinsically")

        ordinal = ann.get("passageOrdinal")
        if not _is_int(ordinal) or ordinal not in texts:
            err(f"{label}.passageOrdinal does not reference an existing passage: {ordinal!r}")
        else:
            text = texts[ordinal]
            start, end = ann.get("startChar"), ann.get("endChar")
            if not _is_int(start) or not _is_int(end):
                err(f"{label} startChar/endChar must be integers (booleans rejected)")
            elif start < 0:
                err(f"{label}.startChar must be >= 0")
            elif end <= start:
                err(f"{label}.endChar must be greater than startChar")
            elif end > len(text):
                err(f"{label}.endChar {end} exceeds passage length {len(text)}")
            else:
                excerpt = ann.get("excerpt")
                if not isinstance(excerpt, str):
                    err(f"{label}.excerpt must be a string")
                elif text[start:end] != excerpt:
                    err(
                        f"{label}.excerpt does not round-trip: stored {excerpt!r}, "
                        f"passage slice {text[start:end]!r}"
                    )

        if ann.get("pressure") not in vocab.PRESSURE:
            err(f"{label}.pressure invalid: {ann.get('pressure')!r}")
        if ann.get("reviewerConfidence") not in vocab.CONFIDENCE:
            err(f"{label}.reviewerConfidence invalid: {ann.get('reviewerConfidence')!r}")
        # Voice is mandatory: the annotation guide requires it on every
        # annotation, and voice accuracy is a reported benchmark metric.
        if ann.get("voiceClass") not in vocab.VOICE:
            err(f"{label}.voiceClass is required and must be a known voice: {ann.get('voiceClass')!r}")

    # ---- adjudication coherence ----
    # The Python validator is the load-bearing scoring gate; the JSON Schema is
    # documentation that nothing in this pipeline executes. So annotatorIds is
    # validated here to the same strictness the schema promises (array, >= 2
    # items, unique, every item a non-empty string) rather than relying on
    # `{a for a in annotators if isinstance(a, str)}`, which silently DISCARDED
    # non-string entries and de-duplicated repeats before counting — so
    # ["a", 7, "b"] and ["a", "b", "b"] both passed.
    annotators = data.get("annotatorIds")
    declared_annotators: set[str] = set()
    if not isinstance(annotators, list):
        err(f"annotatorIds must be an array, got {annotators!r}")
    else:
        seen_annotators: set[str] = set()
        for index, entry in enumerate(annotators):
            # bool is a subclass of str-adjacent int trickery elsewhere; here it
            # is simply not a string, and must not be coerced into one.
            if not isinstance(entry, str) or isinstance(entry, bool):
                err(f"annotatorIds[{index}] must be a string, got {entry!r}")
                continue
            if not entry.strip():
                err(f"annotatorIds[{index}] must be a non-empty string")
                continue
            if entry in seen_annotators:
                err(f"annotatorIds contains duplicate entry {entry!r}")
                continue
            seen_annotators.add(entry)
        declared_annotators = seen_annotators
        if len(annotators) < MIN_ANNOTATORS or len(seen_annotators) < MIN_ANNOTATORS:
            err(
                f"adjudicated documents require at least {MIN_ANNOTATORS} distinct independent "
                f"annotators in annotatorIds, got {annotators!r}"
            )

    # M-12 / A-02: each annotator's ORIGINAL independent submission RECORD must
    # be preserved, even when that annotator proposed nothing. The unit of
    # preservation is the record (one per annotator, carrying a `proposals`
    # array that MAY be empty) — never an individual proposal. That is what
    # makes a genuine hard negative ("two annotators independently reviewed
    # this and found zero rhetorical mechanisms") representable and VALID,
    # while a document with fewer than MIN_ANNOTATORS preserved records is
    # REJECTED regardless of how many proposals those records happen to
    # contain. Counting non-empty proposal lists (the previous `if proposals:`
    # guard) is exactly the bug: it let an empty `annotatorSubmissions: []`
    # skip this check entirely, silently discarding annotation history.
    proposal_ids: set[str] = set()
    # B-04 / C-02: every well-typed proposal, recorded WITH its annotator and
    # its full agreement-relevant shape. C-02: the earlier version kept only a
    # set of (mechanism, ordinal, start, end) fingerprints and treated a gold
    # annotation as auto-merged if it matched ANY ONE of them — which is not
    # consensus at all, merely evidence that a single annotator proposed it.
    # Auto-merge per ADJUDICATION.md §2 requires agreement between at least two
    # distinct annotators, so pressure, voice and annotator identity all have to
    # survive to the grounding check below.
    proposal_records: list[dict[str, Any]] = []
    proposal_id_owner: dict[str, str] = {}
    # D-01: resolutions must be shown to DERIVE their gold from the proposals
    # they cite, so the full source record has to be reachable by id.
    proposal_by_id: dict[str, dict[str, Any]] = {}
    if "annotatorSubmissions" not in data:
        err("annotatorSubmissions is required for adjudicated documents")
        submissions: list[Any] = []
    else:
        submissions = data["annotatorSubmissions"]
        if not isinstance(submissions, list):
            err("annotatorSubmissions must be an array")
            submissions = []

    submission_ids: set[str] = set()
    submission_annotator_ids: set[str] = set()
    for index, submission in enumerate(submissions):
        label = f"annotatorSubmissions[{index}]"
        if not isinstance(submission, dict):
            err(f"{label} is not an object")
            continue

        submission_id = submission.get("submissionId")
        if not isinstance(submission_id, str) or not submission_id.strip():
            err(f"{label}.submissionId must be a non-empty string")
        elif submission_id in submission_ids:
            err(f"duplicate submissionId {submission_id!r}")
        else:
            submission_ids.add(submission_id)

        annotator_id = submission.get("annotatorId")
        if not isinstance(annotator_id, str) or not annotator_id.strip():
            err(f"{label}.annotatorId must be a non-empty string")
        elif annotator_id in submission_annotator_ids:
            err(
                f"{label}.annotatorId {annotator_id!r} has more than one submission record; "
                "each annotator contributes exactly one, whose proposals array may be empty"
            )
        else:
            submission_annotator_ids.add(annotator_id)

        proposals = submission.get("proposals")
        if not isinstance(proposals, list):
            err(f"{label}.proposals must be an array (use [] to record zero findings)")
            continue

        for p_index, proposal in enumerate(proposals):
            p_label = f"{label}.proposals[{p_index}]"
            if not isinstance(proposal, dict):
                err(f"{p_label} is not an object")
                continue
            for required in ("proposalId", "mechanismId", "passageOrdinal", "startChar",
                              "endChar", "excerpt", "pressure", "reviewerConfidence", "voiceClass"):
                if required not in proposal:
                    err(f"{p_label} missing required field {required}")

            # B-03: every field below is validated by VALUE and TYPE, not
            # merely by key presence. The previous version silently skipped
            # validation whenever a field had the wrong type (a bool
            # passageOrdinal, a string startChar, a non-string excerpt) —
            # wrong-typed data passed with zero errors because the guarding
            # `and`/`isinstance` conditions were false and there was no
            # `else` branch to report that. Every branch below has an
            # explicit failure path; nothing falls through silently.
            if "proposalId" in proposal:
                pid = proposal.get("proposalId")
                if not isinstance(pid, str) or not pid.strip():
                    err(f"{p_label}.proposalId must be a non-empty string")
                elif pid in proposal_ids:
                    err(f"duplicate proposalId {pid!r}")
                else:
                    proposal_ids.add(pid)

            if "mechanismId" in proposal:
                mechanism = proposal.get("mechanismId")
                if mechanism not in vocab.mechanism_ids():
                    err(f"{p_label}.mechanismId unknown: {mechanism!r}")
                elif mechanism in vocab.CROSS_DOCUMENT_MECHANISMS:
                    err(
                        f"{p_label}.mechanismId {mechanism!r} is cross-document and cannot "
                        "be proposed intrinsically"
                    )

            if "passageOrdinal" in proposal:
                ordinal = proposal.get("passageOrdinal")
                if not _is_int(ordinal) or ordinal not in texts:
                    err(f"{p_label}.passageOrdinal does not reference an existing passage: {ordinal!r}")
                else:
                    text = texts[ordinal]
                    start, end = proposal.get("startChar"), proposal.get("endChar")
                    if not _is_int(start) or not _is_int(end):
                        err(f"{p_label} startChar/endChar must be integers (booleans rejected)")
                    elif start < 0:
                        err(f"{p_label}.startChar must be >= 0")
                    elif end <= start:
                        err(f"{p_label}.endChar must be greater than startChar")
                    elif end > len(text):
                        err(f"{p_label}.endChar {end} exceeds passage length {len(text)}")
                    else:
                        excerpt = proposal.get("excerpt")
                        if not isinstance(excerpt, str):
                            err(f"{p_label}.excerpt must be a string")
                        elif text[start:end] != excerpt:
                            err(
                                f"{p_label}.excerpt does not round-trip: stored {excerpt!r}, "
                                f"passage slice {text[start:end]!r}"
                            )

            if "pressure" in proposal and proposal.get("pressure") not in vocab.PRESSURE:
                err(f"{p_label}.pressure invalid: {proposal.get('pressure')!r}")
            if "reviewerConfidence" in proposal and proposal.get("reviewerConfidence") not in vocab.CONFIDENCE:
                err(f"{p_label}.reviewerConfidence invalid: {proposal.get('reviewerConfidence')!r}")
            if "voiceClass" in proposal and proposal.get("voiceClass") not in vocab.VOICE:
                err(f"{p_label}.voiceClass invalid: {proposal.get('voiceClass')!r}")

            fp_mechanism = proposal.get("mechanismId")
            fp_ordinal, fp_start, fp_end = (
                proposal.get("passageOrdinal"), proposal.get("startChar"), proposal.get("endChar"),
            )
            if (
                isinstance(annotator_id, str)
                and isinstance(fp_mechanism, str)
                and _is_int(fp_ordinal) and _is_int(fp_start) and _is_int(fp_end)
            ):
                # Read proposalId freshly rather than reusing the `pid` local:
                # that variable is only assigned inside `if "proposalId" in
                # proposal`, so on a proposal missing the field it would still
                # hold the PREVIOUS proposal's id and silently misattribute it.
                own_id = proposal.get("proposalId")
                proposal_records.append({
                    "annotatorId": annotator_id,
                    "proposalId": own_id if isinstance(own_id, str) else None,
                    "mechanismId": fp_mechanism,
                    "passageOrdinal": fp_ordinal,
                    "startChar": fp_start,
                    "endChar": fp_end,
                    "pressure": proposal.get("pressure"),
                    "voiceClass": proposal.get("voiceClass"),
                })
                if isinstance(own_id, str):
                    proposal_id_owner[own_id] = annotator_id
                    proposal_by_id[own_id] = proposal_records[-1]

    if len(submission_annotator_ids) < MIN_ANNOTATORS:
        err(
            f"annotatorSubmissions contain records from {len(submission_annotator_ids)} distinct "
            f"annotator(s); at least {MIN_ANNOTATORS} independent submission records must be "
            "preserved (a record's proposals array may be empty, but the record itself must exist)"
        )

    if isinstance(annotators, list):
        declared = {a for a in annotators if isinstance(a, str)}
        if submission_annotator_ids and declared and submission_annotator_ids != declared:
            err(
                f"annotatorIds {sorted(declared)} does not match the annotators who actually have "
                f"a preserved submission record {sorted(submission_annotator_ids)}"
            )

    # B-04 / C-02 / C-03: EVERY FINAL GOLD OUTCOME MUST HAVE MACHINE-READABLE
    # PROVENANCE, and that provenance must be the one the protocol actually
    # allows.
    #
    # A gold annotation is grounded when EITHER:
    #   (a) it is a genuine AUTO-MERGE under ADJUDICATION.md §2 — at least
    #       MIN_ANNOTATORS distinct annotators independently proposed the same
    #       mechanism on the same passage with the same pressure and the same
    #       voice, pairwise span IoU >= AUTO_MERGE_MIN_IOU, and the gold span
    #       is exactly the intersection of those proposals; or
    #   (b) exactly one resolution record's `resultingAnnotationIds` names it,
    #       with that record satisfying its decision's cardinality contract.
    #
    # C-02: (a) previously accepted a match against ANY ONE proposal. One
    # annotator proposing something and another not proposing it is a PRESENCE
    # DISAGREEMENT and requires adjudication — as does a pressure or voice
    # disagreement. Calling any of those an "auto-merge" silently converted one
    # annotator's opinion into consensus gold.
    resolution_ids: set[str] = set()
    grounded_by_resolution: dict[str, int] = {}

    resolutions = data.get("resolutions", [])
    if resolutions is None:
        resolutions = []
    elif not isinstance(resolutions, list):
        # Fresh-sweep finding: `resolutions or []` type-confused a non-list,
        # non-empty value (e.g. a string) into an iterable of "records" —
        # enumerate() over a string yields its CHARACTERS, one bogus
        # "resolutions[N] is not an object" error per character. Still
        # correctly invalid, but noisy and conceptually wrong; reject the
        # type directly instead.
        err("resolutions must be an array")
        resolutions = []

    for index, record in enumerate(resolutions):
        label = f"resolutions[{index}]"
        if not isinstance(record, dict):
            err(f"{label} is not an object")
            continue

        resolution_id = record.get("resolutionId")
        if resolution_id is not None:
            if not isinstance(resolution_id, str) or not resolution_id.strip():
                err(f"{label}.resolutionId must be a non-empty string")
            elif resolution_id in resolution_ids:
                err(f"duplicate resolutionId {resolution_id!r}")
            else:
                resolution_ids.add(resolution_id)

        decision = record.get("decision")
        if decision not in VALID_RESOLUTION_DECISIONS:
            err(f"{label}.decision invalid: {decision!r}")
        if decision == "unresolvable":
            err(
                f"{label} is marked 'unresolvable' in an adjudicated document; such documents "
                "must remain 'disputed' and are excluded from scoring"
            )

        adjudicator_id = record.get("adjudicatorId")
        if not isinstance(adjudicator_id, str) or not adjudicator_id.strip():
            err(f"{label}.adjudicatorId must be a non-empty string — every resolution is an "
                "adjudicator's decision and must name who made it")
        elif adjudicator_id in declared_annotators:
            # ADJUDICATION.md §3: "The adjudicator is a third person who has
            # not annotated the document." That was documented but never
            # enforced, so an annotator could adjudicate their own
            # disagreement and manufacture consensus single-handed.
            err(
                f"{label}.adjudicatorId {adjudicator_id!r} is also a declared annotator on this "
                "document; the adjudicator must be an independent third person who did not "
                "annotate it"
            )

        if "resultingAnnotationId" in record:
            err(
                f"{label} uses the removed singular 'resultingAnnotationId'; use "
                "'resultingAnnotationIds' (an array) — a 'split' decision produces more "
                "than one gold annotation and the singular field cannot represent it"
            )

        proposal_id_refs = record.get("proposalIds", [])
        if not isinstance(proposal_id_refs, list):
            err(f"{label}.proposalIds must be an array")
            proposal_id_refs = []
        else:
            for pid in proposal_id_refs:
                if pid not in proposal_ids:
                    err(f"{label} references unknown proposalId {pid!r}")

        resulting_ids = record.get("resultingAnnotationIds", [])
        if not isinstance(resulting_ids, list):
            err(f"{label}.resultingAnnotationIds must be an array")
            resulting_ids = []
        else:
            seen_here: set[str] = set()
            for rid in resulting_ids:
                if not isinstance(rid, str) or not rid.strip():
                    err(f"{label}.resultingAnnotationIds entries must be non-empty strings")
                elif rid not in annotation_records:
                    err(f"{label}.resultingAnnotationIds references unknown gold annotation {rid!r}")
                elif rid in seen_here:
                    err(f"{label}.resultingAnnotationIds lists {rid!r} more than once")
                else:
                    seen_here.add(rid)
                    grounded_by_resolution[rid] = grounded_by_resolution.get(rid, 0) + 1

        # C-03: decision-specific cardinality. Without this, `merge` with an
        # empty proposalIds was a backdoor that grounded arbitrary gold with no
        # proposal origin at all — exactly what `adjudicator_add` exists to make
        # explicit and auditable.
        spec = RESOLUTION_CARDINALITY.get(decision)
        if spec is not None:
            min_proposals, max_proposals, min_results, max_results = spec
            if len(proposal_id_refs) < min_proposals:
                err(
                    f"{label} decision {decision!r} requires at least {min_proposals} proposalId(s), "
                    f"got {len(proposal_id_refs)}"
                )
            if max_proposals is not None and len(proposal_id_refs) > max_proposals:
                err(
                    f"{label} decision {decision!r} allows at most {max_proposals} proposalId(s), "
                    f"got {len(proposal_id_refs)}"
                )
            if len(resulting_ids) < min_results:
                err(
                    f"{label} decision {decision!r} requires at least {min_results} resulting gold "
                    f"annotation(s), got {len(resulting_ids)}"
                )
            if max_results is not None and len(resulting_ids) > max_results:
                err(
                    f"{label} decision {decision!r} allows at most {max_results} resulting gold "
                    f"annotation(s), got {len(resulting_ids)}"
                )

        if decision == "merge":
            merging_annotators = {
                proposal_id_owner[pid] for pid in proposal_id_refs if pid in proposal_id_owner
            }
            if len(merging_annotators) < MIN_ANNOTATORS:
                err(
                    f"{label} decision 'merge' reconciles proposals from "
                    f"{len(merging_annotators)} distinct annotator(s); a merge is agreement "
                    f"between at least {MIN_ANNOTATORS} independent annotators, not a "
                    "consolidation of one annotator's own proposals"
                )

        if decision == "adjudicator_add":
            note = record.get("note") or record.get("rationale")
            if not isinstance(note, str) or not note.strip():
                err(f"{label} decision 'adjudicator_add' requires a non-empty note or rationale")

        # ---- D-01: the result must actually DERIVE from the cited proposals ----
        #
        # Cardinality and reference-existence prove only that a resolution
        # points at real records. They do not prove the gold has anything to do
        # with the proposals it names: an `uphold_a` citing a loaded_language
        # proposal could produce a false_dilemma annotation on an unrelated
        # span, and both a `merge` and a `split` could manufacture findings
        # somewhere else in the article entirely. "Uphold" that silently
        # substitutes a different finding is not an uphold.
        sources = [proposal_by_id[pid] for pid in proposal_id_refs if pid in proposal_by_id]
        results = [annotation_records[rid] for rid in resulting_ids if rid in annotation_records]

        if decision in {"uphold_a", "uphold_b"} and len(sources) == 1 and len(results) == 1:
            source, result = sources[0], results[0]
            for field in ("mechanismId", "passageOrdinal", "startChar", "endChar", "pressure", "voiceClass"):
                # reviewerConfidence is deliberately excluded: it is a
                # per-annotator epistemic report, not a property of the
                # rhetorical phenomenon being upheld.
                if result.get(field) != source.get(field):
                    err(
                        f"{label} decision {decision!r} claims to uphold proposal "
                        f"{source.get('proposalId')!r}, but the resulting gold annotation differs on "
                        f"{field} ({source.get(field)!r} -> {result.get(field)!r}); an uphold "
                        "preserves the cited proposal, it does not substitute a different finding"
                    )

        if decision == "merge" and sources and results:
            result = results[0]
            source_ordinals = {s["passageOrdinal"] for s in sources}
            source_mechanisms = {s["mechanismId"] for s in sources}
            if len(source_ordinals) != 1:
                err(f"{label} decision 'merge' cites proposals on different passages {sorted(source_ordinals)}")
            elif result.get("passageOrdinal") not in source_ordinals:
                err(
                    f"{label} decision 'merge' produces gold on passage "
                    f"{result.get('passageOrdinal')!r} but its sources are on {sorted(source_ordinals)}"
                )
            if len(source_mechanisms) != 1:
                err(
                    f"{label} decision 'merge' cites proposals of different mechanisms "
                    f"{sorted(source_mechanisms)}; reconciling different mechanisms is a "
                    "'split' or an 'uphold', not a merge"
                )
            elif result.get("mechanismId") not in source_mechanisms:
                err(
                    f"{label} decision 'merge' produces mechanism {result.get('mechanismId')!r} "
                    f"from sources of mechanism {sorted(source_mechanisms)}"
                )
            result_span = (result.get("startChar"), result.get("endChar"))
            if _is_int(result_span[0]) and _is_int(result_span[1]):
                for source in sources:
                    if source["passageOrdinal"] != result.get("passageOrdinal"):
                        continue
                    if not _spans_overlap(result_span, (source["startChar"], source["endChar"])):
                        err(
                            f"{label} decision 'merge' produces a gold span {result_span} that does "
                            f"not overlap cited proposal {source.get('proposalId')!r} "
                            f"({source['startChar']}, {source['endChar']}); a merge reconciles the "
                            "cited spans, it does not relocate the finding"
                        )

        if decision == "split" and sources and results:
            source_ordinals = {s["passageOrdinal"] for s in sources}
            source_region = (
                min(s["startChar"] for s in sources), max(s["endChar"] for s in sources),
            )
            for result in results:
                if result.get("passageOrdinal") not in source_ordinals:
                    err(
                        f"{label} decision 'split' produces gold "
                        f"{result.get('annotationId')!r} on passage {result.get('passageOrdinal')!r}, "
                        f"outside its source passage(s) {sorted(source_ordinals)}"
                    )
                    continue
                span = (result.get("startChar"), result.get("endChar"))
                if _is_int(span[0]) and _is_int(span[1]) and not _spans_overlap(span, source_region):
                    err(
                        f"{label} decision 'split' produces gold "
                        f"{result.get('annotationId')!r} at {span}, outside the source region "
                        f"{source_region}; a split divides the cited region, it does not create "
                        "unrelated findings elsewhere"
                    )

    # ---- D-03: EXACTLY ONE provenance per gold annotation ----
    #
    # Both origins are computed for every annotation and the pair is checked
    # against a closed truth table. Previously an annotation with one
    # resolution link was accepted without ever asking whether it ALSO had a
    # clear two-annotator auto-merge origin — so a document could, for
    # instance, claim `adjudicator_add` ("no annotator proposed this") over
    # gold that both annotators had in fact proposed identically, which
    # misrepresents where the finding came from.
    #
    #   auto_merge | resolutions | verdict
    #   -----------+-------------+--------------------------------
    #   True       | 0           | VALID (uncontested auto-merge)
    #   False      | 1           | VALID (adjudicated)
    #   False      | 0           | ungrounded
    #   True       | >= 1        | conflicting provenance
    #   False      | > 1         | duplicate provenance
    for ann_id, ann in annotation_records.items():
        links = grounded_by_resolution.get(ann_id, 0)
        merged = _auto_merge_span(ann, proposal_records, declared_annotators)
        auto_merge_origin = (
            merged is not None and (ann.get("startChar"), ann.get("endChar")) == merged
        )

        if auto_merge_origin and links == 0:
            continue
        if not auto_merge_origin and links == 1:
            continue

        if auto_merge_origin and links >= 1:
            err(
                f"annotations[].annotationId {ann_id!r} has CONFLICTING provenance: it is already a "
                f"unanimous auto-merge of the declared annotators AND is claimed by {links} "
                "resolution(s). Exactly one origin must be recorded, so the file cannot say two "
                "different things about where the finding came from"
            )
        elif links > 1:
            err(
                f"annotations[].annotationId {ann_id!r} is claimed by {links} resolutions; each "
                "gold annotation must have exactly one provenance record"
            )
        elif merged is not None:
            err(
                f"annotations[].annotationId {ann_id!r} claims an auto-merge but its span "
                f"({ann.get('startChar')}, {ann.get('endChar')}) is not the protocol-defined "
                f"intersection of the agreeing proposals {merged}; adjudicate instead"
            )
        else:
            err(
                f"annotations[].annotationId {ann_id!r} has no machine-readable provenance: it is "
                "not a unanimous auto-merge of every declared annotator (same mechanism, passage, "
                f"pressure and voice, pairwise span IoU >= {AUTO_MERGE_MIN_IOU}), and no resolution "
                "names it — every final gold outcome must be traceable"
            )

    return report


def validate_corpus(corpus_dir: Path, *, expected_taxonomy: str | None = None) -> list[DocumentReport]:
    expected = expected_taxonomy or vocab.taxonomy_version()
    reports: list[DocumentReport] = []
    for path in sorted(corpus_dir.glob("*.json")):
        if path.name.startswith("_"):
            continue
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            report = DocumentReport(path=path.name)
            report.errors.append(f"invalid JSON: {exc}")
            reports.append(report)
            continue
        reports.append(validate_document(data, path=path.name, expected_taxonomy=expected))
    return reports


class CorpusIntegrityError(RuntimeError):
    """At least one adjudicated document is invalid. Fatal — never skipped."""


def assert_corpus_valid(corpus_dir: Path, *, expected_taxonomy: str | None = None) -> list[DocumentReport]:
    reports = validate_corpus(corpus_dir, expected_taxonomy=expected_taxonomy)
    broken = [r for r in reports if r.scored and not r.valid]
    if broken:
        detail = "\n".join(f"  {r.path}: {e}" for r in broken for e in r.errors)
        raise CorpusIntegrityError(
            f"{len(broken)} adjudicated document(s) failed corpus validation:\n{detail}"
        )
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", default=str(ROOT / "benchmarks" / "corpus"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    corpus_dir = Path(args.corpus)
    if not corpus_dir.exists():
        print(f"corpus directory not found: {corpus_dir}", file=sys.stderr)
        return 1

    reports = validate_corpus(corpus_dir)
    scored = [r for r in reports if r.scored]
    broken = [r for r in scored if not r.valid]

    payload = {
        "corpusDirectory": str(corpus_dir),
        "taxonomyVersion": vocab.taxonomy_version(),
        "documentsSeen": len(reports),
        "adjudicatedDocuments": len(scored),
        "invalidAdjudicatedDocuments": len(broken),
        "reports": [r.to_dict() for r in reports],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Corpus: {corpus_dir}")
        print(f"  taxonomy version   : {payload['taxonomyVersion']}")
        print(f"  documents seen     : {payload['documentsSeen']}")
        print(f"  adjudicated (scored): {payload['adjudicatedDocuments']}")
        print(f"  invalid adjudicated : {payload['invalidAdjudicatedDocuments']}")
        for report in broken:
            print(f"  ! {report.path}")
            for error in report.errors:
                print(f"      - {error}")
        if not scored:
            print("  status: EMPTY — no adjudicated documents. Nothing to score, nothing broken.")
    return 1 if broken else 0


if __name__ == "__main__":
    raise SystemExit(main())
