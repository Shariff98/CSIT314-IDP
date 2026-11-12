import { useEffect, useState } from 'react';
import DesignerCard from '../../components/DesignerCard';
import ProjectCard from '../../components/ProjectCard';
import { useApp } from '../../context/AppContext';
import { flaskApi } from '../../services/api';
import { pageRequest, projectCardData } from '../../utils/projects';

// Home page for visitors and customers: the most viewed projects and the busiest companies,
// straight from the database.
export default function LandingPage({ go, openProject, openDesigner }) {
  const { user } = useApp();
  const [projects, setProjects] = useState(null);
  const [designers, setDesigners] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => pageRequest(signal => flaskApi.getProjects({ sort: 'views', per_page: 6 }, { signal }), {
    success: response => setProjects(response.data.items.map(projectCardData)),
    failure: failure => setError(failure.message),
  }), []);
  useEffect(() => pageRequest(signal => flaskApi.getDesigners({}, { signal }), {
    success: response => setDesigners(response.data.items.slice(0, 3)),
    failure: failure => setError(failure.message),
  }), []);

  const hero = projects?.find(project => project.photos.length)?.photos[0] || '/project-living.svg';
  return (
    <div>
      <section className="landing-hero">
        <div className="landing-copy">
          <span className="eyebrow">{user ? `Welcome back, ${user.name}` : 'Renovation discovery platform'}</span>
          <h1>Find an interior designer for your next home renovation.</h1>
          <p>Browse real renovation projects by room, style and budget, compare design companies,
            and save the projects you like. Not sure where to start? Ask the budget assistant.</p>
          <div className="hero-actions">
            <button className="primary-button" onClick={() => go('projects')}>Browse projects</button>
            <button className="secondary-button" onClick={() => go('designers')}>Find designers</button>
            {!user && <button className="text-button" onClick={() => go('register')}>Create homeowner account</button>}
          </div>
        </div>
        <div className="hero-visual panel">
          <img src={hero} alt="" onError={(event) => { event.currentTarget.onerror = null; event.currentTarget.src = '/project-living.svg'; }} />
        </div>
      </section>

      {error && <div className="page-shell"><div className="alert error-alert" role="alert">Some content could not load: {error}</div></div>}

      <section className="page-shell section-block">
        <div className="section-heading"><div><span className="eyebrow">Inspiration</span><h2>Most viewed projects</h2></div>
          <button className="secondary-button compact" onClick={() => go('projects')}>See all projects</button></div>
        {projects === null ? <p role="status">Loading projects...</p>
          : <div className="card-grid">{projects.map((project) => <ProjectCard key={project.id} project={project} onView={openProject} />)}</div>}
      </section>

      <section className="page-shell section-block">
        <div className="section-heading"><div><span className="eyebrow">Design companies</span><h2>Designers with the most projects</h2></div>
          <button className="secondary-button compact" onClick={() => go('designers')}>See all designers</button></div>
        {designers === null ? <p role="status">Loading designers...</p>
          : <div className="card-grid">{designers.map((designer) => <DesignerCard key={designer.id} designer={designer} onView={openDesigner} />)}</div>}
      </section>
    </div>
  );
}
