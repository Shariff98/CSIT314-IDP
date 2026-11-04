import { useMemo, useState } from 'react';
import FieldError from '../../components/FieldError';
import PageHeader from '../../components/PageHeader';
import { useApp } from '../../context/AppContext';
import { minLength } from '../../utils/validation';

export default function DesignerReviewsPage() {
  const { user, reviews, respondReview } = useApp();
  const mine = reviews.filter((item) => item.designerId === (user?.designerId || 101));
  const [responses, setResponses] = useState({});
  const [errors, setErrors] = useState({});
  const average = useMemo(() => mine.length ? (mine.reduce((sum, item) => sum + item.rating, 0) / mine.length).toFixed(1) : '—', [mine]);

  async function reply(id) {
    const value = responses[id] || '';
    if (!minLength(value, 3)) {
      setErrors((current) => ({ ...current, [id]: 'Response must contain at least 3 characters.' }));
      return;
    }
    await respondReview(id, value);
    setResponses((current) => ({ ...current, [id]: '' }));
    setErrors((current) => ({ ...current, [id]: '' }));
  }

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Reputation" title="Company ratings and reviews" text={`Current prototype average: ${average} stars from ${mine.length} review(s).`} />
      <div className="review-list">{mine.map((review) => <article className="panel review-card" key={review.id}><div className="review-head"><div><strong>{review.customerName}</strong><span className="rating-line">{'★'.repeat(review.rating)}{'☆'.repeat(5-review.rating)}</span></div><small>{review.date}</small></div><p>{review.text}</p>{review.response ? <div className="designer-response"><strong>Your response</strong><p>{review.response}</p></div> : <div className="inline-response"><textarea rows="2" value={responses[review.id] || ''} onChange={(e) => setResponses({ ...responses, [review.id]: e.target.value })} placeholder="Write a public response" /><button className="primary-button" onClick={() => reply(review.id)}>Reply</button><FieldError message={errors[review.id]} /></div>}</article>)}</div>
    </div>
  );
}
