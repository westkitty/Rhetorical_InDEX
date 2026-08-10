# Operational State: Rhetorical InDEX Instrument Alpha Web

<!-- operational-state:metadata
{
  "artifact_path": "apps/web/dist/index.html",
  "current_baseline": {
    "identity": "apps/web/dist/index.html sha256 1a5ebc364fb0f53ac8845b1b7e9ddeac202a13f0020ac0458e263e7bef267812",
    "last_verified": "2026-08-09T22:30:00Z",
    "state": "current-baseline"
  },
  "last_updated": "2026-08-09T22:30:00Z",
  "linked_parent_state": null,
  "project_id": "rhetorical-index-instrument-alpha-web",
  "project_name": "Rhetorical InDEX Instrument Alpha Web",
  "project_root": "apps/web",
  "schema_version": 1,
  "scope_boundaries": [
    "Instrument Alpha web application only",
    "The root standalone Rhetorical_InDEX.html remains the golden Experience Prototype and is not governed or replaced by this subsystem state"
  ],
  "state_revision": 5
}
-->

## 1. Project Identity and Scope

- **Project ID:** `rhetorical-index-instrument-alpha-web`
- **Purpose:** Govern the additive Instrument Alpha web application while preserving the root standalone Experience Prototype as the golden behavioral reference.
- **Project type:** Dependency-light TypeScript web application with embedded synthetic fixtures and offline local-preview analysis.
- **Primary root or artifact:** `apps/web` / `apps/web/dist/index.html`
- **Target environment:** Modern browser. Chromium was directly verified in an earlier release only; not re-executed since.
- **Canonical authority:** Explicit user decisions, the root implementation plan, and verified prototype behavior.
- **Governed scope:** Instrument Alpha web application only.
- **Explicitly not governed:** Root `Rhetorical_InDEX.html`, future live URL ingestion, production comparison/evidence infrastructure, and unrelated repository systems.

## 2. Current Baseline

- **Primary artifact:** `apps/web/dist/index.html`
- **Baseline state:** `current-baseline`. Chromium verification is **stale** (collected against artifact `8b3086f5…`); see the artifact-identity note before section 5.
- **Source/build identity:** SHA-256 `1a5ebc364fb0f53ac8845b1b7e9ddeac202a13f0020ac0458e263e7bef267812` (see Revision 5).
- **Active default user route:** Scanner with explicit synthetic fixture; pasted text switches to Local Preview — Unbenchmarked.
- **Delivery state:** Self-contained HTML exists inside the additive overlay package.
- **Last verified baseline:** 2026-08-09T22:30:00Z (deterministic suites only; no browser run).

## 3. Artifact Contract

The subsystem must remain additive to the canonical repository. It provides one self-contained built HTML artifact plus TypeScript source, shared schemas/taxonomy/fixtures, a strict Python detector-validation boundary, deterministic tests, and Chromium parity QA. It must not overwrite the golden root prototype, claim benchmarked detector accuracy, perform live URL fetching, or invent cross-document analysis for pasted text.

## 4. Active Invariants

Add stable `INV-###` entries for rules future work must preserve.

<!-- operational-state:entry
{
  "authority": "Explicit user-approved hybrid strategy",
  "evidence": "Canonical GitHub repository and hybrid decision record",
  "id": "INV-001",
  "last_checked": "2026-08-09",
  "recheck_trigger": "Any migration, packaging, or default-route change",
  "rule": "The additive Instrument Alpha web application must not overwrite or silently redefine the verified root Rhetorical_InDEX.html Experience Prototype.",
  "scope": "Hybrid migration and scanner parity",
  "state": "requested",
  "status": "active",
  "title": "Golden Experience Prototype remains intact",
  "validation_method": "Apply the release overlay only to new paths and verify no existing root canonical file is staged for replacement."
}
-->
### INV-001 — Golden Experience Prototype remains intact

- **State:** `requested`
- **Authority:** Explicit user-approved hybrid strategy
- **Evidence:** Canonical GitHub repository and hybrid decision record
- **Last Checked:** 2026-08-09
- **Recheck Trigger:** Any migration, packaging, or default-route change
- **Rule:** The additive Instrument Alpha web application must not overwrite or silently redefine the verified root Rhetorical_InDEX.html Experience Prototype.
- **Scope:** Hybrid migration and scanner parity
- **Status:** active
- **Validation Method:** Apply the release overlay only to new paths and verify no existing root canonical file is staged for replacement.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "authority": "Canonical implementation plan",
  "evidence": "Shared contracts and Chromium runtime inspection",
  "id": "INV-002",
  "last_checked": "2026-08-09",
  "recheck_trigger": "Finding schema, profile, scoring, or summary changes",
  "rule": "Interpretive pressure P1-P4 and confidence Low/Medium/High remain separate data and visual dimensions; no master bias, trust, truth, propaganda, or harm score is introduced.",
  "scope": "Instrument Alpha findings and profile UI",
  "state": "verified",
  "status": "active",
  "title": "Pressure and confidence remain independent",
  "validation_method": "Inspect finding cards/drawer/profile and schema fields."
}
-->
### INV-002 — Pressure and confidence remain independent

