"""Evidence architecture.

This is fact-checking ARCHITECTURE, not a fact checker. There is no retrieval,
no authentication service and no verdict engine. What exists is the data model
that a real evidence layer would need, with the epistemic guards already in
place so they cannot be skipped later.

Guards enforced here:
  * Primary evidence is NOT automatically true (rule 11). ``authenticity_state``
    defaults to ``unverified`` and cannot be set to ``verified`` without a
    stated basis.
  * Evidence strength is ranked by evidentiary characteristics, never by how
    many outlets repeated it (rule 10).
  * A claim's state may not be stronger than the evidence supporting it.
"""
from .items import (
    EvidenceItem,
    EvidenceRelation,
    EvidenceStrength,
    claim_state_for,
    rank_evidence,
)

__all__ = [
    "EvidenceItem",
    "EvidenceRelation",
    "EvidenceStrength",
    "claim_state_for",
    "rank_evidence",
]
