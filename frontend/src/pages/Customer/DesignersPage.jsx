import { useMemo, useState } from 'react';
import DesignerCard from '../../components/DesignerCard';
import PageHeader from '../../components/PageHeader';
import ProjectCard from '../../components/ProjectCard';
import { useApp } from '../../context/AppContext';
import { PROPERTY_TYPES } from '../../data/options';

export default function DesignersPage({ openDesigner, openProject }) {
  const { designers, projects, packages, categories } = useApp();
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({propertyType: '', category: '', budget: '', style: '', location: '', rating: ''});
  const [projectSearch, setProjectSearch] = useState('');
  const [projectFilters, setProjectFilters] = useState({ category: '', style: '', budget: '', propertyType: '', location: '' });

  const approvedDesigners = useMemo(() => designers.filter((designer) => {
    if (!designer.verified || designer.status !== 'active') return false;
    const q = search.trim().toLowerCase();
    if (q && !`${designer.companyName} ${designer.description}`.toLowerCase().includes(q)) return false;
    if (filters.propertyType && !(designer.propertyTypes || []).includes(filters.propertyType)) return false;
    if (filters.category && !(designer.categoriesServed || []).includes(filters.category)) return false;
    if (filters.style && !designer.specialties.includes(filters.style)) return false;
    if (filters.location && designer.location !== filters.location) return false;
    if (filters.rating && designer.rating < Number(filters.rating)) return false;
    if (filters.budget && designer.budgetMin > Number(filters.budget)) return false;
    return true;
  }), [designers, search, filters]);

  const filteredProjects = useMemo(() => projects.filter((project) => {
    if (!project.published) return false;
    const q = projectSearch.trim().toLowerCase();
    if (q && !`${project.title} ${project.description} ${project.styles.join(' ')}`.toLowerCase().includes(q)) return false;
    if (projectFilters.category && project.category !== projectFilters.category) return false;
    if (projectFilters.style && !project.styles.includes(projectFilters.style)) return false;
    if (projectFilters.budget && Number(project.budget) > Number(projectFilters.budget)) return false;
    if (projectFilters.propertyType && project.propertyType !== projectFilters.propertyType) return false;
    if (projectFilters.location && project.location !== projectFilters.location) return false;
    return true;
  }), [projects, projectSearch, projectFilters]);

  const allStyles = [...new Set(designers.flatMap((item) => item.specialties))];
  const locations = [...new Set(designers.map((item) => item.location))];
  const projectLocations = [...new Set(projects.map((item) => item.location))];
  const propertyTypes = PROPERTY_TYPES;

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Discovery" title="Browse interior designers" text="Search companies by name, property type, renovation category, budget, style, location or rating." />
      <div className="panel filters-grid">
        <label className="span-2">Search company / designer<input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="e.g. Studio North" /></label>
        <label>Property type<select value={filters.propertyType} onChange={(e) => setFilters({...filters, propertyType: e.target.value})}><option value="">All property types</option>{PROPERTY_TYPES.map((type) => (<option key={type} value={type}>{type}</option>))}</select></label>
        <label>Renovation category<select value={filters.category} onChange={(e) => setFilters({...filters,category: e.target.value})}><option value="">All categories</option>{categories.map((category) => (<option key={category} value={category}>{category}</option>))}</select></label>
        <label>Budget up to<select value={filters.budget} onChange={(e) => setFilters({ ...filters, budget: e.target.value })}><option value="">Any</option><option value="30000">$30,000</option><option value="50000">$50,000</option><option value="80000">$80,000</option><option value="120000">$120,000</option></select></label>
        <label>Style<select value={filters.style} onChange={(e) => setFilters({ ...filters, style: e.target.value })}><option value="">All</option>{allStyles.map((item) => <option key={item}>{item}</option>)}</select></label>
        <label>Location<select value={filters.location} onChange={(e) => setFilters({ ...filters, location: e.target.value })}><option value="">All</option>{locations.map((item) => <option key={item}>{item}</option>)}</select></label>
        <label>Minimum rating<select value={filters.rating} onChange={(e) => setFilters({ ...filters, rating: e.target.value })}><option value="">Any</option><option value="4">4.0+</option><option value="4.5">4.5+</option></select></label>
      </div>
      <p className="result-count">{approvedDesigners.length} designer(s) found</p>
      <div className="card-grid">{approvedDesigners.map((designer) => <DesignerCard key={designer.id} designer={designer} onView={openDesigner} />)}</div>


      <div className="section-heading roomy"><div><span className="eyebrow">Compare options</span><h2>Renovation packages across companies</h2><p className="muted">Compare package scope and indicative pricing before opening a company profile.</p></div></div>
      <div className="card-grid">{packages.map((item) => { const company = designers.find((designer) => designer.id === item.designerId); return <article className="card package-card" key={item.id}><div className="card-body"><span className="card-kicker">{company?.companyName} · {item.renovationType}</span><h3>{item.name}</h3><div className="package-price">${item.price.toLocaleString()}</div><p>{item.description}</p><div className="tag-row">{item.services.map((service) => <span className="tag" key={service}>{service}</span>)}</div><button className="secondary-button full-width" onClick={() => openDesigner(item.designerId)}>View company</button></div></article>; })}</div>

      <div className="section-heading roomy"><div><span className="eyebrow">Selected IDP features</span><h2>Search and filter published renovation projects</h2></div></div>
      <div className="panel filters-grid">
        <label className="span-2">Keyword search<input value={projectSearch} onChange={(e) => setProjectSearch(e.target.value)} placeholder="e.g. minimalist kitchen" /></label>
        <label>Category<select value={projectFilters.category} onChange={(e) => setProjectFilters({...projectFilters, category: e.target.value })}><option value="">All categories</option>{categories.map((item) => (<option key={item} value={item}>{item}</option>))}</select></label>
        <label>Style<select value={projectFilters.style} onChange={(e) => setProjectFilters({ ...projectFilters, style: e.target.value })}><option value="">All</option>{allStyles.map((item) => <option key={item}>{item}</option>)}</select></label>
        <label>Budget up to<select value={projectFilters.budget} onChange={(e) => setProjectFilters({ ...projectFilters, budget: e.target.value })}><option value="">Any</option><option value="25000">$25,000</option><option value="50000">$50,000</option><option value="80000">$80,000</option></select></label>
        <label>Property type<select value={projectFilters.propertyType} onChange={(e) => setProjectFilters({ ...projectFilters, propertyType: e.target.value })}><option value="">All</option>{propertyTypes.map((item) => <option key={item}>{item}</option>)}</select></label>
        <label>Location<select value={projectFilters.location} onChange={(e) => setProjectFilters({ ...projectFilters, location: e.target.value })}><option value="">All</option>{projectLocations.map((item) => <option key={item}>{item}</option>)}</select></label>
      </div>
      <p className="result-count">{filteredProjects.length} project(s) found</p>
      <div className="card-grid">{filteredProjects.map((project) => <ProjectCard key={project.id} project={project} onView={openProject} />)}</div>
    </div>
  );
}