- **State:** `verified`
- **Authority:** Canonical implementation plan
- **Evidence:** Shared contracts and Chromium runtime inspection
- **Last Checked:** 2026-08-09
- **Recheck Trigger:** Finding schema, profile, scoring, or summary changes
- **Rule:** Interpretive pressure P1-P4 and confidence Low/Medium/High remain separate data and visual dimensions; no master bias, trust, truth, propaganda, or harm score is introduced.
- **Scope:** Instrument Alpha findings and profile UI
- **Status:** active
- **Validation Method:** Inspect finding cards/drawer/profile and schema fields.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "authority": "Canonical product contract",
  "evidence": "Runtime check: local preview produces candidates and Compare is unavailable",
  "id": "INV-003",
  "last_checked": "2026-08-09",
  "recheck_trigger": "Detector, Compare, Event, or live-ingestion changes",
  "rule": "Local pasted-text preview may emit only intrinsic candidates; Compare, Event Record, and Material Omission remain unavailable without a matching synthetic fixture or later real comparison infrastructure.",
  "scope": "Local preview and comparison gating",
  "state": "verified",
  "status": "active",
  "title": "Single-document scans cannot invent cross-document claims",
  "validation_method": "Run local preview and attempt Compare/Event navigation."
}
-->
### INV-003 — Single-document scans cannot invent cross-document claims

- **State:** `verified`
- **Authority:** Canonical product contract
- **Evidence:** Runtime check: local preview produces candidates and Compare is unavailable
- **Last Checked:** 2026-08-09
- **Recheck Trigger:** Detector, Compare, Event, or live-ingestion changes
- **Rule:** Local pasted-text preview may emit only intrinsic candidates; Compare, Event Record, and Material Omission remain unavailable without a matching synthetic fixture or later real comparison infrastructure.
- **Scope:** Local preview and comparison gating
- **Status:** active
- **Validation Method:** Run local preview and attempt Compare/Event navigation.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "authority": "Independent repository review, finding F-001",
  "evidence": "packages/schema/src/localPreviewContract.ts; tests/local-preview-contract.test.mjs cross-checks every localPreviewFindings output against the real services/api/detector_contract.py",
  "id": "INV-005",
  "last_checked": "2026-08-09",
  "recheck_trigger": "Any change to localPreviewFindings, localPreviewContract.ts, detector_contract.py, or the canonical vocabulary in packages/schema/schema.json",
  "rule": "The Level 2 Local Preview detector (apps/web/src/app.ts) must validate every candidate against the same semantic invariants represented by services/api/detector_contract.py before it enters application state. Invalid candidates are rejected, not silently repaired.",
  "scope": "Local Preview candidate generation",
  "state": "verified",
  "status": "active",
  "title": "Local Preview output is validated against the same contract as the future Instrument Alpha detector"
}
-->
### INV-005 — Local Preview output is validated against the same contract as the future Instrument Alpha detector

- **State:** `verified`
- **Authority:** Independent repository review, finding F-001
- **Evidence:** `packages/schema/src/localPreviewContract.ts`; `tests/local-preview-contract.test.mjs` cross-checks every `localPreviewFindings` output against the real `services/api/detector_contract.py`
- **Last Checked:** 2026-08-09
- **Recheck Trigger:** Any change to `localPreviewFindings`, `localPreviewContract.ts`, `detector_contract.py`, or the canonical vocabulary in `packages/schema/schema.json`
- **Rule:** The Level 2 Local Preview detector (`apps/web/src/app.ts`) must validate every candidate against the same semantic invariants represented by `services/api/detector_contract.py` before it enters application state. Invalid candidates are rejected, not silently repaired.
- **Scope:** Local Preview candidate generation
- **Status:** active
- **Validation Method:** `npm test` runs `tests/local-preview-contract.test.mjs`, which executes the real compiled `localPreviewFindings` and feeds its output through the real Python validator.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "authority": "Canonical implementation plan and verified prototype behavior",
  "evidence": "59/59 Chromium suite; one semantic article; overlay aria-hidden; geometry delta=0.00 across four viewports",
  "id": "INV-004",
  "last_checked": "2026-08-09",
  "recheck_trigger": "Article rendering, typography, annotation, Lens, or responsive changes",
  "rule": "Scanner uses one semantic article DOM; the Lens visualization is aria-hidden and geometrically aligned without changing canonical text flow.",
  "scope": "Scanner rendering and accessibility",
  "state": "verified",
  "status": "active",
  "title": "One accessible article with non-semantic Lens overlay",
  "validation_method": "Runtime DOM count, accessibility attributes, and base/overlay geometry comparison."
}
-->
### INV-004 — One accessible article with non-semantic Lens overlay

