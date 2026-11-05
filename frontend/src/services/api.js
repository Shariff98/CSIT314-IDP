// =============================================================
// BACKEND INTEGRATION LAYER
// =============================================================
// The React pages should call functions from this file (directly or
// through AppContext). For the assignment prototype the functions below
// simulate a successful server response.
//
// When the Python backend is ready, replace mockRequest() with fetch()
// calls to the agreed REST endpoints. Keep the function names stable so
// most React pages do not need to change.
// =============================================================

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

async function mockRequest(endpoint, options = {}) {
  console.info(`[MOCK API] ${options.method || 'GET'} ${endpoint}`, options.body || '');
  await new Promise((resolve) => setTimeout(resolve, 120));
  return { ok: true, data: options.body ? JSON.parse(options.body) : null };

  /*
  // === BACKEND INTEGRATION: REPLACE MOCK CODE ABOVE WITH THIS ===
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Request failed');
  }

  return { ok: true, data: await response.json() };
  */
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
