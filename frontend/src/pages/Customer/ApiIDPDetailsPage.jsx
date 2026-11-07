import { useEffect, useState } from 'react';
import { flaskApi } from '../../services/api';
import { pageRequest, projectDetailsData, projectDetailsError } from '../../utils/projects';

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

// Real API records never read from, write to, or fall back to AppContext mocks.
export default function ApiIDPDetailsPage({ projectId, onBack }) {
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
        setResult({ requestedId: projectId, project });
      },
      failure: setError,
      settled: () => setLoading(false),
    });
  }, [projectId, retry]);

  const back = <button className="text-button" onClick={onBack}>Back to Browse</button>;
  if (loading || (!error && result?.requestedId !== projectId)) {
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
  return <ApiProjectContent project={project} onBack={onBack} />;
}

export function ApiProjectContent({ project, onBack }) {
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
      </>}
    </section>
  </div>;
}
