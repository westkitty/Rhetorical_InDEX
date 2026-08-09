# Rhetorical InDEX — Release Notes

## Release focus

This packet implements and validates exactly **20 UI/UX improvements** and **20 prototype-engine/backend-equivalent improvements**, with tablet lens behavior treated as release blocking.

## Tablet lens

The prior width/touch dead zone is removed. Coarse-pointer operation now uses capability detection rather than a phone-only breakpoint, with tap-to-place, a dedicated drag handle, above-finger offset, radius-aware bounds, real touch-scroll coexistence, pointer-cancel cleanup, live rotation handling and large-coarse-screen support.

Medium-width tablet layouts now use a full-width article reading surface through 1100 CSS pixels, and the sticky scanner toolbar derives its offset from the actual navigation height.

## UI/UX additions

Findings now support search, family/confidence filters, synchronized selection and exact passage jumps. The scanner adds a live state badge, adjustable lens radius, touch dock, collapsible legend, interactive pressure map, keyboard help, Pattern Mode, Reduced Motion, tablet/mobile bottom-sheet inspection and reset/settings feedback.

## Internal engine additions

The offline prototype now uses one versioned state model with reducer-style transitions, render batching, capability detection, responsive lens geometry, validated settings fallback, finding/article normalization, reusable indexes, derived metrics, stable passage IDs, deterministic multi-mechanism heuristics, positional deduplication, location metadata, central escaping, recoverable errors, hardened pointer lifecycle, provenance and integrity auditing.

## QA

Final pre-package gates: 80/80 static, 75/75 Chromium runtime, 36/36 accessibility/semantics, 10/10 HTML validator, zero CSS parse errors, zero high-severity browser-JS heuristic findings, and Web Authorship Gate PASS.

Known validation limits: Safari/iPadOS, Firefox, and a real screen-reader session were not available. Managed Chromium blocks direct `file://` navigation, so exact file contents were executed in a fresh Chromium frame via CDP instead.
