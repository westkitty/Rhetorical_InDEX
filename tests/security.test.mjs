import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

// Article text is UNTRUSTED input. These tests execute the real compiled
// escaping and rendering helpers from apps/web/dist/app.js and prove hostile
// article content cannot become live markup.

const compiled = fs.readFileSync(new URL('../apps/web/dist/app.js', import.meta.url), 'utf8');
const html = fs.readFileSync(new URL('../apps/web/dist/index.html', import.meta.url), 'utf8');
const appSource = fs.readFileSync(new URL('../apps/web/src/app.ts', import.meta.url), 'utf8');

function extractFunction(source, signature) {
  const start = source.indexOf(signature);
  assert.ok(start >= 0, `${signature} not found in compiled bundle`);
  const braceOpen = source.indexOf('{', start);
  let depth = 0;
  for (let i = braceOpen; i < source.length; i += 1) {
    if (source[i] === '{') depth += 1;
    else if (source[i] === '}') {
      depth -= 1;
      if (depth === 0) return source.slice(start, i + 1);
    }
  }
  throw new Error(`unbalanced braces extracting ${signature}`);
}

const sandbox = {};
vm.createContext(sandbox);
vm.runInContext(extractFunction(compiled, 'function esc('), sandbox);

test('esc neutralizes every character that can break out of markup', () => {
  assert.equal(sandbox.esc('<script>'), '&lt;script&gt;');
  assert.equal(sandbox.esc('"'), '&quot;');
  assert.equal(sandbox.esc("'"), '&#39;');
  assert.equal(sandbox.esc('&'), '&amp;');
  assert.equal(sandbox.esc(null), '');
  assert.equal(sandbox.esc(undefined), '');
});

test('esc escapes ampersands first so entities cannot be reconstructed', () => {
  // A naive implementation ordering & last turns "&lt;" into "&amp;lt;" -> "<".
  assert.equal(sandbox.esc('&lt;script&gt;'), '&amp;lt;script&amp;gt;');
});

test('hostile article payloads survive escaping with no live markup', () => {
  const payloads = [
    '<script>alert(1)</script>',
    '<img src=x onerror=alert(1)>',
    '"><svg/onload=alert(1)>',
    "javascript:alert(document.cookie)",
    '<iframe src="data:text/html,<script>alert(1)</script>">',
    '</span><script>alert(1)</script><span>',
  ];
  for (const payload of payloads) {
    const escaped = sandbox.esc(payload);
    assert.equal(/<[a-z/!]/i.test(escaped), false, `tag survived escaping: ${payload}`);
    assert.equal(escaped.includes('"'), false, `raw quote survived: ${payload}`);
    assert.equal(escaped.includes("'"), false, `raw apostrophe survived: ${payload}`);
  }
});

test('article text is routed through esc before rendering', () => {
  // Behavioral escaping is proven above; this pins the call site so a future
  // refactor cannot render segment text raw while esc still exists unused.
  assert.match(appSource, /const safeText = esc\(segment\.text\)/);
});

test('built artifact embeds fixture data without an executable injection point', () => {
  const bootstrapMatch = html.match(/window\.RI_BOOTSTRAP=(.*?);<\/script>/s);
  assert.ok(bootstrapMatch, 'bootstrap assignment not found');
  assert.equal(
    bootstrapMatch[1].includes('</script'),
    false,
    'bootstrap JSON must not be able to close its own script tag',
  );
  assert.equal(/<script[^>]+src=/i.test(html), false, 'no external script sources');
  assert.equal(/<link[^>]+rel=["']stylesheet/i.test(html), false, 'no external stylesheets');
});

test('built artifact performs no network access of any kind', () => {
  for (const pattern of [/\bfetch\s*\(/, /XMLHttpRequest/, /new\s+WebSocket/, /EventSource/, /navigator\.sendBeacon/]) {
    assert.equal(pattern.test(html), false, `network primitive found in artifact: ${pattern}`);
  }
});

test('built artifact contains no credentials or secret-shaped material', () => {
  for (const pattern of [/api[_-]?key\s*[:=]/i, /secret\s*[:=]/i, /Bearer\s+[A-Za-z0-9._-]{12,}/, /sk-[A-Za-z0-9]{16,}/, /AIza[0-9A-Za-z_-]{20,}/]) {
    assert.equal(pattern.test(html), false, `secret-shaped material found: ${pattern}`);
  }
});

test('built artifact makes no calibration or benchmark accuracy claim', () => {
  for (const pattern of [
    /\bground truth\b/i,
    /\bfact[- ]checked\b/i,
    /\bbenchmark(ed)? (?:accuracy|precision|recall)\b/i,
    /\bproduction[- ]calibrated\b/i,
    /\bvalidated detector\b/i,
    /\b\d{1,3}(?:\.\d+)?%\s*(?:precision|recall|accuracy|f1)\b/i,
  ]) {
    assert.equal(pattern.test(html), false, `overclaiming language found: ${pattern}`);
  }
  assert.match(html, /Uncalibrated|unbenchmarked|UNBENCHMARKED/, 'artifact must state its uncalibrated status');
});
