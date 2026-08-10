# Prototype Parity Matrix

The root `Rhetorical_InDEX.html` Experience Prototype is the behavioral gold
standard. This matrix records, per behavior, whether `apps/web` has been proven
to match it.

**Status vocabulary is strict, and every row carries exactly ONE primary
status.** `PASS` requires executed evidence in this environment. Implementation
being present is NOT evidence and never yields `PASS` — structural presence is
recorded in the Evidence column only. Where a check needs a browser this
environment does not have, the status is `UNVERIFIED` — not `PASS`, not `FAIL`.

## Environment for this pass

| Capability | Available | Consequence |
|---|---|---|
| Node.js 26 | Yes | Static/contract checks executed |
| Python 3.14 | Yes | Detector + contract suites executed |
| TypeScript 5.8 | Yes | Typecheck + build executed |
| Playwright + Chromium | **No** | All runtime/interaction rows are UNVERIFIED |

`pip install playwright` is blocked by this host's externally-managed-Python
policy and no system Chromium binary is present. `tools/runtime_qa.py` was
therefore **not executed in this pass**.

## Matrix

| ID | Behavior | Status | Evidence |
|---|---|---|---|
| P-01 | Article-first default route | UNVERIFIED | Requires runtime navigation |
| P-02 | Clean base article, no duplicated accessible text | PASS | `tests/artifact.test.mjs` — exactly one `#articleBase`, one `#articleOverlay` |
| P-03 | Overlay is `aria-hidden` | PASS | `tests/artifact.test.mjs` asserts `id="articleOverlay" aria-hidden="true"` |
| P-04 | Lens spatial reveal | UNVERIFIED | Requires pointer runtime |
| P-05 | Lens geometry does not alter text flow | UNVERIFIED | Requires layout measurement |
| P-06 | Reveal All | UNVERIFIED | Requires runtime interaction |
| P-07 | Multi-tag on one exact span, source text not duplicated | PASS | `test_five_mechanisms_on_one_span_do_not_duplicate_source_text` (Python); interval rendering in `artifact.test.mjs` |
| P-08 | Pressure and confidence remain independent | PASS | `ScoringIndependenceTests` — both corners reachable; `score_confidence` has no pressure parameter |
| P-09 | Finding selection / drawer opens | UNVERIFIED | Requires runtime interaction |
| P-10 | Jump to passage | UNVERIFIED | Requires runtime interaction |
| P-11 | Findings search / filter | UNVERIFIED | Requires runtime interaction |
| P-12 | Pressure profile is decomposable, no master score | PASS | `test_profile_is_decomposable_and_has_no_master_score`, `test_profile_exposes_no_single_summarizing_number` |
| P-13 | Compare / Framing Switcher | UNVERIFIED | Requires runtime interaction |
| P-14 | Event Record | UNVERIFIED | Requires runtime interaction |
| P-15 | Compare unavailable for single-document scans | UNVERIFIED | Structural: gate present in `app.ts`. Runtime behavior last observed in a prior session and NOT re-executed here. |
| P-16 | Keyboard route through findings | UNVERIFIED | Requires runtime interaction |
| P-17 | Drawer focus trap | UNVERIFIED | Requires runtime focus behavior |
| P-18 | Focus restoration after drawer close | UNVERIFIED | Requires runtime focus behavior |
| P-19 | Escape closes drawer | UNVERIFIED | Requires runtime interaction |
| P-20 | Tablet tap-to-place Lens | UNVERIFIED | Requires touch runtime |
| P-21 | Tablet drag handle + pointer capture | UNVERIFIED | Requires touch runtime |
| P-22 | `pointercancel` cleanup | UNVERIFIED | Requires touch runtime |
| P-23 | Radius-aware bounds clamping | UNVERIFIED | Requires layout runtime |
| P-24 | Resize / orientation re-clamp | UNVERIFIED | Requires layout runtime |
| P-25 | Sticky header clearance at tablet widths | UNVERIFIED | Requires layout runtime |
| P-26 | No horizontal overflow | UNVERIFIED | Requires layout runtime |
| P-27 | Reduced Motion honored | UNVERIFIED | Structural: present in CSS and as an explicit setting (`tests/source-contract.test.mjs` presence guard). Runtime behavior unexecuted. |
| P-28 | Non-color mechanism identification (Pattern Mode) | UNVERIFIED | Structural: Pattern Mode present (presence guard only). Runtime behavior unexecuted. |
| P-29 | Artifact makes no network requests | PASS | `tests/security.test.mjs` — no `fetch`/XHR/WebSocket/EventSource/sendBeacon in artifact |
| P-30 | Hostile article text cannot inject markup | PASS | `tests/security.test.mjs` — real compiled `esc` exercised against 6 payloads |
| P-31 | Artifact makes no calibration/benchmark claim | PASS | `tests/security.test.mjs` overclaiming-language assertions |
| P-32 | Build is reproducible | PASS | Two consecutive clean builds, identical SHA-256 |

## Summary

| Status | Count |
|---|---:|
| PASS | 9 |
| FAIL | 0 |
| UNVERIFIED | 23 |

**No row is marked PASS on the basis of code inspection alone.** The 23
UNVERIFIED rows are not known failures; they are unmeasured in this environment.
Counts are machine-verified by `tools/check_traceability.py`, which also rejects
any row carrying more than one primary status.

## To convert UNVERIFIED to PASS

```bash
pip install playwright && python3 -m playwright install chromium
npm run qa:runtime
```

`qa/runtime-results.json` and `qa/screens/*.png` are **stale**: they were
produced against artifact `8b3086f5…`, and the current artifact is
`1a5ebc36…`. They are retained as historical evidence and must not be read as
current. Screenshots are secondary evidence in any case — they show a moment,
not a behavior.
