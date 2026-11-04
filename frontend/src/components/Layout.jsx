import { useApp } from '../context/AppContext';

const roleMenus = {
  customer: [
    ['customer-home', 'Home'],
    ['customer-idps', 'Browse IDPs'],
    ['customer-designers', 'Designers'],
    ['customer-requirements', 'Requirements'],
    ['customer-favourites', 'Favourites'],
    ['customer-consultations', 'Consultations'],
    ['customer-payments', 'Payments'],
  ],
  designer: [
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
  admin: [
    ['admin-dashboard', 'Dashboard'],
    ['admin-accounts', 'Accounts'],
    ['admin-verification', 'Verification'],
    ['admin-reports', 'Reports'],
    ['admin-moderation', 'Reviews'],
    ['admin-categories', 'Categories'],
  ],
};

export default function Layout({ page, go, children }) {
  const { user, logout } = useApp();
  const menu = user ? roleMenus[user.role] || [] : [];

  function handleLogout() {
    logout();
    go('landing');
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand" onClick={() => go(user ? `${user.role}-${user.role === 'customer' ? 'home' : 'dashboard'}` : 'landing')}>
          RenovationLink
        </button>
        {user ? (
          <>
            <nav className="top-nav" aria-label="Main navigation">
              {menu.map(([key, label]) => (
                <button key={key} className={page === key ? 'active' : ''} onClick={() => go(key)}>{label}</button>
              ))}
            </nav>
            <div className="account-box">
              <div>
                <strong>{user.name}</strong>
                <small>{user.role === 'designer' ? 'Interior Designer' : user.role === 'admin' ? 'Administrator' : 'Homeowner'}</small>
              </div>
              <button className="secondary-button compact" onClick={handleLogout}>Log out</button>
            </div>
          </>
        ) : (
          <div className="public-actions">
            <button className="text-button" onClick={() => go('login')}>Log in</button>
            <button className="primary-button compact" onClick={() => go('register')}>Create account</button>
          </div>
        )}
      </header>
      <main>{children}</main>
      <footer className="footer">
        <strong>RenovationLink</strong>
        <span>CSIT314 React frontend prototype - Not yet merged with backend</span>
      </footer>
    </div>
  );
}
