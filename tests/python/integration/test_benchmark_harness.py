"""Integration tests: the benchmark harness itself.

These prove the METRICS MATH is correct. They do not measure detector quality
and they do not add any adjudicated document to the real corpus — every fixture
here is built in a temporary directory and discarded.

The repository's benchmark status remains EMPTY. That is asserted below as a
guard: if someone ever drops a document into benchmarks/corpus/, this test
fails loudly rather than letting an unreviewed corpus silently start producing
numbers that documentation might then quote.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from benchmarks.scripts.evaluate import evaluate, load_corpus  # noqa: E402


def document(annotations, *, status="adjudicated", article_id="bench-t1"):
    return {
        "articleId": article_id,
        "genre": "straight_news",
        "taxonomyVersion": "1.0.0-alpha0",
        "adjudicationStatus": status,
        "passages": [
            {"ordinal": 0, "passageType": "paragraph",
             "text": "The council approved a draconian, reckless scheme on Tuesday."},
        ],
        "annotations": annotations,
    }


def annotation(needle, mechanism, pressure="P3", ordinal=0, **extra):
    text = "The council approved a draconian, reckless scheme on Tuesday."
    start = text.index(needle)
    return {
        "annotationId": f"a-{start}", "passageOrdinal": ordinal,
        "startChar": start, "endChar": start + len(needle), "excerpt": needle,
        "mechanismId": mechanism, "pressure": pressure, "reviewerConfidence": "High",
        **extra,
    }


class HarnessCorrectnessTests(unittest.TestCase):
    def test_perfect_prediction_scores_perfect_recall_and_precision(self):
        gold = [annotation("draconian, reckless scheme", "loaded_language")]
        results = evaluate([document(gold)])
        loaded = results["perMechanism"]["loaded_language"]
        self.assertEqual(loaded["truePositives"], 1)
        self.assertEqual(loaded["falseNegatives"], 0)
        self.assertEqual(loaded["recall"], 1.0)
        self.assertEqual(loaded["exactSpanAccuracy"], 1.0)

    def test_missed_gold_annotation_counts_as_a_false_negative(self):
        # A mechanism the detector does not implement a signal for here.
        gold = [annotation("on Tuesday", "false_dilemma", pressure="P2")]
        results = evaluate([document(gold)])
        self.assertEqual(results["perMechanism"]["false_dilemma"]["falseNegatives"], 1)
        self.assertEqual(results["perMechanism"]["false_dilemma"]["recall"], 0.0)

    def test_unannotated_detection_counts_as_a_false_positive(self):
        results = evaluate([document([])])
        loaded = results["perMechanism"]["loaded_language"]
        self.assertGreater(loaded["falsePositives"], 0)
        self.assertEqual(loaded["precision"], 0.0)

    def test_f2_weights_recall_above_precision(self):
        """False negatives are the costlier error class for this instrument."""
        gold = [annotation("draconian, reckless scheme", "loaded_language")]
        results = evaluate([document(gold)])
        loaded = results["perMechanism"]["loaded_language"]
        if loaded["precision"] is not None and loaded["recall"] is not None:
            if loaded["recall"] > loaded["precision"]:
                self.assertGreater(loaded["f2RecallWeighted"], loaded["f1"])

    def test_pressure_disagreement_is_measured_separately_from_detection(self):
        gold = [annotation("draconian, reckless scheme", "loaded_language", pressure="P1")]
        results = evaluate([document(gold)])
        loaded = results["perMechanism"]["loaded_language"]
        self.assertEqual(loaded["truePositives"], 1, "detection should still succeed")
        self.assertEqual(loaded["pressureAgreement"], 0.0, "pressure should disagree")

    def test_no_aggregate_hides_a_failing_mechanism(self):
        results = evaluate([document([annotation("draconian, reckless scheme", "loaded_language")])])
        self.assertIn("perMechanism", results)
        for key in ("overallScore", "aggregateF1", "headline", "score"):
            self.assertNotIn(key, results)

    def test_only_adjudicated_documents_are_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp)
            (path / "draft.json").write_text(json.dumps(document([], status="annotated")))
            (path / "disputed.json").write_text(json.dumps(document([], status="disputed")))
            (path / "good.json").write_text(json.dumps(document([], status="adjudicated")))
            (path / "_example.json").write_text(json.dumps(document([], status="adjudicated")))
            loaded = load_corpus(path)
        self.assertEqual(len(loaded), 1, "only adjudicated, non-underscore documents count")

    def test_underscore_prefixed_files_never_contribute(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp)
            (path / "_schema.json").write_text(json.dumps(document([], status="adjudicated")))
            self.assertEqual(load_corpus(path), [])


class RepositoryBenchmarkStatusTests(unittest.TestCase):
    def test_repository_corpus_is_empty_and_status_is_reported_as_such(self):
        """Guard: no number may appear until humans have annotated something."""
        documents = load_corpus(ROOT / "benchmarks" / "corpus")
        self.assertEqual(
            documents, [],
            "benchmarks/corpus contains adjudicated documents; detector calibration "
            "claims in documentation must be re-checked before this test is updated",
        )

    def test_cli_reports_empty_without_inventing_metrics(self):
        proc = subprocess.run(
            [sys.executable, "benchmarks/scripts/evaluate.py", "--json"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["benchmarkStatus"], "EMPTY")
        self.assertIsNone(payload["metrics"])
        self.assertIn("PENDING", payload["message"])

    def test_worked_example_excerpts_round_trip(self):
        example = json.loads((ROOT / "benchmarks" / "corpus" / "_example.json").read_text())
        passages = {p["ordinal"]: p["text"] for p in example["passages"]}
        for item in example["annotations"]:
            text = passages[item["passageOrdinal"]]
            self.assertEqual(
                text[item["startChar"]:item["endChar"]], item["excerpt"], item["annotationId"]
            )

    def test_worked_example_uses_one_mechanism_per_annotation(self):
        example = json.loads((ROOT / "benchmarks" / "corpus" / "_example.json").read_text())
        for item in example["annotations"]:
            self.assertIsInstance(item["mechanismId"], str)
            self.assertNotIn("mechanisms", item)


if __name__ == "__main__":
    unittest.main()
