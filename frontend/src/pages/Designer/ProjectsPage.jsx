import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import { useApp } from '../../context/AppContext';

export default function ProjectsPage() {
  const { user, activeProjects, toggleMilestone } = useApp();
  const mine = activeProjects.filter((item) => item.designerId === (user?.designerId || 101));
  return (
    <div className="page-shell">
      <PageHeader eyebrow="Active renovation work" title="Manage renovation projects" text="Track current customer projects and record completed renovation milestones." />
      <div className="stack-list">
        {mine.map((project) => {
          const completed = project.milestones.filter((item) => item.completed).length;
          return <article className="panel project-progress-card" key={project.id}>
            <div className="section-heading compact-heading"><div><span className="card-kicker">{project.customerName}</span><h2>{project.projectName}</h2></div><StatusBadge>{project.status}</StatusBadge></div>
            <div className="progress-bar"><span style={{ width: `${(completed / project.milestones.length) * 100}%` }} /></div>
            <p className="muted">{completed} of {project.milestones.length} milestones complete</p>
            <div className="milestone-list">{project.milestones.map((milestone) => <label className={`milestone ${milestone.completed ? 'done' : ''}`} key={milestone.id}><input type="checkbox" checked={milestone.completed} onChange={() => toggleMilestone(project.id, milestone.id)} /><span>{milestone.name}</span></label>)}</div>
          </article>;
        })}
      </div>
    </div>
  );
}
