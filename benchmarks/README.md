# Rhetorical InDEX — Benchmark

## Status: EMPTY — no human annotation has been performed

```
$ python3 benchmarks/scripts/evaluate.py
The benchmark corpus contains no adjudicated human annotations.
No detector performance metrics exist and none are estimated.
Detector calibration status: PENDING.
```

This directory contains the **machinery** to measure the Level 3 Instrument
Alpha detector. It contains **no results**, because measuring a detector
requires human annotators and none have annotated anything yet.

Nothing in this repository states a precision, recall, F1, span-accuracy or
calibration figure for the detector. If you find such a number anywhere, it is a
bug — report it, because it was not produced by this harness.

## What exists

| Component | Path | State |
|---|---|---|
| Corpus schema | `benchmarks/corpus/_schema.json` | Complete |
| Worked example (excluded from scoring) | `benchmarks/corpus/_example.json` | Complete |
| Annotation guide | `benchmarks/ANNOTATION_GUIDE.md` | Complete |
| Adjudication protocol | `benchmarks/ADJUDICATION.md` | Complete |
| Evaluation harness | `benchmarks/scripts/evaluate.py` | Complete, self-tested |
| Adjudicated corpus | `benchmarks/corpus/*.json` | **Empty (0 documents)** |

Files beginning with `_` are schema/example material and are deliberately
skipped by the loader so they can never contribute to a score.

## Metrics the harness computes

Per mechanism, never averaged into a headline number:

- precision, recall, F1
- **F2 (recall-weighted)** — false negatives are the costlier error class for
  this instrument; silently missing rhetoric is worse than flagging a
  borderline case a reader can dismiss
- exact-span accuracy and mean span IoU
- pressure agreement
- voice-provenance accuracy
- confusion against overlapping gold mechanisms

A predicted span counts as matched at IoU ≥ 0.5; exact-span accuracy is tracked
separately and is the stricter figure.

## Pilot corpus targets (from the implementation plan §44)

Starting targets, not sacred numbers:

- 40–60 articles across straight news, analysis, opinion and press-release-like material
- ≥ 400 candidate/negative passages
- ≥ 30 reviewed positive examples per implemented mechanism where prevalence allows
- deliberate near-miss negatives and confusion-neighbour cases
- multi-label spans and quoted-speaker cases

## Running it

```bash
python3 benchmarks/scripts/evaluate.py --json
```

Exit codes: `0` = ran (possibly EMPTY), `2` = corpus directory missing.

## What would change the calibration status

Only this: adjudicated human annotations landing in `benchmarks/corpus/` and
this harness producing measured numbers. Until then every document in this
repository must describe the Level 3 detector as **uncalibrated**.
