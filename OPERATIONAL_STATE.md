# Operational State: Rhetorical InDEX

<!-- operational-state:metadata
{
  "artifact_path": "/mnt/data/rhetorical-index/Rhetorical_InDEX.html",
  "current_baseline": {
    "identity": "Rhetorical_InDEX.html sha256 bfe0020facf08cad391caa4dcca9a0428e765d8f0f4b5afeaac11f883c10dd18 + Rhetorical_InDEX_Implementation_Plan.md sha256 40dce003d1ba8525d2be8b1b24e8e72077bcedf77adc8599bfa6064042a75c57",
    "last_verified": "2026-08-09T10:40:00Z",
    "state": "current-baseline"
  },
  "last_updated": "2026-08-09T10:40:54Z",
  "linked_parent_state": null,
  "project_id": "rhetorical-index",
  "project_name": "Rhetorical InDEX",
  "project_root": "/mnt/data/rhetorical-index",
  "schema_version": 1,
  "scope_boundaries": [
    "Rhetorical InDEX MVP implementation plan",
    "Standalone offline HTML prototype",
    "Current release ZIP and QA evidence"
  ],
  "state_revision": 5
}
-->

## 1. Project Identity and Scope

- **Project ID:** `rhetorical-index`
- **Purpose:** Preserve current operational truth for Rhetorical InDEX.
- **Project type:** Unclassified durable artifact project.
- **Primary root or artifact:** `/mnt/data/rhetorical-index`
- **Target environment:** Unknown until established by project evidence.
- **Canonical authority:** Explicit user instruction and project-local evidence.
- **Governed scope:** Project rooted at /mnt/data/rhetorical-index
- **Explicitly not governed:** Unrelated projects and neighboring subsystems unless explicitly linked.

## 2. Current Baseline

- **Primary artifact:** `Not yet established`
- **Baseline state:** `unknown`
- **Source/build/install identity:** Unknown unless recorded below.
- **Active default user route:** Unknown unless recorded below.
- **Delivery state:** Unknown unless recorded below.
- **Last verified baseline:** Not yet established.

## 3. Artifact Contract

Record the literal deliverable shape, file count and type, dimensions, runtime behavior, user journey, dependencies, packaging, delivery, and prohibited substitutions.

## 4. Active Invariants

Add stable `INV-###` entries for rules future work must preserve.

<!-- operational-state:entry
{
  "authority": "Explicit user decision",
  "evidence": "Discovery walk decision",
  "id": "INV-001",
  "last_checked": "pre-build",
  "recheck_trigger": "Navigation or information-architecture changes",
  "rule": "The default user journey begins in an individual article scanner; comparison and event evidence are reachable from the article.",
  "scope": "MVP product and prototype",
  "state": "requested",
  "status": "active",
  "title": "Article-first entry",
  "validation_method": "Open prototype and confirm Scanner is the default view and Compare is directly reachable."
}
-->
### INV-001 — Article-first entry

- **State:** `requested`
- **Authority:** Explicit user decision
- **Evidence:** Discovery walk decision
- **Last Checked:** pre-build
- **Recheck Trigger:** Navigation or information-architecture changes
- **Rule:** The default user journey begins in an individual article scanner; comparison and event evidence are reachable from the article.
- **Scope:** MVP product and prototype
- **Status:** active
- **Validation Method:** Open prototype and confirm Scanner is the default view and Compare is directly reachable.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "authority": "Explicit user decision",
  "evidence": "Discovery walk decision",
  "id": "INV-002",
  "last_checked": "pre-build",
  "recheck_trigger": "Scoring, taxonomy, copy, or summary changes",
  "rule": "MVP severity describes strength of interpretive pressure, not political side, moral worth, or potential harm.",
  "scope": "Analysis model and UI language",
  "state": "requested",
  "status": "active",
  "title": "Interpretive pressure is the MVP analytical target",
  "validation_method": "Inspect plan, scanner labels, and prototype summaries for prohibited conflation with harm or ideology."
}
-->
### INV-002 — Interpretive pressure is the MVP analytical target

- **State:** `requested`
- **Authority:** Explicit user decision
- **Evidence:** Discovery walk decision
- **Last Checked:** pre-build
- **Recheck Trigger:** Scoring, taxonomy, copy, or summary changes
- **Rule:** MVP severity describes strength of interpretive pressure, not political side, moral worth, or potential harm.
- **Scope:** Analysis model and UI language
- **Status:** active
- **Validation Method:** Inspect plan, scanner labels, and prototype summaries for prohibited conflation with harm or ideology.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "authority": "Explicit user decision",
  "evidence": "Discovery walk decision",
  "id": "INV-003",
  "last_checked": "pre-build",
  "recheck_trigger": "Source metadata or comparison changes",
  "rule": "The core interface must not classify sources or findings by a Left/Center/Right axis.",
  "scope": "MVP information architecture and analysis",
  "state": "requested",
  "status": "active",
  "title": "No left-center-right default taxonomy",
  "validation_method": "Search plan and prototype UI for source-side scoring or left-center-right controls."
}
-->
### INV-003 — No left-center-right default taxonomy

