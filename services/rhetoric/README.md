# Level 3 — Instrument Alpha rhetoric detector

**Status: structurally complete, UNCALIBRATED.**

No benchmark has been run against this pipeline. There is no precision, recall,
F1 or span-accuracy figure for it anywhere in this repository, and none is
estimated. Output is candidate rhetorical analysis for human review.

Network-free. No provider transport is wired; see "Providers" below.

## Stage map

| # | Stage | Module |
|---|---|---|
| 1 | input normalization | `document.normalize_text` |
| 2 | passage segmentation | `document.segment` |
| 3 | candidate generation | `candidates.generate` |
| 4 | context assembly | `context.assemble` |
| 5 | mechanism classification | `providers.DetectorProvider.verify` |
| 6 | exact span localization | `validation.resolve_span` |
| 7 | pressure classification | `scoring.score_pressure` |
| 8 | confidence classification | `scoring.score_confidence` |
| 9 | voice provenance | `voice.classify` |
| 10 | structured validation | `validation.validate_finding_payload` |
| 11 | span reconciliation | `models.dedupe_findings` |
| 12 | finding creation | `models.Finding` |
| 13 | coverage accounting | `models.AnalysisRun` |
| 14 | run finalization | `AnalysisRun.finalize` |

## Implemented mechanisms

Four of twelve, deliberately: **loaded_language, presupposition,
agent_suppression, false_dilemma**. Correct four-mechanism analysis is worth
more than fictional twelve-mechanism coverage. Requesting any other mechanism
raises rather than silently returning nothing.

Cross-document mechanisms (`material_omission`, `selective_quotation`,
`headline_body_mismatch`) are structurally barred: `Finding.__post_init__`
refuses to construct them, and validation rejects them.

## Running it

```bash
python3 -m services.api.analyze --file article.txt
python3 -m services.api.analyze --text "..." --json
```

## Providers

| Provider | State |
|---|---|
| `MockDetectorProvider` | Deterministic test double |
| `HeuristicDetectorProvider` | Rule-based, unbenchmarked. Default. |
| `ModelDetectorProvider` | Prompt construction + strict response parsing implemented and tested; **transport not wired**. Raises `ProviderUnavailable` without credentials. |

A missing credential produces a `DetectorFailure` and a failed/partial run. It
never produces an invented verdict.

Provider output is untrusted: everything passes through `validation` before it
can influence a Finding. Swapping providers cannot widen what the system
accepts — `test_swapping_providers_does_not_widen_what_is_accepted` proves it.

## The rule that matters most

**Reject, never repair.** If a provider returns a verdict with missing or
malformed `criteriaTriggered`, validation raises. It does not substitute the
mechanism's taxonomy criteria to make the record well-formed — that would
manufacture detector evidence and show a user a criterion no detector asserted.

`test_provider_cannot_get_criteria_backfilled_from_the_taxonomy` and
`test_missing_criteria_is_rejected_and_not_backfilled` guard this. Both were
verified to fail when the guard is removed.

## Pressure vs confidence

Two models, two inputs, two questions:

- **pressure** — how strongly does this mechanism constrain interpretation here?
  Ordinal P1–P4, governed by the mechanism's own taxonomy rubric.
- **confidence** — how sure is the detector the mechanism is present at all?

`score_confidence` has no `pressure` parameter, so confidence cannot inherit
pressure. Tests assert both corners are reachable (P4+Low, P1+High).

## Coverage honesty

`AnalysisRun` is created before analysis and owns coverage truth. Every passage
lands in exactly one of processed / failed / unprocessed, asserted by
`assert_coverage_invariant`. Duplicate appends cannot inflate `coverage_ratio`.
A partial run can never report `isCompleteCoverage: true`.

An unexpected provider exception degrades the run to partial/failed with a
recorded `DetectorFailure` — it neither crashes the analysis nor is swallowed.

## Determinism

Same input + same detector build → same `content_hash`, same `run_id`, same
finding ids. No clock or RNG participates in identity. Timestamps are injected
by the caller.

## What this package does NOT do

URL ingestion · network access · live coverage retrieval · evidence
authentication · fact checking · cross-document comparison · material omission ·
benchmark scoring. Comparison and omission live in `services/comparison` and
require an explicit `ComparisonSet`.
