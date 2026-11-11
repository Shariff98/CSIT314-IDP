import test from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { flaskApi, queryString } from '../services/api.js';

// Records each fetch and answers with a JSON envelope.
function recordFetch(t, data = {}) {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    calls.push({ url, options });
    return new Response(JSON.stringify({ data }), { headers: { 'Content-Type': 'application/json' } });
  });
  return calls;
}

test('designer project actions use the right method, address and JSON body', async t => {
  const calls = recordFetch(t, { project: { id: 5 } });
  await flaskApi.getMyProject(5);
  await flaskApi.updateMyProject(5, { title: 'T' });
  await flaskApi.deleteMyProject(5);
  await flaskApi.assignTags(5, { category: 'Kitchen', style_tags: 'Modern' });
  await flaskApi.markStatus(5, 'Past');
  await flaskApi.setPublished(5, true);
  await flaskApi.setCoverPhoto(9);
  await flaskApi.deletePhoto(9);
  assert.deepEqual(calls.map(c => [c.options.method || 'GET', c.url]), [
    ['GET', '/api/designer/portfolio/5'],
    ['PUT', '/api/designer/portfolio/5'],
    ['DELETE', '/api/designer/portfolio/5'],
    ['PUT', '/api/designer/portfolio/5/tags'],
    ['PUT', '/api/designer/portfolio/5/status'],
    ['PUT', '/api/designer/portfolio/5/publish'],
    ['PUT', '/api/designer/photos/9/cover'],
    ['DELETE', '/api/designer/photos/9'],
  ]);
  assert.deepEqual(JSON.parse(calls[4].options.body), { status: 'Past' });
  assert.deepEqual(JSON.parse(calls[5].options.body), { published: true });
  assert.ok(calls.every(c => c.options.credentials === 'include'));
});

test('photo upload sends multipart form data without forcing a JSON content type', async t => {
  const calls = recordFetch(t, { project: { id: 5 } });
  const file = new File(['png'], 'room.png', { type: 'image/png' });
  await flaskApi.uploadPhoto(5, file);
  await flaskApi.uploadCompanyImage('logo', file);
  assert.equal(calls[0].url, '/api/designer/portfolio/5/photos');
  assert.ok(calls[0].options.body instanceof FormData);
  assert.equal(calls[0].options.body.get('photo').name, 'room.png');
  assert.equal(calls[0].options.headers.has('Content-Type'), false);
  assert.equal(calls[1].options.body.get('kind'), 'logo');
});

test('designer directory, company and analytics addresses', async t => {
  const calls = recordFetch(t);
  await flaskApi.getDesigners({ q: 'tan', specialisation: '', max_budget: 30000 });
  await flaskApi.getDesigner(3);
  await flaskApi.getAnalytics();
  await flaskApi.getMyCompany();
  await flaskApi.createCompany({ name: 'N' });
  await flaskApi.updateServices({ budget_min: 1 });
  await flaskApi.addTeamMember({ name: 'A', position: 'B' });
  await flaskApi.removeTeamMember(4);
  assert.deepEqual(calls.map(c => [c.options.method || 'GET', c.url]), [
    ['GET', '/api/designers?q=tan&max_budget=30000'],
    ['GET', '/api/designers/3'],
    ['GET', '/api/designer/analytics'],
    ['GET', '/api/designer/company'],
    ['POST', '/api/designer/company'],
    ['PUT', '/api/designer/company/services'],
    ['POST', '/api/designer/company/team'],
    ['DELETE', '/api/designer/company/team/4'],
  ]);
});

test('query strings drop empty values', () => {
  assert.equal(queryString({ a: '', b: null, c: undefined, d: 0, e: 'x' }), '?d=0&e=x');
  assert.equal(queryString({}), '');
});

test('there is no mock API left', async () => {
  const module = await import('../services/api.js');
  assert.equal(module.api, undefined);
});

test('manage-project helpers map the server project to the form and back', async () => {
  const { createServer } = await import('vite');
  const server = await createServer({ root: fileURLToPath(new URL('../../', import.meta.url)),
    optimizeDeps: { noDiscovery: true, include: [] },
    server: { middlewareMode: true, hmr: false, ws: false, watch: null }, appType: 'custom' });
  try {
    const { formFromProject, updatePayload } = await server.ssrLoadModule('/src/pages/Designer/ManageProjectPage.jsx');
    const { projectFormErrors } = await server.ssrLoadModule('/src/pages/Designer/CreateProjectPage.jsx');
    const project = { title: 'Kitchen', description: 'Warm', category: 'Kitchen', budget: 12000, property_type: null,
      location: 'Tampines', completion_date: null, style_tags: ['Modern', 'Japandi'] };
    const form = formFromProject(project);
    assert.equal(form.styles, 'Modern, Japandi');
    assert.equal(form.propertyType, '');
    assert.deepEqual(updatePayload(form), { title: 'Kitchen', description: 'Warm', category: 'Kitchen', budget: 12000,
      property_type: '', location: 'Tampines', completion_date: null });
    assert.deepEqual(projectFormErrors(form), {});
    assert.deepEqual(Object.keys(projectFormErrors({ ...form, title: ' ', budget: '1.5' })).sort(), ['budget', 'title']);
  } finally { await server.close(); }
});