- **State:** `requested`
- **Authority:** Explicit user decision
- **Evidence:** Discovery walk decision
- **Last Checked:** pre-build
- **Recheck Trigger:** Source metadata or comparison changes
- **Rule:** The core interface must not classify sources or findings by a Left/Center/Right axis.
- **Scope:** MVP information architecture and analysis
- **Status:** active
- **Validation Method:** Search plan and prototype UI for source-side scoring or left-center-right controls.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "authority": "Explicit user decision",
  "evidence": "Discovery walk decision",
  "id": "INV-004",
  "last_checked": "pre-build",
  "recheck_trigger": "Finding schema or visual encoding changes",
  "rule": "Rhetorical-force intensity and model confidence must be represented as different dimensions.",
  "scope": "Finding schema, scoring, and UI",
  "state": "requested",
  "status": "active",
  "title": "Confidence is separate from intensity",
  "validation_method": "Inspect finding schema and prototype tags for separate intensity and confidence indicators."
}
-->
### INV-004 — Confidence is separate from intensity

- **State:** `requested`
- **Authority:** Explicit user decision
- **Evidence:** Discovery walk decision
- **Last Checked:** pre-build
- **Recheck Trigger:** Finding schema or visual encoding changes
- **Rule:** Rhetorical-force intensity and model confidence must be represented as different dimensions.
- **Scope:** Finding schema, scoring, and UI
- **Status:** active
- **Validation Method:** Inspect finding schema and prototype tags for separate intensity and confidence indicators.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "authority": "Explicit user decision",
  "evidence": "Discovery walk decision",
  "id": "INV-005",
  "last_checked": "pre-build",
  "recheck_trigger": "Omission or comparison model changes",
  "rule": "Material omission must be evaluated relative to other coverage and evidence, not inferred from a single article alone.",
  "scope": "Comparison and fact/evidence analysis",
  "state": "requested",
  "status": "active",
  "title": "Comparison detects material omission",
  "validation_method": "Inspect plan and demo comparison for peer-relative omission evidence."
}
-->
### INV-005 — Comparison detects material omission

- **State:** `requested`
- **Authority:** Explicit user decision
- **Evidence:** Discovery walk decision
- **Last Checked:** pre-build
- **Recheck Trigger:** Omission or comparison model changes
- **Rule:** Material omission must be evaluated relative to other coverage and evidence, not inferred from a single article alone.
- **Scope:** Comparison and fact/evidence analysis
- **Status:** active
- **Validation Method:** Inspect plan and demo comparison for peer-relative omission evidence.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "authority": "Explicit user decision",
  "evidence": "Discovery walk decision",
  "id": "INV-006",
  "last_checked": "pre-build",
  "recheck_trigger": "Finding details, comparison, or evidence UI changes",
  "rule": "Every finding must be inspectable to exact text, mechanism definition, intensity, confidence, evidence or comparison basis, and competing interpretation where applicable.",
  "scope": "MVP output contract and UI",
  "state": "requested",
  "status": "active",
  "title": "Radical inspectability",
  "validation_method": "Use prototype detail drawer and plan schema to trace representative findings end to end."
}
-->
### INV-006 — Radical inspectability

- **State:** `requested`
- **Authority:** Explicit user decision
- **Evidence:** Discovery walk decision
- **Last Checked:** pre-build
- **Recheck Trigger:** Finding details, comparison, or evidence UI changes
- **Rule:** Every finding must be inspectable to exact text, mechanism definition, intensity, confidence, evidence or comparison basis, and competing interpretation where applicable.
- **Scope:** MVP output contract and UI
- **Status:** active
- **Validation Method:** Use prototype detail drawer and plan schema to trace representative findings end to end.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "authority": "Explicit user decision",
  "evidence": "Discovery walk decision",
  "id": "INV-007",
  "last_checked": "pre-build",
  "recheck_trigger": "Scanner rendering or mobile interaction changes",
  "rule": "Low-confidence and other findings remain available by default, while the article stays readable through a cursor or touch lens that reveals rhetorical color locally.",
  "scope": "Scanner interaction",
  "state": "requested",
  "status": "active",
  "title": "Lens limits visual overload",
  "validation_method": "Move lens through article and verify unscanned regions remain visually calm while findings appear inside the lens."
}
-->
### INV-007 — Lens limits visual overload

