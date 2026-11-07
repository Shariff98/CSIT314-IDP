import { flaskApi } from '../services/api.js';

export const canSaveProject = user => user?.role === 'Customer' && user.status === 'Active';

// One operation per button at a time; failures release the lock for a retry.
// Never infer success locally or touch AppContext's mock favourite IDs.
export function favouriteMutation(api = flaskApi) {
  let pending = false;
  return async (id, desiredSaved) => {
    if (pending) return null;
    pending = true;
    try {
      const response = await (desiredSaved ? api.saveProject(id) : api.removeSavedProject(id));
      const data = response.data;
      if (data?.project_id !== Number(id) || data.saved !== desiredSaved) {
        throw new Error('The server did not confirm the favourite change. Please retry.');
      }
      return data;
    } finally {
      pending = false;
    }
  };
}

export function favouriteError(error) {
  if (error.status === 401) return 'Your session has expired. Please log in again to manage favourites.';
  if (error.status === 403) return 'An active Customer account is required to manage favourites.';
  if (error.status === 404) return 'This project is no longer available to save.';
  return `Could not confirm the favourite change. ${error.message} Please retry.`;
}
