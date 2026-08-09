# Rhetorical InDEX — Hybrid Instrument Alpha QA Report

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
