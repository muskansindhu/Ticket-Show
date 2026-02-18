import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { apiRequest, formatCurrency } from "../apiClient.js";
import Icon from "../components/Icon.jsx";
import { formatTime12Hour, formatTimeRange } from "../utils/time.js";

export default function ShowDetail() {
  const { showId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [show, setShow] = useState(location.state?.show || null);
  const [venues, setVenues] = useState([]);
  const [selectedVenue, setSelectedVenue] = useState(null);
  const [schedules, setSchedules] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadShow() {
      if (show) return;
      try {
        const data = await apiRequest("/shows/?limit=100");
        const match = data.find((item) => String(item.id) === String(showId));
        setShow(match || null);
      } catch (err) {
        setError(err.message);
      }
    }
    loadShow();
  }, [show, showId]);

  useEffect(() => {
    async function loadVenues() {
      try {
        const data = await apiRequest(`/shows/${showId}/venues`);
        setVenues(data);
      } catch (err) {
        setError(err.message);
      }
    }
    loadVenues();
  }, [showId]);

  async function handleVenueSelect(venue) {
    setSelectedVenue(venue);
    setError("");
    try {
      const data = await apiRequest(
        `/schedules/venue/${venue.id}?show_id=${showId}`
      );
      setSchedules(data);
    } catch (err) {
      setError(err.message);
    }
  }

  function handleScheduleClick(schedule) {
    if (!show || !selectedVenue) return;
    navigate(`/seats/${schedule.id}`, {
      state: { show, venue: selectedVenue, schedule }
    });
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow"><Icon name="ticket" size={14} /> Show detail</p>
          <h2>{show ? show.title : "Show"}</h2>
          <p className="muted">{show?.description || "Select a venue and showtime."}</p>
        </div>
        {show ? (
          <div className="hero-chips">
            <span className="meta-chip"><Icon name="clock" size={12} /> {show.duration_minutes} min</span>
            <span className="meta-chip"><Icon name="credit" size={12} /> {formatCurrency(show.price)}</span>
          </div>
        ) : null}
      </div>
      {error ? <p className="notice">{error}</p> : null}
      <div className="grid-cards">
        <div className="form-card reveal" style={{ "--delay": "0.05s" }}>
          <h3 className="title-row"><Icon name="location" size={16} /> Venues showing this title</h3>
          <div className="list-stack">
            {venues.map((venue) => (
              <button
                key={venue.id}
                type="button"
                className={`venue-option ${selectedVenue?.id === venue.id ? "active" : ""}`}
                onClick={() => handleVenueSelect(venue)}
              >
                <div>
                  <strong>{venue.name}</strong>
                  <p className="muted icon-row"><Icon name="location" size={12} /> {venue.location}</p>
                </div>
                <span className="meta-chip"><Icon name="clock" size={12} /> {formatTimeRange(venue.opening_time, venue.closing_time)}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="form-card reveal" style={{ "--delay": "0.1s" }}>
          <h3 className="title-row"><Icon name="calendar" size={16} /> Schedules</h3>
          {schedules.length === 0 ? (
            <p className="muted">Pick a venue to load showtimes.</p>
          ) : (
            <div className="schedule-grid">
              {schedules.map((schedule) => (
                <button
                  key={schedule.id}
                  type="button"
                  className="schedule-chip"
                  onClick={() => handleScheduleClick(schedule)}
                >
                  <Icon name="clock" size={14} />
                  {formatTime12Hour(schedule.start_time)}
                  <Icon name="arrowRight" size={14} />
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
