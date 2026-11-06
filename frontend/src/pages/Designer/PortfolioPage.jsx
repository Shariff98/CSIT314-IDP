import { useState } from 'react';
import FieldError from '../../components/FieldError';
import PageHeader from '../../components/PageHeader';
import ProjectCard from '../../components/ProjectCard';
import { useApp } from '../../context/AppContext';
import { isPositiveNumber, isRequired, validateFiles } from '../../utils/validation';
import { PROPERTY_TYPES } from '../../data/options';

const blank = { title: '', description: '', propertyType: '', location: '', budget: '', completionDate: '', category: '', styles: '' };

export default function PortfolioPage() {
  const { user, projects, categories, createPortfolioProject, updatePortfolioProject, deletePortfolioProject } = useApp();
  const designerId = user?.designerId || 101;
  const mine = projects.filter((item) => item.designerId === designerId);
  const [form, setForm] = useState(blank);
  const [files, setFiles] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');

  function edit(project) {
    setEditingId(project.id);
    setForm({ title: project.title, description: project.description, propertyType: project.propertyType, location: project.location, budget: project.budget, completionDate: project.completionDate, category: project.category, styles: project.styles.join(', ') });
    setMessage('');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function submit(event) {
    event.preventDefault();
    const next = {};
    if (!isRequired(form.title)) next.title = 'Title is required.';
    if (!isRequired(form.description)) next.description = 'Description is required.';
    if (!isRequired(form.propertyType)) next.propertyType = 'Property type is required.';
    if (!isRequired(form.location)) next.location = 'Location is required.';
    if (!isPositiveNumber(form.budget)) next.budget = 'Budget must be greater than 0.';
    if (!isRequired(form.completionDate)) next.completionDate = 'Completion date is required.';
    if (!isRequired(form.category)) next.category = 'Choose a category.';
    if (!isRequired(form.styles)) next.styles = 'Add at least one style tag.';
    const fileError = validateFiles(files, { imagesOnly: true, maxFiles: 8 });
    if (!editingId && !files.length) next.photos = 'Upload at least one project photo.';
    if (fileError) next.photos = fileError;
    setErrors(next);
    if (Object.keys(next).length) return;

    const existing = editingId ? projects.find((item) => item.id === editingId) : null;
    const payload = {
      ...form,
      budget: Number(form.budget),
      styles: form.styles.split(',').map((item) => item.trim()).filter(Boolean),
      photos: files.length ? Array.from(files).map((_, index) => ['/project-living.svg','/project-kitchen.svg','/project-bedroom.svg'][index % 3]) : existing?.photos,
    };
    // === BACKEND INTEGRATION === Actual images should be uploaded with multipart/form-data and stored by Python/cloud storage.
    if (editingId) {
      await updatePortfolioProject(editingId, payload);
      setMessage('Portfolio project updated.');
    } else {
      await createPortfolioProject(payload);
      setMessage('Portfolio project created and published in this prototype.');
    }
    setEditingId(null);
    setForm(blank);
    setFiles([]);
    event.target.reset();
  }

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Selected IDP features" title="Create and manage portfolio" text="Create an IDP with details, assign category/style tags, upload multiple photos, then edit or remove projects." />
      <form className="panel form-card" onSubmit={submit} noValidate>
        <div className="section-heading compact-heading"><div><h2>{editingId ? 'Edit portfolio project' : 'Create portfolio project'}</h2></div>{editingId && <button type="button" className="text-button" onClick={() => { setEditingId(null); setForm(blank); }}>Cancel edit</button>}</div>
        <div className="two-column-form">
          <label>Project title<input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /><FieldError message={errors.title} /></label>
          <label>Property type<select value={form.propertyType} onChange={(e) => setForm({...form, propertyType: e.target.value})}><option value="">Choose property type</option>{PROPERTY_TYPES.map((type) => (<option key={type} value={type}>{type}</option>))}</select><FieldError message={errors.propertyType} /></label>
          <label>Location<input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} /><FieldError message={errors.location} /></label>
          <label>Budget (SGD)<input type="number" min="1" value={form.budget} onChange={(e) => setForm({ ...form, budget: e.target.value })} /><FieldError message={errors.budget} /></label>
          <label>Completion date<input type="date" value={form.completionDate} onChange={(e) => setForm({ ...form, completionDate: e.target.value })} /><FieldError message={errors.completionDate} /></label>
          <label>Category<select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}><option value="">Choose category</option>{categories.map((item) => <option key={item}>{item}</option>)}</select><FieldError message={errors.category} /></label>
        </div>
        <label>Description<textarea rows="4" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /><FieldError message={errors.description} /></label>
        <label>Style tags (comma-separated)<input value={form.styles} onChange={(e) => setForm({ ...form, styles: e.target.value })} placeholder="Minimalist, Scandinavian" /><FieldError message={errors.styles} /></label>
        <label>Project photos<input type="file" accept="image/*" multiple onChange={(e) => setFiles(e.target.files)} /><FieldError message={errors.photos} /><small>Multiple image upload selected feature. Mock preview paths are used until backend storage is connected.</small></label>
        <button className="primary-button" type="submit">{editingId ? 'Update project' : 'Create project'}</button>{message && <div className="alert success-alert">{message}</div>}
      </form>
      <div className="section-heading roomy"><div><h2>My portfolio</h2><p className="muted">Each card shows the view counter required by the selected user story.</p></div></div>
      <div className="card-grid">{mine.map((project) => <ProjectCard key={project.id} project={project} editable onEdit={edit} onDelete={deletePortfolioProject} />)}</div>
    </div>
  );
}
