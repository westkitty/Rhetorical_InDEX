"""Stage 4: bounded context assembly.

Contextual verification needs *some* surrounding text, but handing a provider
the whole article invites two failures: cross-document contamination (the
provider starts reasoning about material the intrinsic slice must not see) and
unbounded cost. Context is therefore explicitly windowed and carries only
observations the verification stage is entitled to use.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .candidates import Candidate
from .document import Article, Passage
from . import voice as voice_module

CONTEXT_WINDOW_CHARS = 240

_HEDGE = re.compile(
    r"\b(?:alleged|allegedly|reportedly|appears?\s+to|seems?\s+to|may|might|could|"
    r"according\s+to|claims?|purported|suggests?|reportedly)\b",
    re.IGNORECASE,
)
_NAMED_ACTOR = re.compile(
    r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:said|announced|ordered|approved|issued|declined)|"
    r"(?:police|officers?|regulators?|officials?|lawmakers?|the\s+(?:department|agency|commission|committee|board|council)))\b"
)


@dataclass(frozen=True)
class CandidateContext:
    candidate: Candidate
    passage_text: str
    passage_type: str
    before: str
    after: str
    voice_class: str
    voice_certainty: float
    contains_hedge: bool
    agent_named_nearby: bool
    preceding_passage_text: str | None = None

    @property
    def excerpt(self) -> str:
        return self.candidate.excerpt


def assemble(
    article: Article,
    passage: Passage,
    candidate: Candidate,
    *,
    window: int = CONTEXT_WINDOW_CHARS,
) -> CandidateContext:
    if candidate.passage_id != passage.passage_id:
        raise ValueError("candidate/passage mismatch during context assembly")

    text = passage.text
    if not (0 <= candidate.start_char < candidate.end_char <= len(text)):
        raise ValueError("candidate span is out of bounds for its passage")
    if text[candidate.start_char:candidate.end_char] != candidate.excerpt:
        raise ValueError("candidate excerpt does not round-trip against its passage")

    before = text[max(0, candidate.start_char - window):candidate.start_char]
    after = text[candidate.end_char:candidate.end_char + window]

    voice_class, voice_certainty = voice_module.classify(
        passage, candidate.start_char, candidate.end_char
    )

    # The taxonomy's agent-suppression exclusion allows for an actor named in
    # the immediately preceding sentence, so the preceding passage is included
    # for that test only.
    preceding_text = None
    if passage.ordinal > 0:
        preceding_text = article.passages[passage.ordinal - 1].text

    agent_scope = f"{preceding_text or ''} {before}"
    return CandidateContext(
        candidate=candidate,
        passage_text=text,
        passage_type=passage.passage_type,
        before=before,
        after=after,
        voice_class=voice_class,
        voice_certainty=voice_certainty,
        contains_hedge=bool(_HEDGE.search(f"{before} {candidate.excerpt} {after}")),
        agent_named_nearby=bool(_NAMED_ACTOR.search(agent_scope)),
        preceding_passage_text=preceding_text,
    )
