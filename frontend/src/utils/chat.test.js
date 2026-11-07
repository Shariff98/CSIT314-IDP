import test from 'node:test';
import assert from 'node:assert/strict';
import { describePrefs } from './chat.js';

test('describePrefs summarises what the assistant remembers', () => {
  assert.equal(describePrefs({ budget: 10000, category: 'Kitchen', styles: ['Modern'] }), 'Modern Kitchen · around $10,000');
  assert.equal(describePrefs({ budget: 8000, strict_max: true, styles: [] }), 'up to $8,000');
  assert.equal(describePrefs({ category: 'Bathroom', property_type: 'HDB' }), 'Bathroom HDB');
});

test('describePrefs is empty when nothing is remembered', () => {
  assert.equal(describePrefs(null), '');
  assert.equal(describePrefs({ budget: null, category: null, styles: [] }), '');
});
