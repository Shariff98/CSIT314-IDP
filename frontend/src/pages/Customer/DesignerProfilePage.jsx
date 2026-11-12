import { useEffect, useState } from 'react';
import ProjectCard from '../../components/ProjectCard';
import { useApp } from '../../context/AppContext';
import { flaskApi } from '../../services/api';
import { pageRequest, projectCardData } from '../../utils/projects';

const money = (value) => `$${Number(value).toLocaleString()}`;

function Field({ label, value }) {
  if (value === undefined || value === null || value === '' || (Array.isArray(value) && !value.length)) return null;
  return <div><dt>{label}</dt><dd>{Array.isArray(value) ? value.join(', ') : value}</dd></div>;
}

// US-53 View interior designer company page (and US-15, the designer previewing their own page).
export default function DesignerProfilePage({ designerId, openProject, go }) {
  const { user } = useApp();
  const [page, setPage] = useState(null);
  const [error, setError] = useState(null);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    setPage(null);
    setError(null);
    return pageRequest(signal => flaskApi.getDesigner(designerId, { signal }), {
      success: response => setPage(response.data),
      failure: setError,
    });
  }, [designerId, retry]);

  const back = <button className="text-button" onClick={() => go('designers')}>Back to designers</button>;
  if (error) {
    return <div className="page-shell">{back}<div className="panel form-card" role="alert">
      <h2>{error.status === 404 ? 'Company page unavailable' : 'Could not load this company'}</h2>
      <p>{error.status === 404 ? 'This designer has no public company page.' : error.message}</p>
      {error.status !== 404 && <button className="secondary-button" onClick={() => setRetry(value => value + 1)}>Retry</button>}
    </div></div>;
  }
  if (!page) return <div className="page-shell">{back}<div className="panel form-card" role="status">Loading company page...</div></div>;

  const { company, team, projects } = page;
  const ownPage = user?.id === designerId;
  const cards = projects.map(projectCardData);
  return (
    <div className="page-shell">
      {back}
      {ownPage && <div className="alert warning-alert">This is how customers see your company page.</div>}
      <section className="panel company-hero">
        <img src={company.cover_url || company.logo_url || cards[0]?.photos[0] || '/floor-plan.svg'} alt="" />
        <div>
          <span className="eyebrow">{company.service_areas.join(' · ') || 'Interior design company'}</span>
          <h1>{company.name}</h1>
          <p>{company.description}</p>
          <div className="tag-row">{company.specialisations.map((item) => <span className="tag" key={item}>{item}</span>)}</div>
          <div className="company-meta">
            {company.budget_min && company.budget_max && <span>Budget {money(company.budget_min)} – {money(company.budget_max)}</span>}
            {company.years_experience > 0 && <span>{company.years_experience} years' experience</span>}
            <span>{cards.length} published project(s)</span>
          </div>
        </div>
      </section>

      <div className="two-panel-grid section-block">
        <section className="panel form-card" aria-label="Contact and services">
          <h2>Contact and services</h2>
          <dl className="detail-list">
            <Field label="Email" value={company.email} />
            <Field label="Phone" value={company.phone} />
            <Field label="Address" value={company.address} />
            <Field label="Registration number" value={company.registration_no} />
            <Field label="Services" value={company.services} />
            <Field label="Certifications" value={company.certifications} />
            <Field label="Awards" value={company.awards} />
          </dl>
        </section>
        <section className="panel form-card" aria-label="Team">
          <h2>Team</h2>
          {team.length ? <ul className="team-list">{team.map((member) => <li key={member.id}><strong>{member.name}</strong><span className="muted">{member.position}</span></li>)}</ul>
            : <p className="muted">No team members listed yet.</p>}
        </section>
      </div>

      <div className="section-heading"><div><span className="eyebrow">Portfolio</span><h2>Projects by {company.name}</h2></div></div>
      {cards.length ? <div className="card-grid">{cards.map((project) => <ProjectCard key={project.id} project={project} onView={openProject} />)}</div>
        : <div className="empty-state panel"><h3>No published projects yet</h3></div>}
    </div>
  );
}
