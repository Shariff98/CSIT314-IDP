import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import { useApp } from '../../context/AppContext';

export default function DesignerPaymentsPage() {
  const { user, payments } = useApp();
  const designerId = user?.designerId || 101;
  const mine = payments.filter((item) => item.designerId === designerId);
  const paid = mine.filter((item) => item.status === 'Paid').reduce((sum, item) => sum + item.amount, 0);
  const outstanding = mine.filter((item) => item.status === 'Outstanding').reduce((sum, item) => sum + item.amount, 0);
  return (
    <div className="page-shell">
      <PageHeader eyebrow="Project finance" title="Customer payments" text="View payment records associated with your renovation projects." />
      <div className="metric-grid"><div className="metric-card static"><span>Total received</span><strong>${paid.toLocaleString()}</strong></div><div className="metric-card static"><span>Outstanding</span><strong>${outstanding.toLocaleString()}</strong></div><div className="metric-card static"><span>Records</span><strong>{mine.length}</strong></div></div>
      <div className="table-wrap panel"><table><thead><tr><th>Customer</th><th>Project</th><th>Invoice</th><th>Type</th><th>Amount</th><th>Status</th></tr></thead><tbody>{mine.map((item) => <tr key={item.id}><td>{item.customerName}</td><td>{item.projectName}</td><td>{item.invoiceNo}</td><td>{item.type}</td><td>${item.amount.toLocaleString()}</td><td><StatusBadge>{item.status}</StatusBadge></td></tr>)}</tbody></table></div>
    </div>
  );
}
