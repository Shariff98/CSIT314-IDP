import { useEffect, useRef, useState } from 'react';
import { useApp } from '../../context/AppContext';
import { flaskApi } from '../../services/api';
import { pageRequest, projectCardData, projectDetailsData, projectDetailsError } from '../../utils/projects';
import ProjectCard from '../../components/ProjectCard';
import { canSaveProject, favouriteMutation, favouriteError } from '../../utils/favourites';

const placeholder = '/project-living.svg';
const money = value => Number(value).toLocaleString('en-SG');

function Photo({ src, alt, ...props }) {
  return <img {...props} src={src || placeholder} alt={alt} onError={event => {
    event.currentTarget.onerror = null;
    if (event.currentTarget.getAttribute('src') !== placeholder) event.currentTarget.src = placeholder;
  }} />;
}

function Field({ label, value }) {
  return value !== undefined && value !== null && value !== ''
    ? <div><dt>{label}</dt><dd>{Array.isArray(value) ? value.join(', ') : value}</dd></div> : null;
}

// Only authentication is read from context. Project/favourite data stays local.
export default function ApiIDPDetailsPage({ projectId, onBack, onOpenProject, onOpenDesigner }) {
  const { user } = useApp();
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    setLoading(true);
    setResult(null);
    setError(null);
    return pageRequest(signal => flaskApi.getProject(projectId, { signal }), {
      success: response => {
        const project = projectDetailsData(response.data.project);
        if (project.id !== Number(projectId)) throw new Error('Server returned a different project.');
        const others = (response.data.other_projects || []).map(projectCardData);
        setResult({ requestedId: projectId, customerId: user?.id, project, others, isSaved: response.data.is_saved === true });
      },
      failure: setError,
      settled: () => setLoading(false),
    });
  }, [projectId, retry, user?.id, user?.role]);

  const back = <button className="text-button" onClick={onBack}>Back to Browse</button>;
  if (loading || (!error && (result?.requestedId !== projectId || result?.customerId !== user?.id))) {
    return <div className="page-shell">{back}<div className="panel form-card" role="status">Loading project details...</div></div>;
  }
  if (error) {
    return <div className="page-shell">{back}<div className="panel form-card" role="alert">
      <h2>{error.status === 404 ? 'Project unavailable' : 'Unable to load project'}</h2>
      <p>{projectDetailsError(error)}</p>
      <button className="secondary-button" onClick={() => { setLoading(true); setRetry(value => value + 1); }}>Retry</button>
    </div></div>;
  }

  const { project } = result;
  const favouriteAction = canSaveProject(user)
    ? <FavouriteProjectButton key={`${user.id}:${project.id}:${result.isSaved}`} projectId={project.id} initialSaved={result.isSaved} />
    : !user ? <p className="muted">Log in as a homeowner to save this project to your favourites.</p> : null;
  return <ApiProjectContent project={project} onBack={onBack} favouriteAction={favouriteAction}
    otherProjects={result.others} onOpenProject={onOpenProject} onOpenDesigner={onOpenDesigner} />;
}

export function FavouriteProjectButton({ projectId, initialSaved }) {
  const [saved, setSaved] = useState(initialSaved);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const change = useRef(null);
  const busy = useRef(false);
  if (!change.current) change.current = favouriteMutation();
  const active = useRef(true);
  useEffect(() => { active.current = true; return () => { active.current = false; }; }, []);

  async function toggle() {
    if (busy.current) return;
    busy.current = true;
    setPending(true);
    setError('');
    try {
      const result = await change.current(projectId, !saved);
      if (active.current && result) setSaved(result.saved);
    } catch (error) {
      if (active.current) setError(favouriteError(error));
    } finally {
      busy.current = false;
      if (active.current) setPending(false);
    }
  }

  return <div>
    <button className="primary-button full-width" onClick={toggle} disabled={pending} aria-pressed={saved}>
      {pending ? 'Updating favourites...' : saved ? 'Remove from Favourites' : 'Save to Favourites'}
    </button>
    {error && <p className="alert error-alert" role="alert">{error}</p>}
  </div>;
}

export function ApiProjectContent({ project, onBack, favouriteAction = null, otherProjects = [], onOpenProject, onOpenDesigner }) {
  const company = project.company;
  return <div className="page-shell">
    <button className="text-button" onClick={onBack}>Back to Browse</button>
    <div className="detail-layout">
      <div>
        <Photo className="detail-hero" src={project.photos[0]} alt={project.photos.length ? project.title : 'Project photo unavailable'} />
        {!project.photos.length && <p className="muted">No project photos available.</p>}
        {project.photos.length > 1 && <div className="thumbnail-grid">
          {project.photos.map((photo, index) => <Photo key={`${photo}-${index}`} src={photo} alt={`${project.title}, photo ${index + 1}`} />)}
        </div>}
      </div>
      <aside className="panel detail-panel">
        <span className="eyebrow">{project.category || 'Uncategorised'}</span>
        <h1>{project.title || 'Untitled project'}</h1>
        <p>{project.description || 'No description available.'}</p>
        <dl className="detail-list">
          <Field label="Budget (SGD)" value={project.budget == null ? null : `$${money(project.budget)}`} />
          <Field label="Property" value={project.propertyType || 'Not specified'} />
          <Field label="Location" value={project.location || 'Not specified'} />
          <Field label="Completion" value={project.completionDate} />
          <Field label="Views" value={project.views ?? 0} />
        </dl>
        {project.styles.length ? <div className="tag-row">{project.styles.map((style, index) => <span className="tag" key={`${style}-${index}`}>{style}</span>)}</div> : <p className="muted">No design styles specified.</p>}
        {favouriteAction}
      </aside>
    </div>
    <section className="panel form-card section-block" aria-label="Company information">
      <h2>{company?.name || 'Company information unavailable'}</h2>
      {company && <>
        {company.cover_url && <Photo className="detail-hero" src={company.cover_url} alt={`${company.name || 'Company'} cover`} />}
        {company.logo_url && <Photo className="cover" src={company.logo_url} alt={`${company.name || 'Company'} logo`} />}
        {company.description && <p>{company.description}</p>}
        <dl className="detail-list">
          <Field label="Registration number" value={company.registration_no} />
          <Field label="Address" value={company.address} />
          <Field label="Phone" value={company.phone} />
          <Field label="Email" value={company.email} />
          <Field label="Years of experience" value={company.years_experience} />
          <Field label="Minimum budget (SGD)" value={company.budget_min == null ? null : `$${money(company.budget_min)}`} />
          <Field label="Maximum budget (SGD)" value={company.budget_max == null ? null : `$${money(company.budget_max)}`} />
          <Field label="Specialisations" value={company.specialisations?.length ? company.specialisations : null} />
          <Field label="Service areas" value={company.service_areas?.length ? company.service_areas : null} />
          <Field label="Services" value={company.services?.length ? company.services : null} />
          <Field label="Certifications" value={company.certifications} />
          <Field label="Awards" value={company.awards} />
        </dl>
        {onOpenDesigner && project.designerId && <button className="secondary-button" onClick={() => onOpenDesigner(project.designerId)}>
          View company page and all projects
        </button>}
      </>}
    </section>
    {otherProjects.length > 0 && <section className="section-block" aria-label="More from this designer">
      <div className="section-heading"><div><h2>More from this designer</h2></div></div>
      <div className="card-grid">{otherProjects.map(other => <ProjectCard key={other.id} project={other} onView={onOpenProject} />)}</div>
    </section>}
  </div>;
}
