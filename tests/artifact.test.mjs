import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const html = fs.readFileSync(new URL('../apps/web/dist/index.html', import.meta.url), 'utf8');
const source = fs.readFileSync(new URL('../apps/web/src/app.ts', import.meta.url), 'utf8');

test('built artifact is self-contained and has one semantic article plus aria-hidden overlay', () => {
  assert.equal(/<script[^>]+src=/i.test(html), false);
  assert.equal(/<link[^>]+rel=["']stylesheet/i.test(html), false);
  assert.equal((html.match(/id="articleBase"/g) || []).length, 1);
  assert.equal((html.match(/id="articleOverlay"/g) || []).length, 1);
  assert.match(html, /id="articleOverlay" aria-hidden="true"/);
});

test('artifact contains no live URL ingestion or overclaiming benchmark/evidence copy', () => {
  assert.equal(/type="url"/i.test(html), false);
  assert.equal(/ground truth/i.test(html), false);
  assert.equal(/human-reviewed benchmark metrics/i.test(html), false);
  assert.equal(/reproducibility guarantee/i.test(html), false);
});

test('local preview is bounded to four intrinsic mechanisms and does not emit material omission', () => {
  const localStart = source.indexOf('function localPreviewFindings');
  const localEnd = source.indexOf('function loadPasteArticle');
  assert.ok(localStart >= 0 && localEnd > localStart);
  const body = source.slice(localStart, localEnd);
  for (const id of ['loaded_language','presupposition','agent_suppression','false_dilemma']) assert.match(body, new RegExp(id));
  assert.equal(/material_omission/.test(body), false);
});
