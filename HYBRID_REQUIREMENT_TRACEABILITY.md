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
| H-017 | Pasted text is honestly labeled unbenchmarked and cannot invent Compare/Event/Material Omission. | Local Preview runtime journey; Compare unavailable; strict Python contract rejects `material_omission`; `tests/local-preview-contract.test.mjs` proves it never emits `material_omission`. | PASS |
| H-018 | Do not import the experimental Express/Gemini server or URL fetcher. | No server dependency or fetch/XHR runtime path in the web artifact; donor ledger marks them rejected. | PASS |
| H-019 | Establish a strict future Python boundary for the four-mechanism detector slice, and document it accurately as the future Level 3 Instrument Alpha detector, not the shipped Level 2 Local Preview heuristic. | `services/api/detector_contract.py`; Python tests; `services/api/README.md` three-level detector description. | PASS |
| H-020 | Double-check implementation through static, deterministic, and real browser checks. | Typecheck/build, 11 Node tests, 5 Python tests, 59 Chromium checks, authorship audit. | PASS |
| H-021 | Record remaining uncertainty instead of calling it verified. | Safari/iPadOS, Firefox, real screen-reader session remain `UNK-001` in subsystem operational state. | PASS |
| H-022 | Produce a downloadable ZIP with integrity evidence. | Release ZIP + `MANIFEST.md` + `CHECKSUMS.sha256`; archive integrity is tested before handoff. | PASS |
| H-023 | Provide a terminal path that commits the overlay without overwriting protected root files or pushing automatically. | `APPLY_TO_REPO.sh` was exercised in a throwaway Git repository: one local commit created, clean post-commit tree, protected root prototype/plan hashes unchanged, no push. | PASS |

## Independent review closure (F-001 – F-004)

An independent repository review of commit `dd6a7a5` (`MERGE READY WITH MINOR FOLLOW-UPS`) identified four findings. This cleanup pass closes them:

| ID | Finding | Repair | Evidence | Status |
|---|---|---|---|---|
| F-001 | Documentation described the four-mechanism heuristic detector as future/pending work while it already shipped in `apps/web/src/app.ts`, unvalidated by `services/api/detector_contract.py`. | Formalized the three detector levels (Level 1 Experience Prototype, Level 2 Local Preview — already implemented, Level 3 Instrument Alpha — not yet implemented) across `INSTRUMENT_ALPHA_README.md`, `HYBRID_RELEASE_NOTES.md`, `apps/web/OPERATIONAL_STATE.md`, `docs/migration/HYBRID_DECISION.md`, `docs/migration/HYBRID_SESSION_RECORD.md`, `services/api/README.md`. Added `packages/schema/src/localPreviewContract.ts`, wired into `localPreviewFindings` so Local Preview candidates are validated (rejected, not repaired) before entering application state. | `tests/local-preview-contract.test.mjs` proves every current `localPreviewFindings` output is accepted by the real `services/api/detector_contract.py`. | CLOSED |
| F-002 | No automated check guaranteed TypeScript and Python vocabulary (`MechanismId`/`PressureLevel`/`ConfidenceLevel`/`VoiceClass` vs `INTRINSIC_ALPHA_SLICE`/`PRESSURE`/`CONFIDENCE`/`VOICE`) stayed synchronized. | Added `packages/schema/schema.json` enums as the single canonical vocabulary source. | `tests/vocabulary-parity.test.mjs` (Node) and `tests/python/test_vocabulary_parity.py` (Python) fail if either language drifts from `schema.json` or from each other. | CLOSED |
| F-003 | Several `tests/source-contract.test.mjs` assertions checked only for token presence in source and could be mistaken for behavioral proof. | Retitled those tests as explicit structural/source-presence guards; added a genuine behavioral regression test for the validator logic in `tests/local-preview-contract.test.mjs`. Chromium/Playwright runtime QA (`tools/runtime_qa.py`) remains the authoritative behavioral layer for browser-specific interaction (pointer capture, focus trap, geometry). | Updated test names/comments in `tests/source-contract.test.mjs`. | CLOSED |
| F-004 | Typo `"Praming a debate as a stark choice"` in the `false_dilemma` P2 pressure rubric. | Corrected to `"Framing a debate as a stark choice"` in `packages/taxonomy/taxonomy.json`; rebuilt `apps/web/dist/index.html` so the baked-in copy matches. | Confirmed no other occurrence of the typo anywhere in the repository. | CLOSED |

**Verdict:** Complete for the requested hybrid foundation, with explicitly declared cross-browser/assistive-technology limitations that do not alter the delivered scope. F-001 through F-004 from the independent review are closed as of this cleanup pass; exact test counts and any environment-limited (unverified) checks are recorded in `HYBRID_QA_REPORT.md`.
