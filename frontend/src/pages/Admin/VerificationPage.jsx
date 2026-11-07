import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import { useApp } from '../../context/AppContext';

export default function VerificationPage() {
  const { designers, verifyCompany } = useApp();
  const pending = designers.filter((item) => !item.verified);
  return (
    <div className="page-shell">
      <PageHeader eyebrow="Company onboarding" title="Verify interior design companies" text="Review new company profiles before allowing them to receive customer requests." />
      <div className="stack-list">
        {pending.map((designer) => <article className="panel verification-card" key={designer.id}>
          <div className="section-heading compact-heading"><div><span className="eyebrow">Registration {designer.registrationNo}</span><h2>{designer.companyName}</h2></div><StatusBadge>{designer.status}</StatusBadge></div>
          <p>{designer.description}</p>
          <div className="info-grid compact-info"><div><strong>Contact</strong><span>{designer.contactEmail}</span><span>{designer.phone}</span></div><div><strong>Location</strong><span>{designer.location}</span></div><div><strong>Specialties</strong><span>{designer.specialties.join(', ')}</span></div></div>
          <div className="card-actions"><button className="primary-button" onClick={() => verifyCompany(designer.id, 'approved')}>Approve registration</button><button className="danger-button" onClick={() => verifyCompany(designer.id, 'rejected')}>Reject registration</button></div>
        </article>)}
        {!pending.length && <div className="empty-state panel"><h3>No pending companies</h3><p>All company registrations have been reviewed.</p></div>}
      </div>
    </div>
  );
}
