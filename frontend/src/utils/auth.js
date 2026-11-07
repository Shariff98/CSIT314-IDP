export const homeForRole = {
  Customer: 'customer-home',
  InteriorDesigner: 'designer-dashboard',
  UserAdmin: 'admin-dashboard',
  PlatformManager: 'manager-categories',
};

export function unauthenticatedMessage(wasAuthenticated, currentMessage = '') {
  return wasAuthenticated ? 'Your session has expired. Please log in again.' : currentMessage;
}

// Only select a role home during startup, never during later public navigation.
export function initialPage(page, user, explicitlySelected = false, isRoot = true) {
  return !explicitlySelected && isRoot && page === 'landing' && user
    ? homeForRole[user.role] || page
    : page;
}

export function canAccessPage(page, user) {
  if (page === 'designer-profile') return true;
  if (page.startsWith('customer-')) return user?.role === 'Customer';
  if (page.startsWith('designer-')) return user?.role === 'InteriorDesigner';
  if (page === 'admin-categories' || page.startsWith('manager-')) return user?.role === 'PlatformManager';
  if (page.startsWith('admin-')) return user?.role === 'UserAdmin';
  return true;
}

export function publicUser(user) {
  if (!user || !user.id || typeof user.name !== 'string' || !Object.hasOwn(homeForRole, user.role)) {
    throw new Error('This account role is not supported by this application.');
  }
  return { id: user.id, name: user.name, email: user.email, role: user.role, status: user.status };
}

export function registrationPayload(data) {
  return { name: data.name, email: data.email, password: data.password, confirm_password: data.confirmPassword };
}
