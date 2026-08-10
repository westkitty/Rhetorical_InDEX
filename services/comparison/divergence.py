"""Deterministic factual-divergence detection for claim alignment.

Purpose: stop the aligner converting *unresolved contradiction* into
*evidentiary support*. Two claims can share almost all their vocabulary and
still assert incompatible facts — "spending rose 12 percent" vs "spending rose
40 percent" differ by one token and mean different things. Lexical overlap
alone cannot see that, so this module supplies a bounded, inspectable set of
high-value conflict checks that run before any high-overlap pair is allowed to
be treated as agreement.

Scope discipline — what this is NOT:
  * not a semantic entailment engine
  * not general contradiction detection
  * not a paraphrase detector
It catches selected numeric, temporal and polarity conflicts, plus explicit
negation. Everything it misses stays `uncertain`, which is non-usable for
Material Omission. The design bias is fail-closed: a missed divergence must
never become confident agreement, so an unrecognized conflict falls back to
"we could not establish this", never "these agree".
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

# --------------------------------------------------------------------------
# Negation (pre-existing behaviour, folded into the same detector)
# --------------------------------------------------------------------------

_NEGATION = re.compile(
    r"\b(?:not|no|never|without|denies|denied|rejects|rejected|refutes|refuted|"
    r"contrary|fails\s+to|failed\s+to|cannot|can't|won't|didn't|doesn't|isn't|aren't)\b",
    re.IGNORECASE,
)

# --------------------------------------------------------------------------
# Numeric
# --------------------------------------------------------------------------

_SCALE = {
    "hundred": 100, "thousand": 1_000, "k": 1_000,
    "million": 1_000_000, "m": 1_000_000,
    "billion": 1_000_000_000, "bn": 1_000_000_000, "b": 1_000_000_000,
    "trillion": 1_000_000_000_000,
}

# Currency first, then percent, then scaled/bare numbers.
_NUM_CURRENCY = re.compile(
    r"(?P<sym>[$£€])\s?(?P<value>\d[\d,]*(?:\.\d+)?)\s*(?P<scale>hundred|thousand|million|billion|trillion|k|m|bn|b)?",
    re.IGNORECASE,
)
_NUM_PERCENT = re.compile(
    r"(?P<value>\d[\d,]*(?:\.\d+)?)\s*(?:%|per\s?cent(?:age)?)",
    re.IGNORECASE,
)
_NUM_PLAIN = re.compile(
    r"(?<![\w$£€.])(?P<value>\d[\d,]*(?:\.\d+)?)\s*(?P<scale>hundred|thousand|million|billion|trillion)?(?![\w%])",
    re.IGNORECASE,
)
_CLOCK = re.compile(r"\b(?P<h>\d{1,2})(?::(?P<m>\d{2}))?\s*(?P<mer>a\.?m\.?|p\.?m\.?)\b", re.IGNORECASE)

# --------------------------------------------------------------------------
# Temporal
# --------------------------------------------------------------------------

_WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
_MONTHS = ("january", "february", "march", "april", "may", "june", "july",
           "august", "september", "october", "november", "december")
_WEEKDAY_RE = re.compile(r"\b(" + "|".join(_WEEKDAYS) + r")\b", re.IGNORECASE)
_MONTH_DAY_RE = re.compile(
    r"\b(?P<month>" + "|".join(_MONTHS) + r")\s+(?P<day>\d{1,2})\b", re.IGNORECASE
)
_YEAR_RE = re.compile(r"\b(?P<year>(?:19|20)\d{2})\b")

# --------------------------------------------------------------------------
# Polarity / antonym pairs — deliberately small, explicit and auditable.
# Highly polysemous tokens ("up", "down", "over", "under") are excluded: at
# high lexical overlap they produce false conflicts more often than real ones.
# --------------------------------------------------------------------------

_POLARITY_PAIRS: tuple[tuple[str, frozenset[str], frozenset[str]], ...] = (
    ("direction", frozenset({
        "increase", "increases", "increased", "increasing", "rise", "rises", "rose",
        "risen", "rising", "grew", "grow", "grows", "growing", "surge", "surged",
        "climb", "climbed", "higher", "expand", "expands", "expanded", "expanding",
    }), frozenset({
        "decrease", "decreases", "decreased", "decreasing", "fall", "falls", "fell",
        "fallen", "falling", "drop", "drops", "dropped", "dropping", "shrink",
        "shrank", "shrunk", "decline", "declines", "declined", "lower", "reduce",
        "reduces", "reduced", "reducing", "cut", "cuts",
    })),
    ("benefit", frozenset({"help", "helps", "helped", "helping", "benefit", "benefits", "benefited", "aid", "aids", "aided"}),
                frozenset({"harm", "harms", "harmed", "harming", "hurt", "hurts", "damage", "damages", "damaged"})),
    ("approval", frozenset({"approve", "approves", "approved", "approving", "adopt", "adopts", "adopted", "passed", "passes", "ratified"}),
                 frozenset({"reject", "rejects", "rejected", "rejecting", "deny", "denies", "denied", "blocked", "blocks", "defeated", "vetoed"})),
    ("permission", frozenset({"allow", "allows", "allowed", "allowing", "permit", "permits", "permitted", "authorize", "authorizes", "authorized"}),
                   frozenset({"prohibit", "prohibits", "prohibited", "ban", "bans", "banned", "forbid", "forbids", "forbade", "forbidden", "barred"})),
    ("stance", frozenset({"support", "supports", "supported", "supporting", "backs", "backed", "endorse", "endorses", "endorsed"}),
               frozenset({"oppose", "opposes", "opposed", "opposing", "resist", "resists", "resisted", "condemn", "condemns", "condemned"})),
    ("safety", frozenset({"safe", "safer", "safety", "secure"}),
               frozenset({"dangerous", "unsafe", "hazardous", "risky", "perilous"})),
    ("legality", frozenset({"legal", "lawful", "permitted"}),
                 frozenset({"illegal", "unlawful", "criminal"})),
    ("presence", frozenset({"present", "included", "includes", "contained", "contains"}),
                 frozenset({"absent", "missing", "omitted", "excluded", "excludes"})),
    ("gain", frozenset({"gain", "gains", "gained", "won", "wins"}),
             frozenset({"lose", "loses", "lost", "losing", "losses"})),
    ("sequence", frozenset({"before", "prior", "preceding", "earlier"}),
                 frozenset({"after", "following", "subsequent", "later"})),
)

_WORD = re.compile(r"[A-Za-z]+")


@dataclass(frozen=True)
class Divergence:
    kind: str          # "negation" | "numeric" | "temporal" | "polarity"
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "detail": self.detail}


def _strip_commas(value: str) -> str:
    return value.replace(",", "")


def _numeric_values(text: str) -> dict[str, set[float]]:
    """Extract normalized numbers grouped by kind.

    Normalization makes formatting variants equal: "12%" == "12 percent",
    "1,000" == "1000", "$2 million" == "$2000000".
    """
    found: dict[str, set[float]] = {"currency": set(), "percent": set(), "plain": set(), "clock": set()}
    consumed: list[tuple[int, int]] = []

    for match in _NUM_CURRENCY.finditer(text):
        value = float(_strip_commas(match.group("value")))
        scale = match.group("scale")
        if scale:
            value *= _SCALE[scale.lower()]
        found["currency"].add(value)
        consumed.append(match.span())

    for match in _NUM_PERCENT.finditer(text):
        found["percent"].add(float(_strip_commas(match.group("value"))))
        consumed.append(match.span())

    for match in _CLOCK.finditer(text):
        hour = int(match.group("h")) % 12
        minute = int(match.group("m") or 0)
        if match.group("mer").lower().startswith("p"):
            hour += 12
        found["clock"].add(hour * 60 + minute)
        consumed.append(match.span())

    for match in _NUM_PLAIN.finditer(text):
        if any(start <= match.start() < end for start, end in consumed):
            continue
        value = float(_strip_commas(match.group("value")))
        scale = match.group("scale")
        if scale:
            value *= _SCALE[scale.lower()]
        found["plain"].add(value)

    return found


def _numeric_divergences(a: str, b: str) -> list[Divergence]:
    left, right = _numeric_values(a), _numeric_values(b)
    out: list[Divergence] = []
    for kind in ("currency", "percent", "clock", "plain"):
        lv, rv = left[kind], right[kind]
        # Only a conflict when BOTH sides state a value of this kind and the
        # stated values differ. One side being silent is missing detail, not a
        # contradiction, and must not be treated as one.
        if lv and rv and lv != rv:
            out.append(Divergence("numeric", f"{kind} values differ: {sorted(lv)} vs {sorted(rv)}"))
    return out


def _temporal_divergences(a: str, b: str) -> list[Divergence]:
    out: list[Divergence] = []

    days_a = {m.group(1).lower() for m in _WEEKDAY_RE.finditer(a)}
    days_b = {m.group(1).lower() for m in _WEEKDAY_RE.finditer(b)}
    if days_a and days_b and days_a != days_b:
        out.append(Divergence("temporal", f"weekday differs: {sorted(days_a)} vs {sorted(days_b)}"))

    md_a = {(m.group("month").lower(), int(m.group("day"))) for m in _MONTH_DAY_RE.finditer(a)}
    md_b = {(m.group("month").lower(), int(m.group("day"))) for m in _MONTH_DAY_RE.finditer(b)}
    if md_a and md_b and md_a != md_b:
        out.append(Divergence("temporal", f"calendar date differs: {sorted(md_a)} vs {sorted(md_b)}"))

    years_a = {int(m.group("year")) for m in _YEAR_RE.finditer(a)}
    years_b = {int(m.group("year")) for m in _YEAR_RE.finditer(b)}
    if years_a and years_b and years_a != years_b:
        out.append(Divergence("temporal", f"year differs: {sorted(years_a)} vs {sorted(years_b)}"))

    return out


def _polarity_divergences(a: str, b: str) -> list[Divergence]:
    words_a = {w.lower() for w in _WORD.findall(a)}
    words_b = {w.lower() for w in _WORD.findall(b)}
    out: list[Divergence] = []
    for name, positive, negative in _POLARITY_PAIRS:
        a_pos, a_neg = words_a & positive, words_a & negative
        b_pos, b_neg = words_b & positive, words_b & negative
        # Opposite poles across the two claims, and neither claim is itself
        # internally two-sided (which would make the comparison meaningless).
        if a_pos and b_neg and not a_neg and not b_pos:
            out.append(Divergence("polarity", f"{name}: {sorted(a_pos)} vs {sorted(b_neg)}"))
        elif a_neg and b_pos and not a_pos and not b_neg:
            out.append(Divergence("polarity", f"{name}: {sorted(a_neg)} vs {sorted(b_pos)}"))
    return out


def _negation_divergence(a: str, b: str) -> list[Divergence]:
    neg_a = bool(_NEGATION.search(a))
    neg_b = bool(_NEGATION.search(b))
    if neg_a != neg_b:
        return [Divergence("negation", f"negation polarity differs (a={neg_a}, b={neg_b})")]
    return []


def detect_divergence(a: str, b: str) -> list[Divergence]:
    """All detected factual divergences between two propositions.

    Empty result means "no conflict was detected" — NOT "these agree". Callers
    must not treat an empty list as positive evidence of agreement.
    """
    return (
        _negation_divergence(a, b)
        + _numeric_divergences(a, b)
        + _temporal_divergences(a, b)
        + _polarity_divergences(a, b)
    )


def has_negation_conflict(divergences: Iterable[Divergence]) -> bool:
    return any(d.kind == "negation" for d in divergences)


def describe(divergences: Iterable[Divergence]) -> str:
    items = list(divergences)
    if not items:
        return "no factual divergence detected"
    return "; ".join(f"{d.kind}: {d.detail}" for d in items)


def supported_checks() -> dict[str, Any]:
    """Inspectable description of what this module can and cannot catch."""
    return {
        "kinds": ["negation", "numeric", "temporal", "polarity"],
        "numeric": ["currency", "percent", "clock time", "plain/scaled integers"],
        "numericNormalization": ["12% == 12 percent", "1,000 == 1000", "$2 million == $2000000"],
        "temporal": ["weekday", "month + day", "year"],
        "polarityPairs": [name for name, _, _ in _POLARITY_PAIRS],
        "notCovered": [
            "general semantic entailment",
            "paraphrase with low lexical overlap",
            "unit conversion (miles vs kilometres)",
            "implicit contradiction requiring world knowledge",
            "antonyms outside the bounded pair list",
        ],
        "failureMode": "fail-closed: undetected divergence remains `uncertain`, never `compatible`",
    }
