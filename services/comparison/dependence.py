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
