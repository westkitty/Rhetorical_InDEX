# Rhetorical InDEX — Instrument Alpha Foundation

This directory set is designed to be overlaid onto the current `westkitty/Rhetorical_InDEX` repository without replacing the verified standalone Experience Prototype.

## What this adds

- `apps/web/`: a dependency-light TypeScript component application with a working article-first scanner, spatial Rhetorical Lens, exact-span multi-tag rendering, finding drawer, Compare framing switcher, Event Record, taxonomy explorer, and methodology view.
- `packages/schema/`: the reviewed shared TypeScript contracts.
- `packages/taxonomy/`: the twelve-mechanism Alpha-0 taxonomy transplanted from the experimental application and kept as versioned data.
- `packages/fixtures/`: a synthetic multi-source event fixture with `example.invalid` provenance.
- `services/api/`: a network-free Python detector validation boundary for the future four-mechanism intrinsic detector slice.
- `tests/`: deterministic contract/fixture/artifact tests plus prototype-parity documentation.
- `tools/`: a standalone build and Chromium runtime QA harness.

## What this intentionally does not add

- URL ingestion.
- A remote model dependency.
- Live comparison or live omission detection.
- A claim of benchmarked detector accuracy.
- A replacement for the existing root `Rhetorical_InDEX.html` Experience Prototype.

Pasted text runs a clearly labeled **Local Preview — Unbenchmarked** detector limited to four intrinsic mechanisms. It emits candidates only. The synthetic fixture remains the only path with Compare, omission, and Event Record material.

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
