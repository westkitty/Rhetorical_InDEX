# Instrument Alpha — Architecture

## Layout

```
apps/web/                 Level 2 browser scanner (TypeScript, dependency-light)
packages/
  schema/                 Canonical contracts — schema.json is the single source
    schema.json           Controlled vocabulary + required-field contracts
    src/contracts.ts      TypeScript bindings (verified against schema.json)
    src/localPreviewContract.ts  Level 2 validation boundary
  taxonomy/taxonomy.json  12 mechanism records (canonical mechanism id list)
  fixtures/               Synthetic SB-802 event, example.invalid provenance
services/
  rhetoric/               Level 3 detector pipeline  <-- the substantive addition
  comparison/             Claims, alignment, material omission gates, dependence
  evidence/               Evidence items, relations, authenticity, ranking
  api/
    detector_contract.py  Strict intrinsic validation boundary
    analyze.py            Local network-free orchestration + CLI
benchmarks/               Machinery only; corpus is empty
tests/
  *.test.mjs              Node: artifact, fixture, taxonomy, vocabulary, security
  python/unit/            Document, voice, scoring, validation, coverage, schema
  python/integration/     Pipeline, comparison/evidence, benchmark harness
  python/adversarial/     Deliberate attacks
  prototype-parity/       PARITY_MATRIX.md
```

## Dependency direction

```
schema.json  (canonical, depends on nothing)
     |
     +--> contracts.ts, localPreviewContract.ts   (TypeScript)
     +--> rhetoric/vocabulary.py                  (Python)
     +--> api/detector_contract.py                (Python)
                    |
taxonomy.json ------+--> rhetoric/{candidates,scoring,providers,validation}
                              |
                              +--> rhetoric/pipeline --> api/analyze
                                                          |
comparison/ (imports rhetoric.vocabulary only) <----------+
evidence/   (imports rhetoric.vocabulary only)
```

No cycles. `services/comparison` and `services/evidence` depend on the shared
vocabulary, never on the detector pipeline — comparison must remain possible
without running a detector, and the detector must remain possible without a
comparison set.

`apps/web` depends on `packages/*` only. It does not depend on `services/*`,
which is why Level 3 is not reachable from the browser build.

## Why no cross-language duplication

`packages/schema/schema.json` is the only place the controlled vocabulary is
written. Both languages *read* it:

- Python (`vocabulary.py`, `detector_contract.py`) loads it at import time
- TypeScript declares literal unions, verified against it by
  `tests/vocabulary-parity.test.mjs`
- The build embeds it into `window.RI_BOOTSTRAP.vocabulary`

Drift is impossible by construction on the Python side and test-detected on the
TypeScript side. `tests/python/test_vocabulary_parity.py` checks Python's
runtime values; the Node suite additionally asserts TypeScript and Python agree
*with each other*, not merely with the file.

The 12-mechanism id list lives only in `taxonomy.json` and is deliberately not
duplicated into `schema.json`.

## Coordinate convention

**All span coordinates are passage-local.** There is no document-global offset
space. A `Finding` addresses `(passageId, startChar, endChar, occurrenceIndex)`,
and `passage.text[startChar:endChar] == excerpt` is enforced at validation and
asserted in tests. One convention removes an entire class of reconciliation bugs.

## Identity

| Object | Rule |
|---|---|
| `contentHash` | SHA-256 over canonical `(passageType, text)` serialization |
| `articleId` | `art-{contentHash[:16]}` unless supplied |
| `passageId` | `{articleId}:p{ordinal:04d}` |
| `runId` | SHA-256 of `(contentHash, detectorVersion, providerId, salt)` |
| `findingId` | SHA-256 of `(runId, passageId, mechanismId, start, end, occurrence)` |

All derived from inputs — no clock, no RNG. The same article analyzed by the
same build is byte-reproducible, which the benchmark harness depends on.

## Trust boundaries

1. **Article text is untrusted.** Escaped at render (`esc`), never executed.
   Hostile payloads tested in `tests/security.test.mjs`.
2. **Provider output is untrusted.** Every verdict passes `validate_verdict`;
   every finding passes `validate_finding_payload`. Swapping providers cannot
   widen what is accepted.
3. **Comparison material carries provenance.** `ComparisonSet.provenanceKind`
   distinguishes `synthetic_fixture` from `retrieved`; synthetic omissions are
   labelled on the output object.

## Deferred by design

URL ingestion · HTTP listener · model transport · evidence retrieval ·
event discovery · source registry · production persistence.

`ModelDetectorProvider` implements prompt construction and strict response
parsing but no transport. Without credentials it raises `ProviderUnavailable`,
which surfaces as a `DetectorFailure` and a failed run — never as a fabricated
verdict.
