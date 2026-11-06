import { useState } from 'react';
import FieldError from '../../components/FieldError';
import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import { useApp } from '../../context/AppContext';
import { isPositiveNumber, isRequired } from '../../utils/validation';

export default function PaymentsPage() {
  const {
    payments,
    designers,
    user,
    makePayment,
    settleOutstandingInvoice
  } = useApp();
  const [form, setForm] = useState({ designerId: '101', projectName: '', amount: '', type: 'Deposit' });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');
  const [settlingId, setSettlingId] = useState(null);
  const [paymentError, setPaymentError] = useState('');
  const mine = payments.filter((item) => item.customerName === user?.name);

  async function submit(event) {
    event.preventDefault();
    const next = {};
    if (!isRequired(form.designerId)) next.designerId = 'Choose a company.';
    if (!isRequired(form.projectName)) next.projectName = 'Project name is required.';
    if (!isPositiveNumber(form.amount)) next.amount = 'Payment amount must be greater than 0.';
    setErrors(next);
    if (Object.keys(next).length) return;

    // === BACKEND INTEGRATION === Real payment gateway/tokenisation must be handled server-side.
    const payment = await makePayment({ ...form, designerId: Number(form.designerId), amount: Number(form.amount) });
    setMessage(`Mock payment successful. Receipt ${payment.invoiceNo} is now available.`);
    setForm({ ...form, projectName: '', amount: '' });
  }

  async function payOutstanding(payment) {
    setMessage('');
    setPaymentError('');
    setSettlingId(payment.id);

    try {
      const updated = await settleOutstandingInvoice(payment.id);

      setMessage(
        `Mock payment successful. Invoice ${updated.invoiceNo} is now Paid. Receipt available.`
      );
    } catch (error) {
      setPaymentError(
        error.message || 'Unable to settle the invoice.'
      );
    } finally {
      setSettlingId(null);
    }
  }

  function downloadReceipt(payment) {
    const text = `RenovationLink Receipt\n${payment.invoiceNo}\nProject: ${payment.projectName}\nAmount: $${payment.amount}\nStatus: ${payment.status}`;
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${payment.invoiceNo}.txt`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Renovation finance" title="Payments" text="Make a mock deposit or milestone payment, view history and download prototype receipts." />
      <div className="two-panel-grid">
        <form className="panel form-card" onSubmit={submit} noValidate>
          <h2>Make renovation payment</h2>
          <p className="muted">To settle an existing amount owed, use{' '}<strong>Pay outstanding</strong>{' '}in Payment history below.</p>
          <label>Company<select value={form.designerId} onChange={(e) => setForm({ ...form, designerId: e.target.value })}>{designers.filter((d) => d.verified).map((designer) => <option key={designer.id} value={designer.id}>{designer.companyName}</option>)}</select><FieldError message={errors.designerId} /></label>
          <label>Project name<input value={form.projectName} onChange={(e) => setForm({ ...form, projectName: e.target.value })} /><FieldError message={errors.projectName} /></label>
          <label>Payment type<select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}><option>Deposit</option><option>Design Fee</option><option>Renovation Milestone</option><option>Final Payment</option></select></label>
          <label>Amount (SGD)<input type="number" min="1" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /><FieldError message={errors.amount} /></label>
          <div className="mock-payment-box"><strong>Mock payment method</strong><p>No card data is collected in this assignment frontend.</p></div>
          <button className="primary-button" type="submit">Pay now</button>{message && <div className="alert success-alert">{message}</div>}{paymentError && (<div className="alert error-alert" role="alert">{paymentError}</div>)}
        </form>
        <div className="panel info-card payment-summary"><strong>Payment summary</strong><span>Total paid: ${mine.filter((p) => p.status === 'Paid').reduce((s,p) => s+p.amount,0).toLocaleString()}</span><span>Outstanding: ${mine.filter((p) => p.status === 'Outstanding').reduce((s,p) => s+p.amount,0).toLocaleString()}</span><span>{mine.length} payment record(s)</span></div>
      </div>
      <div className="section-heading roomy"><div><h2>Payment history</h2></div></div>
      <div className="table-wrap panel">
        <table>
          <thead>
            <tr>
              <th>Invoice</th>
              <th>Project</th>
              <th>Type</th>
              <th>Amount</th>
              <th>Date</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {mine.map((payment) => (
              <tr key={payment.id}>
                <td>{payment.invoiceNo}</td>
                <td>{payment.projectName}</td>
                <td>{payment.type}</td>
                <td>${payment.amount.toLocaleString()}</td>
                <td>{payment.date}</td>

                <td>
                  <StatusBadge>{payment.status}</StatusBadge>
                </td>

                <td>
                  {payment.status === 'Outstanding' ? (
                    <button
                      type="button"
                      className="text-button"
                      disabled={settlingId !== null}
                      onClick={() => payOutstanding(payment)}
                    >
                      {settlingId === payment.id
                        ? 'Processing...'
                        : `Pay outstanding ($${payment.amount.toLocaleString()})`}
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="text-button"
                      onClick={() => downloadReceipt(payment)}
                    >
                      Download receipt
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
