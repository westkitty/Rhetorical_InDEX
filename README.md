# Rhetorical InDEX

Rhetorical InDEX is an offline experience prototype for inspecting **interpretive pressure** in news language. Open `Rhetorical_InDEX.html` in a modern browser; no server, install step, account, or network connection is required.

## What is in this release

- An article-first scanner with a movable rhetoric lens.
- Tablet/coarse-pointer tap and drag interaction, including portrait/landscape behavior.
- Multi-tag rhetorical findings with pressure and confidence kept separate.
- Search, confidence and family filters, exact finding-to-passage navigation, pressure-map jumps, Pattern Mode and Reduced Motion.
- Fixture-backed Compare and Event Record views.
- A local paste demonstration using intentionally limited heuristics; it does **not** perform live fact checking or web comparison.
- The complete implementation plan embedded in the HTML and provided separately as Markdown.
- Full improvement traceability and QA evidence.

## Open it

Double-click `Rhetorical_InDEX.html` or open it through your browser's **Open File** command. The file is deliberately self-contained and has no external runtime dependencies.

## Important prototype boundary

The included comparison/event material is fictional demonstration data. Paste mode runs only the small local heuristic detector described in the plan. No result should be interpreted as a live source lookup, production fact check, ideology score, harm score, or trust score.

## Tablet controls

On coarse-pointer devices, tap article text to place the lens. Drag the floating `⌖` handle for continuous scanning; the inspected area stays above the finger. Lens, Pin, Reveal All and size controls remain available on the touch control dock. Normal vertical touch scrolling is preserved.

See `QA_REPORT.md` and `IMPROVEMENT_TRACEABILITY.md` for validation evidence and known environment limitations.
