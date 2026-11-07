import PageHeader from '../../components/PageHeader';
import ProjectCard from '../../components/ProjectCard';
import StatusBadge from '../../components/StatusBadge';
import { useApp } from '../../context/AppContext';

export default function DesignerDashboard({ openProject, go }) {
  const { user, designers, projects, enquiries, consultations, reviews } = useApp();
  const designerId = user?.designerId || 101;
  const company = designers.find((item) => item.id === designerId);
  const mine = projects.filter((item) => item.designerId === designerId);
  const myEnquiries = enquiries.filter((item) => item.designerId === designerId);
  const myConsultations = consultations.filter((item) => item.designerId === designerId);
  const myReviews = reviews.filter((item) => item.designerId === designerId);
  const totalViews = mine.reduce((sum, item) => sum + item.views, 0);
  const averageRating = myReviews.length ? (myReviews.reduce((sum, item) => sum + item.rating, 0) / myReviews.length).toFixed(1) : '—';

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Interior designer portal" title={company?.companyName || 'Company dashboard'} text="Monitor project interest, enquiries, consultations and customer feedback." actions={<StatusBadge>{company?.verified ? 'verified' : company?.status || 'pending'}</StatusBadge>} />
      <div className="metric-grid four">
        <button className="metric-card" onClick={() => go('designer-portfolio')}><span>Total project views</span><strong>{totalViews.toLocaleString()}</strong><small>Selected assignment feature</small></button>
        <button className="metric-card" onClick={() => go('designer-enquiries')}><span>Pending enquiries</span><strong>{myEnquiries.filter((item) => item.status === 'pending').length}</strong><small>Customer requests</small></button>
        <button className="metric-card" onClick={() => go('designer-consultations')}><span>Consultations</span><strong>{myConsultations.length}</strong><small>Manage appointments</small></button>
        <button className="metric-card" onClick={() => go('designer-reviews')}><span>Company rating</span><strong>{averageRating}★</strong><small>{myReviews.length} review(s)</small></button>
      </div>
      {!company?.verified && <div className="alert warning-alert">Your company profile is pending administrator verification. In a real backend, quotation and project actions should remain restricted until approval.</div>}
      <div className="section-heading"><div><span className="eyebrow">Portfolio performance</span><h2>Views for each IDP</h2></div><button className="primary-button" onClick={() => go('designer-portfolio')}>Manage portfolio</button></div>
      <div className="card-grid">{mine.map((project) => <ProjectCard key={project.id} project={project} onView={openProject} showSave={false} />)}</div>
    </div>
  );
}