- **State:** `verified`
- **Authority:** Canonical implementation plan and verified prototype behavior
- **Evidence:** 59/59 Chromium suite; one semantic article; overlay aria-hidden; geometry delta=0.00 across four viewports
- **Last Checked:** 2026-08-09
- **Recheck Trigger:** Article rendering, typography, annotation, Lens, or responsive changes
- **Rule:** Scanner uses one semantic article DOM; the Lens visualization is aria-hidden and geometrically aligned without changing canonical text flow.
- **Scope:** Scanner rendering and accessibility
- **Status:** active
- **Validation Method:** Runtime DOM count, accessibility attributes, and base/overlay geometry comparison.
<!-- /operational-state:entry -->

**Note on artifact identity (updated 2026-08-09, Instrument Alpha completion pass):** the current baseline hash is `1a5ebc36…`. It supersedes `4b2652f6…`, which itself superseded the `8b3086f5...` hash referenced by `VER-001` through `VER-004` below. The rebuild that produced the new hash added Local Preview candidate validation (`INV-005`) and a taxonomy typo fix; it did not touch DOM structure, element IDs, CSS, or scanner/Lens/drawer logic. `VER-001`–`VER-004`'s Chromium evidence has NOT been re-collected against either newer artifact — Playwright/Chromium is unavailable in this environment — so all four are now marked `freshness: stale`. Their `state: verified` reflects what was true for artifact `8b3086f5…` and must NOT be read as a current claim about `1a5ebc36…`. Re-run `npm run qa:runtime` to restore them. See `tests/prototype-parity/PARITY_MATRIX.md` for the current, honest per-behavior status (11 PASS / 0 FAIL / 21 UNVERIFIED).

## 5. Verified Working Behavior

Add stable `VER-###` entries only when evidence proves the required behavior through an appropriate path.

<!-- operational-state:entry
{
  "artifact_revision": "apps/web/dist/index.html sha256 8b3086f56998b9f74a3533de8db93195ab2cb308bca6d715d15842b1f3d61a3a",
  "capability": "Article-first scanner supports exact spatial Lens reveal, Reveal All, radius-aware bounds, touch drag, pointer cancellation, and responsive layouts.",
  "dependencies": "Chromium and embedded fixture/taxonomy only; no runtime network dependency",
  "evidence": "qa/runtime-results.json: 59/59 pass; screenshots in qa/screens",
  "freshness": "stale",
  "id": "VER-001",
  "last_verified": "2026-08-09T19:00:00Z",
  "recheck_trigger": "Scanner, CSS, Lens, pointer, typography, or responsive changes",
  "scope": "Desktop, 768x1024 tablet portrait, 1024x768 tablet landscape, 410x844 phone",
  "state": "verified",
  "title": "Scanner Lens parity path works in tested Chromium viewports",
  "verification_method": "Automated Chromium runtime suite with exact built standalone HTML"
}
-->
### VER-001 — Scanner Lens parity path works in tested Chromium viewports

- **State:** `verified`
- **Artifact Revision:** apps/web/dist/index.html sha256 8b3086f56998b9f74a3533de8db93195ab2cb308bca6d715d15842b1f3d61a3a
- **Capability:** Article-first scanner supports exact spatial Lens reveal, Reveal All, radius-aware bounds, touch drag, pointer cancellation, and responsive layouts.
- **Dependencies:** Chromium and embedded fixture/taxonomy only; no runtime network dependency
- **Evidence:** qa/runtime-results.json: 59/59 pass; screenshots in qa/screens
- **Freshness:** stale — evidence predates artifact 1a5ebc36…; not re-collected
- **Last Verified:** 2026-08-09T19:00:00Z
- **Recheck Trigger:** Scanner, CSS, Lens, pointer, typography, or responsive changes
- **Scope:** Desktop, 768x1024 tablet portrait, 1024x768 tablet landscape, 410x844 phone
- **Verification Method:** Automated Chromium runtime suite with exact built standalone HTML
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "artifact_revision": "apps/web/dist/index.html sha256 8b3086f56998b9f74a3533de8db93195ab2cb308bca6d715d15842b1f3d61a3a",
  "capability": "Finding drawer traps focus, closes with Escape/controls, restores focus, and supports Reduced Motion and Pattern Mode.",
  "dependencies": "Browser focus behavior",
  "evidence": "qa/runtime-results.json includes repeated focus-trap checks, focus restoration, Reduced Motion, and Pattern Mode",
  "freshness": "stale",
  "id": "VER-002",
  "last_verified": "2026-08-09T19:00:00Z",
  "recheck_trigger": "Drawer, keyboard, focus, motion, or accessibility changes",
  "scope": "Scanner finding inspection",
  "state": "verified",
  "title": "Finding inspection accessibility path works in tested Chromium",
  "verification_method": "Automated Chromium keyboard/focus/runtime checks"
}
-->
### VER-002 — Finding inspection accessibility path works in tested Chromium

