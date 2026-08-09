# Rhetorical InDEX — QA and Bug Sweep Report

## 1. Executive summary

- **Target:** `Rhetorical_InDEX.html` plus its implementation plan and release packet.
- **Scope inspected:** scanner UI, responsive/tablet behavior, touch/pointer lifecycle, filtering/navigation, paste-mode safety, internal state/data engine, accessibility/contrast, embedded/external plan parity, offline dependency surface, and release packaging inputs.
- **Editing mode:** fixes applied directly to the standalone HTML and plan.
- **Validation mode:** deterministic source checks plus real Chromium DOM/CSS/JavaScript execution through CDP, including emulated touch.
- **Current-turn UI/UX improvements:** **20 / 20 implemented and traced**.
- **Current-turn engine/backend-equivalent improvements:** **20 / 20 implemented and traced**.
- **Confirmed current-turn defects found:** 6.
- **Confirmed current-turn defects fixed:** 6.
- **Remaining confirmed defects in inspected scope:** 0.
- **Final bug-sweep verdict:** **No unresolved confirmed bugs in inspected scope; remaining risks need verification.**

The remaining risks are browser-environment coverage, not known failures: this runtime could execute Chromium but could not navigate ordinary `file://` URLs because the installed browser is organization-policy managed. The exact standalone HTML was therefore injected into a fresh blank Chromium frame through CDP; its inline HTML/CSS/JavaScript executed normally with no network dependencies. Firefox/Safari and a real screen reader were not available.

## 2. Validation summary

| Gate | Result |
|---|---:|
| Exact 20 UI + 20 engine traceability/static checks | **80 / 80 pass** |
| Chromium end-to-end/runtime checks | **75 / 75 pass** |
| Accessibility/contrast/semantics | **36 / 36 pass** |
| HTML Artifact Studio validator | **10 / 10 pass** |
| JavaScript syntax | **Pass** |
| CSS parser | **0 parse errors** |
| Browser-JS heuristic scan | **0 high severity** |
| Web authorship gate | **PASS** |
| External runtime dependencies | **0** |
| `fetch` / XHR runtime calls | **0** |

Current artifact identities before release packaging:

- `Rhetorical_InDEX.html` — SHA-256 `bfe0020facf08cad391caa4dcca9a0428e765d8f0f4b5afeaac11f883c10dd18`
- `Rhetorical_InDEX_Implementation_Plan.md` — SHA-256 `40dce003d1ba8525d2be8b1b24e8e72077bcedf77adc8599bfa6064042a75c57`

## 3. Tablet lens validation

Tablet support was treated as a release-blocking path because the lens is the primary interaction metaphor.

Validated in Chromium:

- 768 × 1024 coarse-pointer portrait;
- live 768 × 1024 → 1024 × 768 orientation change without reloading;
- 1366 × 1024 coarse-pointer large-screen path;
- touch dock and drag handle visibility;
- tap-to-place lens;
- real touch-scroll coexistence;
- drag-handle scanning with pointer capture;
- above-finger lens offset;
- pin state and status badge;
- Reveal All / Lens state coordination;
- radius slider and tablet/phone bounds;
- `pointercancel` ownership cleanup;
- rotation/resize geometry clamping;
- dynamic sticky-toolbar clearance from the real top-navigation height;
- full-width medium/tablet reading layout through 1100 CSS pixels;
- bottom-sheet inspector and inert closed state;
- no horizontal document overflow.

Screenshots are included in `qa/screens/` for desktop, tablet portrait, tablet landscape, and phone.

## 4. Sweep history

| Pass | Purpose | Bugs found | Fixes | Result |
|---|---|---:|---:|---|
| 1 | Baseline/root-cause + first implementation sweep | 3 | 3 | Tablet path became operable; metric/range defects repaired |
| 2 | Real browser responsive/visual and DOM integrity sweep | 3 | 3 | Medium tablet layout, sticky offset, and duplicate IDs repaired |
| 3 | Independent closure resweep | 0 | 0 | 80/80 static, 75/75 runtime, 36/36 accessibility all pass |

## 5. Current-turn bug ledger

### BUG-013 — Tablet lens dead zone
- **Status:** fixed
- **Severity:** high
- **Affected area:** tablet/coarse-pointer scanner interaction
- **Evidence:** prior touch handle was displayed only below 680px while article pointer tracking ignored touch, leaving ordinary 768–1024px tablets without a reliable continuous lens path.
- **Repair:** capability-based touch dock/handle, tap-to-place article behavior, dedicated handle drag with pointer capture, touch offset, radius-aware clamping, and tablet/large-coarse media rules.
- **Validation:** Chromium portrait, landscape rotation, large-coarse, touch-scroll, tap, drag, pin, radius, and cancel tests pass.