- **State:** `requested`
- **Authority:** Explicit user decision
- **Evidence:** Discovery walk decision
- **Last Checked:** pre-build
- **Recheck Trigger:** Scanner rendering or mobile interaction changes
- **Rule:** Low-confidence and other findings remain available by default, while the article stays readable through a cursor or touch lens that reveals rhetorical color locally.
- **Scope:** Scanner interaction
- **Status:** active
- **Validation Method:** Move lens through article and verify unscanned regions remain visually calm while findings appear inside the lens.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "authority": "Explicit user decision",
  "evidence": "Discovery walk decision",
  "id": "INV-008",
  "last_checked": "pre-build",
  "recheck_trigger": "Tag rendering or taxonomy changes",
  "rule": "A passage may carry all applicable taxonomy tags; the system must not force a single dominant mechanism.",
  "scope": "Finding model and lens tags",
  "state": "requested",
  "status": "active",
  "title": "Multiple mechanisms may coexist",
  "validation_method": "Verify at least one demo passage renders multiple simultaneous tags."
}
-->
### INV-008 — Multiple mechanisms may coexist

- **State:** `requested`
- **Authority:** Explicit user decision
- **Evidence:** Discovery walk decision
- **Last Checked:** pre-build
- **Recheck Trigger:** Tag rendering or taxonomy changes
- **Rule:** A passage may carry all applicable taxonomy tags; the system must not force a single dominant mechanism.
- **Scope:** Finding model and lens tags
- **Status:** active
- **Validation Method:** Verify at least one demo passage renders multiple simultaneous tags.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "authority": "Explicit user decision",
  "evidence": "Discovery walk decision",
  "id": "INV-009",
  "last_checked": "pre-build",
  "recheck_trigger": "Threshold, confidence, or filtering changes",
  "rule": "MVP detection should prefer surfacing plausible findings over silent false negatives; low-confidence findings remain visible and explicitly marked as uncertain.",
  "scope": "Detection thresholds and UI",
  "state": "requested",
  "status": "active",
  "title": "High-recall posture with visible uncertainty",
  "validation_method": "Inspect threshold plan and prototype confidence styling for tentative findings."
}
-->
### INV-009 — High-recall posture with visible uncertainty

- **State:** `requested`
- **Authority:** Explicit user decision
- **Evidence:** Discovery walk decision
- **Last Checked:** pre-build
- **Recheck Trigger:** Threshold, confidence, or filtering changes
- **Rule:** MVP detection should prefer surfacing plausible findings over silent false negatives; low-confidence findings remain visible and explicitly marked as uncertain.
- **Scope:** Detection thresholds and UI
- **Status:** active
- **Validation Method:** Inspect threshold plan and prototype confidence styling for tentative findings.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "authority": "Explicit user decision",
  "evidence": "Discovery walk decision",
  "id": "INV-010",
  "last_checked": "pre-build",
  "recheck_trigger": "Roadmap or model-scope changes",
  "rule": "Novel rhetorical-pattern discovery is deferred until the finite MVP taxonomy is detected accurately enough to serve as a calibrated base instrument.",
  "scope": "MVP analysis roadmap",
  "state": "requested",
  "status": "active",
  "title": "Taxonomy before novelty",
  "validation_method": "Confirm novel-pattern discovery is post-MVP and taxonomy implementation precedes it."
}
-->
### INV-010 — Taxonomy before novelty

- **State:** `requested`
- **Authority:** Explicit user decision
- **Evidence:** Discovery walk decision
- **Last Checked:** pre-build
- **Recheck Trigger:** Roadmap or model-scope changes
- **Rule:** Novel rhetorical-pattern discovery is deferred until the finite MVP taxonomy is detected accurately enough to serve as a calibrated base instrument.
- **Scope:** MVP analysis roadmap
- **Status:** active
- **Validation Method:** Confirm novel-pattern discovery is post-MVP and taxonomy implementation precedes it.
<!-- /operational-state:entry -->

## 5. Verified Working Behavior

Add stable `VER-###` entries only when evidence proves the required behavior through an appropriate path.

