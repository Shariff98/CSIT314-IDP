import test from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { flaskApi } from '../services/api.js';
import { projectCardData, pageRequest } from './projects.js';
import { createPortfolioPayload, createPortfolioMutation, portfolioOptionalFieldErrors } from './createPortfolio.js';

const createForm = { title: 'Real draft', description: 'Warm kitchen', category: 'Kitchen', budget: '12000',
  propertyType: 'Condo', location: 'Tampines', completionDate: '2026-01-01', styles: 'Modern, Japandi' };

test('real Create accepts an empty completion date and maps it to null', () => {
  const form = { ...createForm, completionDate: '' };
  assert.deepEqual(portfolioOptionalFieldErrors(form, false), {});
  assert.equal(createPortfolioPayload(form).completion_date, null);
  assert.deepEqual(portfolioOptionalFieldErrors(form, true), { completionDate: 'Completion date is required.' });
});

test('real Create accepts empty style tags and maps them to empty text', () => {
  const form = { ...createForm, styles: '' };
  assert.deepEqual(portfolioOptionalFieldErrors(form, false), {});
  assert.equal(createPortfolioPayload(form).style_tags, '');
  assert.deepEqual(portfolioOptionalFieldErrors(form, true), { styles: 'Add at least one style tag.' });
});

test('both optional fields can be empty together; demo Edit keeps its required validation', () => {
  const form = { ...createForm, completionDate: '', styles: '' };
  assert.deepEqual(portfolioOptionalFieldErrors(form, false), {});
  assert.equal(createPortfolioPayload(form).completion_date, null);
  assert.equal(createPortfolioPayload(form).style_tags, '');
  assert.deepEqual(portfolioOptionalFieldErrors(form, true), {
    completionDate: 'Completion date is required.', styles: 'Add at least one style tag.',
  });
});

test('create maps metadata only and always requests a draft, ignoring mock IDs and photo paths', () => {
  const form = { ...createForm, designerId: 101, id: 201, views: 100, photos: ['/project-living.svg'], publish: true };
  const before = structuredClone(form);
  const payload = createPortfolioPayload(form);
  assert.deepEqual(payload, { title: 'Real draft', description: 'Warm kitchen', category: 'Kitchen', budget: 12000,
    property_type: 'Condo', location: 'Tampines', completion_date: '2026-01-01', style_tags: 'Modern, Japandi', publish: false });
  assert.deepEqual(form, before);
  for (const budget of ['0', '-1', '1.5', 'abc', '', 'Infinity']) {
    assert.throws(() => createPortfolioPayload({ ...form, budget }), /positive whole number/);
  }
});

test('creation blocks duplicate submits, confirms server draft before success, and never mutates the form', async () => {
  let resolve;
  let count = 0;
  const create = createPortfolioMutation({ createPortfolioProject: payload => {
    count++;
    assert.equal(payload.publish, false);
    assert.equal(Object.hasOwn(payload, 'photos'), false);
    return new Promise(done => { resolve = done; });
  } });
  const form = { ...createForm };
  let confirmed = null;
  const pending = create(form).then(result => { confirmed = result; });
  assert.equal(confirmed, null);
  assert.equal(await create(form), null);
  assert.equal(count, 1);
  resolve({ data: { project: { id: 77, published: false, photos: [] } } });
  await pending;
  assert.equal(confirmed.id, 77);
  assert.deepEqual(form, createForm);
});

test('failed creation preserves values and releases the submission lock for retry', async () => {
  let fails = true;
  const form = { ...createForm };
  const create = createPortfolioMutation({ createPortfolioProject: async () => {
    if (fails) throw new Error('Offline');
    return { data: { project: { id: 5, published: false } } };
  } });
  await assert.rejects(create(form), /Offline/);
  assert.deepEqual(form, createForm);
  fails = false;
  assert.equal((await create(form)).id, 5);
  const wrong = createPortfolioMutation({ createPortfolioProject: async () => ({ data: { project: { id: 5, published: true } } }) });
  await assert.rejects(wrong(form), /did not confirm draft creation/);
});

test('real create uses JSON and server IDs; refreshing the portfolio retrieves the new draft', async t => {
  const records = [];
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, '/api/designer/portfolio');
    assert.equal(options.credentials, 'include');
    let data;
    if (options.method === 'POST') {
      assert.equal(options.headers.get('Content-Type'), 'application/json');
      const payload = JSON.parse(options.body);
      assert.equal(Object.hasOwn(payload, 'photos'), false);
      const project = { id: 700, designer_id: 8, title: payload.title, published: payload.publish, photos: [] };
      records.push(project);
      data = { project };
    } else data = { items: records, total: records.length };
    return new Response(JSON.stringify({ data }), { status: options.method === 'POST' ? 201 : 200,
      headers: { 'Content-Type': 'application/json' } });
  });
  assert.equal((await flaskApi.getMyPortfolio()).data.total, 0);
  const created = await createPortfolioMutation()(createForm);
  assert.equal(created.id, 700);
  const refreshed = await flaskApi.getMyPortfolio();
  assert.equal(refreshed.data.total, 1);
  assert.equal(refreshed.data.items[0].published, false);
  assert.deepEqual(refreshed.data.items[0].photos, []);
});

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
    assert.match(page, /Photo uploads are not connected yet. You can create a project without photos./);
    assert.match(page, /Create saves a real Flask draft without photos/);
    assert.match(page, /type="file"[^>]*disabled/);
  } finally { await server.close(); }
});
