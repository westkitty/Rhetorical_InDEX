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

import bisect
import re
from dataclasses import dataclass
from decimal import Decimal
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

# Strict numeric literal grammar (review finding C-01).
#
# The previous body pattern was `\d[\d,]*`, which accepted ANY arrangement of
# digits and commas and then had every comma stripped during canonicalization.
# That silently turned structurally different source text into the SAME number:
# "1,2,3" / "1,00" / "12,34,567" / "1,,000" all canonicalized to the same
# values as "123" / "100" / "1234567" / "1000", so a malformed or entirely
# different numeral could establish `same_proposition` with an unrelated clean
# integer. Comma-stripping is only meaning-preserving for genuine thousands
# grouping; anywhere else a comma is a separator, not decoration.
#
# Accepted as ONE numeric token:
#   * ungrouped digits            1, 12, 123, 1000, 1000000
#   * correct thousands grouping  1,000  12,345  1,234,567
#   * either, with a fraction     1,234.50  1234.5
#
# Rejected as one token (each stays literal text, or splits into separate
# numerals with the comma surviving as text — never silently reflowed into a
# different clean integer):
#   1,2,3   1,00   12,34,567   1234,567   1,,000   ,1000   1000,
#
# The grouped alternative is tried FIRST: `\d+` would otherwise match only the
# leading run of "1,234,567" and strand the rest.
_NUM_BODY = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"

