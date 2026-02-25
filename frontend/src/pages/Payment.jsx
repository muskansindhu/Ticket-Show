import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import { apiRequest, formatCurrency } from "../apiClient.js";
import { useAuth } from "../context/auth.jsx";
import Icon from "../components/Icon.jsx";
import { formatTime12Hour } from "../utils/time.js";

export default function Payment() {
  const { user } = useAuth();
  const { state } = useLocation();
  const navigate = useNavigate();
  const booking = state?.booking;
  const show = state?.show;
  const venue = state?.venue;
  const schedule = state?.schedule;
  const amount = state?.amount || booking?.total_amount || 0;
  const seatCount = booking?.seat_ids?.length || 0;
  const scheduleLabel = schedule?.start_time
    ? formatTime12Hour(schedule.start_time)
    : "--";

  const [form] = useState({
    booking_id: booking?.id || "",
    amount,
    payment_method: "DODO",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handlePay(event) {
    event.preventDefault();
    if (!booking) {
      setError("Missing booking details. Please start again.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await apiRequest("/payments", {
        method: "POST",
        body: JSON.stringify({
          booking_id: Number(form.booking_id),
          amount: Number(form.amount),
          payment_method: form.payment_method,
          user_id: user?.id || 0,
        }),
      });
      if (response?.checkout_url) {
        window.location.assign(response.checkout_url);
        return;
      }
      navigate("/bookings", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">
            <Icon name="credit" size={14} /> Secure payment
          </p>
          <h2>Payment</h2>
          <p className="muted">Confirm payment to finish the booking.</p>
        </div>
      </div>
      <div className="grid-cards payment-shell">
        <form
          className="form-card payment-form reveal"
          style={{ "--delay": "0.06s" }}
          onSubmit={handlePay}
        >
          <div className="payment-form-head">
            <h3 className="title-row">
              <Icon name="wallet" size={16} /> Checkout details
            </h3>
            <span className="status-pill pending">Secure session</span>
          </div>
          <div className="payment-info-grid">
            <label>
              Booking ID
              <div className="input-wrap">
                <Icon name="ticket" size={16} className="input-icon" />
                <input type="number" value={form.booking_id} readOnly />
              </div>
            </label>
            <label>
              Amount payable
              <div className="input-wrap">
                <Icon name="credit" size={16} className="input-icon" />
                <input
                  type="text"
                  value={formatCurrency(form.amount)}
                  readOnly
                />
              </div>
            </label>
          </div>
          <label>
            Payment provider
            <div className="input-wrap">
              <Icon name="wallet" size={16} className="input-icon" />
              <input type="text" value="Dodo Payments" readOnly />
            </div>
          </label>
          <div className="payment-trust muted">
            <span className="icon-row">
              <Icon name="lock" size={13} /> Dodo secure hosted checkout
            </span>
            <span className="icon-row">
              <Icon name="ticket" size={13} /> Booking confirms after webhook
            </span>
          </div>
          <button className="primary" type="submit" disabled={loading}>
            {loading ? "Processing..." : `Proceed to pay ${formatCurrency(form.amount)}`}
          </button>
          {error ? <p className="notice">{error}</p> : null}
        </form>
        <div
          className="form-card payment-summary reveal"
          style={{ "--delay": "0.12s" }}
        >
          <h3 className="title-row">
            <Icon name="ticket" size={16} /> Order summary
          </h3>
          <div className="payment-summary-list">
            <div className="payment-summary-row">
              <span className="muted">Movie</span>
              <strong>{show?.title || "--"}</strong>
            </div>
            <div className="payment-summary-row">
              <span className="muted">Venue</span>
              <strong>{venue?.name || "--"}</strong>
            </div>
            <div className="payment-summary-row">
              <span className="muted">Show time</span>
              <strong>{scheduleLabel}</strong>
            </div>
            <div className="payment-summary-row">
              <span className="muted">Seats</span>
              <strong>{seatCount}</strong>
            </div>
          </div>
          <div className="payment-total">
            <span className="muted">Total payable</span>
            <strong>{formatCurrency(amount)}</strong>
          </div>
          <p className="muted">
            You will be redirected to Dodo checkout and then back to your bookings.
          </p>
        </div>
      </div>
    </section>
  );
}
