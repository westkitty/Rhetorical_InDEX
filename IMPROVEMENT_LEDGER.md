# Rhetorical InDEX — Current Improvement Ledger

This ledger freezes the current pass at exactly **20 UI/UX improvements** and **20 prototype-engine/backend-equivalent improvements**. The offline one-file deliverable remains authoritative; no remote server is implied.

## UI/UX — exactly 20

| ID | Improvement | Verification |
|---|---|---|
| UI-01 | Make the lens fully operable on tablet/coarse-pointer devices, not only phone widths. | 768x1024 and 1024x768 coarse-pointer runtime paths can move the lens. |
| UI-02 | Add tap-to-place lens behavior for coarse pointers while preserving vertical scrolling. | A short tap moves the lens; ordinary drag-scroll remains usable. |
| UI-03 | Upgrade the drag handle with a smart above-finger offset and bounded movement. | Handle drag keeps lens visible and inside article bounds. |
| UI-04 | Add a user-adjustable lens-radius control with device-appropriate bounds. | Radius range updates clip/ring live and survives responsive resize. |
| UI-05 | Add a compact tablet/mobile scanner control dock for Lens, Pin, Reveal, and Radius. | Dock is reachable on coarse pointers and does not cover article text. |
| UI-06 | Add a live scanner-state badge: Live, Pinned, Reveal all, or Off. | Badge text/state updates with every lens transition. |
| UI-07 | Make scanner controls sticky on medium/tablet layouts without hiding content. | Tablet scroll keeps essential lens controls reachable. |
| UI-08 | Add confidence filtering to Findings: All, medium/high, low candidates. | List count and visible findings update correctly. |
| UI-09 | Add family filtering to Findings. | Selecting a family filters the list without altering source annotations. |
| UI-10 | Add findings search by mechanism or excerpt. | Search narrows list and supports clear/reset. |
| UI-11 | Synchronize selected finding state between list, article passage, and drawer. | Selection highlights both list row and corresponding base passage. |
| UI-12 | Add “Jump to passage” from the finding drawer. | Action closes/retains drawer appropriately and scrolls/focuses exact passage. |
| UI-13 | Convert the finding drawer into a tablet/mobile bottom sheet at narrow/coarse layouts. | Sheet stays within viewport, preserves focus trap, and avoids horizontal overflow. |
| UI-14 | Make overlapping tag stacks wrap/cap width on tablets and phones. | Multi-tag spans remain legible without page overflow. |
| UI-15 | Make the mechanism legend collapsible with state preserved during the session. | Toggle changes visibility and aria-expanded. |
| UI-16 | Make pressure-map segments interactive paragraph jump targets. | Activating a segment scrolls to its paragraph and gives transient emphasis. |
| UI-17 | Add concise keyboard-shortcut help inside the scanner. | Help disclosure lists L/A/C/E/Escape and remains keyboard accessible. |
| UI-18 | Add an in-product Reduced Motion preference independent of OS preference. | Toggle suppresses nonessential transitions/animations. |
| UI-19 | Add a Pattern/High-Contrast annotation mode so meaning is not color-only. | Annotation families gain distinguishable underline/border patterns and labels. |
| UI-20 | Add Restore scanner defaults and a visible settings-saved indicator. | Reset restores lens/filter/accessibility defaults and persisted settings reflect state. |

## Prototype engine / backend-equivalent — exactly 20

| ID | Improvement | Verification |
|---|---|---|
| ENG-01 | Replace scattered scanner globals with one versioned application-state object. | State source contains a single authoritative `appState`. |
| ENG-02 | Route state changes through a reducer-style `dispatch(action)` transition function. | Lens/filter/settings controls dispatch actions instead of mutating globals directly. |
| ENG-03 | Batch derived UI updates through `requestAnimationFrame` scheduling. | Rapid lens/filter changes coalesce without stale state. |
| ENG-04 | Add runtime capability detection for coarse pointer, hover, viewport class, and motion preference. | Capability snapshot updates on media/viewport change. |
| ENG-05 | Add a lens-geometry engine with safe padding, radius-aware clamping, and touch offset. | Unit tests cover desktop/tablet/phone bounds. |
| ENG-06 | Recalculate geometry on `visualViewport`, resize, and orientation changes. | Tablet rotation keeps lens in bounds. |
| ENG-07 | Add versioned, validated settings persistence with safe fallback on malformed storage. | Valid settings restore; malformed settings reset safely. |
| ENG-08 | Add finding-schema validation/normalization. | Invalid pressure/confidence/family values are normalized or quarantined. |
| ENG-09 | Add article-schema validation for paragraphs, segments, and referenced finding IDs. | Orphan IDs are reported and do not crash rendering. |
| ENG-10 | Build reusable finding indexes by id, family, confidence, mechanism, and passage. | Filters/search use indexes rather than ad-hoc repeated scans. |
| ENG-11 | Centralize pressure/density/dominant-family metrics in a derived-metrics engine. | Profile derives from normalized state and segment coverage once per render cycle. |
| ENG-12 | Add stable paragraph/segment IDs and pressure records for exact navigation. | Findings and pressure map resolve to stable passage IDs. |
| ENG-13 | Improve local heuristic detection so every sentence can return multiple applicable mechanisms deterministically. | A sentence matching two patterns yields both candidates. |
| ENG-14 | Deduplicate identical mechanism/span candidates while preserving repeated occurrences at different positions. | Duplicate detector hits collapse; repeated passage occurrences remain separate. |
| ENG-15 | Track passage offsets/locations in local paste mode. | Drawer “Jump to passage” works for pasted analysis too. |
| ENG-16 | Centralize untrusted-text escaping and rendered-fragment helpers. | Pasted HTML/script-like text is displayed as text and never executes. |
| ENG-17 | Add a render/error boundary that surfaces a recoverable offline error state instead of silently failing. | Forced invalid state produces visible error and Restore action. |
| ENG-18 | Harden pointer lifecycle with active-pointer ownership, `pointercancel`, and capture cleanup. | Cancelled drags do not leave the lens stuck/pinned. |
| ENG-19 | Attach detector/provenance metadata to every finding and expose it in inspection. | Drawer shows fixture vs local-heuristic origin and engine version. |
| ENG-20 | Add a pre-render integrity audit for article/finding references and state invariants. | Integrity report is clean for demo and local paste fixtures; violations are surfaced. |
