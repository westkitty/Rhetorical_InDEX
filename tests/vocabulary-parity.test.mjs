import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { spawnSync } from 'node:child_process';

// F-002: prove TypeScript and Python vocabulary cannot silently drift from each
// other, or from the single canonical source in packages/schema/schema.json.

const contracts = fs.readFileSync(new URL('../packages/schema/src/contracts.ts', import.meta.url), 'utf8');
const app = fs.readFileSync(new URL('../apps/web/src/app.ts', import.meta.url), 'utf8');
const detectorContract = fs.readFileSync(new URL('../services/api/detector_contract.py', import.meta.url), 'utf8');
const schema = JSON.parse(fs.readFileSync(new URL('../packages/schema/schema.json', import.meta.url)));
const taxonomy = JSON.parse(fs.readFileSync(new URL('../packages/taxonomy/taxonomy.json', import.meta.url)));

function extractTsUnion(typeName) {
  const marker = `type ${typeName} =`;
  const start = contracts.indexOf(marker);
  assert.ok(start >= 0, `${typeName} not found in packages/schema/src/contracts.ts`);
  const end = contracts.indexOf(';', start);
  const block = contracts.slice(start + marker.length, end);
  return [...block.matchAll(/'([^']+)'/g)].map((m) => m[1]).sort();
}

// Python no longer restates the vocabulary as literals — it reads schema.json
// directly (services/api/detector_contract.py, services/rhetoric/vocabulary.py),
// so drift is impossible by construction. We therefore verify Python's RUNTIME
// values rather than grepping for literals: a stronger check than the string
// match it replaces, since it would also catch a bad loader.
function pythonRuntimeVocabulary() {
  const script = `
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("detector_contract", "services/api/detector_contract.py")
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
print(json.dumps({
    "PRESSURE": sorted(m.PRESSURE),
    "CONFIDENCE": sorted(m.CONFIDENCE),
    "VOICE": sorted(m.VOICE),
    "INTRINSIC_ALPHA_SLICE": sorted(m.INTRINSIC_ALPHA_SLICE),
}))
`;
  const proc = spawnSync('python3', ['-c', script], {
    cwd: new URL('..', import.meta.url).pathname,
    encoding: 'utf8',
  });
  assert.equal(proc.status, 0, proc.stderr);
  return JSON.parse(proc.stdout);
}

test('TypeScript pressure/confidence/voice unions match the canonical schema vocabulary', () => {
  assert.deepEqual(extractTsUnion('PressureLevel'), [...schema.properties.pressureLevel.enum].sort());
  assert.deepEqual(extractTsUnion('ConfidenceLevel'), [...schema.properties.confidenceLevel.enum].sort());
  assert.deepEqual(extractTsUnion('VoiceClass'), [...schema.properties.voiceClass.enum].sort());
});

test('TypeScript MechanismId union matches the canonical taxonomy mechanism ids', () => {
  assert.deepEqual(extractTsUnion('MechanismId'), taxonomy.mechanisms.map((m) => m.id).sort());
});

test('Python detector_contract runtime vocabulary matches the canonical schema vocabulary', () => {
  const py = pythonRuntimeVocabulary();
  assert.deepEqual(py.PRESSURE, [...schema.properties.pressureLevel.enum].sort());
  assert.deepEqual(py.CONFIDENCE, [...schema.properties.confidenceLevel.enum].sort());
  assert.deepEqual(py.VOICE, [...schema.properties.voiceClass.enum].sort());
  assert.deepEqual(py.INTRINSIC_ALPHA_SLICE, [...schema.properties.intrinsicAlphaSlice.enum].sort());
});

test('TypeScript and Python VOCABULARY agree with each other (not domain object shapes)', () => {
  const py = pythonRuntimeVocabulary();
  assert.deepEqual(extractTsUnion('PressureLevel'), py.PRESSURE);
  assert.deepEqual(extractTsUnion('ConfidenceLevel'), py.CONFIDENCE);
  assert.deepEqual(extractTsUnion('VoiceClass'), py.VOICE);
});

test('canonical intrinsic Alpha slice is a subset of both the taxonomy and the TypeScript MechanismId contract', () => {
  const taxonomyIds = new Set(taxonomy.mechanisms.map((m) => m.id));
  const tsIds = new Set(extractTsUnion('MechanismId'));
  for (const id of schema.properties.intrinsicAlphaSlice.enum) {
    assert.ok(taxonomyIds.has(id), `${id} missing from taxonomy.json`);
    assert.ok(tsIds.has(id), `${id} missing from TypeScript MechanismId contract`);
  }
});

test('Local Preview heuristic never emits a mechanism outside the canonical intrinsic Alpha slice', () => {
  const start = app.indexOf('function localPreviewFindings');
  const end = app.indexOf('function loadPasteArticle');
  assert.ok(start >= 0 && end > start);
  const body = app.slice(start, end);
  const knownIds = taxonomy.mechanisms.map((m) => m.id);
  const pattern = new RegExp(`'(${knownIds.join('|')})'`, 'g');
  const emitted = new Set([...body.matchAll(pattern)].map((m) => m[1]));
  assert.deepEqual([...emitted].sort(), [...schema.properties.intrinsicAlphaSlice.enum].sort());
});
