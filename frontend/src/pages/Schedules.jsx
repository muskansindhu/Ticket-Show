import { useEffect, useState } from "react";
import { apiRequest, toQuery } from "../apiClient.js";
import { formatTime12Hour } from "../utils/time.js";

export default function Schedules() {
  const [venues, setVenues] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [form, setForm] = useState({ venueId: "", fromDate: "", toDate: "" });
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadVenues() {
      try {
        const data = await apiRequest("/venues/?limit=100");
        setVenues(data);
      } catch (err) {
        setError(err.message);
      }
    }
    loadVenues();
  }, []);

  async function handleSearch(event) {
    event.preventDefault();
    setError("");
    if (!form.venueId) {
      setError("Select a venue to search schedules.");
      return;
    }
    try {
      const query = toQuery({
        from_date: form.fromDate,
        to_date: form.toDate
      });
      const data = await apiRequest(`/schedules/venue/${form.venueId}${query}`);
      setSchedules(data);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h2>Schedules</h2>
          <p>Find showtimes by venue and date window.</p>
        </div>
      </div>
      <form className="form-card" onSubmit={handleSearch}>
        <label>
          Venue
          <select
            value={form.venueId}
            onChange={(event) => setForm({ ...form, venueId: event.target.value })}
          >
            <option value="">Select venue</option>
            {venues.map((venue) => (
              <option key={venue.id} value={venue.id}>
                {venue.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          From
          <input
            type="datetime-local"
            value={form.fromDate}
            onChange={(event) => setForm({ ...form, fromDate: event.target.value })}
          />
        </label>
        <label>
          To
          <input
            type="datetime-local"
            value={form.toDate}
            onChange={(event) => setForm({ ...form, toDate: event.target.value })}
          />
        </label>
        <button className="primary" type="submit">
          Search schedules
        </button>
      </form>
      {error ? <p className="notice">{error}</p> : null}
      <div className="schedule-grid">
        {schedules.map((item) => (
          <div className="schedule-card" key={item.id}>
            <div>
              <h3>{item.show_title}</h3>
              <p>{item.venue_name} · {item.screen_name}</p>
            </div>
            <div className="schedule-meta">
              <span>{formatTime12Hour(item.start_time)}</span>
              <span>{formatTime12Hour(item.end_time)}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
