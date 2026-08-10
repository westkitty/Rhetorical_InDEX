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
DECISIONS_PRODUCING_GOLD = {"uphold_a", "uphold_b", "merge", "split", "adjudicator_add"}


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
    annotators = data.get("annotatorIds")
    if not isinstance(annotators, list) or len({a for a in annotators if isinstance(a, str)}) < MIN_ANNOTATORS:
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
    # B-04: fingerprints of well-typed proposals, used below to recognize an
    # uncontested auto-merge (a gold annotation that exactly restates some
    # original proposal) without requiring a resolution record for it.
    proposal_fingerprints: set[tuple[str, int, int, int]] = set()
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
            if isinstance(fp_mechanism, str) and _is_int(fp_ordinal) and _is_int(fp_start) and _is_int(fp_end):
                proposal_fingerprints.add((fp_mechanism, fp_ordinal, fp_start, fp_end))

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

    # B-04: EVERY FINAL GOLD OUTCOME MUST HAVE MACHINE-READABLE PROVENANCE.
    #
    # Policy (recorded in ADJUDICATION.md §7): a third-party adjudicator MAY
    # add a positive finding that neither original annotator proposed, but
    # only via an explicit `adjudicator_add` resolution — never silently.
    # A gold annotation is grounded when EITHER:
    #   (a) it exactly restates some preserved proposal (mechanism, passage,
    #       span) — the uncontested auto-merge case from ADJUDICATION.md §2,
    #       which by design needs no resolution record; or
    #   (b) a resolution record's `resultingAnnotationId` names it.
    # Anything else is ungrounded gold and is rejected.
    resolution_ids: set[str] = set()
    grounded_annotation_ids: set[str] = set()

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

        proposal_id_refs = record.get("proposalIds", [])
        if not isinstance(proposal_id_refs, list):
            err(f"{label}.proposalIds must be an array")
            proposal_id_refs = []
        else:
            for pid in proposal_id_refs:
                if pid not in proposal_ids:
                    err(f"{label} references unknown proposalId {pid!r}")

        resulting_id = record.get("resultingAnnotationId")
        if decision == "drop":
            if resulting_id is not None:
                err(f"{label} decision 'drop' must not carry a resultingAnnotationId — nothing survives a drop")
        elif decision in DECISIONS_PRODUCING_GOLD:
            if not isinstance(resulting_id, str) or not resulting_id.strip():
                err(f"{label} decision {decision!r} requires a non-empty resultingAnnotationId")
            elif resulting_id not in annotation_records:
                err(
                    f"{label}.resultingAnnotationId {resulting_id!r} does not reference an "
                    "existing gold annotation"
                )
            else:
                grounded_annotation_ids.add(resulting_id)

        if decision == "adjudicator_add":
            if proposal_id_refs:
                err(
                    f"{label} decision 'adjudicator_add' must have an empty proposalIds — it "
                    "explicitly has no proposal origin, and claiming one would misrepresent it"
                )
            note = record.get("note") or record.get("rationale")
            if not isinstance(note, str) or not note.strip():
                err(f"{label} decision 'adjudicator_add' requires a non-empty note or rationale")

    for ann_id, ann in annotation_records.items():
        if ann_id in grounded_annotation_ids:
            continue
        fingerprint = (ann.get("mechanismId"), ann.get("passageOrdinal"), ann.get("startChar"), ann.get("endChar"))
        if fingerprint in proposal_fingerprints:
            continue
        err(
            f"annotations[].annotationId {ann_id!r} has no machine-readable provenance: it does "
            "not exactly restate any preserved proposal, and no resolution's resultingAnnotationId "
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
