# Rhetorical InDEX — Hybrid Instrument Alpha QA Report

> **Superseded for current status.** This report records the hybrid foundation build and its
> cleanup pass. Artifact hashes and Chromium figures below are historical. For the current
> artifact, current per-behavior verification status, and the Level 3 detector, see
> `INSTRUMENT_ALPHA_TRACEABILITY.md`, `tests/prototype-parity/PARITY_MATRIX.md` and
> `KNOWN_LIMITATIONS.md`. No Chromium run was executed in the Instrument Alpha completion pass.

## Verdict

**Verified foundation in the inspected scope; cross-browser and real assistive-technology coverage remain unverified.**

This report covers the additive Instrument Alpha foundation only. It does not replace the existing root `QA_REPORT.md` for the standalone Experience Prototype and does not claim that the future production detector, URL ingestion, News-Scale comparison, or evidence graph exist.

## Baseline relationship

- Canonical repository: `westkitty/Rhetorical_InDEX`
- Observed canonical clean-import commit: `a685c4d98c0be35f8ba2019be6bd2a3b6f5d9ee5`
- Golden behavior reference: existing root `Rhetorical_InDEX.html`
- Hybrid artifact: `apps/web/dist/index.html`
- Hybrid artifact SHA-256: `8b3086f56998b9f74a3533de8db93195ab2cb308bca6d715d15842b1f3d61a3a`

The release overlay intentionally does **not** contain or overwrite the root prototype or implementation plan.

## Validation performed

| Gate | Result |
|---|---:|
| TypeScript typecheck | PASS |
| Standalone web build | PASS |
| Node contract/artifact tests | **11 / 11 PASS** |
| Python detector-contract tests | **5 / 5 PASS** |
| Chromium runtime/parity checks | **59 / 59 PASS** |
| Web Authorship deterministic audit | **PASS** |
| Additive commit installer dry-run in throwaway Git repo | **PASS** |
| Protected root prototype/plan unchanged by installer | **PASS** |
| Observed external runtime requests | **0** |
| Observed console errors in tested paths | **0** |
| Base/Lens overlay geometry delta | **0.00** at all four tested viewport groups |

Chromium runtime groups:

- desktop 1440×1000;
- tablet portrait 768×1024;
- tablet landscape 1024×768;
- phone 410×844.

## Runtime behaviors directly checked

- one semantic article DOM;
- Lens overlay is `aria-hidden`;
- spatial Lens reveal and Reveal All;
- exact finding geometry and non-flow Lens readout;
- base/overlay geometry remains aligned;
- finding drawer opens;
- repeated Tab navigation remains trapped in the open drawer;
- focus restores after closing the drawer;
- Reduced Motion and Pattern Mode state;
- local pasted-text preview is explicitly unbenchmarked;
- local preview emits intrinsic candidates;
- single-document Compare remains unavailable;
- touch Lens handle visibility;
- radius-aware Lens bounds;
- pointer ownership and `pointercancel` cleanup;
- sticky scanner controls clear the actual wrapped header height;
- no horizontal overflow in tablet/phone checks;
- no external runtime requests or console errors in the exercised paths.

## Defects found and repaired during this build

### QA-001 — Drawer focus restoration was invalidated by list re-render

- **Severity:** major accessibility regression
- **Cause:** selecting a finding rebuilt the findings list and destroyed the opener element saved for restoration.
- **Repair:** selection updates no longer replace the opener DOM node.
- **Verification:** automated drawer-close check confirms focus returns to the invoking finding control.

### QA-002 — Tablet sticky scanner offset could fall under wrapped header

- **Severity:** major tablet usability regression
- **Cause:** scanner sticky offset assumed a static header height while navigation wraps at tablet widths.
- **Repair:** the application tracks the actual topbar height with `ResizeObserver` and repositions sticky scanner controls accordingly.
- **Verification:** portrait and landscape geometry checks confirm toolbar top clears the rendered topbar bottom.

### QA-003 — Pointer-cancel state was cleared internally but not immediately reflected visually

- **Severity:** medium interaction-state defect
- **Cause:** pointer ownership cleanup did not force the Lens visual state to re-render.
- **Repair:** drag end/cancel now re-renders Lens state immediately.
- **Verification:** portrait, landscape, and phone checks confirm `pointercancel` clears ownership.

## Epistemic-integrity checks

The release also statically verifies that the built artifact does not contain:

- `Ground Truth` claims;
- invented human-reviewed benchmark metrics;
- live URL fetching;
- a `material_omission` intrinsic detector path.

The taxonomy screen explicitly states that human-reviewed performance metrics have not yet been established.

## Environment limitations

The container had no outbound DNS, so a local `git clone` or dependency download could not be used. Canonical repository files were inspected through the connected GitHub API, and the hybrid is packaged as a strictly additive overlay.

Managed Chromium in this environment blocks ordinary localhost/file navigation. Runtime QA therefore used the **exact built standalone HTML** with Playwright `page.set_content()`, the same class of workaround used in the verified Experience Prototype QA. The artifact itself makes no runtime network requests.

Not verified here:

- Safari/iPadOS;
- Firefox;
- a real screen-reader session.

Those are not known failures, but they remain unverified and are recorded in `apps/web/OPERATIONAL_STATE.md`.

## Cleanup pass — independent review findings F-001 through F-004

An independent repository review of commit `dd6a7a5` returned **MERGE READY WITH MINOR FOLLOW-UPS** and identified four findings (F-001 through F-004). This section records their closure truthfully, including what was and was not re-verified.

### What changed

