import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import { useApp } from '../../context/AppContext';

export default function AdminDashboard({ go }) {
  const { accounts, designers, projects, enquiries, companyReports } = useApp();
  const pendingCompanies = designers.filter((item) => !item.verified && item.status === 'pending').length;
  const activeCustomers = accounts.filter((item) => item.role === 'customer' && item.status === 'active').length;
  const activeDesigners = designers.filter((item) => item.verified && item.status === 'active').length;
  const openReports = companyReports.filter((item) => item.status === 'open').length;

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Platform management" title="Administrator dashboard" text="Monitor customers, interior design companies, renovation activity and platform health." />
      <div className="metric-grid four">
        <button className="metric-card" onClick={() => go('admin-accounts')}><span>Active customers</span><strong>{activeCustomers}</strong><small>Manage accounts</small></button>
        <button className="metric-card" onClick={() => go('admin-verification')}><span>Verified companies</span><strong>{activeDesigners}</strong><small>{pendingCompanies} pending approval</small></button>
        <button className="metric-card" onClick={() => go('admin-reports')}><span>Open reports</span><strong>{openReports}</strong><small>Investigate complaints</small></button>
        <div className="metric-card static"><span>Published IDPs</span><strong>{projects.filter((item) => item.published).length}</strong><small>{enquiries.length} enquiry record(s)</small></div>
      </div>

      <div className="section-heading"><div><span className="eyebrow">Platform statistics</span><h2>Current activity</h2></div></div>
      <div className="stats-panel panel">
        <div><span>Total registrations</span><strong>{accounts.length + designers.length}</strong></div>
        <div><span>Total designers</span><strong>{designers.length}</strong></div>
        <div><span>Total projects</span><strong>{projects.length}</strong></div>
        <div><span>Quotation enquiries</span><strong>{enquiries.length}</strong></div>
      </div>
      <div className="section-heading roomy"><div><span className="eyebrow">Recent company statuses</span><h2>Interior design companies</h2></div></div>
      <div className="table-wrap panel"><table><thead><tr><th>Company</th><th>Location</th><th>Rating</th><th>Status</th></tr></thead><tbody>{designers.map((designer) => <tr key={designer.id}><td>{designer.companyName}</td><td>{designer.location}</td><td>{designer.rating || 'New'}</td><td><StatusBadge>{designer.status}</StatusBadge></td></tr>)}</tbody></table></div>
    </div>
  );
}
