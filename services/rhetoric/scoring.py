"""Stages 7-8: pressure and confidence.

These are two different questions and are computed by two different models with
two different inputs:

  pressure   — "How strongly does THIS mechanism constrain interpretation here?"
               Ordinal P1-P4, governed by the mechanism's own taxonomy rubric.
               Says nothing about whether the statement is true.

  confidence — "How sure is the detector that the mechanism is present at all?"
               Low/Medium/High, epistemic only.

They must be able to vary independently: a P4 finding may be Low confidence, a
P1 finding may be High confidence. tests/python/unit/test_scoring.py asserts
that both corners are reachable, so a future refactor that quietly couples them
fails the suite.

Every score returns a factor trace so the finding drawer can show *why* —
"radically inspectable" is a product requirement, not a nicety.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from . import vocabulary as vocab

_PRESSURE_BY_RANK = {1: "P1", 2: "P2", 3: "P3", 4: "P4"}

# Participles denoting force, harm or major fiscal consequence. Suppressing the
# actor of these matters more than suppressing the actor of "was scheduled".
_CONSEQUENTIAL_PARTICIPLES = {
    "fired", "shot", "killed", "wounded", "injured", "beaten", "detained",
    "arrested", "deported", "evicted", "seized", "confiscated", "destroyed",
    "demolished", "discharged", "deployed", "silenced", "suppressed",
    "defunded", "cut", "slashed", "eliminated", "terminated", "dismissed",
    "leaked", "misled", "denied", "revoked", "banned",
}


@dataclass(frozen=True)
class Score:
    value: str
    factors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value, "factors": list(self.factors)}


def _clamp_rank(rank: int) -> int:
    return max(1, min(4, rank))


# --------------------------------------------------------------------------
# Pressure — mechanism-specific, rubric-governed
# --------------------------------------------------------------------------

# Review finding M-14: the scorer disagreed with the taxonomy's own worked
# examples. The taxonomy rubric is authoritative, and it grades loaded language
# by DOMINANCE, not by the intensity of a single word:
#   P1 "Single mildly emotive modifier"
#   P2 "Sustained use of evaluative epithets throughout a paragraph"
#   P3 "Highly charged framing words that directly steer moral interpretation"
#   P4 "Dominant inflammatory or DEHUMANIZING terminology DOMINATING sentence structure"
# A severe term such as "draconian" is highly charged (P3); it only reaches P4
# when it dominates or dehumanizes.
_DEHUMANIZING = {
    "vermin", "parasite", "parasites", "infestation", "infest", "subhuman",
    "savage", "savages", "animals", "scum", "filth", "cockroaches", "barbaric",
    "monstrous", "evil",
}
_DOMINANT_DENSITY = 0.35


def _pressure_loaded_language(features: dict[str, Any]) -> Score:
    factors: list[str] = []
    peak = features.get("peak_tier", "mild")
    count = int(features.get("term_count", 1))
    terms = {str(t).lower() for t in features.get("terms", [])}

    base = {"mild": 1, "noun": 2, "verb": 2, "strong": 3, "severe": 3}.get(peak, 1)
    factors.append(f"peak evaluative tier: {peak} (base {_PRESSURE_BY_RANK[base]})")

    if count >= 2 and base < 3:
        base += 1
        factors.append(f"sustained evaluative loading: {count} terms in one span (+1)")

    dehumanizing = terms & _DEHUMANIZING
    density = float(features.get("passage_density", 0.0))
    if dehumanizing:
        base = 4
        factors.append(f"dehumanizing terminology {sorted(dehumanizing)} (rubric P4)")
    elif density >= _DOMINANT_DENSITY and count >= 2:
        base = max(base, 4)
        factors.append(
            f"evaluative terms dominate the passage (density {density:.2f} >= {_DOMINANT_DENSITY}) (rubric P4)"
        )

    if features.get("technical_context"):
        base -= 1
        factors.append("same-sentence technical/legal or physical-event context (-1)")

    if features.get("passage_type") == "heading" and base < 4:
        base += 1
        factors.append("evaluative loading sits in a heading, amplifying framing reach (+1)")

    return Score(_PRESSURE_BY_RANK[_clamp_rank(base)], tuple(factors))


def _pressure_presupposition(features: dict[str, Any]) -> Score:
    factors: list[str] = []
    construction = features.get("construction", "change_of_state")

    if features.get("embeds_disputed_premise"):
        base = 3
        factors.append(f"factive construction ({construction}) embeds its complement as established fact (base P3)")
    else:
        base = 1
        factors.append(f"weak change-of-state marker ({construction}) presupposes a prior state (base P1)")
        if int(features.get("span_words", 0)) >= 8:
            base += 1
            factors.append("presupposed material extends across a substantial clause (+1)")

    return Score(_PRESSURE_BY_RANK[_clamp_rank(base)], tuple(factors))


def _pressure_agent_suppression(features: dict[str, Any]) -> Score:
    factors: list[str] = []
    construction = features.get("construction", "agentless_passive")
    base = 2
    factors.append(f"{construction} with no named actor (base P2)")

    participle = str(features.get("participle", "")).lower()
    if participle in _CONSEQUENTIAL_PARTICIPLES:
        base += 1
        factors.append(f"suppressed actor governs a consequential action ('{participle}') (+1)")

    if features.get("passage_type") == "heading":
        base += 1
        factors.append("agency removed in a heading, where most readers stop (+1)")

    return Score(_PRESSURE_BY_RANK[_clamp_rank(base)], tuple(factors))


# M-14: the taxonomy grades false dilemma by what the REJECTED branch threatens:
#   P3 "Forcing acceptance of a radical policy by framing the only alternative as total collapse"
#   P4 "Totalizing binary trap framing opposition as destruction"
_CATASTROPHIC_BRANCH = re.compile(
    r"\b(?:surrender|collapse|destroy(?:ed|ing)?|destruction|ruin|perish|die|death|"
    r"annihilat\w*|obliterat\w*|lose\s+everything|cease\s+to\s+exist|"
    r"criminal\s+syndicates?|anarchy|lawlessness|invasion|catastrophe)\b",
    re.IGNORECASE,
)


def _pressure_false_dilemma(features: dict[str, Any]) -> Score:
    factors: list[str] = []
    construction = features.get("construction", "either_or")
    excerpt = str(features.get("excerpt", ""))

    if construction == "closed_binary_phrase":
        base = 3
        factors.append("explicit closed-binary phrasing forecloses intermediate options (base P3)")
    else:
        base = 2
        factors.append("either/or construction presents two options (base P2)")
        if int(features.get("span_words", 0)) >= 12:
            base += 1
            factors.append("binary framing spans an extended clause, dominating the sentence (+1)")

    if _CATASTROPHIC_BRANCH.search(excerpt):
        base = max(base, 4)
        factors.append("the rejected branch is framed as destruction, not merely a worse outcome (rubric P4)")

    if features.get("alternatives_listed_nearby"):
        base -= 1
        factors.append("same-sentence text explicitly acknowledges other options (-1)")

    return Score(_PRESSURE_BY_RANK[_clamp_rank(base)], tuple(factors))


_PRESSURE_MODELS = {
    "loaded_language": _pressure_loaded_language,
    "presupposition": _pressure_presupposition,
    "agent_suppression": _pressure_agent_suppression,
    "false_dilemma": _pressure_false_dilemma,
}


def score_pressure(mechanism_id: str, features: dict[str, Any]) -> Score:
    model = _PRESSURE_MODELS.get(mechanism_id)
    if model is None:
        raise ValueError(f"no pressure model implemented for mechanism {mechanism_id!r}")
    score = model(features)
    if score.value not in vocab.PRESSURE:
        raise ValueError(f"pressure model produced invalid level: {score.value!r}")
    return score


def pressure_anchor(mechanism_id: str, level: str) -> str:
    """The taxonomy rubric sentence for this mechanism at this level."""
    rubric = vocab.mechanism(mechanism_id)["pressureRubric"]
    return rubric[level.lower()]


# --------------------------------------------------------------------------
# Confidence — epistemic only
# --------------------------------------------------------------------------

_GENERATOR_RELIABILITY = {
    "lexical.loaded_v1": 0.80,
    "grammatical.presupp_factive_wh_v1": 0.78,
    "grammatical.presupp_factive_allowed_v1": 0.70,
    "grammatical.presupp_change_of_state_v1": 0.42,
    "grammatical.passive_v1": 0.62,
    "grammatical.nominalization_v1": 0.55,
    "logical.dilemma_either_or_v1": 0.60,
    "logical.dilemma_closed_binary_phrase_v1": 0.80,
}


def score_confidence(
    *,
    generator: str,
    features: dict[str, Any],
    voice_certainty: float,
    verdict_certainty: float,
    agreeing_votes: int,
    total_votes: int,
) -> Score:
    """Combine epistemic factors into Low/Medium/High.

    Note what is deliberately absent: no pressure value, no rhetorical intensity
    and no tier information feed this function. Confidence cannot inherit
    pressure because it never sees it.
    """
    factors: list[str] = []

    base = _GENERATOR_RELIABILITY.get(generator, 0.5)
    factors.append(f"generator {generator} baseline reliability {base:.2f}")

    score = base * 0.4 + verdict_certainty * 0.35 + voice_certainty * 0.25
    factors.append(f"contextual verification certainty {verdict_certainty:.2f}")
    factors.append(f"voice provenance certainty {voice_certainty:.2f}")

    if total_votes > 1:
        agreement = agreeing_votes / total_votes
        score = score * 0.75 + agreement * 0.25
        factors.append(f"detector agreement {agreeing_votes}/{total_votes}")

    if features.get("technical_context"):
        score -= 0.12
        factors.append("competing technical reading present (-0.12)")
    if features.get("alternatives_listed_nearby"):
        score -= 0.10
        factors.append("nearby alternatives weaken the reading (-0.10)")
    if str(features.get("construction")) == "change_of_state":
        score -= 0.08
        factors.append("weak construction is frequently a false positive (-0.08)")

    score = max(0.0, min(1.0, score))
    if score >= 0.70:
        value = "High"
    elif score >= 0.48:
        value = "Medium"
    else:
        value = "Low"
    factors.append(f"combined epistemic score {score:.2f} -> {value}")
    return Score(value, tuple(factors))


def reportable_state(confidence: str, applies: str = "yes") -> str:
    """Two reporting thresholds (implementation plan §24.1).

    Candidates stay visible so recall is preserved, but only higher-confidence
    findings are allowed to inflate headline density statistics.

    Review finding M-05: an explicitly `uncertain` verdict may NEVER become
    `confirmed`, whatever its numeric confidence. "The detector is unsure this
    mechanism applies" and "this finding is confirmed" cannot both be true, and
    capping confidence to Medium was not enough because Medium mapped straight
    to confirmed. Presence-uncertainty now gates the state directly.
    """
    if confidence not in vocab.CONFIDENCE:
        raise ValueError(f"unknown confidence: {confidence!r}")
    if applies not in {"yes", "no", "uncertain"}:
        raise ValueError(f"unknown applies value: {applies!r}")
    if applies != "yes":
        return "candidate"
    return "confirmed" if vocab.confidence_rank(confidence) >= 2 else "candidate"
