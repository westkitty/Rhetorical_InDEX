"""Stage 3: candidate generation.

Deliberately recall-oriented (implementation plan §22.1). Candidates are cheap
lexical/grammatical signals; they are NOT findings. Every candidate must survive
contextual verification, exclusion criteria, validation and reconciliation
before it can become a Finding.

Each candidate carries mechanism-specific ``features`` used later by the
pressure model (§23.2). Features are observations, not verdicts — the pressure
model owns the judgment, so that the rubric stays auditable in one place.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .document import Passage

# --------------------------------------------------------------------------
# Lexicons. Tiered by rhetorical intensity, not by political valence: the
# instrument has no left/right axis and these lists must stay ideologically
# symmetric. Terms are chosen for evaluative loading, not for the side that
# typically deploys them.
# --------------------------------------------------------------------------

_LOADED_SEVERE = {
    "draconian", "tyrannical", "despotic", "barbaric", "monstrous", "evil",
    "catastrophic", "apocalyptic", "devastating", "disastrous", "ruinous",
    "corrupt", "criminal", "treasonous", "fascist", "authoritarian",
}
_LOADED_STRONG = {
    "reckless", "outrageous", "shameful", "disgraceful", "brutal", "cynical",
    "radical", "extremist", "dangerous", "alarming", "shocking", "scandalous",
    "heroic", "courageous", "visionary", "landmark", "triumphant",
}
_LOADED_MILD = {
    "controversial", "troubling", "questionable", "aggressive", "sweeping",
    "bold", "ambitious", "remarkable", "notable", "significant",
}
_LOADED_NOUNS = {
    "scheme", "plot", "ploy", "regime", "crackdown", "onslaught", "assault",
    "giveaway", "grab", "windfall", "boondoggle",
}
_LOADED_VERBS = {
    "siphon", "siphons", "siphoning", "ram", "rammed", "ramming", "gut",
    "gutted", "gutting", "slash", "slashed", "slashing", "torch", "torched",
    "dismantle", "dismantled", "dismantling", "plunder", "plundered",
}

# Terms whose apparent loading is technical, legal or physically descriptive.
# Presence of these near a hit is an exclusion signal, not a positive one.
_TECHNICAL_CONTEXT = re.compile(
    r"\b(?:felony|misdemeanor|statute|magnitude|richter|category\s+[1-5]|"
    r"non-compliance|indictment|earthquake|hurricane|wildfire|magnitude)\b",
    re.IGNORECASE,
)

_FACTIVE = r"(?:refused|failed|declined|neglected|continued|stopped|admitted|revealed|exposed|acknowledged)"
_PRESUPP_WH = re.compile(
    rf"\b{_FACTIVE}\s+to\s+(?:explain|say|address|justify|acknowledge|answer)\s+(?:why|how|when|whether)\b[^.!?]*",
    re.IGNORECASE,
)
_PRESUPP_CHANGE = re.compile(
    r"\b(?:still|again|finally|once\s+again|continues?\s+to|keeps?\s+on|no\s+longer)\b[^.!?]{0,90}",
    re.IGNORECASE,
)
_PRESUPP_ALLOWED = re.compile(
    r"\b(?:allowed|permitted|let|enabled)\s+(?:this|that|the|it|them|him|her)\b[^.!?]{0,80}",
    re.IGNORECASE,
)

# Irregular past participles that do NOT end in ed/en/wn/ht/pt. Without these
# the canonical agent-suppression example in the taxonomy itself — "Mistakes
# were made" — is silently missed, which is a recall failure in exactly the
# class of rhetoric this mechanism exists to catch.
_IRREGULAR_PARTICIPLES = (
    "made|done|sent|built|held|told|brought|thought|found|kept|left|lost|met|paid|"
    "sold|spent|won|cut|hit|hurt|set|shut|spread|cost|put|read|said|lit|dealt|felt|"
    "meant|struck|stuck|swept|split|quit|shed|bled|fled|led|fed"
)
_PASSIVE = re.compile(
    r"\b(?:was|were|is|are|been|be|being|got)\s+(?:\w+ly\s+)?"
    rf"(?P<participle>\w+(?:ed|en|wn|ht|pt)|(?:{_IRREGULAR_PARTICIPLES}))\b"
    r"(?P<tail>[^.!?]{0,80})",
    re.IGNORECASE,
)
_BY_AGENT = re.compile(r"\bby\s+(?:the\s+|a\s+|an\s+)?[A-Za-z]", re.IGNORECASE)
_NOMINALIZATION = re.compile(
    r"\b(?:the\s+)?(?:occurrence|implementation|elimination|reduction|termination|"
    r"cancellation|displacement|escalation|deterioration|loss)\s+of\s+\w+",
    re.IGNORECASE,
)
# Participles that are ordinary adjectival states rather than suppressed agency.
_STATIVE_PARTICIPLES = {
    "based", "located", "situated", "aimed", "intended", "designed", "known",
    "supposed", "expected", "scheduled", "involved", "concerned", "related",
    "interested", "willing", "unwilling", "able",
}

_DILEMMA_EITHER = re.compile(
    r"\beither\b[^.!?]{0,140}?\bor\b[^.!?]{0,140}", re.IGNORECASE
)
_DILEMMA_PHRASE = re.compile(
    r"\b(?:no\s+alternative|no\s+other\s+(?:choice|option)|only\s+two\s+(?:choices|options|paths)|"
    r"with\s+us\s+or\s+against\s+us|sink\s+or\s+swim|now\s+or\s+never|"
    r"(?:must|will)\s+(?:either\s+)?choose\s+between)\b[^.!?]{0,120}",
    re.IGNORECASE,
)
_DILEMMA_ALTERNATIVES = re.compile(
    r"\b(?:ranging\s+from|among\s+them|alternatives\s+include|other\s+options|"
    r"a\s+range\s+of|several\s+proposals|middle\s+ground|compromise)\b",
    re.IGNORECASE,
)

_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")


@dataclass(frozen=True)
class Candidate:
    passage_id: str
    mechanism_id: str
    start_char: int
    end_char: int
    excerpt: str
    generator: str
    features: dict[str, Any] = field(default_factory=dict)

    def key(self) -> tuple[str, str, int, int]:
        return (self.passage_id, self.mechanism_id, self.start_char, self.end_char)


def _word_span(text: str, match: re.Match) -> tuple[int, int]:
    """Trim trailing whitespace/punctuation so the span is a clean excerpt."""
    start, end = match.start(), match.end()
    while end > start and text[end - 1] in " \t\n,;:—-":
        end -= 1
    return start, end


def _passage_word_count(text: str) -> int:
    return len(_WORD.findall(text)) or 1


def _sentence_bounded_window(text: str, start: int, desired_end: int) -> str:
    """Text from `start` to `desired_end`, truncated at the first sentence end.

    Used for exclusion tests that must not see across a sentence boundary.
    """
    end = min(len(text), desired_end)
    terminator = re.search(r"[.!?]", text[start:end])
    if terminator:
        end = start + terminator.start()
    return text[start:end]


def loaded_language(passage: Passage) -> list[Candidate]:
    text = passage.text
    hits: list[tuple[int, int, str, str]] = []
    for match in _WORD.finditer(text):
        term = match.group(0).lower()
        if term in _LOADED_SEVERE:
            tier = "severe"
        elif term in _LOADED_STRONG:
            tier = "strong"
        elif term in _LOADED_MILD:
            tier = "mild"
        elif term in _LOADED_NOUNS:
            tier = "noun"
        elif term in _LOADED_VERBS:
            tier = "verb"
        else:
            continue
        hits.append((match.start(), match.end(), term, tier))

    if not hits:
        return []

    density = len(hits) / _passage_word_count(text)
    technical = bool(_TECHNICAL_CONTEXT.search(text))

    # Merge adjacent hits separated only by punctuation/conjunction into one
    # span, so "draconian, reckless scheme" is one Finding rather than three.
    merged: list[list[Any]] = []
    for start, end, term, tier in hits:
        if merged and start - merged[-1][1] <= 12 and not re.search(r"[.!?]", text[merged[-1][1]:start]):
            merged[-1][1] = end
            merged[-1][2].append(term)
            merged[-1][3].append(tier)
        else:
            merged.append([start, end, [term], [tier]])

    out: list[Candidate] = []
    for start, end, terms, tiers in merged:
        out.append(
            Candidate(
                passage_id=passage.passage_id,
                mechanism_id="loaded_language",
                start_char=start,
                end_char=end,
                excerpt=text[start:end],
                generator="lexical.loaded_v1",
                features={
                    "terms": terms,
                    "tiers": tiers,
                    "peak_tier": _peak_tier(tiers),
                    "term_count": len(terms),
                    "passage_density": round(density, 4),
                    "technical_context": technical,
                    "passage_type": passage.passage_type,
                },
            )
        )
    return out


def _peak_tier(tiers: list[str]) -> str:
    order = {"mild": 1, "noun": 2, "verb": 2, "strong": 3, "severe": 4}
    return max(tiers, key=lambda t: order.get(t, 0))


def presupposition(passage: Passage) -> list[Candidate]:
    text = passage.text
    out: list[Candidate] = []
    seen: set[tuple[int, int]] = set()

    for pattern, kind in (
        (_PRESUPP_WH, "factive_wh"),
        (_PRESUPP_ALLOWED, "factive_allowed"),
        (_PRESUPP_CHANGE, "change_of_state"),
    ):
        for match in pattern.finditer(text):
            start, end = _word_span(text, match)
            if end - start < 4 or (start, end) in seen:
                continue
            seen.add((start, end))
            out.append(
                Candidate(
                    passage_id=passage.passage_id,
                    mechanism_id="presupposition",
                    start_char=start,
                    end_char=end,
                    excerpt=text[start:end],
                    generator=f"grammatical.presupp_{kind}_v1",
                    features={
                        "construction": kind,
                        # A factive verb embeds its complement as fact; a bare
                        # change-of-state adverb is a much weaker signal.
                        "embeds_disputed_premise": kind in {"factive_wh", "factive_allowed"},
                        "span_words": len(_WORD.findall(text[start:end])),
                        "passage_type": passage.passage_type,
                    },
                )
            )
    return out


def agent_suppression(passage: Passage) -> list[Candidate]:
    text = passage.text
    out: list[Candidate] = []

    for match in _PASSIVE.finditer(text):
        participle = match.group("participle").lower()
        if participle in _STATIVE_PARTICIPLES:
            continue
        start, end = _word_span(text, match)
        # The by-agent test must stay inside the CURRENT sentence. A window that
        # runs past a sentence boundary lets "...by the department" in the next
        # sentence suppress a genuinely agentless clause in this one, which
        # silently loses exactly the rhetoric this mechanism exists to catch.
        window = _sentence_bounded_window(text, match.start(), match.end() + 40)
        if _BY_AGENT.search(window):
            # "was announced by the department" names its actor: not suppression.
            continue
        out.append(
            Candidate(
                passage_id=passage.passage_id,
                mechanism_id="agent_suppression",
                start_char=start,
                end_char=end,
                excerpt=text[start:end],
                generator="grammatical.passive_v1",
                features={
                    "construction": "agentless_passive",
                    "participle": participle,
                    "by_agent_present": False,
                    "span_words": len(_WORD.findall(text[start:end])),
                    "passage_type": passage.passage_type,
                },
            )
        )

    for match in _NOMINALIZATION.finditer(text):
        start, end = _word_span(text, match)
        out.append(
            Candidate(
                passage_id=passage.passage_id,
                mechanism_id="agent_suppression",
                start_char=start,
                end_char=end,
                excerpt=text[start:end],
                generator="grammatical.nominalization_v1",
                features={
                    "construction": "nominalization",
                    "by_agent_present": False,
                    "span_words": len(_WORD.findall(text[start:end])),
                    "passage_type": passage.passage_type,
                },
            )
        )
    return out


def false_dilemma(passage: Passage) -> list[Candidate]:
    text = passage.text
    alternatives_present = bool(_DILEMMA_ALTERNATIVES.search(text))
    out: list[Candidate] = []
    seen: set[tuple[int, int]] = set()

    for pattern, kind in ((_DILEMMA_EITHER, "either_or"), (_DILEMMA_PHRASE, "closed_binary_phrase")):
        for match in pattern.finditer(text):
            start, end = _word_span(text, match)
            if (start, end) in seen:
                continue
            seen.add((start, end))
            out.append(
                Candidate(
                    passage_id=passage.passage_id,
                    mechanism_id="false_dilemma",
                    start_char=start,
                    end_char=end,
                    excerpt=text[start:end],
                    generator=f"logical.dilemma_{kind}_v1",
                    features={
                        "construction": kind,
                        # The taxonomy's exclusion criterion: surrounding text
                        # that explicitly lists other options defeats the claim.
                        "alternatives_listed_nearby": alternatives_present,
                        "span_words": len(_WORD.findall(text[start:end])),
                        "passage_type": passage.passage_type,
                    },
                )
            )
    return out


_GENERATORS = {
    "loaded_language": loaded_language,
    "presupposition": presupposition,
    "agent_suppression": agent_suppression,
    "false_dilemma": false_dilemma,
}


def generate(passage: Passage, mechanisms: frozenset[str] | set[str]) -> list[Candidate]:
    """Generate candidates for the requested mechanisms on one passage."""
    out: list[Candidate] = []
    for mechanism_id in sorted(mechanisms):
        generator = _GENERATORS.get(mechanism_id)
        if generator is None:
            raise ValueError(f"no candidate generator implemented for {mechanism_id!r}")
        out.extend(generator(passage))
    out.sort(key=lambda c: (c.start_char, c.end_char, c.mechanism_id))
    return out


def supported_mechanisms() -> frozenset[str]:
    return frozenset(_GENERATORS)
