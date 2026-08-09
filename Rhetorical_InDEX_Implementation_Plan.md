# Rhetorical InDEX — Revised Beginning-to-End Implementation Plan

**Status:** source-of-truth implementation plan after adversarial review  
**Product name:** **Rhetorical InDEX**  
**Product class:** open-source, public-interest news rhetoric scanner and comparative evidence instrument  
**Primary audience:** ordinary news readers, with deeper inspection available for researchers, journalists, educators, and maintainers  
**First-run analytical target:** interpretive pressure, not potential harm  
**First-run interaction:** article-first scanner with movable lens  

---

## 0. What changed after the adversarial review

The first plan was too broad to be a credible first build. The revised plan therefore changes the execution model without changing the product philosophy.

Five rules now govern the build:

1. **Ship in three layers:** Experience Prototype -> Instrument Alpha -> News-Scale Beta. The scanner experience is proven before the news infrastructure is allowed to dominate the project.
2. **Start with a smaller taxonomy kernel:** the first working detector implements a bounded set of mechanisms with explicit boundaries. Expansion is gated mechanism by mechanism.
3. **Prove comparison with fixtures before live aggregation:** the UI and data contract for same-event comparison, omission, and evidence can be validated without first building a global news crawler.
4. **Expose structured evidence, not mystical reasoning:** transparency means exact span, criteria, evidence, detector votes, uncertainty, alternatives, and versioning. It does not mean exposing private chain-of-thought or dumping an unbounded explanation monologue.
5. **Prevent uncertainty from cascading:** uncertain findings remain visible, but low-confidence claim alignment, incomplete source coverage, and weak evidence retrieval cannot silently become strong contradiction or omission judgments.

These are permanent guardrails unless explicitly revised later.

---

# Part I — Product contract

## 1. Purpose

Rhetorical InDEX exists to help a reader see what language is doing to their interpretation while they are reading news.

Every telling of an event makes selections: what is foregrounded, what is omitted, which actor is named, which verb is chosen, how certain a claim sounds, which quote is selected, which context is deferred, and which emotional frame becomes the default. Rhetorical InDEX makes those operations inspectable.

The MVP does **not** need to decide which political faction is "correct." It does not need a centrist reference point. It does not need to classify a source as Left, Center, or Right. The scanner should instead expose the mechanics of the telling itself and the evidence structure underneath factual claims.

The product succeeds when a reader can move from:

> "This article feels manipulative."

or

> "This article sounds neutral, so I assume it is neutral."

into a more precise inspection:

> "This sentence presupposes a disputed premise, assigns certainty beyond its source, suppresses the actor, and omits a duration clause that appears in peer coverage and the underlying order."

The instrument should make disagreement more productive because every finding can be challenged at the level of text, definition, evidence, and method.

## 2. Core definitions

### 2.1 Interpretive pressure

**Interpretive pressure** is the degree to which language steers, narrows, preloads, emotionally weights, or structurally constrains a reader's interpretation of a passage.

Interpretive pressure is not synonymous with:

- falsehood;
- harm;
- ideology;
- bias score;
- malicious intent;
- source reliability;
- moral wrongness.

A factually accurate passage can apply very strong interpretive pressure. A false or materially misleading passage can be written in calm, low-pressure language.

### 2.2 Finding

A **finding** is a claim by Rhetorical InDEX that one or more defined rhetorical, logical, evidentiary, or journalism-specific mechanisms occur in a particular scope of source material.

A finding always includes:

- the exact affected text or structural relationship;
- one or more taxonomy mechanisms;
- interpretive-pressure level;
- confidence;
- observable criteria that triggered the finding;
- relevant exclusion/near-miss considerations;
- alternative interpretation or limitation;
- provenance and analysis version.

### 2.3 Material omission

A **material omission candidate** is a fact or context item absent from the target article whose inclusion could reasonably change how the event is interpreted with respect to agency, cause, scale, timeline, status, responsibility, consequence, denominator, or evidence quality.

It can only be emitted when the system can show:

1. what the missing claim is;
2. that it was reasonably knowable at the article's publication/update time;
3. what independent coverage and/or primary evidence supports it;
4. why its absence is material;
5. how confident the system is in the event/claim alignment.

The label describes effect and evidence, not author intent.

### 2.4 Coverage consensus

**Coverage consensus** is the degree to which genuinely independent reporting sources assert compatible versions of a claim. It is not a truth score.

### 2.5 Primary evidence

**Primary evidence** is source material close to the event or claim itself: documents, datasets, recordings, filings, orders, transcripts, original research, or first-party statements when those statements are the object of the claim.

Primary evidence is not automatically correct, complete, or neutral. It is assessed for authenticity, directness, context, temporal relevance, and independence.

---

## 3. Non-negotiable product rules

1. Default entry is an article scanner.
2. Compare is the first results destination.
3. Event Record is secondary to Compare but directly reachable.
4. Intrinsic rhetoric analysis is the primary pressure signal.
5. Peer comparison modifies/contextualizes intrinsic analysis; it does not define rhetoric by majority vote.
6. Multiple mechanisms may apply to the same text.
7. Low-confidence findings are visible by default.
8. Confidence and pressure are separate visual and data dimensions.
9. Color hue indicates mechanism family; strength indicates pressure, never harm or confidence.
10. No Left/Center/Right source axis in the core UI.
11. No social/community layer in the first release.
12. No potential-harm score in the first release.
13. No plain-language renaming system is required for the first release; canonical terms come first.
14. No novel mechanism can be promoted directly from model improvisation into production taxonomy.
15. No single trust, propaganda, distortion, or truth score may summarize an article.
16. Every important analytical assertion is inspectable.
17. The system must distinguish "not found" from "false" and "widely repeated" from "strongly evidenced."
18. Quoted-speaker rhetoric and outlet/editorial rhetoric must remain distinguishable.
19. Incomplete source coverage must be visible.
20. The scanner must remain usable without a mouse or the lens effect.

---

## 4. Release layers

### 4.1 Layer A — Experience Prototype

Purpose: prove the human interaction before building production inference or ingestion.

Uses:

- one self-contained HTML file;
- fictional event/source fixtures;
- hand-authored findings;
- optional local heuristic scan for pasted text;
- fully working lens, multi-tags, detail drawer, pressure profile, Compare, Event Record, settings, and plan viewer.

This prototype is not presented as live fact-checking.

### 4.2 Layer B — Instrument Alpha

Purpose: prove that a bounded taxonomy can be detected accurately and transparently on real text.

Includes:

- paste-text scanning;
- bounded Alpha-0 taxonomy;
- real intrinsic detector pipeline;
- reviewed benchmark built **after** the first vertical slice exists;
- fixture-backed comparison/evidence UI;
- versioned finding schema;
- public methodology.

Live broad news aggregation is not required for Instrument Alpha.

### 4.3 Layer C — News-Scale Beta

Purpose: attach the proven instrument to real event discovery, peer coverage, claim alignment, omission detection, and primary-evidence workflows.

Includes:

- URL ingestion;
- source registry;
- peer event clustering;
- source-dependence graph;
- claim extraction/alignment;
- journalism-specific cross-document mechanisms;
- evidence retrieval;
- evolving Event Record;
- public open-source deployment.

This separation prevents infrastructure ambition from delaying the core scanner.

---

# Part II — Exact MVP feature contract

## 5. MVP feature inventory

For this plan, **MVP** means the first useful Instrument Alpha plus the fixture-backed comparison experience. News-Scale Beta expands the same product rather than redefining it.

| Feature | User value | MVP behavior | Production path |
|---|---|---|---|
| Article reader | Keeps news reading primary | Clean reading column | URL/paste normalized article model |
| Scanner lens | Reveals analysis without visual overload | Movable local reveal | DOM-range annotation overlay |
| Multi-tag spans | Shows overlapping mechanisms | All applicable tags rendered | Multi-label finding schema |
| Technical rhetoric tags | Builds precise vocabulary | Canonical mechanism names | Versioned taxonomy package |
| Pressure intensity | Shows rhetorical force | 1–4 ordinal per finding | Mechanism-specific calibrated rubric |
| Confidence | Shows uncertainty | Low/Medium/High separate from pressure | Calibrated detector confidence |
| Pressure profile | Shows article pattern | density/peaks/dominant families | derived profile with candidate/confirmed bands |
| Finding drawer | Makes analysis inspectable | exact span, criteria, alternative, versions | structured decision trace/evidence |
| Compare coverage | Shows differences first | fixture-backed side-by-side | live event peers and aligned claims |
| Omission | Shows what changes interpretation by absence | fixture-backed candidate | event-time-aware comparative detector |
| Fact/evidence states | Separates evidence from rhetoric | supported/contested/etc. fixture | live evidence graph |
| Coverage consensus | Shows reporting agreement | source count + dependence note | source-independence graph |
| Strongest primary evidence | Surfaces conflict with dominant account | fixture evidence record | evidence retrieval/ranking |
| Forensic Event Record | Separates event from tellings | atomic claim ledger | evolving evidence graph |
| Accessibility fallback | Makes scanner usable beyond pointer | Reveal All + findings list | maintained as first-class path |

