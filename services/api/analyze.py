"""Local, network-free analysis boundary for the Level 3 detector.

This is the orchestrator seam the future HTTP service will sit behind. It is
deliberately NOT an HTTP server: URL ingestion and network exposure are still
deferred, and adding a listener now would reintroduce exactly the surface the
hybrid migration rejected.

What it provides today:
  * one stable entry point (`analyze_document`) returning a fully serializable
    envelope with run, article, findings, profile and transparency block;
  * a CLI (`python3 -m services.api.analyze --file article.txt`) so the detector
    is actually runnable and inspectable without a browser;
  * an explicit transparency block so no consumer can render results without
    also being handed the calibration status.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.rhetoric import vocabulary as vocab  # noqa: E402
from services.rhetoric.pipeline import (  # noqa: E402
    DETECTOR_VERSION,
    IMPLEMENTED_MECHANISMS,
    analyze_text,
    pressure_profile,
)
from services.rhetoric.providers import (  # noqa: E402
    DetectorProvider,
    HeuristicDetectorProvider,
    ModelDetectorProvider,
)

# Calibration status is a constant, not a computed value, precisely so it cannot
# drift optimistically. It changes only when benchmarks/corpus/ contains
# adjudicated human annotations and benchmarks/scripts/evaluate.py reports them.
CALIBRATION_STATUS = "uncalibrated"
CALIBRATION_NOTE = (
    "This detector has not been benchmarked. No precision, recall or accuracy "
    "figure exists for it. Output is candidate rhetorical analysis for human "
    "review, not a validated measurement."
)


def build_provider(kind: str = "heuristic") -> DetectorProvider:
    if kind == "heuristic":
        return HeuristicDetectorProvider()
    if kind == "model":
        # Returns the provider regardless of credentials. If they are absent it
        # will raise ProviderUnavailable per passage and the run becomes failed —
        # visibly, rather than silently degrading to heuristics.
        return ModelDetectorProvider()
    raise ValueError(f"unknown provider kind: {kind!r}")


def transparency_block(provider: DetectorProvider) -> dict[str, Any]:
    """Everything a consumer needs to avoid overstating what it is showing."""
    return {
        "detectorLevel": 3,
        "detectorLevelName": "Instrument Alpha",
        "detectorVersion": DETECTOR_VERSION,
        "taxonomyVersion": vocab.taxonomy_version(),
        "schemaVersion": vocab.SCHEMA_VERSION,
        "provider": provider.describe(),
        "implementedMechanisms": sorted(IMPLEMENTED_MECHANISMS),
        "totalTaxonomyMechanisms": len(vocab.mechanism_ids()),
        "calibrationStatus": CALIBRATION_STATUS,
        "calibrationNote": CALIBRATION_NOTE,
        "benchmarkStatus": "EMPTY",
        "capabilities": {
            "intrinsicRhetoricAnalysis": True,
            "crossDocumentComparison": False,
            "materialOmissionDetection": False,
            "evidenceRetrieval": False,
            "factChecking": False,
            "urlIngestion": False,
            "networkAccess": False,
        },
        "limitations": [
            "Interpretive pressure is not factuality: a true statement can carry high pressure.",
            "Confidence is detector certainty, not confidence that a claim is true.",
            "Only four of twelve taxonomy mechanisms are implemented at this level.",
            "Material omission, comparison and evidence require a comparison set and are not available here.",
            "No benchmark has been run; treat all output as unvalidated candidates.",
        ],
    }


def analyze_document(
    text: str,
    *,
    provider_kind: str = "heuristic",
    batch_size: int = 25,
    started_at: str | None = None,
    completed_at: str | None = None,
    **article_metadata: Any,
) -> dict[str, Any]:
    """Analyze one document. Returns a fully serializable envelope."""
    provider = build_provider(provider_kind)
    result = analyze_text(
        text,
        provider=provider,
        batch_size=batch_size,
        started_at=started_at,
        completed_at=completed_at,
        **article_metadata,
    )
    return {
        "transparency": transparency_block(provider),
        "run": result.run.to_dict(),
        "article": result.article.to_dict(),
        "findings": [f.to_dict() for f in result.findings],
        "profile": pressure_profile(result.findings),
        "comparison": {
            "available": False,
            "reason": (
                "Comparison, Event Record and Material Omission require a validated "
                "same-event comparison set. A single-document scan cannot invent one."
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="path to a UTF-8 text file")
    source.add_argument("--text", help="inline article text")
    source.add_argument("--stdin", action="store_true", help="read article text from stdin")
    parser.add_argument("--provider", default="heuristic", choices=["heuristic", "model"])
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--json", action="store_true", help="emit the full JSON envelope")
    args = parser.parse_args(argv)

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("error: no article text supplied", file=sys.stderr)
        return 2

    envelope = analyze_document(text, provider_kind=args.provider, batch_size=args.batch_size)

    if args.json:
        print(json.dumps(envelope, indent=2))
        return 0

    run = envelope["run"]
    transparency = envelope["transparency"]
    print(f"Rhetorical InDEX — Level 3 {transparency['detectorLevelName']} "
          f"({transparency['detectorVersion']})")
    print(f"Calibration: {transparency['calibrationStatus'].upper()} — benchmark {transparency['benchmarkStatus']}")
    print(f"Taxonomy: {transparency['taxonomyVersion']}  |  "
          f"mechanisms implemented: {len(transparency['implementedMechanisms'])}"
          f"/{transparency['totalTaxonomyMechanisms']}")
    print(f"\nRun {run['runId']}  status={run['status']}  "
          f"coverage={run['coverageRatio'] * 100:.1f}% "
          f"({len(run['processedPassageIds'])}/{len(run['allPassageIds'])} passages)")
    for warning in run["warnings"]:
        print(f"  ! {warning}")

    print(f"\n{len(envelope['findings'])} finding(s):\n")
    for finding in envelope["findings"]:
        print(f"  [{finding['pressure']}] {finding['mechanismId']}  "
              f"confidence={finding['confidence']}  voice={finding['voiceClass']}")
        print(f"      {finding['excerpt']!r}")
        for criterion in finding["triggeredCriteria"]:
            print(f"      · {criterion}")
        if finding["alternateInterpretation"]:
            print(f"      ? {finding['alternateInterpretation']}")
        print()

    profile = envelope["profile"]
    print(f"Pressure distribution: {profile['byPressure']}")
    print(f"Voice distribution:    {profile['byVoice']}")
    print(f"\n{transparency['calibrationNote']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
