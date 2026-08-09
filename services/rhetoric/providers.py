"""Stage 5: contextual verification behind a provider boundary.

A provider answers one bounded question per candidate: *does this mechanism
actually apply to this exact span, given this context and this taxonomy record?*
It returns structured observations only — never prose reasoning, never a
finished Finding.

Provider output is UNTRUSTED. Everything a provider returns passes through
``validation.validate_verdict`` before it can influence a Finding. That is the
whole point of the boundary: swapping a rule-based provider for a model
provider must not widen what the system will accept.

Three kinds exist:
  MockDetectorProvider      deterministic test double, scripted verdicts
  HeuristicDetectorProvider rule-based, unbenchmarked, ships today (Level 3 slice)
  ModelDetectorProvider     external model; raises ProviderUnavailable without
                            credentials. It does NOT invent a successful call.
"""
from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from . import vocabulary as vocab
from .context import CandidateContext


class ProviderUnavailable(RuntimeError):
    """Raised when a provider cannot run (e.g. missing credentials).

    This is an honest failure that surfaces as a DetectorFailure and a partial
    AnalysisRun. It is never swallowed into a fabricated verdict.
    """


@dataclass(frozen=True)
class Verdict:
    """Raw structured provider output. Untrusted until validated."""

    applies: str  # "yes" | "no" | "uncertain"
    criteria_triggered: tuple[str, ...] = ()
    criteria_failed: tuple[str, ...] = ()
    nearest_neighbor_overlap: tuple[str, ...] = ()
    certainty: float = 0.5
    provider_id: str = "unknown"
    notes: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "applies": self.applies,
            "criteriaTriggered": list(self.criteria_triggered),
            "criteriaFailed": list(self.criteria_failed),
            "nearestNeighborOverlap": list(self.nearest_neighbor_overlap),
            "certainty": self.certainty,
            "providerId": self.provider_id,
            "notes": self.notes,
        }


class DetectorProvider(ABC):
    kind: str = "mock"
    provider_id: str = "abstract"
    version: str = "0"

    @abstractmethod
    def verify(self, context: CandidateContext) -> Verdict:
        """Return a structured verdict for one candidate."""

    def describe(self) -> dict[str, str]:
        return {"kind": self.kind, "providerId": self.provider_id, "version": self.version}


# --------------------------------------------------------------------------
# Mock
# --------------------------------------------------------------------------

class MockDetectorProvider(DetectorProvider):
    """Deterministic test double.

    Scripted by (mechanism_id, excerpt) or by mechanism_id, else a default.
    Used to exercise pipeline behaviour — partial failure, rejection paths,
    multi-tag reconciliation — without depending on heuristic quality.
    """

    kind = "mock"
    provider_id = "mock.scripted"
    version = "1"

    def __init__(
        self,
        *,
        default: Verdict | None = None,
        by_mechanism: dict[str, Verdict] | None = None,
        by_excerpt: dict[tuple[str, str], Verdict] | None = None,
        raise_on_passage: set[str] | None = None,
    ) -> None:
        self._default = default or Verdict(
            applies="yes",
            criteria_triggered=("mock criterion",),
            certainty=0.75,
            provider_id=self.provider_id,
        )
        self._by_mechanism = by_mechanism or {}
        self._by_excerpt = by_excerpt or {}
        self._raise_on_passage = raise_on_passage or set()

    def verify(self, context: CandidateContext) -> Verdict:
        if context.candidate.passage_id in self._raise_on_passage:
            raise ProviderUnavailable(f"mock failure for passage {context.candidate.passage_id}")
        key = (context.candidate.mechanism_id, context.candidate.excerpt)
        if key in self._by_excerpt:
            return self._by_excerpt[key]
        if context.candidate.mechanism_id in self._by_mechanism:
            return self._by_mechanism[context.candidate.mechanism_id]
        return self._default


# --------------------------------------------------------------------------
# Heuristic
# --------------------------------------------------------------------------