- **State:** `verified`
- **Artifact Revision:** apps/web/dist/index.html sha256 8b3086f56998b9f74a3533de8db93195ab2cb308bca6d715d15842b1f3d61a3a
- **Capability:** Finding drawer traps focus, closes with Escape/controls, restores focus, and supports Reduced Motion and Pattern Mode.
- **Dependencies:** Browser focus behavior
- **Evidence:** qa/runtime-results.json includes repeated focus-trap checks, focus restoration, Reduced Motion, and Pattern Mode
- **Freshness:** stale — evidence predates artifact 1a5ebc36…; not re-collected
- **Last Verified:** 2026-08-09T19:00:00Z
- **Recheck Trigger:** Drawer, keyboard, focus, motion, or accessibility changes
- **Scope:** Scanner finding inspection
- **Verification Method:** Automated Chromium keyboard/focus/runtime checks
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "artifact_revision": "taxonomy sha256 7e091832494fbcdd904f1699686e230a1dbddfeafec3c6dd5cc9888547be0c01; fixture sha256 a167d7b37711f9dc2f7f90fbc289289ef9dfc7081cb0aa5b706d36d9f0a1577a",
  "capability": "Twelve Alpha-0 taxonomy records, exact fixture spans, one-mechanism Finding contract, and strict future detector boundary are internally consistent.",
  "dependencies": "Node.js and Python standard library for tests",
  "evidence": "11/11 Node tests and 5/5 Python tests passed",
  "freshness": "stale",
  "id": "VER-003",
  "last_verified": "2026-08-09T19:00:00Z",
  "recheck_trigger": "Schema, taxonomy, fixture, or detector-contract changes",
  "scope": "packages/schema, packages/taxonomy, packages/fixtures, services/api/detector_contract.py",
  "state": "verified",
  "title": "Shared taxonomy and fixture contracts pass deterministic checks",
  "verification_method": "Node contract tests plus Python unittest suite"
}
-->
### VER-003 — Shared taxonomy and fixture contracts pass deterministic checks

- **State:** `verified`
- **Artifact Revision:** taxonomy sha256 7e091832494fbcdd904f1699686e230a1dbddfeafec3c6dd5cc9888547be0c01; fixture sha256 a167d7b37711f9dc2f7f90fbc289289ef9dfc7081cb0aa5b706d36d9f0a1577a
- **Capability:** Twelve Alpha-0 taxonomy records, exact fixture spans, one-mechanism Finding contract, and strict future detector boundary are internally consistent.
- **Dependencies:** Node.js and Python standard library for tests
- **Evidence:** 11/11 Node tests and 5/5 Python tests passed
- **Freshness:** stale — evidence predates artifact 1a5ebc36…; not re-collected
- **Last Verified:** 2026-08-09T19:00:00Z
- **Recheck Trigger:** Schema, taxonomy, fixture, or detector-contract changes
- **Scope:** packages/schema, packages/taxonomy, packages/fixtures, services/api/detector_contract.py
- **Verification Method:** Node contract tests plus Python unittest suite
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "artifact_revision": "apps/web/dist/index.html sha256 8b3086f56998b9f74a3533de8db93195ab2cb308bca6d715d15842b1f3d61a3a",
  "capability": "The built Instrument Alpha web artifact runs without external network requests in the tested journeys and produced no console errors.",
  "dependencies": "Embedded data only",
  "evidence": "qa/runtime-results.json reports no external requests and no console errors for all four tested viewport groups",
  "freshness": "stale",
  "id": "VER-004",
  "last_verified": "2026-08-09T19:00:00Z",
  "recheck_trigger": "Any dependency, network, build, or runtime integration change",
  "scope": "Standalone built web artifact",
  "state": "verified",
  "title": "Runtime remains offline and free of observed console failures",
  "verification_method": "Chromium request and console instrumentation"
}
-->
### VER-004 — Runtime remains offline and free of observed console failures

- **State:** `verified`
- **Artifact Revision:** apps/web/dist/index.html sha256 8b3086f56998b9f74a3533de8db93195ab2cb308bca6d715d15842b1f3d61a3a
- **Capability:** The built Instrument Alpha web artifact runs without external network requests in the tested journeys and produced no console errors.
- **Dependencies:** Embedded data only
- **Evidence:** qa/runtime-results.json reports no external requests and no console errors for all four tested viewport groups
- **Freshness:** stale — evidence predates artifact 1a5ebc36…; not re-collected
- **Last Verified:** 2026-08-09T19:00:00Z
- **Recheck Trigger:** Any dependency, network, build, or runtime integration change
- **Scope:** Standalone built web artifact
- **Verification Method:** Chromium request and console instrumentation
<!-- /operational-state:entry -->

