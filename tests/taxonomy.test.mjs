import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const taxonomy = JSON.parse(fs.readFileSync(new URL('../packages/taxonomy/taxonomy.json', import.meta.url)));

const required = ['loaded_language','euphemism_dysphemism','presupposition','epistemic_overstatement','agent_suppression','appeal_to_fear','false_dilemma','hasty_generalization','causal_overclaim','headline_body_mismatch','selective_quotation','material_omission'];

test('Alpha-0 taxonomy has exactly the 12 canonical mechanism ids', () => {
  assert.equal(taxonomy.mechanisms.length, 12);
  assert.deepEqual([...taxonomy.mechanisms.map(m => m.id)].sort(), [...required].sort());
});

test('every mechanism has governing criteria, exclusions, pressure anchors, neighbors, and examples', () => {
  for (const mechanism of taxonomy.mechanisms) {
    assert.ok(mechanism.definition.length > 30, mechanism.id);
    assert.ok(mechanism.positiveCriteria.length > 0, mechanism.id);
    assert.ok(mechanism.exclusionCriteria.length > 0, mechanism.id);
    for (const key of ['p1','p2','p3','p4']) assert.ok(mechanism.pressureRubric[key].length > 0, `${mechanism.id}:${key}`);
    assert.ok(Array.isArray(mechanism.confusableNeighbors), mechanism.id);
    assert.ok(mechanism.positiveExamples.length > 0, mechanism.id);
    assert.ok(mechanism.negativeExamples.length > 0, mechanism.id);
  }
});
