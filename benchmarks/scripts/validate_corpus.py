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

    proposals = data.get("annotatorSubmissions", [])
    if not isinstance(proposals, list):
        err("annotatorSubmissions must be an array")
        proposals = []
    proposal_ids: set[str] = set()
    for index, proposal in enumerate(proposals):
        label = f"annotatorSubmissions[{index}]"
        if not isinstance(proposal, dict):
            err(f"{label} is not an object")
            continue
        for required in ("proposalId", "annotatorId", "mechanismId", "passageOrdinal",
                         "startChar", "endChar", "excerpt", "pressure", "reviewerConfidence", "voiceClass"):
            if required not in proposal:
                err(f"{label} missing required field {required}")
        pid = proposal.get("proposalId")
        if isinstance(pid, str):
            if pid in proposal_ids:
                err(f"duplicate proposalId {pid!r}")
            proposal_ids.add(pid)
        ordinal = proposal.get("passageOrdinal")
        if _is_int(ordinal) and ordinal in texts:
            start, end, excerpt = proposal.get("startChar"), proposal.get("endChar"), proposal.get("excerpt")
            if _is_int(start) and _is_int(end) and isinstance(excerpt, str):
                if not (0 <= start < end <= len(texts[ordinal])) or texts[ordinal][start:end] != excerpt:
                    err(f"{label}.excerpt does not round-trip against its passage")

    # M-12: original independent submissions must be preserved so
    # inter-annotator agreement stays computable after adjudication.
    if proposals:
        submitting = {p.get("annotatorId") for p in proposals if isinstance(p, dict)}
        if len(submitting) < MIN_ANNOTATORS:
            err(
                f"annotatorSubmissions contain proposals from {len(submitting)} annotator(s); "
                f"at least {MIN_ANNOTATORS} independent submissions must be preserved"
            )

    for index, record in enumerate(data.get("resolutions", []) or []):
        label = f"resolutions[{index}]"
        if not isinstance(record, dict):
            err(f"{label} is not an object")
            continue
        decision = record.get("decision")
        if decision not in {"uphold_a", "uphold_b", "merge", "drop", "split", "unresolvable"}:
            err(f"{label}.decision invalid: {decision!r}")
        if decision == "unresolvable":
            err(
                f"{label} is marked 'unresolvable' in an adjudicated document; such documents "
                "must remain 'disputed' and are excluded from scoring"
            )
        for pid in record.get("proposalIds", []) or []:
            if proposal_ids and pid not in proposal_ids:
                err(f"{label} references unknown proposalId {pid!r}")

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
