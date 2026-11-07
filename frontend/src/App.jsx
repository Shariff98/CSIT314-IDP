import { useEffect, useRef, useState } from 'react';
import Layout from './components/Layout';
import { useApp } from './context/AppContext';
import { homeForRole, canAccessPage, initialPage } from './utils/auth';

import LandingPage from './pages/Public/LandingPage';
import LoginPage from './pages/Public/LoginPage';
import RegisterPage from './pages/Public/RegisterPage';

import CustomerHome from './pages/Customer/CustomerHome';
import DesignersPage from './pages/Customer/DesignersPage';
import IDPsPage from './pages/Customer/IDPsPage';
import DesignerProfilePage from './pages/Customer/DesignerProfilePage';
import IDPDetailsPage from './pages/Customer/IDPDetailsPage';
import ApiIDPDetailsPage from './pages/Customer/ApiIDPDetailsPage';
import RequirementsPage from './pages/Customer/RequirementsPage';
import FavouritesPage from './pages/Customer/FavouritesPage';
import CustomerConsultationsPage from './pages/Customer/ConsultationsPage';
import CustomerPaymentsPage from './pages/Customer/PaymentsPage';

import DesignerDashboard from './pages/Designer/DesignerDashboard';
import CompanyProfilePage from './pages/Designer/CompanyProfilePage';
import PortfolioPage from './pages/Designer/PortfolioPage';
import PackagesPage from './pages/Designer/PackagesPage';
import EnquiriesPage from './pages/Designer/EnquiriesPage';
import DesignerConsultationsPage from './pages/Designer/ConsultationsPage';
import ProjectsPage from './pages/Designer/ProjectsPage';
import DesignerPaymentsPage from './pages/Designer/PaymentsPage';
import DesignerReviewsPage from './pages/Designer/ReviewsPage';

import AdminDashboard from './pages/Admin/AdminDashboard';
import AccountsPage from './pages/Admin/AccountsPage';
import VerificationPage from './pages/Admin/VerificationPage';
import ReportsPage from './pages/Admin/ReportsPage';
import ModerationPage from './pages/Admin/ModerationPage';
import CategoriesPage from './pages/Admin/CategoriesPage';

export default function App() {
  const { user, authLoading } = useApp();
  const [page, setPage] = useState('landing');
  const [initialNavigationPending, setInitialNavigationPending] = useState(true);
  const explicitlyNavigated = useRef(false);
  const [selectedDesignerId, setSelectedDesignerId] = useState(101);
  const [selectedProjectId, setSelectedProjectId] = useState(201);
  const [selectedApiProjectId, setSelectedApiProjectId] = useState(null);

  const go = (next) => {
    explicitlyNavigated.current = true;
    setPage(next);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const openDesigner = (id) => {
    setSelectedDesignerId(id);
    go('designer-profile');
  };

  const openProject = (id) => {
    setSelectedProjectId(id);
    go('project-details');
  };

  const openApiProject = (id) => {
    setSelectedApiProjectId(id);
    go('api-project-details');
  };

  const allowed = canAccessPage(page, user);
  useEffect(() => {
    if (!authLoading && initialNavigationPending) {
      setPage(current => initialPage(current, user, explicitlyNavigated.current, window.location.pathname === '/'));
      setInitialNavigationPending(false);
    }
  }, [authLoading, initialNavigationPending, user]);
  useEffect(() => {
    if (!authLoading && !initialNavigationPending && !allowed) setPage(user ? homeForRole[user.role] || 'landing' : 'login');
  }, [page, user, authLoading, initialNavigationPending, allowed]);

  if (authLoading || initialNavigationPending) return <Layout page={page} go={go}><div className="auth-page" role="status">Checking your login session...</div></Layout>;
  if (!allowed) return <Layout page={page} go={go}><div className="auth-page" role="status">Opening your account page...</div></Layout>;

  let content;
  switch (page) {
    case 'login': content = <LoginPage go={go} />; break;
    case 'register': content = <RegisterPage go={go} />; break;
    case 'designer-profile': content = <DesignerProfilePage designerId={selectedDesignerId} go={go} openProject={openProject} />; break;
    case 'project-details': content = <IDPDetailsPage projectId={selectedProjectId} go={go} openDesigner={openDesigner} />; break;
    case 'api-project-details': content = <ApiIDPDetailsPage key={selectedApiProjectId} projectId={selectedApiProjectId} onBack={() => go('customer-idps')} />; break;

    case 'customer-home': content = <CustomerHome go={go} openDesigner={openDesigner} openProject={openProject} />; break;
    case 'customer-designers': content = <DesignersPage openDesigner={openDesigner} openProject={openProject} />; break;
    case 'customer-idps': content = <IDPsPage openApiProject={openApiProject} />; break;
    case 'customer-requirements': content = <RequirementsPage />; break;
    case 'customer-favourites': content = <FavouritesPage openDesigner={openDesigner} openApiProject={openApiProject} />; break;
    case 'customer-consultations': content = <CustomerConsultationsPage />; break;
    case 'customer-payments': content = <CustomerPaymentsPage />; break;

    case 'designer-dashboard': content = <DesignerDashboard openProject={openProject} go={go} />; break;
    case 'designer-company': content = <CompanyProfilePage />; break;
    case 'designer-portfolio': content = <PortfolioPage />; break;
    case 'designer-packages': content = <PackagesPage />; break;
    case 'designer-enquiries': content = <EnquiriesPage />; break;
    case 'designer-consultations': content = <DesignerConsultationsPage />; break;
    case 'designer-projects': content = <ProjectsPage />; break;
    case 'designer-payments': content = <DesignerPaymentsPage />; break;
    case 'designer-reviews': content = <DesignerReviewsPage />; break;

    case 'admin-dashboard': content = <AdminDashboard go={go} />; break;
    case 'admin-accounts': content = <AccountsPage />; break;
    case 'admin-verification': content = <VerificationPage />; break;
    case 'admin-reports': content = <ReportsPage />; break;
    case 'admin-moderation': content = <ModerationPage />; break;
    case 'manager-categories':
    case 'admin-categories': content = <CategoriesPage />; break;

    default: content = <LandingPage go={go} openDesigner={openDesigner} openProject={openProject} />;
  }

  return <Layout page={page} go={go}>{content}</Layout>;
}
