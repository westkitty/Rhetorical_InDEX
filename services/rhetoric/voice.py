"""Voice provenance classification.

Epistemic constitution rule 8: quoted-speaker rhetoric must be distinguishable
from outlet rhetoric. A publisher reproducing an inflammatory quote is not the
same act as a publisher writing inflammatory prose, and the instrument must not
conflate them.

Where the evidence is genuinely ambiguous — a span straddling a quotation
boundary, or a passage with unbalanced quote marks — this module returns
``uncertain`` rather than guessing. Uncertainty is a legitimate output.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .document import Passage

_OPEN_QUOTES = "\"“‟"
_CLOSE_QUOTES = "\"”"
_ATTRIBUTION = re.compile(
    r"\b(?:said|says|told|stated|according to|wrote|argued|claimed|added|noted|testified)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class QuotedRegion:
    start: int
    end: int
    balanced: bool


def quoted_regions(text: str) -> tuple[tuple[QuotedRegion, ...], bool]:
    """Locate quoted regions. Returns (regions, well_formed).

    ``well_formed`` is False when quote marks are unbalanced, which downgrades
    downstream confidence instead of producing a confident wrong attribution.
    """
    regions: list[QuotedRegion] = []
    open_index: int | None = None
    well_formed = True

    for index, char in enumerate(text):
        if open_index is None:
            if char in _OPEN_QUOTES:
                open_index = index
            continue
        # An apostrophe-style straight quote can close; curly close marks close.
        if char in _CLOSE_QUOTES:
            regions.append(QuotedRegion(start=open_index, end=index + 1, balanced=True))
            open_index = None

    if open_index is not None:
        # Unterminated quote: record the tail as an unbalanced region.
        regions.append(QuotedRegion(start=open_index, end=len(text), balanced=False))
        well_formed = False

    return tuple(regions), well_formed


def classify(passage: Passage, start_char: int, end_char: int) -> tuple[str, float]:
    """Classify the voice of a span. Returns (voice_class, certainty 0.0-1.0).

    Certainty is a continuous internal signal consumed by the confidence model;
    it is deliberately NOT surfaced as a pressure value.
    """
    if start_char < 0 or end_char > len(passage.text) or end_char <= start_char:
        raise ValueError("voice classification requires an in-bounds span")

    if passage.passage_type == "heading":
        # A headline may itself quote a speaker — `Mayor Calls Plan "Draconian"`.
        # The loading there belongs to the speaker, not the outlet, so a span
        # inside quotation marks is attributed to the speaker even in a heading
        # (review finding O-04). Only unquoted heading text is outlet voice.
        heading_regions, heading_well_formed = quoted_regions(passage.text)
        inside_quote = [
            r for r in heading_regions if r.start <= start_char and end_char <= r.end
        ]
        if inside_quote:
            return ("quoted_speaker", 0.8) if inside_quote[0].balanced else ("uncertain", 0.4)
        if not heading_well_formed:
            return "uncertain", 0.35
        return "headline", 0.95

    if passage.passage_type == "blockquote":
        # A whole-passage blockquote is quoted material by construction.
        return "quoted_speaker", 0.9

    if passage.passage_type == "caption":
        return "document_material", 0.7

    regions, well_formed = quoted_regions(passage.text)

    fully_inside = [r for r in regions if r.start <= start_char and end_char <= r.end]
    if fully_inside:
        region = fully_inside[0]
        if not region.balanced:
            # Inside an unterminated quote: probably quoted, but not provable.
            return "uncertain", 0.4
        return "quoted_speaker", 0.85 if well_formed else 0.6

    # Straddling a quote boundary is genuinely ambiguous.
    straddles = [
        r for r in regions
        if (r.start < end_char and start_char < r.end) and not (r.start <= start_char and end_char <= r.end)
    ]
    if straddles:
        return "uncertain", 0.3

    if not well_formed:
        # Unbalanced quoting anywhere in the passage weakens any outlet claim.
        return "uncertain", 0.35

    # Outside quotes. Attribution verbs nearby suggest the outlet is
    # paraphrasing a source rather than asserting in its own voice.
    if _ATTRIBUTION.search(passage.text):
        return "paraphrased_source", 0.6

    return "reporter", 0.8


def is_outlet_voice(voice_class: str) -> bool:
    """Whether this voice represents the publication asserting in its own voice."""
    return voice_class in {"reporter", "editorial", "headline"}
