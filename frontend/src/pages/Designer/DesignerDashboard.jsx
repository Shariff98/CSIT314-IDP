import { useEffect, useState } from 'react';
import PageHeader from '../../components/PageHeader';
import { flaskApi } from '../../services/api';
import { pageRequest } from '../../utils/projects';

// US-57 portfolio dashboard, US-29 views per project, US-46 shortlists per project, US-48 milestones.
// The deeper reports (rank, trends by date, compare, CSV export) are the Flask /analytics pages.
export default function DesignerDashboard({ go }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    setError('');
    return pageRequest(signal => flaskApi.getAnalytics({ signal }), {
      success: response => setData(response.data),
      failure: failure => setError(failure.message),
    });
  }, [retry]);

  const open = (id) => go('portfolio-item', { id });
  const actions = <>
    <button className="primary-button" onClick={() => go('portfolio-new')}>New project</button>
    <a className="secondary-button" href="/analytics/">Full analytics</a>
  </>;

  if (error) {
    return <div className="page-shell"><PageHeader eyebrow="Interior designer" title="Dashboard" actions={actions} />
      <div className="panel form-card alert error-alert" role="alert"><p>Could not load your statistics: {error}</p>
        <button className="secondary-button" onClick={() => setRetry(value => value + 1)}>Retry</button></div></div>;
  }
  if (!data) return <div className="page-shell"><PageHeader eyebrow="Interior designer" title="Dashboard" actions={actions} /><p role="status">Loading your statistics...</p></div>;

  const { summary, views, shortlists, notifications, unread_notifications: unread } = data;
  const metric = (label, value, note, onClick) => (
    <button className={`metric-card ${onClick ? '' : 'static'}`} onClick={onClick} disabled={!onClick}>
      <span>{label}</span><strong>{value}</strong>{note && <small>{note}</small>}
    </button>
  );

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Interior designer" title="Dashboard" text="How customers are responding to your projects." actions={actions} />
      <div className="metric-grid four">
        {metric('Projects', summary.projects, `${summary.published} published · ${summary.drafts} drafts`, () => go('portfolio'))}
        {metric('Total views', summary.views.toLocaleString(), `${summary.views_30_days} in the last 30 days`)}
        {metric('Shortlists', summary.shortlists, `${summary.shortlists_30_days} in the last 30 days`)}
        {metric('Save rate', `${summary.save_rate}%`, 'shortlists per 100 views')}
      </div>
      {summary.top_project && <div className="alert success-alert">Most viewed: <a href={`#/designer/projects/${summary.top_project.id}`}
        onClick={(e) => { e.preventDefault(); open(summary.top_project.id); }}>{summary.top_project.title}</a> with {summary.top_project.views} views.</div>}

      <div className="two-panel-grid section-block">
        <CountTable title="Views per project" metric="views" data={views} onOpen={open} />
        <CountTable title="Shortlists per project" metric="shortlists" data={shortlists} onOpen={open} />
      </div>

      <section className="panel form-card section-block" aria-label="Milestones">
        <div className="section-heading compact-heading"><div><h2>Milestones</h2>
          <p className="muted">{unread} unread</p></div><a className="text-button" href="/analytics/notifications">All notifications</a></div>
        {notifications.length ? <ul className="notification-list">{notifications.map((n) => <li key={n.id} className={n.is_read ? '' : 'unread'}>{n.message}</li>)}</ul>
          : <p className="muted">No milestones yet. You'll see one when a project reaches 10 views or 5 shortlists.</p>}
      </section>
    </div>
  );
}

function CountTable({ title, metric, data, onOpen }) {
  return (
    <section className="panel form-card data-table" aria-label={title}>
      <h2>{title}</h2>
      <p className="muted">Total: {data.total.toLocaleString()}</p>
      {data.rows.length === 0 ? <p className="muted">No projects yet.</p> : <div className="table-wrap"><table>
        <thead><tr><th scope="col">Project</th><th scope="col">State</th><th scope="col" className="number">{metric === 'views' ? 'Views' : 'Shortlists'}</th></tr></thead>
        <tbody>{[...data.rows].sort((a, b) => b[metric] - a[metric]).slice(0, 10).map((row) => <tr key={row.id}>
          <td><a href={`#/designer/projects/${row.id}`} onClick={(e) => { e.preventDefault(); onOpen(row.id); }}>{row.title}</a></td>
          <td>{row.published ? row.status : 'Draft'}</td>
          <td className="number">{row[metric].toLocaleString()}</td>
        </tr>)}</tbody>
      </table></div>}
      {data.rows.length > 10 && <p className="muted">Showing the top 10 of {data.rows.length}.</p>}
    </section>
  );
}
