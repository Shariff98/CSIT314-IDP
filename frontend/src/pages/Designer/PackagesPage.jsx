import { useState } from 'react';
import FieldError from '../../components/FieldError';
import PageHeader from '../../components/PageHeader';
import { useApp } from '../../context/AppContext';
import { isPositiveNumber, isRequired } from '../../utils/validation';

const blank = { name: '', renovationType: '', price: '', description: '', services: '' };

export default function PackagesPage() {
  const { user, packages, savePackage, updatePackage, deletePackage } = useApp();
  const designerId = user?.designerId || 101;
  const mine = packages.filter((item) => item.designerId === designerId);
  const [form, setForm] = useState(blank);
  const [editingId, setEditingId] = useState(null);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');

  function edit(item) {
    setEditingId(item.id);
    setForm({ name: item.name, renovationType: item.renovationType, price: item.price, description: item.description, services: item.services.join(', ') });
    setMessage('');
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(blank);
    setErrors({});
  }

  async function submit(event) {
    event.preventDefault();
    const next = {};
    if (!isRequired(form.name)) next.name = 'Package name is required.';
    if (!isRequired(form.renovationType)) next.renovationType = 'Renovation type is required.';
    if (!isPositiveNumber(form.price)) next.price = 'Price must be greater than 0.';
    if (!isRequired(form.description)) next.description = 'Description is required.';
    if (!isRequired(form.services)) next.services = 'List at least one service.';
    setErrors(next);
    if (Object.keys(next).length) return;

    const payload = { ...form, price: Number(form.price), services: form.services.split(',').map((item) => item.trim()).filter(Boolean) };
    if (editingId) {
      await updatePackage(editingId, payload);
      setMessage('Renovation package updated.');
    } else {
      await savePackage(payload);
      setMessage('Renovation package created.');
    }
    setEditingId(null);
    setForm(blank);
  }

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Commercial offering" title="Renovation packages" text="Create packages, then update pricing/services or remove outdated offerings." />
      <div className="two-panel-grid">
        <form className="panel form-card" onSubmit={submit} noValidate>
          <div className="section-heading compact-heading"><div><h2>{editingId ? 'Edit package' : 'Create package'}</h2></div>{editingId && <button type="button" className="text-button" onClick={cancelEdit}>Cancel</button>}</div>
          <label>Package name<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /><FieldError message={errors.name} /></label>
          <label>Renovation type<input value={form.renovationType} onChange={(e) => setForm({ ...form, renovationType: e.target.value })} /><FieldError message={errors.renovationType} /></label>
          <label>Price (SGD)<input type="number" min="1" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} /><FieldError message={errors.price} /></label>
          <label>Description<textarea rows="4" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /><FieldError message={errors.description} /></label>
          <label>Services (comma-separated)<input value={form.services} onChange={(e) => setForm({ ...form, services: e.target.value })} /><FieldError message={errors.services} /></label>
          <button className="primary-button" type="submit">{editingId ? 'Update package' : 'Create package'}</button>{message && <div className="alert success-alert">{message}</div>}
        </form>
        <div className="stack-list">{mine.map((item) => <article className="panel list-card" key={item.id}><div><span className="card-kicker">{item.renovationType}</span><h3>{item.name}</h3><p>{item.description}</p><strong>${item.price.toLocaleString()}</strong></div><div className="card-actions"><button className="secondary-button" onClick={() => edit(item)}>Edit</button><button className="danger-button" onClick={() => deletePackage(item.id)}>Remove</button></div></article>)}</div>
      </div>
    </div>
  );
}
