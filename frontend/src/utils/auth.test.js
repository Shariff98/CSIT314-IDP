import test from 'node:test';
import assert from 'node:assert/strict';
import { homeForRole, flaskHomeForRole, canAccessPage, fallbackPage, publicUser, registrationPayload, unauthenticatedMessage, initialPage } from './auth.js';
import { flaskApi } from '../services/api.js';

test('expected anonymous 401 is silent, including after successful logout', () => {
  assert.equal(unauthenticatedMessage(false), '');
  assert.equal(unauthenticatedMessage(false, 'You have been logged out.'), 'You have been logged out.');
  assert.equal(unauthenticatedMessage(false, 'Account created. Please log in.'), 'Account created. Please log in.');
});

test('losing an authenticated session reports expiry and keeps the message on subsequent checks', () => {
  const message = unauthenticatedMessage(true);
  assert.equal(message, 'Your session has expired. Please log in again.');
  assert.equal(unauthenticatedMessage(false, message), message);
});

test('opening the bare address sends a logged-in user to their role home; other pages are kept', () => {
  assert.equal(initialPage('landing', null), 'landing');
  assert.equal(initialPage('landing', { role: 'Customer' }), 'landing');
  assert.equal(initialPage('landing', { role: 'InteriorDesigner' }), 'dashboard');
  for (const page of ['project', 'designer', 'favourites', 'portfolio-item']) {
    assert.equal(initialPage(page, { role: 'InteriorDesigner' }), page);
  }
});

test('public pages are open to everyone, including visitors', () => {
  for (const page of ['landing', 'login', 'register', 'projects', 'project', 'designers', 'designer']) {
    for (const user of [null, { role: 'Customer' }, { role: 'InteriorDesigner' }]) assert.equal(canAccessPage(page, user), true);
  }
});

test('favourites are for customers; designer tools are for designers; unknown pages for no one', () => {
  const customer = { role: 'Customer' };
  const designer = { role: 'InteriorDesigner' };
  assert.equal(canAccessPage('favourites', customer), true);
  assert.equal(canAccessPage('favourites', designer), false);
  assert.equal(canAccessPage('favourites', null), false);
  for (const page of ['dashboard', 'portfolio', 'portfolio-new', 'portfolio-item', 'company']) {
    assert.equal(canAccessPage(page, designer), true);
    assert.equal(canAccessPage(page, customer), false);
    assert.equal(canAccessPage(page, null), false);
  }
  assert.equal(canAccessPage('admin-accounts', { role: 'UserAdmin' }), false);
});

test('a blocked page sends visitors to log in and users to their home', () => {
  assert.equal(fallbackPage(null), 'login');
  assert.equal(fallbackPage({ role: 'Customer' }), 'landing');
  assert.equal(fallbackPage({ role: 'InteriorDesigner' }), 'dashboard');
});

test('every role is accepted; admins and managers are handed to the Flask pages', () => {
  for (const role of [...Object.keys(homeForRole), ...Object.keys(flaskHomeForRole)]) {
    const user = publicUser({ id: 1, name: 'Person', email: 'p@example.com', role, status: 'Active', password: 'secret', password_hash: 'hash' });
    assert.equal(user.role, role);
    assert.equal(Object.hasOwn(user, 'password'), false);
    assert.equal(Object.hasOwn(user, 'password_hash'), false);
  }
  assert.deepEqual(flaskHomeForRole, { UserAdmin: '/admin/accounts', PlatformManager: '/platform/' });
  assert.throws(() => publicUser({ id: 1, name: 'Unknown', role: 'admin' }), /not supported/);
});

test('registration maps confirmation and does not send phone or requested role', () => {
  assert.deepEqual(registrationPayload({ name: 'New', email: 'new@example.com', password: 'longpassword',
    confirmPassword: 'longpassword', phone: '12345678', role: 'UserAdmin' }), {
    name: 'New', email: 'new@example.com', password: 'longpassword', confirm_password: 'longpassword',
  });
});

test('authentication requests preserve cookies, envelopes, and server errors', async (t) => {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    calls.push({ url, options });
    return new Response(JSON.stringify({ data: { user: { id: 1, role: 'Customer' } } }),
      { headers: { 'Content-Type': 'application/json' } });
  });
  const result = await flaskApi.login({ email: 'p@example.com', password: 'secret' });
  assert.equal(result.data.user.role, 'Customer');
  assert.equal(result.data.data, undefined);
  assert.equal(calls[0].url, '/api/auth/login');
  assert.equal(calls[0].options.credentials, 'include');
  await flaskApi.getCurrentUser();
  assert.equal(calls.at(-1).url, '/api/auth/me');
  await flaskApi.logout();
  assert.equal(calls.at(-1).options.method, 'POST');
  assert.equal(calls.at(-1).url, '/api/auth/logout');
  await flaskApi.registerCustomer(registrationPayload({ name: 'New', confirmPassword: 'secret' }));
  assert.equal(calls.at(-1).url, '/api/customers/register');
  assert.equal(JSON.parse(calls.at(-1).options.body).confirm_password, 'secret');
  globalThis.fetch = async () => new Response(JSON.stringify({ error: { code: 'authentication_required', message: 'Please log in.' } }),
    { status: 401, headers: { 'Content-Type': 'application/json' } });
  await assert.rejects(flaskApi.getCurrentUser(), error => error.status === 401 && error.message === 'Please log in.');
  globalThis.fetch = async () => { throw new TypeError('offline'); };
  await assert.rejects(flaskApi.login({}), /Unable to reach the server/);
});
