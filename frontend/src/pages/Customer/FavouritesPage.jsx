import PageHeader from '../../components/PageHeader';
import ApiFavouriteProjects from './ApiFavouriteProjects';
import { useApp } from '../../context/AppContext';

// US-44 View favourites list, US-08 Search and filter favourites, US-56 Remove from favourites.
export default function FavouritesPage({ openProject }) {
  const { user } = useApp();
  return (
    <div className="page-shell">
      <PageHeader eyebrow="Saved items" title="My favourites" text="Projects you saved. Search them, open one, or remove it from your list." />
      <ApiFavouriteProjects key={user?.id} openApiProject={openProject} />
    </div>
  );
}
