import { useMemo, useState } from 'react';
import FieldError from '../../components/FieldError';
import ProjectCard from '../../components/ProjectCard';
import { useApp } from '../../context/AppContext';
import { isFutureOrToday, isPhone, isPositiveNumber, isRequired, minLength, validateFiles } from '../../utils/validation';

export default function DesignerProfilePage({ designerId, go, openProject }) {
  const {
    designers, projects, packages, reviews, favouriteDesignerIds, toggleFavouriteDesigner,
    submitEnquiry, bookConsultation, submitReview, reportCompany, user,
  } = useApp();
  const designer = designers.find((item) => item.id === designerId);
  const designerProjects = projects.filter((item) => item.designerId === designerId && item.published);
  const designerPackages = packages.filter((item) => item.designerId === designerId);
  const designerReviews = reviews.filter((item) => item.designerId === designerId);
  const saved = favouriteDesignerIds.includes(designerId);

  const [enquiry, setEnquiry] = useState({ propertyType: '', areaSize: '', budget: '', name: user?.name || '', phone: user?.phone || '', additionalInfo: '' });
  const [enquiryImages, setEnquiryImages] = useState([]);
  const [enquiryErrors, setEnquiryErrors] = useState({});
  const [enquirySuccess, setEnquirySuccess] = useState('');
  const [consultation, setConsultation] = useState({ date: '', time: '', mode: 'In-person' });
  const [consultErrors, setConsultErrors] = useState({});
  const [consultSuccess, setConsultSuccess] = useState('');
  const [review, setReview] = useState({ rating: '5', text: '' });
  const [reviewError, setReviewError] = useState('');
  const [reviewSuccess, setReviewSuccess] = useState('');
  const [report, setReport] = useState({ reason: '', details: '' });
  const [reportErrors, setReportErrors] = useState({});
  const [reportSuccess, setReportSuccess] = useState('');

  const averageRating = useMemo(() => {
    if (!designerReviews.length) return 0;
    return (designerReviews.reduce((sum, item) => sum + Number(item.rating), 0) / designerReviews.length).toFixed(1);
  }, [designerReviews]);

  if (!designer) return <div className="page-shell"><div className="empty-state panel"><h2>Designer not found</h2></div></div>;

  async function sendEnquiry(event) {
    event.preventDefault();
    const errors = {};
    if (!isRequired(enquiry.propertyType)) errors.propertyType = 'Property type is required.';
    if (!isPositiveNumber(enquiry.areaSize)) errors.areaSize = 'Area size must be greater than 0.';
    if (!isPositiveNumber(enquiry.budget)) errors.budget = 'Budget must be greater than 0.';
    if (!isRequired(enquiry.name)) errors.name = 'Name is required.';
    if (!isPhone(enquiry.phone)) errors.phone = 'Enter a valid phone number.';
    const imageError = validateFiles(enquiryImages, { imagesOnly: true, maxFiles: 5 });
    if (imageError) errors.images = imageError;
    setEnquiryErrors(errors);
    if (Object.keys(errors).length) return;

    // === BACKEND INTEGRATION === Images require FormData/multipart upload to Python.
    await submitEnquiry({
      ...enquiry,
      designerId,
      areaSize: Number(enquiry.areaSize),
      budget: Number(enquiry.budget),
      inspirationNames: Array.from(enquiryImages).map((file) => file.name),
      floorPlanName: '',
    });
    setEnquirySuccess(`${designer.companyName} will contact you soon regarding your quotation request.`);
  }

  async function sendConsultation(event) {
    event.preventDefault();
    const errors = {};
    if (!isFutureOrToday(consultation.date)) errors.date = 'Choose today or a future date.';
    if (!isRequired(consultation.time)) errors.time = 'Select a consultation time.';
    setConsultErrors(errors);
    if (Object.keys(errors).length) return;
    await bookConsultation({ ...consultation, designerId });
    setConsultSuccess('Consultation request submitted. The company can accept or reschedule it from their portal.');
  }

  async function sendReview(event) {
    event.preventDefault();
    if (!minLength(review.text, 10)) {
      setReviewError('Please write at least 10 characters.');
      return;
    }
    setReviewError('');
    await submitReview({ designerId, rating: Number(review.rating), text: review.text });
    setReviewSuccess('Review submitted successfully.');
    setReview({ rating: '5', text: '' });
  }

  async function sendReport(event) {
    event.preventDefault();
    const errors = {};
    if (!isRequired(report.reason)) errors.reason = 'Select a reason.';
    if (!minLength(report.details, 15)) errors.details = 'Please provide at least 15 characters of details.';
    setReportErrors(errors);
    if (Object.keys(errors).length) return;
    await reportCompany({ designerId, ...report });
    setReportSuccess('Report submitted to platform management for review.');
    setReport({ reason: '', details: '' });
  }

  return (
    <div className="page-shell">
      <button className="text-button" onClick={() => go(user ? 'customer-designers' : 'landing')}>← Back to designers</button>
      <section className="company-hero panel">
        <img src={designer.logo} alt={`${designer.companyName} logo placeholder`} />
        <div>
          <span className="eyebrow">Verified interior design company</span>
          <h1>{designer.companyName}</h1>
          <p>{designer.description}</p>
          <div className="tag-row">{designer.specialties.map((item) => <span className="tag" key={item}>{item}</span>)}</div>
          <div className="company-meta"><span>★ {averageRating || designer.rating}</span><span>{designer.yearsExperience} years experience</span><span>{designer.location}</span></div>
          {user?.role === 'customer' ? <button className="secondary-button" onClick={() => toggleFavouriteDesigner(designer.id)}>{saved ? 'Remove favourite designer' : 'Save favourite designer'}</button> : !user ? <button className="secondary-button" onClick={() => go('login')}>Log in to save / enquire</button> : null}
        </div>
      </section>

      <section className="section-block"><div className="section-heading"><div><span className="eyebrow">Company information</span><h2>Services and specialties</h2></div></div><div className="info-grid"><div className="panel info-card"><strong>Services</strong>{designer.services.map((item) => <span key={item}>• {item}</span>)}</div><div className="panel info-card"><strong>Property types served</strong>{(designer.propertyTypes || []).map((item) => (<span key={item}>• {item}</span>))}</div><div className="panel info-card"><strong>Renovation categories</strong>{(designer.categoriesServed || []).map((item) => (<span key={item}>• {item}</span>))}</div>
      <div className="panel info-card"><strong>Typical budget</strong><span>${designer.budgetMin.toLocaleString()} – ${designer.budgetMax.toLocaleString()}</span><span>{designer.contactEmail}</span><span>{designer.phone}</span></div></div></section>

      {!user && <div className="alert warning-alert section-block">Browsing is public. Log in as a homeowner before submitting enquiries, consultations, reviews or reports in a real implementation.</div>}

      <section className="section-block"><div className="section-heading"><div><span className="eyebrow">Portfolio</span><h2>Previous renovation projects</h2></div></div><div className="card-grid">{designerProjects.map((project) => <ProjectCard key={project.id} project={project} onView={openProject} />)}</div></section>

      <section className="section-block"><div className="section-heading"><div><span className="eyebrow">Packages</span><h2>Renovation packages</h2></div></div><div className="card-grid">{designerPackages.map((item) => <article className="card package-card" key={item.id}><div className="card-body"><span className="card-kicker">{item.renovationType}</span><h3>{item.name}</h3><div className="package-price">${item.price.toLocaleString()}</div><p>{item.description}</p><div className="tag-row">{item.services.map((service) => <span className="tag" key={service}>{service}</span>)}</div></div></article>)}</div></section>

      <section className="two-panel-grid section-block">
        <form className="panel form-card" onSubmit={sendEnquiry} noValidate>
          <span className="eyebrow">Quotation / enquiry</span><h2>Request a quotation</h2>
          <div className="two-column-form">
            <label>Property type<input value={enquiry.propertyType} onChange={(e) => setEnquiry({ ...enquiry, propertyType: e.target.value })} placeholder="4-Room HDB" /><FieldError message={enquiryErrors.propertyType} /></label>
            <label>Area size (m²)<input type="number" min="1" value={enquiry.areaSize} onChange={(e) => setEnquiry({ ...enquiry, areaSize: e.target.value })} /><FieldError message={enquiryErrors.areaSize} /></label>
            <label>Budget (SGD)<input type="number" min="1" value={enquiry.budget} onChange={(e) => setEnquiry({ ...enquiry, budget: e.target.value })} /><FieldError message={enquiryErrors.budget} /></label>
            <label>Name<input value={enquiry.name} onChange={(e) => setEnquiry({ ...enquiry, name: e.target.value })} /><FieldError message={enquiryErrors.name} /></label>
            <label className="span-2">Phone number<input value={enquiry.phone} onChange={(e) => setEnquiry({ ...enquiry, phone: e.target.value })} /><FieldError message={enquiryErrors.phone} /></label>
          </div>
          <label>Reference image uploads<input type="file" accept="image/*" multiple onChange={(e) => setEnquiryImages(e.target.files)} /><FieldError message={enquiryErrors.images} /><small>Prototype stores file names only. Backend will upload the actual files.</small></label>
          <label>Additional information<textarea rows="4" value={enquiry.additionalInfo} onChange={(e) => setEnquiry({ ...enquiry, additionalInfo: e.target.value })} /></label>
          <button className="primary-button" type="submit">Send quotation request</button>
          {enquirySuccess && <div className="alert success-alert">{enquirySuccess}</div>}
        </form>

        <form className="panel form-card" onSubmit={sendConsultation} noValidate>
          <span className="eyebrow">Appointment</span><h2>Book consultation</h2>
          <label>Date<input type="date" value={consultation.date} onChange={(e) => setConsultation({ ...consultation, date: e.target.value })} /><FieldError message={consultErrors.date} /></label>
          <label>Time<input type="time" value={consultation.time} onChange={(e) => setConsultation({ ...consultation, time: e.target.value })} /><FieldError message={consultErrors.time} /></label>
          <label>Mode<select value={consultation.mode} onChange={(e) => setConsultation({ ...consultation, mode: e.target.value })}><option>In-person</option><option>Video Call</option><option>Phone Call</option></select></label>
          <button className="primary-button" type="submit">Request consultation</button>
          {consultSuccess && <div className="alert success-alert">{consultSuccess}</div>}
        </form>
      </section>

      <section className="section-block"><div className="section-heading"><div><span className="eyebrow">Customer experiences</span><h2>Reviews</h2></div></div><div className="review-list">{designerReviews.map((item) => <article className="panel review-card" key={item.id}><div><strong>{item.customerName}</strong><span className="rating-line">{'★'.repeat(item.rating)}{'☆'.repeat(5-item.rating)}</span></div><p>{item.text}</p>{item.response && <div className="designer-response"><strong>Company response</strong><p>{item.response}</p></div>}</article>)}</div></section>

      <section className="two-panel-grid section-block">
        <form className="panel form-card" onSubmit={sendReview} noValidate>
          <span className="eyebrow">Assignment prototype</span><h2>Submit review</h2><p className="muted">For assignment purposes, the completion restriction is not enforced.</p>
          <label>Rating<select value={review.rating} onChange={(e) => setReview({ ...review, rating: e.target.value })}>{[5,4,3,2,1].map((n) => <option key={n} value={n}>{n} star{n > 1 ? 's' : ''}</option>)}</select></label>
          <label>Review<textarea rows="4" value={review.text} onChange={(e) => setReview({ ...review, text: e.target.value })} /></label><FieldError message={reviewError} />
          <button className="primary-button" type="submit">Submit review</button>{reviewSuccess && <div className="alert success-alert">{reviewSuccess}</div>}
        </form>

        <form className="panel form-card" onSubmit={sendReport} noValidate>
          <span className="eyebrow">Safety</span><h2>Report company</h2>
          <label>Reason<select value={report.reason} onChange={(e) => setReport({ ...report, reason: e.target.value })}><option value="">Select reason</option><option>Fraudulent behaviour</option><option>Misleading advertisement</option><option>Inappropriate conduct</option><option>Other</option></select><FieldError message={reportErrors.reason} /></label>
          <label>Details<textarea rows="4" value={report.details} onChange={(e) => setReport({ ...report, details: e.target.value })} /><FieldError message={reportErrors.details} /></label>
          <button className="danger-button" type="submit">Submit report</button>{reportSuccess && <div className="alert success-alert">{reportSuccess}</div>}
        </form>
      </section>
    </div>
  );
}