## 6. Known Not Working

Add stable `BRK-###` entries for confirmed failures. Keep them until repair evidence exists.

## 7. Implemented but Unverified

Add stable `UNV-###` entries for code, files, configuration, or artifact features that exist but are not proven through the required user journey.

## 8. Unknown or Evidence-Stale State

Add stable `UNK-###` entries for missing, conflicting, inaccessible, stale, or invalidated evidence.

<!-- operational-state:entry
{
  "decisive_check": "Run equivalent scanner/focus/touch suite in Safari/iPadOS and Firefox and conduct a real screen-reader session.",
  "evidence": "Current environment validated Chromium only",
  "id": "UNK-001",
  "state": "unknown",
  "title": "Cross-browser and assistive-technology coverage"
}
-->
### UNK-001 — Cross-browser and assistive-technology coverage

- **State:** `unknown`
- **Decisive Check:** Run equivalent scanner/focus/touch suite in Safari/iPadOS and Firefox and conduct a real screen-reader session.
- **Evidence:** Current environment validated Chromium only
<!-- /operational-state:entry -->

## 9. Pending Work

Add stable `PND-###` entries for intentionally incomplete work. Pending does not automatically mean failed.

<!-- operational-state:entry
{
  "blocks_completion": false,
  "dependency": "Reviewed taxonomy contract, provenance/run schema, and a human-reviewed benchmark corpus",
  "id": "PND-001",
  "priority": "next",
  "reason_pending": "This release intentionally establishes the verified hybrid foundation, including a heuristic Level 2 Local Preview detector, before calibrated Level 3 production inference.",
  "state": "pending",
  "task": "Replace or augment the current heuristic Level 2 Local Preview detector (apps/web/src/app.ts, present since this release) with the first calibrated Level 3 four-mechanism Instrument Alpha detector behind services/api/detector_contract.py, then build the human-reviewed benchmark around the functioning detector.",
  "title": "Calibrated Level 3 Instrument Alpha detector",
  "validation_needed": "Stable exact spans, structured criteria/exclusions, pressure/confidence, voice provenance, no cross-document assertions, and per-mechanism benchmark evidence against a human-reviewed corpus."
}
-->
### PND-001 — Calibrated Level 3 Instrument Alpha detector

- **State:** `pending`
- **Blocks Completion:** No
- **Dependency:** Reviewed taxonomy contract, provenance/run schema, and a human-reviewed benchmark corpus
- **Priority:** next
- **Reason Pending:** This release intentionally establishes the verified hybrid foundation, including a heuristic Level 2 Local Preview detector, before calibrated Level 3 production inference.
- **Task:** Replace or augment the current heuristic Level 2 Local Preview detector (`apps/web/src/app.ts`, present since this release) with the first calibrated Level 3 four-mechanism Instrument Alpha detector behind `services/api/detector_contract.py`, then build the human-reviewed benchmark around the functioning detector.
- **Validation Needed:** Stable exact spans, structured criteria/exclusions, pressure/confidence, voice provenance, no cross-document assertions, and per-mechanism benchmark evidence against a human-reviewed corpus.

**Note (independent review, finding F-001):** an earlier revision of this entry described the four-mechanism heuristic detector itself as pending. That was inaccurate — the Level 2 Local Preview detector already existed in `apps/web/src/app.ts` at the time. Only the calibrated Level 3 detector is pending. See `INV-005` for the validation boundary now in place around the existing Level 2 detector.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "blocks_completion": false,
  "dependency": "PND-001",
  "id": "PND-002",
  "priority": "after detector",
  "reason_pending": "Canonical build sequence requires detector before benchmark.",
  "state": "pending",
  "task": "Create and adjudicate the first benchmark only after the calibrated Level 3 four-mechanism detector vertical slice exists (not the heuristic Level 2 Local Preview detector, which is intentionally unbenchmarked).",
  "title": "First human-reviewed detector benchmark",
  "validation_needed": "Per-mechanism precision, recall, span accuracy, pressure agreement, calibration, and error classes."
}
-->
### PND-002 — First human-reviewed detector benchmark

- **State:** `pending`
- **Blocks Completion:** No
- **Dependency:** PND-001
- **Priority:** after detector
- **Reason Pending:** Canonical build sequence requires detector before benchmark.
- **Task:** Create and adjudicate the first benchmark only after the calibrated Level 3 four-mechanism detector vertical slice exists (not the heuristic Level 2 Local Preview detector, which is intentionally unbenchmarked).
- **Validation Needed:** Per-mechanism precision, recall, span accuracy, pressure agreement, calibration, and error classes.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "blocks_completion": false,
  "dependency": "Instrument Alpha detector and benchmark",
  "id": "PND-003",
  "priority": "later",
  "reason_pending": "Canonical roadmap places URL ingestion after Instrument Alpha; current AI Studio server/SSRF experiment was rejected from the hybrid.",
  "state": "pending",
  "task": "Build URL ingestion, source registry, comparison/evidence infrastructure only after Instrument Alpha credibility gates are met.",
  "title": "Safe URL ingestion and news-scale infrastructure",
  "validation_needed": "Production network-security, extraction, rights, source-dependence, and chronology gates."
}
-->
### PND-003 — Safe URL ingestion and news-scale infrastructure

