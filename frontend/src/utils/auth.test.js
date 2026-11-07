import test from 'node:test';
import assert from 'node:assert/strict';
import { homeForRole, canAccessPage, publicUser, registrationPayload, unauthenticatedMessage, initialPage } from './auth.js';
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

test('root refresh selects the restored user home for each role; anonymous visitors see landing', () => {
  assert.equal(initialPage('landing', null), 'landing');
  for (const [role, home] of Object.entries(homeForRole)) {
    assert.equal(initialPage('landing', { role }), home);
  }
});

test('initial navigation preserves deliberate public selections and non-root visits', () => {
  const user = { role: 'Customer' };
  for (const page of ['landing', 'designer-profile', 'project-details', 'login', 'register']) {
    assert.equal(initialPage(page, user, true), page);
  }
  assert.equal(initialPage('landing', user, false, false), 'landing');
  assert.equal(initialPage('project-details', user), 'project-details');
  assert.equal(initialPage('customer-favourites', user), 'customer-favourites');
});

for (const [role, home] of Object.entries(homeForRole)) {
  test(`${role} keeps its role and can access only its protected pages`, () => {
    const user = publicUser({ id: 1, name: 'Person', email: 'p@example.com', role, status: 'Active', password: 'secret', password_hash: 'hash' });
    assert.equal(user.role, role);
    assert.equal(Object.hasOwn(user, 'password'), false);
    assert.equal(Object.hasOwn(user, 'password_hash'), false);
    assert.equal(canAccessPage(home, user), true);
    for (const [otherRole, otherHome] of Object.entries(homeForRole)) {
      if (role !== otherRole) assert.equal(canAccessPage(otherHome, user), false);
    }
  });
}

test('anonymous visitors cannot open protected pages but can browse public profiles', () => {
  for (const home of Object.values(homeForRole)) assert.equal(canAccessPage(home, null), false);
  assert.equal(canAccessPage('designer-profile', null), true);
  assert.equal(canAccessPage('project-details', null), true);
  assert.equal(canAccessPage('admin-categories', { role: 'UserAdmin' }), false);
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