---

# Part III — User experience

## 6. Entry and scan creation

### 6.1 Production entry screen

Primary content:

- Product name: **Rhetorical InDEX**
- Product descriptor: **Inspect the pressure inside the language.**
- URL input.
- Paste-text option.
- Demo event.

The interface should not begin with a manifesto. A short methodology link is sufficient.

### 6.2 Scan request states

A scan is a staged job with explicit states:

1. `received`
2. `extracting`
3. `intrinsic_analysis`
4. `article_ready`
5. `peer_search`
6. `comparison_analysis`
7. `evidence_analysis`
8. `complete`
9. `partial`
10. `failed`

The user can enter the article when `article_ready` is reached. Peer/evidence work can continue progressively.

The system never keeps a reader staring at a fake spinner until every backend stage completes.

## 7. Default Scanner view

### 7.1 Desktop composition

**Header rail**

- Rhetorical InDEX mark.
- Source/title metadata.
- analysis-version/provenance button.
- Lens toggle.
- Reveal All toggle.
- Filters.
- Primary action: **Compare coverage**.

**Pressure profile**

- Peak pressure level.
- Candidate/confirmed flagged density displayed separately.
- Dominant mechanism families.
- Mini-map of pressure clusters by paragraph.

**Article**

- Comfortable serif or editorial reading face using local/system fonts.
- approximately 65–75 character line length.
- wide margins around the article so the lens can move without colliding with controls.

**Right detail region on wide screens**

- collapsed until a finding is selected.
- no permanent dashboard clutter.

### 7.2 Mobile composition

- header condenses to product mark, compare action, and scanner menu.
- article remains primary.
- a draggable lens control sits slightly above the bottom safe area.
- selected finding opens a bottom sheet.
- Compare becomes a sticky but non-obscuring action after the article heading.
- horizontal comparison tables become claim cards.

## 8. Lens interaction

### 8.1 Default visual state

Outside the lens:

- article is plain;
- optional faint margin ticks indicate that findings exist in nearby paragraphs;
- no permanent colored blocks cover the reading experience.

Inside the lens:

- affected span background appears;
- saturation/weight reflects pressure 1–4;
- mechanism tags appear at the end of the relevant span or in a stable attached marker lane;
- confidence is represented by tag border style and accessible label;
- multiple tags are visible together.

### 8.2 Stable activation rule

The lens reveals; it does not have to serve as the only click target.

A finding can be selected by:

- clicking a visible marker while the lens is pinned;
- clicking the corresponding item in the findings rail/list;
- using keyboard next/previous finding controls;
- tapping the marker in mobile Reveal All mode.

This avoids fragile hit targets inside a moving clip mask.

### 8.3 Lens controls

- Toggle Lens.
- Pin/unpin lens.
- Lens size Small/Medium/Large.
- Reveal All.
- Hide/show candidate low-confidence findings; default show.
- Filter by mechanism family; default all.

### 8.4 Keyboard model

Proposed shortcuts:

- `L` Lens toggle.
- `A` Reveal All.
- `J` Next finding.
- `K` Previous finding.
- `Enter` Inspect selected finding.
- `C` Compare coverage.
- `E` Event Record.
- `Esc` Close drawer/sheet or unpin lens.

Shortcuts are discoverable in a command/help panel and do not override browser conventions when focus is in an input.

## 9. Tags and visual semantics

### 9.1 Tag content

First-run tags use canonical terms such as:

- Loaded language
- Presupposition
- Epistemic overstatement
- Agent suppression
- Appeal to fear
- False dilemma
- Hasty generalization
- Causal overclaim
- Headline/body mismatch
- Selective quotation
- Material omission

Plain-language glosses can later appear in definitions, but no additional label-generation system is required for Alpha.

### 9.2 Intensity encoding

Pressure uses:

- stronger/lighter fill within one family hue;
- explicit `P1`, `P2`, `P3`, `P4` in the detailed view;
- accessible text: "Interpretive pressure: strong (3 of 4)."

### 9.3 Confidence encoding

Confidence uses:

- high: solid tag border;
- medium: dashed border;
- low: dotted border;
- explicit confidence text in tooltip/drawer.

Low confidence does not disappear by default.

### 9.4 No color-only meaning

Mechanism name, pressure level, confidence text/border, and position all remain usable without color perception.

## 10. Finding detail drawer

The drawer uses progressive disclosure.

### 10.1 First layer: immediate answer

- Mechanism.
- Exact affected text.
- Pressure level.
- Confidence.
- One-sentence basis.

### 10.2 Second layer: Why this was tagged

Structured observations only:

- triggered criteria;
- linguistic/structural feature;
- evidence or comparison dependency;
- overlap with other mechanisms.

### 10.3 Third layer: Why it could be wrong

- near-miss condition;
- detector disagreement;
- missing context;
- alternate grammatical/semantic interpretation;
- evidence limitation.

### 10.4 Fourth layer: Comparison and evidence

When available:

- aligned peer wording;
- omission context;
- evidence item;
- coverage consensus;
- source dependence warning.

### 10.5 Fifth layer: Provenance

- taxonomy version;
- detector versions;
- source snapshot hash/ID;
- analysis run;
- timestamp;
- configuration.

The UI exposes a **decision trace**, not raw hidden chain-of-thought.

## 11. Pressure profile

No single trust/distortion score is shown.

Profile components:

1. **Peak pressure:** highest pressure level among displayed findings.
2. **Confirmed density:** share of relevant text covered by medium/high-confidence findings above the reporting threshold.
3. **Candidate density:** share covered only by low-confidence findings.
4. **Pressure distribution:** count by P1–P4.
5. **Dominant mechanism families:** by span coverage and finding count.
6. **Pressure map:** paragraph locations of P3/P4 clusters.
7. **Peer deltas:** only when sufficient comparison coverage exists.

This structure prevents article-padding from hiding intense local passages inside a harmless average.

---

# Part IV — Comparison, evidence, and omission

## 12. Compare is the first results destination

The reader selects **Compare coverage** from the article.

The view begins with **What this article does differently**.

Possible cards:

- `Higher fear framing` — "3 aligned claims show stronger fear framing than the available peer set."
- `Agency differs` — "This article leaves the actor implicit where 4 peers name the agency."
- `Material omission candidate` — missing fact with time/evidence support.
- `Evidence conflict` — dominant reporting vs primary evidence.
- `Lower certainty` — target uses more qualified wording than peers.

Each card opens the underlying aligned claims. No card exists without traceable data.

## 13. Claim-level comparison

A comparison row contains:

```text
normalized_claim
alignment_confidence
target_excerpt
peer_excerpts[]
peer_source_independence[]
mechanism_differences[]
evidence_state
material_omission_state
```

### 13.1 Alignment relation types

- equivalent
- narrower
- broader
- contradicts
- partially overlaps
- contextualizes
- unrelated
- uncertain

Low-confidence alignment may be displayed as a candidate but may not drive a strong omission/contradiction label until a secondary verifier passes.

## 14. Quoted speech versus outlet voice

Every text finding includes voice provenance:

- `headline`
- `reporter`
- `quoted_speaker`
- `caption`
- `editorial_note`
- `source_document`

The interface should say, for example:

> **Appeal to fear — quoted speaker**
> The rhetoric is in the quotation. The outlet's analytical responsibility is represented separately through selection, headline framing, surrounding qualification, and prominence.

This prevents the scanner from falsely attributing every quoted mechanism to the journalist.

## 15. Material omission

### 15.1 Candidate generation

An omission candidate requires:

1. event membership above threshold;
2. claim alignment above threshold;
3. evidence that the missing fact existed by the target article's relevant timestamp;
4. support from independent coverage and/or evidence;
5. a materiality rationale;
6. no evidence that the target expressed the same fact in a semantically equivalent form.

### 15.2 Materiality dimensions

The finding must name one or more dimensions:

- Agency
- Cause
- Scale
- Timeline
- Status (proposed/enacted, alleged/proven, temporary/permanent)
- Responsibility
- Consequence
- Denominator/baseline
- Evidence quality

No generic "important context" finding is allowed.

### 15.3 Chronology

Every candidate is evaluated against `article_known_at`.

If a fact entered the record after publication, the system may show it as a **later development**, not an omission.

If an article was updated later, the updated timestamp creates a new comparison snapshot.

