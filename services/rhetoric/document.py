"""Canonical Article / Passage model.

Document structure is preserved rather than flattened into one whitespace-
collapsed blob: headings, blockquotes and list items stay addressable, because
voice provenance and pressure both depend on where text sits structurally.

Identity rules:
  * ``content_hash`` is SHA-256 (cryptographic, deterministic) over a canonical
    serialization that includes passage type and text. Identical canonical input
    yields an identical hash; any change to text or structure changes it.
  * ``passage_id`` is ``{article_id}:p{ordinal:04d}`` — stable and derivable, so
    Findings remain addressable across re-runs of the same input.

Span coordinates on a Finding are ALWAYS passage-local offsets into
``Passage.text``. There is no document-global offset space; a single coordinate
convention removes a whole class of reconciliation bugs.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Iterable

from . import vocabulary as vocab

_UNIT_SEP = "\x1f"
_RECORD_SEP = "\x1e"

_MARKDOWN_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(?P<text>.+?)\s*#*\s*$")
_BLOCKQUOTE = re.compile(r"^\s{0,3}>\s?(?P<text>.*)$")
_LIST_ITEM = re.compile(r"^\s{0,3}(?:[-*•‣]|\d{1,3}[.)])\s+(?P<text>.+)$")
# A caption keyword must be followed by a delimiter (":" / "." / "—") or a
# figure number. Without that, an ordinary sentence merely *beginning* with
# "Photo opportunities were limited..." is misread as a caption, which then
# mis-attributes its voice to document_material.
_CAPTION = re.compile(
    r"^\s*(?:figure|fig\.?|photo|image|caption|credit|pictured)\s*"
    r"(?:\d+\s*)?[:.—-]\s*(?P<text>\S.*)$",
    re.IGNORECASE,
)
_SENTENCE_END = re.compile(r"[.!?][\"'”’)\]]*\s*$")


def normalize_text(raw: str) -> str:
    """Canonical text normalization.

    Deliberately conservative: it fixes encoding-level variation (NFC, CRLF,
    non-breaking spaces, zero-width characters) but does NOT rewrite quotes,
    dashes or casing. Rewriting those would change the exact excerpt a Finding
    must round-trip against, which is exactly what the span contract forbids.
    """
    text = unicodedata.normalize("NFC", raw)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace(" ", " ").replace(" ", " ").replace(" ", " ")
    text = re.sub(r"[​‌‍﻿]", "", text)
    # Collapse runs of spaces/tabs but never across a newline (structure matters).
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


@dataclass(frozen=True)
class Passage:
    passage_id: str
    article_id: str
    ordinal: int
    passage_type: str
    text: str

    def __post_init__(self) -> None:
        if self.passage_type not in vocab.PASSAGE_TYPE:
            raise ValueError(f"invalid passage type: {self.passage_type!r}")
        if self.ordinal < 0:
            raise ValueError("passage ordinal must be non-negative")
        if not self.text:
            raise ValueError("passage text must be non-empty")

    def slice(self, start: int, end: int) -> str:
        return self.text[start:end]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passageId": self.passage_id,
            "articleId": self.article_id,
            "ordinal": self.ordinal,
            "passageType": self.passage_type,
            "text": self.text,
        }


@dataclass(frozen=True)
class Article:
    article_id: str
    content_hash: str
    passages: tuple[Passage, ...]
    provenance: dict[str, Any] = field(default_factory=dict)
    title: str | None = None
    publisher: str | None = None
    author: str | None = None
    published_at: str | None = None
    retrieved_at: str | None = None
    language: str = "en"

    def passage(self, passage_id: str) -> Passage:
        for item in self.passages:
            if item.passage_id == passage_id:
                return item
        raise KeyError(f"unknown passage id: {passage_id!r}")

    @property
    def passage_ids(self) -> tuple[str, ...]:
        return tuple(p.passage_id for p in self.passages)

    @property
    def canonical_text(self) -> str:
        return "\n\n".join(p.text for p in self.passages)

    def to_dict(self) -> dict[str, Any]:
        return {
            "articleId": self.article_id,
            "contentHash": self.content_hash,
            "title": self.title,
            "publisher": self.publisher,
            "author": self.author,
            "publishedAt": self.published_at,
            "retrievedAt": self.retrieved_at,
            "language": self.language,
            "passages": [p.to_dict() for p in self.passages],
            "provenance": dict(self.provenance),
        }


def _quote_marks_balanced(text: str) -> bool:
    """Whether quotation marks in `text` pair up.

    Curly marks are counted directionally; straight double quotes are counted by
    parity. An unbalanced result means quoted material is present but its extent
    is unresolved, which must block heading classification (see O-04).
    """
    if text.count("“") != text.count("”"):
        return False
    if text.count('"') % 2 != 0:
        return False
    return True


def _classify_line_block(block: str) -> tuple[str, str]:
    """Return (passage_type, cleaned_text) for one raw block."""
    stripped = block.strip()

    heading = _MARKDOWN_HEADING.match(stripped)
    if heading:
        return "heading", heading.group("text").strip()

    lines = stripped.split("\n")
    if all(_BLOCKQUOTE.match(line) for line in lines):
        inner = "\n".join(_BLOCKQUOTE.match(line).group("text") for line in lines).strip()
        if inner:
            return "blockquote", inner

    if len(lines) == 1:
        listed = _LIST_ITEM.match(stripped)
        if listed:
            return "list_item", listed.group("text").strip()

        caption = _CAPTION.match(stripped)
        if caption and caption.group("text").strip():
            return "caption", stripped

        # A short line with no terminal sentence punctuation reads as a heading.
        # Bounded by word count so that a genuine short sentence fragment inside
        # prose is not silently promoted to a heading.
        #
        # A line carrying an UNBALANCED quotation mark is excluded (review
        # finding O-04): a truncated fragment such as
        #     The memo said "the plan is draconian and unworkable
        # otherwise became a heading, and headings are classified as `headline`
        # voice — which attributes quoted rhetoric to the outlet. Falling back
        # to `paragraph` lets voice resolve to quoted_speaker/uncertain instead.
        if (
            len(stripped) <= 120
            and not _SENTENCE_END.search(stripped)
            and 0 < len(stripped.split()) <= 14
            and _quote_marks_balanced(stripped)
        ):
            return "heading", stripped

    # A block that is entirely wrapped in quotation marks is quoted material.
    if len(stripped) > 1 and stripped[0] in "\"“" and stripped[-1] in "\"”":
        return "blockquote", stripped

    return "paragraph", stripped


def segment(raw_text: str, *, article_id: str | None = None, **metadata: Any) -> Article:
    """Deterministically segment raw text into a canonical Article.

    Segmentation is pure: the same input always yields the same passages, the
    same passage ids and the same content hash. No clock, no randomness, no
    counters that survive across calls.
    """
    normalized = normalize_text(raw_text)
    if not normalized:
        raise ValueError("cannot segment empty text")

    raw_blocks = [b for b in re.split(r"\n\s*\n", normalized) if b.strip()]
    classified: list[tuple[str, str]] = []
    for block in raw_blocks:
        block_lines = block.split("\n")
        # Multi-line blocks that are uniformly list items become separate passages.
        if len(block_lines) > 1 and all(_LIST_ITEM.match(line) for line in block_lines):
            for line in block_lines:
                classified.append(("list_item", _LIST_ITEM.match(line).group("text").strip()))
            continue
        # A multi-line block whose first line is a heading splits into heading + body.
        first_heading = _MARKDOWN_HEADING.match(block_lines[0]) if len(block_lines) > 1 else None
        if first_heading:
            classified.append(("heading", first_heading.group("text").strip()))
            remainder = "\n".join(block_lines[1:]).strip()
            if remainder:
                classified.append(_classify_line_block(remainder))
            continue
        classified.append(_classify_line_block(block))

    classified = [(kind, text) for kind, text in classified if text.strip()]
    if not classified:
        raise ValueError("cannot segment text into any non-empty passage")

    content_hash = compute_content_hash(classified)
    resolved_article_id = article_id or derive_article_id(
        content_hash,
        publisher=metadata.get("publisher"),
        source_id=(metadata.get("provenance") or {}).get("sourceId"),
        url=metadata.get("url"),
    )

    passages = tuple(
        Passage(
            passage_id=f"{resolved_article_id}:p{ordinal:04d}",
            article_id=resolved_article_id,
            ordinal=ordinal,
            passage_type=kind,
            text=text,
        )
        for ordinal, (kind, text) in enumerate(classified)
    )

    provenance = dict(metadata.pop("provenance", {}) or {})
    provenance.setdefault("segmenter", "rhetoric.document.segment")
    provenance.setdefault("normalization", "NFC+newline+space")
    return Article(
        article_id=resolved_article_id,
        content_hash=content_hash,
        passages=passages,
        provenance=provenance,
        **metadata,
    )


def derive_article_id(
    content_hash: str,
    *,
    publisher: str | None = None,
    source_id: str | None = None,
    url: str | None = None,
) -> str:
    """Article identity, which is NOT the same thing as content identity.

    Review finding O-07: a purely content-derived id gave two different
    publishers carrying identical syndicated copy the SAME article id. For
    cross-document comparison that is actively dangerous — it would let one
    article appear to corroborate itself.

    * No provenance supplied (a bare local paste): fall back to content
      identity, which is the honest answer for a source-less document.
    * Any provenance supplied: fold it into the id so two publications of the
      same text remain distinct articles.

    ``content_hash`` remains separately available on the Article for genuine
    duplicate-text detection.
    """
    provenance = "|".join(part for part in (source_id, publisher, url) if part)
    if not provenance:
        return f"art-{content_hash[:16]}"
    digest = hashlib.sha256(f"{content_hash}|{provenance}".encode("utf-8")).hexdigest()
    return f"art-{digest[:16]}"


def compute_content_hash(classified: Iterable[tuple[str, str]]) -> str:
    """SHA-256 over a canonical serialization including structure.

    Passage type participates in the hash: the same words rearranged from
    heading into paragraph is a materially different document to analyze.
    """
    payload = _RECORD_SEP.join(f"{kind}{_UNIT_SEP}{text}" for kind, text in classified)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def article_from_passages(
    article_id: str,
    passages: Iterable[tuple[str, str]],
    **metadata: Any,
) -> Article:
    """Build an Article from already-structured (passage_type, text) pairs.

    Used by fixtures and the benchmark corpus, where structure is authored
    rather than inferred.
    """
    classified = [(kind, normalize_text(text)) for kind, text in passages]
    classified = [(kind, text) for kind, text in classified if text]
    if not classified:
        raise ValueError("cannot build an article with no non-empty passages")
    for kind, _ in classified:
        if kind not in vocab.PASSAGE_TYPE:
            raise ValueError(f"invalid passage type: {kind!r}")
    content_hash = compute_content_hash(classified)
    built = tuple(
        Passage(
            passage_id=f"{article_id}:p{ordinal:04d}",
            article_id=article_id,
            ordinal=ordinal,
            passage_type=kind,
            text=text,
        )
        for ordinal, (kind, text) in enumerate(classified)
    )
    provenance = dict(metadata.pop("provenance", {}) or {})
    provenance.setdefault("segmenter", "rhetoric.document.article_from_passages")
    return Article(
        article_id=article_id,
        content_hash=content_hash,
        passages=built,
        provenance=provenance,
        **metadata,
    )
