import { useEffect, useState } from "react";
import { apiRequest, formatCurrency, makeIdempotencyKey, parseSeatIds } from "../apiClient.js";

export default function Bookings() {
  const [bookings, setBookings] = useState([]);
  const [form, setForm] = useState({ scheduleId: "", seatIds: "" });
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

  async function handleCreate(event) {
    event.preventDefault();
    setError("");
    try {
      const payload = {
        schedule_id: Number(form.scheduleId),
        seat_ids: parseSeatIds(form.seatIds),
        idempotency_key: makeIdempotencyKey()
      };
      const booking = await apiRequest("/bookings", {
        method: "POST",
        body: JSON.stringify(payload)
      });
      setBookings((prev) => [booking, ...prev]);
      setForm({ scheduleId: "", seatIds: "" });
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleCancel(id) {
    setError("");
    try {
      await apiRequest(`/bookings/${id}`, { method: "DELETE" });
      setBookings((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h2>Bookings</h2>
          <p>Create and manage reservations in one place.</p>
        </div>
      </div>
      <div className="grid-cards">
        <form className="form-card" onSubmit={handleCreate}>
          <h3>Create booking</h3>
          <label>
            Schedule ID
            <input
              type="number"
              value={form.scheduleId}
              onChange={(event) => setForm({ ...form, scheduleId: event.target.value })}
              required
            />
          </label>
          <label>
            Seat IDs (comma-separated)
            <input
              value={form.seatIds}
              onChange={(event) => setForm({ ...form, seatIds: event.target.value })}
              required
            />
          </label>
          <button className="primary" type="submit">Reserve seats</button>
          {error ? <p className="notice">{error}</p> : null}
        </form>
        <div className="list-stack">
          {bookings.map((booking) => (
            <div className="booking-card" key={booking.id}>
              <div>
                <h4>Booking #{booking.id}</h4>
                <p>Status: {booking.status}</p>
              </div>
              <div className="booking-meta">
                <span>Schedule {booking.schedule_id}</span>
                <span>{formatCurrency(booking.total_amount)}</span>
              </div>
              <button className="ghost" type="button" onClick={() => handleCancel(booking.id)}>
                Cancel booking
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
