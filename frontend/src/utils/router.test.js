import test from 'node:test';
import assert from 'node:assert/strict';
import { PAGES, hashFor, parseHash } from './router.js';

test('every page has an address and reads back to itself', () => {
  for (const page of PAGES) {
    const hash = hashFor(page, { id: 42 });
    assert.deepEqual(parseHash(hash).page, page, hash);
  }
});

test('ids are read from the address', () => {
  assert.deepEqual(parseHash('#/projects/12'), { page: 'project', params: { id: 12 } });
  assert.deepEqual(parseHash('#/designers/7'), { page: 'designer', params: { id: 7 } });
  assert.deepEqual(parseHash('#/designer/projects/5'), { page: 'portfolio-item', params: { id: 5 } });
  assert.equal(hashFor('project', { id: 12 }), '#/projects/12');
});

test('"new" is a page, not a project id', () => {
  assert.deepEqual(parseHash('#/designer/projects/new'), { page: 'portfolio-new', params: {} });
});

test('empty, unknown and malformed addresses open the landing page', () => {
  for (const hash of ['', '#', '#/', '#/nowhere', '#/projects/abc', '#/projects/0', '#/projects/-1', '#/projects/1/2']) {
    assert.equal(parseHash(hash).page, 'landing', hash);
  }
  assert.equal(hashFor('missing-page'), '#/');
});

test('trailing slashes and query strings are ignored', () => {
  assert.deepEqual(parseHash('#/projects/'), { page: 'projects', params: {} });
  assert.deepEqual(parseHash('#/projects/3?from=chat'), { page: 'project', params: { id: 3 } });
});