### BUG-014 — Lens range values could snap away from displayed state
- **Status:** fixed
- **Severity:** medium
- **Affected area:** lens-radius controls
- **Evidence:** `min=78`, `step=4`, and default value 145 placed legitimate state values off the native range step grid; Chromium snapped a requested value to a neighboring step.
- **Repair:** both range controls now use one-pixel steps while retaining device-specific min/max bounds.
- **Validation:** Chromium state and CSS `--lens-r` stay identical after range changes.

### BUG-015 — Fully covered metric was capped at 99%
- **Status:** fixed
- **Severity:** medium
- **Affected area:** derived density metrics
- **Evidence:** metrics used `Math.min(99, ...)`, so a genuinely 100%-covered synthetic segment reported 99%.
- **Repair:** legitimate density is now capped at 100%, not 99%.
- **Validation:** multi-tag single-segment engine fixture reports 100% confirmed density without double-counting.

### BUG-016 — 1024px tablet landscape used compressed desktop two-column scanner
- **Status:** fixed
- **Severity:** medium
- **Affected area:** responsive scanner layout
- **Evidence:** visual Chromium pass showed a narrow article beside a 330px support rail at 1024px.
- **Repair:** the medium responsive layout now extends through 1100px and uses a full-width article column with support panels below.
- **Validation:** 1024 × 768 Chromium article panel exceeds 900px and has zero horizontal overflow.

### BUG-017 — Sticky scanner offset assumed a fixed header height
- **Status:** fixed
- **Severity:** medium
- **Affected area:** tablet sticky controls
- **Evidence:** tablet navigation can occupy two rows while scanner sticky `top` was hard-coded, creating a deterministic overlap risk on scroll.
- **Repair:** scanner sticky offset now uses a CSS variable synchronized to the rendered topbar height on bootstrap, resize, orientation, and viewport changes.
- **Validation:** touch-scroll runtime confirms scanner sticky top remains at or below the actual topbar bottom.

### BUG-018 — Base and overlay article layers duplicated paragraph IDs
- **Status:** fixed
- **Severity:** medium
- **Affected area:** DOM identity, anchor navigation, accessibility tooling
- **Evidence:** runtime duplicate-ID check found `paragraph-1` through `paragraph-7` in both base and aria-hidden scan layers.
- **Repair:** stable paragraph IDs now exist only on the interactive base layer; the visual scan overlay keeps data indices without IDs.
- **Validation:** runtime unique-ID checks pass in both demo and local paste modes.

## 6. Suspected risks reviewed

- **Bottom sheet appeared beyond 1024px during an early test:** disproven. The assertion sampled the 280ms slide transition at ~100ms; after transition completion the fixed sheet resolves to the CSS viewport bottom. Runtime test now waits for the state transition before geometry assertion.
- **Browser-JS `duplicate-id` heuristic:** reviewed. The scanner reports a template expression as a possible duplicate; real rendered DOM uniqueness is now explicitly tested in demo and paste modes.
- **Browser-JS `innerHTML` heuristics:** reviewed. Dynamic text routes through the central `esc()` helper, and a script-like paste payload is verified to remain literal text and never create/execute a script element.
- **Listener lifecycle heuristic:** reviewed. Page-lifetime listeners are owned by one `AbortController`; temporary drawer actions are `once:true`.

## 7. Accessibility and presentation review

The accessibility suite covers key contrast pairs, semantic landmarks, labels for touch/range/filter controls, aria-hidden duplicate overlay, hidden/inert dialog state, live region, keyboard activation, focus trap, Escape behavior, reduced-motion support, 54px touch handle, confidence border styles, Pattern Mode non-color family signals, pressure text labels, and collapsible legend state.

Web-authorship audit verdict is **PASS**. Two minor non-blocking signals remain: the transient paragraph-target pulse is intentional state feedback, and the repeated rounded-container grammar is intentional visual language rather than an unreviewed default.

## 8. Final verdict

**No unresolved confirmed bugs in inspected scope; remaining risks need verification.**

Before a public browser-support promise, run the same interaction suite in Safari/iPadOS and Firefox and complete a real assistive-technology session. No current evidence indicates a failure in those environments; they were simply unavailable here.
