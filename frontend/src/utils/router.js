// Hash URLs for the React pages, e.g. #/projects/12 or #/designer/projects/5.
//
// Hash URLs never reach Flask, so they cannot clash with the Flask pages (/login, /admin/...)
// and the server needs no extra routes. They give every page a real address: refresh keeps
// the page, Back/Forward work, and a link can be shared.

const ROUTES = [
  ['landing', '/'],
  ['login', '/login'],
  ['register', '/register'],
  ['projects', '/projects'],
  ['project', '/projects/:id'],
  ['designers', '/designers'],
  ['designer', '/designers/:id'],
  ['favourites', '/favourites'],
  ['dashboard', '/designer'],
  ['portfolio', '/designer/projects'],
  ['portfolio-new', '/designer/projects/new'],
  ['portfolio-item', '/designer/projects/:id'],
  ['company', '/designer/company'],
];

export const PAGES = ROUTES.map(([page]) => page);

function match(pattern, path) {
  const want = pattern.split('/');
  const got = path.split('/');
  if (want.length !== got.length) return null;
  const params = {};
  for (let i = 0; i < want.length; i++) {
    if (want[i] === ':id') {
      if (!/^[1-9]\d{0,15}$/.test(got[i])) return null;
      params.id = Number(got[i]);
    } else if (want[i] !== got[i]) return null;
  }
  return params;
}

// '#/projects/12?x' -> { page: 'project', params: { id: 12 } }. Unknown addresses go to the landing page.
export function parseHash(hash = '') {
  const path = (String(hash).replace(/^#/, '').split('?')[0] || '/').replace(/(.)\/+$/, '$1');
  // Exact routes first, so /designer/projects/new is not read as a project id.
  for (const [page, pattern] of ROUTES) {
    if (!pattern.includes(':') && pattern === path) return { page, params: {} };
  }
  for (const [page, pattern] of ROUTES) {
    if (pattern.includes(':')) {
      const params = match(pattern, path);
      if (params) return { page, params };
    }
  }
  return { page: 'landing', params: {} };
}

// ('project', { id: 12 }) -> '#/projects/12'
export function hashFor(page, params = {}) {
  const route = ROUTES.find(([name]) => name === page);
  if (!route) return '#/';
  return `#${route[1].replace(':id', String(params.id ?? ''))}`;
}