## 16. Fact/evidence states

### 16.1 Claim state vocabulary

- Supported by direct evidence
- Corroborated by independent reporting
- Contested
- Contradicted by identified evidence
- Unverified
- Context-sensitive
- Non-factual/interpretive
- Retrieval incomplete

`Retrieval incomplete` is deliberately separate so a failed evidence search cannot masquerade as a factual judgment.

### 16.2 Evidence-quality dimensions

Every primary evidence item can be inspected against:

- Authenticity: is the item what it claims to be?
- Directness: how directly does it bear on the exact claim?
- Completeness: is the relevant context available?
- Temporal relevance: was it valid at the claim's time?
- Independence: is it simply the claimant restating its own claim?
- Scope fit: does it actually cover the geography/population/period implied?

The system may surface the strongest item found, but it does not erase its limitations.

## 17. Coverage consensus and source dependence

Coverage consensus must be calculated from a source-dependence graph, not raw article count.

Dependence clues:

- exact/near-exact text overlap;
- explicit syndication credit;
- shared wire-service attribution;
- common linked primary source;
- publication sequence;
- paragraph-order similarity;
- shared uncommon errors/phrases;
- source-to-source citation.

The graph stores uncertainty. The UI can say:

> "6 articles repeat this claim; at least 3 appear independently reported."

That is more honest than "6 sources confirm."

## 18. Event Record

The Event Record is a versioned forensic ledger, not a neutralized article.

Each claim row contains:

- claim ID;
- normalized proposition;
- earliest known time;
- current evidence state;
- strongest identified evidence with limitations;
- coverage consensus;
- source-dependence note;
- contradictions;
- source wording variants;
- rhetorical differences;
- omission relationships;
- event-record version.

### 18.1 Evolving events

The record is temporal.

A claim can move:

`unverified -> corroborated -> contested -> contradicted`

or another path as evidence changes.

Old article comparisons remain reproducible against the evidence state available at the time of that analysis.

---

# Part V — Taxonomy and detector design

## 19. Alpha-0 taxonomy kernel

The revised plan does not attempt the entire rhetoric textbook at once.

### 19.1 Intrinsic kernel

1. **Loaded language**
2. **Euphemism / dysphemism**
3. **Presupposition**
4. **Epistemic overstatement**
5. **Agent suppression**
6. **Appeal to fear**
7. **False dilemma**
8. **Hasty generalization**
9. **Causal overclaim**

### 19.2 Journalism/cross-document kernel

10. **Headline/body mismatch**
11. **Selective quotation / quote-mining**
12. **Material omission**

These twelve are a starting instrument, not a claim that other mechanisms are unimportant.

### 19.3 Batch-2 candidates

Add only after per-mechanism gates:

- Straw man
- Ad hominem
- Whataboutism / tu quoque
- Slippery slope
- Scapegoating / collective attribution
- Anecdotal substitution
- Buried qualification
- Source laundering
- Agency inflation
- Appeal to authority with strict contextual rules

## 20. Taxonomy record

Every mechanism lives in a versioned record:

```yaml
mechanism_id: epistemic_overstatement
canonical_name: Epistemic overstatement
family: epistemic
scope: [clause, sentence, paragraph]
definition: ...
positive_criteria:
  - ...
exclusion_criteria:
  - ...
nearest_neighbors:
  - presupposition
  - causal_overclaim
cooccurrence_rules:
  - ...
required_context:
  - evidence_support
pressure_features:
  - ...
pressure_anchors:
  1: ...
  2: ...
  3: ...
  4: ...
examples:
  - ...
counterexamples:
  - ...
review_state: alpha
```

## 21. Mechanism confusion matrix

Before detector implementation, every mechanism is compared with nearest neighbors.

Example distinctions:

- **Presupposition vs epistemic overstatement:** presupposition embeds a proposition as given; overstatement raises certainty beyond support.
- **Loaded language vs appeal to fear:** loaded language is connotative framing; fear appeal specifically uses feared consequence as persuasive leverage.
- **Agent suppression vs material omission:** agent suppression occurs in the sentence/grammar; material omission is cross-document absence of a fact.
- **Causal overclaim vs hasty generalization:** causal overclaim asserts cause; hasty generalization broadens from insufficient sample.

Co-occurrence is allowed when criteria independently hold.

## 22. Mechanism detection pipeline

### 22.1 Candidate generation

Use low-cost mechanisms first:

- syntax parser features;
- lexical/phrase signals;
- modality/certainty markers;
- attribution structure;
- sentence relationships;
- specialized classifiers.

Candidate generation is intentionally recall-heavy.

### 22.2 Contextual verification

Context-dependent candidates are passed to a structured contextual judge.

The judge receives:

- exact span;
- bounded surrounding context;
- mechanism definition;
- positive/exclusion criteria;
- relevant evidence features;
- nearest-neighbor definitions.

Output is schema-constrained:

```text
applies: yes/no/uncertain
criteria_triggered[]
criteria_failed[]
nearest_neighbor_overlap[]
pressure_features[]
confidence_factors[]
```

### 22.3 Reconciliation

A deterministic reconciler:

- preserves multiple tags;
- merges duplicate span candidates;
- marks detector disagreement;
- prevents low-confidence claim alignment from generating strong cross-document findings;
- stores detector votes.

### 22.4 No raw reasoning requirement

The system stores structured observations and decisions, not hidden/private reasoning traces. This keeps transparency reproducible and bounded.

## 23. Pressure scoring

Pressure is an ordinal mechanism-specific judgment.

### 23.1 Universal level meaning

- `P1 Light`: a mechanism is present but exerts limited steering.
- `P2 Moderate`: materially affects interpretation while alternatives remain salient.
- `P3 Strong`: substantially constrains interpretation, agency, certainty, or emotional frame.
- `P4 Extreme`: the mechanism dominates the interpretive framing of the relevant passage.

### 23.2 Feature-based scoring

Each mechanism defines its own features.

Example: **Agent suppression**

- Is an actor grammatically omitted?
- Is the actor central to responsibility?
- Is the actor named nearby?
- Does the omission materially change perceived agency?
- Is passive voice required by ordinary informational structure?

Example: **Appeal to fear**

- Is a feared outcome invoked?
- Is the feared outcome central to the persuasive move?
- Is likelihood/support established?
- Is severity language proportional to evidence?
- Does the passage present alternatives or uncertainty?

The drawer shows the fired features.

## 24. Confidence model

Internal confidence can be continuous, but the initial UI shows Low/Medium/High.

Inputs:

- detector agreement;
- span-boundary certainty;
- parser confidence;
- contextual judge certainty;
- evidence availability;
- claim alignment confidence;
- taxonomy ambiguity;
- source extraction quality.

### 24.1 Two reporting thresholds

To preserve the user's high-recall preference without turning the profile into noise:

- **Candidate threshold:** low enough that plausible findings remain visible inside Lens/Findings.
- **Profile threshold:** higher threshold for confirmed-density statistics and comparative aggregate statements.

Candidate findings still appear by default; they simply do not silently inflate headline metrics.

---

# Part VI — Data and architecture

## 25. Core data objects

### 25.1 Article

```text
article_id
source_id
canonical_url
headline
byline
published_at
updated_at
fetched_at
language
genre_guess
extraction_confidence
content_blocks[]
content_hash
rights_status
```

### 25.2 Finding

```text
finding_id
article_id
mechanism_id
voice
scope
span_start
span_end
exact_text
pressure_level
confidence
criteria_triggered[]
criteria_failed[]
alternate_interpretation
detector_votes[]
comparison_refs[]
evidence_refs[]
taxonomy_version
analysis_run_id
```

### 25.3 Claim

```text
claim_id
article_id
mention_span
normalized_proposition
claim_type
entities[]
attribution
speaker
time_reference
certainty_markers[]
extraction_confidence
```

### 25.4 Claim relation

```text
relation_id
claim_a
claim_b
relation_type
confidence
verification_stage
```

### 25.5 Evidence item

```text
evidence_id
type
source_uri
snapshot_id
observed_at
effective_from
authenticity_state
directness
completeness
temporal_relevance
independence
scope_fit
notes
```

### 25.6 Event record

```text
event_id
version
created_at
knowledge_cutoff
member_articles[]
claim_records[]
coverage_gaps[]
```

## 26. Repository layout

```text
rhetorical-index/
  apps/
    web/
  services/
    api/
    ingest/
    rhetoric/
    comparison/
    evidence/
  packages/
    schema/
    taxonomy/
    scoring/
    fixtures/
    ui/
  benchmarks/
    annotation_guides/
    corpus/
    adjudication/
    reports/
  docs/
    product/
    methodology/
    architecture/
    governance/
  infra/
    local/
    deploy/
  tests/
    end_to_end/
    regression/
```

