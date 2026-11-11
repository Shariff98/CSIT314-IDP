import test from 'node:test';
import assert from 'node:assert/strict';
import { describePrefs, loadChat, saveChat } from './chat.js';

test('describePrefs summarises what the assistant remembers', () => {
  assert.equal(describePrefs({ budget: 10000, category: 'Kitchen', styles: ['Modern'] }), 'Modern Kitchen · around $10,000');
  assert.equal(describePrefs({ budget: 8000, strict_max: true, styles: [] }), 'up to $8,000');
  assert.equal(describePrefs({ category: 'Bathroom', property_type: 'HDB' }), 'Bathroom HDB');
});

test('describePrefs is empty when nothing is remembered', () => {
  assert.equal(describePrefs(null), '');
  assert.equal(describePrefs({ budget: null, category: null, styles: [] }), '');
});

test('describePrefs shows budget ranges and excluded styles', () => {
  assert.equal(describePrefs({ budget: 12000, budget_min: 8000, strict_max: true, category: 'Kitchen' }),
    'Kitchen · $8,000–$12,000');
  assert.equal(describePrefs({ budget: 10000, styles: ['Modern'], exclude_styles: ['Industrial', 'Rustic'] }),
    'Modern · around $10,000 · not Industrial, Rustic');
});

function memoryStorage() {
  const data = new Map();
  return { getItem: (k) => data.get(k) ?? null, setItem: (k, v) => data.set(k, String(v)) };
}

test('chat is saved and loaded without error messages', () => {
  const storage = memoryStorage();
  const messages = [{ role: 'user', content: 'kitchen 10k' }, { role: 'assistant', content: 'oops', error: true }];
  saveChat(storage, { messages, context: { budget: 10000 } });
  assert.deepEqual(loadChat(storage), { messages: [messages[0]], context: { budget: 10000 } });
});

test('only the latest 40 messages are kept', () => {
  const storage = memoryStorage();
  const messages = Array.from({ length: 50 }, (_, i) => ({ role: 'user', content: String(i) }));
  saveChat(storage, { messages, context: null });
  const loaded = loadChat(storage);
  assert.equal(loaded.messages.length, 40);
  assert.equal(loaded.messages[0].content, '10');
});

test('missing, broken or blocked storage gives null and never throws', () => {
  assert.equal(loadChat(null), null);
  assert.equal(loadChat(memoryStorage()), null);
  const broken = { getItem: () => '{not json', setItem: () => { throw new Error('full'); } };
  assert.equal(loadChat(broken), null);
  assert.doesNotThrow(() => saveChat(broken, { messages: [], context: null }));
  const blocked = { getItem: () => { throw new Error('denied'); } };
  assert.equal(loadChat(blocked), null);
});
