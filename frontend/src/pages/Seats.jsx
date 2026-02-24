import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import {
  apiRequest,
  formatCurrency,
  makeIdempotencyKey,
} from "../apiClient.js";
import Icon from "../components/Icon.jsx";
import { formatTime12Hour } from "../utils/time.js";
import poster1 from "../assets/posters/poster-1.jpg";
import poster2 from "../assets/posters/poster-2.jpg";
import poster3 from "../assets/posters/poster-3.jpg";
import poster4 from "../assets/posters/poster-4.jpg";

const posters = [poster1, poster2, poster3, poster4];

export default function Seats() {
  const { scheduleId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const show = location.state?.show;
  const venue = location.state?.venue;
  const schedule = location.state?.schedule;

  const [seats, setSeats] = useState([]);
  const [selected, setSelected] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadSeats() {
      setLoading(true);
      try {
        const data = await apiRequest(`/bookings/schedule/${scheduleId}/seats`);
        if (Array.isArray(data)) {
          setSeats(data);
          setError("");
        } else {
          setSeats([]);
          setError("Seat data is unavailable for this schedule.");
        }
      } catch (err) {
        setSeats([]);
        setError(err.message || "Unable to load seats.");
      } finally {
        setLoading(false);
      }
    }
    loadSeats();
  }, [scheduleId]);

  const grouped = useMemo(() => {
    const map = new Map();
    seats.forEach((seat) => {
      const row = seat.row_number || "";
      if (!map.has(row)) map.set(row, []);
      map.get(row).push(seat);
    });
    map.forEach((rowSeats, row) => {
      rowSeats.sort((a, b) => Number(a.seat_number) - Number(b.seat_number));
      map.set(row, rowSeats);
    });
    return Array.from(map.entries());
  }, [seats]);

  function toggleSeat(seat) {
    if (!seat.is_available) return;
    setSelected((prev) =>
      prev.some((item) => item.id === seat.id)
        ? prev.filter((item) => item.id !== seat.id)
        : [...prev, seat],
    );
  }

  async function handleBooking() {
    if (selected.length === 0) return;
    setError("");
    try {
      const payload = {
        schedule_id: Number(scheduleId),
        seat_ids: selected.map((seat) => seat.id),
        idempotency_key: makeIdempotencyKey(),
      };
      const booking = await apiRequest("/bookings", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      const amount = (show?.price || 0) * selected.length;
      navigate("/payment", {
        state: { booking, amount, show, venue, schedule },
      });
    } catch (err) {
      setError(err.message);
    }
  }

  const total = (show?.price || 0) * selected.length;
  const scheduleDate = schedule?.start_time
    ? new Date(schedule.start_time)
    : null;
  const scheduleLabel = schedule?.start_time
    ? formatTime12Hour(schedule.start_time)
    : "";
  const scheduleYear = scheduleDate ? scheduleDate.getFullYear() : "";
  const heroPoster =
    posters[(Number(show?.id || scheduleId) || 0) % posters.length];

  return (
    <section className="page seat-page">
      {error ? <p className="notice">{error}</p> : null}
      <div className="seat-shell">
        <aside className="seat-info reveal" style={{ "--delay": "0.06s" }}>
          <div className="seat-info__header">
            <div className="seat-poster">
              <img src={heroPoster} alt={show?.title || "Show poster"} />
              <div className="poster-play">
                <Icon name="play" size={16} />
              </div>
            </div>
            <div className="seat-details">
              <p className="eyebrow">
                <Icon name="film" size={14} /> Seat booking
              </p>
              <h2>{show?.title || "Show"}</h2>
              <div className="seat-meta">
                {scheduleYear ? <span>{scheduleYear}</span> : null}
                {show?.duration_minutes ? (
                  <span>{show.duration_minutes} min</span>
                ) : null}
                {venue?.name ? <span>{venue.name}</span> : null}
              </div>
              <p className="muted">
                {show?.description || "Select seats and confirm your booking."}
              </p>
            </div>
          </div>

          <div className="seat-info__section">
            <p className="section-title">Selected time</p>
            <div className="time-chip">
              <Icon name="clock" size={14} />
              <span>{scheduleLabel || "Schedule not selected"}</span>
            </div>
          </div>

          <div className="seat-info__section">
            <p className="section-title">Selected tickets</p>
            <div className="ticket-list">
              <p className="ticket-quantity">
                {selected.length} {selected.length === 1 ? "seat" : "seats"}{" "}
                selected
              </p>
              <p className="muted">
                Seat and row details are shown on the final ticket after
                booking.
              </p>
            </div>
          </div>

          <div className="seat-info__footer">
            <div>
              <p className="section-title">Total</p>
              <p className="total-amount">{formatCurrency(total)}</p>
            </div>
            <button
              className="primary"
              type="button"
              onClick={handleBooking}
              disabled={selected.length === 0}
            >
              Buy tickets
            </button>
          </div>
        </aside>

        <div className="seat-map reveal" style={{ "--delay": "0.1s" }}>
          <div className="seat-map__top">
            <div>
              <p className="eyebrow">
                <Icon name="seat" size={14} /> Choose seats
              </p>
              <h3>Seating</h3>
            </div>
            <div className="legend">
              <span>
                <i className="dot selected"></i>Selected
              </span>
              <span>
                <i className="dot available"></i>Available
              </span>
              <span>
                <i className="dot booked"></i>Booked
              </span>
            </div>
          </div>
          <div className="screen-arc">
            <span>SCREEN</span>
          </div>
          {loading ? (
            <p className="muted">Loading seats...</p>
          ) : grouped.length === 0 ? (
            <p className="muted">
              No seats are configured for this screen yet.
            </p>
          ) : (
            <div className="seat-grid">
              {grouped.map(([row, rowSeats]) => (
                <div className="seat-row" key={row}>
                  <span className="row-label row-label-left">{row}</span>
                  <div className="seat-row-grid">
                    {rowSeats.map((seat) => {
                      const isSelected = selected.some(
                        (item) => item.id === seat.id,
                      );
                      const className = seat.is_booked
                        ? "seat booked"
                        : seat.is_locked
                          ? "seat locked"
                          : isSelected
                            ? "seat selected"
                            : "seat";
                      return (
                        <button
                          key={seat.id}
                          type="button"
                          className={className}
                          onClick={() => toggleSeat(seat)}
                        >
                          {seat.seat_number}
                        </button>
                      );
                    })}
                  </div>
                  <span className="row-label row-label-right">{row}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