## 27. Technology choices

Use conservative components and pin exact versions when implementation begins.

- Frontend: TypeScript component application, client-side routing, semantic HTML/CSS.
- Backend/API: Python web service.
- Analysis workers: Python.
- Database: PostgreSQL.
- Vector retrieval: PostgreSQL vector extension initially.
- Background jobs: database-backed queue initially.
- Object storage: evidence/article snapshots where permitted.
- Search: PostgreSQL full-text plus vector retrieval.
- Shared contracts: JSON Schema plus generated Python/TypeScript types.
- Local development: containerized services and seeded fixture database.

Do not introduce Redis, Elasticsearch, Kafka, a dedicated vector database, or microservice orchestration merely because they are fashionable. Add them only when measured load requires them.

## 28. Service boundaries

### 28.1 API/orchestrator

Responsibilities:

- create scan;
- return stage state;
- serve article/finding/compare/event objects;
- enforce access and retention policies;
- stream incremental results.

### 28.2 Ingest

Responsibilities:

- safe URL fetching;
- access/robots policy;
- parsing/extraction;
- canonicalization;
- content hashing;
- duplicate detection;
- rights metadata.

### 28.3 Rhetoric service

Responsibilities:

- segmentation;
- voice/quotation attribution;
- candidate generation;
- contextual verification;
- pressure/confidence;
- finding provenance.

### 28.4 Comparison service

Responsibilities:

- event candidate retrieval;
- source-dependence graph;
- claim extraction/alignment;
- rhetorical difference calculations;
- omission candidates.

### 28.5 Evidence service

Responsibilities:

- identify candidate primary sources;
- snapshot metadata/content where allowed;
- claim/evidence relation;
- evidence-quality dimensions;
- chronology.

Service boundaries can initially run in one deployable application with separate modules. They are logical ownership boundaries, not a command to create premature distributed systems.

---

# Part VII — Ingestion and source coverage

## 29. URL ingestion safety

A production URL fetcher is security-sensitive.

Required controls:

- allow only `http`/`https`;
- resolve DNS and block private/link-local/loopback ranges;
- re-check destination after redirects;
- cap redirects;
- cap response size;
- enforce content types;
- time out aggressively;
- sanitize extracted HTML;
- never execute article scripts;
- do not accept arbitrary file/system schemes;
- log extraction failure without logging sensitive user content unnecessarily.

This prevents SSRF and hostile-content ingestion from becoming an obvious weak point.

## 30. Source registry

Store:

- source domain;
- feed endpoints;
- extraction adapter;
- known syndication relationships;
- geography/language;
- access constraints;
- storage/quotation policy;
- fetch reliability;
- last successful fetch.

No political-axis label is required.

## 31. Coverage disclosure

Every comparison includes a coverage disclosure:

- peer-set time window;
- number of fetched articles;
- estimated independent-source count;
- known fetch failures;
- languages included;
- source categories represented;
- whether the peer set is likely incomplete.

The product never silently presents a small peer sample as "the media."

---

# Part VIII — Frontend implementation

## 32. Semantic rendering strategy

Use one accessible base article DOM.

Annotations are derived from character ranges and rendered as:

- inline wrappers when stable;
- non-semantic overlay geometry for Lens visualization;
- synchronized findings list.

The overlay is `aria-hidden` and does not duplicate accessible text.

For long articles:

- track annotations per paragraph;
- mount overlay only near viewport;
- batch geometry updates in `requestAnimationFrame`;
- recompute on resize/font changes.

## 33. Lens geometry

Desktop:

- default radius roughly 140 CSS px;
- CSS custom properties `--lens-x`, `--lens-y`, `--lens-r`;
- overlay clipped with `clip-path` or mask;
- visible ring separate from overlay;
- pointer events remain on base article or stable marker targets.

Touch:

- draggable control point offset from lens center;
- lens center displayed above finger;
- tap pin/unpin;
- bottom sheet for finding details.

## 34. State model

Frontend scan state:

```text
activeView: scanner | compare | event | plan
lensEnabled
lensPinned
lensPosition
lensRadius
revealAll
activeFilters[]
showCandidates
selectedFindingId
selectedClaimId
selectedEvidenceId
scanStage
```

All state transitions have explicit UI consequences and can be tested without network calls against fixtures.

## 35. Loading, empty, error, success, offline states

### Scanner

- default: article visible.
- loading: staged real progress.
- empty: no article loaded -> URL/paste/demo actions.
- error: extraction error with paste fallback.
- partial: intrinsic findings available, compare unavailable.
- offline: previously loaded snapshot/fixtures available; live URL fetch disabled.

### Compare

- loading peer set;
- insufficient coverage;
- available but low independence;
- successful alignment;
- claim-level ambiguity.

### Event Record

- no primary evidence found;
- retrieval incomplete;
- conflicting evidence;
- later-development notice.

## 36. Motion system

Motion exists only where it explains state.

- lens position follows input directly or with subtle one-frame interpolation;
- detail drawer uses 180–240 ms transition;
- view changes use short fade/translate;
- pressure bars animate only after filter change;
- selected claim comparison crossfades rather than reshuffling unexpectedly;
- no ambient looping animations;
- `prefers-reduced-motion` removes transforms/interpolation and keeps instant state changes.

## 37. Accessibility gates

Required before Alpha:

- logical heading structure;
- article landmark;
- nav labels;
- visible focus;
- full keyboard route through scanner, findings, compare, event record;
- dialog/drawer focus management;
- Escape behavior;
- no color-only meaning;
- minimum touch targets;
- text zoom to 200% without loss of controls;
- reduced motion;
- live status announcements for scan stage and errors;
- accessible tables/cards for comparisons;
- screen-reader label for every finding including mechanism, pressure, confidence, and excerpt.

---

# Part IX — Performance and cost

## 38. Interaction budgets

Prototype/Frontend targets:

- lens pointer response should feel immediate; target one animation frame under ordinary desktop load;
- no layout shift when tags are revealed;
- finding selection response <100 ms locally;
- article scrolling remains smooth with annotations enabled;
- long-plan view is lazy/sectioned enough to remain navigable.

Production targets:

- article text should become readable before all analytical stages finish;
- intrinsic findings stream progressively;
- comparison/evidence may arrive later;
- one slow peer source cannot block article scanning.

These are budgets, not claims until measured.

## 39. Compute budget

Analysis tiers:

1. local/deterministic preprocessing;
2. cheap candidate retrieval/classification;
3. contextual verification only on candidates;
4. comparison only on aligned claims;
5. evidence retrieval only for factual claims that matter to comparison/omission.

Cache key includes:

`content_hash + taxonomy_version + detector_bundle_version + configuration`

Re-use stable results rather than re-running the full stack for every reader.

---

# Part X — Build and validation sequence

## 40. Phase 0 — Repository and contracts

### Build

- initialize repository;
- write product constitution/non-goals;
- create schemas for Article, Finding, Claim, Evidence, Event Record;
- create taxonomy package with versioning;
- create fixture format;
- create CI for lint/unit/static checks;
- create operational-state and decision-log conventions.

### Acceptance

- pressure/confidence are distinct fields;
- voice provenance exists;
- no ideology axis exists;
- every derived object can point to parent provenance;
- event objects support knowledge cutoff/timestamps.

## 41. Phase 1 — Experience Prototype

### Build

- self-contained article reader;
- movable lens;
- multi-tag spans;
- low-confidence visible candidate;
- finding detail drawer;
- pressure profile;
- Compare-first results;
- fixture omission;
- fixture evidence conflict;
- Event Record;
- settings;
- mobile and keyboard fallback;
- reduced motion.

### Fixture requirement

Use a fictional event so no prototype copy is mistaken for a live political fact check.

The fixture must contain:

- one factually supported but rhetorically high-pressure passage;
- one calm but context-sensitive claim;
- one multi-tag span;
- one low-confidence candidate;
- one material omission;
- one dominant-coverage/primary-evidence conflict;
- one quoted-speaker finding;
- one peer source with softer rhetoric;
- one peer source with stronger rhetoric.

### Acceptance

Article -> Lens -> Finding -> Compare -> Event Record works without network access.

## 42. Phase 2 — Alpha-0 taxonomy specification

For each of the 12 kernel mechanisms:

- canonical definition;
- positive criteria;
- exclusion criteria;
- near misses;
- nearest-neighbor distinctions;
- valid co-occurrences;
- context requirements;
- pressure features;
- P1–P4 anchors;
- examples/counterexamples;
- reviewer notes.

### Acceptance

A human reviewer can apply the definition without a model prompt and explain disagreements using the taxonomy record.

## 43. Phase 3 — First real detector vertical slice

Implement 4 mechanisms first:

