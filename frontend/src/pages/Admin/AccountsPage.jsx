import { useMemo, useState } from 'react';
import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import { useApp } from '../../context/AppContext';

export default function AccountsPage() {
  const { accounts, designers, setAccountStatus, removeAccount, setDesignerStatus, removeDesigner } = useApp();
  const [query, setQuery] = useState('');
  const [role, setRole] = useState('');
  const filtered = useMemo(() => accounts.filter((item) => {
    const q = query.toLowerCase();
    return (!q || `${item.name} ${item.email}`.toLowerCase().includes(q)) && (!role || item.role === role);
  }), [accounts, query, role]);

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Account administration" title="Manage customer and ID company accounts" text="View, suspend, reactivate or remove registered users and companies." />
      <div className="panel filters-grid simple-filters"><label className="span-2">Search name / email<input value={query} onChange={(e) => setQuery(e.target.value)} /></label><label>Role<select value={role} onChange={(e) => setRole(e.target.value)}><option value="">All</option><option value="customer">Customer</option><option value="designer">Designer user</option><option value="admin">Admin</option></select></label></div>
      <div className="section-heading"><div><h2>User accounts</h2></div></div>
      <div className="table-wrap panel"><table><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead><tbody>{filtered.map((account) => <tr key={account.id}><td>{account.name}</td><td>{account.email}</td><td>{account.role}</td><td><StatusBadge>{account.status}</StatusBadge></td><td className="action-cell">{account.status === 'active' ? <button className="secondary-button compact" onClick={() => setAccountStatus(account.id, 'suspended')}>Suspend</button> : <button className="secondary-button compact" onClick={() => setAccountStatus(account.id, 'active')}>Reactivate</button>}<button className="danger-button compact" onClick={() => removeAccount(account.id)}>Remove</button></td></tr>)}</tbody></table></div>

      <div className="section-heading roomy"><div><h2>ID company accounts</h2></div></div>
      <div className="table-wrap panel"><table><thead><tr><th>Company</th><th>Registration</th><th>Contact</th><th>Status</th><th>Actions</th></tr></thead><tbody>{designers.map((designer) => <tr key={designer.id}><td>{designer.companyName}</td><td>{designer.registrationNo}</td><td>{designer.contactEmail}</td><td><StatusBadge>{designer.status}</StatusBadge></td><td className="action-cell">{designer.status === 'active' ? <button className="secondary-button compact" onClick={() => setDesignerStatus(designer.id, 'suspended')}>Suspend</button> : designer.verified && designer.status === 'suspended' ? <button className="secondary-button compact" onClick={() => setDesignerStatus(designer.id, 'active')}>Reactivate</button> : <span className="muted">Use Verification</span>}<button className="danger-button compact" onClick={() => removeDesigner(designer.id)}>Remove</button></td></tr>)}</tbody></table></div>
    </div>
  );
}