_HEDGE = re.compile(
    r"\b(?:alleged|allegedly|reportedly|appears?\s+to|seems?\s+to|may|might|could|"
    r"according\s+to|claims?|purported|suggest(?:s|ed)?)\b",
    re.IGNORECASE,
)


class HeuristicDetectorProvider(DetectorProvider):
    """Rule-based contextual verification. Unbenchmarked.

    Applies each mechanism's taxonomy exclusion criteria as concrete tests and
    reports which named criteria fired. Criteria strings are taken from the
    taxonomy only when the corresponding test actually passes — the taxonomy is
    never used to backfill evidence for a criterion that did not fire.
    """

    kind = "heuristic"
    provider_id = "heuristic.contextual"
    version = "1.0.0"

    def verify(self, context: CandidateContext) -> Verdict:
        mechanism_id = context.candidate.mechanism_id
        record = vocab.mechanism(mechanism_id)
        positive = record["positiveCriteria"]
        exclusions = record["exclusionCriteria"]
        features = context.candidate.features

        triggered: list[str] = []
        failed: list[str] = []
        neighbors: list[str] = []
        certainty = 0.6

        if mechanism_id == "loaded_language":
            tiers = features.get("tiers", [])
            if any(t in {"severe", "strong", "mild"} for t in tiers):
                triggered.append(positive[0])
            if any(t in {"noun", "verb"} for t in tiers):
                triggered.append(positive[1])
            if features.get("technical_context"):
                failed.append(exclusions[0])
                certainty -= 0.2
            if context.voice_class == "quoted_speaker":
                failed.append(exclusions[1])
                certainty -= 0.1
            if features.get("peak_tier") in {"severe", "strong"}:
                certainty += 0.2
                neighbors.append("appeal_to_fear")

        elif mechanism_id == "presupposition":
            if features.get("embeds_disputed_premise"):
                triggered.append(positive[0])
                if context.contains_hedge:
                    failed.append(exclusions[1])
                    certainty -= 0.15
                else:
                    triggered.append(positive[1])
                    certainty += 0.2
            else:
                certainty -= 0.15
                neighbors.append("epistemic_overstatement")

        elif mechanism_id == "agent_suppression":
            if features.get("construction") == "agentless_passive":
                triggered.append(positive[0])
            else:
                triggered.append(positive[1])
            if context.agent_named_nearby:
                failed.append(exclusions[1])
                certainty -= 0.3
            else:
                certainty += 0.15
            neighbors.append("material_omission")

        elif mechanism_id == "false_dilemma":
            triggered.append(positive[0])
            if features.get("alternatives_listed_nearby"):
                failed.append(exclusions[1])
                certainty -= 0.3
            else:
                triggered.append(positive[2])
                certainty += 0.15
            neighbors.append("hasty_generalization")

        else:
            raise ValueError(f"heuristic provider does not implement {mechanism_id!r}")

        if not triggered:
            return Verdict(
                applies="no",
                criteria_failed=tuple(failed),
                nearest_neighbor_overlap=tuple(neighbors),
                certainty=max(0.0, min(1.0, certainty)),
                provider_id=self.provider_id,
                notes="no positive criterion fired",
            )

        # An exclusion that outnumbers the positive evidence yields "uncertain",
        # not a silent "yes". Uncertainty must survive to the Finding.
        if failed and len(failed) >= len(triggered):
            applies = "uncertain"
        elif failed:
            applies = "uncertain" if certainty < 0.5 else "yes"
        else:
            applies = "yes"

        return Verdict(
            applies=applies,
            criteria_triggered=tuple(dict.fromkeys(triggered)),
            criteria_failed=tuple(dict.fromkeys(failed)),
            nearest_neighbor_overlap=tuple(dict.fromkeys(neighbors)),
            certainty=max(0.0, min(1.0, certainty)),
            provider_id=self.provider_id,
        )


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------