<!-- operational-state:entry
{
  "artifact_revision": "HTML sha256 1ecad10a4d540b7f8ffbaaee111e660e68a73ea0f57908f58c0fcede4195bdda",
  "blocks_completion": true,
  "capability": "The self-contained Rhetorical InDEX HTML prototype implements the approved article-first scanner, comparison-first results, forensic Event Record, taxonomy, local paste demonstration, embedded plan, and release QA packet.",
  "dependencies": "No external dependencies for the HTML artifact; browser required to open it",
  "dependency": "None beyond current artifact environment",
  "evidence": "43 runtime + 49 static + 11 pure-JS + 24 accessibility checks all passed; 12 confirmed bugs were repaired; initial archive passed unzip -t.",
  "freshness": "Current release",
  "id": "VER-001",
  "last_verified": "2026-08-09T05:19:00Z",
  "priority": "highest",
  "reason_pending": "Work has not yet been executed.",
  "recheck_trigger": "Any HTML/CSS/JavaScript, embedded-plan, responsive-layout, or packaging change",
  "scope": "Current Experience Prototype release packet",
  "state": "verified",
  "task": "Create initial plan, adversarially revise it, build offline prototype, perform UI/UX review, deterministic validation, bug sweep, final QA, and ZIP packaging.",
  "title": "Experience prototype and release packet validated",
  "validation_needed": "End-to-end scanner interaction, plan parity, offline operation, accessibility basics, archive integrity",
  "verification_method": "Chromium CDP journey tests, static/product QA, pure-JavaScript tests, accessibility/contrast checks, HTML/CSS validators, visual screenshot review, authorship audit, and ZIP integrity check"
}
-->
### VER-001 — Experience prototype and release packet validated

- **State:** `verified`
- **Artifact Revision:** HTML sha256 1ecad10a4d540b7f8ffbaaee111e660e68a73ea0f57908f58c0fcede4195bdda
- **Blocks Completion:** Yes
- **Capability:** The self-contained Rhetorical InDEX HTML prototype implements the approved article-first scanner, comparison-first results, forensic Event Record, taxonomy, local paste demonstration, embedded plan, and release QA packet.
- **Dependencies:** No external dependencies for the HTML artifact; browser required to open it
- **Dependency:** None beyond current artifact environment
- **Evidence:** 43 runtime + 49 static + 11 pure-JS + 24 accessibility checks all passed; 12 confirmed bugs were repaired; initial archive passed unzip -t.
- **Freshness:** Current release
- **Last Verified:** 2026-08-09T05:19:00Z
- **Priority:** highest
- **Reason Pending:** Work has not yet been executed.
- **Recheck Trigger:** Any HTML/CSS/JavaScript, embedded-plan, responsive-layout, or packaging change
- **Scope:** Current Experience Prototype release packet
- **Task:** Create initial plan, adversarially revise it, build offline prototype, perform UI/UX review, deterministic validation, bug sweep, final QA, and ZIP packaging.
- **Validation Needed:** End-to-end scanner interaction, plan parity, offline operation, accessibility basics, archive integrity
- **Verification Method:** Chromium CDP journey tests, static/product QA, pure-JavaScript tests, accessibility/contrast checks, HTML/CSS validators, visual screenshot review, authorship audit, and ZIP integrity check
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "artifact_revision": "Plan sha256 ee1762c59effb595d98666bcdb585210d5a2b08195ad362de5898b9e660716ac",
  "capability": "The external Markdown contains the full revised beginning-to-end implementation plan and the explicitly requested 25-problem, 25-fix, 25-polish adversarial review.",
  "dependencies": "None",
  "evidence": "External plan is 9,906 shell-counted words / 2,072 lines; static QA confirms all three adversarial sections contain exactly 25 numbered entries; embedded HTML plan contains all H1/H2 headings from the clean plan source.",
  "freshness": "Current release",
  "id": "VER-002",
  "last_verified": "2026-08-09T05:19:00Z",
  "recheck_trigger": "Any plan, taxonomy, scope, or product-invariant change",
  "scope": "Rhetorical_InDEX_Implementation_Plan.md",
  "state": "verified",
  "title": "Revised plan and adversarial review are complete",
  "verification_method": "Heading parity, word/count checks, numbered-section counts, and requirement traceability review"
}
-->
### VER-002 — Revised plan and adversarial review are complete

