import { useState } from 'react';
import FieldError from '../../components/FieldError';
import PageHeader from '../../components/PageHeader';
import { useApp } from '../../context/AppContext';
import { isRequired } from '../../utils/validation';

export default function CategoriesPage() {
  const { categories, addCategory, removeCategory } = useApp();
  const [name, setName] = useState('');
  const [error, setError] = useState('');

  async function submit(event) {
    event.preventDefault();
    if (!isRequired(name)) { setError('Category name is required.'); return; }
    if (categories.some((item) => item.toLowerCase() === name.trim().toLowerCase())) { setError('This category already exists.'); return; }
    setError('');
    await addCategory(name.trim());
    setName('');
  }

  return (
    <div className="page-shell narrow-content">
      <PageHeader eyebrow="Platform taxonomy" title="Manage renovation categories" text="Maintain categories and styles used to organise portfolio projects." />
      <form className="panel form-card inline-category-form" onSubmit={submit} noValidate><label>New category<input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Balcony" /><FieldError message={error} /></label><button className="primary-button" type="submit">Add category</button></form>
      <div className="stack-list roomy">{categories.map((category) => <div className="panel list-card" key={category}><strong>{category}</strong><button className="danger-button compact" onClick={() => removeCategory(category)}>Remove</button></div>)}</div>
    </div>
  );
}
