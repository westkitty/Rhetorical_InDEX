import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const contracts = fs.readFileSync(new URL('../packages/schema/src/contracts.ts', import.meta.url), 'utf8');
const app = fs.readFileSync(new URL('../apps/web/src/app.ts', import.meta.url), 'utf8');
const css = fs.readFileSync(new URL('../apps/web/src/styles.css', import.meta.url), 'utf8');

// F-003 (independent review): the tests in this file are structural
// source-contract guards, not behavioral proof. They confirm a token, hook, or
// shape is present in source — they do NOT execute the referenced logic and
// cannot catch a regression where the identifier still exists but is wired
// incorrectly (e.g. setPointerCapture present in source but never actually
// called on pointerdown). Genuine runtime/behavioral verification of pointer
// capture, focus trap, geometry, and responsive interaction lives in the
// Chromium/Playwright suite (tools/runtime_qa.py) and, for the Local Preview
// detector's output specifically, in tests/local-preview-contract.test.mjs
// (which executes the real compiled function, not just greps for its name).
// Test names below are prefixed "[structural guard]" to make this explicit.

test('[structural guard] Finding contract source declares a singular-mechanism, exact-span shape', () => {
  const findingBlock = contracts.slice(contracts.indexOf('interface Finding'), contracts.indexOf('interface Article'));
  assert.match(findingBlock, /mechanism: MechanismId/);
  assert.equal(/mechanisms\s*:/.test(findingBlock), false);
  assert.match(findingBlock, /span: SpanLocation/);
});

test('[structural guard] lens implementation hooks (radius clamp, pointer capture, pointercancel, resize re-clamp) are present in source', () => {
  // Presence-only: proves these identifiers have not been silently deleted.
  // Does not prove pointer capture actually engages or radius clamping is
  // correct at runtime — that is the Chromium suite's job.
  assert.match(app, /radius \+ 8/);
  assert.match(app, /setPointerCapture/);
  assert.match(app, /pointercancel/);
  assert.match(app, /visualViewport/);
  assert.match(app, /orientationchange/);
});

test('[structural guard] drawer focus-trap/restore hooks and reduced-motion support are present in source', () => {
  // Presence-only: proves these identifiers have not been silently deleted.
  // Does not prove the focus trap or restoration actually works at runtime —
  // that is the Chromium suite's job (repeated Tab-trap + Escape-restore
  // checks in tools/runtime_qa.py).
  assert.match(app, /trapDrawerFocus/);
  assert.match(app, /lastFocus\?\.isConnected/);
  assert.match(css, /prefers-reduced-motion:reduce/);
  assert.match(css, /user-reduced-motion/);
});
