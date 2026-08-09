"""Level 3 Instrument Alpha detector — pipeline orchestration.

Stage order (implementation plan §22):
   1 input normalization        -> document.normalize_text
   2 passage segmentation       -> document.segment
   3 candidate generation       -> candidates.generate
   4 context assembly           -> context.assemble
   5 mechanism classification   -> providers.DetectorProvider.verify
   6 exact span localization    -> validation.resolve_span
   7 pressure classification    -> scoring.score_pressure
   8 confidence classification  -> scoring.score_confidence
   9 voice provenance           -> voice.classify (via context)
  10 structured validation      -> validation.validate_finding_payload
  11 span reconciliation        -> models.dedupe_findings
  12 finding creation           -> models.Finding
  13 coverage accounting        -> models.AnalysisRun
  14 run finalization           -> AnalysisRun.finalize

Calibration status: this pipeline is STRUCTURALLY complete and UNCALIBRATED.
No benchmark has been run against it, so no accuracy claim is made anywhere in
the code, the UI or the documentation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from . import candidates as candidates_module
from . import context as context_module
from . import scoring
from . import vocabulary as vocab
from .document import Article, Passage, segment
from .models import (
    AnalysisRun,
    Finding,
    batch_passages,
    dedupe_findings,
    make_finding_id,
    make_run_id,
)
from .providers import DetectorProvider, ProviderUnavailable, Verdict, default_provider
from .validation import (
    DETECTOR_SCHEMA_VERSION,
    DetectorFailure,
    DetectorRejection,
    validate_finding_payload,
    validate_verdict,
)

DETECTOR_VERSION = "instrument-alpha-l3-0.1.0"
DEFAULT_BATCH_SIZE = 25

# The implemented Level 3 slice. Deliberately four mechanisms, not twelve.
IMPLEMENTED_MECHANISMS: frozenset[str] = vocab.INTRINSIC_ALPHA_SLICE


@dataclass
class AnalysisResult:
    run: AnalysisRun
    article: Article
    findings: tuple[Finding, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run": self.run.to_dict(),
            "article": self.article.to_dict(),
            "findings": [f.to_dict() for f in self.findings],
        }

    def findings_for_passage(self, passage_id: str) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.passage_id == passage_id)

    @property
    def coverage_is_complete(self) -> bool:
        return self.run.is_complete_coverage


def analyze_text(
    raw_text: str,
    *,
    provider: DetectorProvider | None = None,
    mechanisms: Iterable[str] | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    started_at: str | None = None,
    completed_at: str | None = None,
    run_salt: str = "",
    article_id: str | None = None,
    **article_metadata: Any,
) -> AnalysisResult:
    """Segment and analyze raw text end to end."""
    article = segment(raw_text, article_id=article_id, **article_metadata)
    return analyze_article(
        article,
        provider=provider,
        mechanisms=mechanisms,
        batch_size=batch_size,
        started_at=started_at,
        completed_at=completed_at,
        run_salt=run_salt,
    )


def analyze_article(
    article: Article,
    *,
    provider: DetectorProvider | None = None,
    mechanisms: Iterable[str] | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    started_at: str | None = None,
    completed_at: str | None = None,
    run_salt: str = "",
) -> AnalysisResult:
    active_provider = provider or default_provider()
    requested = frozenset(mechanisms) if mechanisms is not None else IMPLEMENTED_MECHANISMS

    unsupported = requested - IMPLEMENTED_MECHANISMS
    if unsupported:
        raise ValueError(
            f"mechanisms outside the implemented Level 3 slice: {sorted(unsupported)}"
        )

    run = AnalysisRun(
        run_id=make_run_id(
            content_hash=article.content_hash,
            detector_version=DETECTOR_VERSION,
            provider_id=active_provider.provider_id,
            salt=run_salt,
        ),
        article_id=article.article_id,
        content_hash=article.content_hash,
        taxonomy_version=vocab.taxonomy_version(),
        detector_version=DETECTOR_VERSION,
        provider=active_provider.describe(),
        all_passage_ids=article.passage_ids,
        started_at=started_at,
    )

    collected: list[Finding] = []
    for batch_index, batch in enumerate(batch_passages(article.passage_ids, batch_size)):
        batch_record: dict[str, Any] = {
            "batchIndex": batch_index,
            "passageIds": list(batch),
            "status": "complete",
            "findingCount": 0,
        }
        batch_findings: list[Finding] = []
        batch_failed = False

        for passage_id in batch:
            passage = article.passage(passage_id)
            try:
                passage_findings = _analyze_passage(
                    article, passage, run, active_provider, requested
                )
            except ProviderUnavailable as exc:
                # An unavailable provider fails the passage honestly. It does
                # NOT produce a finding, and the run becomes partial/failed.
                run.failed_passage_ids.append(passage_id)
                run.failures.append(
                    DetectorFailure(
                        passage_id=passage_id,
                        stage="contextual_verification",
                        reason=f"provider unavailable: {exc}",
                    )
                )
                batch_failed = True
                continue
            except Exception as exc:  # noqa: BLE001 - deliberate service boundary
                # A provider bug must not destroy the whole analysis. The
                # failure is recorded (never swallowed): it appears in
                # run.failures, marks the passage failed, and downgrades the run
                # to partial/failed so no consumer can mistake this for a clean
                # scan. Losing one passage honestly beats losing the run.
                run.failed_passage_ids.append(passage_id)
                run.failures.append(
                    DetectorFailure(
                        passage_id=passage_id,
                        stage="provider_error",
                        reason=f"{type(exc).__name__}: {exc}",
                    )
                )
                batch_failed = True
                continue

            batch_findings.extend(passage_findings)
            run.processed_passage_ids.append(passage_id)

        collected.extend(batch_findings)
        batch_record["findingCount"] = len(batch_findings)
        if batch_failed:
            batch_record["status"] = "partial" if batch_findings else "failed"
        run.batches.append(batch_record)

    findings = tuple(dedupe_findings(collected))
    run.finding_count = len(findings)
    run.finalize(completed_at=completed_at)

    if not run.is_complete_coverage:
        run.warnings.append(
            f"Coverage incomplete: {len(run.processed_passage_ids)}/{len(run.all_passage_ids)} "
            f"passages analyzed. Findings shown are from analyzed passages only."
        )

    return AnalysisResult(run=run, article=article, findings=findings)


def _analyze_passage(
    article: Article,
    passage: Passage,
    run: AnalysisRun,
    provider: DetectorProvider,
    mechanisms: frozenset[str],
) -> list[Finding]:
    """Run stages 3-12 for one passage.

    ProviderUnavailable propagates (the passage failed). Every other rejection
    is recorded as a DetectorFailure and drops only that candidate: one bad
    candidate must not discard an entire passage's legitimate findings.
    """
    produced: list[Finding] = []

    for candidate in candidates_module.generate(passage, mechanisms):
        try:
            ctx = context_module.assemble(article, passage, candidate)
        except ValueError as exc:
            run.rejected_candidate_count += 1
            run.failures.append(
                DetectorFailure(
                    passage_id=passage.passage_id,
                    stage="context_assembly",
                    reason=str(exc),
                    mechanism_id=candidate.mechanism_id,
                    excerpt=candidate.excerpt,
                )
            )
            continue

        verdict: Verdict = provider.verify(ctx)

        try:
            validate_verdict(
                verdict, mechanism_id=candidate.mechanism_id, passage_id=passage.passage_id
            )
        except DetectorRejection as exc:
            run.rejected_candidate_count += 1
            run.failures.append(
                DetectorFailure(
                    passage_id=passage.passage_id,
                    stage=exc.stage,
                    reason=exc.reason,
                    mechanism_id=candidate.mechanism_id,
                    excerpt=candidate.excerpt,
                )
            )
            continue

        if verdict.applies == "no":
            continue

        pressure = scoring.score_pressure(candidate.mechanism_id, candidate.features)
        confidence = scoring.score_confidence(
            generator=candidate.generator,
            features=candidate.features,
            voice_certainty=ctx.voice_certainty,
            verdict_certainty=verdict.certainty,
            agreeing_votes=1 if verdict.applies == "yes" else 0,
            total_votes=1,
        )

        # An "uncertain" verdict may never be reported as High confidence.
        # This is where uncertainty would otherwise silently evaporate.
        confidence_value = confidence.value
        confidence_factors = list(confidence.factors)
        if verdict.applies == "uncertain" and confidence_value == "High":
            confidence_value = "Medium"
            confidence_factors.append(
                "capped at Medium: contextual verification returned 'uncertain'"
            )

        payload = {
            "mechanismId": candidate.mechanism_id,
            "passageId": passage.passage_id,
            "excerpt": candidate.excerpt,
            "startChar": candidate.start_char,
            "endChar": candidate.end_char,
            "pressure": pressure.value,
            "confidence": confidence_value,
            "voiceClass": ctx.voice_class,
            "triggeredCriteria": list(verdict.criteria_triggered),
            "taxonomyVersion": vocab.taxonomy_version(),
            "detectorSchemaVersion": DETECTOR_SCHEMA_VERSION,
        }

        try:
            resolved = validate_finding_payload(
                payload,
                article=article,
                allowed_mechanisms=mechanisms,
                taxonomy_version=vocab.taxonomy_version(),
            )
        except DetectorRejection as exc:
            run.rejected_candidate_count += 1
            run.failures.append(
                DetectorFailure(
                    passage_id=passage.passage_id,
                    stage=exc.stage,
                    reason=exc.reason,
                    mechanism_id=candidate.mechanism_id,
                    excerpt=candidate.excerpt,
                )
            )
            continue

        record = vocab.mechanism(candidate.mechanism_id)
        produced.append(
            Finding(
                finding_id=make_finding_id(
                    run_id=run.run_id,
                    passage_id=resolved.passage_id,
                    mechanism_id=candidate.mechanism_id,
                    start=resolved.start_char,
                    end=resolved.end_char,
                    occurrence=resolved.occurrence_index,
                ),
                analysis_run_id=run.run_id,
                article_id=article.article_id,
                passage_id=resolved.passage_id,
                mechanism_id=candidate.mechanism_id,
                family=record["family"],
                excerpt=resolved.excerpt,
                start_char=resolved.start_char,
                end_char=resolved.end_char,
                occurrence_index=resolved.occurrence_index,
                pressure=pressure.value,
                confidence=confidence_value,
                state=scoring.reportable_state(confidence_value),
                voice_class=ctx.voice_class,
                triggered_criteria=tuple(verdict.criteria_triggered),
                failed_criteria=tuple(verdict.criteria_failed),
                nearest_neighbors=tuple(verdict.nearest_neighbor_overlap),
                pressure_factors=pressure.factors,
                confidence_factors=tuple(confidence_factors),
                detector_votes=(
                    {
                        "provider": verdict.provider_id,
                        "applies": verdict.applies,
                        "certainty": round(float(verdict.certainty), 4),
                        "generator": candidate.generator,
                    },
                ),
                alternate_interpretation=_alternate_interpretation(verdict, record),
                taxonomy_version=vocab.taxonomy_version(),
                detector_version=DETECTOR_VERSION,
            )
        )

    return produced


def _alternate_interpretation(verdict: Verdict, record: dict[str, Any]) -> str | None:
    """Surface the competing reading, when the detector actually found one.

    Returns None when no exclusion fired and no neighbour overlapped. It does
    not invent a plausible-sounding caveat to fill the field.
    """
    parts: list[str] = []
    if verdict.criteria_failed:
        parts.append(
            "A competing reading is supported by: " + "; ".join(verdict.criteria_failed)
        )
    if verdict.nearest_neighbor_overlap:
        names = []
        for neighbor_id in verdict.nearest_neighbor_overlap:
            try:
                names.append(vocab.mechanism(neighbor_id)["canonicalName"])
            except ValueError:
                continue
        if names:
            parts.append("Confusable with: " + ", ".join(names) + ".")
    if verdict.applies == "uncertain":
        parts.append("Contextual verification returned uncertain for this span.")
    return " ".join(parts) if parts else None


def pressure_profile(findings: Sequence[Finding]) -> dict[str, Any]:
    """Decomposable article-level summary. Deliberately NOT a master score.

    Returns counts and distributions that can always be traced back to
    individual findings. There is no single number here, by design.
    """
    confirmed = [f for f in findings if f.state == "confirmed"]
    by_mechanism: dict[str, int] = {}
    by_family: dict[str, int] = {}
    by_pressure: dict[str, int] = {level: 0 for level in vocab.PRESSURE_ORDER}
    by_confidence: dict[str, int] = {level: 0 for level in vocab.CONFIDENCE_ORDER}
    by_voice: dict[str, int] = {}

    for finding in findings:
        by_mechanism[finding.mechanism_id] = by_mechanism.get(finding.mechanism_id, 0) + 1
        by_family[finding.family] = by_family.get(finding.family, 0) + 1
        by_pressure[finding.pressure] += 1
        by_confidence[finding.confidence] += 1
        by_voice[finding.voice_class] = by_voice.get(finding.voice_class, 0) + 1

    peak = "P1"
    for finding in findings:
        if vocab.pressure_rank(finding.pressure) > vocab.pressure_rank(peak):
            peak = finding.pressure

    return {
        "totalFindings": len(findings),
        "confirmedFindings": len(confirmed),
        "candidateFindings": len(findings) - len(confirmed),
        "peakPressure": peak if findings else None,
        "byMechanism": by_mechanism,
        "byFamily": by_family,
        "byPressure": by_pressure,
        "byConfidence": by_confidence,
        "byVoice": by_voice,
        "outletVoiceFindings": sum(
            1 for f in findings if f.voice_class in {"reporter", "editorial", "headline"}
        ),
        "quotedVoiceFindings": sum(1 for f in findings if f.voice_class == "quoted_speaker"),
        "uncertainVoiceFindings": sum(1 for f in findings if f.voice_class == "uncertain"),
        "note": (
            "Counts and distributions only. Interpretive pressure is not factuality, "
            "and this profile is deliberately not reducible to a single score."
        ),
    }