- **State:** `verified`
- **Artifact Revision:** Plan sha256 ee1762c59effb595d98666bcdb585210d5a2b08195ad362de5898b9e660716ac
- **Capability:** The external Markdown contains the full revised beginning-to-end implementation plan and the explicitly requested 25-problem, 25-fix, 25-polish adversarial review.
- **Dependencies:** None
- **Evidence:** External plan is 9,906 shell-counted words / 2,072 lines; static QA confirms all three adversarial sections contain exactly 25 numbered entries; embedded HTML plan contains all H1/H2 headings from the clean plan source.
- **Freshness:** Current release
- **Last Verified:** 2026-08-09T05:19:00Z
- **Recheck Trigger:** Any plan, taxonomy, scope, or product-invariant change
- **Scope:** Rhetorical_InDEX_Implementation_Plan.md
- **Verification Method:** Heading parity, word/count checks, numbered-section counts, and requirement traceability review
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "affected_user_path": "Article-first scanner on tablet/coarse-pointer devices",
  "artifact_revision": "Rhetorical_InDEX.html sha256 bfe0020facf08cad391caa4dcca9a0428e765d8f0f4b5afeaac11f883c10dd18",
  "capability": "The article-first lens supports coarse-pointer tap placement, drag-handle scanning, pin/reveal/radius controls, real touch scrolling, pointer cancellation, rotation clamping, and medium-width responsive layout.",
  "dependencies": "Current standalone HTML only",
  "evidence": "runtime_v02_results.json: 75/75 pass; v02 tablet screenshots; QA_REPORT.md BUG-013/016/017 closure",
  "freshness": "current release candidate",
  "id": "VER-003",
  "last_verified": "2026-08-09T10:40:00Z",
  "observed_failure": "The current scanner lens does not provide a reliable tablet/coarse-pointer interaction path; the dedicated touch handle is only exposed below the phone breakpoint while article pointer movement explicitly ignores touch input.",
  "recheck_trigger": "Any lens geometry, pointer lifecycle, responsive breakpoint, sticky header, touch dock, or article-layer change",
  "required_repair": "Provide a tablet/coarse-pointer lens control path, safe lens bounds, and responsive controls without breaking vertical reading/scrolling.",
  "required_validation": "Run direct tablet-sized coarse-pointer runtime tests for drag, tap/place, pin, reveal-all, scroll coexistence, orientation change, and overflow.",
  "scope": "Chromium emulation at 768x1024, live rotation to 1024x768, and 1366x1024 coarse-pointer path",
  "severity": "high",
  "state": "verified",
  "status": "active",
  "title": "Tablet and coarse-pointer lens path is reliable in tested Chromium targets",
  "verification_method": "CDP-emulated real touch events plus computed layout/state assertions",
  "workaround": "Reveal All can expose all annotations but does not preserve the intended lens interaction."
}
-->
### VER-003 — Tablet and coarse-pointer lens path is reliable in tested Chromium targets

- **State:** `verified`
- **Affected User Path:** Article-first scanner on tablet/coarse-pointer devices
- **Artifact Revision:** Rhetorical_InDEX.html sha256 bfe0020facf08cad391caa4dcca9a0428e765d8f0f4b5afeaac11f883c10dd18
- **Capability:** The article-first lens supports coarse-pointer tap placement, drag-handle scanning, pin/reveal/radius controls, real touch scrolling, pointer cancellation, rotation clamping, and medium-width responsive layout.
- **Dependencies:** Current standalone HTML only
- **Evidence:** runtime_v02_results.json: 75/75 pass; v02 tablet screenshots; QA_REPORT.md BUG-013/016/017 closure
- **Freshness:** current release candidate
- **Last Verified:** 2026-08-09T10:40:00Z
- **Observed Failure:** The current scanner lens does not provide a reliable tablet/coarse-pointer interaction path; the dedicated touch handle is only exposed below the phone breakpoint while article pointer movement explicitly ignores touch input.
- **Recheck Trigger:** Any lens geometry, pointer lifecycle, responsive breakpoint, sticky header, touch dock, or article-layer change
- **Required Repair:** Provide a tablet/coarse-pointer lens control path, safe lens bounds, and responsive controls without breaking vertical reading/scrolling.
- **Required Validation:** Run direct tablet-sized coarse-pointer runtime tests for drag, tap/place, pin, reveal-all, scroll coexistence, orientation change, and overflow.
- **Scope:** Chromium emulation at 768x1024, live rotation to 1024x768, and 1366x1024 coarse-pointer path
- **Severity:** high
- **Status:** active
- **Verification Method:** CDP-emulated real touch events plus computed layout/state assertions
- **Workaround:** Reveal All can expose all annotations but does not preserve the intended lens interaction.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "artifact_revision": "HTML bfe0020facf08cad391caa4dcca9a0428e765d8f0f4b5afeaac11f883c10dd18 / plan 40dce003d1ba8525d2be8b1b24e8e72077bcedf77adc8599bfa6064042a75c57",
  "blocks_completion": true,
  "capability": "Exactly UI-01 through UI-20 and ENG-01 through ENG-20 are implemented in the standalone experience prototype and mapped to verification evidence.",
  "dependencies": "Current test artifacts and release packet",
  "dependency": "Current verified Rhetorical InDEX experience-prototype baseline",
  "evidence": "IMPROVEMENT_TRACEABILITY.md and QA_REPORT.md",
  "freshness": "current release candidate",
  "id": "VER-004",
  "last_verified": "2026-08-09T10:40:00Z",
  "priority": "highest",
  "reason_pending": "Requested in current turn; implementation and validation have not yet been performed.",
  "recheck_trigger": "Any change to scanner UI, internal state/data engine, plan capability table, or packaging",
  "scope": "Current Rhetorical InDEX offline prototype and implementation plan",
  "state": "verified",
  "status": "active",
  "task": "Implement exactly twenty substantive UI/UX improvements and exactly twenty substantive prototype-engine/backend improvements, including the tablet lens repair, then update the plan, QA evidence, operational state, and ZIP.",
  "title": "Twenty UI/UX and twenty engine improvements are implemented and traced",
  "validation_needed": "Requirement-count audit, tablet runtime journey, regression checks across all views, accessibility, offline operation, static/security checks, bug sweep, and archive integrity.",
  "verification_method": "Improvement ledger, 80/80 static checks, 75/75 Chromium runtime checks, 36/36 accessibility checks, syntax/CSS/authorship gates, and bug resweep"
}
-->
### VER-004 — Twenty UI/UX and twenty engine improvements are implemented and traced

