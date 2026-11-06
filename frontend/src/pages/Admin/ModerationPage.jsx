import PageHeader from '../../components/PageHeader';
import { useApp } from '../../context/AppContext';

export default function ModerationPage() {
  const { reviews, designers, removeReview } = useApp();
  return (
    <div className="page-shell">
      <PageHeader eyebrow="Content moderation" title="Moderate customer reviews" text="Remove inappropriate or fake reviews from the platform." />
      <div className="review-list">{reviews.map((review) => { const designer = designers.find((item) => item.id === review.designerId); return <article className="panel review-card" key={review.id}><div className="review-head"><div><strong>{review.customerName}</strong><span className="rating-line">{'★'.repeat(review.rating)}{'☆'.repeat(5-review.rating)}</span></div><span>{designer?.companyName}</span></div><p>{review.text}</p>{review.response && <div className="designer-response"><strong>Company response</strong><p>{review.response}</p></div>}<button className="danger-button" onClick={() => removeReview(review.id)}>Remove review</button></article>; })}</div>
    </div>
  );
}
