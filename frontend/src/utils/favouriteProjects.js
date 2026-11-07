import { flaskApi } from '../services/api.js';
import { projectCardData } from './projects.js';
import { favouriteError } from './favourites.js';

export const emptyFavouriteList = () => ({ items: [], total: 0, loading: true, error: '', pending: [], removalErrors: {} });

export function favouriteListError(error) {
  if (error.status === 401) return 'Your session has expired. Please log in again to view favourites.';
  if (error.status === 403) return 'An active Customer account is required to view favourites.';
  return `Could not load favourite projects. ${error.message}`;
}

// Each mounted project section owns this state. Nothing enters mock favourites.
export function favouriteList(onChange, api = flaskApi) {
  let active = true;
  let revision = 0;
  let state = emptyFavouriteList();
  const removed = new Set();
  const pending = new Set();
  const emit = patch => {
    if (!active) return;
    state = { ...state, ...patch };
    onChange(state);
  };
  return {
    async load(search = '', category = '') {
      const request = ++revision;
      emit({ loading: true, error: '' });
      try {
        const response = await api.getFavouriteProjects({ q: search.trim(), category });
        if (!active || request !== revision) return;
        const items = response.data.items.map(projectCardData).filter(item => !removed.has(item.id));
        // This API returns the entire matching list, not a paginated subset.
        emit({ items, total: items.length });
      } catch (error) {
        if (active && request === revision) emit({ error: favouriteListError(error) });
      } finally {
        if (active && request === revision) emit({ loading: false });
      }
    },
    async remove(id) {
      if (!active || pending.has(id)) return;
      pending.add(id);
      emit({ pending: [...pending], removalErrors: { ...state.removalErrors, [id]: '' } });
      try {
        const response = await api.removeSavedProject(id);
        if (response.data?.project_id !== id || response.data.saved !== false) {
          throw new Error('The server did not confirm removal.');
        }
        if (!active) return;
        // A list request begun before deletion may still contain this ID.
        removed.add(id);
        const items = state.items.filter(item => item.id !== id);
        emit({ items, total: items.length });
      } catch (error) {
        emit({ removalErrors: { ...state.removalErrors, [id]: favouriteError(error) } });
      } finally {
        pending.delete(id);
        emit({ pending: [...pending] });
      }
    },
    prepareLoad() { ++revision; emit({ loading: true, error: '' }); },
    cancelLoad() { ++revision; },
    dispose() { active = false; ++revision; },
  };
}
