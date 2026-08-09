# Verified Hybrid Migration Decision

## Decision

Rhetorical InDEX keeps four forms of authority separate:

1. **Repository and product authority:** the existing GitHub repository and its implementation plan.
2. **Behavioral authority:** the verified standalone `Rhetorical_InDEX.html` Experience Prototype.
3. **Donor implementation:** reviewed domain/taxonomy/fixture concepts from the experimental component application.
4. **Instrument Alpha implementation:** the new code under `apps/`, `packages/`, `services/`, and `tests/`.

The new code is additive. It does not overwrite the standalone prototype.

## Why this structure

The standalone prototype has the strongest evidence for Lens behavior, tablet interaction, accessibility, responsive layout, and honest fixture boundaries, but a single large HTML file is not the long-term production architecture.

The experimental component application contains useful typed contracts, taxonomy records, fixture models, exact-span utilities, and Compare/Event interface ideas, but it also accumulated unreliable networking, provenance, runtime QA, and Lens behavior. Promoting that codebase wholesale would inherit those risks.

The hybrid therefore carries forward the verified behavior while selectively transplanting the reusable domain pieces.

## Current implementation choices

### Kept from the standalone prototype behavior

- article-first scanner;
- clean base article plus `aria-hidden` clipped visual overlay;
- Lens position/radius as explicit state;
- spatial reveal and Reveal All;
- exact passage navigation;
- pointer capture/cancel lifecycle;
- radius-aware bounds;
- resize/orientation re-clamping;
- drawer focus trap/restore;
- Reduced Motion and non-color Pattern Mode;
- synthetic comparison boundaries.

### Transplanted from the experimental component application

- one-Finding/one-mechanism domain contract;
- Alpha-0 taxonomy records;
- synthetic SB-802 event/claim/evidence structure;
- same-claim/different-wording Framing Switcher concept;
- Event Record object model;
- source-dependence and omission data shapes as fixture concepts.

### Rejected or deferred

- Express/Gemini server;
- live URL ingestion and its SSRF surface;
- model-generated omission from single-document scans;
- stale self-authored QA documents;
- corrupted nested archives;
- invented benchmark metrics;
- production claims about detector accuracy.

## Next gate

The next substantive milestone is the first real Python detector vertical slice for:

- Loaded language
- Presupposition
- Agent suppression
- False dilemma

It must sit behind `services/api/detector_contract.py`, then be measured with the first human-reviewed benchmark before additional mechanisms or URL ingestion are promoted.
