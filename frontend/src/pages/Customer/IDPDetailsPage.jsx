import { useEffect, useState } from 'react';
import { useApp } from '../../context/AppContext';

export default function IDPDetailsPage({ projectId, go, openDesigner }) {
  const {
    user,
    projects,
    designers,
    categories,
    favouriteProjectIds,
    toggleFavouriteProject,
    incrementProjectView,
    updatePortfolioProject
  } = useApp();
  const project = projects.find((item) => item.id === projectId);
  const designer = project ? designers.find((item) => item.id === project.designerId) : null;
  const isOwner =
    user?.role === 'designer' &&
    user.designerId === project?.designerId;
  const [editingTags, setEditingTags] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(project?.category || '');
  const [styleTags, setStyleTags] = useState(project?.styles?.join(', ') || '');
  const [editError, setEditError] = useState('');
  const [saving, setSaving] = useState(false);

  // Reset editing fields when a different IDP is opened.
  useEffect(() => {
    setEditingTags(false);
    setSelectedCategory(project?.category || '');
    setStyleTags(project?.styles?.join(', ') || '');
    setEditError('');
  }, [projectId]);

  async function saveTags(event) {
    event.preventDefault();

    if (!isOwner) return;

    const styles = [...new Set(
      styleTags
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean)
    )];

    if (!selectedCategory || styles.length === 0) {
      setEditError('Select a category and enter at least one style tag.');
      return;
    }

    setSaving(true);
    setEditError('');

    try {
      // === BACKEND INTEGRATION ===
      // Python must verify the designer owns this IDP.
      // Update only its category and style tags.
      await updatePortfolioProject(project.id, {
        category: selectedCategory,
        styles
      });

      setEditingTags(false);
    } catch (error) {
      setEditError(error.message || 'Failed to update project.');
    } finally {
      setSaving(false);
    }
  }

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
          {isOwner ? (
            <div>
              {editingTags ? (
                <form
                  onSubmit={saveTags}
                  style={{ display: 'grid', gap: '12px' }}
                >
                  <label>
                    Project category
                    <select
                      value={selectedCategory}
                      onChange={(e) => setSelectedCategory(e.target.value)}
                    >
                      <option value="">Select category</option>
                      {categories.map((category) => (
                        <option key={category} value={category}>
                          {category}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label>
                    Style tags (comma-separated)
                    <input
                      value={styleTags}
                      onChange={(e) => setStyleTags(e.target.value)}
                      placeholder="Modern, Minimalist, Scandinavian"
                    />
                  </label>

                  {editError && (
                    <p role="alert" style={{ color: '#b42318' }}>
                      {editError}
                    </p>
                  )}

                  <button
                    type="submit"
                    className="primary-button full-width"
                    disabled={saving}
                  >
                    {saving ? 'Saving...' : 'Save category and tags'}
                  </button>

                  <button
                    type="button"
                    className="secondary-button full-width"
                    onClick={() => setEditingTags(false)}
                  >
                    Cancel
                  </button>
                </form>
              ) : (
                <button
                  className="primary-button full-width"
                  onClick={() => {
                    setSelectedCategory(project.category);
                    setStyleTags(project.styles.join(', '));
                    setEditError('');
                    setEditingTags(true);
                  }}
                >
                  Edit category / style tags
                </button>
              )}

              <button
                className="secondary-button full-width"
                style={{ marginTop: '12px' }}
                onClick={() => go('designer-portfolio')}
              >
                Manage full IDP details
              </button>
            </div>
          ) : user?.role === 'customer' ? (
            <button
              className="primary-button full-width"
              onClick={() => toggleFavouriteProject(project.id)}
            >
              {favouriteProjectIds.includes(project.id)
                ? 'Remove from favourites'
                : 'Save project to favourites'}
            </button>
          ) : !user ? (
            <button
              className="primary-button full-width"
              onClick={() => go('login')}
            >
              Log in to save this project
            </button>
          ) : null}
        </aside>
      </div>
    </div>
  );
}
