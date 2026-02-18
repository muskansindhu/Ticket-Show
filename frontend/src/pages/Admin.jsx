import { useState } from "react";
import { apiRequest } from "../apiClient.js";
import Icon from "../components/Icon.jsx";

export default function Admin() {
  const [showForm, setShowForm] = useState({
    title: "",
    duration_minutes: 120,
    price: 20,
    description: "",
    language: "EN",
    rating: "PG"
  });
  const [venueForm, setVenueForm] = useState({
    name: "",
    location: "",
    opening_time: "10:00",
    closing_time: "23:00"
  });
  const [screenForm, setScreenForm] = useState({
    venue_id: "",
    name: "",
    capacity: 50
  });
  const [scheduleForm, setScheduleForm] = useState({
    show_id: "",
    screen_id: "",
    start_time: ""
  });
  const [message, setMessage] = useState("");

  async function submitShow(event) {
    event.preventDefault();
    setMessage("");
    try {
      await apiRequest("/shows/", {
        method: "POST",
        body: JSON.stringify({
          ...showForm,
          duration_minutes: Number(showForm.duration_minutes),
          price: Number(showForm.price)
        })
      });
      setMessage("Show created.");
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function submitVenue(event) {
    event.preventDefault();
    setMessage("");
    try {
      await apiRequest("/venues/", {
        method: "POST",
        body: JSON.stringify(venueForm)
      });
      setMessage("Venue created.");
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function submitScreen(event) {
    event.preventDefault();
    setMessage("");
    try {
      await apiRequest("/screens/", {
        method: "POST",
        body: JSON.stringify({
          ...screenForm,
          venue_id: Number(screenForm.venue_id),
          capacity: Number(screenForm.capacity)
        })
      });
      setMessage("Screen created.");
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function submitSchedule(event) {
    event.preventDefault();
    setMessage("");
    try {
      await apiRequest("/schedules/", {
        method: "POST",
        body: JSON.stringify({
          show_id: Number(scheduleForm.show_id),
          screen_id: Number(scheduleForm.screen_id),
          start_time: scheduleForm.start_time
        })
      });
      setMessage("Schedule created.");
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow"><Icon name="admin" size={14} /> Admin hub</p>
          <h2>Admin control center</h2>
          <p className="muted">Manage shows, venues, screens, and schedules.</p>
        </div>
      </div>
      <div className="grid-cards">
        <form className="form-card reveal" style={{ "--delay": "0.04s" }} onSubmit={submitShow}>
          <h3 className="title-row"><Icon name="spark" size={16} /> Create show</h3>
          <input
            placeholder="Title"
            value={showForm.title}
            onChange={(event) => setShowForm({ ...showForm, title: event.target.value })}
            required
          />
          <input
            placeholder="Description"
            value={showForm.description}
            onChange={(event) => setShowForm({ ...showForm, description: event.target.value })}
            required
          />
          <div className="inline">
            <input
              type="number"
              placeholder="Duration"
              value={showForm.duration_minutes}
              onChange={(event) =>
                setShowForm({ ...showForm, duration_minutes: event.target.value })
              }
            />
            <input
              type="number"
              placeholder="Price"
              value={showForm.price}
              onChange={(event) => setShowForm({ ...showForm, price: event.target.value })}
            />
          </div>
          <button className="primary" type="submit">Create show</button>
        </form>

        <form className="form-card reveal" style={{ "--delay": "0.08s" }} onSubmit={submitVenue}>
          <h3 className="title-row"><Icon name="location" size={16} /> Create venue</h3>
          <input
            placeholder="Name"
            value={venueForm.name}
            onChange={(event) => setVenueForm({ ...venueForm, name: event.target.value })}
            required
          />
          <input
            placeholder="Location"
            value={venueForm.location}
            onChange={(event) => setVenueForm({ ...venueForm, location: event.target.value })}
            required
          />
          <div className="inline">
            <input
              type="time"
              value={venueForm.opening_time}
              onChange={(event) => setVenueForm({ ...venueForm, opening_time: event.target.value })}
            />
            <input
              type="time"
              value={venueForm.closing_time}
              onChange={(event) => setVenueForm({ ...venueForm, closing_time: event.target.value })}
            />
          </div>
          <button className="primary" type="submit">Create venue</button>
        </form>

        <form className="form-card reveal" style={{ "--delay": "0.12s" }} onSubmit={submitScreen}>
          <h3 className="title-row"><Icon name="seat" size={16} /> Create screen</h3>
          <input
            placeholder="Venue ID"
            value={screenForm.venue_id}
            onChange={(event) => setScreenForm({ ...screenForm, venue_id: event.target.value })}
            required
          />
          <input
            placeholder="Screen name"
            value={screenForm.name}
            onChange={(event) => setScreenForm({ ...screenForm, name: event.target.value })}
            required
          />
          <input
            type="number"
            placeholder="Capacity"
            value={screenForm.capacity}
            onChange={(event) => setScreenForm({ ...screenForm, capacity: event.target.value })}
          />
          <button className="primary" type="submit">Create screen</button>
        </form>

        <form className="form-card reveal" style={{ "--delay": "0.16s" }} onSubmit={submitSchedule}>
          <h3 className="title-row"><Icon name="calendar" size={16} /> Create schedule</h3>
          <input
            placeholder="Show ID"
            value={scheduleForm.show_id}
            onChange={(event) => setScheduleForm({ ...scheduleForm, show_id: event.target.value })}
            required
          />
          <input
            placeholder="Screen ID"
            value={scheduleForm.screen_id}
            onChange={(event) => setScheduleForm({ ...scheduleForm, screen_id: event.target.value })}
            required
          />
          <input
            type="datetime-local"
            value={scheduleForm.start_time}
            onChange={(event) => setScheduleForm({ ...scheduleForm, start_time: event.target.value })}
            required
          />
          <button className="primary" type="submit">Create schedule</button>
        </form>
      </div>
      {message ? <p className="notice">{message}</p> : null}
    </section>
  );
}
