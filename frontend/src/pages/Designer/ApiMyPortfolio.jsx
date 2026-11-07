import { useEffect, useState } from 'react';
import ProjectCard from '../../components/ProjectCard';
import { flaskApi } from '../../services/api';
import { projectCardData, pageRequest } from '../../utils/projects';

export default function ApiMyPortfolio() {
  const [result, setResult] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    setLoading(true);
    setError('');
    return pageRequest(signal => flaskApi.getMyPortfolio({}, { signal }), {
      success: response => setResult({ total: response.data.total,
        items: response.data.items.map(project => ({ ...projectCardData(project), status: project.status })) }),
      failure: error => setError(error.status === 401 ? 'Please log in again with an active account.'
        : error.status === 403 ? 'An InteriorDesigner account is required to view this portfolio.' : error.message),
      settled: () => setLoading(false),
    });
  }, [retry]);

  return <PortfolioResults result={result} loading={loading} error={error} onRetry={() => setRetry(value => value + 1)} />;
}

export function PortfolioResults({ result, loading, error, onRetry }) {
  if (loading) return <div className="panel form-card" role="status">Loading your portfolio...</div>;
  if (error) return <div className="panel form-card alert error-alert" role="alert"><p>{error}</p>
    <button className="secondary-button" onClick={onRetry}>Retry portfolio</button></div>;
  if (!result.items.length) return <div className="empty-state panel"><h3>No portfolio projects yet</h3>
    <p>Your real Flask projects will appear here. The demo form does not create real projects yet.</p></div>;
  return <div>
    <p className="muted">{result.total} project(s) / read-only</p>
    <div className="card-grid">{result.items.map(project => <div key={`api-portfolio-${project.id}`}>
      <div className="tag-row"><span className="tag">{project.published ? 'Published' : 'Draft'}</span>
        {project.status && <span className="tag">{project.status}</span>}</div>
      <ProjectCard project={project} showSave={false} />
    </div>)}</div>
  </div>;
}