- Loaded language;
- Presupposition;
- Agent suppression;
- False dilemma.

Why these four:

- lexical, pragmatic, grammatical, and logical categories are all represented;
- they test multi-label overlap and different detector strategies;
- they create enough output to build the first real benchmark.

### Build

- article segmentation;
- quotation/voice classification;
- candidate generation;
- structured contextual verification;
- finding reconciliation;
- pressure/confidence;
- transparent drawer output;
- local API endpoint.

### Acceptance

- real pasted articles produce structured findings;
- exact span is stable;
- detector votes are stored;
- multi-tag output works;
- no cross-document assertions are invented.

## 44. Phase 4 — First reviewed benchmark

Only now create the first benchmark for the actual instrument.

### Pilot corpus starting target

A practical first reviewed set can begin around:

- 40–60 articles across straight news, analysis, opinion, and press-release-like material;
- at least 400 candidate/negative passages;
- at least 30 positive reviewed examples per implemented mechanism where prevalence allows;
- deliberate near-miss negatives;
- multi-label examples;
- quoted-speaker examples.

These are starting targets, not sacred sample sizes. Expand where uncertainty intervals are too wide.

### Annotation fields

- exact span;
- mechanism(s);
- pressure level;
- reviewer confidence;
- alternative acceptable mechanism;
- near-miss/exclusion rationale;
- voice provenance;
- taxonomy version;
- adjudication status.

### Metrics

- recall per mechanism;
- precision per mechanism;
- recall-weighted F2;
- span overlap;
- multi-label recall;
- pressure agreement;
- calibration by confidence band;
- false positive types;
- false negative types.

No aggregate hides a failing mechanism.

## 45. Phase 5 — Calibrate and expand intrinsic kernel

### Gate for adding a mechanism

A new mechanism needs:

1. taxonomy record complete;
2. detector implemented;
3. reviewed fixture set;
4. error analysis;
5. per-mechanism benchmark report;
6. no unresolved confusion that makes its tag meaningless.

Add remaining intrinsic kernel in batches, not all at once.

## 46. Phase 6 — Instrument Alpha release

Includes:

- paste-text analysis;
- stable Alpha-0 intrinsic set;
- Lens and accessible fallbacks;
- pressure profile;
- fixture comparison/event record;
- public taxonomy/methodology;
- benchmark results;
- correction packet export/submission mechanism;
- no live broad aggregation requirement.

### Alpha release gate

- every production tag has a reviewed definition;
- every production detector has per-mechanism metrics;
- candidate/confirmed threshold behavior is documented;
- no claims of comprehensive fact-checking;
- UI can expose uncertainty without collapsing usability.

## 47. Phase 7 — Source registry and safe URL ingestion

Build after Instrument Alpha is credible.

- URL fetcher security;
- extraction adapters;
- source registry;
- metadata and rights handling;
- duplicate/syndication fingerprints;
- coverage disclosure.

### Acceptance

URL scanning adds convenience without changing intrinsic finding semantics.

## 48. Phase 8 — Event discovery

- event candidate retrieval;
- entity/time/semantic clustering;
- confidence;
- event merge/split internal tooling;
- coverage-gap tracking.

### Acceptance

Reviewed event fixtures cluster correctly and obvious unrelated stories stay separate.

## 49. Phase 9 — Source-dependence graph

- wire/syndication markers;
- text similarity;
- shared citations;
- chronology;
- uncertainty.

### Acceptance

Copied or common-origin articles do not count as independent confirmations without qualification.

## 50. Phase 10 — Claim extraction and alignment

- atomic claim extraction;
- attribution/speaker;
- semantic candidate retrieval;
- relation verification;
- alignment confidence;
- downstream-use threshold.

### Acceptance

Low-confidence alignments cannot produce strong omission or contradiction claims.

## 51. Phase 11 — Journalism cross-document kernel

Implement:

- Headline/body mismatch;
- Selective quotation;
- Material omission.

Each gets its own reviewed event-bundle benchmark.

### Acceptance

No omission is emitted without chronology, evidence, materiality dimension, and alignment trace.

## 52. Phase 12 — Evidence graph

- primary evidence retrieval;
- evidence-quality rubric;
- claim/evidence relations;
- strongest-evidence surfacing;
- contradiction state;
- retrieval-incomplete state;
- versioned Event Record.

### Acceptance

A dominant reporting account can visibly conflict with primary evidence without the system pretending the conflict is automatically resolved.

## 53. Phase 13 — News-Scale Beta

Full live journey:

URL -> readable article -> intrinsic findings -> Lens -> Compare -> peer excerpts -> omission -> claim evidence -> evolving Event Record.

### Beta release gate

- coverage disclosure works;
- source dependence is visible;
- omission chronology is enforced;
- claim alignment uncertainty is contained;
- evidence retrieval failures are explicit;
- benchmark includes cross-document mechanisms;
- privacy/rights/security policies reflect real behavior.

## 54. Phase 14 — Taxonomy expansion and novel-pattern research

Only after the bounded instrument is stable:

- add Batch-2 mechanisms through normal gates;
- collect uncategorized repeated patterns;
- cluster candidate novel patterns internally;
- require human taxonomy proposal before user-facing promotion.

Potential-harm analysis belongs in a separately governed later project phase so it cannot quietly redefine pressure.

---

# Part XI — Benchmark governance

## 55. Human review model

Each benchmark item carries independent annotations rather than forcing instant consensus.

Recommended states:

- agreed;
- majority with dissent;
- adjudicated;
- inherently contestable;
- taxonomy insufficient;
- invalid sample.

### 55.1 Annotator training

Annotators receive:

- mechanism definitions;
- near-miss examples;
- overlap rules;
- pressure anchors;
- voice-provenance rules;
- confidence guidance.

Training samples are separate from benchmark samples.

### 55.2 Taxonomy version migration

When a definition changes:

- old labels keep their taxonomy version;
- affected benchmark items are flagged for re-review;
- metrics are not compared across incompatible definition versions without migration notes.

## 56. Failure priority

Because the product is recall-biased:

1. track false negatives aggressively;
2. keep low-confidence candidates visible;
3. still report false positives by mechanism;
4. do not permit candidate noise to dominate profile summary;
5. optimize thresholds based on the real cost of each failure type, not one global number.

---

# Part XII — Corrections and criticism

## 57. Finding dispute packet

A user can dispute one finding without entering a social system.

Packet:

```text
analysis_run_id
finding_id
exact_span
current_mechanism
user_expected_mechanism_or_none
user_rationale
optional_evidence_refs
client_version
```

The user can copy/download this packet or submit it to maintainers when hosted submission exists.

No public voting determines whether a rhetorical mechanism is real.

## 58. Maintainer correction workflow

1. Triage: detector bug, taxonomy ambiguity, evidence error, alignment error, UI error, or disagreement.
2. Reproduce against source snapshot.
3. Add regression fixture when valid.
4. Repair smallest affected layer.
5. Re-run per-mechanism benchmark.
6. Publish change note when taxonomy or behavior changes materially.

Criticism improves the instrument by leaving evidence in the regression corpus.

---

# Part XIII — Security, privacy, rights

## 59. Privacy

- no account required for basic use where feasible;
- no ideological reader profile;
- minimize pasted-text retention;
- self-hosting supported;
- clearly disclose remote model processing if used;
- analytics disabled by default in self-hosted builds;
- no targeted advertising model.

## 60. Prompt/content injection defense

Article text is data, never instruction.

- strict model system/rubric boundaries;
- structured outputs;
- sanitization;
- no execution of article HTML/scripts;
- bounded context;
- detector prompts versioned and application-owned;
- hostile text cannot alter tool/network permissions.

## 61. Rights and quotation

- respect access controls;
- do not bypass paywalls;
- store full text only where user-supplied or rights permit;
- comparison excerpts are minimal and provenance-linked;
- source snapshot rights status is explicit;
- primary evidence has separate rights metadata;
- code/data/taxonomy licenses are independently documented.

A network-copyleft code license may be considered later if it matches governance goals, but it is not an implementation dependency.

---

# Part XIV — Open-source governance and documentation

## 62. Public methodology

Publish from the same versioned taxonomy data used by the application:

- mechanism definitions;
- criteria and exclusions;
- pressure rubrics;
- known confusion pairs;
- benchmark methodology;
- per-mechanism results;
- known failure modes;
- detector/version manifest;
- correction process.

Documentation should be generated or checked against taxonomy source so the website cannot drift into marketing claims unsupported by the implementation.

## 63. Change control

Taxonomy changes require:

- problem statement;
- examples;
- counterexamples;
- nearest-neighbor analysis;
- regression impact;
- benchmark migration plan;
- version bump.

Detector changes require benchmark diffs.

