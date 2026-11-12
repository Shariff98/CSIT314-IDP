import { useEffect, useState } from 'react';
import DesignerCard from '../../components/DesignerCard';
import PageHeader from '../../components/PageHeader';
import { flaskApi } from '../../services/api';
import { pageRequest } from '../../utils/projects';

// Browse design companies (GET /api/designers). Projects have their own single search on
// Browse projects, so this page only searches companies.
const emptyFilters = { specialisation: '', service_area: '', max_budget: '' };

export default function DesignersPage({ openDesigner }) {
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState(emptyFilters);
  const [result, setResult] = useState({ items: [], total: 0, options: { specialisations: [], service_areas: [] } });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    setLoading(true);
    setError('');
    let cancel = () => {};
    const timer = setTimeout(() => {
      cancel = pageRequest(signal => flaskApi.getDesigners({ q: search.trim(), ...filters }, { signal }), {
        success: response => setResult(response.data),
        failure: failure => setError(failure.message),
        settled: () => setLoading(false),
      });
    }, 250);
    return () => { clearTimeout(timer); cancel(); };
  }, [search, filters, retry]);

  const update = (field, value) => setFilters(previous => ({ ...previous, [field]: value }));
  const reset = () => { setSearch(''); setFilters(emptyFilters); };
  const { specialisations, service_areas: areas } = result.options;

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Discovery" title="Browse interior designers"
        text="Search design companies by name, style, service area or budget, then open a company to see all its projects." />
      <div className="panel filters-grid">
        <label className="span-2">Search companies<input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="e.g. Tan & Alex" /></label>
        <label>Style speciality<select value={filters.specialisation} onChange={(e) => update('specialisation', e.target.value)}>
          <option value="">All styles</option>{specialisations.map((item) => <option key={item}>{item}</option>)}
        </select></label>
        <label>Service area<select value={filters.service_area} onChange={(e) => update('service_area', e.target.value)}>
          <option value="">All areas</option>{areas.map((item) => <option key={item}>{item}</option>)}
        </select></label>
        <label>My budget<select value={filters.max_budget} onChange={(e) => update('max_budget', e.target.value)}>
          <option value="">Any</option>
          {[20000, 30000, 50000, 80000].map((value) => <option key={value} value={value}>${value.toLocaleString()}</option>)}
        </select></label>
        <button className="secondary-button compact" onClick={reset}>Clear filters</button>
      </div>
      <p className="result-count">{loading ? 'Loading designers...' : error ? 'Designers unavailable' : `${result.total} designer(s) found`}</p>
      {error ? <div className="panel form-card alert error-alert" role="alert"><p>Could not load designers: {error}</p>
        <button className="secondary-button" onClick={() => setRetry(value => value + 1)}>Retry</button></div>
        : !loading && result.items.length === 0 ? <div className="empty-state panel"><h3>No designers match</h3>
          <p className="muted">Try another style, area or budget.</p></div>
          : <div className="card-grid">{result.items.map((designer) => <DesignerCard key={designer.id} designer={designer} onView={openDesigner} />)}</div>}
    </div>
  );
}
