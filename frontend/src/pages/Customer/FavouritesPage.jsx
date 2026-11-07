import DesignerCard from '../../components/DesignerCard';
import EmptyState from '../../components/EmptyState';
import PageHeader from '../../components/PageHeader';
import ApiFavouriteProjects from './ApiFavouriteProjects';
import { useApp } from '../../context/AppContext';

export default function FavouritesPage({ openDesigner, openApiProject }) {
  const { user, designers, favouriteDesignerIds } = useApp();
  const favouriteDesigners = designers.filter((item) => favouriteDesignerIds.includes(item.id));

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Saved items" title="My favourites" text="Review saved interior design companies and portfolio projects." />
      <div className="section-heading"><div><h2>Favourite designers</h2></div></div>
      {favouriteDesigners.length ? <div className="card-grid">{favouriteDesigners.map((designer) => <DesignerCard key={designer.id} designer={designer} onView={openDesigner} />)}</div> : <EmptyState title="No favourite designers" text="Save a company from the designer browsing page." />}
      <ApiFavouriteProjects key={user?.id} openApiProject={openApiProject} />
    </div>
  );
}
