import PageHeader from '../../components/PageHeader';
import DesignerCard from '../../components/DesignerCard';
import ProjectCard from '../../components/ProjectCard';
import { useApp } from '../../context/AppContext';

export default function CustomerHome({ go, openDesigner, openProject }) {
  const { user, designers, projects, consultations, payments } = useApp();
  const approvedDesigners = designers.filter((item) => item.verified && item.status === 'active');
  const publishedProjects = projects.filter((item) => item.published);
  const upcoming = consultations.filter((item) => item.customerName === user?.name).length;
  const outstanding = payments.filter((item) => item.customerName === user?.name && item.status === 'Outstanding').reduce((sum, item) => sum + item.amount, 0);

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Homeowner portal" title={`Hello, ${user?.name || 'Homeowner'}`} text="Explore designers, save inspiration and manage your renovation activity." />
      <div className="metric-grid">
        <button className="metric-card" onClick={() => go('customer-designers')}><span>Verified designers</span><strong>{approvedDesigners.length}</strong><small>Browse companies</small></button>
        <button className="metric-card" onClick={() => go('customer-consultations')}><span>Consultations</span><strong>{upcoming}</strong><small>View schedule</small></button>
        <button className="metric-card" onClick={() => go('customer-payments')}><span>Outstanding</span><strong>${outstanding.toLocaleString()}</strong><small>View payments</small></button>
      </div>

      <div className="section-heading"><div><span className="eyebrow">Find a company</span><h2>Interior designers</h2></div><button className="text-button" onClick={() => go('customer-designers')}>View all →</button></div>
      <div className="card-grid">{approvedDesigners.slice(0, 3).map((designer) => <DesignerCard key={designer.id} designer={designer} onView={openDesigner} />)}</div>

      <div className="section-heading"><div><span className="eyebrow">Renovation inspiration</span><h2>Browse published IDPs</h2></div><button className="text-button" onClick={() => go('customer-idps')}> Browse & Filter All →</button></div>
      <div className="card-grid">{publishedProjects.slice(0, 6).map((project) => <ProjectCard key={project.id} project={project} onView={openProject} />)}</div>
    </div>
  );
}
