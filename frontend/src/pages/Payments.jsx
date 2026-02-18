import { useState } from "react";
import { apiRequest, formatCurrency } from "../apiClient.js";
import { useAuth } from "../context/auth.jsx";

export default function Payments() {
  const { user } = useAuth();
  const [form, setForm] = useState({ bookingId: "", amount: "", paymentMethod: "CARD" });
  const [payment, setPayment] = useState(null);
  const [error, setError] = useState("");

  async function handlePayment(event) {
    event.preventDefault();
    setError("");
    try {
      const payload = {
        booking_id: Number(form.bookingId),
        amount: Number(form.amount),
        payment_method: form.paymentMethod,
        user_id: user?.id || 0
      };
      const result = await apiRequest("/payments", {
        method: "POST",
        body: JSON.stringify(payload)
      });
      setPayment(result);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h2>Payments</h2>
          <p>Capture payment and confirm tickets.</p>
        </div>
      </div>
      <div className="grid-cards">
        <form className="form-card" onSubmit={handlePayment}>
          <label>
            Booking ID
            <input
              type="number"
              value={form.bookingId}
              onChange={(event) => setForm({ ...form, bookingId: event.target.value })}
              required
            />
          </label>
          <label>
            Amount
            <input
              type="number"
              step="0.01"
              value={form.amount}
              onChange={(event) => setForm({ ...form, amount: event.target.value })}
              required
            />
          </label>
          <label>
            Payment method
            <select
              value={form.paymentMethod}
              onChange={(event) => setForm({ ...form, paymentMethod: event.target.value })}
            >
              <option value="CARD">Card</option>
              <option value="UPI">UPI</option>
              <option value="NETBANKING">Netbanking</option>
              <option value="WALLET">Wallet</option>
            </select>
          </label>
          <button className="primary" type="submit">Confirm payment</button>
          {error ? <p className="notice">{error}</p> : null}
        </form>
        <div className="form-card">
          <h3>Latest payment</h3>
          {payment ? (
            <div className="payment-card">
              <p>Payment #{payment.id}</p>
              <p>{formatCurrency(payment.amount)} · {payment.status}</p>
              <p>Method: {payment.payment_method}</p>
            </div>
          ) : (
            <p className="muted">No payment submitted yet.</p>
          )}
        </div>
      </div>
    </section>
  );
}
