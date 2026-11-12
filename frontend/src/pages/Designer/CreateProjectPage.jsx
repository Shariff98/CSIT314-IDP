import { useEffect, useRef, useState } from 'react';
import FieldError from '../../components/FieldError';
import PageHeader from '../../components/PageHeader';
import { flaskApi } from '../../services/api';
import { isRequired } from '../../utils/validation';
import { pageRequest } from '../../utils/projects';
import { createPortfolioMutation, portfolioOptionalFieldErrors } from '../../utils/createPortfolio';

export const blankProject = { title: '', description: '', propertyType: '', location: '', budget: '', completionDate: '', category: '', styles: '' };

// Checks the browser can do before asking Flask (Flask checks everything again).
export function projectFormErrors(form) {
  const errors = {};
  if (!isRequired(form.title)) errors.title = 'Title is required.';
  if (!isRequired(form.description)) errors.description = 'Description is required.';
  if (!isRequired(form.category)) errors.category = 'Choose a category.';
  const budget = Number(form.budget);
  if (!Number.isSafeInteger(budget) || budget < 1) errors.budget = 'Budget must be a positive whole number.';
  return { ...errors, ...portfolioOptionalFieldErrors(form, false) };
}

// The fields shared by Create (US-54) and Edit (US-04).
export function ProjectFields({ form, setForm, errors, options, withStyles = true }) {
  const set = (field) => (event) => setForm({ ...form, [field]: event.target.value });
  return <>
    <div className="two-column-form">
      <label>Project title<input value={form.title} onChange={set('title')} /><FieldError message={errors.title} /></label>
      <label>Category<select value={form.category} onChange={set('category')}><option value="">Choose category</option>
        {options.categories.map((item) => <option key={item}>{item}</option>)}</select><FieldError message={errors.category} /></label>
      <label>Budget (SGD)<input type="number" min="1" step="1" value={form.budget} onChange={set('budget')} /><FieldError message={errors.budget} /></label>
      <label>Property type<select value={form.propertyType} onChange={set('propertyType')}><option value="">Not specified</option>
        {options.property_types.map((item) => <option key={item}>{item}</option>)}</select></label>
      <label>Location<input value={form.location} onChange={set('location')} placeholder="e.g. Tampines" /></label>
      <label>Completion date<input type="date" value={form.completionDate || ''} onChange={set('completionDate')} /></label>
    </div>
    <label>Description<textarea rows="4" value={form.description} onChange={set('description')} /><FieldError message={errors.description} /></label>
    {withStyles && <label>Style tags (comma-separated, up to 5)<input value={form.styles} onChange={set('styles')} placeholder="Minimalist, Scandinavian" /></label>}
  </>;
}

export function useProjectOptions() {
  const [options, setOptions] = useState({ categories: [], property_types: [] });
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    setError('');
    return pageRequest(() => flaskApi.getProjectOptions(), {
      success: response => setOptions(response.data),
      failure: failure => setError(failure.message),
    });
  }, [retry]);
  return { options, error, retry: () => setRetry(value => value + 1) };
}

// US-54 Create IDP. It is saved as a draft; photos and publishing are on the next page.
export default function CreateProjectPage({ go }) {
  const [form, setForm] = useState(blankProject);
  const [errors, setErrors] = useState({});
  const [saveError, setSaveError] = useState('');
  const [saving, setSaving] = useState(false);
  const create = useRef(null);
  if (!create.current) create.current = createPortfolioMutation();
  const { options, error: optionsError, retry } = useProjectOptions();

  async function submit(event) {
    event.preventDefault();
    const next = projectFormErrors(form);
    setErrors(next);
    if (Object.keys(next).length) return;
    setSaving(true);
    setSaveError('');
    try {
      const project = await create.current(form);
      if (project) go('portfolio-item', { id: project.id });
    } catch (error) {
      setSaveError(error.status === 401 ? 'Please log in again with an active designer account.' : error.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Portfolio" title="New project" text="Save the details as a draft. On the next page you can add photos and publish it." />
      <form className="panel form-card" onSubmit={submit} noValidate>
        {optionsError && <div className="alert error-alert" role="alert">Could not load categories: {optionsError}
          <button className="secondary-button compact" type="button" onClick={retry}>Retry</button></div>}
        <fieldset disabled={saving} style={{ border: 0, margin: 0, padding: 0, minWidth: 0 }}>
          <ProjectFields form={form} setForm={setForm} errors={errors} options={options} />
          <div className="button-row">
            <button className="primary-button" type="submit">{saving ? 'Saving...' : 'Save draft and add photos'}</button>
            <button className="text-button" type="button" onClick={() => go('portfolio')}>Cancel</button>
          </div>
        </fieldset>
        {saveError && <div className="alert error-alert" role="alert">{saveError}</div>}
      </form>
    </div>
  );
}
