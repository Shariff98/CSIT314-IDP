import test from 'node:test';
import assert from 'node:assert/strict';
import { canSaveProject, favouriteMutation, favouriteError } from './favourites.js';
import { flaskApi } from '../services/api.js';
import { fileURLToPath } from 'node:url';

test('save button is restricted to active backend Customers', () => {
  assert.equal(canSaveProject({ role: 'Customer', status: 'Active' }), true);
  for (const user of [null, { role: 'Customer', status: 'Suspended' },
    ...['InteriorDesigner', 'UserAdmin', 'PlatformManager'].map(role => ({ role, status: 'Active' }))]) {
    assert.equal(canSaveProject(user), false);
  }
});

test('pending saves prevent duplicate calls and state changes only after confirmation', async () => {
  let resolve;
  let count = 0;
  const change = favouriteMutation({ saveProject: () => { count++; return new Promise(done => { resolve = done; }); } });
  let saved = false;
  const pending = change(201, true).then(result => { saved = result.saved; });
  assert.equal(saved, false);
  assert.equal(await change(201, true), null);
  assert.equal(count, 1);
  resolve({ data: { project_id: 201, saved: true, result: 'saved' } });
  await pending;
  assert.equal(saved, true);
});

test('failed or invalid confirmation does not succeed and permits retry/removal', async () => {
  let fail = true;
  const change = favouriteMutation({
    saveProject: async id => { if (fail) throw new Error('Offline'); return { data: { project_id: id, saved: true } }; },
    removeSavedProject: async id => ({ data: { project_id: id, saved: false } }),
  });
  await assert.rejects(change(1, true), /Offline/);
  fail = false;
  assert.equal((await change(1, true)).saved, true);
  assert.equal((await change(1, false)).saved, false);
  const invalid = favouriteMutation({ saveProject: async () => ({ data: { project_id: 999, saved: true } }) });
  await assert.rejects(invalid(1, true), /did not confirm/);
  assert.match(favouriteError({ status: 401 }), /log in again/);
  assert.match(favouriteError({ status: 403 }), /Customer/);
  assert.match(favouriteError({ status: 404 }), /no longer available/);
});

test('real favourite methods use cookies and correct routes without changing mock services', async t => {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    calls.push({ url, options });
    return new Response(JSON.stringify({ data: {} }), { headers: { 'Content-Type': 'application/json' } });
  });
  await flaskApi.saveProject(201);
  await flaskApi.removeSavedProject(201);
  await flaskApi.getFavouriteProjects({ q: 'warm kitchen', category: 'Kitchen', ignored: '' });
  assert.equal(calls[0].url, '/api/favourites/projects/201');
  assert.equal(calls[0].options.method, 'POST');
  assert.equal(calls[1].options.method, 'DELETE');
  assert.equal(calls[2].url, '/api/favourites/projects?q=warm+kitchen&category=Kitchen');
  for (const call of calls) assert.equal(call.options.credentials, 'include');
});

test('reopening details reads persisted saved state from Flask', async t => {
  let saved = false;
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    if (options.method === 'POST') saved = true;
    if (options.method === 'DELETE') saved = false;
    const data = url.startsWith('/api/idps/') ? { project: { id: 1 }, is_saved: saved }
      : { project_id: 1, saved };
    return new Response(JSON.stringify({ data }), { headers: { 'Content-Type': 'application/json' } });
  });
  assert.equal((await flaskApi.getProject(1)).data.is_saved, false);
  await flaskApi.saveProject(1);
  assert.equal((await flaskApi.getProject(1)).data.is_saved, true);
  await flaskApi.removeSavedProject(1);
  assert.equal((await flaskApi.getProject(1)).data.is_saved, false);
});

test('button markup reflects initial server saved state and can be placed on real details', async () => {
  const { createServer } = await import('vite');
  const server = await createServer({ root: fileURLToPath(new URL('../../', import.meta.url)),
    optimizeDeps: { noDiscovery: true, include: [] },
    server: { middlewareMode: true, hmr: false, ws: false, watch: null }, appType: 'custom' });
  try {
    const { FavouriteProjectButton, ApiProjectContent } = await server.ssrLoadModule('/src/pages/Customer/ApiIDPDetailsPage.jsx');
    const { createElement } = await import('react');
    const { renderToStaticMarkup } = await import('react-dom/server');
    const unsaved = renderToStaticMarkup(createElement(FavouriteProjectButton, { projectId: 1, initialSaved: false }));
    const saved = renderToStaticMarkup(createElement(FavouriteProjectButton, { projectId: 1, initialSaved: true }));
    assert.match(unsaved, /Save to Favourites/);
    assert.match(unsaved, /aria-pressed="false"/);
    assert.match(saved, /Remove from Favourites/);
    assert.match(saved, /aria-pressed="true"/);
    const html = renderToStaticMarkup(createElement(ApiProjectContent, {
      project: { title: 'Real', photos: [], styles: [], views: 0 }, onBack: () => {},
      favouriteAction: createElement(FavouriteProjectButton, { projectId: 1, initialSaved: true }),
    }));
    assert.match(html, /Remove from Favourites/);
    assert.doesNotMatch(html, /Edit category|Manage full/);
  } finally { await server.close(); }
});
