import { useState } from 'react';
import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import { useApp } from '../../context/AppContext';

export default function EnquiriesPage() {
  const { user, enquiries, updateEnquiryStatus } = useApp();
  const designerId = user?.designerId || 101;
  const mine = enquiries.filter((item) => item.designerId === designerId);
  const [selectedId, setSelectedId] = useState(mine[0]?.id || null);
  const selected = mine.find((item) => item.id === selectedId);

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Customer interest" title="Customer enquiries" text="Review quotation requests, renovation requirements, floor plans and inspiration uploads in one place." />
      <div className="split-view">
        <aside className="panel list-pane">
          {mine.map((item) => (
            <button key={item.id} className={`list-row ${selectedId === item.id ? 'selected' : ''}`} onClick={() => setSelectedId(item.id)}>
              <div><strong>{item.customerName}</strong><small>{item.propertyType || 'Renovation enquiry'} · {item.createdAt}</small></div>
              <StatusBadge>{item.status}</StatusBadge>
            </button>
          ))}
          {!mine.length && <div className="empty-table">No enquiries yet.</div>}
        </aside>
        <section className="panel detail-pane">
          {selected ? (
            <>
              <div className="section-heading compact-heading"><div><span className="eyebrow">Full enquiry</span><h2>{selected.customerName}</h2></div><StatusBadge>{selected.status}</StatusBadge></div>
              <dl className="detail-list wide-list">
                <div><dt>Phone</dt><dd>{selected.phone || 'Not provided'}</dd></div>
                <div><dt>Property type</dt><dd>{selected.propertyType || 'Not provided'}</dd></div>
                <div><dt>Area size</dt><dd>{selected.areaSize ? `${selected.areaSize} m²` : 'Not provided'}</dd></div>
                <div><dt>Budget</dt><dd>{selected.budget ? `$${Number(selected.budget).toLocaleString()}` : 'Not provided'}</dd></div>
                <div><dt>Preferred style</dt><dd>{selected.preferredStyle || 'Not provided'}</dd></div>
                <div><dt>Rooms</dt><dd>{selected.rooms || 'Not provided'}</dd></div>
                <div><dt>Expected completion</dt><dd>{selected.expectedCompletionDate || 'Not provided'}</dd></div>
              </dl>
              <div className="document-grid">
                <div className="document-card"><strong>Floor plan</strong><span>{selected.floorPlanName || 'No file attached'}</span>{selected.floorPlanName && <img src="/floor-plan.svg" alt="Floor plan placeholder" />}</div>
                <div className="document-card"><strong>Inspiration images</strong>{selected.inspirationNames?.length ? selected.inspirationNames.map((name) => <span key={name}>{name}</span>) : <span>No images attached</span>}</div>
              </div>
              <div className="panel inset-panel"><strong>Additional information</strong><p>{selected.additionalInfo || 'No additional information provided.'}</p></div>
              <div className="card-actions">
                <button className="primary-button" onClick={() => updateEnquiryStatus(selected.id, 'accepted')}>Accept enquiry</button>
                <button className="danger-button" onClick={() => updateEnquiryStatus(selected.id, 'declined')}>Decline enquiry</button>
              </div>
              <p className="muted"><small>Assignment assumption: after acceptance, the ID contacts the customer through phone/WhatsApp outside this prototype.</small></p>
            </>
          ) : <div className="empty-state"><h3>Select an enquiry</h3></div>}
        </section>
      </div>
    </div>
  );
}
