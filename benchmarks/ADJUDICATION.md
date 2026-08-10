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
those may auto-merge.

**Auto-merge requires UNANIMITY (finding D-02).** Requiring merely "at least
two agreeing annotators" was still wrong once a document had three or more:
A and B agreeing while C proposed a different pressure, a different voice, or
nothing at all still auto-merged on the strength of A+B, discarding exactly
the dissent the corpus exists to preserve. The enforced rule is now:

- **every** annotator declared in `annotatorIds` must contribute **exactly
  one** qualifying proposal to the consensus cluster;
- all of them must agree on `mechanismId`, `passageOrdinal`, `pressure` and
  `voiceClass` (`reviewerConfidence` need not match);
- **every pair** of their spans must reach IoU ≥ 0.8;
- the gold span must equal the intersection across **all** participants.

Any missing proposal, any extra ambiguous matching proposal from the same
annotator, any pressure/voice/mechanism dissent, or any sub-threshold span
disagreement means **adjudication is required**.

This is deliberately stricter than majority vote. At Alpha, conservative
escalation is preferable to silently erasing a dissenting annotator: an
escalated case costs an adjudicator's time, whereas an erased dissent
corrupts the calibration signal permanently and invisibly.

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
error — provenance is exactly one record per outcome. Finding D-03: this was
documented but not enforced, so a document could label gold that both
annotators had in fact proposed identically as an `adjudicator_add` ("nobody
proposed this"), misrepresenting where the finding came from. Both origins
are now computed for every annotation and checked against a closed table:

| auto-merge origin | resolution links | verdict |
|---|---|---|
| yes | 0 | **valid** — uncontested auto-merge |
| no | 1 | **valid** — adjudicated |
| no | 0 | rejected: ungrounded |
| yes | ≥ 1 | rejected: conflicting provenance |
| no | > 1 | rejected: duplicate provenance |

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
- `adjudicatorId` is **required, non-empty, and must NOT appear in
  `annotatorIds`** — §3 says the adjudicator is a third person who has not
  annotated the document, and finding D-01's companion check now enforces it.
  An annotator adjudicating their own disagreement can manufacture consensus
  single-handed.
- every id in `proposalIds` must reference a real preserved proposal, and
  every id in `resultingAnnotationIds` a real entry in `annotations[]` —
  including when the document has zero real proposals (a resolution cannot
  invent a proposal to point at just because there are none to check
  against).
- `adjudicator_add` must carry a non-empty `note` or `rationale` explaining
  what the adjudicator saw and why.

### The result must derive from the cited proposals (finding D-01)

Reference-existence and cardinality prove only that a resolution points at
real records — not that its gold has anything to do with them. An `uphold_a`
citing a `loaded_language` proposal could emit a `false_dilemma` annotation on
an unrelated span; a `merge` or `split` could manufacture findings elsewhere
in the article entirely. An "uphold" that silently substitutes a different
finding is not an uphold. The enforced relationships:

| Decision | Required source → result relationship |
|---|---|
| `uphold_a` / `uphold_b` | the gold **exactly preserves** the cited proposal's `mechanismId`, `passageOrdinal`, `startChar`, `endChar`, `pressure` and `voiceClass`. `reviewerConfidence` may differ — it is a per-annotator epistemic report, not a property of the phenomenon. |
| `merge` | sources share one `passageOrdinal` and one `mechanismId` **and a non-empty common span intersection** (`max(starts) < min(ends)`); the gold uses that same passage and mechanism, overlaps that common intersection, and does not extend beyond the outer bounds of the cited spans. Pressure and voice may be chosen by the adjudicator (that is often the disagreement being reconciled); the originals stay preserved in `annotatorSubmissions`. |
| `split` | **every** resulting annotation is **wholly contained** in one connected component of the cited source coverage **on its own passage**, and **every** cited proposal is overlapped by at least one result on its own passage. A split may legitimately yield different `mechanismId`s — it may not relocate, extend past, or bridge across the text the annotators marked. |

**Span provenance is per-span and per-passage (finding E-01/E-02).** Two
weaker forms were rejected:

- A `split` must not be validated against a global bounding hull
  `min(start)..max(end)`. Sources at 0..10 and 90..100 produce a "region" of
  0..100, which would bless an unrelated result at 40..50 sitting in the gap
  between them; and because a hull discards `passageOrdinal`, coordinates from
  one passage could numerically vouch for a result on another. Unrelated gap
  text can never become a split result, and a cited proposal that no result
  represents is an incomplete split.
- A `merge` must not be validated by overlapping the gold against each source
  independently. Two *disjoint* findings both overlap a bridging gold span, so
  0..10 and 90..100 would license a gold of 5..95 swallowing eighty characters
  of unrelated text. Disjoint cited spans are separate occurrences and need
  separate resolutions; a merge reconciles **one** shared occurrence.

**Auto-merge clustering is occurrence-local.** A proposal only joins the
consensus cluster for a gold annotation if it actually overlaps that gold.
Matching on mechanism/passage/pressure/voice alone swept in every other
occurrence of the same mechanism in the same passage, so a passage with two
distinct P3/reporter `loaded_language` findings looked ambiguous when the two
findings were never in competition. Genuinely competing proposals — two from
the same annotator both overlapping the same gold — still escalate.
| `drop` | no resulting gold at all. |
| `adjudicator_add` | no source proposals, exactly one result, an independent named adjudicator, and a rationale. This remains the **only** path to entirely new gold with no proposal origin. |

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
- [ ] every gold annotation is either a **unanimous** auto-merge of every
      declared annotator (§2) or has exactly one `resolutions[]` record naming
      it, never both (§7b truth table)
- [ ] every resolution's result actually derives from the proposals it cites
- [ ] no `adjudicatorId` appears in `annotatorIds`
- [ ] `annotatorIds` are ≥ 2 unique non-empty strings matching the preserved
      submission annotators exactly

## 9. Re-adjudication on taxonomy change

A semantic change to a mechanism's definition, criteria or rubric invalidates
annotations made against the previous version. Those documents drop to
`disputed` until re-adjudicated. Metrics computed across mixed taxonomy versions
are not comparable and must not be reported as a trend.
