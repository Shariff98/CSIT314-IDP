import { useEffect, useState } from 'react';
import PageHeader from '../../components/PageHeader';
import { flaskApi } from '../../services/api';
import { validateFiles } from '../../utils/validation';
import { pageRequest } from '../../utils/projects';
import { ProjectFields, projectFormErrors, useProjectOptions } from './CreateProjectPage';

const MAX_PHOTOS = 10;
const money = (value) => `$${Number(value).toLocaleString()}`;

export function formFromProject(project) {
  return { title: project.title, description: project.description, category: project.category,
    budget: String(project.budget), propertyType: project.property_type || '', location: project.location || '',
    completionDate: project.completion_date || '', styles: project.style_tags.join(', ') };
}

export function updatePayload(form) {
  return { title: form.title, description: form.description, category: form.category, budget: Number(form.budget),
    property_type: form.propertyType, location: form.location, completion_date: form.completionDate || null };
}

// One of the designer's own projects. Every button calls one Flask endpoint and shows the
// project as Flask saved it:
// US-27 view, US-04 edit, US-26 tags, US-06 current/past, US-33 publish, US-55 photos,
// US-05 delete, US-29 view count and US-46 shortlist count.
export default function ManageProjectPage({ projectId, go }) {
  const [project, setProject] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [busy, setBusy] = useState('');
  const [message, setMessage] = useState(null);
  const [form, setForm] = useState(null);
  const [errors, setErrors] = useState({});
  const [tags, setTags] = useState({ category: '', styles: '' });
  const { options } = useProjectOptions();

  function show(saved) {
    setProject(saved);
    setForm(formFromProject(saved));
    setTags({ category: saved.category, styles: saved.style_tags.join(', ') });
  }

  useEffect(() => pageRequest(signal => flaskApi.getMyProject(projectId, { signal }), {
    success: response => show(response.data.project),
    failure: setLoadError,
  }), [projectId]);

  // Runs one request, then shows the server's version of the project and a message.
  async function run(name, request, success) {
    setBusy(name);
    setMessage(null);
    try {
      const response = await request();
      if (response?.data?.project) show(response.data.project);
      setMessage({ ok: true, text: typeof success === 'function' ? success(response.data) : success });
      return response;
    } catch (error) {
      setMessage({ ok: false, text: error.status === 401 ? 'Please log in again.' : error.message });
      return null;
    } finally {
      setBusy('');
    }
  }

  if (loadError) {
    return <div className="page-shell"><button className="text-button" onClick={() => go('portfolio')}>Back to my projects</button>
      <div className="panel form-card" role="alert"><h2>{loadError.status === 404 ? 'Project not found' : 'Could not load the project'}</h2>
        <p>{loadError.status === 404 ? 'It may have been deleted, or it belongs to another designer.' : loadError.message}</p></div></div>;
  }
  if (!project) return <div className="page-shell"><p role="status">Loading project...</p></div>;

  async function saveDetails(event) {
    event.preventDefault();
    const next = projectFormErrors({ ...form, styles: '' });
    setErrors(next);
    if (Object.keys(next).length) return;
    await run('details', () => flaskApi.updateMyProject(project.id, updatePayload(form)), 'Project details saved.');
  }

  async function uploadPhotos(event) {
    const input = event.currentTarget;
    const files = Array.from(input.files || []);
    input.value = '';
    const problem = validateFiles(files, { imagesOnly: true, maxFiles: MAX_PHOTOS - project.photos.length });
    if (problem) { setMessage({ ok: false, text: problem }); return; }
    if (files.some((file) => file.size > 5 * 1024 * 1024)) { setMessage({ ok: false, text: 'Each photo must be 5 MB or smaller.' }); return; }
    setBusy('photos');
    setMessage(null);
    let uploaded = 0;
    try {
      for (const file of files) {   // one request per photo, so one bad file doesn't lose the others
        const response = await flaskApi.uploadPhoto(project.id, file);
        show(response.data.project);
        uploaded++;
      }
      setMessage({ ok: true, text: `${uploaded} photo(s) uploaded.` });
    } catch (error) {
      setMessage({ ok: false, text: `${uploaded} uploaded, then: ${error.message}` });
    } finally {
      setBusy('');
    }
  }

  async function remove() {
    if (!window.confirm(`Delete "${project.title}"? Its photos, favourites and view history are deleted too. This cannot be undone.`)) return;
    const response = await run('delete', () => flaskApi.deleteMyProject(project.id), 'Project deleted.');
    if (response) go('portfolio');
  }

  const published = project.published;
  return (
    <div className="page-shell">
      <button className="text-button" onClick={() => go('portfolio')}>Back to my projects</button>
      <PageHeader eyebrow={`${published ? 'Published' : 'Draft'} · ${project.status}`} title={project.title}
        text={`${project.category} · ${money(project.budget)}${project.location ? ` · ${project.location}` : ''}`}
        actions={published && <a className="secondary-button" href={`#/projects/${project.id}`}>View as customer</a>} />

      {message && <div className={`alert ${message.ok ? 'success-alert' : 'error-alert'}`} role={message.ok ? 'status' : 'alert'}>{message.text}</div>}
      {!published && <div className="alert warning-alert">Customers can't see drafts. {project.photos.length ? 'Publish it when you are ready.' : 'Add a photo, then publish it.'}</div>}

      <div className="manage-grid section-block">
        <div>
          <section className="panel form-card" aria-label="Photos">
            <h2>Photos</h2>
            <p className="muted">{project.photos.length} of {MAX_PHOTOS}. The cover photo is shown on cards. JPG, PNG, GIF or WEBP, up to 5 MB each.</p>
            {project.photos.length > 0 && <div className="photo-grid">{project.photos.map((photo) => (
              <figure key={photo.id} className={`photo-tile ${photo.is_cover ? 'cover' : ''}`} style={{ margin: 0 }}>
                <img src={photo.url} alt={photo.is_cover ? 'Cover photo' : 'Project photo'} />
                <div className="card-actions">
                  {photo.is_cover ? <span className="tag">Cover</span>
                    : <button className="secondary-button compact" disabled={!!busy}
                      onClick={() => run('cover', () => flaskApi.setCoverPhoto(photo.id), 'Cover photo changed.')}>Make cover</button>}
                  <button className="danger-button compact" disabled={!!busy}
                    onClick={() => run('photo', () => flaskApi.deletePhoto(photo.id), 'Photo deleted.')}>Delete</button>
                </div>
              </figure>))}</div>}
            <label>Add photos<input type="file" accept="image/*" multiple disabled={!!busy || project.photos.length >= MAX_PHOTOS} onChange={uploadPhotos} /></label>
            {busy === 'photos' && <p role="status">Uploading...</p>}
          </section>

          <form className="panel form-card" onSubmit={saveDetails} noValidate aria-label="Project details">
            <h2>Details</h2>
            <fieldset disabled={!!busy} style={{ border: 0, margin: 0, padding: 0, minWidth: 0 }}>
              <ProjectFields form={form} setForm={setForm} errors={errors} options={options} withStyles={false} />
              <button className="primary-button" type="submit">{busy === 'details' ? 'Saving...' : 'Save details'}</button>
            </fieldset>
          </form>
        </div>

        <div>
          <section className="panel form-card" aria-label="Interest">
            <h2>Interest</h2>
            <dl className="detail-list">
              <div><dt>Views</dt><dd>{project.views.toLocaleString()}</dd></div>
              <div><dt>Shortlisted by customers</dt><dd>{project.shortlists}</dd></div>
            </dl>
          </section>

          <section className="panel form-card" aria-label="Visibility">
            <h2>Visibility</h2>
            <p className="muted">{published ? 'Customers can find this project.' : 'Only you can see this draft.'}</p>
            <div className="button-row">
              <button className="primary-button" disabled={!!busy}
                onClick={() => run('publish', () => flaskApi.setPublished(project.id, !published),
                  published ? 'Moved back to drafts.' : 'Published. Customers can now see it.')}>
                {published ? 'Unpublish' : 'Publish'}</button>
            </div>
            <h3>Project status</h3>
            <div className="button-row">
              {['Current', 'Past'].map((status) => <button key={status} disabled={!!busy || project.status === status}
                className={project.status === status ? 'secondary-button' : 'primary-button'}
                onClick={() => run('status', () => flaskApi.markStatus(project.id, status), `Marked as ${status.toLowerCase()}.`)}>
                {project.status === status ? `${status} (now)` : `Mark as ${status.toLowerCase()}`}</button>)}
            </div>
          </section>

          <form className="panel form-card" aria-label="Category and style tags" onSubmit={(event) => {
            event.preventDefault();
            run('tags', () => flaskApi.assignTags(project.id, { category: tags.category, style_tags: tags.styles }), 'Category and style tags saved.');
          }}>
            <h2>Category and style tags</h2>
            <fieldset disabled={!!busy} style={{ border: 0, margin: 0, padding: 0, minWidth: 0 }}>
              <label>Category<select value={tags.category} onChange={(e) => setTags({ ...tags, category: e.target.value })}>
                {!options.categories.includes(tags.category) && <option value={tags.category}>{tags.category}</option>}
                {options.categories.map((item) => <option key={item}>{item}</option>)}</select></label>
              <label>Style tags (comma-separated, up to 5)<input value={tags.styles} onChange={(e) => setTags({ ...tags, styles: e.target.value })} placeholder="Modern, Japandi" /></label>
              {project.style_tags.length > 0 && <div className="tag-row">{project.style_tags.map((tag) => <span className="tag" key={tag}>{tag}</span>)}</div>}
              <button className="primary-button" type="submit">{busy === 'tags' ? 'Saving...' : 'Save tags'}</button>
            </fieldset>
          </form>

          <section className="panel form-card" aria-label="Delete project">
            <h2>Delete project</h2>
            <p className="muted">Removes the project with its photos, favourites and view history.</p>
            <button className="danger-button" disabled={!!busy} onClick={remove}>Delete project</button>
          </section>
        </div>
      </div>
    </div>
  );
}
