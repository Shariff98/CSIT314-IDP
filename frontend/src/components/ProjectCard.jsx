// One project card. Saving to favourites happens on the project's details page, where the
// server confirms the change, so the card itself has no Save button.
const placeholder = '/project-living.svg';

export default function ProjectCard({ project, onView, viewLabel = 'View details', children }) {
  return (
    <article className="card project-card">
      <img className="card-image" src={project.photos?.[0] || placeholder} alt={project.photos?.[0] ? project.title : ''}
        onError={(event) => { event.currentTarget.onerror = null; event.currentTarget.src = placeholder; }} />
      <div className="card-body">
        <div className="card-kicker">{[project.category, project.propertyType].filter(Boolean).join(' · ')}</div>
        <h3>{project.title}</h3>
        {project.companyName && <p className="muted">by {project.companyName}</p>}
        <div className="tag-row">{(project.styles || []).map((style) => <span className="tag" key={style}>{style}</span>)}</div>
        <p className="line-clamp">{project.description}</p>
        <div className="project-meta">
          <span>${Number(project.budget || 0).toLocaleString()}</span>
          <span aria-label={`${project.views ?? 0} views`}>👁 {project.views ?? 0}</span>
        </div>
        {(onView || children) && <div className="card-actions">
          {onView && <button className="primary-button" onClick={() => onView(project.id)}>{viewLabel}</button>}
          {children}
        </div>}
      </div>
    </article>
  );
}
