"""Canonical controlled vocabulary, loaded from packages/schema/schema.json.

Python does not restate these values. It reads the same file TypeScript is
verified against, so cross-language vocabulary drift is impossible by
construction rather than merely detectable after the fact.

tests/python/test_vocabulary_parity.py verifies the runtime values here against
schema.json; tests/vocabulary-parity.test.mjs verifies the TypeScript literal
unions against the same file.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "packages" / "schema" / "schema.json"
TAXONOMY_PATH = ROOT / "packages" / "taxonomy" / "taxonomy.json"


@lru_cache(maxsize=1)
def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def _enum(name: str) -> frozenset[str]:
    prop = _schema()["properties"].get(name)
    if prop is None or "enum" not in prop:
        raise KeyError(f"schema.json has no enum property named {name!r}")
    return frozenset(prop["enum"])


def _enum_ordered(name: str) -> tuple[str, ...]:
    return tuple(_schema()["properties"][name]["enum"])


SCHEMA_VERSION: str = _schema()["schemaVersion"]

PRESSURE: frozenset[str] = _enum("pressureLevel")
CONFIDENCE: frozenset[str] = _enum("confidenceLevel")
VOICE: frozenset[str] = _enum("voiceClass")
INTRINSIC_ALPHA_SLICE: frozenset[str] = _enum("intrinsicAlphaSlice")
MECHANISM_FAMILY: frozenset[str] = _enum("mechanismFamily")
FINDING_STATE: frozenset[str] = _enum("findingState")
PASSAGE_TYPE: frozenset[str] = _enum("passageType")
ANALYSIS_RUN_STATUS: frozenset[str] = _enum("analysisRunStatus")
DETECTOR_PROVIDER_KIND: frozenset[str] = _enum("detectorProviderKind")
CLAIM_STATE: frozenset[str] = _enum("claimState")
ALIGNMENT_RELATION: frozenset[str] = _enum("alignmentRelation")
AUTHENTICITY_STATE: frozenset[str] = _enum("authenticityState")
EVIDENCE_DIRECTNESS: frozenset[str] = _enum("evidenceDirectness")
SOURCE_DEPENDENCE_TYPE: frozenset[str] = _enum("sourceDependenceType")
OMISSION_DIMENSION: frozenset[str] = _enum("omissionDimension")

# Ordered forms where ordinality is meaningful.
PRESSURE_ORDER: tuple[str, ...] = _enum_ordered("pressureLevel")
CONFIDENCE_ORDER: tuple[str, ...] = _enum_ordered("confidenceLevel")

# Mechanisms that are inherently cross-document and may NEVER be emitted by an
# intrinsic single-article scan (epistemic constitution rule 9).
CROSS_DOCUMENT_MECHANISMS: frozenset[str] = frozenset(
    {"material_omission", "selective_quotation", "headline_body_mismatch"}
)


def pressure_rank(level: str) -> int:
    """1-based ordinal rank. Raises on unknown input rather than defaulting."""
    if level not in PRESSURE:
        raise ValueError(f"unknown pressure level: {level!r}")
    return PRESSURE_ORDER.index(level) + 1


def confidence_rank(level: str) -> int:
    if level not in CONFIDENCE:
        raise ValueError(f"unknown confidence level: {level!r}")
    return CONFIDENCE_ORDER.index(level) + 1


@lru_cache(maxsize=1)
def taxonomy() -> dict:
    return json.loads(TAXONOMY_PATH.read_text())


@lru_cache(maxsize=1)
def taxonomy_version() -> str:
    return taxonomy()["version"]


@lru_cache(maxsize=1)
def mechanism_ids() -> frozenset[str]:
    return frozenset(m["id"] for m in taxonomy()["mechanisms"])


@lru_cache(maxsize=1)
def mechanisms_by_id() -> dict[str, dict]:
    return {m["id"]: m for m in taxonomy()["mechanisms"]}


def mechanism(mechanism_id: str) -> dict:
    record = mechanisms_by_id().get(mechanism_id)
    if record is None:
        raise ValueError(f"unknown mechanism id: {mechanism_id!r}")
    return record


def object_required_fields(object_name: str) -> tuple[str, ...]:
    """Required-field contract for a core domain object, from schema.json $defs."""
    defs = _schema()["$defs"]
    if object_name not in defs:
        raise KeyError(f"schema.json $defs has no object named {object_name!r}")
    return tuple(defs[object_name].get("required", ()))
