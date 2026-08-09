# Rhetorical InDEX — Instrument Alpha Foundation

This directory set is designed to be overlaid onto the current `westkitty/Rhetorical_InDEX` repository without replacing the verified standalone Experience Prototype.

## What this adds

- `apps/web/`: a dependency-light TypeScript component application with a working article-first scanner, spatial Rhetorical Lens, exact-span multi-tag rendering, finding drawer, Compare framing switcher, Event Record, taxonomy explorer, and methodology view.
- `packages/schema/`: the reviewed shared TypeScript contracts, the canonical cross-language vocabulary (`schema.json`), and the Local Preview validation boundary (`src/localPreviewContract.ts`).
- `packages/taxonomy/`: the twelve-mechanism Alpha-0 taxonomy transplanted from the experimental application and kept as versioned data.
- `packages/fixtures/`: a synthetic multi-source event fixture with `example.invalid` provenance.
- `services/api/`: a network-free Python detector validation boundary for the future calibrated four-mechanism intrinsic detector.
- `tests/`: deterministic contract/fixture/artifact/vocabulary-parity tests plus prototype-parity documentation.
- `tools/`: a standalone build and Chromium runtime QA harness.

## Three detector levels

This foundation is deliberately explicit about which detector is which:

1. **Level 1 — Experience Prototype detector.** Deterministic/synthetic demonstration belonging to the trusted root `Rhetorical_InDEX.html`. Not a calibrated analytical instrument.
2. **Level 2 — Local Preview detector.** Runs on real pasted text in the browser today (`apps/web/src/app.ts`). Heuristic, unbenchmarked, bounded to the same four-mechanism slice (Loaded language, Presupposition, Agent suppression, False dilemma), explicitly non-authoritative, intended for interaction and contract validation rather than production analysis. Its output is validated against `packages/schema/src/localPreviewContract.ts` before entering application state, and `tests/local-preview-contract.test.mjs` proves that output also satisfies `services/api/detector_contract.py`'s invariants.
3. **Level 3 — Instrument Alpha detector.** The future calibrated detector, governed by the canonical taxonomy and the strict `services/api/detector_contract.py` boundary, to be benchmarked against a human-reviewed corpus. **Not yet implemented.**

## What this intentionally does not add

- URL ingestion.
- A remote model dependency.
- Live comparison or live omission detection.
- A claim of benchmarked detector accuracy.
- A replacement for the existing root `Rhetorical_InDEX.html` Experience Prototype.
- A calibrated Level 3 Instrument Alpha detector (see above — that is future work, not this release).

Pasted text runs the clearly labeled **Local Preview — Unbenchmarked** Level 2 detector described above. It emits candidates only. The synthetic fixture remains the only path with Compare, omission, and Event Record material.

## Open the new web artifact

Open:

`apps/web/dist/index.html`

It is self-contained and has no runtime network dependency.

## Rebuild and test

If TypeScript is not already installed locally:

```bash
npm install
```

Then:

```bash
npm run typecheck
npm run build
npm test
```

The optional Chromium QA harness is:

```bash
npm run qa:runtime
```

It requires Python Playwright and a Chromium executable.

## Governing relationship

The existing GitHub implementation plan remains the product and architecture authority. The existing root standalone HTML remains the golden Experience Prototype until a future Instrument Alpha release explicitly passes replacement gates.
