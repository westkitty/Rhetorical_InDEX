#!/usr/bin/env python3
"""Benchmark evaluation harness for the Level 3 Instrument Alpha detector.

This computes metrics FROM a human-annotated corpus. It does not contain,
generate, estimate or default any performance number. If the corpus is empty —
which it currently is — this script reports EMPTY and exits without producing
metrics. That is the correct behaviour: there is no benchmark result to report
because no human annotation has been performed.

Usage:
    python3 benchmarks/scripts/evaluate.py [--corpus benchmarks/corpus] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from services.rhetoric import analyze_article, vocabulary as vocab  # noqa: E402
from services.rhetoric.document import article_from_passages  # noqa: E402
from services.rhetoric.pipeline import IMPLEMENTED_MECHANISMS  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_corpus import CorpusIntegrityError, assert_corpus_valid  # noqa: E402

# A predicted span counts as a span-level match when IoU meets this threshold.
SPAN_IOU_THRESHOLD = 0.5


@dataclass
class MechanismMetrics:
    mechanism_id: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    exact_span_matches: int = 0
    pressure_agreements: int = 0
    pressure_comparisons: int = 0
    voice_agreements: int = 0
    voice_comparisons: int = 0
    span_ious: list[float] = field(default_factory=list)

    @property
    def precision(self) -> float | None:
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom else None

    @property
    def recall(self) -> float | None:
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom else None

    @property
    def f1(self) -> float | None:
        p, r = self.precision, self.recall
        if p is None or r is None or (p + r) == 0:
            return None
        return 2 * p * r / (p + r)

    @property
    def f2(self) -> float | None:
        """Recall-weighted. False negatives are the costlier error class here."""
        p, r = self.precision, self.recall
        if p is None or r is None or (4 * p + r) == 0:
            return None
        return 5 * p * r / (4 * p + r)

    @property
    def exact_span_accuracy(self) -> float | None:
        return self.exact_span_matches / self.true_positives if self.true_positives else None

    @property
    def mean_span_iou(self) -> float | None:
        return sum(self.span_ious) / len(self.span_ious) if self.span_ious else None

    @property
    def pressure_agreement(self) -> float | None:
        return self.pressure_agreements / self.pressure_comparisons if self.pressure_comparisons else None

    @property
    def voice_accuracy(self) -> float | None:
        return self.voice_agreements / self.voice_comparisons if self.voice_comparisons else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mechanismId": self.mechanism_id,
            "truePositives": self.true_positives,
            "falsePositives": self.false_positives,
            "falseNegatives": self.false_negatives,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "f2RecallWeighted": self.f2,
            "exactSpanAccuracy": self.exact_span_accuracy,
            "meanSpanIoU": self.mean_span_iou,
            "pressureAgreement": self.pressure_agreement,
            "voiceAccuracy": self.voice_accuracy,
        }


def maximum_matching(pairs: dict[int, list[int]]) -> dict[int, int]:
    """Deterministic maximum-cardinality bipartite matching (Hopcroft-Karp-lite).

    Review finding O-05: greedy first-best matching made TP/FP/FN depend on
    prediction iteration order — one prediction could claim the only gold span a
    second prediction could have matched, turning two true positives into one TP
    plus an FP and an FN. Metrics that move with iteration order are not metrics.

    `pairs` maps prediction index -> eligible gold indices, pre-sorted by
    descending IoU then ascending index so ties resolve deterministically.
    """
    match_gold: dict[int, int] = {}

    def augment(pred: int, seen: set[int]) -> bool:
        for gold in pairs.get(pred, ()):
            if gold in seen:
                continue
            seen.add(gold)
            if gold not in match_gold or augment(match_gold[gold], seen):
                match_gold[gold] = pred
                return True
        return False

    for pred in sorted(pairs):
        augment(pred, set())
    return {pred: gold for gold, pred in match_gold.items()}


def _iou(a_start: int, a_end: int, b_start: int, b_end: int) -> float:
    overlap = max(0, min(a_end, b_end) - max(a_start, b_start))
    union = max(a_end, b_end) - min(a_start, b_start)
    return overlap / union if union else 0.0


def load_corpus(corpus_dir: Path) -> list[dict[str, Any]]:
    """Load adjudicated annotation documents, VALIDATING them first.

    Review finding M-09: `adjudicationStatus == "adjudicated"` used to be
    sufficient, so a malformed gold file would silently produce metrics. Every
    adjudicated document is now validated, and an invalid one raises
    CorpusIntegrityError rather than being quietly skipped — a corpus that is
    broken must look broken, not small.
    """
    assert_corpus_valid(corpus_dir)

    documents: list[dict[str, Any]] = []
    for path in sorted(corpus_dir.glob("*.json")):
        if path.name.startswith("_"):
            continue
        data = json.loads(path.read_text())
        if data.get("adjudicationStatus") != "adjudicated":
            continue
        documents.append(data)
    return documents


def evaluate(documents: Sequence[dict[str, Any]]) -> dict[str, Any]:
    metrics = {m: MechanismMetrics(m) for m in sorted(IMPLEMENTED_MECHANISMS)}
    confusion: dict[str, dict[str, int]] = {}

    for document in documents:
        article = article_from_passages(
            document["articleId"],
            [(p["passageType"], p["text"]) for p in document["passages"]],
        )
        result = analyze_article(article)

        gold = [a for a in document["annotations"] if a["mechanismId"] in metrics]
        predicted = [f for f in result.findings if f.mechanism_id in metrics]

        # Build eligibility, then solve for MAXIMUM cardinality rather than
        # taking greedy first-best (O-05).
        eligible: dict[int, list[int]] = {}
        iou_by_pair: dict[tuple[int, int], float] = {}
        for pred_index, finding in enumerate(predicted):
            passage_ordinal = article.passage(finding.passage_id).ordinal
            options: list[tuple[float, int]] = []
            for gold_index, annotation in enumerate(gold):
                if annotation["mechanismId"] != finding.mechanism_id:
                    continue
                if annotation["passageOrdinal"] != passage_ordinal:
                    continue
                score = _iou(
                    finding.start_char, finding.end_char,
                    annotation["startChar"], annotation["endChar"],
                )
                if score >= SPAN_IOU_THRESHOLD:
                    options.append((score, gold_index))
                    iou_by_pair[(pred_index, gold_index)] = score
            # Descending IoU, then ascending gold index: deterministic tie-break.
            options.sort(key=lambda item: (-item[0], item[1]))
            eligible[pred_index] = [gold_index for _, gold_index in options]

        matching = maximum_matching(eligible)
        matched_gold: set[int] = set(matching.values())

        for pred_index, finding in enumerate(predicted):
            best_index = matching.get(pred_index)
            best_iou = iou_by_pair.get((pred_index, best_index), 0.0) if best_index is not None else 0.0

            bucket = metrics[finding.mechanism_id]
            if best_index is not None:
                annotation = gold[best_index]
                bucket.true_positives += 1
                bucket.span_ious.append(best_iou)
                if (finding.start_char, finding.end_char) == (annotation["startChar"], annotation["endChar"]):
                    bucket.exact_span_matches += 1
                if "pressure" in annotation:
                    bucket.pressure_comparisons += 1
                    if annotation["pressure"] == finding.pressure:
                        bucket.pressure_agreements += 1
                if "voiceClass" in annotation:
                    bucket.voice_comparisons += 1
                    if annotation["voiceClass"] == finding.voice_class:
                        bucket.voice_agreements += 1
            else:
                bucket.false_positives += 1
                # Record what the detector confused this span with, if anything.
                passage_ordinal = article.passage(finding.passage_id).ordinal
                overlapping = [
                    a["mechanismId"] for a in gold
                    if a["passageOrdinal"] == passage_ordinal
                    and _iou(finding.start_char, finding.end_char, a["startChar"], a["endChar"]) > 0
                ]
                key = finding.mechanism_id
                confusion.setdefault(key, {})
                for other in overlapping or ["<none>"]:
                    confusion[key][other] = confusion[key].get(other, 0) + 1

        for index, annotation in enumerate(gold):
            if index not in matched_gold:
                metrics[annotation["mechanismId"]].false_negatives += 1

    return {
        "corpusDocuments": len(documents),
        "taxonomyVersion": vocab.taxonomy_version(),
        "spanIoUThreshold": SPAN_IOU_THRESHOLD,
        "perMechanism": {m: bucket.to_dict() for m, bucket in metrics.items()},
        "confusion": confusion,
        "note": (
            "No aggregate hides a failing mechanism: per-mechanism figures are "
            "reported individually and are not averaged into a headline score."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", default=str(ROOT / "benchmarks" / "corpus"))
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    corpus_dir = Path(args.corpus)
    if not corpus_dir.exists():
        print(f"BENCHMARK STATUS: MISSING — no corpus directory at {corpus_dir}", file=sys.stderr)
        return 2

    try:
        documents = load_corpus(corpus_dir)
    except CorpusIntegrityError as exc:
        print(f"CORPUS INTEGRITY FAILURE\n{exc}", file=sys.stderr)
        return 3
    if not documents:
        payload = {
            "benchmarkStatus": "EMPTY",
            "corpusDocuments": 0,
            "adjudicatedDocuments": 0,
            "metrics": None,
            "message": (
                "The benchmark corpus contains no adjudicated human annotations. "
                "No detector performance metrics exist and none are estimated. "
                "Detector calibration status: PENDING."
            ),
        }
        print(json.dumps(payload, indent=2) if args.json else payload["message"])
        return 0

    results = evaluate(documents)
    results["benchmarkStatus"] = "MEASURED"
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"Benchmark over {results['corpusDocuments']} adjudicated document(s)\n")
        for mechanism_id, bucket in results["perMechanism"].items():
            print(f"  {mechanism_id}")
            for label, key in (
                ("precision", "precision"), ("recall", "recall"),
                ("F1", "f1"), ("F2 (recall-weighted)", "f2RecallWeighted"),
                ("exact span", "exactSpanAccuracy"), ("mean span IoU", "meanSpanIoU"),
                ("pressure agreement", "pressureAgreement"), ("voice accuracy", "voiceAccuracy"),
            ):
                value = bucket[key]
                print(f"    {label:22s} {'n/a' if value is None else f'{value:.3f}'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
