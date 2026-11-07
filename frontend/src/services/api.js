// =============================================================
// BACKEND INTEGRATION LAYER
// =============================================================
// flaskApi exposes the implemented backend endpoints. The existing api
// export stays mock-based until AppContext and pages are migrated.
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

const postJson = (endpoint, payload) => apiRequest(endpoint, {
  method: 'POST',
  ...(payload === undefined ? {} : { body: JSON.stringify(payload) }),
});

export const flaskApi = {
  login: (payload) => postJson('/auth/login', payload),
  registerCustomer: (payload) => postJson('/customers/register', payload),
  getCurrentUser: () => apiRequest('/auth/me'),
  logout: () => postJson('/auth/logout'),
  getProjects: (params = {}, options = {}) => {
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== '') query.set(key, String(value));
    }
    return apiRequest(`/idps${query.size ? `?${query}` : ''}`, options);
  },
  getProjectOptions: () => apiRequest('/idps/options'),
  saveProject: (id) => postJson(`/favourites/projects/${encodeURIComponent(id)}`),
  removeSavedProject: (id) => apiRequest(`/favourites/projects/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  getFavouriteProjects: (params = {}) => {
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== '') query.set(key, String(value));
    }
    return apiRequest(`/favourites/projects${query.size ? `?${query}` : ''}`);
  },
  // The detail route requires an ID: /api/idps/<id>.
  getProject: (id, options = {}) => {
    if (!/^\d+$/.test(String(id)) || !Number.isSafeInteger(Number(id)) || Number(id) < 1) {
      return Promise.reject(new Error('A positive project ID is required.'));
    }
    return apiRequest(`/idps/${encodeURIComponent(id)}`, options);
  },
};

async function mockRequest(endpoint, options = {}) {
  console.info(`[MOCK API] ${options.method || 'GET'} ${endpoint}`, options.body || '');
  await new Promise((resolve) => setTimeout(resolve, 120));
  return { ok: true, data: options.body ? JSON.parse(options.body) : null };

}

export const api = {
  login: (payload) => mockRequest('/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
  registerCustomer: (payload) => mockRequest('/customers/register', { method: 'POST', body: JSON.stringify(payload) }),
  getDesigners: () => mockRequest('/designers'),
  getDesigner: (id) => mockRequest(`/designers/${id}`),
  submitEnquiry: (payload) => mockRequest('/enquiries', { method: 'POST', body: JSON.stringify(payload) }),
  submitRequirements: (payload) => mockRequest('/renovation-requirements', { method: 'POST', body: JSON.stringify(payload) }),
  bookConsultation: (payload) => mockRequest('/consultations', { method: 'POST', body: JSON.stringify(payload) }),
  makePayment: (payload) => mockRequest('/payments', { method: 'POST', body: JSON.stringify(payload) }),
  settleOutstandingInvoice: (id) => mockRequest(`/payments/${id}/settle`, { method: 'PATCH' }),
  submitReview: (payload) => mockRequest('/reviews', { method: 'POST', body: JSON.stringify(payload) }),
  reportCompany: (payload) => mockRequest('/reports/companies', { method: 'POST', body: JSON.stringify(payload) }),
  toggleFavouriteDesigner: (id, saved) => mockRequest(`/favourites/designers/${id}`, { method: saved ? 'POST' : 'DELETE' }),
  toggleFavouriteProject: (id, saved) => mockRequest(`/favourites/projects/${id}`, { method: saved ? 'POST' : 'DELETE' }),
  saveCompanyProfile: (payload) => mockRequest('/designer/company-profile', { method: 'PUT', body: JSON.stringify(payload) }),
  createPortfolioProject: (payload) => mockRequest('/designer/portfolio', { method: 'POST', body: JSON.stringify(payload) }),
  updatePortfolioProject: (id, payload) => mockRequest(`/designer/portfolio/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deletePortfolioProject: (id) => mockRequest(`/designer/portfolio/${id}`, { method: 'DELETE' }),
  savePackage: (payload) => mockRequest('/designer/packages', { method: 'POST', body: JSON.stringify(payload) }),
  updatePackage: (id, payload) => mockRequest(`/designer/packages/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deletePackage: (id) => mockRequest(`/designer/packages/${id}`, { method: 'DELETE' }),
  updateEnquiryStatus: (id, status) => mockRequest(`/designer/enquiries/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) }),
  updateConsultation: (id, payload) => mockRequest(`/designer/consultations/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  updateMilestone: (projectId, payload) => mockRequest(`/designer/projects/${projectId}/milestones`, { method: 'PATCH', body: JSON.stringify(payload) }),
  respondReview: (id, response) => mockRequest(`/designer/reviews/${id}/response`, { method: 'POST', body: JSON.stringify({ response }) }),
  updateAccount: (id, payload) => mockRequest(`/admin/accounts/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  updateCompanyAccount: (id, payload) => mockRequest(`/admin/companies/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  removeCompanyAccount: (id) => mockRequest(`/admin/companies/${id}`, { method: 'DELETE' }),
  verifyCompany: (id, status) => mockRequest(`/admin/companies/${id}/verification`, { method: 'PATCH', body: JSON.stringify({ status }) }),
  resolveReport: (id, payload) => mockRequest(`/admin/reports/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  removeReview: (id) => mockRequest(`/admin/reviews/${id}`, { method: 'DELETE' }),
  saveCategory: (payload) => mockRequest('/admin/categories', { method: 'POST', body: JSON.stringify(payload) }),
};
