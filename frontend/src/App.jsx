import { useEffect, useState } from 'react';
import Layout from './components/Layout';
import { useApp } from './context/AppContext';

import LandingPage from './pages/Public/LandingPage';
import LoginPage from './pages/Public/LoginPage';
import RegisterPage from './pages/Public/RegisterPage';

import CustomerHome from './pages/Customer/CustomerHome';
import DesignersPage from './pages/Customer/DesignersPage';
import IDPsPage from './pages/Customer/IDPsPage';
import DesignerProfilePage from './pages/Customer/DesignerProfilePage';
import IDPDetailsPage from './pages/Customer/IDPDetailsPage';
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

const homeForRole = {
  customer: 'customer-home',
  designer: 'designer-dashboard',
  admin: 'admin-dashboard',
};

export default function App() {
  const { user } = useApp();
  const [page, setPage] = useState('landing');
  const [selectedDesignerId, setSelectedDesignerId] = useState(101);
  const [selectedProjectId, setSelectedProjectId] = useState(201);

  const go = (next) => {
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

useEffect(() => {
  const isPublicProfile = page === 'designer-profile';

  const protectedPrefix = isPublicProfile
    ? null
    : page.startsWith('customer-')
      ? 'customer'
      : page.startsWith('designer-')
        ? 'designer'
        : page.startsWith('admin-')
          ? 'admin'
          : null;

  if (protectedPrefix && !user) {
    setPage('login');
  } else if (protectedPrefix && user?.role !== protectedPrefix) {
    setPage(homeForRole[user.role]);
  }
}, [page, user]);

  let content;
  switch (page) {
    case 'login': content = <LoginPage go={go} />; break;
    case 'register': content = <RegisterPage go={go} />; break;
    case 'designer-profile': content = <DesignerProfilePage designerId={selectedDesignerId} go={go} openProject={openProject} />; break;
    case 'project-details': content = <IDPDetailsPage projectId={selectedProjectId} go={go} openDesigner={openDesigner} />; break;

    case 'customer-home': content = <CustomerHome go={go} openDesigner={openDesigner} openProject={openProject} />; break;
    case 'customer-designers': content = <DesignersPage openDesigner={openDesigner} openProject={openProject} />; break;
    case 'customer-idps': content = <IDPsPage openProject={openProject} />; break;
    case 'customer-requirements': content = <RequirementsPage />; break;
    case 'customer-favourites': content = <FavouritesPage openDesigner={openDesigner} openProject={openProject} />; break;
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
    case 'admin-categories': content = <CategoriesPage />; break;

    default: content = <LandingPage go={go} openDesigner={openDesigner} openProject={openProject} />;
  }

  return <Layout page={page} go={go}>{content}</Layout>;
}
