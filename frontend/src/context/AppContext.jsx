import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import {
  demoAccounts,
  initialActiveProjects,
  initialCategories,
  initialCompanyReports,
  initialConsultations,
  initialDesigners,
  initialEnquiries,
  initialPackages,
  initialPayments,
  initialProjects,
  initialReviews,
} from '../data/mockData';
import { api, flaskApi } from '../services/api';
import { publicUser, registrationPayload, unauthenticatedMessage } from '../utils/auth';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authMessage, setAuthMessage] = useState('');
  const authVersion = useRef(0);
  const authBusy = useRef(false);
  const identity = useRef(null);
  const [accounts, setAccounts] = useState(() => demoAccounts.map(({ password, ...account }) => account));
  const [designers, setDesigners] = useState(initialDesigners);
  const [projects, setProjects] = useState(initialProjects);
  const [packages, setPackages] = useState(initialPackages);
  const [reviews, setReviews] = useState(initialReviews);
  const [enquiries, setEnquiries] = useState(initialEnquiries);
  const [consultations, setConsultations] = useState(initialConsultations);
  const [payments, setPayments] = useState(initialPayments);
  const [activeProjects, setActiveProjects] = useState(initialActiveProjects);
  const [companyReports, setCompanyReports] = useState(initialCompanyReports);
  const [categories, setCategories] = useState(initialCategories);
  const [favouriteDesignerIds, setFavouriteDesignerIds] = useState([]);
  const [favouriteProjectIds, setFavouriteProjectIds] = useState([]);

  function clearUserState() {
    identity.current = null;
    setUser(null);
    setFavouriteDesignerIds([]);
    setFavouriteProjectIds([]);
    setAccounts(demoAccounts.map(({ password, ...account }) => account));
    setDesigners(initialDesigners);
    setProjects(initialProjects);
    setPackages(initialPackages);
    setReviews(initialReviews);
    setEnquiries(initialEnquiries);
    setConsultations(initialConsultations);
    setPayments(initialPayments);
    setActiveProjects(initialActiveProjects);
    setCompanyReports(initialCompanyReports);
    setCategories(initialCategories);
  }

  useEffect(() => {
    let active = true;
    async function restoreSession() {
      if (authBusy.current) return;
      const version = ++authVersion.current;
      try {
        const response = await flaskApi.getCurrentUser();
        if (active && version === authVersion.current) {
          const restored = publicUser(response.data.user);
          if (identity.current !== null && identity.current !== restored.id) clearUserState();
          identity.current = restored.id;
          setUser(restored);
          setAuthMessage('');
        }
      } catch (error) {
        if (!active || version !== authVersion.current) return;
        if (error.status === 401) {
          const wasAuthenticated = identity.current !== null;
          clearUserState();
          setAuthMessage(current => unauthenticatedMessage(wasAuthenticated, current));
        } else {
          setAuthMessage(error.message);
        }
      } finally {
        if (active && version === authVersion.current) setAuthLoading(false);
      }
    }
    restoreSession();
    // Recheck when returning to the tab, so expired sessions are cleared.
    window.addEventListener('focus', restoreSession);
    return () => { active = false; window.removeEventListener('focus', restoreSession); };
  }, []);

  async function login(email, password) {
    ++authVersion.current;
    authBusy.current = true;
    try {
      const response = await flaskApi.login({ email, password });
      const account = publicUser(response.data.user);
      clearUserState();
      identity.current = account.id;
      setAuthMessage('');
      setUser(account);
      return account;
    } finally {
      authBusy.current = false;
    }
  }

  async function registerCustomer(data) {
    const response = await flaskApi.registerCustomer(registrationPayload(data));
    setAuthMessage('Account created. Please log in with your email and password.');
    return response.data.user;
  }

  async function logout() {
    ++authVersion.current;
    authBusy.current = true;
    try {
      await flaskApi.logout();
      clearUserState();
      setAuthMessage('You have been logged out.');
    } finally {
      authBusy.current = false;
    }
  }

  async function toggleFavouriteDesigner(id) {
    const saved = !favouriteDesignerIds.includes(id);
    await api.toggleFavouriteDesigner(id, saved);
    setFavouriteDesignerIds((current) => (saved ? [...current, id] : current.filter((item) => item !== id)));
  }

  async function toggleFavouriteProject(id) {
    const saved = !favouriteProjectIds.includes(id);
    await api.toggleFavouriteProject(id, saved);
    setFavouriteProjectIds((current) => (saved ? [...current, id] : current.filter((item) => item !== id)));
  }

  function incrementProjectView(id) {
    // === BACKEND INTEGRATION ===
    // Backend should increment view count once per customer/session based on assignment rules.
    setProjects((current) => current.map((project) => (project.id === id ? { ...project, views: project.views + 1 } : project)));
  }

  async function submitEnquiry(data) {
    await api.submitEnquiry(data);
    const enquiry = {
      id: Date.now(),
      ...data,
      customerName: user?.name || data.name,
      status: 'pending',
      createdAt: new Date().toISOString().slice(0, 10),
    };
    setEnquiries((current) => [enquiry, ...current]);
    return enquiry;
  }

  async function submitRequirements(data) {
    await api.submitRequirements(data);
    const enquiry = {
      id: Date.now(),
      ...data,
      customerName: user?.name || data.name || 'Customer',
      status: 'pending',
      createdAt: new Date().toISOString().slice(0, 10),
    };
    setEnquiries((current) => [enquiry, ...current]);
    return enquiry;
  }

  async function bookConsultation(data) {
    await api.bookConsultation(data);
    const consultation = { id: Date.now(), customerName: user?.name || 'Customer', status: 'pending', ...data };
    setConsultations((current) => [consultation, ...current]);
    return consultation;
  }

  async function makePayment(data) {
    await api.makePayment(data);
    const payment = {
      id: Date.now(),
      customerName: user?.name || 'Customer',
      date: new Date().toISOString().slice(0, 10),
      status: 'Paid',
      invoiceNo: `INV-${new Date().getFullYear()}-${String(Date.now()).slice(-5)}`,
      ...data,
    };
    setPayments((current) => [payment, ...current]);
    return payment;
  }

  async function settleOutstandingInvoice(id) {
    const invoice = payments.find((item) => item.id === id);

    // Only the customer who owns the invoice can settle it.
    if (
      user?.role !== 'Customer' ||
      !invoice ||
      invoice.customerName !== user.name
    ) {
      throw new Error('Invoice not found for this customer.');
    }

    if (invoice.status !== 'Outstanding') {
      throw new Error('This invoice is already paid.');
    }

    // === BACKEND INTEGRATION ===
    // Python must verify invoice ownership and confirm payment
    // before marking the invoice as Paid.
    await api.settleOutstandingInvoice(id);

    const updated = {
      ...invoice,
      status: 'Paid',
      paidOn: new Date().toISOString().slice(0, 10),
    };

    // Update the EXISTING invoice, instead of adding a duplicate.
    setPayments((current) =>
      current.map((item) =>
        item.id === id ? updated : item
      )
    );

    return updated;
  }

  async function submitReview(data) {
    await api.submitReview(data);
    const review = {
      id: Date.now(),
      customerName: user?.name || 'Customer',
      date: new Date().toISOString().slice(0, 10),
      response: '',
      ...data,
    };
    setReviews((current) => [review, ...current]);
    return review;
  }

  async function reportCompany(data) {
    await api.reportCompany(data);
    const report = {
      id: Date.now(),
      customerName: user?.name || 'Customer',
      date: new Date().toISOString().slice(0, 10),
      status: 'open',
      ...data,
    };
    setCompanyReports((current) => [report, ...current]);
    return report;
  }

  async function saveCompanyProfile(data) {
    await api.saveCompanyProfile(data);
    const designerId = user?.designerId || 101;
    setDesigners((current) => current.map((designer) => (designer.id === designerId ? { ...designer, ...data, status: designer.verified ? 'active' : 'pending' } : designer)));
  }

  async function createPortfolioProject(data) {
    await api.createPortfolioProject(data);
    const project = {
      id: Date.now(),
      designerId: user?.designerId || 101,
      views: 0,
      published: true,
      ...data,
    };
    setProjects((current) => [project, ...current]);
    return project;
  }

  async function updatePortfolioProject(id, data) {
    await api.updatePortfolioProject(id, data);
    setProjects((current) => current.map((project) => (project.id === id ? { ...project, ...data } : project)));
  }

  async function deletePortfolioProject(id) {
    await api.deletePortfolioProject(id);
    setProjects((current) => current.filter((project) => project.id !== id));
    setFavouriteProjectIds((current) => current.filter((projectId) => projectId !== id));
  }

  async function savePackage(data) {
    await api.savePackage(data);
    const packageItem = { id: Date.now(), designerId: user?.designerId || 101, ...data };
    setPackages((current) => [packageItem, ...current]);
    return packageItem;
  }

  async function updatePackage(id, data) {
    await api.updatePackage(id, data);
    setPackages((current) => current.map((item) => (item.id === id ? { ...item, ...data } : item)));
  }

  async function deletePackage(id) {
    await api.deletePackage(id);
    setPackages((current) => current.filter((item) => item.id !== id));
  }

  async function updateEnquiryStatus(id, status) {
    await api.updateEnquiryStatus(id, status);
    setEnquiries((current) => current.map((enquiry) => (enquiry.id === id ? { ...enquiry, status } : enquiry)));
  }

  async function updateConsultation(id, updates) {
    await api.updateConsultation(id, updates);
    setConsultations((current) => current.map((item) => (item.id === id ? { ...item, ...updates } : item)));
  }

  async function toggleMilestone(projectId, milestoneId) {
    const project = activeProjects.find((item) => item.id === projectId);
    const milestone = project?.milestones.find((item) => item.id === milestoneId);
    if (!project || !milestone) return;
    await api.updateMilestone(projectId, { milestoneId, completed: !milestone.completed });
    setActiveProjects((current) => current.map((item) => item.id === projectId ? {
      ...item,
      milestones: item.milestones.map((entry) => entry.id === milestoneId ? { ...entry, completed: !entry.completed } : entry),
    } : item));
  }

  async function respondReview(id, response) {
    await api.respondReview(id, response);
    setReviews((current) => current.map((review) => (review.id === id ? { ...review, response } : review)));
  }

  async function setAccountStatus(id, status) {
    await api.updateAccount(id, { status });
    setAccounts((current) => current.map((account) => (account.id === id ? { ...account, status } : account)));
  }

  async function removeAccount(id) {
    await api.updateAccount(id, { removed: true });
    setAccounts((current) => current.filter((account) => account.id !== id));
  }

  async function setDesignerStatus(id, status) {
    await api.updateCompanyAccount(id, { status });
    setDesigners((current) => current.map((designer) => (designer.id === id ? { ...designer, status } : designer)));
  }

  async function removeDesigner(id) {
    await api.removeCompanyAccount(id);
    setDesigners((current) => current.filter((designer) => designer.id !== id));
  }

  async function verifyCompany(id, status) {
    await api.verifyCompany(id, status);
    setDesigners((current) => current.map((designer) => designer.id === id ? {
      ...designer,
      verified: status === 'approved',
      status: status === 'approved' ? 'active' : 'rejected',
    } : designer));
  }

  async function resolveReport(id, status) {
    await api.resolveReport(id, { status });
    setCompanyReports((current) => current.map((report) => (report.id === id ? { ...report, status } : report)));
  }

  async function removeReview(id) {
    await api.removeReview(id);
    setReviews((current) => current.filter((review) => review.id !== id));
  }

  async function addCategory(name) {
    await api.saveCategory({ name });
    if (!categories.some((category) => category.toLowerCase() === name.toLowerCase())) {
      setCategories((current) => [...current, name]);
    }
  }

  function removeCategory(name) {
    // === BACKEND INTEGRATION === DELETE /admin/categories/:id
    setCategories((current) => current.filter((category) => category !== name));
  }

  const value = useMemo(() => ({
    user,
    authLoading,
    authMessage,
    accounts,
    designers,
    projects,
    packages,
    reviews,
    enquiries,
    consultations,
    payments,
    activeProjects,
    companyReports,
    categories,
    favouriteDesignerIds,
    favouriteProjectIds,
    login,
    registerCustomer,
    logout,
    toggleFavouriteDesigner,
    toggleFavouriteProject,
    incrementProjectView,
    submitEnquiry,
    submitRequirements,
    bookConsultation,
    makePayment,
    settleOutstandingInvoice,
    submitReview,
    reportCompany,
    saveCompanyProfile,
    createPortfolioProject,
    updatePortfolioProject,
    deletePortfolioProject,
    savePackage,
    updatePackage,
    deletePackage,
    updateEnquiryStatus,
    updateConsultation,
    toggleMilestone,
    respondReview,
    setAccountStatus,
    removeAccount,
    setDesignerStatus,
    removeDesigner,
    verifyCompany,
    resolveReport,
    removeReview,
    addCategory,
    removeCategory,
  }), [
    user, authLoading, authMessage, accounts, designers, projects, packages, reviews, enquiries, consultations, payments,
    activeProjects, companyReports, categories, favouriteDesignerIds, favouriteProjectIds,
  ]);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const value = useContext(AppContext);
  if (!value) throw new Error('useApp must be used inside AppProvider');
  return value;
}