- `packages/schema/src/localPreviewContract.ts` (new): validates every Local Preview candidate against the same semantic invariants as `services/api/detector_contract.py` before it enters application state. Wired into `localPreviewFindings` in `apps/web/src/app.ts`; invalid candidates are rejected (dropped, counted, surfaced in the live-region announcement), never silently repaired.
- `packages/schema/schema.json`: extended with `voiceClass` and `intrinsicAlphaSlice` enums as the single canonical vocabulary source shared by TypeScript and Python.
- `tools/build_web.py`: embeds that canonical vocabulary into the built artifact's bootstrap data (`window.RI_BOOTSTRAP.vocabulary`) instead of it being hand-duplicated in the browser bundle.
- `tests/vocabulary-parity.test.mjs` (new, Node) and `tests/python/test_vocabulary_parity.py` (new, Python): fail if TypeScript's `contracts.ts` unions or Python's `detector_contract.py` sets drift from `packages/schema/schema.json` or from each other.
- `tests/local-preview-contract.test.mjs` (new): executes the real compiled `localPreviewFindings` (extracted from `apps/web/dist/app.js`, not reimplemented) against representative text and proves every candidate it produces is accepted by the real `services/api/detector_contract.py`, run as a Python subprocess.
- `tests/source-contract.test.mjs`: three tests renamed/annotated `[structural guard]` with comments clarifying they check source-token presence, not runtime behavior; the Chromium suite and the new `local-preview-contract.test.mjs` are named as the actual behavioral evidence.
- `packages/taxonomy/taxonomy.json`: fixed `"Praming a debate..."` → `"Framing a debate..."` in the `false_dilemma` P2 rubric. Confirmed (`grep -r`) this string did not appear anywhere else in the repository outside the taxonomy source and its baked-in copy in `apps/web/dist/index.html`, which is now corrected by rebuild.
- `INSTRUMENT_ALPHA_README.md`, `HYBRID_RELEASE_NOTES.md`, `HYBRID_REQUIREMENT_TRACEABILITY.md`, `apps/web/OPERATIONAL_STATE.md`, `docs/migration/HYBRID_DECISION.md`, `docs/migration/HYBRID_SESSION_RECORD.md`, `services/api/README.md`: now describe three explicit detector levels (Level 1 Experience Prototype, Level 2 Local Preview — implemented, unbenchmarked, present since the original hybrid commit, Level 3 Instrument Alpha — the future calibrated detector, not yet implemented) instead of implying the four-mechanism heuristic detector was future work.

### Exact commands run and results (this cleanup pass)

| Check | Command | Result |
|---|---:|---:|
| TypeScript typecheck | `npm run typecheck` | PASS |
| Web build | `npm run build` | PASS — `apps/web/dist/index.html` SHA-256 `4b2652f6d4985454bf2b6236d622ad32ce3fa3c34c20124037201f70291879b9` |
| Build reproducibility | rebuilt twice in a row, hashes compared | IDENTICAL both times |
| Node test suite | `node --test tests/*.test.mjs` | **20 / 20 PASS** (11 pre-existing tests, unchanged in count, 3 renamed `[structural guard]` for F-003 + 5 new in `tests/vocabulary-parity.test.mjs` + 4 new in `tests/local-preview-contract.test.mjs`) |
| Python test suite | `python3 -m unittest discover -s tests/python -p 'test_*.py'` | **8 / 8 PASS** (5 pre-existing `test_detector_contract` + 3 new `test_vocabulary_parity`) |
| Adversarial: TS validator (`validateLocalPreviewCandidate`) | 11 hand-constructed malformed candidates (bad mechanism, bad pressure/confidence/voice, out-of-bounds span, inverted span, empty/whitespace criteria, non-integer index) plus 1 positive control | **11/11 rejected, positive control accepted** |
| Adversarial: vocabulary-drift detection | Injected an extra `"robot"` value into `packages/schema/schema.json`'s `voiceClass` enum, ran both parity tests, reverted | **Both the Node and Python parity tests failed as expected**, proving they actually detect drift and are not vacuous |
| Typo recheck | `grep -rl "Praming"` across the full repository | **0 occurrences** |

### Explicitly UNVERIFIED in this cleanup pass (not converted to PASS)

- **Chromium/Playwright runtime QA (`tools/runtime_qa.py`, the 59-check suite behind `qa/runtime-results.json` and `qa/screens/*`).** Playwright is not installed in this environment and `pip install playwright` is blocked by the environment's externally-managed-Python protection; no system Chromium binary is available either. This suite was **not re-executed** in this cleanup pass. `qa/runtime-results.json` and `qa/screens/*.png` reflect the artifact hash `8b3086f5...` from the original hybrid build and are now **stale** relative to the rebuilt artifact hash `4b2652f6...` above. The changes in this pass do not touch DOM structure, element IDs, CSS, or the scanner/Lens/drawer implementation the Chromium suite exercises — only `localPreviewFindings`' internal candidate-validation step and doc text — so a regression in that specific surface is unlikely, but this is a reasoned expectation, not a re-measurement. **Re-run `npm run qa:runtime` in an environment with Playwright + Chromium before treating the 59-check figure as current.**
- Safari/iPadOS, Firefox, and a real screen-reader session remain unverified, unchanged from the original report.

### Findings closed

See `HYBRID_REQUIREMENT_TRACEABILITY.md` → "Independent review closure (F-001 – F-004)" for the finding-by-finding repair/evidence table. Summary: **F-001, F-002, F-003, F-004 are all closed** by the changes and tests above.
