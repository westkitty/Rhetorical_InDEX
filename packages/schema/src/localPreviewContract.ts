// Local Preview integrity boundary (Level 2 detector).
//
// Mirrors the invariants enforced by services/api/detector_contract.py for the
// same bounded four-mechanism intrinsic Alpha slice, so heuristic candidates
// produced in the browser cannot silently violate the same semantic contract
// the future Level 3 Instrument Alpha detector must satisfy. This module does
// not fetch anything and does not run a server; it validates data that is
// already local to the page.
//
// Allowed vocabulary is read from window.RI_BOOTSTRAP.vocabulary, which is
// generated at build time directly from packages/schema/schema.json (see
// tools/build_web.py) rather than being retyped here. tests/vocabulary-parity
// .test.mjs and tests/python/test_vocabulary_parity.py fail if this vocabulary
// ever disagrees with services/api/detector_contract.py.

class LocalPreviewIntegrityError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'LocalPreviewIntegrityError';
  }
}

interface LocalPreviewCandidate {
  paragraphIndex: number;
  startChar: number;
  endChar: number;
  mechanism: MechanismId;
  pressure: PressureLevel;
  confidence: ConfidenceLevel;
  voiceClass: VoiceClass;
  triggeredCriteria: string[];
}

function validateLocalPreviewCandidate(
  vocabulary: CanonicalVocabulary,
  paragraphs: string[],
  candidate: LocalPreviewCandidate,
): LocalPreviewCandidate {
  if (!vocabulary.intrinsicAlphaSlice.includes(candidate.mechanism)) {
    throw new LocalPreviewIntegrityError(`unknown or cross-document mechanism for intrinsic alpha slice: ${candidate.mechanism}`);
  }
  if (!vocabulary.pressureLevel.includes(candidate.pressure)) {
    throw new LocalPreviewIntegrityError(`invalid pressure: ${candidate.pressure}`);
  }
  if (!vocabulary.confidenceLevel.includes(candidate.confidence)) {
    throw new LocalPreviewIntegrityError(`invalid confidence: ${candidate.confidence}`);
  }
  if (!vocabulary.voiceClass.includes(candidate.voiceClass)) {
    throw new LocalPreviewIntegrityError(`invalid voice class: ${candidate.voiceClass}`);
  }
  if (!Number.isInteger(candidate.paragraphIndex) || candidate.paragraphIndex < 0 || candidate.paragraphIndex >= paragraphs.length) {
    throw new LocalPreviewIntegrityError(`invalid paragraph index: ${candidate.paragraphIndex}`);
  }
  if (
    !Array.isArray(candidate.triggeredCriteria) ||
    candidate.triggeredCriteria.length === 0 ||
    !candidate.triggeredCriteria.every((criterion) => typeof criterion === 'string' && criterion.trim().length > 0)
  ) {
    throw new LocalPreviewIntegrityError('invalid triggered criteria');
  }
  const paragraph = paragraphs[candidate.paragraphIndex];
  if (
    !Number.isInteger(candidate.startChar) ||
    !Number.isInteger(candidate.endChar) ||
    candidate.startChar < 0 ||
    candidate.endChar <= candidate.startChar ||
    candidate.endChar > paragraph.length
  ) {
    throw new LocalPreviewIntegrityError('invalid span bounds');
  }
  const exactText = paragraph.slice(candidate.startChar, candidate.endChar);
  if (!exactText.trim()) {
    throw new LocalPreviewIntegrityError('missing exact text');
  }
  if (paragraph.indexOf(exactText) < 0) {
    throw new LocalPreviewIntegrityError('exact text not found in referenced passage');
  }
  return candidate;
}
