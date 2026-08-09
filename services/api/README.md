# API / detector service boundary

This directory deliberately does **not** contain the AI Studio Express/Gemini server or URL fetcher.

`detector_contract.py` is the network-free validation boundary for the **Level 3 Instrument Alpha detector** — the future calibrated Python service for the bounded four-mechanism intrinsic slice: exact spans, strict enums, nonempty structured criteria, repeated-excerpt disambiguation, and an explicit ban on cross-document mechanisms in the intrinsic slice. That calibrated detector is **not yet implemented**.

This boundary is not the only place the same invariants are enforced today. The **Level 2 Local Preview detector** (`apps/web/src/app.ts`, `localPreviewFindings`) already ships in the browser build and runs on real pasted text — it is a heuristic, unbenchmarked, client-side detector for the same four mechanisms, explicitly labeled "Local Preview — Unbenchmarked" in the UI. It validates its own output against `packages/schema/src/localPreviewContract.ts`, a TypeScript mirror of this file's invariants, so it cannot silently violate the semantic contract this module represents even though it does not call into Python. `tests/local-preview-contract.test.mjs` proves every candidate `localPreviewFindings` produces is also accepted by `validate_intrinsic_candidate` in this file, and `tests/vocabulary-parity.test.mjs` / `tests/python/test_vocabulary_parity.py` prove the two languages' allowed vocabularies cannot drift apart undetected.

The three detector levels in this repository, in full:

1. **Level 1 — Experience Prototype detector**: deterministic/synthetic demonstration inside the root `Rhetorical_InDEX.html`; not a calibrated analytical instrument.
2. **Level 2 — Local Preview detector**: heuristic, unbenchmarked, runs on real pasted text today, bounded to this same four-mechanism slice, explicitly non-authoritative. **Already implemented.**
3. **Level 3 — Instrument Alpha detector**: the future calibrated detector this file's contract exists to govern, benchmarked against a human-reviewed corpus. **Not yet implemented.**

The next substantive milestone is to replace or augment the current heuristic Level 2 detector with the first calibrated Level 3 Instrument Alpha detector behind this contract, then build the human-reviewed benchmark around the functioning detector. URL ingestion remains deferred until Instrument Alpha is credible.
