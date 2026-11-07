import { useState } from 'react';
import FieldError from '../../components/FieldError';
import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import { useApp } from '../../context/AppContext';
import { isFutureOrToday, isRequired } from '../../utils/validation';

export default function DesignerConsultationsPage() {
  const { user, consultations, updateConsultation } = useApp();
  const mine = consultations.filter((item) => item.designerId === (user?.designerId || 101));
  const [rescheduleId, setRescheduleId] = useState(null);
  const [newDate, setNewDate] = useState('');
  const [newTime, setNewTime] = useState('');
  const [error, setError] = useState('');

  async function reschedule(id) {
    if (!isFutureOrToday(newDate) || !isRequired(newTime)) {
      setError('Choose a valid future date and time.');
      return;
    }
    await updateConsultation(id, { date: newDate, time: newTime, status: 'rescheduled' });
    setRescheduleId(null); setNewDate(''); setNewTime(''); setError('');
  }

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Appointments" title="Manage consultations" text="Accept pending appointment requests or reschedule them." />
      <div className="stack-list">
        {mine.map((item) => <article className="panel list-card consultation-card" key={item.id}>
          <div><span className="card-kicker">{item.mode}</span><h3>{item.customerName}</h3><p>{item.date} at {item.time}</p><StatusBadge>{item.status}</StatusBadge></div>
          <div className="card-actions">
            <button className="primary-button" onClick={() => updateConsultation(item.id, { status: 'confirmed' })}>Accept</button>
            <button className="secondary-button" onClick={() => setRescheduleId(item.id)}>Reschedule</button>
          </div>
          {rescheduleId === item.id && <div className="inline-form"><label>New date<input type="date" value={newDate} onChange={(e) => setNewDate(e.target.value)} /></label><label>New time<input type="time" value={newTime} onChange={(e) => setNewTime(e.target.value)} /></label><button className="primary-button" onClick={() => reschedule(item.id)}>Save</button><FieldError message={error} /></div>}
        </article>)}
      </div>
    </div>
  );
}
