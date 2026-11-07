import { useMemo, useState } from 'react';
import PageHeader from '../../components/PageHeader';
import ProjectCard from '../../components/ProjectCard';
import { useApp } from '../../context/AppContext';
import { PROPERTY_TYPES } from '../../data/options';

const emptyFilters = {
  category: '',
  style: '',
  budget: '',
  propertyType: '',
  location: ''
};

export default function IDPsPage({ openProject }) {
  const { projects, categories } = useApp();

  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState(emptyFilters);

  // Only published IDPs should be accessible to customers.
  const publishedProjects = projects.filter(
    (project) => project.published
  );

  // Generate dropdown options from available project data.
  const styles = [
    ...new Set(publishedProjects.flatMap(
      (project) => project.styles || []
    ))
  ].sort();

  const locations = [
    ...new Set(publishedProjects.map(
      (project) => project.location
    ))
  ].sort();

  const filteredProjects = useMemo(() => {
    return projects.filter((project) => {
      if (!project.published) return false;

      const keyword = search.trim().toLowerCase();

      if (
        keyword &&
        !`${project.title} ${project.description} ${project.category}`
          .toLowerCase()
          .includes(keyword)
      ) return false;

      if (
        filters.category &&
        project.category !== filters.category
      ) return false;

      if (
        filters.style &&
        !project.styles.includes(filters.style)
      ) return false;

      if (
        filters.budget &&
        Number(project.budget) > Number(filters.budget)
      ) return false;

      if (
        filters.propertyType &&
        project.propertyType !== filters.propertyType
      ) return false;

      if (
        filters.location &&
        project.location !== filters.location
      ) return false;

      return true;
    });
  }, [projects, search, filters]);

  function updateFilter(field, value) {
    setFilters((previous) => ({
      ...previous,
      [field]: value
    }));
  }

  function resetFilters() {
    setSearch('');
    setFilters({ ...emptyFilters });
  }

  // === BACKEND INTEGRATION ===
  // Currently filters mock project data locally.
  // Later, call GET /api/idps with search/filter query parameters.
  // Python should return published projects matching the filters.

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="Renovation inspiration"
        title="Browse Interior Design Projects"
        text="Explore renovation projects by room category, style, budget, property type or location."
      />

      <div className="panel filters-grid">
        <label className="span-2">
          Search IDPs
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search renovation projects..."
          />
        </label>

        <label>
          Category
          <select
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
            value={filters.propertyType}
            onChange={(e) =>
              updateFilter('propertyType', e.target.value)
            }
          >
            <option value="">All property types</option>
            {PROPERTY_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>

        <label>
          Location
          <select
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
      </div>

      <div className="section-heading roomy">
        <div>
          <h2>Renovation Projects</h2>
          <p className="muted">
            {filteredProjects.length} project(s) found
          </p>
        </div>

        <button
          className="secondary-button compact"
          onClick={resetFilters}
        >
          Clear filters
        </button>
      </div>

      {filteredProjects.length === 0 ? (
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
          {filteredProjects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onView={openProject}
            />
          ))}
        </div>
      )}
    </div>
  );
}