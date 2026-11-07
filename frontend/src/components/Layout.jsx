import { useState } from 'react';
import { homeForRole } from '../utils/auth';
import { useApp } from '../context/AppContext';

const roleMenus = {
  Customer: [
    ['customer-home', 'Home'],
    ['customer-idps', 'Browse IDPs'],
    ['customer-designers', 'Designers'],
    ['customer-requirements', 'Requirements'],
    ['customer-favourites', 'Favourites'],
    ['customer-consultations', 'Consultations'],
    ['customer-payments', 'Payments'],
  ],
  InteriorDesigner: [
    ['designer-dashboard', 'Dashboard'],
    ['designer-company', 'Company Profile'],
    ['designer-portfolio', 'Portfolio'],
    ['designer-packages', 'Packages'],
    ['designer-enquiries', 'Enquiries'],
    ['designer-consultations', 'Consultations'],
    ['designer-projects', 'Projects'],
    ['designer-payments', 'Payments'],
    ['designer-reviews', 'Reviews'],
  ],
  UserAdmin: [
    ['admin-dashboard', 'Dashboard'],
    ['admin-accounts', 'Accounts'],
    ['admin-verification', 'Verification'],
    ['admin-reports', 'Reports'],
    ['admin-moderation', 'Reviews'],

  ],
  PlatformManager: [['manager-categories', 'Categories']],
};

export default function Layout({ page, go, children }) {
  const { user, logout, authLoading, authMessage } = useApp();
  const [logoutError, setLogoutError] = useState('');
  const [loggingOut, setLoggingOut] = useState(false);
  const menu = user ? roleMenus[user.role] || [] : [];

  async function handleLogout() {
    setLoggingOut(true);
    setLogoutError('');
    try {
      await logout();
      go('landing');
    } catch (error) {
      setLogoutError(`Could not log out. ${error.message} Please try again.`);
    } finally {
      setLoggingOut(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand" onClick={() => go(user ? homeForRole[user.role] || 'landing' : 'landing')}>
          RenovationLink
        </button>
        {authLoading ? <span role="status">Checking session...</span> : user ? (
          <>
            <nav className="top-nav" aria-label="Main navigation">
              {menu.map(([key, label]) => (
                <button key={key} className={page === key ? 'active' : ''} onClick={() => go(key)}>{label}</button>
              ))}
            </nav>
            <div className="account-box">
              <div>
                <strong>{user.name}</strong>
                <small>{({ Customer: 'Homeowner', InteriorDesigner: 'Interior Designer', UserAdmin: 'User Administrator', PlatformManager: 'Platform Manager' })[user.role]}</small>
              </div>
              <button className="secondary-button compact" onClick={handleLogout} disabled={loggingOut}>{loggingOut ? 'Logging out...' : 'Log out'}</button>
            </div>
          </>
        ) : (
          <div className="public-actions">
            <button className="text-button" onClick={() => go('login')}>Log in</button>
            <button className="primary-button compact" onClick={() => go('register')}>Create account</button>
          </div>
        )}
      </header>
      <main>{authMessage && <div className="alert" role="status">{authMessage}</div>}{logoutError && <div className="alert error-alert" role="alert">{logoutError}</div>}{children}</main>
      <footer className="footer">
        <strong>RenovationLink</strong>
        <span>CSIT314 Design Match</span>
      </footer>
    </div>
  );
}
