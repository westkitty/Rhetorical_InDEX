type PressureLevel = 'P1' | 'P2' | 'P3' | 'P4';
type ConfidenceLevel = 'Low' | 'Medium' | 'High';
type FindingState = 'candidate' | 'confirmed';
type VoiceClass = 'headline' | 'reporter' | 'editorial' | 'quoted_speaker' | 'paraphrased_source' | 'document_material' | 'uncertain';
type MechanismFamily = 'intrinsic_linguistic' | 'framing_epistemic' | 'agency_causality' | 'journalism_cross_doc';
type MechanismId =
  | 'loaded_language'
  | 'euphemism_dysphemism'
  | 'presupposition'
  | 'epistemic_overstatement'
  | 'agent_suppression'
  | 'appeal_to_fear'
  | 'false_dilemma'
  | 'hasty_generalization'
  | 'causal_overclaim'
  | 'headline_body_mismatch'
  | 'selective_quotation'
  | 'material_omission';

interface TaxonomyMechanism {
  id: MechanismId;
  canonicalName: string;
  family: MechanismFamily;
  definition: string;
  positiveCriteria: string[];
  exclusionCriteria: string[];
  pressureRubric: { p1: string; p2: string; p3: string; p4: string };
  requiredContext: string;
  confusableNeighbors: { neighborId: MechanismId; distinction: string }[];
  positiveExamples: { text: string; rationale: string; pressure: PressureLevel }[];
  negativeExamples: { text: string; whyNot: string }[];
  version: string;
}

interface SpanLocation {
  startChar: number;
  endChar: number;
  paragraphIndex: number;
  sentenceIndex?: number;
  text: string;
}

interface Finding {
  id: string;
  articleId: string;
  span: SpanLocation;
  mechanism: MechanismId;
  family: MechanismFamily;
  pressure: PressureLevel;
  confidence: ConfidenceLevel;
  state: FindingState;
  voiceClass: VoiceClass;
  triggeredCriteria: string[];
  nearMissCriteria?: string[];
  alternateInterpretation?: string;
  detectorVotes?: { detector: string; vote: boolean }[];
  taxonomyVersion: string;
  detectorVersion: string;
  analysisRunId: string;
  timestamp: string;
}

interface Article {
  id: string;
  sourceId: string;
  title: string;
  author?: string;
  publisher: string;
  url: string;
  publishedAt: string;
  updatedAt?: string;
  extractedAt: string;
  content: string;
  paragraphs: string[];
  snapshotHash: string;
}

interface SourceWording {
  sourceId: string;
  sourceName: string;
  excerpt: string;
  articleTitle: string;
  articleUrl: string;
  publishedAt: string;
  pressure?: PressureLevel;
  mechanismIds?: MechanismId[];
}

type ClaimState = 'supported_by_direct_evidence' | 'corroborated' | 'contested' | 'contradicted_by_evidence' | 'unverified' | 'non_factual' | 'retrieval_incomplete';
interface Claim {
  id: string;
  eventId: string;
  normalizedClaim: string;
  sourceWordings: SourceWording[];
  attribution?: string;
  firstKnownTimestamp: string;
  state: ClaimState;
  evidenceItemIds: string[];
  confidence: ConfidenceLevel;
}

interface EvidenceItem {
  id: string;
  title: string;
  type: string;
  description: string;
  provenanceUrl?: string;
  directness: 'direct' | 'contextual' | 'derivative';
  authenticityState: 'verified' | 'unverified' | 'disputed';
  publishedAt: string;
  excerptText?: string;
}

interface MaterialOmission {
  id: string;
  articleId: string;
  missingClaim: string;
  dimension: string;
  rationale: string;
  supportingSources: string[];
  primaryEvidenceIds: string[];
  knowableAtTimestamp: string;
  confidence: ConfidenceLevel;
  isLaterDevelopment?: boolean;
}

interface EventRecord {
  id: string;
  title: string;
  description: string;
  timeWindow: { start: string; end: string };
  memberArticleIds: string[];
  articles: Article[];
  atomicClaims: Claim[];
  primaryEvidence: EvidenceItem[];
  sourceDependencies: unknown[];
  omissions: MaterialOmission[];
  versionHistory: { version: number; timestamp: string; summary: string }[];
}

type ScanStage = 'received' | 'intrinsic_analysis' | 'article_ready' | 'complete' | 'partial' | 'failed';
interface AnalysisRun {
  runId: string;
  scanMode: 'synthetic_fixture' | 'local_preview';
  articleSnapshotHash: string;
  taxonomyVersion: string;
  detectorVersion: string;
  timestamp: string;
  stage: ScanStage;
  findingsCount: number;
  /** null when there are no findings: absence of pressure is not P1 (O-04). */
  peakPressure: PressureLevel | null;
  confirmedDensity: number;
  candidateDensity: number;
  processedParagraphs: number[];
  unprocessedParagraphs: number[];
}

type AnalysisRunStatus = 'processing' | 'complete' | 'partial' | 'failed';
type PassageType = 'heading' | 'paragraph' | 'blockquote' | 'list_item' | 'caption' | 'other';
type DetectorProviderKind = 'mock' | 'heuristic' | 'model';
type AlignmentRelation = 'same_proposition' | 'compatible' | 'more_specific' | 'less_specific' | 'contradictory' | 'unrelated' | 'uncertain';
type AuthenticityState = 'verified' | 'unverified' | 'disputed';
type SourceDependenceType = 'independent_reporting' | 'syndication' | 'quotation' | 'citation' | 'shared_source' | 'unknown';

interface CanonicalVocabulary {
  pressureLevel: PressureLevel[];
  confidenceLevel: ConfidenceLevel[];
  voiceClass: VoiceClass[];
  intrinsicAlphaSlice: MechanismId[];
  mechanismFamily: MechanismFamily[];
  findingState: FindingState[];
  passageType: PassageType[];
  analysisRunStatus: AnalysisRunStatus[];
  detectorProviderKind: DetectorProviderKind[];
  claimState: ClaimState[];
  alignmentRelation: AlignmentRelation[];
  authenticityState: AuthenticityState[];
  evidenceDirectness: EvidenceItem['directness'][];
  sourceDependenceType: SourceDependenceType[];
  omissionDimension: string[];
}

interface BootstrapData {
  taxonomy: { version: string; mechanisms: TaxonomyMechanism[] };
  fixture: { mode: 'synthetic_fixture'; event: EventRecord; findings: Finding[] };
  vocabulary: CanonicalVocabulary;
}

interface Window {
  RI_BOOTSTRAP: BootstrapData;
}
