import { useEffect, useState } from 'react';
import ProjectCard from '../../components/ProjectCard';
import { flaskApi } from '../../services/api';
import { projectCardData, pageRequest } from '../../utils/projects';

// US-16 View my IDPs and US-03 Search and filter my IDPs (drafts included).
export default function ApiMyPortfolio({ filters = {}, onManage }) {
  const [result, setResult] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const query = JSON.stringify(filters);

  useEffect(() => {
    setLoading(true);
    setError('');
    let cancel = () => {};
    const timer = setTimeout(() => {
      cancel = pageRequest(signal => flaskApi.getMyPortfolio(JSON.parse(query), { signal }), {
        success: response => setResult({ total: response.data.total,
          items: response.data.items.map(project => ({ ...projectCardData(project), status: project.status })) }),
        failure: failure => setError(failure.status === 401 ? 'Please log in again with an active account.'
          : failure.status === 403 ? 'An InteriorDesigner account is required to view this portfolio.' : failure.message),
        settled: () => setLoading(false),
      });
    }, 250);
    return () => { clearTimeout(timer); cancel(); };
  }, [retry, query]);

  return <PortfolioResults result={result} loading={loading} error={error} onRetry={() => setRetry(value => value + 1)}
    onManage={onManage} filtered={Object.values(filters).some(Boolean)} />;
}

export function PortfolioResults({ result, loading, error, onRetry, onManage, filtered = false }) {
  if (loading) return <div className="panel form-card" role="status">Loading your portfolio...</div>;
  if (error) return <div className="panel form-card alert error-alert" role="alert"><p>{error}</p>
    <button className="secondary-button" onClick={onRetry}>Retry portfolio</button></div>;
  if (!result.items.length) return <div className="empty-state panel">
    <h3>{filtered ? 'No projects match these filters' : 'No portfolio projects yet'}</h3>
    <p>{filtered ? 'Try another search or clear the filters.' : 'Your projects will appear here after you create one.'}</p></div>;
  return <div>
    <p className="muted">{result.total} project(s)</p>
    <div className="card-grid">{result.items.map(project => <div key={`api-portfolio-${project.id}`}>
      <div className="tag-row"><span className="tag">{project.published ? 'Published' : 'Draft'}</span>
        {project.status && <span className="tag">{project.status}</span>}</div>
      <ProjectCard project={project} onView={onManage} viewLabel="Manage project" />
    </div>)}</div>
  </div>;
}