- **State:** `pending`
- **Blocks Completion:** No
- **Dependency:** Instrument Alpha detector and benchmark
- **Priority:** later
- **Reason Pending:** Canonical roadmap places URL ingestion after Instrument Alpha; current AI Studio server/SSRF experiment was rejected from the hybrid.
- **Task:** Build URL ingestion, source registry, comparison/evidence infrastructure only after Instrument Alpha credibility gates are met.
- **Validation Needed:** Production network-security, extraction, rights, source-dependence, and chronology gates.
<!-- /operational-state:entry -->

## 10. Active Decisions, Defaults, and Prohibitions

Add stable `DEC-###` entries for source locks, routes, naming, packaging, style, rejected approaches, environment limits, and explicit supersessions.

<!-- operational-state:entry
{
  "decision": "GitHub repository governs; the root standalone prototype defines verified behavior; donor AI Studio modules accelerate the new implementation; the canonical implementation plan defines the target architecture.",
  "id": "DEC-001",
  "state": "requested",
  "status": "active",
  "title": "Verified Hybrid Migration authority model"
}
-->
### DEC-001 — Verified Hybrid Migration authority model

- **State:** `requested`
- **Decision:** GitHub repository governs; the root standalone prototype defines verified behavior; donor AI Studio modules accelerate the new implementation; the canonical implementation plan defines the target architecture.
- **Status:** active
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "decision": "Do not import the AI Studio Express/Gemini server or URL fetcher. Local preview remains offline and explicitly unbenchmarked; live URL ingestion is deferred.",
  "id": "DEC-002",
  "state": "requested",
  "status": "active",
  "title": "No live URL ingestion in this Alpha foundation"
}
-->
### DEC-002 — No live URL ingestion in this Alpha foundation

- **State:** `requested`
- **Decision:** Do not import the AI Studio Express/Gemini server or URL fetcher. Local preview remains offline and explicitly unbenchmarked; live URL ingestion is deferred.
- **Status:** active
<!-- /operational-state:entry -->

## 11. Validation and Evidence Matrix

| ID | Claim or behavior | State | Evidence | Validation method | Artifact/revision | Last checked | Recheck trigger |
|---|---|---|---|---|---|---|---|

## 12. Current Change Scope and Impact Radius

- **Allowed to change:** `apps/web`, additive `packages`, `services/api` detector contract, `tests`, `tools`, migration/QA documentation, and release metadata.
- **Must remain unchanged:** Existing root `Rhetorical_InDEX.html`, canonical implementation plan, and other pre-existing repository files when this overlay is applied.
- **Potentially affected behavior:** New Instrument Alpha scanner, fixture Compare/Event views, shared contracts, and future detector boundary only.
- **Mandatory checks:** TypeScript typecheck/build, deterministic Node/Python tests, Chromium desktop/tablet/phone runtime parity, console/network inspection, archive integrity.
- **Checks deliberately reused:** Root Experience Prototype QA remains historical evidence and is not falsely re-run by this subsystem.
- **Repair class:** Additive hybrid migration foundation.

## 13. Compact Revision Log

### Revision 1 — 2026-08-09T19:15:09Z

- **Artifact/source identity:** `Not yet established`
- **State deltas:** Initialized operational state.
- **New evidence:** None.
- **Validation not performed:** All behavioral validation remains pending unless explicitly recorded above.

### Revision 2 — 2026-08-09T19:17:09Z

- **Artifact/source identity:** apps/web/dist/index.html sha256 8b3086f56998b9f74a3533de8db93195ab2cb308bca6d715d15842b1f3d61a3a
- **State deltas:** Updated metadata: project_root, artifact_path, current_baseline, scope_boundaries; Added INV-001 to 4. Active Invariants; Added INV-002 to 4. Active Invariants; Added INV-003 to 4. Active Invariants; Added INV-004 to 4. Active Invariants; Added VER-001 to 5. Verified Working Behavior; Added VER-002 to 5. Verified Working Behavior; Added VER-003 to 5. Verified Working Behavior; Added VER-004 to 5. Verified Working Behavior; Added UNK-001 to 8. Unknown or Evidence-Stale State; Added PND-001 to 9. Pending Work; Added PND-002 to 9. Pending Work; Added PND-003 to 9. Pending Work; Added DEC-001 to 10. Active Decisions, Defaults, and Prohibitions; Added DEC-002 to 10. Active Decisions, Defaults, and Prohibitions
- **New evidence:** 11/11 Node contract tests passed; 5/5 Python detector-contract tests passed; 59/59 Chromium runtime checks passed; Base and Lens overlay geometry measured delta=0.00 on desktop, tablet portrait, tablet landscape, and phone; No external runtime requests or console errors observed in tested Chromium paths
- **Newly verified behavior:** INV-002; INV-003; INV-004; VER-001; VER-002; VER-003; VER-004
- **Newly known failure:** None.
- **Superseded rule:** None.
- **Validation not performed:** Safari/iPadOS runtime; Firefox runtime; Real screen-reader session
- **Reason for broad revalidation:** New additive Instrument Alpha frontend and shared contracts were created beside the verified Experience Prototype.
- **Summary:** Record verified hybrid Instrument Alpha web baseline and protected migration boundaries

