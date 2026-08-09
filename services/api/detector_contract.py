"""Strict detector boundary for the future Python rhetoric service.

This module is intentionally network-free. It exists to make the first real detector
vertical slice inherit the exact-span and semantic-validation rules learned from the
prototype work instead of importing the AI Studio server wholesale.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

PRESSURE = {"P1", "P2", "P3", "P4"}
CONFIDENCE = {"Low", "Medium", "High"}
VOICE = {"headline", "reporter", "editorial", "quoted_speaker", "paraphrased_source", "document_material"}
INTRINSIC_ALPHA_SLICE = {"loaded_language", "presupposition", "agent_suppression", "false_dilemma"}


@dataclass(frozen=True)
class ValidatedCandidate:
    paragraph_index: int
    start_char: int
    end_char: int
    exact_text: str
    mechanism: str
    pressure: str
    confidence: str
    voice_class: str
    triggered_criteria: tuple[str, ...]


def validate_intrinsic_candidate(paragraphs: list[str], candidate: dict[str, Any]) -> ValidatedCandidate:
    mechanism = candidate.get("mechanism")
    if mechanism not in INTRINSIC_ALPHA_SLICE:
        raise ValueError("unknown or cross-document mechanism for intrinsic alpha slice")
    pressure = candidate.get("pressure")
    confidence = candidate.get("confidence")
    voice_class = candidate.get("voiceClass")
    if pressure not in PRESSURE:
        raise ValueError("invalid pressure")
    if confidence not in CONFIDENCE:
        raise ValueError("invalid confidence")
    if voice_class not in VOICE:
        raise ValueError("invalid voice class")
    paragraph_index = candidate.get("paragraphIndex")
    if not isinstance(paragraph_index, int) or isinstance(paragraph_index, bool) or not 0 <= paragraph_index < len(paragraphs):
        raise ValueError("invalid paragraph index")
    exact_text = candidate.get("exactText")
    if not isinstance(exact_text, str) or not exact_text:
        raise ValueError("missing exact text")
    criteria = candidate.get("triggeredCriteria")
    if not isinstance(criteria, list) or not criteria or not all(isinstance(x, str) and x.strip() for x in criteria):
        raise ValueError("invalid triggered criteria")
    paragraph = paragraphs[paragraph_index]
    matches: list[int] = []
    cursor = 0
    while True:
        pos = paragraph.find(exact_text, cursor)
        if pos < 0:
            break
        matches.append(pos)
        cursor = pos + 1
    if not matches:
        raise ValueError("exact text not found")
    occurrence = candidate.get("occurrenceIndex")
    if len(matches) > 1:
        if not isinstance(occurrence, int) or isinstance(occurrence, bool) or not 0 <= occurrence < len(matches):
            raise ValueError("ambiguous repeated excerpt")
        start_char = matches[occurrence]
    else:
        if occurrence not in (None, 0):
            raise ValueError("invalid occurrence index")
        start_char = matches[0]
    end_char = start_char + len(exact_text)
    return ValidatedCandidate(
        paragraph_index=paragraph_index,
        start_char=start_char,
        end_char=end_char,
        exact_text=exact_text,
        mechanism=mechanism,
        pressure=pressure,
        confidence=confidence,
        voice_class=voice_class,
        triggered_criteria=tuple(criteria),
    )
