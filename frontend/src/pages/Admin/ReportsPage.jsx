import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import { useApp } from '../../context/AppContext';

export default function ReportsPage() {
  const { companyReports, designers, resolveReport } = useApp();
  return (
    <div className="page-shell">
      <PageHeader eyebrow="Customer complaints" title="Manage reported companies" text="Investigate submitted complaints and mark them resolved or dismissed." />
      <div className="stack-list">
        {companyReports.map((report) => { const designer = designers.find((item) => item.id === report.designerId); return <article className="panel report-card" key={report.id}><div className="section-heading compact-heading"><div><span className="eyebrow">{report.reason}</span><h2>{designer?.companyName}</h2></div><StatusBadge>{report.status}</StatusBadge></div><p><strong>Reported by:</strong> {report.customerName} · {report.date}</p><p>{report.details}</p><div className="card-actions"><button className="primary-button" onClick={() => resolveReport(report.id, 'resolved')}>Resolve</button><button className="secondary-button" onClick={() => resolveReport(report.id, 'dismissed')}>Dismiss</button></div></article>; })}
      </div>
    </div>
  );
}