No political group or publication receives an exemption from analysis rules.

---

# Part XV — Observability

## 64. Technical metrics

- scan stage latency;
- article extraction failures;
- detector errors;
- candidate volume;
- detector disagreement;
- event cluster confidence;
- claim alignment confidence;
- evidence retrieval completion;
- UI runtime errors;
- lens frame performance;
- memory footprint for long articles.

## 65. Epistemic metrics

- false negative reports;
- false positive reports;
- mechanism confusion pairs;
- pressure disagreement;
- source-dependence corrections;
- omission disputes;
- claim-evidence contradiction errors;
- benchmark drift.

These should not be collapsed into a vanity "accuracy" metric.

---

# Part XVI — Exact Experience Prototype specification

## 66. Prototype goals

The standalone prototype distributed with this plan must prove:

1. article-first reading;
2. lens reveal;
3. multiple tags on one span;
4. pressure intensity vs confidence separation;
5. low-confidence visibility;
6. inspectable finding details;
7. pressure profile;
8. Compare-first result flow;
9. material omission demonstration;
10. coverage consensus vs primary evidence separation;
11. Event Record;
12. mobile/keyboard/reduced-motion design intent;
13. full implementation plan in the same file.

## 67. Prototype fixture

Use a fictional local-news event with fictional sources.

The fixture should include:

- a temporary public policy described as permanent by implication;
- a headline stronger than the body;
- a quoted speaker using fear rhetoric;
- an agentless sentence;
- a claim with overstated certainty;
- a missing expiration clause found in peer coverage and the fictional primary order;
- peer wording variations;
- one primary-evidence note that conflicts with dominant coverage;
- one low-confidence finding;
- one multi-tag phrase.

The prototype must label all source material as fictional demonstration content.

## 68. Prototype paste mode

The offline file may include a local heuristic scanner for user-pasted text.

It must clearly state:

- no network access;
- no real fact-checking;
- no peer search unless using the built-in fixture;
- heuristics are only to demonstrate interaction and finding structure.

The local heuristic scanner can identify a few obvious candidate patterns such as absolute certainty terms, false-dilemma markers, loaded terms, or agentless constructions. It should prefer honesty over pretending to be a production classifier.

## 69. Prototype views

### Scanner

- default active view;
- demo article;
- lens;
- finding markers;
- profile;
- paste mode.

### Compare

- "What this article does differently" cards;
- aligned claim/source excerpts;
- omission candidate;
- evidence conflict.

### Event Record

- atomic claims;
- support states;
- coverage consensus;
- primary evidence;
- rhetoric variants.

### Taxonomy

- Alpha-0 mechanism list and definitions.

### Plan

- full revised implementation plan;
- adversarial review;
- navigation/search/section collapse for usability.

---

# Part XVII — Quality gates

## 70. Engineering tests before benchmark

These tests validate software behavior, not rhetorical truth:

- schema validation;
- exact span mapping;
- no overlapping DOM corruption;
- multi-tag rendering;
- confidence/pressure independence;
- lens toggle/pin/reveal all;
- keyboard navigation;
- responsive layout;
- reduced motion;
- error states;
- comparison state transitions;
- event-record version display;
- source/evidence provenance links;
- security tests for URL fetcher when that phase exists.

## 71. Scientific/analytical tests after detector exists

- per-mechanism benchmark;
- multi-label recall;
- pressure agreement;
- calibration;
- cross-style robustness;
- quoted-speaker attribution;
- adversarial near misses;
- calm-false vs intense-true separation;
- event-bundle omission evaluation;
- claim alignment errors;
- source dependence.

## 72. Accessibility test matrix

Desktop keyboard, touch/mobile, screen reader semantics, reduced motion, zoom, high contrast/color perception, long article, dense findings, and empty/error states are separate test cases.

## 73. Release proof packet

Every release should generate:

- version manifest;
- benchmark report;
- known issues;
- taxonomy version;
- detector bundle version;
- UI regression results;
- source coverage limitations;
- rights/privacy changes;
- migration notes.

---

# Part XVIII — Final end-to-end build order

## 74. Beginning-to-end checklist

1. Create repository and operational-state file.
2. Commit product purpose and non-goals.
3. Define Article/Finding/Claim/Evidence/Event schemas.
4. Define taxonomy schema and mechanism IDs.
5. Build fictional event fixture.
6. Build article reading UI.
7. Build Lens interaction and Reveal All fallback.
8. Build multi-tag rendering.
9. Build finding detail drawer with structured transparency.
10. Build pressure profile.
11. Build Compare-first fixture UI.
12. Build omission/evidence conflict fixture.
13. Build Event Record fixture.
14. Run UX/accessibility/bug review on experience prototype.
15. Freeze Alpha-0 definitions for first four intrinsic mechanisms.
16. Build segmentation and voice provenance.
17. Build candidate generation.
18. Build structured contextual verifier.
19. Build reconciliation and pressure/confidence output.
20. Connect real findings to existing scanner UI.
21. Create first human-reviewed benchmark for implemented mechanisms.
22. Calibrate candidate/profile thresholds.
23. Repair errors and add regression fixtures.
24. Expand intrinsic taxonomy in gated batches.
25. Release Instrument Alpha with paste-text analysis and fixture comparison.
26. Build secure URL ingestion.
27. Build source registry and coverage disclosure.
28. Build event clustering.
29. Build source-dependence graph.
30. Build claim extraction/alignment.
31. Benchmark claim alignment independently.
32. Build journalism cross-document mechanisms.
33. Build material omission with chronology/materiality trace.
34. Build evidence retrieval and quality rubric.
35. Build evolving Event Record.
36. Run cross-document benchmark and adversarial event fixtures.
37. Run security/privacy/rights review.
38. Run full accessibility and runtime performance gate.
39. Release News-Scale Beta with explicit known limits.
40. Only then open novel-mechanism research and separate potential-harm design work.

---

# Part XIX — Definition of done

## 75. Experience Prototype done

The prototype is done when the entire article -> Lens -> Finding -> Compare -> Event Record -> Plan journey works offline, the interface exposes the approved semantics, and no control falsely claims live analysis capability.

## 76. Instrument Alpha done

Instrument Alpha is done when the bounded taxonomy actually produces real findings on real pasted article text, every production mechanism has a reviewed definition and per-mechanism benchmark, uncertainty is visible, multi-label behavior works, and the fixture-backed comparison experience remains intact.

## 77. News-Scale Beta done

News-Scale Beta is done when live URL ingestion and same-event comparison can support claim-level rhetorical comparison, event-time-aware omission, source-dependence-aware coverage consensus, evidence conflict, and a versioned Event Record without silently converting missing retrieval or uncertain alignment into factual certainty.

## 78. Project success criterion

Rhetorical InDEX is not successful because it produces more labels than a human can. It is successful when a reader can see language differently after using it: the scanner exposes pressure clearly enough that the user can recognize the same mechanics later without depending on the scanner.

The product remains an instrument, not a political authority. Its authority is limited to what it can show.


---

# Appendix A — Adversarial critique that produced this revision


The initial plan is directionally coherent, but coherence is not enough. It still contains several ways to build an impressive system that fails the actual product: a fast, inspectable instrument for ordinary readers. The review below treats every elegant abstraction as suspect until it proves that it helps the reader see interpretive pressure more clearly.

## 1. Twenty-five problems

