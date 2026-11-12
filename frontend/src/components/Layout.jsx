import { useState } from 'react';
import { homeForRole } from '../utils/auth';
import { hashFor } from '../utils/router';
import { useApp } from '../context/AppContext';

// [page, label]. The second-level pages light up their section (e.g. one project -> Browse projects).
const publicMenu = [['projects', 'Browse projects'], ['designers', 'Designers']];
const roleMenus = {
  Customer: [['landing', 'Home'], ...publicMenu, ['favourites', 'Favourites']],
  InteriorDesigner: [['dashboard', 'Dashboard'], ['portfolio', 'My projects'], ['portfolio-new', 'New project'],
    ['company', 'Company profile']],
};
const SECTION = { project: 'projects', designer: 'designers', 'portfolio-item': 'portfolio' };
const ROLE_NAMES = { Customer: 'Homeowner', InteriorDesigner: 'Interior Designer' };

export default function Layout({ page, go, children }) {
  const { user, logout, authLoading, authMessage } = useApp();
  const [logoutError, setLogoutError] = useState('');
  const [loggingOut, setLoggingOut] = useState(false);
  const menu = user ? roleMenus[user.role] || [] : publicMenu;
  const active = SECTION[page] || page;

  async function handleLogout() {
    setLoggingOut(true);
    setLogoutError('');
    try {
      // Leave a members-only page first, so the app doesn't redirect to Log in on the way out.
      go('landing');
      await logout();
    } catch (error) {
      setLogoutError(`Could not log out. ${error.message} Please try again.`);
    } finally {
      setLoggingOut(false);
    }
  }

  // Real links (href) so pages can be opened in a new tab; clicks stay inside the app.
  const link = (key, label, className = '') => (
    <a key={key} href={hashFor(key)} className={`${className} ${active === key ? 'active' : ''}`.trim()}
      aria-current={active === key ? 'page' : undefined}
      onClick={(event) => { event.preventDefault(); go(key); }}>{label}</a>
  );

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#/" onClick={(event) => { event.preventDefault(); go(user ? homeForRole[user.role] || 'landing' : 'landing'); }}>
          RenovationLink
        </a>
        {authLoading ? <span role="status">Checking session...</span> : (
          <>
            <nav className="top-nav" aria-label="Main navigation">
              {menu.map(([key, label]) => link(key, label))}
              {user?.role === 'InteriorDesigner' && <a href="/analytics/">Full analytics</a>}
            </nav>
            {user ? (
              <div className="account-box">
                <div>
                  <strong>{user.name}</strong>
                  <small>{ROLE_NAMES[user.role] || user.role}</small>
                </div>
                <button className="secondary-button compact" onClick={handleLogout} disabled={loggingOut}>{loggingOut ? 'Logging out...' : 'Log out'}</button>
              </div>
            ) : (
              <div className="public-actions">
                <button className="text-button" onClick={() => go('login')}>Log in</button>
                <button className="primary-button compact" onClick={() => go('register')}>Create account</button>
              </div>
            )}
          </>
        )}
      </header>
      <main>{authMessage && <div className="alert" role="status">{authMessage}</div>}{logoutError && <div className="alert error-alert" role="alert">{logoutError}</div>}{children}</main>
      <footer className="footer">
        <strong>RenovationLink</strong>
        <span>CSIT314 RenovationLink</span>
      </footer>
    </div>
  );
}
