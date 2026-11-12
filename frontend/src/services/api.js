// =============================================================
// BACKEND INTEGRATION LAYER
// =============================================================
// Every call goes to the Flask JSON API (same address in production; Vite proxies
// /api in development). There is no mock data: what the page shows is what Flask stored.
// =============================================================

export const API_BASE_URL = '/api';

// Return Flask's { data: ... } envelope unchanged. Errors carry the HTTP
// status and backend code so callers can distinguish an expired session.
export async function apiRequest(endpoint, options = {}) {
  const headers = new Headers(options.headers);
  headers.set('Accept', 'application/json');
  if (options.body !== undefined && typeof options.body === 'string' && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include',
    });
  } catch (cause) {
    if (cause.name === 'AbortError') throw cause;
    throw new Error('Unable to reach the server. Check your connection and that Flask is running.', { cause });
  }

  let payload;
  try {
    const contentType = response.headers.get('Content-Type') || '';
    if (!contentType.includes('application/json') && !contentType.includes('+json')) {
      throw new Error('Non-JSON response');
    }
    payload = await response.json();
  } catch (cause) {
    if (cause.name === 'AbortError') throw cause;
    const error = new Error(`Unexpected server response (HTTP ${response.status}). Expected JSON.`, { cause });
    error.status = response.status;
    throw error;
  }

  if (!response.ok) {
    const error = new Error(payload?.error?.message || `Request failed (HTTP ${response.status}).`);
    error.status = response.status;
    error.code = payload?.error?.code;
    throw error;
  }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload) || !Object.hasOwn(payload, 'data')) {
    const error = new Error('Unexpected server response. Missing data envelope.');
    error.status = response.status;
    throw error;
  }
  return payload;
}

const sendJson = (method) => (endpoint, payload) => apiRequest(endpoint, {
  method,
  ...(payload === undefined ? {} : { body: JSON.stringify(payload) }),
});
const postJson = sendJson('POST');
const putJson = sendJson('PUT');
const remove = (endpoint) => apiRequest(endpoint, { method: 'DELETE' });

// multipart/form-data upload: the browser sets the Content-Type boundary itself.
function upload(endpoint, fields) {
  const form = new FormData();
  for (const [key, value] of Object.entries(fields)) form.append(key, value);
  return apiRequest(endpoint, { method: 'POST', body: form });
}

export function queryString(params = {}) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') query.set(key, String(value));
  }
  return query.size ? `?${query}` : '';
}

const id = (value) => encodeURIComponent(value);

export const flaskApi = {
  // ----- accounts (US-23 log in, US-01 log out, US-43 register) -----
  login: (payload) => postJson('/auth/login', payload),
  registerCustomer: (payload) => postJson('/customers/register', payload),
  getCurrentUser: () => apiRequest('/auth/me'),
  logout: () => postJson('/auth/logout'),

  // ----- published projects (US-07, 28, 17, 18 browse/search/filter/sort; US-34 details) -----
  getProjects: (params = {}, options = {}) => apiRequest(`/idps${queryString(params)}`, options),
  getProjectOptions: () => apiRequest('/idps/options'),
  // The detail route requires an ID: /api/idps/<id>.
  getProject: (projectId, options = {}) => {
    if (!/^\d+$/.test(String(projectId)) || !Number.isSafeInteger(Number(projectId)) || Number(projectId) < 1) {
      return Promise.reject(new Error('A positive project ID is required.'));
    }
    return apiRequest(`/idps/${id(projectId)}`, options);
  },

  // ----- favourites (US-19 save, US-56 remove, US-44 list, US-08 search) -----
  saveProject: (projectId) => postJson(`/favourites/projects/${id(projectId)}`),
  removeSavedProject: (projectId) => remove(`/favourites/projects/${id(projectId)}`),
  getFavouriteProjects: (params = {}) => apiRequest(`/favourites/projects${queryString(params)}`),

  // ----- designer directory and company page (US-53) -----
  getDesigners: (params = {}, options = {}) => apiRequest(`/designers${queryString(params)}`, options),
  getDesigner: (designerId, options = {}) => apiRequest(`/designers/${id(designerId)}`, options),

  // ----- designer: own projects (US-16, 03, 27, 54, 04, 05, 06, 26, 33, 55) -----
  getMyPortfolio: (params = {}, options = {}) => apiRequest(`/designer/portfolio${queryString(params)}`, options),
  createPortfolioProject: (payload) => postJson('/designer/portfolio', payload),
  getMyProject: (projectId, options = {}) => apiRequest(`/designer/portfolio/${id(projectId)}`, options),
  updateMyProject: (projectId, payload) => putJson(`/designer/portfolio/${id(projectId)}`, payload),
  deleteMyProject: (projectId) => remove(`/designer/portfolio/${id(projectId)}`),
  assignTags: (projectId, payload) => putJson(`/designer/portfolio/${id(projectId)}/tags`, payload),
  markStatus: (projectId, status) => putJson(`/designer/portfolio/${id(projectId)}/status`, { status }),
  setPublished: (projectId, published) => putJson(`/designer/portfolio/${id(projectId)}/publish`, { published }),
  uploadPhoto: (projectId, file) => upload(`/designer/portfolio/${id(projectId)}/photos`, { photo: file }),
  setCoverPhoto: (photoId) => putJson(`/designer/photos/${id(photoId)}/cover`),
  deletePhoto: (photoId) => remove(`/designer/photos/${id(photoId)}`),

  // ----- designer: analytics (US-57, 29, 46, 48) -----
  getAnalytics: (options = {}) => apiRequest('/designer/analytics', options),

  // ----- designer: company profile (US-02, 24, 32, 25, 12, 14, 13, 52) -----
  getMyCompany: (options = {}) => apiRequest('/designer/company', options),
  createCompany: (payload) => postJson('/designer/company', payload),
  updateCompany: (payload) => putJson('/designer/company', payload),
  updateSpecialisations: (payload) => putJson('/designer/company/specialisations', payload),
  updateCredentials: (payload) => putJson('/designer/company/credentials', payload),
  updateServices: (payload) => putJson('/designer/company/services', payload),
  addTeamMember: (payload) => postJson('/designer/company/team', payload),
  removeTeamMember: (memberId) => remove(`/designer/company/team/${id(memberId)}`),
  uploadCompanyImage: (kind, file) => upload('/designer/company/images', { kind, image: file }),
};