class ModelDetectorProvider(DetectorProvider):
    """External model provider.

    Fully implemented up to the network boundary: prompt construction, strict
    response schema and response parsing are real and unit-tested against
    recorded payloads. The transport itself is intentionally not implemented,
    and without credentials this class raises ProviderUnavailable.

    It never fabricates a verdict. A missing credential produces a
    DetectorFailure and a partial AnalysisRun, which is the honest outcome.
    """

    kind = "model"
    provider_id = "model.structured"
    version = "0.1.0-unwired"

    RESPONSE_SCHEMA: dict[str, Any] = {
        "type": "object",
        "required": ["applies", "criteriaTriggered", "criteriaFailed", "certainty"],
        "properties": {
            "applies": {"enum": ["yes", "no", "uncertain"]},
            "criteriaTriggered": {"type": "array", "items": {"type": "string"}},
            "criteriaFailed": {"type": "array", "items": {"type": "string"}},
            "nearestNeighborOverlap": {"type": "array", "items": {"type": "string"}},
            "certainty": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        },
        "additionalProperties": False,
    }

    def __init__(self, *, api_key: str | None = None, transport: Any = None) -> None:
        self._api_key = api_key or os.environ.get("RHETORIC_MODEL_API_KEY")
        self._transport = transport

    def available(self) -> bool:
        return bool(self._api_key) and self._transport is not None

    def build_prompt(self, context: CandidateContext) -> dict[str, Any]:
        """Construct the bounded verification request.

        The model sees the exact span, bounded context, the mechanism's own
        definition and criteria, and its confusion neighbours — and nothing
        else. It is never asked to free-form summarize the article.
        """
        record = vocab.mechanism(context.candidate.mechanism_id)
        return {
            "task": "rhetorical_mechanism_verification",
            "taxonomyVersion": vocab.taxonomy_version(),
            "mechanism": {
                "id": record["id"],
                "canonicalName": record["canonicalName"],
                "definition": record["definition"],
                "positiveCriteria": record["positiveCriteria"],
                "exclusionCriteria": record["exclusionCriteria"],
                "confusableNeighbors": record["confusableNeighbors"],
            },
            "span": {
                "exactText": context.candidate.excerpt,
                "passageType": context.passage_type,
                "voiceClass": context.voice_class,
            },
            "context": {
                "before": context.before,
                "after": context.after,
                "passageText": context.passage_text,
            },
            "instructions": (
                "Decide only whether this mechanism applies to the exact span. "
                "Cite criteria verbatim from the supplied lists. Do not invent criteria. "
                "Return 'uncertain' when the evidence is genuinely ambiguous."
            ),
            "responseSchema": self.RESPONSE_SCHEMA,
        }

    def parse_response(self, payload: str | dict[str, Any]) -> Verdict:
        """Parse and shape a model response. Malformed input raises."""
        data = json.loads(payload) if isinstance(payload, str) else payload
        if not isinstance(data, dict):
            raise ValueError("model response must be a JSON object")
        for required in ("applies", "criteriaTriggered", "criteriaFailed", "certainty"):
            if required not in data:
                raise ValueError(f"model response missing required field: {required}")
        certainty = data["certainty"]
        if not isinstance(certainty, (int, float)) or isinstance(certainty, bool):
            raise ValueError("model response certainty must be numeric")
        if not 0.0 <= float(certainty) <= 1.0:
            raise ValueError("model response certainty out of range")
        return Verdict(
            applies=str(data["applies"]),
            criteria_triggered=tuple(data["criteriaTriggered"]),
            criteria_failed=tuple(data["criteriaFailed"]),
            nearest_neighbor_overlap=tuple(data.get("nearestNeighborOverlap", ())),
            certainty=float(certainty),
            provider_id=self.provider_id,
            raw=data,
        )

    def verify(self, context: CandidateContext) -> Verdict:
        if not self.available():
            raise ProviderUnavailable(
                "model detector provider has no credentials/transport configured; "
                "no verdict was produced and none was invented"
            )
        response = self._transport.complete(self.build_prompt(context))  # pragma: no cover
        return self.parse_response(response)  # pragma: no cover


def default_provider() -> DetectorProvider:
    return HeuristicDetectorProvider()
