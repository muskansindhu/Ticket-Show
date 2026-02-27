import { useEffect, useState } from "react";
import { apiRequest, formatCurrency } from "../apiClient.js";
import Icon from "../components/Icon.jsx";
import { formatTime12Hour } from "../utils/time.js";

function formatDateLabel(value) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  });
}

function formatDateTimeLabel(value) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  return `${formatDateLabel(date)} · ${formatTime12Hour(value)}`;
}

function isNotFoundError(err) {
  const message = String(err?.message || "").toLowerCase();
  return message.includes("not found") || message.includes("404");
}

function getRefundDestinationNote(paymentDetail, bookingDetail) {
  if (!paymentDetail) return "";

  const paymentMethod = String(paymentDetail.payment_method || "").toUpperCase();
  const paymentStatus = String(paymentDetail.status || "").toUpperCase();
  const bookingStatus = String(bookingDetail?.status || "").toUpperCase();
  const isRefundFlow =
    paymentStatus === "REFUND_INITIATED" ||
    paymentStatus === "REFUNDED" ||
    (bookingStatus === "CANCELLED" && paymentStatus === "COMPLETED");

  if (!isRefundFlow) return "";

  if (paymentMethod === "DODO") {
    if (paymentStatus === "REFUNDED") {
      return "Refund sent to your original payment method.";
    }
    if (paymentStatus === "REFUND_INITIATED") {
      return "Refund is in progress to your original payment method.";
    }
    return "Booking is cancelled. Any refund will be sent to your original payment method.";
  }

  if (paymentStatus === "REFUNDED") {
    return "Refund credited to your Ticket Show wallet.";
  }
  if (paymentStatus === "REFUND_INITIATED") {
    return "Refund is in progress to your Ticket Show wallet.";
  }
  return "Booking is cancelled. Refund will be processed based on your payment method.";
}

