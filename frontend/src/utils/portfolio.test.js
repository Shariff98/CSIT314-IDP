import test from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { flaskApi } from '../services/api.js';
import { projectCardData, pageRequest } from './projects.js';

test('owner portfolio request sends only filter parameters and preserves cookies and cancellation', async t => {
  const controller = new AbortController();
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, '/api/designer/portfolio?q=blue&status=Draft&category=Kitchen&date_from=2026-01-01');
    assert.equal(options.credentials, 'include');
    assert.equal(options.signal, controller.signal);
    assert.equal(options.method, undefined);
    return new Response(JSON.stringify({ data: { items: [{ id: 3, designer_id: 7, published: false }], total: 1 } }),
      { headers: { 'Content-Type': 'application/json' } });
  });
  const response = await flaskApi.getMyPortfolio({ q: 'blue', status: 'Draft', category: 'Kitchen', date_from: '2026-01-01', date_to: '' }, { signal: controller.signal });
  assert.equal(response.data.items[0].designer_id, 7);
  assert.equal(response.data.total, 1);
});

test('portfolio adapter uses actual account/company data and retains drafts', () => {
  const source = { id: 201, designer_id: 88, published: false, style_tags: ['Modern'], company: { name: 'Actual studio' },
    photos: [{ url: '/uploads/real.png' }] };
  const result = projectCardData(source);
  assert.equal(result.designerId, 88);
  assert.notEqual(result.designerId, 101);
  assert.equal(result.companyName, 'Actual studio');
  assert.equal(result.published, false);
  assert.deepEqual(result.photos, ['/uploads/real.png']);
  assert.deepEqual(projectCardData({ id: 1 }).styles, []);
});

test('replaced and unmounted portfolio requests do not publish stale results', async () => {
  let complete;
  let signal;
  const cancel = pageRequest(value => { signal = value; return new Promise(resolve => { complete = resolve; }); }, {
    success: assert.fail, failure: assert.fail, settled: assert.fail,
  });
  await new Promise(resolve => setImmediate(resolve));
  cancel();
  complete({ data: { items: [{ id: 999 }] } });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(signal.aborted, true);
});

test('portfolio errors settle loading and allow a subsequent retry', async () => {
  const events = [];
  pageRequest(async () => { throw Object.assign(new Error('Please log in.'), { status: 401 }); }, {
    success: assert.fail, failure: error => events.push(error.status), settled: () => events.push('settled'),
  });
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(events, [401, 'settled']);
  pageRequest(async () => ({ data: { items: [], total: 0 } }), {
    success: response => events.push(response.data.total), failure: assert.fail,
  });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(events.at(-1), 0);
});

test('portfolio rendering has loading/empty/error states and real cards have no mutation actions', async () => {
  const { createServer } = await import('vite');
  const server = await createServer({ root: fileURLToPath(new URL('../../', import.meta.url)),
    optimizeDeps: { noDiscovery: true, include: [] },
    server: { middlewareMode: true, hmr: false, ws: false, watch: null }, appType: 'custom' });
  try {
    const { PortfolioResults } = await server.ssrLoadModule('/src/pages/Designer/ApiMyPortfolio.jsx');
    const { default: PortfolioPage } = await server.ssrLoadModule('/src/pages/Designer/PortfolioPage.jsx');
    const { AppProvider } = await server.ssrLoadModule('/src/context/AppContext.jsx');
    const { createElement } = await import('react');
    const { renderToStaticMarkup } = await import('react-dom/server');
    const render = props => renderToStaticMarkup(createElement(AppProvider, null,
      createElement(PortfolioResults, { result: { items: [], total: 0 }, onRetry: () => {}, ...props })));
    assert.match(render({ loading: true }), /Loading your portfolio/);
    assert.match(render({}), /No portfolio projects yet/);
    assert.match(render({ error: 'Offline' }), /Retry portfolio/);
    const items = [false, true].map((published, index) => ({ ...projectCardData({ id: 201 + index, title: 'Real project', published,
      company: { name: 'Actual studio' } }), status: 'Current' }));
    const html = render({ result: { items, total: 2 } });
    assert.match(html, /Actual studio/);
    assert.match(html, /Draft/);
    assert.match(html, /Published/);
    assert.match(html, /2 project\(s\)/);
    assert.doesNotMatch(html, />Save<|>Saved<|>Edit<|>Remove<|View details|Studio North/);
    const page = renderToStaticMarkup(createElement(AppProvider, null, createElement(PortfolioPage)));
    assert.match(page, /Create and manage portfolio/);
    assert.match(page, /Demo only/);
    assert.match(page, /Project title/);
    assert.match(page, /Demo projects/);
    assert.match(page, /Loading your portfolio/);
  } finally { await server.close(); }
});
