import { useEffect, useRef, useState } from 'react';
import Layout from './components/Layout';
import ChatWidget from './components/ChatWidget';
import { useApp } from './context/AppContext';
import { canAccessPage, fallbackPage, flaskHomeForRole, initialPage } from './utils/auth';
import { hashFor, parseHash } from './utils/router';

import LandingPage from './pages/Public/LandingPage';
import LoginPage from './pages/Public/LoginPage';
import RegisterPage from './pages/Public/RegisterPage';

import IDPsPage from './pages/Customer/IDPsPage';
import ApiIDPDetailsPage from './pages/Customer/ApiIDPDetailsPage';
import DesignersPage from './pages/Customer/DesignersPage';
import DesignerProfilePage from './pages/Customer/DesignerProfilePage';
import FavouritesPage from './pages/Customer/FavouritesPage';

import DesignerDashboard from './pages/Designer/DesignerDashboard';
import PortfolioPage from './pages/Designer/PortfolioPage';
import CreateProjectPage from './pages/Designer/CreateProjectPage';
import ManageProjectPage from './pages/Designer/ManageProjectPage';
import CompanyProfilePage from './pages/Designer/CompanyProfilePage';

function currentRoute() {
  return parseHash(typeof window === 'undefined' ? '' : window.location.hash);
}

export default function App() {
  const { user, authLoading } = useApp();
  const [route, setRoute] = useState(currentRoute);
  const startedAtHome = useRef(true);

  // The address bar is the source of truth: Back/Forward and typed URLs change the page.
  useEffect(() => {
    const onHashChange = () => {
      startedAtHome.current = false;
      setRoute(currentRoute());
    };
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  function go(page, params = {}) {
    const hash = hashFor(page, params);
    startedAtHome.current = false;
    if (window.location.hash === hash) setRoute(parseHash(hash));
    else window.location.hash = hash;   // fires hashchange, which updates the page
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Swap the current history entry instead of adding one (used for redirects).
  function replace(page, params = {}) {
    window.location.replace(hashFor(page, params));
    setRoute(parseHash(hashFor(page, params)));
  }

  const flaskHome = user ? flaskHomeForRole[user.role] : null;
  const allowed = canAccessPage(route.page, user);

  useEffect(() => {
    if (authLoading) return;
    if (flaskHome) {
      // User Admin and Platform Manager use the Flask administration pages.
      window.location.assign(flaskHome);
      return;
    }
    if (!allowed) replace(fallbackPage(user));
    else if (startedAtHome.current && user) {
      const home = initialPage(route.page, user);
      if (home !== route.page) replace(home);
    }
    startedAtHome.current = false;
  }, [authLoading, user, flaskHome, allowed, route.page]);

  if (authLoading) return <Layout page={route.page} go={go}><div className="auth-page" role="status">Checking your login session...</div></Layout>;
  if (flaskHome) {
    return <Layout page={route.page} go={go}><div className="auth-page" role="status">
      Opening the administration pages... <a href={flaskHome}>Continue</a>
    </div></Layout>;
  }
  if (!allowed) return <Layout page={route.page} go={go}><div className="auth-page" role="status">Opening your account page...</div></Layout>;

  const openProject = (id) => go('project', { id });
  const openDesigner = (id) => go('designer', { id });
  const id = route.params.id;

  let content;
  switch (route.page) {
    case 'login': content = <LoginPage go={go} />; break;
    case 'register': content = <RegisterPage go={go} />; break;
    case 'projects': content = <IDPsPage openProject={openProject} />; break;
    case 'project': content = <ApiIDPDetailsPage key={id} projectId={id} onBack={() => go('projects')}
      onOpenProject={openProject} onOpenDesigner={openDesigner} />; break;
    case 'designers': content = <DesignersPage openDesigner={openDesigner} />; break;
    case 'designer': content = <DesignerProfilePage key={id} designerId={id} openProject={openProject} go={go} />; break;
    case 'favourites': content = <FavouritesPage openProject={openProject} />; break;

    case 'dashboard': content = <DesignerDashboard go={go} />; break;
    case 'portfolio': content = <PortfolioPage go={go} />; break;
    case 'portfolio-new': content = <CreateProjectPage go={go} />; break;
    case 'portfolio-item': content = <ManageProjectPage key={id} projectId={id} go={go} />; break;
    case 'company': content = <CompanyProfilePage go={go} />; break;

    default: content = <LandingPage go={go} openProject={openProject} openDesigner={openDesigner} />;
  }

  // Budget Match Assistant: shown to visitors and customers on every page.
  const showChat = !user || user.role === 'Customer';

  return (
    <>
      <Layout page={route.page} go={go}>{content}</Layout>
      {showChat && <ChatWidget onOpenProject={openProject} />}
    </>
  );
}