### Revision 3 — 2026-08-09T20:00:00Z

- **Artifact/source identity:** apps/web/dist/index.html sha256 4b2652f6d4985454bf2b6236d622ad32ce3fa3c34c20124037201f70291879b9
- **State deltas:** Updated metadata (`current_baseline`, `last_updated`, `state_revision`); added `INV-005`; rewrote `PND-001` and `PND-002` to accurately distinguish the already-implemented heuristic Level 2 Local Preview detector from the not-yet-implemented calibrated Level 3 Instrument Alpha detector; added artifact-identity note ahead of section 5.
- **New evidence:** Independent repository review closure of findings F-001–F-004 (see `HYBRID_QA_REPORT.md` "Cleanup pass" section and `HYBRID_REQUIREMENT_TRACEABILITY.md` closure table). TypeScript typecheck PASS; build PASS and reproducible (rebuilt twice, identical hash); 20/20 Node tests PASS; 8/8 Python tests PASS; 11/11 hand-constructed adversarial candidates against the TS validator correctly rejected with 1/1 positive control correctly accepted; injected vocabulary drift correctly caught by both new parity tests, then reverted.
- **Newly verified behavior:** INV-005.
- **Newly known failure:** None.
- **Superseded rule:** None — `PND-001`/`PND-002` reworded for accuracy, not for a rule change.
- **Validation not performed:** Chromium/Playwright runtime QA was not re-executed against the new artifact hash in this pass (environment has no Playwright/Chromium); Safari/iPadOS, Firefox, and real screen-reader sessions remain unverified, unchanged from Revision 2.
- **Reason for broad revalidation:** Independent review findings F-001 (detector-level documentation mismatch + missing Local Preview validation boundary), F-002 (no TS/Python vocabulary parity check), F-003 (presence tests read as behavioral proof), and F-004 (taxonomy typo).
- **Summary:** Close independent review findings F-001–F-004: formalize the three detector levels, validate Local Preview output against the same contract as the future Instrument Alpha detector, add automated vocabulary parity, clarify structural-guard test semantics, and fix the taxonomy typo.

### Revision 4 — 2026-08-09T21:30:00Z — Instrument Alpha completion program

- **Artifact/source identity:** `apps/web/dist/index.html` sha256 `1a5ebc364fb0f53ac8845b1b7e9ddeac202a13f0020ac0458e263e7bef267812`
- **Scope of change:** additive. A Level 3 detector (`services/rhetoric`), comparison/omission gates (`services/comparison`), evidence architecture (`services/evidence`), a local analysis boundary + CLI (`services/api/analyze.py`), and benchmark machinery (`benchmarks/`) were added beside the existing Level 2 browser scanner. The only change to `apps/web` is a text-only transparency block appended to the Methodology view.
- **New evidence:** 29/29 Node tests PASS; 160/160 Python tests PASS; typecheck PASS; build PASS and reproducible (two clean builds, identical hash); adversarial mutation testing confirmed the suite detects removal of the criteria-fabrication guard, the uncertainty cap, the nested-span collapse and cross-language vocabulary drift.
- **Newly verified behavior:** see `INSTRUMENT_ALPHA_TRACEABILITY.md` — 106 PASS rows.
- **Newly known failure:** None. Six defects were found by adversarial review and all six are fixed with regression tests (`docs/ADVERSARIAL_REVIEW.md`, D-001 … D-006).
- **Superseded rule:** None.
- **Validation NOT performed:** Chromium/Playwright runtime QA was **not executed** in this pass (Playwright unavailable on this host). All browser-runtime, responsive, touch and focus-management rows remain **UNVERIFIED** — see `tests/prototype-parity/PARITY_MATRIX.md` (11 PASS / 0 FAIL / 21 UNVERIFIED). `qa/runtime-results.json` and `qa/screens/*.png` are **stale**: produced against artifact `8b3086f5…`, superseded by `1a5ebc36…`. They are retained as historical evidence only.
- **Calibration status:** **UNCALIBRATED.** `benchmarks/corpus/` contains zero adjudicated documents; `benchmarks/scripts/evaluate.py` reports `EMPTY`. No accuracy figure exists for any detector level and none is stated anywhere.
- **Summary:** Build the Level 3 Instrument Alpha detector pipeline, comparison/evidence architecture and benchmark machinery beside the verified prototype, with strict validation, coverage honesty and adversarial regression coverage.

