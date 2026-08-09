# Annotation Guide — Alpha-0, four-mechanism slice

Taxonomy version: `1.0.0-alpha0`. Mechanisms in scope: **Loaded language,
Presupposition, Agent suppression, False dilemma**. Ignore everything else; do
not annotate mechanisms outside this slice even when you can see them.

You are annotating **interpretive pressure**, not truth. A sentence can be
entirely accurate and still exert strong rhetorical pressure. Never let your
belief about whether a claim is *correct* influence whether you mark a
mechanism, or at what level.

There is no political axis in this task. If you find yourself reasoning about
which "side" a passage favours, stop — that reasoning has no place in the
output and will corrupt the corpus.

---

## 1. The span rule

**One annotation = one mechanism on one exact span.**

If a span exhibits three mechanisms, create three annotations with identical
coordinates. Never write a list of mechanisms into one annotation.

### Minimum span
The shortest contiguous text that carries the mechanism. For loaded language
this is usually the evaluative word plus the noun it colours
("draconian scheme"), not the whole sentence.

### Maximum span
Never extend past the sentence containing the mechanism. Never include a
trailing period, comma or closing quotation mark unless it is inside the
construction.

### Stacked terms
Consecutive evaluative terms modifying the same referent are ONE annotation:
`draconian, reckless scheme` — not three.

### Exactness
`excerpt` must equal `passages[passageOrdinal].text[startChar:endChar]`
character for character. The corpus validator rejects any mismatch.

---

## 2. Mechanism decision rules

### Loaded language
**Mark when:** a word choice imports evaluation the neutral alternative would
not (`scheme` for `plan`, `siphon` for `transfer`, `regime` for `government`).

**Do not mark when:**
- the term is technical or legal with a precise meaning (`felony`, `non-compliance`);
- it factually describes a physical event (`catastrophic earthquake`, `Category 5`);
- the emotional tone belongs strictly to a quoted speaker — still annotate it,
  but set `voiceClass: quoted_speaker`. **Do not skip quoted loading.** We need
  those cases to measure voice attribution.

**Confusion neighbours:** if the term specifically invokes *threat or danger*,
it may be Appeal to fear (out of scope — leave unannotated, and record
`isHardNegativeFor: ["loaded_language"]` if a detector would plausibly fire).

### Presupposition
**Mark when:** a disputed proposition is embedded as background such that
engaging with the sentence concedes it — factive verbs (`refused to explain
why X`), change-of-state verbs (`stopped doing X`), definite descriptions of
contested entities.

**Do not mark when:**
- the presupposed material is uncontested background (`since the earth orbits the sun`);
- the sentence explicitly attributes and hedges the premise (`what critics call
  a collapse`).

**Confusion neighbour:** if certainty is *asserted openly* rather than embedded
in syntax, that is Epistemic overstatement (out of scope).

### Agent suppression
**Mark when:** grammar removes a responsible actor — agentless passive
(`Mistakes were made`), nominalization (`the elimination of oversight`), or
agency assigned to an abstraction (`the policy caused suffering`).

**Do not mark when:**
- a `by [agent]` phrase names the actor **in the same sentence**;
- the actor is named in the immediately preceding sentence and the omission is
  ordinary grammatical ellipsis;
- the actor is genuinely unknown and the article says so.

**Judgement call:** passive voice is not automatically suppression. Ask: *would
naming the actor change perceived responsibility?* If no, do not annotate.

### False dilemma
**Mark when:** a situation with more than two available positions is presented
as a binary, foreclosing middle options.

**Do not mark when:**
- the binary is genuine (guilty/not guilty under a statute; a bill passes or fails);
- the surrounding text explicitly lists other options.

---

## 3. Pressure (P1–P4)

Use the **mechanism's own rubric** in `packages/taxonomy/taxonomy.json`, not a
generic sense of severity. Pressure answers: *how strongly does this mechanism
constrain interpretation here?*

- **P1** present but limited steering
- **P2** materially affects interpretation; alternatives stay salient
- **P3** substantially constrains interpretation, agency or certainty
- **P4** dominates the interpretive framing of the passage

Pressure is **not** confidence. If you are unsure the mechanism is present at
all, that goes in `reviewerConfidence`. A P4 you are unsure about is
`pressure: P4, reviewerConfidence: Low` — never P2 as a hedge.

---

## 4. Voice

Set `voiceClass` on every annotation:

| Value | Use when |
|---|---|
| `headline` | span is in a heading |
| `reporter` | outlet asserting in its own voice |
| `editorial` | explicitly labelled opinion/analysis |
| `quoted_speaker` | inside quotation marks attributed to a person |
| `paraphrased_source` | outlet reporting a source's position without quoting |
| `document_material` | quoted from a document, statute or transcript |
| `uncertain` | span straddles a quote boundary, or attribution is unclear |

Use `uncertain` freely. A confident wrong attribution is worse than an honest
`uncertain`, and we measure this dimension separately.

---

## 5. Hard negatives

Deliberately include passages that *look* like a mechanism and are not. Mark
them with `isHardNegativeFor` and a `nearMissRationale`. These are the most
valuable documents in the corpus — a benchmark of only obvious positives
measures nothing useful.

An article with zero annotations is a legitimate, valuable document. Submit it.

---

## 6. Disagreement

Do not resolve disagreement by discussion before recording it. Annotate
independently, then record every disagreement in `disagreements[]`. Adjudication
(see `ADJUDICATION.md`) resolves it afterwards, and the original positions stay
in the file permanently — inter-annotator disagreement is the calibration
signal, and erasing it destroys information we cannot recover.

If you cannot decide between two mechanisms, annotate your best choice and set
`alternativeAcceptableMechanism`.

---

## 7. Before submitting

- [ ] every `excerpt` round-trips exactly against its passage
- [ ] one mechanism per annotation
- [ ] no annotation crosses a sentence boundary
- [ ] `pressure` set from the mechanism's rubric, not a generic feel
- [ ] `reviewerConfidence` reflects presence-uncertainty only
- [ ] `voiceClass` set, `uncertain` where genuinely unclear
- [ ] hard negatives recorded with rationale
- [ ] `adjudicationStatus` left at `annotated` (adjudicators set `adjudicated`)
