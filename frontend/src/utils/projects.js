// Adapt only this page's API results; shared mock records stay unchanged.
export function projectCardData(project) {
  return {
    id: project.id,
    designerId: project.designer_id,
    title: project.title,
    description: project.description,
    category: project.category,
    budget: project.budget,
    propertyType: project.property_type || '',
    location: project.location || '',
    completionDate: project.completion_date,
    published: project.published,
    views: project.views,
    styles: Array.isArray(project.style_tags) ? project.style_tags : [],
    photos: (project.photos || []).filter(photo => photo?.url).map(photo => photo.url),
    // An explicit null prevents a coincidentally matching mock designer ID.
    companyName: project.company?.name || null,
  };
}

export function projectDetailsData(project) {
  if (!project || !Number.isSafeInteger(project.id) || project.id < 1) {
    throw new Error('Unexpected project details response.');
  }
  return { ...projectCardData(project), company: project.company || null, status: project.status };
}

export function projectDetailsError(error) {
  return error.status === 404 ? 'Project not found or unavailable.' : `Could not load project: ${error.message}`;
}

export function projectQuery(search, filters, page, perPage = 24) {
  return { q: search.trim(), category: filters.category, style: filters.style,
    max_budget: filters.budget, property_type: filters.propertyType, location: filters.location,
    sort: filters.sort || 'newest', page, per_page: perPage };
}

// Cleanup both aborts fetch and ignores late completions, even if a transport
// does not support cancellation. Each effect owns its own request lifecycle.
export function pageRequest(task, { success, failure, settled = () => {} }) {
  const controller = new AbortController();
  let active = true;
  Promise.resolve().then(() => active ? task(controller.signal) : undefined).then(result => {
    if (active) success(result);
  }).catch(error => {
    if (active && error.name !== 'AbortError') failure(error);
  }).finally(() => { if (active) settled(); });
  return () => { active = false; controller.abort(); };
}
