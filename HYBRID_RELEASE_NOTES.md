# Rhetorical InDEX — Hybrid Instrument Alpha Foundation

## Purpose

This release creates the additive bridge from the verified standalone Experience Prototype to Instrument Alpha.

It does not replace the root prototype. It establishes a componentized, testable structure whose scanner behavior is checked against the trusted prototype and whose domain contracts selectively incorporate useful work from the experimental application.

## Added

- dependency-light TypeScript web application under `apps/web`;
- self-contained built web artifact at `apps/web/dist/index.html`;
- shared schema package with one-Finding/one-mechanism contract;
- twelve-mechanism Alpha-0 taxonomy data;
- synthetic multi-source fixture with reserved `example.invalid` provenance;
- Framing Switcher-style Compare experience;
- forensic Event Record fixture view;
- strict Python candidate-validation boundary for the first four intrinsic mechanisms;
- deterministic Node/Python tests;
- Chromium prototype-parity QA and screenshots;
- subsystem operational state and migration decision records.

## Intentionally deferred

- production detector inference;
- human-reviewed benchmark;
- URL ingestion;
- live event discovery/peer comparison;
- live Material Omission detection;
- primary-evidence retrieval;
- production database/job infrastructure.

## Validation snapshot

- TypeScript typecheck: PASS
- Build: PASS
- Node: 11/11 PASS
- Python: 5/5 PASS
- Chromium runtime: 59/59 PASS
- Web authorship audit: PASS

See `HYBRID_QA_REPORT.md` and `apps/web/OPERATIONAL_STATE.md` for evidence and limitations.
