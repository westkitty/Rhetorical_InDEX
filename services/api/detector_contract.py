"""Strict detector boundary for the future Python rhetoric service.

This module is intentionally network-free. It exists to make the first real detector
vertical slice inherit the exact-span and semantic-validation rules learned from the
prototype work instead of importing the AI Studio server wholesale.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Vocabulary is READ from the canonical contract source rather than restated
# here. Previously these were literal sets kept in sync with TypeScript by a
# parity test; reading the same file the TypeScript bindings are verified
# against makes drift impossible by construction instead of merely detectable.
# Loaded directly (not via services.rhetoric) so this module stays importable
# by file path with no package/sys.path assumptions.
_SCHEMA = json.loads(
    (Path(__file__).resolve().parents[2] / "packages" / "schema" / "schema.json").read_text()
)


def _enum(name: str) -> set[str]:
    return set(_SCHEMA["properties"][name]["enum"])


PRESSURE = _enum("pressureLevel")
CONFIDENCE = _enum("confidenceLevel")
VOICE = _enum("voiceClass")
INTRINSIC_ALPHA_SLICE = _enum("intrinsicAlphaSlice")


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