1. **The "minimum effective" taxonomy is not minimal.** Twenty-plus mechanisms plus journalism-specific behaviors is enough surface area to create a mediocre classifier suite before any one detector becomes trustworthy.
2. **Several taxonomy items overlap semantically.** Loaded language, dysphemism, fear appeal, scapegoating, agency inflation, and causal overclaim can stack in ways the first plan does not precisely disambiguate, creating unstable multi-label output.
3. **Some labels are only fallacious in context.** Appeal to authority, anecdotal evidence, passive voice, and even emotionally charged language can be entirely appropriate. The plan risks converting technique detection into automatic condemnation.
4. **Interpretive-pressure levels are still descriptive rather than operational.** "Strong" and "extreme" sound sensible, but two reviewers could apply them differently because the plan lacks mechanism-specific observable features and scoring anchors.
5. **Recall bias could destroy usability.** Saying false negatives are worse does not remove the cost of false positives. A high-recall detector can paint every paragraph and train the user to ignore the instrument.
6. **The lens is visually clever but interactionally fragile.** Tags inside a clipped overlay may be difficult to click, line-wrap may drift, and touch users may cover the very text they are trying to inspect.
7. **The duplicated text-layer implementation could create accessibility and layout bugs.** Two copies of article text increase the risk of screen-reader duplication, selection weirdness, copy/paste confusion, scroll mismatch, and mobile reflow differences.
8. **Comparison infrastructure can swallow the scanner MVP.** Ingestion, clustering, source independence, claim alignment, evidence retrieval, and omission are each substantial systems. Building them as one early block would delay the core scanner indefinitely.
9. **The plan treats source coverage as if a broad corpus will simply exist.** A same-event comparator is only useful if source acquisition is broad enough, timely enough, and legally usable enough to avoid a distorted comparison set.
10. **"Strongest primary evidence" is underspecified.** Primary material can be authentic but incomplete, self-serving, superseded, decontextualized, or irrelevant to the exact claim. The initial plan has no evidence-quality rubric.
11. **The fact-check layer could become a hidden truth oracle.** Labels such as "contradicted" may look definitive even when the evidence retrieval system simply failed to find a relevant record or misread scope.
12. **Source independence is treated as a feature rather than a research problem.** Syndication, rewrites, shared press releases, common expert sources, and copying can create dependency that is difficult to infer from text similarity alone.
13. **Material omission is vulnerable to hindsight.** Later facts, later corrections, or facts unavailable at publication time can make an earlier article look deceptively incomplete unless event chronology is first-class.
14. **Materiality itself can become ideology by another name.** "Could change interpretation" is useful but broad. Without explicit dimensions and a reasoned materiality trace, maintainers can smuggle preferred context into omission findings.
15. **Claim alignment errors can poison everything downstream.** If two passages are incorrectly treated as the same claim, rhetoric comparison, contradiction, consensus, and omission all become confidently wrong together.
16. **The transparency promise is too close to "show all model reasoning."** The product needs inspectable decision evidence, not raw hidden reasoning or verbose post-hoc stories that sound explanatory but are not reproducible.
17. **Radical transparency can become radical cognitive overload.** Exact text, definition, rationale, alternative interpretation, evidence, provenance, model versions, peer excerpts, and confidence in one drawer can bury the actual finding.
18. **The plan lacks explicit performance budgets.** A scanner that takes forty seconds to analyze an ordinary article, drops frames under the lens, or loads a huge comparison bundle will not become part of ordinary reading.
19. **The plan does not define a cost budget.** Multi-stage language-model analysis across an article plus peers can make each scan expensive enough to sabotage a public-interest service.
20. **The benchmark arrives too late.** The user was right that there must be an instrument before a benchmark, but the initial sequence waits until the full intrinsic taxonomy exists. That allows detector mistakes to compound before disciplined measurement begins.
21. **The benchmark plan is missing annotation governance.** Two reviewers and adjudication are not enough; the plan needs uncertainty rules, disagreement preservation, annotator training, version migration, and a policy for inherently contestable cases.
22. **Quoted speech is not separated cleanly from reporter voice.** Flagging a politician's fear appeal inside a quotation as if the outlet authored it would be analytically misleading unless speaker and editorial framing are distinct.
23. **The plan lacks an explicit evolving-event model.** Claims can be true at 9:00, corrected at 11:00, and superseded by documents at 15:00. Static event records can turn update latency into false accusation.
24. **The open-source governance section is stronger than the correction workflow.** The plan says critics should improve the project but does not define how a user disputes one finding, what evidence is required, or how a correction changes the taxonomy/model without creating a popularity contest.
25. **The MVP exit criteria are still too broad.** URL ingestion, full Alpha-1 taxonomy, live event clustering, claim alignment, omission, primary evidence, benchmark, accessibility, rights, and open-source release in one "MVP" can easily become a multi-year wish list rather than a first shippable instrument.

## 2. Twenty-five targeted fixes

1. **Reduce the first instrument to a calibrated kernel.** Start Alpha-0 with 8–10 mechanisms chosen for high reader value and observable boundaries; add the rest only after a per-mechanism gate passes.
2. **Create a mechanism-confusion matrix before implementation.** Every mechanism definition must list nearest neighbors, overlap rules, and examples where two or more tags legitimately co-occur.
3. **Rename the detector contract from "fallacy detector" to "mechanism detector."** A finding states that a technique is present; evaluative language such as misleading is a separate evidence-backed judgment.
4. **Make pressure scoring feature-based.** Each mechanism gets observable intensity features and anchor examples for levels 1–4; UI explanations list which features fired.
5. **Use a two-threshold recall strategy.** Render low-confidence candidates by default inside the lens/findings list, but visually demote them and prevent them from inflating headline profile statistics until a lower calibration threshold is met.
6. **Separate lens reveal from tag activation.** The lens reveals color and compact markers; selecting a finding happens through a stable marker hit target, pinned lens, or synchronized list instead of relying on ephemeral clipped buttons.
7. **Use one semantic article DOM plus non-semantic annotation overlay.** Base text remains selectable and accessible; overlay is `aria-hidden`, pointer-neutral by default, and generated from measured ranges rather than a second accessible text tree.
8. **Split comparison into fixture-backed and live stages.** The first scanner ships with hand-authored event bundles to prove the comparison UX. Live ingestion/clustering is a later infrastructure milestone that cannot block instrument validation.
9. **Define corpus coverage as an explicit product metric.** Comparison UI must disclose peer-set size, source diversity, fetch gaps, and publication-time coverage instead of implying comprehensiveness.
10. **Add an evidence-quality rubric.** Primary evidence is scored by authenticity, directness to claim, completeness/context, temporal relevance, and independence from the party making the claim.
11. **Separate retrieval state from claim state.** "No supporting evidence found" is not "false." Contradiction requires a positive conflicting evidence relation and should expose the exact relation.
12. **Represent source dependence as a graph with uncertainty.** Use syndication markers, text overlap, citation chains, shared URLs, publication order, and common-origin clues; expose uncertain independence rather than forcing binary independent/not-independent.
13. **Make event time a required field on omission candidates.** A fact can only count as an omission if it was reasonably available at the target article's publication/update timestamp.
14. **Break materiality into explicit dimensions.** Agency, cause, scale, timeline, status, responsibility, consequence, denominator, and evidence quality become inspectable materiality reasons; no generic "important context" label is sufficient.
15. **Require alignment confidence before downstream use.** Low-confidence claim matches can be shown as candidates but cannot power contradiction or omission findings without confirmation by a second relation check.
16. **Publish structured decision traces, not hidden reasoning.** Show criteria, evidence, detector votes, span, alternatives, and rule/model versions. Never claim to expose private chain-of-thought.
17. **Use progressive disclosure.** Finding drawer opens with four essentials—what, where, pressure, confidence—then expandable sections for why, comparison, evidence, and provenance.
18. **Set performance budgets now.** Prototype: 60 fps lens target on ordinary desktop, <100 ms interaction response, no network. Production targets: first article text visible quickly, intrinsic findings streamed progressively, comparison can arrive later.
19. **Set a compute budget and tiered analysis.** Cheap deterministic/specialized passes retrieve candidates; expensive contextual judges run only on candidates or ambiguous cases. Cache by source snapshot and analysis version.
20. **Benchmark after the first vertical slice, then continuously.** Build 3–5 mechanisms, create the first reviewed corpus for those outputs, calibrate, then expand taxonomy in gated batches.
21. **Create annotation governance.** Store disagreement, reviewer certainty, adjudicator rationale, taxonomy version, and "inherently contestable" status; never force consensus where the concept itself is ambiguous.
22. **Model speaker provenance.** Every finding carries `voice = reporter | quoted_speaker | headline | caption | source_document`; comparison UI distinguishes outlet framing from rhetoric inside quoted material.
23. **Version event records over time.** Claims and evidence have valid-from/observed-at timestamps; the UI can show what was knowable when the article was published and what changed later.
24. **Build a bounded correction packet.** Users can export or submit one finding dispute containing exact span, expected classification, evidence, and rationale. It enters maintainer review, not public voting.
25. **Redefine release layers.** Prototype proves experience; Alpha proves the instrument on a bounded taxonomy; Beta adds live news-scale comparison/evidence. Do not call all three one MVP milestone.

## 3. Twenty-five additional polish improvements

