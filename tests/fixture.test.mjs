import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const fixture = JSON.parse(fs.readFileSync(new URL('../packages/fixtures/sb802-demo.json', import.meta.url)));
const article = fixture.event.articles[0];

test('fixture is explicit synthetic data with reserved URLs', () => {
  assert.equal(fixture.mode, 'synthetic_fixture');
  for (const item of fixture.event.articles) assert.equal(new URL(item.url).hostname, 'example.invalid');
  for (const evidence of fixture.event.primaryEvidence) {
    if (evidence.provenanceUrl) assert.equal(new URL(evidence.provenanceUrl).hostname, 'example.invalid');
  }
});

test('every fixture finding round-trips to the exact source span', () => {
  for (const finding of fixture.findings) {
    const paragraph = article.paragraphs[finding.span.paragraphIndex];
    assert.ok(paragraph, finding.id);
    assert.equal(paragraph.slice(finding.span.startChar, finding.span.endChar), finding.span.text, finding.id);
    assert.equal(typeof finding.mechanism, 'string', finding.id);
    assert.equal('mechanisms' in finding, false, finding.id);
  }
});

test('fixture comparison remains cross-document and chronology-bearing', () => {
  assert.ok(fixture.event.articles.length >= 3);
  assert.ok(fixture.event.atomicClaims.length > 0);
  assert.ok(fixture.event.omissions.length > 0);
  for (const omission of fixture.event.omissions) {
    assert.ok(omission.knowableAtTimestamp);
    assert.ok(omission.primaryEvidenceIds.length > 0 || omission.supportingSources.length > 0);
  }
});
