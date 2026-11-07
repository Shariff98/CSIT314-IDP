import test from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { favouriteList, emptyFavouriteList } from './favouriteProjects.js';

const row = id => ({ id, title: `Real ${id}`, designer_id: 101, company: { name: 'Actual company' },
  style_tags: ['Modern'], photos: [{ url: '/uploads/real.png' }], property_type: 'Condo' });

test('listing maps API records locally and sends keyword/category parameters', async () => {
  let state;
  let params;
  const list = favouriteList(value => { state = value; }, {
    getFavouriteProjects: async query => { params = query; return { data: { items: [row(201)], total: 1 } }; },
  });
  await list.load(' kitchen ', 'Kitchen');
  assert.deepEqual(params, { q: 'kitchen', category: 'Kitchen' });
  assert.equal(state.items[0].companyName, 'Actual company');
  assert.equal(state.items[0].propertyType, 'Condo');
  assert.deepEqual(state.items[0].photos, ['/uploads/real.png']);
  assert.deepEqual(state.items[0].styles, ['Modern']);
  assert.equal(state.loading, false);
  assert.equal(state.total, 1);
});

test('removal changes count only after server confirmation and blocks duplicate clicks', async () => {
  let state;
  let confirm;
  let calls = 0;
  const list = favouriteList(value => { state = value; }, {
    getFavouriteProjects: async () => ({ data: { items: [row(1), row(2)], total: 2 } }),
    removeSavedProject: () => { calls++; return new Promise(resolve => { confirm = resolve; }); },
  });
  await list.load();
  const removing = list.remove(1);
  assert.deepEqual(state.pending, [1]);
  assert.equal(state.total, 2);
  await list.remove(1);
  assert.equal(calls, 1);
  confirm({ data: { project_id: 1, saved: false } });
  await removing;
  assert.equal(state.total, 1);
  assert.deepEqual(state.items.map(item => item.id), [2]);
  assert.deepEqual(state.pending, []);
});

test('failed removal keeps the card and supports retry', async () => {
  let state;
  let fail = true;
  const list = favouriteList(value => { state = value; }, {
    getFavouriteProjects: async () => ({ data: { items: [row(1)], total: 1 } }),
    removeSavedProject: async id => {
      if (fail) throw new Error('Offline');
      return { data: { project_id: id, saved: false } };
    },
  });
  await list.load();
  await list.remove(1);
  assert.equal(state.total, 1);
  assert.match(state.removalErrors[1], /Offline/);
  assert.deepEqual(state.pending, []);
  fail = false;
  await list.remove(1);
  assert.equal(state.total, 0);
  assert.equal(state.removalErrors[1], '');
});

test('older list results cannot overwrite newer filters or restore a confirmed removal', async () => {
  let state;
  const pending = [];
  const list = favouriteList(value => { state = value; }, {
    getFavouriteProjects: () => new Promise(resolve => pending.push(resolve)),
    removeSavedProject: async id => ({ data: { project_id: id, saved: false } }),
  });
  const old = list.load('old');
  const newer = list.load('new');
  pending[1]({ data: { items: [row(2)], total: 1 } });
  await newer;
  pending[0]({ data: { items: [row(1)], total: 1 } });
  await old;
  assert.deepEqual(state.items.map(item => item.id), [2]);
  const outstanding = list.load();
  await list.remove(2);
  pending[2]({ data: { items: [row(2), row(3)], total: 2 } });
  await outstanding;
  assert.deepEqual(state.items.map(item => item.id), [3]);
  assert.equal(state.total, 1);
});

test('navigation cleanup ignores pending work and reopening fetches afresh', async () => {
  let resolve;
  let changes = 0;
  const list = favouriteList(() => changes++, { getFavouriteProjects: () => new Promise(done => { resolve = done; }) });
  const pending = list.load();
  list.dispose();
  const before = changes;
  resolve({ data: { items: [row(1)], total: 1 } });
  await pending;
  assert.equal(changes, before);
  let state;
  await favouriteList(value => { state = value; }, { getFavouriteProjects: async () => ({ data: { items: [], total: 0 } }) }).load();
  assert.equal(state.total, 0);
  assert.equal(state.loading, false);
});

test('list errors distinguish expired/forbidden sessions and can be retried', async () => {
  let state;
  let status = 401;
  const list = favouriteList(value => { state = value; }, { getFavouriteProjects: async () => {
    if (status) throw Object.assign(new Error('Unavailable'), { status });
    return { data: { items: [], total: 0 } };
  } });
  await list.load();
  assert.match(state.error, /log in again/);
  status = 403;
  await list.load();
  assert.match(state.error, /Customer account/);
  status = 0;
  await list.load();
  assert.equal(state.error, '');
  assert.deepEqual(state.items, []);
});

test('rendered list states distinguish empty/search results and hide mock Save actions', async () => {
  const { createServer } = await import('vite');
  const server = await createServer({ root: fileURLToPath(new URL('../../', import.meta.url)),
    optimizeDeps: { noDiscovery: true, include: [] },
    server: { middlewareMode: true, hmr: false, ws: false, watch: null }, appType: 'custom' });
  try {
    const { FavouriteProjectsResults } = await server.ssrLoadModule('/src/pages/Customer/ApiFavouriteProjects.jsx');
    const { AppProvider } = await server.ssrLoadModule('/src/context/AppContext.jsx');
    const { createElement } = await import('react');
    const { renderToStaticMarkup } = await import('react-dom/server');
    const render = (state, filtered = false) => renderToStaticMarkup(createElement(AppProvider, null,
      createElement(FavouriteProjectsResults, { state, filtered, openApiProject: () => {}, onRemove: () => {}, onRetry: () => {}, onClear: () => {} })));
    assert.match(render(emptyFavouriteList()), /Loading favourite projects/);
    const empty = { ...emptyFavouriteList(), loading: false };
    assert.match(render(empty), /No saved projects/);
    assert.match(render(empty, true), /No matching saved projects/);
    assert.match(render(empty, true), /Clear Filters/);
    assert.match(render({ ...empty, error: 'Offline' }), /Retry projects/);
    let state;
    await favouriteList(value => { state = value; }, { getFavouriteProjects: async () => ({ data: { items: [row(201)], total: 1 } }) }).load();
    const html = render({ ...state, pending: [201] });
    assert.match(html, /Actual company/);
    assert.match(html, /View details/);
    assert.match(html, /disabled=""[^>]*>Removing/);
    assert.doesNotMatch(html, />Save<|>Saved</);
    assert.doesNotMatch(html, /Studio North/);
  } finally { await server.close(); }
});