1. Give each taxonomy mechanism a stable short ID so version migrations remain traceable even if display names change.
2. Add a "mechanism family" legend that remains available without occupying article space.
3. Show confidence through border style plus text, and pressure through fill strength plus a numeric/ordinal level so neither is color-only.
4. Add a compact article mini-map that marks pressure peaks without implying moral danger.
5. Allow the reader to pin one finding and move the lens elsewhere while the detail panel remains stable.
6. Add an "exact span" copy button in advanced mode for reproducible issue reports.
7. Add a finding permalink within a saved/exported scan snapshot.
8. Distinguish "not analyzed," "analyzed and no finding," and "analysis failed" states.
9. Include article genre metadata when confidently available: straight news, analysis, opinion, transcript, press release; never use genre as an exemption from rhetoric analysis.
10. Make headline analysis visually distinct because a headline has different rhetorical and space constraints than body prose.
11. Use paragraph-level lazy annotation rendering for long articles.
12. Add a keyboard command palette for Lens, Reveal All, Compare, Findings, and Event Record.
13. Provide a print/export stylesheet that renders findings as numbered footnotes rather than requiring the lens.
14. Add a provenance badge that opens analysis version information without placing model metadata in the main reading flow.
15. Make the comparison panel disclose the peer-set time window.
16. Show an explicit "coverage gap" indicator when known sources could not be fetched.
17. Preserve source excerpts exactly and visually distinguish source text from system normalization.
18. Display normalized claims in forensic language, but keep original wording one click away.
19. Add a "why peers disagree" slot for claim relation types rather than presenting disagreement as a flat contradiction.
20. Create regression fixtures specifically for factual prose with intense rhetoric and false prose with calm rhetoric to preserve the truth/rhetoric separation.
21. Create fixtures where multiple mechanisms overlap so multi-label behavior is deliberately tested rather than incidental.
22. Add synthetic source-laundering networks to test whether copied stories inflate consensus.
23. Make every production detector change generate a before/after benchmark diff by mechanism.
24. Keep analytics off by default in self-hosted builds and avoid any reader ideology inference entirely.
25. Add a public methodology page generated from the same versioned taxonomy records used by the scanner so documentation cannot silently drift away from implementation.

## 4. Revision verdict

The initial plan should **not** be implemented as written. Its product philosophy is strong, but its execution scope is too broad, its taxonomy too ambitious, its evidence semantics insufficiently constrained, and its first release definition too large.

The revised source of truth must therefore adopt five structural changes:

1. Three release layers: **Experience Prototype -> Instrument Alpha -> News-Scale Beta**.
2. A smaller **Alpha-0 mechanism kernel** with gated taxonomy expansion.
3. Fixture-backed comparison before live ingestion infrastructure.
4. Structured, layered transparency instead of an everything-at-once explanation dump.
5. Explicit error containment: low-confidence findings can be visible, but uncertain claim alignment, weak evidence retrieval, and incomplete peer coverage must not silently cascade into strong downstream judgments.

---

# Part XX — Tablet-safe scanner and internal engine contract

## 79. Tablet and coarse-pointer interaction contract

The scanner must not infer “touch device” from phone width. A tablet can be 768–1366 CSS pixels wide and still have a coarse primary pointer. The lens interaction therefore uses capability detection and responsive geometry together.

On a coarse-pointer device:

- the lens remains available at phone and tablet widths;
- a short tap on ordinary article text places the lens above the finger without preventing normal vertical scrolling;
- a dedicated scanner handle remains reachable while reading and can be dragged with pointer capture;
- the lens center is offset above the touch point so the finger does not conceal the inspected text;
- the lens radius is clamped to the available article geometry;
- portrait/landscape changes, `visualViewport` changes, and resize events recompute the lens safely;
- Lens, Pin, Reveal All, and size controls remain reachable from a compact touch control dock;
- the finding inspector becomes a bottom sheet at tablet/mobile/coarse-pointer layouts;
- tag stacks wrap and re-align instead of creating horizontal page overflow.

The touch path must coexist with scrolling. The article itself does not capture touch movement. Tap-to-place is recognized only when pointer travel stays below the tap threshold; continuous scanning is owned by the dedicated handle.

## 80. Current UI/UX capability set — 20 required behaviors

| ID | Required behavior |
|---|---|
| UI-01 | Tablet/coarse-pointer lens operation independent of phone breakpoint. |
| UI-02 | Tap-to-place lens on coarse pointers without hijacking vertical scroll. |
| UI-03 | Drag handle with above-finger offset and radius-aware bounds. |
| UI-04 | User-adjustable lens radius with device-appropriate limits. |
| UI-05 | Compact tablet/mobile scanner control dock. |
| UI-06 | Live scanner-state badge for Live, Pinned, Reveal All, and Off. |
| UI-07 | Sticky medium-width scanner controls. |
| UI-08 | Confidence filtering in the Findings list. |
| UI-09 | Mechanism-family filtering in the Findings list. |
| UI-10 | Findings search by mechanism or excerpt. |
| UI-11 | Synchronized selected state across list, passage, and inspector. |
| UI-12 | Jump-to-passage action from the finding inspector. |
| UI-13 | Tablet/mobile finding inspector presented as a bottom sheet. |
| UI-14 | Wrapped and edge-aligned overlapping tag stacks. |
| UI-15 | Collapsible mechanism legend. |
| UI-16 | Interactive paragraph pressure-map navigation. |
| UI-17 | In-scanner keyboard shortcut help. |
| UI-18 | In-product Reduced Motion preference. |
| UI-19 | Pattern/high-contrast annotation mode so family meaning is not color-only. |
| UI-20 | Restore-defaults control plus local/session settings-state feedback. |

These controls are interface support for the existing product contract. They do not add ideology scoring, potential-harm scoring, social features, or a generalized trust score.

## 81. Current prototype-engine capability set — 20 required behaviors

The standalone HTML has no remote server. Its “backend” for the Experience Prototype is therefore the internal analysis/data/state engine. Production services remain a later implementation layer.

| ID | Required engine behavior |
|---|---|
| ENG-01 | One versioned authoritative application-state object. |
| ENG-02 | Reducer-style `dispatch(action)` state transitions. |
| ENG-03 | `requestAnimationFrame` batching for derived UI updates. |
| ENG-04 | Runtime capability detection for pointer, hover, viewport class, and motion preference. |
| ENG-05 | Lens geometry engine with safe padding, radius-aware clamping, and touch offset. |
| ENG-06 | Geometry recomputation on visual viewport, resize, and orientation changes. |
| ENG-07 | Versioned validated settings persistence with malformed-storage fallback. |
| ENG-08 | Finding-schema normalization and validation. |
| ENG-09 | Article-schema normalization and finding-reference validation. |
| ENG-10 | Reusable indexes by ID, family, confidence, mechanism, and passage. |
| ENG-11 | Central derived metrics for peak pressure, confirmed/candidate density, and dominant families. |
| ENG-12 | Stable paragraph and segment IDs with paragraph-pressure records. |
| ENG-13 | Deterministic multi-mechanism local heuristic detection. |
| ENG-14 | Duplicate candidate suppression without collapsing repeated occurrences at different passages. |
| ENG-15 | Finding-to-passage location metadata for exact navigation. |
| ENG-16 | Central escaping/render-fragment rules for untrusted pasted text. |
| ENG-17 | Recoverable render/runtime error boundary. |
| ENG-18 | Active pointer ownership, `pointercancel`, and pointer-capture cleanup. |
| ENG-19 | Per-finding origin/detector/engine provenance metadata. |
| ENG-20 | Pre-render integrity audit for article/finding references and state invariants. |

## 82. Validation gate for this capability set

The capability set is not accepted from source presence alone. The release gate must include:

1. desktop pointer journey;
2. tablet portrait coarse-pointer journey;
3. tablet landscape coarse-pointer journey;
4. phone coarse-pointer journey;
5. lens tap placement, handle drag, pin/unpin, Lens Off, Reveal All, radius change, rotation/resize, and scroll coexistence;
6. finding search, family/confidence filtering, multi-tag inspection, jump-to-passage, pressure-map navigation, legend toggle, Pattern Mode, Reduced Motion, reset, and settings persistence;
7. local-paste multi-mechanism detection, safe escaping, comparison lockout, schema/integrity checks, and provenance display;
8. keyboard focus containment and shortcut behavior;
9. responsive overflow checks for Scanner, Compare, Event Record, Taxonomy, and Plan;
10. deterministic static checks, JavaScript syntax/heuristic inspection, accessibility/contrast review, offline-dependency check, bug resweep, and archive integrity.

A failed tablet lens path blocks release because the lens is the primary interaction metaphor, not optional decoration.

## 83. Medium-width layout and scanner measurement semantics

The responsive implementation treats medium-width touch layouts as a reading surface, not a compressed desktop dashboard. From 681 through 1100 CSS pixels, the scanner uses a full-width article column and moves support panels below it. The sticky scanner toolbar derives its top offset from the rendered primary navigation height so a two-row tablet header cannot cover the controls.

Lens-radius controls use one-pixel increments within device-specific bounds so the displayed value, persisted value, slider thumb, and clip geometry remain identical. Density metrics are allowed to reach 100% when every character-bearing segment is covered by the relevant confidence class; the profile must not artificially stop at 99%.

On coarse-pointer screens wider than the nominal tablet breakpoint, touch capability remains authoritative for interaction: the touch dock and drag handle stay available even when the visual layout has enough room for desktop-style columns.
