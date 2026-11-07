import { useEffect, useRef, useState } from 'react';
import FieldError from '../../components/FieldError';
import PageHeader from '../../components/PageHeader';
import ProjectCard from '../../components/ProjectCard';
import { useApp } from '../../context/AppContext';
import { isPositiveNumber, isRequired, validateFiles } from '../../utils/validation';
import { PROPERTY_TYPES } from '../../data/options';
import ApiMyPortfolio from './ApiMyPortfolio';
import { flaskApi } from '../../services/api';
import { pageRequest } from '../../utils/projects';
import { createPortfolioMutation, portfolioOptionalFieldErrors } from '../../utils/createPortfolio';

const blank = { title: '', description: '', propertyType: '', location: '', budget: '', completionDate: '', category: '', styles: '' };

export default function PortfolioPage() {
  const { user, projects, categories, updatePortfolioProject, deletePortfolioProject } = useApp();
  const designerId = user?.designerId || 101;
  const mine = projects.filter((item) => item.designerId === designerId);
  const [form, setForm] = useState(blank);
  const [files, setFiles] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');
  const [saveError, setSaveError] = useState('');
  const [saving, setSaving] = useState(false);
  const busy = useRef(false);
  const createReal = useRef(null);
  if (!createReal.current) createReal.current = createPortfolioMutation();
  const [refreshToken, setRefreshToken] = useState(0);
  const [options, setOptions] = useState({ categories: [], property_types: [] });
  const [optionsLoading, setOptionsLoading] = useState(true);
  const [optionsError, setOptionsError] = useState('');
  const [optionsRetry, setOptionsRetry] = useState(0);

  useEffect(() => {
    setOptionsLoading(true);
    setOptionsError('');
    return pageRequest(() => flaskApi.getProjectOptions(), {
      success: response => setOptions(response.data),
      failure: error => setOptionsError(error.message),
      settled: () => setOptionsLoading(false),
    });
  }, [optionsRetry]);

  function edit(project) {
    if (busy.current) return;
    setSaveError('');
    setEditingId(project.id);
    setForm({ title: project.title, description: project.description, propertyType: project.propertyType, location: project.location, budget: project.budget, completionDate: project.completionDate, category: project.category, styles: project.styles.join(', ') });
    setMessage('');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function submit(event) {
    event.preventDefault();
    if (busy.current) return;
    setMessage('');
    setSaveError('');
    const formElement = event.currentTarget;
    const next = {};
    if (!isRequired(form.title)) next.title = 'Title is required.';
    if (!isRequired(form.description)) next.description = 'Description is required.';
    if (!isRequired(form.propertyType)) next.propertyType = 'Property type is required.';
    if (!isRequired(form.location)) next.location = 'Location is required.';
    if (editingId ? !isPositiveNumber(form.budget) : !Number.isSafeInteger(Number(form.budget)) || Number(form.budget) < 1) {
      next.budget = editingId ? 'Budget must be greater than 0.' : 'Budget must be a positive whole number.';
    }
    Object.assign(next, portfolioOptionalFieldErrors(form, !!editingId));
    if (!isRequired(form.category)) next.category = 'Choose a category.';
    if (editingId) {
      const fileError = validateFiles(files, { imagesOnly: true, maxFiles: 8 });
      if (fileError) next.photos = fileError;
    } else if (optionsLoading || optionsError) {
      next.category = 'Load the active categories before creating a project.';
    }
    setErrors(next);
    if (Object.keys(next).length) return;

    busy.current = true;
    setSaving(true);
    setSaveError('');
    setMessage('');
    try {
      if (editingId) {
        // Preserve Dinesh's demo edit workflow. Never send its mock IDs/photos to Flask.
        const existing = projects.find(item => item.id === editingId);
        await updatePortfolioProject(editingId, {
          ...form, budget: Number(form.budget),
          styles: form.styles.split(',').map(item => item.trim()).filter(Boolean),
          photos: files.length ? Array.from(files).map((_, index) => ['/project-living.svg', '/project-kitchen.svg', '/project-bedroom.svg'][index % 3]) : existing?.photos,
        });
        setMessage('Demo project updated. No Flask project was changed.');
      } else {
        const project = await createReal.current(form);
        if (!project) return;
        setMessage('Project created in Flask as a draft. No photos were uploaded.');
        setRefreshToken(value => value + 1);
      }
      setEditingId(null);
      setForm(blank);
      setFiles([]);
      formElement.reset();
    } catch (error) {
      setSaveError(error.status === 401 ? 'Please log in again with an active designer account.'
        : error.status === 403 ? 'An InteriorDesigner account is required.'
          : !editingId && error.status !== 400 ? `${error.message} Check My portfolio before retrying; creation could not be confirmed.` : error.message);
    } finally {
      busy.current = false;
      setSaving(false);
    }
  }

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Selected IDP features" title="Create and manage portfolio" text="Create an IDP with details, assign category/style tags, upload multiple photos, then edit or remove projects." />
      <form className="panel form-card" onSubmit={submit} noValidate>
        <p className="muted">Create saves a real Flask draft without photos. Demo only: Edit/Update/Remove below change prototype records, not Flask projects.</p>
        {optionsLoading && !editingId && <p role="status">Loading active categories...</p>}
        {optionsError && !editingId && <div className="alert error-alert" role="alert">Could not load categories: {optionsError}
          <button className="secondary-button compact" type="button" onClick={() => setOptionsRetry(value => value + 1)}>Retry categories</button>
        </div>}
        <fieldset disabled={saving} style={{ border: 0, margin: 0, padding: 0, minWidth: 0 }}>
        <div className="section-heading compact-heading"><div><h2>{editingId ? 'Edit portfolio project' : 'Create portfolio project'}</h2></div>{editingId && <button type="button" className="text-button" onClick={() => { setEditingId(null); setForm(blank); }}>Cancel edit</button>}</div>
        <div className="two-column-form">
          <label>Project title<input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /><FieldError message={errors.title} /></label>
          <label>Property type<select value={form.propertyType} onChange={(e) => setForm({...form, propertyType: e.target.value})}><option value="">Choose property type</option>{(editingId ? PROPERTY_TYPES : options.property_types).map((type) => (<option key={type} value={type}>{type}</option>))}</select><FieldError message={errors.propertyType} /></label>
          <label>Location<input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} /><FieldError message={errors.location} /></label>
          <label>Budget (SGD)<input type="number" min="1" value={form.budget} onChange={(e) => setForm({ ...form, budget: e.target.value })} /><FieldError message={errors.budget} /></label>
          <label>Completion date<input type="date" value={form.completionDate} onChange={(e) => setForm({ ...form, completionDate: e.target.value })} /><FieldError message={errors.completionDate} /></label>
          <label>Category<select disabled={!editingId && (optionsLoading || !!optionsError)} value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}><option value="">Choose category</option>{(editingId ? categories : options.categories).map((item) => <option key={item}>{item}</option>)}</select><FieldError message={errors.category} /></label>
        </div>
        <label>Description<textarea rows="4" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /><FieldError message={errors.description} /></label>
        <label>Style tags (comma-separated)<input value={form.styles} onChange={(e) => setForm({ ...form, styles: e.target.value })} placeholder="Minimalist, Scandinavian" /><FieldError message={errors.styles} /></label>
        <label>Project photos<input type="file" accept="image/*" multiple disabled={!editingId} onChange={(e) => setFiles(e.target.files)} /><FieldError message={errors.photos} /><small>{editingId ? 'Demo only: selected photos use mock preview paths.' : 'Photo uploads are not connected yet. You can create a project without photos.'}</small></label>
        <button className="primary-button" type="submit" disabled={saving || (!editingId && (optionsLoading || !!optionsError))}>{saving ? 'Saving...' : editingId ? 'Update project' : 'Create project'}</button>
        </fieldset>
        {saveError && <div className="alert error-alert" role="alert">{saveError}</div>}
        {message && <div className="alert success-alert" role="status">{message}</div>}
      </form>
      <div className="section-heading roomy"><div><h2>My portfolio</h2><p className="muted">Each card shows the view counter required by the selected user story.</p></div></div>
      <ApiMyPortfolio key={user?.id} refreshToken={refreshToken} />
      <div className="section-heading roomy"><div><h2>Demo projects</h2><p className="muted">Demo only: Edit and Remove affect mock records. They do not update the real portfolio above.</p></div></div>
      <div className="card-grid">{mine.map((project) => <ProjectCard key={project.id} project={project} editable onEdit={edit} onDelete={deletePortfolioProject} />)}</div>
    </div>
  );
}
