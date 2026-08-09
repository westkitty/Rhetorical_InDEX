"""Level 3 Instrument Alpha rhetoric detector.

Network-free. Structurally complete, UNCALIBRATED: no benchmark has been run
against this pipeline, so this package makes no accuracy claim.

See services/rhetoric/README.md for the stage map and calibration status.
"""
from .document import Article, Passage, segment, article_from_passages, normalize_text
from .models import AnalysisRun, Finding
from .pipeline import (
    DETECTOR_VERSION,
    IMPLEMENTED_MECHANISMS,
    AnalysisResult,
    analyze_article,
    analyze_text,
    pressure_profile,
)
from .providers import (
    DetectorProvider,
    HeuristicDetectorProvider,
    MockDetectorProvider,
    ModelDetectorProvider,
    ProviderUnavailable,
    Verdict,
)
from .validation import DetectorFailure, DetectorRejection

__all__ = [
    "Article",
    "Passage",
    "segment",
    "article_from_passages",
    "normalize_text",
    "AnalysisRun",
    "Finding",
    "AnalysisResult",
    "analyze_article",
    "analyze_text",
    "pressure_profile",
    "DETECTOR_VERSION",
    "IMPLEMENTED_MECHANISMS",
    "DetectorProvider",
    "HeuristicDetectorProvider",
    "MockDetectorProvider",
    "ModelDetectorProvider",
    "ProviderUnavailable",
    "Verdict",
    "DetectorFailure",
    "DetectorRejection",
]