- **State:** `verified`
- **Artifact Revision:** HTML bfe0020facf08cad391caa4dcca9a0428e765d8f0f4b5afeaac11f883c10dd18 / plan 40dce003d1ba8525d2be8b1b24e8e72077bcedf77adc8599bfa6064042a75c57
- **Blocks Completion:** Yes
- **Capability:** Exactly UI-01 through UI-20 and ENG-01 through ENG-20 are implemented in the standalone experience prototype and mapped to verification evidence.
- **Dependencies:** Current test artifacts and release packet
- **Dependency:** Current verified Rhetorical InDEX experience-prototype baseline
- **Evidence:** IMPROVEMENT_TRACEABILITY.md and QA_REPORT.md
- **Freshness:** current release candidate
- **Last Verified:** 2026-08-09T10:40:00Z
- **Priority:** highest
- **Reason Pending:** Requested in current turn; implementation and validation have not yet been performed.
- **Recheck Trigger:** Any change to scanner UI, internal state/data engine, plan capability table, or packaging
- **Scope:** Current Rhetorical InDEX offline prototype and implementation plan
- **Status:** active
- **Task:** Implement exactly twenty substantive UI/UX improvements and exactly twenty substantive prototype-engine/backend improvements, including the tablet lens repair, then update the plan, QA evidence, operational state, and ZIP.
- **Validation Needed:** Requirement-count audit, tablet runtime journey, regression checks across all views, accessibility, offline operation, static/security checks, bug sweep, and archive integrity.
- **Verification Method:** Improvement ledger, 80/80 static checks, 75/75 Chromium runtime checks, 36/36 accessibility checks, syntax/CSS/authorship gates, and bug resweep
<!-- /operational-state:entry -->

## 6. Known Not Working

Add stable `BRK-###` entries for confirmed failures. Keep them until repair evidence exists.

## 7. Implemented but Unverified

Add stable `UNV-###` entries for code, files, configuration, or artifact features that exist but are not proven through the required user journey.

## 8. Unknown or Evidence-Stale State

Add stable `UNK-###` entries for missing, conflicting, inaccessible, stale, or invalidated evidence.

## 9. Pending Work

Add stable `PND-###` entries for intentionally incomplete work. Pending does not automatically mean failed.

## 10. Active Decisions, Defaults, and Prohibitions

Add stable `DEC-###` entries for source locks, routes, naming, packaging, style, rejected approaches, environment limits, and explicit supersessions.

<!-- operational-state:entry
{
  "authority": "Explicit user decisions",
  "evidence": "Discovery walk decisions",
  "id": "DEC-001",
  "last_checked": "pre-build",
  "recheck_trigger": "MVP scope change",
  "rule": "No social feed, public annotations, follower system, moderation layer, or potential-harm score is part of the first MVP.",
  "scope": "MVP",
  "state": "requested",
  "status": "active",
  "title": "MVP excludes social features and potential-harm scoring",
  "validation_method": "Inspect plan and prototype feature inventory."
}
-->
### DEC-001 — MVP excludes social features and potential-harm scoring

- **State:** `requested`
- **Authority:** Explicit user decisions
- **Evidence:** Discovery walk decisions
- **Last Checked:** pre-build
- **Recheck Trigger:** MVP scope change
- **Rule:** No social feed, public annotations, follower system, moderation layer, or potential-harm score is part of the first MVP.
- **Scope:** MVP
- **Status:** active
- **Validation Method:** Inspect plan and prototype feature inventory.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "authority": "Explicit user decision",
  "evidence": "Discovery walk decision",
  "id": "DEC-002",
  "last_checked": "pre-build",
  "recheck_trigger": "Copy or taxonomy changes",
  "rule": "The first-run scanner uses established rhetorical or logical terms as tags; plain-language label generation is deferred.",
  "scope": "MVP copy and taxonomy",
  "state": "requested",
  "status": "active",
  "title": "Technical rhetoric terms are the first-run labels",
  "validation_method": "Inspect prototype tags and plan copy rules."
}
-->
### DEC-002 — Technical rhetoric terms are the first-run labels

