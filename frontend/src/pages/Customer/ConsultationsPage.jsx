import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import { useApp } from '../../context/AppContext';

export default function ConsultationsPage() {
  const { consultations, designers, user } = useApp();
  const mine = consultations.filter((item) => item.customerName === user?.name);
  return (
    <div className="page-shell">
      <PageHeader eyebrow="Appointments" title="Consultation schedule" text="View upcoming consultation requests and their latest status." />
      <div className="table-wrap panel"><table><thead><tr><th>Company</th><th>Date</th><th>Time</th><th>Mode</th><th>Status</th></tr></thead><tbody>{mine.map((item) => { const designer = designers.find((d) => d.id === item.designerId); return <tr key={item.id}><td>{designer?.companyName}</td><td>{item.date}</td><td>{item.time}</td><td>{item.mode}</td><td><StatusBadge>{item.status}</StatusBadge></td></tr>; })}</tbody></table>{!mine.length && <div className="empty-table">No consultation requests yet.</div>}</div>
    </div>
  );
}
