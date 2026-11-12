// Which pages each role may open, and where each role starts.

// Roles that use the React app, and the page each lands on after logging in.
export const homeForRole = {
  Customer: 'landing',
  InteriorDesigner: 'dashboard',
};

// Roles whose pages are the Flask (Jinja) administration pages. React logs them in, then
// hands over to these addresses; the Flask session cookie is shared, so no second login.
export const flaskHomeForRole = {
  UserAdmin: '/admin/accounts',
  PlatformManager: '/platform/',
};

const PUBLIC_PAGES = new Set(['landing', 'login', 'register', 'projects', 'project', 'designers', 'designer']);
const CUSTOMER_PAGES = new Set(['favourites']);
const DESIGNER_PAGES = new Set(['dashboard', 'portfolio', 'portfolio-new', 'portfolio-item', 'company']);

export function unauthenticatedMessage(wasAuthenticated, currentMessage = '') {
  return wasAuthenticated ? 'Your session has expired. Please log in again.' : currentMessage;
}

// On first load, a logged-in user opening the bare address goes to their role's home.
export function initialPage(page, user) {
  return page === 'landing' && user ? homeForRole[user.role] || page : page;
}

export function canAccessPage(page, user) {
  if (PUBLIC_PAGES.has(page)) return true;
  if (CUSTOMER_PAGES.has(page)) return user?.role === 'Customer';
  if (DESIGNER_PAGES.has(page)) return user?.role === 'InteriorDesigner';
  return false;
}

// Where to send someone who opened a page they may not see.
export function fallbackPage(user) {
  return user ? homeForRole[user.role] || 'landing' : 'login';
}

export function publicUser(user) {
  const known = Object.hasOwn(homeForRole, user?.role) || Object.hasOwn(flaskHomeForRole, user?.role);
  if (!user || !user.id || typeof user.name !== 'string' || !known) {
    throw new Error('This account role is not supported by this application.');
  }
  return { id: user.id, name: user.name, email: user.email, role: user.role, status: user.status };
}

export function registrationPayload(data) {
  return { name: data.name, email: data.email, password: data.password, confirm_password: data.confirmPassword };
}
