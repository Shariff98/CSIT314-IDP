import { flaskApi } from '../services/api.js';
import { isRequired } from './validation.js';

export function portfolioOptionalFieldErrors(form, demoEdit) {
  const errors = {};
  if (demoEdit && !isRequired(form.completionDate)) errors.completionDate = 'Completion date is required.';
  if (demoEdit && !isRequired(form.styles)) errors.styles = 'Add at least one style tag.';
  return errors;
}

export function createPortfolioPayload(form) {
  const budget = Number(form.budget);
  if (!Number.isSafeInteger(budget) || budget < 1) throw new Error('Budget must be a positive whole number.');
  return { title: form.title, description: form.description, category: form.category, budget,
    property_type: form.propertyType || '', location: form.location || '', completion_date: form.completionDate || null,
    style_tags: form.styles || '', publish: false };
}

// Isolate real creation from all mock ID generation and mock photo paths.
export function createPortfolioMutation(api = flaskApi) {
  let pending = false;
  return async form => {
    if (pending) return null;
    pending = true;
    try {
      const response = await api.createPortfolioProject(createPortfolioPayload(form));
      const project = response.data?.project;
      if (!Number.isSafeInteger(project?.id) || project.id < 1 || project.published !== false) {
        throw new Error('The server did not confirm draft creation. Reopen the portfolio to check before retrying.');
      }
      return project;
    } finally { pending = false; }
  };
}
