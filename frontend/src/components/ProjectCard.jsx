import { useApp } from '../context/AppContext';

export default function ProjectCard({ project, onView, editable = false, onEdit, onDelete, showSave = true }) {
  const { designers, favouriteProjectIds, toggleFavouriteProject } = useApp();
  const designer = designers.find((item) => item.id === project.designerId);
  const companyName = Object.hasOwn(project, 'companyName') ? project.companyName : designer?.companyName;
  const saved = favouriteProjectIds.includes(project.id);

  return (
    <article className="card project-card">
      <img className="card-image" src={project.photos?.[0] || '/project-living.svg'} alt={`${project.title} placeholder`} />
      <div className="card-body">
        <div className="card-kicker">{project.category} · {project.propertyType}</div>
        <h3>{project.title}</h3>
        {companyName && <p className="muted">by {companyName}</p>}
        <div className="tag-row">{project.styles.map((style) => <span className="tag" key={style}>{style}</span>)}</div>
        <p className="line-clamp">{project.description}</p>
        <div className="project-meta">
          <span>${Number(project.budget).toLocaleString()}</span>
          <span>👁 {project.views}</span>
        </div>
        <div className="card-actions">
          {onView && <button className="primary-button" onClick={() => onView(project.id)}>View details</button>}
          {!editable && showSave && <button className="secondary-button" onClick={() => toggleFavouriteProject(project.id)}>{saved ? 'Saved' : 'Save'}</button>}
          {editable && <button className="secondary-button" onClick={() => onEdit(project)}>Edit</button>}
          {editable && <button className="danger-button" onClick={() => onDelete(project.id)}>Remove</button>}
        </div>
      </div>
    </article>
  );
}
