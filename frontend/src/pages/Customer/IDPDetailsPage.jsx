import { useEffect } from 'react';
import { useApp } from '../../context/AppContext';

export default function IDPDetailsPage({ projectId, go, openDesigner }) {
  const { user, projects, designers, favouriteProjectIds, toggleFavouriteProject, incrementProjectView } = useApp();
  const project = projects.find((item) => item.id === projectId);
  const designer = project ? designers.find((item) => item.id === project.designerId) : null;

  useEffect(() => {
    if (projectId) incrementProjectView(projectId);
    // Intentionally only runs when a different project is opened.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  if (!project) return <div className="page-shell"><div className="empty-state panel"><h2>Project not found</h2><button className="primary-button" onClick={() => go(user ? 'customer-designers' : 'landing')}>Back to browse</button></div></div>;

  return (
    <div className="page-shell">
      <button className="text-button" onClick={() => go(user ? 'customer-designers' : 'landing')}>← Back to browsing</button>
      <div className="detail-layout">
        <div>
          <img className="detail-hero" src={project.photos[0]} alt="Project placeholder" />
          <div className="thumbnail-grid">{project.photos.map((photo, index) => <img key={`${photo}-${index}`} src={photo} alt={`Project placeholder ${index + 1}`} />)}</div>
        </div>
        <aside className="panel detail-panel">
          <span className="eyebrow">{project.category}</span>
          <h1>{project.title}</h1>
          <button className="designer-link" onClick={() => openDesigner(designer.id)}>{designer?.companyName}</button>
          <p>{project.description}</p>
          <dl className="detail-list">
            <div><dt>Budget</dt><dd>${Number(project.budget).toLocaleString()}</dd></div>
            <div><dt>Property</dt><dd>{project.propertyType}</dd></div>
            <div><dt>Location</dt><dd>{project.location}</dd></div>
            <div><dt>Completion</dt><dd>{project.completionDate}</dd></div>
            <div><dt>Views</dt><dd>{project.views}</dd></div>
          </dl>
          <div className="tag-row">{project.styles.map((style) => <span className="tag" key={style}>{style}</span>)}</div>
          {user?.role === 'customer' ? <button className="primary-button full-width" onClick={() => toggleFavouriteProject(project.id)}>{favouriteProjectIds.includes(project.id) ? 'Remove from favourites' : 'Save project to favourites'}</button> : <button className="primary-button full-width" onClick={() => go('login')}>Log in to save this project</button>}
        </aside>
      </div>
    </div>
  );
}