### Revision 5 — 2026-08-09T22:30:00Z — Independent pre-merge review closure

- **Artifact/source identity:** `apps/web/dist/index.html` sha256 `1a5ebc364fb0f53ac8845b1b7e9ddeac202a13f0020ac0458e263e7bef267812` (unchanged — this pass touched no web source).
- **Scope of change:** `services/comparison/` (new `divergence.py`; `claims.py`, `omission.py`), `services/rhetoric/` (`candidates.py`, `document.py`, `voice.py`, `providers.py`), `tools/check_traceability.py`, tests and QA documentation. No web/UI change, no new features, no new mechanisms, no networking.
- **New evidence:** typecheck PASS; build PASS and reproducible (two clean builds, identical hash); **29/29 Node**; **207/207 Python** (was 160); benchmark still reports `EMPTY`; `tools/check_traceability.py` PASS on both QA matrices. Ten mutations — including allowing `compatible` to ground an omission, disabling the divergence gate, and reinstating tier-derived certainty — each produced test failures and were reverted.
- **Newly verified behavior:** `Z-01` … `Z-34` (see `INSTRUMENT_ALPHA_TRACEABILITY.md`).
- **Newly known failure:** None. The Major blocker M-01 is closed: contradictory peer claims can no longer establish presence for a Material Omission, and no source can be credited with a proposition it did not assert.
- **Superseded rule:** `is_usable_for_omission` narrowed to `same_proposition` only (was `{same_proposition, compatible, more_specific, less_specific}`). Deliberately conservative; rationale recorded in `KNOWN_LIMITATIONS.md`.
- **Validation NOT performed:** Chromium/Playwright runtime QA — Playwright remains unavailable on this host. Prototype parity is now **9 PASS / 0 FAIL / 23 UNVERIFIED** after removing dual-status rows that had been counted as PASS on structural presence. `qa/runtime-results.json` and `qa/screens/*.png` remain **stale**.
- **Calibration status:** **UNCALIBRATED**, unchanged. `benchmarks/corpus/` holds zero adjudicated documents.
- **Summary:** Close the independent pre-merge review — add deterministic factual-divergence guards so unresolved contradiction can never become evidentiary support, narrow Material Omission eligibility, decouple confidence from rhetorical pressure, and machine-verify every QA total.

### Revision 6 — 2026-08-09T23:59:00Z — Pre-calibration hardening

- **Artifact/source identity:** `apps/web/dist/index.html` sha256 `f38639156e1bbcdb4f113dfcd442a47d00ae6a00f70672d915aa5352ae55b275`
- **Taxonomy version:** bumped `1.0.0-alpha0` → **`1.1.0-alpha0`** (semantic change: quoted speech is no longer an exclusion for loaded language — rhetoric inside a quotation is still rhetoric, and `voiceClass` records whose it is). Propagated to fixtures, benchmark schema/example, annotation guide, tests and the built artifact.
- **Scope of change:** `services/comparison/` (new `divergence.canonical_proposition` identity gate, tri-state independence, comparison-set membership, timezone-aware chronology), `services/rhetoric/` (uncertain-verdict state, taxonomy-criteria membership, strict model parsing, rubric-aligned pressure, candidate-local exclusions, failure attribution, run/article identity), `services/evidence/` (relation-confidence caps, distinct-item corroboration), `benchmarks/` (corpus validator, optimal matching, protocol and schema), `apps/web/src/app.ts` (voice classification, agent-suppression parity, zero-finding peak), `tools/runtime_qa.py` (portability).
- **New evidence:** typecheck PASS; build PASS and reproducible; **29 → 39 Node tests**; **207 → 289 Python tests**; corpus validator PASS; benchmark still `EMPTY`; traceability PASS (machine-verified). Twelve guard mutations each produced failures and were reverted.
- **Newly known failure:** None. All 26 audit findings are closed with executed evidence.
- **Validation NOT performed:** Chromium/Playwright runtime QA — Playwright is not installed on this host. `npm run qa:runtime` now exits 2 with install instructions instead of silently using a Linux-only path. Prototype parity remains **9 PASS / 0 FAIL / 23 UNVERIFIED**; `qa/runtime-results.json` and `qa/screens/*.png` remain **stale**.
- **Calibration status:** **UNCALIBRATED**, unchanged. `benchmarks/corpus/` holds zero adjudicated documents and is now machine-guarded against malformed gold.
- **Summary:** Harden every epistemic boundary before human calibration begins — most importantly, stop treating absence of detected contradiction as evidence of propositional agreement.
