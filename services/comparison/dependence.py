"""Source dependence.

Ten articles repeating one wire story are not ten independent reports. Treating
them as independent is how coverage consensus quietly becomes a truth claim.

``unknown`` is the honest default and is treated CONSERVATIVELY: an unknown
relationship does not get to count as independence when the answer would
strengthen a downstream assertion.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from services.rhetoric import vocabulary as vocab

# Relationships that collapse two sources into one origin for corroboration.
_DEPENDENT_RELATIONS = frozenset({"syndication", "quotation", "citation", "shared_source"})


@dataclass(frozen=True)
class SourceDependency:
    source_pair: tuple[str, str]
    relationship_type: str
    confidence: str
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.relationship_type not in vocab.SOURCE_DEPENDENCE_TYPE:
            raise ValueError(f"invalid source dependence type: {self.relationship_type!r}")
        if self.confidence not in vocab.CONFIDENCE:
            raise ValueError(f"invalid dependence confidence: {self.confidence!r}")
        if len(self.source_pair) != 2:
            raise ValueError("source_pair must contain exactly two source ids")

    @property
    def collapses_origins(self) -> bool:
        """Whether this link means the two sources share one origin.

        A Low-confidence dependence claim still collapses them: when we are
        unsure whether two reports are independent, the conservative reading is
        that they may not be. Overstating independence inflates corroboration.
        """
        return self.relationship_type in _DEPENDENT_RELATIONS

    def to_dict(self) -> dict[str, Any]:
        return {
            "sourcePair": list(self.source_pair),
            "relationshipType": self.relationship_type,
            "confidence": self.confidence,
            "notes": self.notes,
        }


def independent_source_count(
    source_ids: Sequence[str], dependencies: Iterable[SourceDependency]
) -> int:
    """Count distinct independent origins via union-find over dependence links."""
    unique = list(dict.fromkeys(source_ids))
    if not unique:
        return 0

    parent = {source_id: source_id for source_id in unique}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for dependency in dependencies:
        left, right = dependency.source_pair
        if left in parent and right in parent and dependency.collapses_origins:
            union(left, right)

    return len({find(source_id) for source_id in unique})


@dataclass(frozen=True)
class IndependenceAssessment:
    """Tri-state independence: confirmed / dependent / unresolved.

    Review finding M-02: counting distinct source ids as independent origins
    silently converts *absence of dependency data* into *evidence of
    independence*. It is not. A pair is only confirmed independent when an
    explicit `independent_reporting` link asserts it; otherwise it is
    unresolved, and unresolved must never satisfy a hard corroboration gate.
    """

    source_ids: tuple[str, ...]
    origin_count: int
    confirmed_independent_pairs: tuple[tuple[str, str], ...]
    dependent_pairs: tuple[tuple[str, str], ...]
    unresolved_pairs: tuple[tuple[str, str], ...]

    @property
    def confirmed_independent_count(self) -> int:
        """Sources provable to be mutually independent.

        Returns the size of the largest set of sources in which EVERY pair is
        explicitly confirmed independent. Anything unresolved is excluded, so
        this number can only be earned, never assumed.
        """
        if len(self.source_ids) < 2:
            return len(self.source_ids)
        confirmed = {frozenset(p) for p in self.confirmed_independent_pairs}
        best = 1
        # Source sets here are tiny (a comparison set of articles); exhaustive
        # clique search is both adequate and deterministic.
        from itertools import combinations
        for size in range(len(self.source_ids), 1, -1):
            for group in combinations(sorted(self.source_ids), size):
                if all(frozenset(pair) in confirmed for pair in combinations(group, 2)):
                    return size
            if size <= best:
                break
        return best

    @property
    def has_unresolved(self) -> bool:
        return bool(self.unresolved_pairs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sourceIds": list(self.source_ids),
            "originCount": self.origin_count,
            "confirmedIndependentCount": self.confirmed_independent_count,
            "confirmedIndependentPairs": [list(p) for p in self.confirmed_independent_pairs],
            "dependentPairs": [list(p) for p in self.dependent_pairs],
            "unresolvedPairs": [list(p) for p in self.unresolved_pairs],
            "note": (
                "Independence is never inferred from the absence of dependency data. "
                "Unresolved pairs are reported as unresolved and do not count toward "
                "confirmed independence."
            ),
        }


def assess_independence(
    source_ids: Sequence[str], dependencies: Iterable[SourceDependency]
) -> IndependenceAssessment:
    """Classify every source pair as confirmed-independent, dependent, or unresolved."""
    from itertools import combinations

    unique = tuple(dict.fromkeys(source_ids))
    dependency_list = list(dependencies)

    confirmed: list[tuple[str, str]] = []
    dependent: list[tuple[str, str]] = []
    unresolved: list[tuple[str, str]] = []

    def _lookup(a: str, b: str) -> SourceDependency | None:
        for dependency in dependency_list:
            if set(dependency.source_pair) == {a, b}:
                return dependency
        return None

    for a, b in combinations(unique, 2):
        dependency = _lookup(a, b)
        if dependency is None:
            unresolved.append((a, b))
        elif dependency.collapses_origins:
            dependent.append((a, b))
        elif dependency.relationship_type == "independent_reporting" and \
                vocab.confidence_rank(dependency.confidence) >= 2:
            confirmed.append((a, b))
        else:
            # `unknown`, or independent_reporting asserted only at Low
            # confidence, is not good enough to be called independence.
            unresolved.append((a, b))

    return IndependenceAssessment(
        source_ids=unique,
        origin_count=independent_source_count(unique, dependency_list),
        confirmed_independent_pairs=tuple(confirmed),
        dependent_pairs=tuple(dependent),
        unresolved_pairs=tuple(unresolved),
    )


def describe_independence(
    source_ids: Sequence[str], dependencies: Iterable[SourceDependency]
) -> dict[str, Any]:
    dependency_list = list(dependencies)
    independent = independent_source_count(source_ids, dependency_list)
    unique = list(dict.fromkeys(source_ids))
    unknown_pairs = [
        d for d in dependency_list if d.relationship_type == "unknown"
    ]
    return {
        "rawSourceCount": len(unique),
        "independentOriginCount": independent,
        "collapsed": len(unique) - independent,
        "unknownRelationships": len(unknown_pairs),
        "note": (
            "Independence is not assumed. Sources linked by syndication, quotation, "
            "citation or a shared origin are counted once."
            + (
                f" {len(unknown_pairs)} relationship(s) remain unknown and are not "
                "claimed as independent."
                if unknown_pairs
                else ""
            )
        ),
    }
