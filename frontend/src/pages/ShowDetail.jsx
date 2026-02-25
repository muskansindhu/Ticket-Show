import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { apiRequest, formatCurrency } from "../apiClient.js";
import Icon from "../components/Icon.jsx";
import { formatTime12Hour, formatTimeRange } from "../utils/time.js";
import { useAuth } from "../context/auth.jsx";

function toDateKey(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function buildDateRow(days = 7) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return Array.from({ length: days }, (_, index) => {
    const date = new Date(today);
    date.setDate(today.getDate() + index);
    return {
      key: toDateKey(date),
      weekday: date.toLocaleDateString("en-US", { weekday: "short" }).toUpperCase(),
      day: date.toLocaleDateString("en-US", { day: "2-digit" }),
      month: date.toLocaleDateString("en-US", { month: "short" }).toUpperCase()
    };
  });
}

export default function ShowDetail() {
  const { user } = useAuth();
  const { showId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [show, setShow] = useState(location.state?.show || null);
  const [venues, setVenues] = useState([]);
  const [schedulesByVenueId, setSchedulesByVenueId] = useState({});
  const [scheduleErrorsByVenueId, setScheduleErrorsByVenueId] = useState({});
  const [loadingSchedules, setLoadingSchedules] = useState(false);
  const [selectedScheduleId, setSelectedScheduleId] = useState(null);
  const [selectedDateKey, setSelectedDateKey] = useState(() => toDateKey(new Date()));
  const [error, setError] = useState("");
  const dateRow = buildDateRow(7);

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
        const city = user?.city ? `?city=${encodeURIComponent(user.city)}` : "";
        const data = await apiRequest(`/shows/${showId}/venues${city}`);
        setVenues(data);
      } catch (err) {
        setError(err.message);
      }
    }
    loadVenues();
  }, [showId, user?.city]);

  useEffect(() => {
    let cancelled = false;

    async function loadVenueSchedules() {
      if (venues.length === 0) {
        setLoadingSchedules(false);
        setSchedulesByVenueId({});
        setScheduleErrorsByVenueId({});
        return;
      }

      setLoadingSchedules(true);
      const results = await Promise.allSettled(
        venues.map(async (venue) => {
          const data = await apiRequest(`/schedules/venue/${venue.id}?show_id=${showId}`);
          return { venueId: venue.id, schedules: data };
        })
      );

      if (cancelled) return;

      const nextSchedulesByVenue = {};
      const nextScheduleErrorsByVenue = {};

      results.forEach((result, index) => {
        const venueId = venues[index].id;
        if (result.status === "fulfilled") {
          nextSchedulesByVenue[venueId] = Array.isArray(result.value.schedules)
            ? result.value.schedules
            : [];
          return;
        }
        nextSchedulesByVenue[venueId] = [];
        nextScheduleErrorsByVenue[venueId] =
          result.reason?.message || "Unable to load schedules for this venue.";
      });

      setSchedulesByVenueId(nextSchedulesByVenue);
      setScheduleErrorsByVenueId(nextScheduleErrorsByVenue);
      setLoadingSchedules(false);
    }

    loadVenueSchedules();
    return () => {
      cancelled = true;
    };
  }, [venues, showId]);

  function getSchedulesGroupedByScreen(schedules) {
    const grouped = new Map();

    schedules.forEach((schedule) => {
      const screenName = schedule.screen_name || "Screen";
      if (!grouped.has(screenName)) {
        grouped.set(screenName, []);
      }
      grouped.get(screenName).push(schedule);
    });

    return Array.from(grouped.entries());
  }

  function handleScheduleClick(venue, schedule) {
    if (!show || !venue) return;
    setSelectedScheduleId(schedule.id);
    navigate(`/seats/${schedule.id}`, {
      state: { show, venue, schedule },
    });
  }

  return (
    <section className="page">
      <div className="show-date-strip reveal" style={{ "--delay": "0.02s" }}>
        {dateRow.map((date) => {
          const hasSchedules = venues.some((venue) =>
            (schedulesByVenueId[venue.id] || []).some(
              (schedule) => toDateKey(schedule.start_time) === date.key
            )
          );

          return (
            <button
              key={date.key}
              type="button"
              className={`show-date-chip${
                selectedDateKey === date.key ? " active" : ""
              }${!hasSchedules ? " muted-chip" : ""}`}
              onClick={() => {
                setSelectedDateKey(date.key);
                setSelectedScheduleId(null);
              }}
            >
              <span className="show-date-weekday">{date.weekday}</span>
              <span className="show-date-day">{date.day}</span>
              <span className="show-date-month">{date.month}</span>
            </button>
          );
        })}
      </div>

      <div className="page-header">
        <div>
          <p className="eyebrow">
            <Icon name="ticket" size={14} /> Show detail
          </p>
          <h2>{show ? show.title : "Show"}</h2>
          <p className="muted">
            {show?.description || "Select a venue and showtime."}
          </p>
        </div>
        {show ? (
          <div className="hero-chips">
            <span className="meta-chip">
              <Icon name="clock" size={12} /> {show.duration_minutes} min
            </span>
            <span className="meta-chip">
              <Icon name="credit" size={12} /> {formatCurrency(show.price)}
            </span>
          </div>
        ) : null}
      </div>
      {error ? <p className="notice">{error}</p> : null}
      <div className="form-card show-venues-panel reveal" style={{ "--delay": "0.05s" }}>
        <h3 className="title-row">
          <Icon name="location" size={16} /> Venues showing this title
        </h3>
        {venues.length === 0 ? (
          <p className="muted">
            {user?.city
              ? `No venues in ${user.city} are showing this title right now.`
              : "No venues are showing this title right now."}
          </p>
        ) : (
          <div className="show-venues-list">
            {venues.map((venue, index) => {
              const venueError = scheduleErrorsByVenueId[venue.id];
              const venueSchedules = schedulesByVenueId[venue.id] || [];
              const filteredVenueSchedules = venueSchedules.filter(
                (schedule) => toDateKey(schedule.start_time) === selectedDateKey
              );
              const groupedSchedules = getSchedulesGroupedByScreen(filteredVenueSchedules);

              return (
                <article
                  className={`show-venue-card reveal ${filteredVenueSchedules.length > 0 ? "active" : ""}`}
                  style={{ "--delay": `${index * 0.04}s` }}
                  key={venue.id}
                >
                  <div className="show-venue-head">
                    <div className="show-venue-copy">
                      <h4>{venue.name}</h4>
                      <p className="muted icon-row">
                        <Icon name="location" size={12} />
                        {venue.location}
                      </p>
                    </div>
                    <span className="meta-chip">
                      <Icon name="clock" size={12} />
                      {formatTimeRange(venue.opening_time, venue.closing_time)}
                    </span>
                  </div>

                  {loadingSchedules && venueSchedules.length === 0 && !venueError ? (
                    <p className="muted">Loading schedules...</p>
                  ) : null}
                  {venueError ? <p className="notice">{venueError}</p> : null}

                  {!venueError && groupedSchedules.length === 0 ? (
                    <p className="muted">No schedules available for this date.</p>
                  ) : null}

                  <div className="show-venue-screens">
                    {groupedSchedules.map(([screenName, screenSchedules]) => (
                      <section className="show-screen-group" key={`${venue.id}-${screenName}`}>
                        <p className="show-screen-title">{screenName}</p>
                        <div className="show-schedule-row">
                          {screenSchedules.map((schedule) => (
                            <button
                              key={schedule.id}
                              type="button"
                              className={`schedule-chip show-schedule-btn${
                                selectedScheduleId === schedule.id ? " selected" : ""
                              }`}
                              onClick={() => handleScheduleClick(venue, schedule)}
                            >
                              <Icon name="clock" size={13} />
                              {formatTime12Hour(schedule.start_time)}
                            </button>
                          ))}
                        </div>
                      </section>
                    ))}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
