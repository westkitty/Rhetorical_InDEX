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
| `unresolvable` | the taxonomy does not decide this case |

`unresolvable` is a legitimate outcome and **must not be forced**. It is a
finding about the taxonomy, not about the annotators.

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

## 8. Promotion checklist

Before setting `adjudicationStatus: "adjudicated"`:

- [ ] ≥ 2 independent annotators recorded in `annotatorIds`
- [ ] every escalated disagreement has an adjudicator decision
- [ ] no `unresolvable` annotations remain (else status stays `disputed`)
- [ ] every `excerpt` round-trips exactly against its passage
- [ ] `disagreements[]` retained in full
- [ ] taxonomy version recorded and matches the version annotated against

## 9. Re-adjudication on taxonomy change

A semantic change to a mechanism's definition, criteria or rubric invalidates
annotations made against the previous version. Those documents drop to
`disputed` until re-adjudicated. Metrics computed across mixed taxonomy versions
are not comparable and must not be reported as a trend.
