# Rhetorical InDEX — Hybrid Instrument Alpha Foundation

## Purpose

This release creates the additive bridge from the verified standalone Experience Prototype to Instrument Alpha.

It does not replace the root prototype. It establishes a componentized, testable structure whose scanner behavior is checked against the trusted prototype and whose domain contracts selectively incorporate useful work from the experimental application.

## Added

- dependency-light TypeScript web application under `apps/web`;
- self-contained built web artifact at `apps/web/dist/index.html`;
- shared schema package with one-Finding/one-mechanism contract, a canonical cross-language vocabulary (`packages/schema/schema.json`), and a Local Preview validation boundary (`packages/schema/src/localPreviewContract.ts`);
- twelve-mechanism Alpha-0 taxonomy data;
- synthetic multi-source fixture with reserved `example.invalid` provenance;
- Framing Switcher-style Compare experience;
- forensic Event Record fixture view;
- strict Python candidate-validation boundary for the first four intrinsic mechanisms;
- deterministic Node/Python tests, including automated TypeScript/Python vocabulary-parity tests and a Local Preview contract-validation regression test;
- Chromium prototype-parity QA and screenshots;
- subsystem operational state and migration decision records.

## Detector levels in this release

- **Level 1 — Experience Prototype detector**: deterministic/synthetic, belongs to the root `Rhetorical_InDEX.html`. Unchanged by this release.
- **Level 2 — Local Preview detector**: heuristic, unbenchmarked, runs on real pasted text today, bounded to four intrinsic mechanisms. **Present in this release**, and its output is now validated against the same semantic invariants as `services/api/detector_contract.py` before entering application state.
- **Level 3 — Instrument Alpha detector**: the future calibrated detector governed by `services/api/detector_contract.py` and benchmarked against a human-reviewed corpus. **Not present in this release.**

## Intentionally deferred

- the calibrated Level 3 Instrument Alpha detector;
- human-reviewed benchmark;
- URL ingestion;
- live event discovery/peer comparison;
- live Material Omission detection;
- primary-evidence retrieval;
- production database/job infrastructure.

## Validation snapshot

- TypeScript typecheck: PASS
- Build: PASS
- Node: PASS (see `HYBRID_QA_REPORT.md` for the exact count)
- Python: PASS (see `HYBRID_QA_REPORT.md` for the exact count)
- Chromium runtime: see `HYBRID_QA_REPORT.md` — re-executed only where the review environment allowed it
- Web authorship audit: PASS

See `HYBRID_QA_REPORT.md` and `apps/web/OPERATIONAL_STATE.md` for evidence and limitations.
