import { useEffect, useState } from 'react';
import PageHeader from '../../components/PageHeader';
import { useApp } from '../../context/AppContext';
import { flaskApi } from '../../services/api';
import { pageRequest } from '../../utils/projects';
import ApiMyPortfolio from './ApiMyPortfolio';

const emptyFilters = { q: '', status: '', category: '', date_from: '', date_to: '' };

// My projects: US-16 list and US-03 search/filter. Each card opens the Manage project page.
export default function PortfolioPage({ go }) {
  const { user } = useApp();
  const [filters, setFilters] = useState(emptyFilters);
  const [categories, setCategories] = useState([]);

  useEffect(() => pageRequest(() => flaskApi.getProjectOptions(), {
    success: response => setCategories(response.data.categories),
    failure: () => setCategories([]),
  }), []);

  const update = (field, value) => setFilters(previous => ({ ...previous, [field]: value }));
  return (
    <div className="page-shell">
      <PageHeader eyebrow="Portfolio" title="My projects"
        text="All your projects, drafts included. Open one to edit it, add photos, tag it or publish it."
        actions={<button className="primary-button" onClick={() => go('portfolio-new')}>New project</button>} />
      <div className="panel filters-grid">
        <label className="span-2">Search my projects<input value={filters.q} onChange={(e) => update('q', e.target.value)} placeholder="Title, description or style" /></label>
        <label>Status<select value={filters.status} onChange={(e) => update('status', e.target.value)}>
          <option value="">All</option>{['Published', 'Draft', 'Current', 'Past'].map((item) => <option key={item}>{item}</option>)}
        </select></label>
        <label>Category<select value={filters.category} onChange={(e) => update('category', e.target.value)}>
          <option value="">All categories</option>{categories.map((item) => <option key={item}>{item}</option>)}
        </select></label>
        <label>Created from<input type="date" value={filters.date_from} onChange={(e) => update('date_from', e.target.value)} /></label>
        <label>Created to<input type="date" value={filters.date_to} onChange={(e) => update('date_to', e.target.value)} /></label>
        <button className="secondary-button compact" onClick={() => setFilters(emptyFilters)}>Clear filters</button>
      </div>
      <ApiMyPortfolio key={user?.id} filters={filters} onManage={(id) => go('portfolio-item', { id })} />
    </div>
  );
}
