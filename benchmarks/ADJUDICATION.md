# Adjudication Protocol

Only documents with `adjudicationStatus: "adjudicated"` are scored. This
protocol is how a document gets there.

## 1. Independence first

Each document is annotated by **at least two annotators working independently**.
Annotators must not see each other's spans before both submissions are recorded.
A corpus built by consensus-during-annotation systematically overstates
agreement and produces a benchmark that flatters the detector.

## 2. Automatic merge

Two annotations merge without adjudication when **all** hold:

- same `mechanismId`
- same `passageOrdinal`
- span IoU ≥ 0.8
- same `pressure`
- **same `voiceClass`**
- **same `reviewerConfidence` band is NOT required** (confidence is a per-annotator
  epistemic report, not a property of the span, and is preserved rather than merged)

Review finding M-11: `voiceClass` was previously absent from the auto-merge
conditions while §3 simultaneously listed voice disagreement as grounds for
escalation — the protocol contradicted itself, and auto-merge would have
silently discarded a voice disagreement. Voice now blocks automatic merge.
Anything not in this list escalates.

The merged span takes the **intersection** of the two spans (the text both
annotators agreed carries the mechanism). Record both original spans in
`disagreements[]` when the IoU is below 1.0.

Review finding C-02: the validator previously treated a gold annotation as
auto-merged if it matched **any one** preserved proposal. That is not
consensus — it is evidence that a single annotator proposed it. One annotator
proposing a finding the other did not is a *presence disagreement* (§3), and a
pressure or voice difference is likewise an escalation trigger, so none of
those may auto-merge. `benchmarks/scripts/validate_corpus.py` now requires
proposals from at least two distinct annotators agreeing on mechanism,
passage, pressure and voice with pairwise span IoU ≥ 0.8, and requires the
gold span to equal the intersection exactly.

**Three or more annotators.** Every preserved proposal matching the gold's
mechanism, passage, pressure and voice forms the agreeing set. That set must
cover at least two distinct annotators, **every pair** in it must clear the
IoU threshold, and the merged span is the intersection over the whole set.
A proposal differing on pressure or voice is simply not in the set, which is
exactly why those disagreements fall through to "adjudication required".

## 3. Everything else goes to an adjudicator

Escalate when annotators disagree on:

- presence (one marked it, one did not)
- mechanism identity
- span by more than IoU 0.2
- pressure by more than one level
- voice class

The adjudicator is a third person who has not annotated the document.

## 4. Adjudicator decisions

The adjudicator must choose exactly one:

| Decision | Meaning |
|---|---|
| `uphold_a` / `uphold_b` | one annotator was right |
| `merge` | both correct, spans reconciled |
| `drop` | neither is defensible under the taxonomy |
| `split` | genuinely two mechanisms; becomes two annotations |
| `adjudicator_add` | the adjudicator identifies a finding **neither annotator proposed** (see §7b) |
| `unresolvable` | the taxonomy does not decide this case |

`unresolvable` is a legitimate outcome and **must not be forced**. It is a
finding about the taxonomy, not about the annotators.

`adjudicator_add` is deliberately rare and deliberately explicit. A
third-party adjudicator reviewing the whole article may sometimes notice
something neither original annotator flagged — that is a legitimate part of
adjudication, not a defect in it — but it must never happen silently. See §7b
for exactly what a valid `adjudicator_add` resolution requires.

## 5. Unresolvable cases are taxonomy defects

Every `unresolvable` case is logged as a taxonomy issue with the exact span.
If a criterion cannot be applied consistently by trained annotators, the
criterion is the problem — not the annotators. Fix the taxonomy record
(definition, criteria, exclusions or confusion neighbours), bump the taxonomy
version, and re-adjudicate affected documents.

Documents containing unresolved `unresolvable` annotations stay at
`adjudicationStatus: "disputed"` and are **excluded from scoring**.

## 6. Pressure disagreement

Adjacent-level disagreement (P2 vs P3) is resolved by the adjudicator citing the
specific rubric anchor sentence from the mechanism's `pressureRubric`. If the
anchor does not decide it, the anchor is underspecified — log it as a taxonomy
issue.

Two-level disagreement (P1 vs P3) is treated as a presence disagreement: the
annotators are not seeing the same thing.

## 7. Preservation rule

Adjudication **never deletes** the original annotator positions.

Review finding M-12: a free-text `disagreements[]` note was too lossy to
reconstruct what each annotator actually proposed, so the protocol's promise
that agreement stays computable was not true. The format now separates:

| Field | Contains |
|---|---|
| `annotatorSubmissions[]` | one RECORD per annotator (`submissionId`, `annotatorId`, `proposals[]`), preserved verbatim and never overwritten |
| `annotations[]` | the adjudicated GOLD result |
| `resolutions[]` | which proposals produced which gold annotation, and the adjudicator's decision |

