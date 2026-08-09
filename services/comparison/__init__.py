"""Cross-document comparison: claims, alignment, and material omission.

Network-free. Operates only on an explicitly supplied ComparisonSet, which is
tagged with its provenance kind (`synthetic_fixture` vs `retrieved`) so
synthetic demonstration material can never be presented as real coverage.

The hard gate this package exists to enforce: Material Omission is a
cross-document conclusion. It cannot be produced from a single article, it
cannot outrun the confidence of the claim alignment beneath it, and it cannot
be asserted without a comparison set that actually contains the proposition.
"""
from .claims import Claim, ClaimAlignment, SourceAssertion, align_claims, align_pair
from .omission import (
    ComparisonSet,
    MaterialOmission,
    OmissionRejection,
    detect_material_omissions,
)
from .dependence import SourceDependency, independent_source_count

__all__ = [
    "Claim",
    "ClaimAlignment",
    "SourceAssertion",
    "align_claims",
    "align_pair",
    "ComparisonSet",
    "MaterialOmission",
    "OmissionRejection",
    "detect_material_omissions",
    "SourceDependency",
    "independent_source_count",
]
