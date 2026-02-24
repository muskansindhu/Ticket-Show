import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiRequest, formatCurrency } from "../apiClient.js";
import Icon from "../components/Icon.jsx";
import { formatTime12Hour, formatTimeRange } from "../utils/time.js";
import poster1 from "../assets/posters/poster-1.jpg";
import poster2 from "../assets/posters/poster-2.jpg";
import poster3 from "../assets/posters/poster-3.jpg";
import poster4 from "../assets/posters/poster-4.jpg";
import poster5 from "../assets/posters/poster-5.jpg";
import poster6 from "../assets/posters/poster-6.jpg";
import poster7 from "../assets/posters/poster-7.jpg";
import poster8 from "../assets/posters/poster-8.jpg";
import poster9 from "../assets/posters/poster-9.jpg";

const posters = [poster1, poster2, poster3, poster4, poster5, poster6, poster7, poster8, poster9];
const VENUE_PAGE_SIZE = 100;

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

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

async function fetchAllVenues() {
  let skip = 0;
  const result = [];
  while (true) {
    const query = `?skip=${skip}&limit=${VENUE_PAGE_SIZE}`;
    let batch;
    try {
      batch = await apiRequest(`/venues/${query}`);
    } catch (err) {
      if (!String(err?.message || "").includes("Not Found")) {
        throw err;
      }
      batch = await apiRequest(`/venues${query}`);
    }
    if (!Array.isArray(batch) || batch.length === 0) break;
    result.push(...batch);
    if (batch.length < VENUE_PAGE_SIZE) break;
    skip += VENUE_PAGE_SIZE;
  }
  return result;
}

