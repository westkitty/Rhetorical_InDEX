# Rhetorical InDEX — Hybrid Build Requirement Traceability

| ID | Mandatory requirement | Evidence | Status |
|---|---|---|---|
| H-001 | Use the GitHub project as canonical authority rather than replacing it wholesale with the experimental app. | `docs/migration/HYBRID_DECISION.md`; overlay contains no root prototype/plan replacement. | PASS |
| H-002 | Preserve the verified standalone Experience Prototype as the golden behavioral reference. | `tests/prototype-parity/README.md`; `apps/web/OPERATIONAL_STATE.md` INV-001. | PASS |
| H-003 | Build a new additive Instrument Alpha implementation rather than extending the monolithic prototype as production architecture. | `apps/web`, `packages`, `services`, `tests`, `tools`. | PASS |
| H-004 | Reuse the strongest donor domain pieces instead of importing the whole experimental application. | `docs/migration/DONOR_LEDGER.md`. | PASS |
| H-005 | Keep one-Finding/one-mechanism exact-span contract. | `packages/schema/src/contracts.ts`; source-contract tests. | PASS |
| H-006 | Preserve the twelve-mechanism Alpha-0 taxonomy as versioned shared data. | `packages/taxonomy/taxonomy.json`; taxonomy tests. | PASS |
| H-007 | Preserve synthetic Compare/Event fixture value without presenting it as live reporting. | `packages/fixtures/sb802-demo.json`; explicit Synthetic Fixture UI. | PASS |
| H-008 | Use one accessible article plus an `aria-hidden` Lens visualization layer. | Runtime checks: one semantic article, overlay aria-hidden. | PASS |
| H-009 | Lens must spatially reveal exact rhetoric without changing text-flow geometry. | Runtime geometry delta `0.00`; screenshots; spatial Lens readout check. | PASS |
| H-010 | Multiple findings on the same/overlapping text must not duplicate canonical article text. | `tests/artifact.test.mjs`; interval rendering/source-contract checks. | PASS |
| H-011 | Pressure and confidence remain independent. | Contracts + runtime cards/drawer/profile. | PASS |
| H-012 | Tablet portrait Lens path works with radius-aware bounds. | Chromium 768×1024 runtime checks. | PASS |
| H-013 | Tablet landscape Lens path works with wrapped-header clearance. | Chromium 1024×768 runtime checks. | PASS |
| H-014 | Touch pointer ownership and `pointercancel` cleanup work. | Runtime checks across coarse-pointer viewports. | PASS |
| H-015 | Finding drawer traps focus and restores opener focus. | Repeated runtime Tab checks + focus-restoration check. | PASS |
| H-016 | Reduced Motion and non-color Pattern Mode are present. | Runtime state checks + CSS/source. | PASS |
| H-017 | Pasted text is honestly labeled unbenchmarked and cannot invent Compare/Event/Material Omission. | Local Preview runtime journey; Compare unavailable; strict Python contract rejects `material_omission`. | PASS |
| H-018 | Do not import the experimental Express/Gemini server or URL fetcher. | No server dependency or fetch/XHR runtime path in the web artifact; donor ledger marks them rejected. | PASS |
| H-019 | Establish a strict future Python boundary for the four-mechanism detector slice. | `services/api/detector_contract.py`; 5/5 Python tests. | PASS |
| H-020 | Double-check implementation through static, deterministic, and real browser checks. | Typecheck/build, 11 Node tests, 5 Python tests, 59 Chromium checks, authorship audit. | PASS |
| H-021 | Record remaining uncertainty instead of calling it verified. | Safari/iPadOS, Firefox, real screen-reader session remain `UNK-001` in subsystem operational state. | PASS |
| H-022 | Produce a downloadable ZIP with integrity evidence. | Release ZIP + `MANIFEST.md` + `CHECKSUMS.sha256`; archive integrity is tested before handoff. | PASS |
| H-023 | Provide a terminal path that commits the overlay without overwriting protected root files or pushing automatically. | `APPLY_TO_REPO.sh` was exercised in a throwaway Git repository: one local commit created, clean post-commit tree, protected root prototype/plan hashes unchanged, no push. | PASS |

**Verdict:** Complete for the requested hybrid foundation, with explicitly declared cross-browser/assistive-technology limitations that do not alter the delivered scope.
