import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const contracts = fs.readFileSync(new URL('../packages/schema/src/contracts.ts', import.meta.url), 'utf8');
const app = fs.readFileSync(new URL('../apps/web/src/app.ts', import.meta.url), 'utf8');
const css = fs.readFileSync(new URL('../apps/web/src/styles.css', import.meta.url), 'utf8');

test('Finding contract is singular-mechanism and exact-span oriented', () => {
  const findingBlock = contracts.slice(contracts.indexOf('interface Finding'), contracts.indexOf('interface Article'));
  assert.match(findingBlock, /mechanism: MechanismId/);
  assert.equal(/mechanisms\s*:/.test(findingBlock), false);
  assert.match(findingBlock, /span: SpanLocation/);
});

test('lens includes radius-aware clamp, pointer capture, pointercancel, and resize re-clamp', () => {
  assert.match(app, /radius \+ 8/);
  assert.match(app, /setPointerCapture/);
  assert.match(app, /pointercancel/);
  assert.match(app, /visualViewport/);
  assert.match(app, /orientationchange/);
});

test('drawer has focus trap and restore, and reduced motion exists in both CSS and explicit setting', () => {
  assert.match(app, /trapDrawerFocus/);
  assert.match(app, /lastFocus\?\.isConnected/);
  assert.match(css, /prefers-reduced-motion:reduce/);
  assert.match(css, /user-reduced-motion/);
});