# Currency first, then percent, then scaled/bare numbers.
_NUM_CURRENCY = re.compile(
    r"(?P<sym>[$£€])\s?(?P<value>" + _NUM_BODY + r")\s*(?P<scale>hundred|thousand|million|billion|trillion|k|m|bn|b)?",
    re.IGNORECASE,
)
_NUM_PERCENT = re.compile(
    # Fresh-sweep finding: with a MANDATORY trailing suffix (`%` / "percent")
    # and no guard, a long digit run with no percent sign anywhere caused
    # catastrophic backtracking — O(n^2), ~9s for 10,000 digits, unbounded
    # for longer input. `(?<!\d)` stops finditer from retrying a match start
    # at every position INSIDE an already-failed digit run (only a position
    # not itself preceded by a digit can ever begin a distinct number), and
    # the atomic group `(?>...)` stops the engine from backtracking character
    # -by-character through the digits it already consumed once the suffix
    # check fails — backtracking into the digit run can never succeed here,
    # since only a literal `%` or "percent" immediately following (mod
    # whitespace) makes this a match at all. Together these make matching
    # linear in input length regardless of digit-run length.
    r"(?<!\d)(?P<value>(?>" + _NUM_BODY + r"))\s*(?:%|per\s?cent(?:age)?)",
    re.IGNORECASE,
)
_NUM_PLAIN = re.compile(
    r"(?<![\w$£€.])(?P<value>" + _NUM_BODY + r")\s*(?P<scale>hundred|thousand|million|billion|trillion)?(?![\w%])",
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


def _exact_decimal(raw: str) -> Decimal:
    """Parse a numeric literal exactly. Never routes through binary float."""
    return Decimal(_strip_commas(raw))


def _scale_exact(value: Decimal, multiplier: int) -> Decimal:
    """Multiply a Decimal by a positive integer scale factor with ZERO
    precision loss, regardless of operand magnitude or the ambient Decimal
    context's precision.

    Review finding B-01: ``value *= Decimal(multiplier)`` uses Python's
    ``decimal`` module's *context-bound* multiplication, which silently
    rounds to the active context's precision (28 significant digits by
    default). A 30-digit coefficient times ``1_000_000`` then rounds to 28
    significant digits, so ``123456789012345678901234567890`` and
    ``...67891`` (last digit different) both round to the same product —
    exactly the "arithmetic makes distinct values equal" failure this
    function exists to rule out entirely, not just push further out.

    The fix operates directly on the Decimal's ``(sign, digits, exponent)``
    tuple using Python's arbitrary-precision ``int`` for the multiplication —
    ``int * int`` is exact at any magnitude, with no ambient context, no
    configurable precision, and therefore nothing to misconfigure. The scale
    factor is a plain positive integer (100 .. 1_000_000_000_000), so
    multiplying the coefficient by it and leaving the exponent unchanged is
    exact: value = coefficient * 10**exponent, so
    value * multiplier = (coefficient * multiplier) * 10**exponent.
    """
    if multiplier <= 0:
        raise ValueError(f"scale multiplier must be positive, got {multiplier!r}")
    sign, digits, exponent = value.as_tuple()
    if not isinstance(exponent, int):
        # 'n' (NaN) / 'F' (Infinity) special exponents are never produced by
        # the numeric regexes this feeds from; guard defensively regardless.
        raise ValueError(f"cannot exactly scale a non-finite Decimal: {value!r}")
    coefficient = int("".join(map(str, digits)))
    scaled_coefficient = coefficient * multiplier
    scaled_digits = tuple(int(d) for d in str(scaled_coefficient))
    return Decimal((sign, scaled_digits, exponent))


def _format_exact(value: Decimal) -> str:
    """Exact fixed-point rendering: no scientific notation, no precision loss.

    ``Decimal.normalize()`` is not used here because it can itself emit
    scientific notation for trailing zeros (``Decimal("2000000").normalize()``
    -> ``Decimal("2E+6")``). Formatting with the ``f`` presentation type keeps
    every digit and forces fixed-point; only cosmetic trailing fractional
    zeros are trimmed afterward, which never changes the represented value.
    ``format(value, "f")`` is itself context-independent — it renders the
    Decimal's exact stored digits, it does not recompute or round them.
    """
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


IdentityToken = tuple[str, str]


def _normalize_text_fragment(fragment: str) -> str:
    """Presentation-only normalization of a literal (non-numeric) text span:
    case, curly-quote form, and whitespace. Never touches digits — numeric
    spans are extracted separately, before this ever runs on the remainder."""
    fragment = fragment.lower()
    fragment = re.sub(r"[‘’]", "'", fragment)
    fragment = re.sub(r"[“”]", '"', fragment)
    fragment = re.sub(r"\s+", " ", fragment)
    return fragment.strip()


def canonical_identity_key(text: str) -> tuple[IdentityToken, ...]:
    """The LOAD-BEARING structured identity representation.

    Returns an immutable sequence of typed ``(kind, value)`` tokens —
    ``("text", ...)`` for literal presentation-normalized prose, or
    ``("currency" | "percent" | "num", exact_value)`` for a numeric span
    extracted directly from the ORIGINAL source text. ``propositions_are_identical``
    compares this tuple. It never compares a rendered string.

    Review finding B-02: the previous representation was a single string with
    numeric spans replaced by a marker substring (``"«num:x1000»"``). A marker
    is still just characters, and characters are exactly what source text is
    made of — a proposition whose literal wording happened to CONTAIN that
    substring (coincidentally, or via deliberate injection) canonicalized to
    the identical string as a proposition containing the real number 1000,
    letting fabricated text impersonate a numeric token and falsely establish
    `same_proposition`.

    A tuple of typed tokens closes this by construction, not by making the
    marker syntax harder to collide with: a ``("text", "...")`` token can
    never compare equal to a ``("num", "...")`` token regardless of what
    string content the text token holds, because tuple equality requires
    the KIND to match, not merely the printable characters. Source text is
    never reclassified as numeric after the fact — the only way a numeric
    token is ever produced is a direct regex match against the ORIGINAL
    characters of `text`, before any token has been constructed. There is no
    later string-level pass in which literal text could be mistaken for one.

    Word ORDER is deliberately preserved (as token order), because order
    carries semantic role: "injured 12 and killed 40" and "injured 40 and
    killed 12" contain identical tokens and opposite meanings. Any
    bag-of-tokens comparison is blind to that, which is exactly how M-01 let
    contradictions ground an omission.
    """
    import unicodedata

    text = unicodedata.normalize("NFC", text)

    # `consumed` is kept sorted by start (via bisect.insort) so overlap
    # checks are O(log k) instead of an O(k) linear scan. Fresh-sweep
    # finding: the linear scan made this function O(k^2) in the number of
    # numeric matches — a long, realistic article with hundreds of numbers
    # (dates, currency, percentages) took multiple seconds; pathologically
    # many would be a genuine DoS vector, in the exact function this defect
    # was supposed to hold at the invariant level.
    consumed: list[tuple[int, int]] = []
    numeric_spans: list[tuple[int, int, str, str]] = []

    def _already_consumed(start: int) -> bool:
        idx = bisect.bisect_right(consumed, (start, len(text) + 1)) - 1
        if idx < 0:
            return False
        span_start, span_end = consumed[idx]
        return span_start <= start < span_end

    for match in _NUM_CURRENCY.finditer(text):
        value = _exact_decimal(match.group("value"))
        scale = match.group("scale")
        if scale:
            value = _scale_exact(value, _SCALE[scale.lower()])
        bisect.insort(consumed, match.span())
        numeric_spans.append((match.start(), match.end(), "currency", _format_exact(value)))

    for match in _NUM_PERCENT.finditer(text):
        if _already_consumed(match.start()):
            continue
        value = _exact_decimal(match.group("value"))
        bisect.insort(consumed, match.span())
        numeric_spans.append((match.start(), match.end(), "percent", _format_exact(value)))

    for match in _NUM_PLAIN.finditer(text):
        if _already_consumed(match.start()):
            continue
        value = _exact_decimal(match.group("value"))
        scale = match.group("scale")
        if scale:
            value = _scale_exact(value, _SCALE[scale.lower()])
        bisect.insort(consumed, match.span())
        numeric_spans.append((match.start(), match.end(), "num", _format_exact(value)))

    numeric_spans.sort(key=lambda item: item[0])

    tokens: list[IdentityToken] = []
    cursor = 0
    for start, end, kind, value in numeric_spans:
        if start < cursor:
            continue  # defensive: the priority scan above is already non-overlapping
        literal = _normalize_text_fragment(text[cursor:start])
        if literal:
            tokens.append(("text", literal))
        tokens.append((kind, value))
        cursor = end

    trailing = text[cursor:]
    if trailing:
        trailing = _normalize_text_fragment(trailing)
        # Terminal punctuation only ever applies at the true end of the
        # proposition — matching the previous whole-string behaviour, where
        # the strip regex was anchored to the end of the fully assembled
        # string. Here that is exactly (and only) the final trailing fragment.
        trailing = re.sub(r"[.,;:!?]+$", "", trailing).strip()
        if trailing:
            tokens.append(("text", trailing))

    return tuple(tokens)


def canonical_proposition(text: str) -> str:
    """Diagnostic-only rendering of `canonical_identity_key`. NOT used for
    identity comparison — see `canonical_identity_key` and
    `propositions_are_identical`, which compare the structured tuple
    directly and never call this function.

    This exists for logs and debugging, where a readable string is more
    useful than a tuple. It is deliberately NOT the load-bearing
    representation: two propositions could in principle render to the same
    diagnostic string while still legitimately comparing as non-identical
    (this was exactly finding B-02 — a string-shaped rendering shares the
    same character space as source text and is not safe as an identity key).
    Do not reintroduce string comparison of this function's output as a
    substitute for `canonical_identity_key` equality.
    """
    return " ".join(
        value if kind == "text" else f"[{kind}:x{value}]"
        for kind, value in canonical_identity_key(text)
    )


def propositions_are_identical(a: str, b: str) -> bool:
    """Whether two propositions are the SAME proposition.

    Compares `canonical_identity_key`, the structured typed-token
    representation — never a rendered string (see B-02). This is the only
    affirmative identity signal in the system. It is deliberately strict:
    absence of detected divergence is NOT evidence of identity, so nothing
    else may assert `same_proposition`.
    """
    return canonical_identity_key(a) == canonical_identity_key(b)


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
