import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import vm from 'node:vm';

// F-001: prove that the real, compiled localPreviewFindings() output — the
// Level 2 Local Preview heuristic detector — satisfies the same semantic
// contract enforced by services/api/detector_contract.py's
// validate_intrinsic_candidate(), so the two never silently diverge.
//
// This test executes the ACTUAL compiled functions extracted verbatim from
// apps/web/dist/app.js (produced by `npm run build`), not a reimplementation.
// Run `npm run build` before this test if apps/web/dist/app.js is missing or
// stale, exactly as tests/artifact.test.mjs already assumes for dist/index.html.

const distAppJsPath = new URL('../apps/web/dist/app.js', import.meta.url);
assert.ok(fs.existsSync(distAppJsPath), 'apps/web/dist/app.js missing — run `npm run build` first');
const compiled = fs.readFileSync(distAppJsPath, 'utf8');

const taxonomy = JSON.parse(fs.readFileSync(new URL('../packages/taxonomy/taxonomy.json', import.meta.url)));
const schema = JSON.parse(fs.readFileSync(new URL('../packages/schema/schema.json', import.meta.url)));
const fixture = JSON.parse(fs.readFileSync(new URL('../packages/fixtures/sb802-demo.json', import.meta.url)));

function extractFunctionSource(source, signatureStart) {
  const start = source.indexOf(signatureStart);
  assert.ok(start >= 0, `${signatureStart} not found in apps/web/dist/app.js`);
  const braceOpen = source.indexOf('{', start);
  let depth = 0;
  for (let i = braceOpen; i < source.length; i += 1) {
    if (source[i] === '{') depth += 1;
    else if (source[i] === '}') {
      depth -= 1;
      if (depth === 0) return source.slice(start, i + 1);
    }
  }
  throw new Error(`unbalanced braces extracting ${signatureStart}`);
}

const validateSrc = extractFunctionSource(compiled, 'function validateLocalPreviewCandidate(');
const fnv1aSrc = extractFunctionSource(compiled, 'function fnv1a(');
const localPreviewFindingsSrc = extractFunctionSource(compiled, 'function localPreviewFindings(');

const vocabulary = Object.fromEntries(
  Object.entries(schema.properties)
    .filter(([, value]) => Array.isArray(value.enum))
    .map(([key, value]) => [key, value.enum]),
);

const sandbox = {
  DATA: { taxonomy: { version: taxonomy.version }, vocabulary },
  TAXONOMY: new Map(taxonomy.mechanisms.map((m) => [m.id, { family: m.family }])),
  Date,
  console,
};
vm.createContext(sandbox);
vm.runInContext(`${validateSrc}\n${fnv1aSrc}\n${localPreviewFindingsSrc}`, sandbox);

const sentinelArticle = fixture.event.articles.find((a) => a.id === 'art-sentinel-802');
const testParagraphs = [
  ...sentinelArticle.paragraphs,
  // Ensures agent_suppression coverage: passive voice with no "by [agent]" clause.
  'Mistakes were made during the review, and shots were fired near the checkpoint.',
];
const article = {
  id: 'local-preview-contract-test',
  content: testParagraphs.join('\n\n'),
  paragraphs: testParagraphs,
};

const result = sandbox.localPreviewFindings(article);

test('localPreviewFindings produces at least one candidate on representative text', () => {
  assert.ok(result.findings.length > 0, 'expected local preview to emit candidates for the test fixture text');
});

test('every localPreviewFindings candidate satisfies the TypeScript validator contract by construction', () => {
  // rejectedCount stays 0 on this input because every candidate is well-formed
  // by construction (regex match indices are always in-bounds). A future
  // regression that produces a malformed candidate would surface here as a
  // nonzero rejectedCount rather than as silently-dropped/corrupted output.
  assert.equal(result.rejectedCount, 0, 'no candidate should be silently rejected on well-formed input');
});

test('every localPreviewFindings candidate is accepted by the real Python detector_contract validator', () => {
  assert.ok(result.findings.length > 0);

  const candidates = result.findings.map((finding) => {
    const paragraph = testParagraphs[finding.span.paragraphIndex];
    const text = finding.span.text;
    const occurrences = [];
    let cursor = 0;
    for (;;) {
      const pos = paragraph.indexOf(text, cursor);
      if (pos < 0) break;
      occurrences.push(pos);
      cursor = pos + 1;
    }
    const occurrenceIndex = occurrences.indexOf(finding.span.startChar);
    assert.ok(occurrenceIndex >= 0, `finding ${finding.id} span does not round-trip to its own paragraph`);
    return {
      paragraphIndex: finding.span.paragraphIndex,
      exactText: text,
      occurrenceIndex: occurrences.length > 1 ? occurrenceIndex : undefined,
      mechanism: finding.mechanism,
      pressure: finding.pressure,
      confidence: finding.confidence,
      voiceClass: finding.voiceClass,
      triggeredCriteria: finding.triggeredCriteria,
    };
  });

  const script = `
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("detector_contract", "services/api/detector_contract.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
payload = json.loads(sys.stdin.read())
paragraphs = payload["paragraphs"]
results = []
for candidate in payload["candidates"]:
    try:
        module.validate_intrinsic_candidate(paragraphs, candidate)
        results.append({"ok": True})
    except ValueError as exc:
        results.append({"ok": False, "error": str(exc)})
print(json.dumps(results))
`;
  const proc = spawnSync('python3', ['-c', script], {
    cwd: new URL('..', import.meta.url).pathname,
    input: JSON.stringify({ paragraphs: testParagraphs, candidates }),
    encoding: 'utf8',
  });
  assert.equal(proc.status, 0, proc.stderr);
  const results = JSON.parse(proc.stdout);
  results.forEach((r, i) => {
    assert.ok(r.ok, `Python detector_contract rejected Local Preview candidate ${i} (${candidates[i].mechanism} @ paragraph ${candidates[i].paragraphIndex}): ${r.error}`);
  });
});

test('localPreviewFindings never emits Material Omission or any cross-document mechanism', () => {
  for (const finding of result.findings) {
    assert.ok(vocabulary.intrinsicAlphaSlice.includes(finding.mechanism), `unexpected mechanism ${finding.mechanism}`);
    assert.notEqual(finding.mechanism, 'material_omission');
  }
});