export default function Bookings() {
  const [bookings, setBookings] = useState([]);
  const [expandedBookingId, setExpandedBookingId] = useState(null);
  const [detailsByBookingId, setDetailsByBookingId] = useState({});
  const [loadingDetailsId, setLoadingDetailsId] = useState(null);
  const [cancellingBookingId, setCancellingBookingId] = useState(null);
  const [pendingCancelId, setPendingCancelId] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await apiRequest("/bookings");
        setBookings(data);
      } catch (err) {
        setError(err.message);
      }
    }
    load();
  }, []);

  async function loadBookingDetails(bookingId) {
    if (!bookingId || detailsByBookingId[bookingId]) return;
    setLoadingDetailsId(bookingId);
    try {
      const [bookingResult, paymentResult] = await Promise.allSettled([
        apiRequest(`/bookings/${bookingId}`),
        apiRequest(`/payments/booking/${bookingId}`)
      ]);

      const nextDetail = {};
      if (bookingResult.status === "fulfilled") {
        nextDetail.booking = bookingResult.value;
      } else {
        nextDetail.bookingError = bookingResult.reason?.message || "Unable to load booking details.";
      }

      if (paymentResult.status === "fulfilled") {
        nextDetail.payment = paymentResult.value;
      } else if (!isNotFoundError(paymentResult.reason)) {
        nextDetail.paymentError = paymentResult.reason?.message || "Unable to load payment details.";
      }

      setDetailsByBookingId((prev) => ({
        ...prev,
        [bookingId]: nextDetail
      }));
    } finally {
      setLoadingDetailsId((current) => (current === bookingId ? null : current));
    }
  }

  function handleToggleDetails(bookingId) {
    setExpandedBookingId((current) => (current === bookingId ? null : bookingId));
    if (!detailsByBookingId[bookingId]) {
      loadBookingDetails(bookingId);
    }
  }

  function canCancelBooking(status) {
    return status === "PENDING" || status === "CONFIRMED";
  }

  function promptCancelBooking(bookingId) {
    setPendingCancelId(bookingId);
  }

  function dismissCancelModal() {
    setPendingCancelId(null);
  }

  async function confirmCancelBooking() {
    const bookingId = pendingCancelId;
    if (!bookingId) return;
    setPendingCancelId(null);
    setError("");
    setCancellingBookingId(bookingId);
    try {
      await apiRequest(`/bookings/${bookingId}`, { method: "DELETE" });
      setBookings((prev) =>
        prev.map((item) =>
          item.id === bookingId ? { ...item, status: "CANCELLED" } : item
        )
      );
      setDetailsByBookingId((prev) => ({
        ...prev,
        [bookingId]: {
          ...(prev[bookingId] || {}),
          booking: {
            ...(prev[bookingId]?.booking || {}),
            id: bookingId,
            status: "CANCELLED",
          },
        },
      }));
    } catch (err) {
      setError(err.message);
    } finally {
      setCancellingBookingId(null);
    }
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow"><Icon name="ticket" size={14} /> Bookings</p>
          <h2>My bookings</h2>
          <p className="muted">Your booking history and status.</p>
        </div>
      </div>
      {error ? <p className="notice">{error}</p> : null}
      <div className="list-stack booking-list">
        {bookings.length === 0 ? <p className="muted">No bookings yet.</p> : null}
        {bookings.map((booking, index) => {
          const statusClass = `status-pill ${String(booking.status || "pending").toLowerCase()}`;
          const isExpanded = expandedBookingId === booking.id;
          const detail = detailsByBookingId[booking.id];
          const bookingDetail = detail?.booking || booking;
          const paymentDetail = detail?.payment || null;
          const refundDestinationNote = getRefundDestinationNote(paymentDetail, bookingDetail);
          const seatIds = Array.isArray(bookingDetail.seat_ids) ? bookingDetail.seat_ids : [];
          const isLoadingDetails = loadingDetailsId === booking.id;

          return (
            <article
              className={`booking-card booking-record reveal ${isExpanded ? "expanded" : ""}`}
              style={{ "--delay": `${index * 0.05}s` }}
              key={booking.id}
            >
              <button
                className="booking-summary-btn"
                type="button"
                onClick={() => handleToggleDetails(booking.id)}
                aria-expanded={isExpanded}
                aria-controls={`booking-details-${booking.id}`}
              >
                <div className="booking-header">
                  <div className="booking-title">
                    <Icon name="ticket" size={16} />
                    <h4>Booking #{booking.id}</h4>
                  </div>
                  <span className={statusClass}>{booking.status || "PENDING"}</span>
                </div>
                <div className="booking-meta booking-summary-meta">
                  <span className="icon-inline"><Icon name="calendar" size={14} /> Schedule {booking.schedule_id}</span>
                  <span className="icon-inline"><Icon name="seat" size={14} /> {seatIds.length} seat{seatIds.length === 1 ? "" : "s"}</span>
                  <span className="icon-inline"><Icon name="credit" size={14} /> {formatCurrency(booking.total_amount)}</span>
                </div>
                <p className="muted booking-summary-hint">
                  {isExpanded ? "Hide booking details" : "View booking details"}
                </p>
              </button>

              {isExpanded ? (
                <div className="booking-details" id={`booking-details-${booking.id}`}>
                  {isLoadingDetails ? <p className="muted">Loading booking details...</p> : null}
                  {detail?.bookingError ? <p className="notice">{detail.bookingError}</p> : null}

                  <div className="booking-detail-grid">
                    <div className="booking-detail-item">
                      <span className="section-title">Booking ID</span>
                      <strong>#{bookingDetail.id ?? booking.id}</strong>
                    </div>
                    <div className="booking-detail-item">
                      <span className="section-title">Schedule ID</span>
                      <strong>{bookingDetail.schedule_id ?? booking.schedule_id ?? "--"}</strong>
                    </div>
                    <div className="booking-detail-item">
                      <span className="section-title">Amount</span>
                      <strong>{formatCurrency((bookingDetail.total_amount ?? booking.total_amount) ?? 0)}</strong>
                    </div>
                    <div className="booking-detail-item">
                      <span className="section-title">Booked On</span>
                      <strong>{formatDateTimeLabel(bookingDetail.created_at)}</strong>
                    </div>
                    <div className="booking-detail-item">
                      <span className="section-title">Seat IDs</span>
                      <strong>{seatIds.length > 0 ? seatIds.join(", ") : "--"}</strong>
                    </div>
                  </div>

                  <div className="booking-payment-block">
                    <p className="section-title">Payment</p>
                    {paymentDetail ? (
                      <div className="booking-payment-grid">
                        <span className="icon-inline"><Icon name="wallet" size={13} /> {paymentDetail.payment_method || "--"}</span>
                        <span className="icon-inline"><Icon name="credit" size={13} /> {formatCurrency(paymentDetail.amount)}</span>
                        <span className={`status-pill ${String(paymentDetail.status || "pending").toLowerCase()}`}>
                          {paymentDetail.status || "PENDING"}
                        </span>
                        <span className="muted">Txn: {paymentDetail.transaction_id || "--"}</span>
                      </div>
                    ) : detail?.paymentError ? (
                      <p className="notice">{detail.paymentError}</p>
                    ) : (
                      <p className="muted">Payment not completed yet.</p>
                    )}
                    {refundDestinationNote ? (
                      <p className="booking-refund-note">{refundDestinationNote}</p>
                    ) : null}
                  </div>
                  {canCancelBooking(bookingDetail.status || booking.status) ? (
                    <div className="booking-actions-row">
                      <button
                        className="ghost"
                        type="button"
                        onClick={() => promptCancelBooking(booking.id)}
                        disabled={cancellingBookingId === booking.id}
                      >
                        {cancellingBookingId === booking.id
                          ? "Cancelling..."
                          : "Cancel booking"}
                      </button>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </article>
          );
        })}
      </div>

      {pendingCancelId !== null ? (
        <div
          className="modal-backdrop"
          role="presentation"
          onClick={dismissCancelModal}
        >
          <div
            className="confirm-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="cancel-booking-title"
            onClick={(event) => event.stopPropagation()}
          >
            <h3 id="cancel-booking-title">Cancel Booking #{pendingCancelId}?</h3>
            <p className="muted">
              This will cancel your booking and initiate a refund if applicable.
            </p>
            <div className="confirm-modal-actions">
              <button
                className="ghost"
                type="button"
                onClick={dismissCancelModal}
              >
                Keep Booking
              </button>
              <button
                className="primary danger-btn"
                type="button"
                onClick={confirmCancelBooking}
              >
                Cancel Booking
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
