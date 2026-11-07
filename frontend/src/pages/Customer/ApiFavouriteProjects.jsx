import { useEffect, useRef, useState } from 'react';
import ProjectCard from '../../components/ProjectCard';
import { flaskApi } from '../../services/api';
import { pageRequest } from '../../utils/projects';
import { emptyFavouriteList, favouriteList } from '../../utils/favouriteProjects';

export default function ApiFavouriteProjects({ openApiProject }) {
  const [state, setState] = useState(emptyFavouriteList);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [retry, setRetry] = useState(0);
  const [categories, setCategories] = useState([]);
  const [optionsLoading, setOptionsLoading] = useState(true);
  const [optionsError, setOptionsError] = useState('');
  const [optionsRetry, setOptionsRetry] = useState(0);
  const list = useRef(null);

  useEffect(() => {
    const current = favouriteList(setState);
    list.current = current;
    return () => current.dispose();
  }, []);

  useEffect(() => {
    const current = list.current;
    current.prepareLoad();
    const timer = setTimeout(() => current.load(search, category), 250);
    return () => { clearTimeout(timer); current.cancelLoad(); };
  }, [search, category, retry]);

  useEffect(() => {
    setOptionsLoading(true);
    setOptionsError('');
    return pageRequest(() => flaskApi.getProjectOptions(), {
      success: response => setCategories(response.data.categories),
      failure: error => setOptionsError(error.message),
      settled: () => setOptionsLoading(false),
    });
  }, [optionsRetry]);

  const clear = () => { setSearch(''); setCategory(''); setRetry(value => value + 1); };
  return <section aria-label="Saved Flask projects">
    <div className="section-heading roomy"><div><h2>Favourite projects</h2>
      <p className="muted">{state.loading ? 'Loading favourite projects...' : state.error ? 'Projects unavailable' : `${state.total} saved project(s)`}</p>
    </div></div>
    <div className="panel filters-grid">
      <label>Search favourite projects<input value={search} onChange={event => setSearch(event.target.value)} placeholder="Search saved projects..." /></label>
      <label>Category<select value={category} disabled={optionsLoading || !!optionsError} onChange={event => setCategory(event.target.value)}>
        <option value="">All categories</option>
        {categories.map(name => <option key={name} value={name}>{name}</option>)}
      </select></label>
      <button className="secondary-button compact" onClick={clear}>Clear Filters</button>
    </div>
    {optionsLoading && <p role="status">Loading categories...</p>}
    {optionsError && <div className="alert error-alert" role="alert">Could not load categories: {optionsError}
      <button className="secondary-button compact" onClick={() => setOptionsRetry(value => value + 1)}>Retry categories</button>
    </div>}
    <FavouriteProjectsResults state={state} filtered={!!(search.trim() || category)} openApiProject={openApiProject}
      onRemove={id => list.current.remove(id)} onRetry={() => setRetry(value => value + 1)} onClear={clear} />
  </section>;
}

export function FavouriteProjectsResults({ state, filtered, openApiProject, onRemove, onRetry, onClear }) {
  if (state.loading) return <div className="panel form-card" role="status">Loading favourite projects...</div>;
  if (state.error) return <div className="panel form-card alert error-alert" role="alert"><p>{state.error}</p>
    <button className="secondary-button" onClick={onRetry}>Retry projects</button></div>;
  if (!state.items.length) return <div className="empty-state panel">
    <h3>{filtered ? 'No matching saved projects' : 'No saved projects'}</h3>
    <p>{filtered ? 'Try another search or category.' : 'Save projects from their project details page to see them here.'}</p>
    {filtered && <button className="secondary-button" onClick={onClear}>Clear Filters</button>}
  </div>;
  return <div className="card-grid">{state.items.map(project => <div key={`api-favourite-${project.id}`}>
    <ProjectCard project={project} onView={openApiProject} showSave={false} />
    <button className="secondary-button" disabled={state.pending.includes(project.id)} onClick={() => onRemove(project.id)}>
      {state.pending.includes(project.id) ? 'Removing...' : 'Remove from Favourites'}
    </button>
    {state.removalErrors[project.id] && <p className="alert error-alert" role="alert">{state.removalErrors[project.id]}</p>}
  </div>)}</div>;
}
