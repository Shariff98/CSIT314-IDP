import test from 'node:test';
import assert from 'node:assert/strict';
import { projectCardData, projectQuery, pageRequest } from './projects.js';
import { flaskApi } from '../services/api.js';

const flush = () => new Promise(resolve => setImmediate(resolve));

test('adapter maps API fields and cover-first photo URLs without mutating its input', () => {
  const original = { id: 2, designer_id: 3, title: 'Kitchen', budget: 12000, property_type: 'Condo',
    completion_date: '2026-01-01', published: true, views: 5, style_tags: ['Modern'],
    company: { id: 10, name: 'Real studio' }, photos: [{ id: 4, url: '/uploads/cover.png', is_cover: true }, { url: '/uploads/second.png' }] };
  const before = structuredClone(original);
  const card = projectCardData(original);
  assert.equal(card.designerId, 3);
  assert.equal(card.companyName, 'Real studio');
  assert.equal(card.propertyType, 'Condo');
  assert.equal(card.completionDate, '2026-01-01');
  assert.deepEqual(card.styles, ['Modern']);
  assert.deepEqual(card.photos, ['/uploads/cover.png', '/uploads/second.png']);
  assert.deepEqual(original, before);
});

test('missing company, photos, and tags produce safe card defaults', () => {
  const card = projectCardData({ id: 2, company: null, photos: [null, {}] });
  assert.deepEqual(card.photos, []);
  assert.deepEqual(card.styles, []);
  assert.equal(card.companyName, null);
  assert.equal(Object.hasOwn(card, 'companyName'), true);
  assert.deepEqual(projectCardData({}).photos, []);
});

test('query maps filters and pagination to backend names, retaining zero budgets', () => {
  assert.deepEqual(projectQuery(' kitchen ', { category: 'Kitchen', style: 'Modern', budget: 0,
    propertyType: 'Condo', location: 'Tampines', sort: 'views' }, 2), {
    q: 'kitchen', category: 'Kitchen', style: 'Modern', max_budget: 0,
    property_type: 'Condo', location: 'Tampines', sort: 'views', page: 2, per_page: 24,
  });
  assert.equal(projectQuery('', {}, 1).sort, 'newest');
});

test('late older responses cannot replace newer results, even if abort is ignored', async () => {
  let resolveOld;
  let oldSignal;
  const received = [];
  let settled = 0;
  const old = pageRequest(signal => { oldSignal = signal; return new Promise(resolve => { resolveOld = resolve; }); }, {
    success: value => received.push(value), failure: assert.fail, settled: () => settled++,
  });
  await flush();
  old();
  pageRequest(async () => 'new results', { success: value => received.push(value), failure: assert.fail, settled: () => settled++ });
  await flush();
  resolveOld('stale results');
  await flush();
  assert.equal(oldSignal.aborted, true);
  assert.deepEqual(received, ['new results']);
  assert.equal(settled, 1);
});

test('request failures settle loading and a retry can return empty results', async () => {
  const events = [];
  pageRequest(async () => { throw new Error('Offline'); }, {
    success: assert.fail, failure: error => events.push(error.message), settled: () => events.push('settled'),
  });
  await flush();
  assert.deepEqual(events, ['Offline', 'settled']);
  pageRequest(async () => ({ items: [], total: 0, page: 1, per_page: 24, pages: 1 }), {
    success: result => events.push(result.total), failure: assert.fail,
  });
  await flush();
  assert.equal(events.at(-1), 0);
});

test('cancelled or unmounted requests do not publish errors or update loading', async () => {
  let reject;
  const cancel = pageRequest(() => new Promise((resolve, fail) => { reject = fail; }), {
    success: assert.fail, failure: assert.fail, settled: assert.fail,
  });
  await flush();
  cancel();
  reject(new Error('Late network failure'));
  await flush();
});

test('listing and options use GET, preserve pagination, and do not fetch details or mutate data', async t => {
  const urls = [];
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    urls.push(url);
    assert.equal(options.method, undefined);
    assert.equal(options.credentials, 'include');
    const data = url.endsWith('/options') ? { categories: ['Kitchen'], locations: ['East'], styles: ['Modern'], property_types: ['Condo'], sort_options: { newest: 'Newest' } }
      : { items: [], total: 30, page: 2, per_page: 24, pages: 2 };
    return new Response(JSON.stringify({ data }), { headers: { 'Content-Type': 'application/json' } });
  });
  const listing = await flaskApi.getProjects(projectQuery('', {}, 2));
  assert.equal(listing.data.total, 30);
  assert.equal(listing.data.page, 2);
  assert.equal(listing.data.pages, 2);
  const options = await flaskApi.getProjectOptions();
  assert.deepEqual(options.data.categories, ['Kitchen']);
  assert.match(urls[0], /^\/api\/idps\?/);
  assert.equal(urls[1], '/api/idps/options');
});
