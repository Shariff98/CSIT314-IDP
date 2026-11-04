import { useState } from 'react';
import FieldError from '../../components/FieldError';
import PageHeader from '../../components/PageHeader';
import { useApp } from '../../context/AppContext';
import { isFutureOrToday, isPositiveNumber, isRequired, validateFiles } from '../../utils/validation';

export default function RequirementsPage() {
  const { designers, submitRequirements } = useApp();
  const approved = designers.filter((item) => item.verified && item.status === 'active');
  const [form, setForm] = useState({ designerId: '', propertyType: '', budget: '', preferredStyle: '', rooms: '', expectedCompletionDate: '', additionalInfo: '' });
  const [floorPlan, setFloorPlan] = useState(null);
  const [inspiration, setInspiration] = useState([]);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');

  async function submit(event) {
    event.preventDefault();
    const next = {};
    if (!isRequired(form.designerId)) next.designerId = 'Choose a designer.';
    if (!isRequired(form.propertyType)) next.propertyType = 'Property type is required.';
    if (!isPositiveNumber(form.budget)) next.budget = 'Budget must be greater than 0.';
    if (!isRequired(form.preferredStyle)) next.preferredStyle = 'Preferred style is required.';
    if (!isRequired(form.rooms)) next.rooms = 'Enter at least one room or area.';
    if (!isFutureOrToday(form.expectedCompletionDate)) next.expectedCompletionDate = 'Choose today or a future date.';
    if (!floorPlan) next.floorPlan = 'Upload a floor plan.';
    if (floorPlan && !['application/pdf', 'image/png', 'image/jpeg'].includes(floorPlan.type)) next.floorPlan = 'Floor plan must be PDF, JPG or PNG.';
    const inspirationError = validateFiles(inspiration, { imagesOnly: true, maxFiles: 8 });
    if (inspirationError) next.inspiration = inspirationError;
    setErrors(next);
    if (Object.keys(next).length) return;

    // === BACKEND INTEGRATION === Use multipart/form-data for floor plan + inspiration image files.
    await submitRequirements({
      ...form,
      designerId: Number(form.designerId),
      budget: Number(form.budget),
      floorPlanName: floorPlan.name,
      inspirationNames: Array.from(inspiration).map((file) => file.name),
    });
    setMessage('Renovation requirements submitted. The selected company can now view the full enquiry in its portal.');
  }

  return (
    <div className="page-shell narrow-content">
      <PageHeader eyebrow="Renovation brief" title="Submit renovation requirements" text="Give the designer enough information to understand your property, budget and preferred outcome." />
      <form className="panel form-card large-form" onSubmit={submit} noValidate>
        <div className="two-column-form">
          <label>Interior design company<select value={form.designerId} onChange={(e) => setForm({ ...form, designerId: e.target.value })}><option value="">Choose company</option>{approved.map((designer) => <option key={designer.id} value={designer.id}>{designer.companyName}</option>)}</select><FieldError message={errors.designerId} /></label>
          <label>Property type<input value={form.propertyType} onChange={(e) => setForm({ ...form, propertyType: e.target.value })} placeholder="e.g. 5-Room HDB" /><FieldError message={errors.propertyType} /></label>
          <label>Budget (SGD)<input type="number" min="1" value={form.budget} onChange={(e) => setForm({ ...form, budget: e.target.value })} /><FieldError message={errors.budget} /></label>
          <label>Preferred style<input value={form.preferredStyle} onChange={(e) => setForm({ ...form, preferredStyle: e.target.value })} placeholder="e.g. Modern / Japandi" /><FieldError message={errors.preferredStyle} /></label>
          <label>Rooms / areas<input value={form.rooms} onChange={(e) => setForm({ ...form, rooms: e.target.value })} placeholder="Living room, kitchen, bedrooms" /><FieldError message={errors.rooms} /></label>
          <label>Expected completion date<input type="date" value={form.expectedCompletionDate} onChange={(e) => setForm({ ...form, expectedCompletionDate: e.target.value })} /><FieldError message={errors.expectedCompletionDate} /></label>
        </div>
        <label>Floor plan<input type="file" accept=".pdf,image/png,image/jpeg" onChange={(e) => setFloorPlan(e.target.files?.[0] || null)} /><FieldError message={errors.floorPlan} /><small>PDF, JPG or PNG. Prototype stores file name only.</small></label>
        <label>Inspiration images<input type="file" accept="image/*" multiple onChange={(e) => setInspiration(e.target.files)} /><FieldError message={errors.inspiration} /><small>Up to 8 image files.</small></label>
        <label>Additional information<textarea rows="5" value={form.additionalInfo} onChange={(e) => setForm({ ...form, additionalInfo: e.target.value })} placeholder="Storage needs, preferred materials, existing constraints, etc." /></label>
        <button className="primary-button" type="submit">Submit requirements</button>
        {message && <div className="alert success-alert">{message}</div>}
      </form>
    </div>
  );
}
