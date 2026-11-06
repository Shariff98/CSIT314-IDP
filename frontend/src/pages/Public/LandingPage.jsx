import DesignerCard from '../../components/DesignerCard';
import ProjectCard from '../../components/ProjectCard';
import { useApp } from '../../context/AppContext';

export default function LandingPage({ go, openDesigner, openProject }) {
  const { designers, projects } = useApp();
  const visibleDesigners = designers.filter((item) => item.verified && item.status === 'active').slice(0, 3);
  const visibleProjects = projects.filter((item) => item.published).slice(0, 3);

  return (
    <div>
      <section className="landing-hero">
        <div className="landing-copy">
          <span className="eyebrow">Renovation discovery platform</span>
          <h1>Find an interior designer for your next home renovation.</h1>
          <p>Browse verified design companies, compare portfolios and packages, then send your renovation requirements through one simple prototype platform.</p>
          <div className="hero-actions">
            <button className="primary-button" onClick={() => go('register')}>Create homeowner account</button>
            <button className="secondary-button" onClick={() => go('login')}>Log in</button>
          </div>
        </div>
        <div className="hero-visual panel">
          <img src="/project-living.svg" alt="Interior design placeholder" />
          <div className="floating-stat"><strong>4.8★</strong><span>Top company rating</span></div>
        </div>
      </section>

      <section className="page-shell section-block">
        <div className="section-heading"><div><span className="eyebrow">Design companies</span><h2>Browse verified interior designers</h2></div></div>
        <div className="card-grid">{visibleDesigners.map((designer) => <DesignerCard key={designer.id} designer={designer} onView={openDesigner} showSave={false} />)}</div>
      </section>

      <section className="page-shell section-block">
        <div className="section-heading"><div><span className="eyebrow">Inspiration</span><h2>Published renovation projects</h2></div></div>
        <div className="card-grid">{visibleProjects.map((project) => <ProjectCard key={project.id} project={project} onView={openProject} showSave={false} />)}</div>
      </section>
    </div>
  );
}
