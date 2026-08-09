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

Adjudication **never deletes** the original annotator positions. `disagreements[]`
is append-only and survives into the scored document. Inter-annotator agreement
is a headline property of the corpus and must remain computable from the files
themselves after the fact.

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