export default function Venues() {
  const navigate = useNavigate();
  const [venues, setVenues] = useState([]);
  const [shows, setShows] = useState([]);
  const [selectedVenue, setSelectedVenue] = useState(null);
  const [venueSchedules, setVenueSchedules] = useState([]);
  const [loadingVenues, setLoadingVenues] = useState(true);
  const [loadingSchedules, setLoadingSchedules] = useState(false);
  const [selectedDateKey, setSelectedDateKey] = useState(() => toDateKey(new Date()));
  const [error, setError] = useState("");
  const dateRow = buildDateRow(7);

  useEffect(() => {
    let active = true;
    async function loadData() {
      setLoadingVenues(true);
      try {
        const [venuesData, showsData] = await Promise.all([
          fetchAllVenues(),
          apiRequest("/shows/?limit=100")
        ]);
        if (!active) return;
        setVenues(venuesData);
        setShows(showsData);
        setError("");
      } catch (err) {
        if (!active) return;
        setError(err.message);
      } finally {
        if (active) {
          setLoadingVenues(false);
        }
      }
    }
    loadData();

    return () => {
      active = false;
    };
  }, []);

  const groupedMovies = useMemo(() => {
    const map = new Map();

    // Filter schedules by the selected date first
    const filteredSchedules = venueSchedules.filter(
      (schedule) => toDateKey(schedule.start_time) === selectedDateKey
    );

    filteredSchedules.forEach((schedule) => {
      const key = `${normalize(schedule.show_title)}::${schedule.show_duration}`;
      if (!map.has(key)) {
        map.set(key, {
          key,
          title: schedule.show_title,
          duration: schedule.show_duration,
          schedules: []
        });
      }
      map.get(key).schedules.push(schedule);
    });
    return Array.from(map.values())
      .map((movie) => ({
        ...movie,
        schedules: movie.schedules
          .slice()
          .sort((first, second) => new Date(first.start_time) - new Date(second.start_time))
      }))
      .sort((first, second) => first.title.localeCompare(second.title));
  }, [venueSchedules, selectedDateKey]);

  function findShowBySchedule(schedule) {
    const exactMatch = shows.find(
      (show) =>
        normalize(show.title) === normalize(schedule.show_title) &&
        Number(show.duration_minutes) === Number(schedule.show_duration)
    );
    if (exactMatch) return exactMatch;
    return (
      shows.find((show) => normalize(show.title) === normalize(schedule.show_title)) || null
    );
  }

  async function handleVenueSelect(venue) {
    setSelectedVenue(venue);
    setVenueSchedules([]);
    setError("");
    setLoadingSchedules(true);
    try {
      const data = await apiRequest(`/schedules/venue/${venue.id}`);
      setVenueSchedules(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingSchedules(false);
    }
  }

  function handleScheduleSelect(schedule) {
    if (!selectedVenue) return;
    const show =
      findShowBySchedule(schedule) ||
      {
        title: schedule.show_title,
        duration_minutes: schedule.show_duration,
        description: "",
        price: 0,
        rating: "NR"
      };
    navigate(`/seats/${schedule.id}`, {
      state: { show, venue: selectedVenue, schedule }
    });
  }

  return (
    <section className="page">
      <div className="show-date-strip reveal" style={{ "--delay": "0.02s", marginBottom: "0.5rem" }}>
        {dateRow.map((date) => {
          const hasSchedules = venueSchedules.some(
            (schedule) => toDateKey(schedule.start_time) === date.key
          );

          return (
            <button
              key={date.key}
              type="button"
              className={`show-date-chip${selectedDateKey === date.key ? " active" : ""
                }${!hasSchedules && selectedVenue ? " muted-chip" : ""}`}
              onClick={() => {
                setSelectedDateKey(date.key);
              }}
            >
              <span className="show-date-weekday">{date.weekday}</span>
              <span className="show-date-day">{date.day}</span>
              <span className="show-date-month">{date.month}</span>
            </button>
          );
        })}
      </div>

      <div className="page-header venue-browser-header">
        <div className="venue-browser-copy">
          <p className="eyebrow"><Icon name="location" size={14} /> Browse by venue</p>
          <h2>Choose A Venue</h2>
          <p className="muted">Tap a venue to load all movies and show schedules.</p>
        </div>
      </div>

      {error ? <p className="notice">{error}</p> : null}

      {loadingVenues ? <p className="muted">Loading venues...</p> : null}

      <div className="grid-cards venue-browser-grid">
        {venues.map((venue) => (
          <button
            className={`venue-card clickable venue-browser-card ${selectedVenue?.id === venue.id ? "active" : ""}`}
            key={venue.id}
            type="button"
            onClick={() => handleVenueSelect(venue)}
          >
            <div>
              <h3>{venue.name}</h3>
              <p className="muted icon-row"><Icon name="location" size={12} /> {venue.location}</p>
            </div>
            <div className="venue-timings">
              <p className="muted venue-timings-label">Timings:</p>
              <p className="venue-timings-value">
                <Icon name="clock" size={12} /> {formatTimeRange(venue.opening_time, venue.closing_time)}
              </p>
            </div>
          </button>
        ))}
      </div>
      {!loadingVenues && venues.length === 0 ? (
        <p className="muted">No venues available right now.</p>
      ) : null}

      {selectedVenue ? (
        <section className="venue-results form-card">

          <div className="venue-results-head">
            <div className="venue-results-copy">
              <p className="eyebrow"><Icon name="film" size={13} /> Movies in {selectedVenue.name}</p>
              <p className="muted icon-row venue-results-location"><Icon name="location" size={12} /> {selectedVenue.location}</p>
              <h3>Available movies and schedules</h3>
            </div>
            <span className="meta-chip">
              <Icon name="calendar" size={12} /> {venueSchedules.length} slots
            </span>
          </div>

          {loadingSchedules ? (
            <p className="muted">Loading schedules...</p>
          ) : groupedMovies.length === 0 ? (
            <p className="muted">No schedules are available for this venue right now.</p>
          ) : (
            <div className="venue-movie-list">
              {groupedMovies.map((movie, index) => {
                const show = findShowBySchedule({
                  show_title: movie.title,
                  show_duration: movie.duration
                });
                const poster = posters[(Number(show?.id) || index) % posters.length];
                return (
                  <article className="show-card venue-movie-card reveal" style={{ "--delay": `${index * 0.03}s` }} key={movie.key}>
                    <div className="venue-movie-head">
                      <div className="venue-movie-poster">
                        <img src={poster} alt={movie.title} loading="lazy" />
                      </div>
                      <div className="venue-movie-details">
                        <h3>{movie.title}</h3>
                        <p className="muted icon-row"><Icon name="clock" size={12} /> {movie.duration} min</p>
                        <p className="dashboard-price">{show ? formatCurrency(show.price) : formatCurrency(0)}</p>
                      </div>
                    </div>
                    <div className="schedule-grid venue-slot-grid">
                      {movie.schedules.map((schedule) => (
                        <button
                          className="schedule-chip venue-schedule-chip"
                          key={schedule.id}
                          type="button"
                          onClick={() => handleScheduleSelect(schedule)}
                        >
                          <span className="schedule-time">{formatTime12Hour(schedule.start_time)}</span>
                          <span className="muted">{schedule.screen_name}</span>
                        </button>
                      ))}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      ) : (
        <p className="muted">Select a venue to view all movies with schedule timings.</p>
      )}
    </section>
  );
}