- **State:** `requested`
- **Authority:** Explicit user decision
- **Evidence:** Discovery walk decision
- **Last Checked:** pre-build
- **Recheck Trigger:** Copy or taxonomy changes
- **Rule:** The first-run scanner uses established rhetorical or logical terms as tags; plain-language label generation is deferred.
- **Scope:** MVP copy and taxonomy
- **Status:** active
- **Validation Method:** Inspect prototype tags and plan copy rules.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "authority": "Explicit user request plus deliverable lock",
  "evidence": "Current build request",
  "id": "DEC-003",
  "last_checked": "pre-build",
  "recheck_trigger": "Packaging or filename change",
  "rule": "Deliver Rhetorical_InDEX.html as a fully self-contained offline HTML artifact, Rhetorical_InDEX_Implementation_Plan.md as the external full plan, and package them with QA/state evidence in one ZIP.",
  "scope": "Current handoff",
  "state": "requested",
  "status": "active",
  "title": "Offline package shape",
  "validation_method": "Inspect archive members, open HTML with network disabled, and compare embedded plan against Markdown source."
}
-->
### DEC-003 — Offline package shape

- **State:** `requested`
- **Authority:** Explicit user request plus deliverable lock
- **Evidence:** Current build request
- **Last Checked:** pre-build
- **Recheck Trigger:** Packaging or filename change
- **Rule:** Deliver Rhetorical_InDEX.html as a fully self-contained offline HTML artifact, Rhetorical_InDEX_Implementation_Plan.md as the external full plan, and package them with QA/state evidence in one ZIP.
- **Scope:** Current handoff
- **Status:** active
- **Validation Method:** Inspect archive members, open HTML with network disabled, and compare embedded plan against Markdown source.
<!-- /operational-state:entry -->

<!-- operational-state:entry
{
  "authority": "Explicit user request plus environment constraint",
  "evidence": "Current user turn",
  "id": "DEC-004",
  "last_checked": "pre-implementation",
  "recheck_trigger": "Any scope, packaging, or architecture change during this pass",
  "rule": "This pass must implement exactly twenty UI/UX improvements and exactly twenty backend-equivalent improvements. Because the deliverable remains a self-contained offline HTML prototype, backend-equivalent means the internal analysis/data/state engine and its contracts, not a fabricated remote server.",
  "scope": "Current improvement pass",
  "state": "requested",
  "status": "active",
  "title": "Current improvement pass count and backend interpretation",
  "validation_method": "Count mapped improvements in the implementation ledger and verify each against source/runtime evidence."
}
-->
### DEC-004 — Current improvement pass count and backend interpretation

- **State:** `requested`
- **Authority:** Explicit user request plus environment constraint
- **Evidence:** Current user turn
- **Last Checked:** pre-implementation
- **Recheck Trigger:** Any scope, packaging, or architecture change during this pass
- **Rule:** This pass must implement exactly twenty UI/UX improvements and exactly twenty backend-equivalent improvements. Because the deliverable remains a self-contained offline HTML prototype, backend-equivalent means the internal analysis/data/state engine and its contracts, not a fabricated remote server.
- **Scope:** Current improvement pass
- **Status:** active
- **Validation Method:** Count mapped improvements in the implementation ledger and verify each against source/runtime evidence.
<!-- /operational-state:entry -->

## 11. Validation and Evidence Matrix

| ID | Claim or behavior | State | Evidence | Validation method | Artifact/revision | Last checked | Recheck trigger |
|---|---|---|---|---|---|---|---|

## 12. Current Change Scope and Impact Radius

- **Allowed to change:** Not yet declared.
- **Must remain unchanged:** Existing verified behavior outside the impact radius.
- **Potentially affected behavior:** Unknown until the next task is scoped.
- **Mandatory checks:** None yet selected.
- **Checks deliberately reused:** None yet selected.
- **Repair class:** Undeclared.

## 13. Compact Revision Log

### Revision 1 — 2026-08-09T04:50:08Z

- **Artifact/source identity:** `Not yet established`
- **State deltas:** Initialized operational state.
- **New evidence:** None.
- **Validation not performed:** All behavioral validation remains pending unless explicitly recorded above.

### Revision 2 — 2026-08-09T04:51:52Z

- **Artifact/source identity:** pre-build specification
- **State deltas:** Added INV-001 to 4. Active Invariants; Added INV-002 to 4. Active Invariants; Added INV-003 to 4. Active Invariants; Added INV-004 to 4. Active Invariants; Added INV-005 to 4. Active Invariants; Added INV-006 to 4. Active Invariants; Added INV-007 to 4. Active Invariants; Added INV-008 to 4. Active Invariants; Added INV-009 to 4. Active Invariants; Added INV-010 to 4. Active Invariants; Added DEC-001 to 10. Active Decisions, Defaults, and Prohibitions; Added DEC-002 to 10. Active Decisions, Defaults, and Prohibitions; Added DEC-003 to 10. Active Decisions, Defaults, and Prohibitions; Added PND-001 to 9. Pending Work; Updated metadata: current_baseline, scope_boundaries
- **New evidence:** Current conversation establishes article-first scanner, lens interaction, comparison-first results, radical transparency, and interpretive-pressure scope
- **Newly verified behavior:** None.
- **Newly known failure:** None.
- **Superseded rule:** None.
- **Validation not performed:** No artifact exists yet; runtime validation pending
- **Reason for broad revalidation:** Not applicable.
- **Summary:** Lock Rhetorical InDEX MVP purpose, interaction model, and package contract

