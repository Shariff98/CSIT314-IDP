import test from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { projectDetailsData, projectDetailsError, pageRequest } from './projects.js';
import { flaskApi } from '../services/api.js';

test('details preserve the full API company instead of a mock company with the same ID', () => {
  const company = { id: 101, name: 'Actual company', email: 'real@example.com', services: ['Design'], years_experience: 0 };
  const data = projectDetailsData({ id: 201, designer_id: 101, title: 'Actual project', company,
    photos: [{ id: 1, url: '/uploads/real.png', is_cover: true }], style_tags: ['Japandi'] });
  assert.equal(data.id, 201);
  assert.equal(data.title, 'Actual project');
  assert.deepEqual(data.company, company);
  assert.deepEqual(data.photos, ['/uploads/real.png']);
  assert.deepEqual(data.styles, ['Japandi']);
});

test('missing company, images and optional fields remain safe; invalid responses are rejected', () => {
  const data = projectDetailsData({ id: 1 });
  assert.equal(data.company, null);
  assert.deepEqual(data.photos, []);
  assert.deepEqual(data.styles, []);
  assert.equal(data.location, '');
  assert.throws(() => projectDetailsData(null), /Unexpected/);
  assert.throws(() => projectDetailsData({ id: 0 }), /Unexpected/);
  assert.equal(projectDetailsError({ status: 404 }), 'Project not found or unavailable.');
  assert.equal(projectDetailsError(new Error('Offline')), 'Could not load project: Offline');
});

test('detail request uses real API ID, cookies and signal; a 404 never falls back to mock data and retry works', async t => {
  let available = false;
  const controller = new AbortController();
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, '/api/idps/201');
    assert.equal(options.credentials, 'include');
    assert.equal(options.signal, controller.signal);
    return new Response(JSON.stringify(available ? { data: { project: { id: 201, title: 'Real' } } }
      : { error: { code: 'not_found', message: 'Project not found.' } }),
    { status: available ? 200 : 404, headers: { 'Content-Type': 'application/json' } });
  });
  await assert.rejects(flaskApi.getProject(201, { signal: controller.signal }), error => error.status === 404);
  available = true;
  assert.equal((await flaskApi.getProject(201, { signal: controller.signal })).data.project.title, 'Real');
});

test('changing real project cancels old detail work and ignores late responses', async () => {
  const pending = [];
  const shown = [];
  const start = id => pageRequest(signal => new Promise(resolve => pending.push({ id, signal, resolve })), {
    success: data => shown.push(projectDetailsData(data).id), failure: assert.fail,
  });
  const cancel = start(201);
  await new Promise(resolve => setImmediate(resolve));
  cancel();
  start(202);
  await new Promise(resolve => setImmediate(resolve));
  pending[1].resolve({ id: 202 });
  pending[0].resolve({ id: 201 });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(pending[0].signal.aborted, true);
  assert.deepEqual(shown, [202]);
});

test('real details markup is read-only and handles missing company/photos', async () => {
  // Use Vite's existing JSX transformer, without installing a browser/test framework.
  const { createServer } = await import('vite');
  const server = await createServer({ root: fileURLToPath(new URL('../../', import.meta.url)),
    optimizeDeps: { noDiscovery: true, include: [] },
    server: { middlewareMode: true, hmr: false, watch: null }, appType: 'custom' });
  try {
    const { ApiProjectContent } = await server.ssrLoadModule('/src/pages/Customer/ApiIDPDetailsPage.jsx');
    const { createElement } = await import('react');
    const { renderToStaticMarkup } = await import('react-dom/server');
    const html = renderToStaticMarkup(createElement(ApiProjectContent, {
      project: projectDetailsData({ id: 201, title: 'Real kitchen', budget: 12000, views: 9,
        company: { name: 'Actual studio', email: 'studio@example.com', years_experience: 0 } }), onBack: () => {},
    }));
    assert.match(html, /Real kitchen/);
    assert.match(html, /Actual studio/);
    assert.match(html, /studio@example.com/);
    assert.match(html, /12,000/);
    assert.match(html, /Back to Browse/);
    assert.match(html, /No project photos available/);
    assert.doesNotMatch(html, /Save project|favourites|Edit category|Manage full|designer-link/);
    const missing = renderToStaticMarkup(createElement(ApiProjectContent, { project: projectDetailsData({ id: 1 }), onBack: () => {} }));
    assert.match(missing, /Company information unavailable/);
    assert.match(missing, /project-living.svg/);
  } finally {
    await server.close();
  }
});
