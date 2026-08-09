# 2026-08-09 — Verified Hybrid Migration Build

## Repository state

- Canonical repository: `westkitty/Rhetorical_InDEX`
- Observed baseline commit: `a685c4d98c0be35f8ba2019be6bd2a3b6f5d9ee5`
- Root prototype authority: preserved; not included for replacement in this overlay
- Repository network capability in build container: GitHub connector available; shell DNS unavailable
- Commit/push action: not performed by the build environment; release includes a user-run commit script

## Frozen scope

1. shared contracts, taxonomy, and synthetic fixtures;
2. new Instrument Alpha web scanner with prototype-parity behavior and Compare/Event concepts;
3. deterministic/runtime QA, operational state, and safe additive release packaging.

URL ingestion, the experimental Express/Gemini server, live comparison, and benchmark claims were explicitly excluded.

## Donor adjudication

- GitHub implementation plan governs product and target architecture.
- Root standalone HTML governs verified scanner behavior.
- Experimental application contributes reviewed schema/taxonomy/fixture and interaction ideas only.
- Experimental URL/server implementation and self-authored QA reports are not continuation sources.

## Build defects found and repaired

1. Finding selection rebuilt the opener and broke focus restoration → selection rendering made non-destructive.
2. Wrapped tablet header invalidated fixed sticky offset → actual header height observed with `ResizeObserver`.
3. `pointercancel` cleared state without immediately updating Lens visuals → Lens state re-render added.

## Validation

- TypeScript typecheck: PASS
- Standalone build: PASS
- Node tests: 11/11 PASS
- Python tests: 5/5 PASS
- Chromium runtime checks: 59/59 PASS
- Web Authorship audit: PASS (one non-blocking radius repetition style signal)
- External requests in tested artifact: 0
- Console errors in tested paths: 0

## Remaining uncertainty

- Safari/iPadOS not executed.
- Firefox not executed.
- Real screen reader not executed.
- Production detector and benchmark intentionally pending.

## Next substantive milestone

Replace or augment the current heuristic Level 2 Local Preview detector (`apps/web/src/app.ts`, present since this session's build) with the first calibrated Level 3 four-mechanism Instrument Alpha detector behind `services/api/detector_contract.py`, then construct the first human-reviewed benchmark around the functioning detector. Do not promote URL ingestion before that gate.

## Independent review closure (F-001 – F-004)

A later independent repository review of this session's commit (`dd6a7a5`) found that this record's original "Next substantive milestone" wording described the four-mechanism heuristic detector as future work, when the Level 2 Local Preview detector already existed. A follow-up cleanup pass: (1) formalized the three detector levels across the hybrid documentation set, (2) added `packages/schema/src/localPreviewContract.ts` so Local Preview candidates are validated against the same invariants as `services/api/detector_contract.py` before entering application state, with `tests/local-preview-contract.test.mjs` as regression proof, (3) added `packages/schema/schema.json` as a canonical cross-language vocabulary source with automated TypeScript/Python parity tests, (4) clarified `tests/source-contract.test.mjs` test names as structural/source-presence guards rather than behavioral proof, and (5) fixed a typo in `packages/taxonomy/taxonomy.json`. See `HYBRID_REQUIREMENT_TRACEABILITY.md` and `HYBRID_QA_REPORT.md` for evidence.
