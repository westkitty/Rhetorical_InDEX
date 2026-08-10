import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

// Level 2 (browser Local Preview) hardening regressions: M-15, O-03, O-04.
//
// These execute the REAL compiled functions from apps/web/dist/app.js — not a
// reimplementation — so they fail if the shipped browser bundle regresses.
// Run `npm run build` first.

const compiled = fs.readFileSync(new URL('../apps/web/dist/app.js', import.meta.url), 'utf8');
const taxonomy = JSON.parse(fs.readFileSync(new URL('../packages/taxonomy/taxonomy.json', import.meta.url)));
const schema = JSON.parse(fs.readFileSync(new URL('../packages/schema/schema.json', import.meta.url)));

function extractFunction(signature) {
  const start = compiled.indexOf(signature);
  assert.ok(start >= 0, `${signature} not found in the compiled bundle`);
  const braceOpen = compiled.indexOf('{', start);
  let depth = 0;
  for (let i = braceOpen; i < compiled.length; i += 1) {
    if (compiled[i] === '{') depth += 1;
    else if (compiled[i] === '}') {
      depth -= 1;
      if (depth === 0) return compiled.slice(start, i + 1);
    }
  }
  throw new Error(`unbalanced braces extracting ${signature}`);
}

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
vm.runInContext(
  [
    'function pressureNumber(p){return Number(String(p).slice(1));}',
    extractFunction('function validateLocalPreviewCandidate('),
    extractFunction('function fnv1a('),
    extractFunction('function localQuotedRegions('),
    extractFunction('function classifyLocalVoice('),
    extractFunction('function localPreviewFindings('),
    extractFunction('function calculateCoverage('),
    extractFunction('function calculateMetrics('),
  ].join('\n'),
  sandbox,
);

function analyze(text) {
  const paragraphs = text.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
  return sandbox.localPreviewFindings({
    id: 'local-test',
    content: paragraphs.join('\n\n'),
    paragraphs,
  });
}

// -------------------------------------------------------------------------
// M-15 — quoted rhetoric must not be attributed to the publication
// -------------------------------------------------------------------------

test('M-15: quoted loaded language is attributed to the speaker, not the outlet', () => {
  const { findings } = analyze('The mayor said "this is a draconian, reckless scheme" on Tuesday.');
  assert.ok(findings.length > 0, 'expected findings inside the quotation');
  for (const finding of findings) {
    assert.equal(finding.voiceClass, 'quoted_speaker', `${finding.span.text} was attributed to the outlet`);
  }
});

test('M-15: curly double and single quotes both count as quotation', () => {
  for (const text of [
    'The mayor said “this draconian scheme” today.',
    'The mayor said ‘this draconian scheme’ today.',
  ]) {
    const { findings } = analyze(text);
    assert.ok(findings.length > 0, text);
    for (const finding of findings) assert.equal(finding.voiceClass, 'quoted_speaker', text);
  }
});

test('M-15: an apostrophe is not a quotation mark', () => {
  const { findings } = analyze("The council's plan was called reckless and draconian.");
  assert.ok(findings.length > 0);
  for (const finding of findings) {
    assert.notEqual(finding.voiceClass, 'quoted_speaker', 'apostrophe misread as quoted speech');
  }
});

test('M-15: unbalanced quotation yields uncertain, never outlet voice', () => {
  const { findings } = analyze('The memo said "the plan is draconian and unworkable');
  assert.ok(findings.length > 0);
  for (const finding of findings) {
    assert.equal(finding.voiceClass, 'uncertain');
  }
});

test('M-15: unquoted prose is still reporter voice', () => {
  const { findings } = analyze('The council approved a draconian scheme yesterday.');
  assert.ok(findings.length > 0);
  for (const finding of findings) assert.equal(finding.voiceClass, 'reporter');
});

// -------------------------------------------------------------------------
// O-03 — agent-suppression parity with the Level 3 repairs
// -------------------------------------------------------------------------

function suppression(text) {
  return analyze(text).findings.filter((f) => f.mechanism === 'agent_suppression');
}

test('O-03: irregular participles are detected ("Mistakes were made")', () => {
  assert.ok(suppression('Mistakes were made during the review.').length > 0);
});

test('O-03: temporal and measurement "by" phrases do not name an agent', () => {
  for (const text of [
    'The report was delayed by three weeks.',
    'The budget was cut by 20 percent.',
    'The order was signed by Tuesday.',
  ]) {
    assert.ok(suppression(text).length > 0, `should still flag: ${text}`);
  }
});

test('O-03: a real named agent is still excluded', () => {
  for (const text of [
    'The report was published by the department.',
    'The suspect was detained by police.',
  ]) {
    assert.equal(suppression(text).length, 0, `agent is named, should be excluded: ${text}`);
  }
});

// -------------------------------------------------------------------------
// O-04 — absence of findings is not P1
// -------------------------------------------------------------------------

test('O-04: zero findings reports no peak pressure, not P1', () => {
  const article = { paragraphs: ['An entirely ordinary sentence about municipal scheduling.'] };
  const metrics = sandbox.calculateMetrics(article, []);
  assert.equal(metrics.peakPressure, null, 'P1 means light pressure was detected, not absence');
});

test('O-04: findings still report a real peak', () => {
  const article = { paragraphs: ['A draconian scheme.'] };
  const metrics = sandbox.calculateMetrics(article, [
    { pressure: 'P3', state: 'confirmed', span: { paragraphIndex: 0, startChar: 2, endChar: 11 } },
  ]);
  assert.equal(metrics.peakPressure, 'P3');
});
