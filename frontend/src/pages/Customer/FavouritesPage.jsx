import DesignerCard from '../../components/DesignerCard';
import EmptyState from '../../components/EmptyState';
import PageHeader from '../../components/PageHeader';
import ProjectCard from '../../components/ProjectCard';
import { useApp } from '../../context/AppContext';

export default function FavouritesPage({ openDesigner, openProject }) {
  const { designers, projects, favouriteDesignerIds, favouriteProjectIds } = useApp();
  const favouriteDesigners = designers.filter((item) => favouriteDesignerIds.includes(item.id));
  const favouriteProjects = projects.filter((item) => favouriteProjectIds.includes(item.id));

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Saved items" title="My favourites" text="Review saved interior design companies and portfolio projects." />
      <div className="section-heading"><div><h2>Favourite designers</h2></div></div>
      {favouriteDesigners.length ? <div className="card-grid">{favouriteDesigners.map((designer) => <DesignerCard key={designer.id} designer={designer} onView={openDesigner} />)}</div> : <EmptyState title="No favourite designers" text="Save a company from the designer browsing page." />}
      <div className="section-heading roomy"><div><h2>Favourite projects</h2></div></div>
      {favouriteProjects.length ? <div className="card-grid">{favouriteProjects.map((project) => <ProjectCard key={project.id} project={project} onView={openProject} />)}</div> : <EmptyState title="No favourite projects" text="Save portfolio projects for renovation inspiration." />}
    </div>
  );
}