### Revision 3 — 2026-08-09T05:20:28Z

- **Artifact/source identity:** Rhetorical_InDEX.html sha256 1ecad10a4d540b7f8ffbaaee111e660e68a73ea0f57908f58c0fcede4195bdda / plan sha256 ee1762c59effb595d98666bcdb585210d5a2b08195ad362de5898b9e660716ac
- **State deltas:** Moved PND-001 from 9. Pending Work to 5. Verified Working Behavior as VER-001; Added VER-002 to 5. Verified Working Behavior; Updated metadata: artifact_path, current_baseline
- **New evidence:** 43/43 Chromium CDP runtime checks passed with zero runtime exceptions and zero page error log entries; 49/49 structural/product checks passed; 11/11 pure JavaScript scanner/security checks passed; 24/24 accessibility and contrast checks passed; HTML Artifact Studio validator PASS and Web Authorship Gate PASS; Desktop scanner, mobile scanner, and mobile comparison screenshots visually inspected; Initial release ZIP passed unzip -t integrity check
- **Newly verified behavior:** VER-001; VER-002
- **Newly known failure:** None.
- **Superseded rule:** None.
- **Validation not performed:** Firefox and Safari runtime execution; Live screen-reader session; Direct file:// navigation in the managed Chromium environment because URLBlocklist policy blocks local navigation
- **Reason for broad revalidation:** Final artifact build changed scanner state coordination, mobile lens bounds, accessibility focus containment, responsive overflow handling, and view-switch scrolling during the bug-sweep repair loop.
- **Summary:** Promote the Rhetorical InDEX experience prototype and implementation packet after final QA and release packaging checks

### Revision 4 — 2026-08-09T10:22:28Z

- **Artifact/source identity:** Rhetorical_InDEX.html release baseline sha256 1ecad10a4d540b7f8ffbaaee111e660e68a73ea0f57908f58c0fcede4195bdda
- **State deltas:** Added BRK-001 to 6. Known Not Working; Added PND-002 to 9. Pending Work; Added DEC-004 to 10. Active Decisions, Defaults, and Prohibitions
- **New evidence:** User reports the lens feature is not working correctly on a tablet; User explicitly requests twenty UI/UX improvements and twenty backend/engine improvements
- **Newly verified behavior:** None.
- **Newly known failure:** BRK-001
- **Superseded rule:** None.
- **Validation not performed:** None.
- **Reason for broad revalidation:** The requested pass affects responsive layout, pointer/touch lens interaction, scanner state, local analysis engine, and packaging.
- **Summary:** Open tablet-lens repair and 20+20 improvement pass

### Revision 5 — 2026-08-09T10:40:54Z

- **Artifact/source identity:** Rhetorical_InDEX.html sha256 bfe0020facf08cad391caa4dcca9a0428e765d8f0f4b5afeaac11f883c10dd18 + Rhetorical_InDEX_Implementation_Plan.md sha256 40dce003d1ba8525d2be8b1b24e8e72077bcedf77adc8599bfa6064042a75c57
- **State deltas:** Moved BRK-001 from 6. Known Not Working to 5. Verified Working Behavior as VER-003; Moved PND-002 from 9. Pending Work to 5. Verified Working Behavior as VER-004; Updated metadata: current_baseline
- **New evidence:** 80/80 static/product traceability checks pass; 75/75 Chromium runtime checks pass across desktop, tablet portrait/landscape rotation, phone, large coarse pointer, paste/security, and engine fixtures; 36/36 accessibility/contrast/semantics checks pass; HTML Artifact Studio validator 10/10 pass; CSS parser 0 errors; web authorship gate PASS
- **Newly verified behavior:** VER-003; VER-004
- **Newly known failure:** None.
- **Superseded rule:** None.
- **Validation not performed:** Safari/iPadOS runtime; Firefox runtime; real screen-reader session; direct file:// navigation in managed Chromium (blocked by organization policy; exact document content executed via CDP)
- **Reason for broad revalidation:** The change affects the primary lens interaction, responsive layouts, scanner state management, and internal analysis engine.
- **Summary:** Verify the 20+20 improvement pass and repaired tablet lens after full runtime and QA validation