`annotatorSubmissions[]` holds one entry per annotator, not one entry per
proposal. Each entry's `proposals[]` array holds that annotator's original
findings and — critically — **may be empty**. An empty `proposals[]` is not
missing data; it is the annotator's own record that they independently
reviewed the article and found nothing. This is what makes a genuine hard
negative representable: two annotators, two preserved records, both with
`proposals: []`, is valid adjudicated gold. What is invalid is having *fewer
than two records*, regardless of how many proposals they contain — finding B
of the pre-calibration audit (A-02) was exactly this: an implementation that
counted non-empty proposal lists let `annotatorSubmissions: []` (or the field
missing outright) silently bypass the preservation requirement, because an
empty list and a missing list looked the same to that check. The fix is
structural: the thing being counted is submission *records*, never proposals,
so an empty `proposals[]` inside a real record no longer reads as "nothing was
preserved."

`annotatorSubmissions[]` is append-only and is **never** overwritten by
adjudication. This makes presence, mechanism, span, pressure and voice agreement
all computable from the file itself after the fact.

`benchmarks/scripts/validate_corpus.py` enforces that adjudicated documents
carry a preserved submission record from at least two distinct annotators
(each `submissionId` and `proposalId` globally unique, each `annotatorId`
agreeing with `annotatorIds`), and that every preserved proposal round-trips
against its passage.

## 7b. Every final gold outcome must have machine-readable provenance

Finding B-04 of the final edge-invariant closure: nothing previously stopped
`annotations[]` from containing a finding that traced back to nothing at
all — no matching proposal, no resolution record, no adjudicator name. A
corpus could silently accumulate gold that no annotator or adjudicator could
actually be shown to have produced.

The rule now enforced: a gold annotation is valid only if it is grounded in
**one** of two ways.

1. **Genuine auto-merge** (§2) — at least two distinct annotators
   independently proposed the same mechanism on the same passage with the
   same pressure and the same voice, pairwise span IoU ≥ 0.8, and the gold
   span is exactly the intersection. Needs no resolution record; that is the
   point of §2. (C-02 corrected this: it previously accepted a match against
   any single proposal, which is one annotator's opinion, not consensus.)
2. **An explicit resolution** — exactly one `resolutions[]` record whose
   `resultingAnnotationIds` names it. Required for everything else: a
   presence, pressure, voice or mechanism disagreement, a span adjustment, a
   `merge`, a `split`, or an `adjudicator_add`.

A gold annotation grounded **both** ways, or named by two resolutions, is an
error — provenance is exactly one record per outcome.

### Resolution cardinality (finding C-03)

`resultingAnnotationIds` is an **array**. The previous singular
`resultingAnnotationId` could not represent a `split`, which by definition
produces more than one annotation; the singular key is now rejected outright
so an old-format record can never look grounded. Each decision has a fixed
shape:

| Decision | `proposalIds` | `resultingAnnotationIds` |
|---|---|---|
| `uphold_a` / `uphold_b` | exactly 1 | exactly 1 |
| `merge` | ≥ 2, from ≥ 2 **distinct annotators** | exactly 1 |
| `drop` | ≥ 1 | exactly 0 |
| `split` | ≥ 1 | ≥ 2 |
| `adjudicator_add` | exactly 0 | exactly 1 |
| `unresolvable` | — | never allowed in an adjudicated document |

Without these bounds, `merge` with an empty `proposalIds` grounded arbitrary
gold with no proposal origin at all — a silent backdoor around
`adjudicator_add`, which exists precisely to make that case explicit and
attributable. Requiring a merge to draw on two *distinct* annotators also
stops one annotator's own overlapping proposals being consolidated and
presented as agreement.

Every resolution record is additionally validated:

- `resolutionId`, if present, is unique.
- `adjudicatorId` is **required and non-empty** — a resolution is by
  definition an adjudicator's decision, and the adjudicator must be named.
- every id in `proposalIds` must reference a real preserved proposal, and
  every id in `resultingAnnotationIds` a real entry in `annotations[]` —
  including when the document has zero real proposals (a resolution cannot
  invent a proposal to point at just because there are none to check
  against).
- `adjudicator_add` must carry a non-empty `note` or `rationale` explaining
  what the adjudicator saw and why.

This closes the gap a mechanical validator can actually close. It does not
try to detect every case where an adjudicator *should* have escalated a
disagreement instead of quietly upholding one side — that remains a human
judgment the protocol asks for in §3, not something span/mechanism matching
can verify. What it does guarantee is that nothing reaches gold status
without either genuine recorded two-annotator agreement, or a named
adjudicator and a decision whose shape matches what it claims to have done.

## 8. Promotion checklist

Before setting `adjudicationStatus: "adjudicated"`:

- [ ] ≥ 2 independent annotators recorded in `annotatorIds`
- [ ] every escalated disagreement has an adjudicator decision
- [ ] no `unresolvable` annotations remain (else status stays `disputed`)
- [ ] every `excerpt` round-trips exactly against its passage
- [ ] `disagreements[]` retained in full
- [ ] taxonomy version recorded and matches the version annotated against
- [ ] every gold annotation is either a genuine two-annotator auto-merge (§2)
      or has exactly one `resolutions[]` record naming it and the adjudicator,
      with a decision-consistent cardinality (§7b)

## 9. Re-adjudication on taxonomy change

A semantic change to a mechanism's definition, criteria or rubric invalidates
annotations made against the previous version. Those documents drop to
`disputed` until re-adjudicated. Metrics computed across mixed taxonomy versions
are not comparable and must not be reported as a trend.
