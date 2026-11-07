import { useEffect, useState } from 'react';
import PageHeader from '../../components/PageHeader';
import ProjectCard from '../../components/ProjectCard';
import { flaskApi } from '../../services/api';
import { projectCardData, projectQuery, pageRequest } from '../../utils/projects';

const emptyFilters = {
  category: '',
  style: '',
  budget: '',
  propertyType: '',
  location: '',
  sort: 'newest'
};

export default function IDPsPage() {
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState(emptyFilters);
  const [page, setPage] = useState(1);
  const [result, setResult] = useState({ items: [], total: 0, page: 1, per_page: 24, pages: 1 });
  const [options, setOptions] = useState({ categories: [], styles: [], property_types: [], locations: [], sort_options: {} });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [optionsLoading, setOptionsLoading] = useState(true);
  const [optionsError, setOptionsError] = useState('');
  const [retry, setRetry] = useState(0);
  const [optionsRetry, setOptionsRetry] = useState(0);

  useEffect(() => {
    setOptionsLoading(true);
    setOptionsError('');
    return pageRequest(() => flaskApi.getProjectOptions(), {
      success: response => setOptions(response.data),
      failure: error => setOptionsError(error.message),
      settled: () => setOptionsLoading(false),
    });
  }, [optionsRetry]);

  useEffect(() => {
    setLoading(true);
    setError('');
    let cancel = () => {};
    // Debounce typing/filter changes, and cancel the preceding request.
    const timer = setTimeout(() => {
      cancel = pageRequest(signal => flaskApi.getProjects(projectQuery(search, filters, page), { signal }), {
        success: response => setResult({ ...response.data, items: response.data.items.map(projectCardData) }),
        failure: error => setError(error.message),
        settled: () => setLoading(false),
      });
    }, 250);
    return () => { clearTimeout(timer); cancel(); };
  }, [search, filters, page, retry]);

  function updateFilter(field, value) {
    setLoading(true);
    setPage(1);
    setFilters(previous => ({ ...previous, [field]: value }));
  }

  function resetFilters() {
    setLoading(true);
    setSearch('');
    setFilters({ ...emptyFilters });
    setPage(1);
  }

  const { categories, styles, locations } = options;

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="Renovation inspiration"
        title="Browse Interior Design Projects"
        text="Explore renovation projects by room category, style, budget, property type or location."
      />

      {optionsLoading && <p role="status">Loading filter options...</p>}
      {optionsError && <div className="alert error-alert" role="alert">
        Could not load filter options: {optionsError}
        <button className="secondary-button compact" onClick={() => setOptionsRetry(value => value + 1)}>Retry filter options</button>
      </div>}
      <div className="panel filters-grid">
        <label className="span-2">
          Search IDPs
          <input
            value={search}
            onChange={(e) => { setLoading(true); setSearch(e.target.value); setPage(1); }}
            placeholder="Search renovation projects..."
          />
        </label>

        <label>
          Category
          <select
            disabled={optionsLoading || !!optionsError}
            value={filters.category}
            onChange={(e) =>
              updateFilter('category', e.target.value)
            }
          >
            <option value="">All categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </label>

        <label>
          Design style
          <select
            disabled={optionsLoading || !!optionsError}
            value={filters.style}
            onChange={(e) =>
              updateFilter('style', e.target.value)
            }
          >
            <option value="">All styles</option>
            {styles.map((style) => (
              <option key={style} value={style}>
                {style}
              </option>
            ))}
          </select>
        </label>

        <label>
          Maximum budget
          <select
            disabled={optionsLoading || !!optionsError}
            value={filters.budget}
            onChange={(e) =>
              updateFilter('budget', e.target.value)
            }
          >
            <option value="">Any budget</option>
            <option value="25000">$25,000</option>
            <option value="50000">$50,000</option>
            <option value="80000">$80,000</option>
            <option value="120000">$120,000</option>
            <option value="200000">$200,000</option>
          </select>
        </label>

        <label>
          Property type
          <select
            disabled={optionsLoading || !!optionsError}
            value={filters.propertyType}
            onChange={(e) =>
              updateFilter('propertyType', e.target.value)
            }
          >
            <option value="">All property types</option>
            {options.property_types.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>

        <label>
          Location
          <select
            disabled={optionsLoading || !!optionsError}
            value={filters.location}
            onChange={(e) =>
              updateFilter('location', e.target.value)
            }
          >
            <option value="">All locations</option>
            {locations.map((location) => (
              <option key={location} value={location}>
                {location}
              </option>
            ))}
          </select>
        </label>
        <label>Sort by
          <select value={filters.sort} disabled={optionsLoading || !!optionsError} onChange={e => updateFilter('sort', e.target.value)}>
            {Object.entries(options.sort_options).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
          </select>
        </label>
      </div>

      <div className="section-heading roomy">
        <div>
          <h2>Renovation Projects</h2>
          <p className="muted">
            {loading ? 'Loading projects...' : error ? 'Projects unavailable' : `${result.total} project(s) found`}
          </p>
        </div>

        <button
          className="secondary-button compact"
          onClick={resetFilters}
        >
          Clear filters
        </button>
      </div>

      {loading ? <div className="panel form-card" role="status">Loading projects...</div> : error ? (
        <div className="panel form-card alert error-alert" role="alert">
          <p>Could not load projects: {error}</p>
          <button className="secondary-button" onClick={() => { setLoading(true); setRetry(value => value + 1); }}>Retry projects</button>
        </div>
      ) : result.items.length === 0 ? (
        <div className="panel form-card">
          <p>No projects match your selected filters.</p>
          <button
            className="secondary-button"
            onClick={resetFilters}
          >
            Reset filters
          </button>
        </div>
      ) : (
        <div className="card-grid">
          {result.items.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              showSave={false}
            />
          ))}
        </div>
      )}
      {!loading && !error && result.total > 0 && <nav className="section-heading roomy" aria-label="Project pagination">
        <button className="secondary-button" disabled={result.page <= 1} onClick={() => { setLoading(true); setPage(result.page - 1); }}>Previous</button>
        <span>Page {result.page} of {result.pages} / {result.per_page} per page</span>
        <button className="secondary-button" disabled={result.page >= result.pages} onClick={() => { setLoading(true); setPage(result.page + 1); }}>Next</button>
      </nav>}
    </div>
  );
}
