import { useEffect, useMemo, useState } from "react";
import { apiRequest, formatCurrency } from "../apiClient.js";
import Icon from "../components/Icon.jsx";
import { formatTime12Hour, formatTimeRange } from "../utils/time.js";

const PAGE_LIMIT = 100;
const PANELS = [
  { id: "venues", label: "Venues", icon: "location" },
  { id: "shows", label: "Shows", icon: "film" },
  { id: "schedules", label: "Schedules", icon: "calendar" },
];

function scheduleKey(show) {
  return `${String(show?.title || "")
    .trim()
    .toLowerCase()}::${Number(show?.duration_minutes || 0)}`;
}

async function fetchAll(path, params = {}) {
  let skip = 0;
  const records = [];

  while (true) {
    const search = new URLSearchParams({
      ...params,
      skip: String(skip),
      limit: String(PAGE_LIMIT),
    });
    const batch = await apiRequest(`${path}?${search.toString()}`);
    if (!Array.isArray(batch) || batch.length === 0) break;
    records.push(...batch);
    if (batch.length < PAGE_LIMIT) break;
    skip += PAGE_LIMIT;
  }

  return records;
}

export default function Admin() {
  const [activePanel, setActivePanel] = useState("venues");
  const [expandedVenueId, setExpandedVenueId] = useState(null);
  const [scheduleVenueFilter, setScheduleVenueFilter] = useState("all");

  const [venues, setVenues] = useState([]);
  const [shows, setShows] = useState([]);
  const [screens, setScreens] = useState([]);
  const [schedulesByVenue, setSchedulesByVenue] = useState({});
  const [scheduleErrorsByVenue, setScheduleErrorsByVenue] = useState({});

  const [addedShowsByVenue, setAddedShowsByVenue] = useState({});
  const [showToAddByVenue, setShowToAddByVenue] = useState({});
  const [screenFormsByVenue, setScreenFormsByVenue] = useState({});
  const [scheduleFormsByVenue, setScheduleFormsByVenue] = useState({});

  const [showForm, setShowForm] = useState({
    title: "",
    duration_minutes: "",
    price: "",
    description: "",
    language: "",
    rating: "",
  });
  const [venueForm, setVenueForm] = useState({
    name: "",
    location: "",
    opening_time: "",
    closing_time: "",
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [pendingDelete, setPendingDelete] = useState(null);
  const [editingVenueId, setEditingVenueId] = useState(null);
  const [editingShowId, setEditingShowId] = useState(null);
  const [venueEditForm, setVenueEditForm] = useState({
    name: "",
    location: "",
    opening_time: "",
    closing_time: "",
  });
  const [showEditForm, setShowEditForm] = useState({
    title: "",
    description: "",
    duration_minutes: "",
    price: "",
    language: "",
    rating: "",
  });

  const showLookupByKey = useMemo(() => {
    const map = new Map();
    shows.forEach((show) => map.set(scheduleKey(show), show));
    return map;
  }, [shows]);

  const flatSchedules = useMemo(() => {
    return venues
      .flatMap((venue) =>
        (schedulesByVenue[venue.id] || []).map((schedule) => ({
          ...schedule,
          venue_id: venue.id,
          venue_name: venue.name,
        })),
      )
      .sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
  }, [venues, schedulesByVenue]);

  const filteredSchedules = useMemo(() => {
    if (scheduleVenueFilter === "all") return flatSchedules;
    return flatSchedules.filter(
      (schedule) => Number(schedule.venue_id) === Number(scheduleVenueFilter),
    );
  }, [flatSchedules, scheduleVenueFilter]);

  async function loadAdminData() {
    setLoading(true);
    setMessage("");
    try {
      const [venueData, showData, screenData] = await Promise.all([
        fetchAll("/venues/", { include_inactive: "true" }),
        fetchAll("/shows/", { include_cancelled: "true" }),
        fetchAll("/screens/"),
      ]);

      const scheduleResults = await Promise.allSettled(
        venueData.map((venue) => apiRequest(`/schedules/venue/${venue.id}`)),
      );

      const nextSchedulesByVenue = {};
      const nextScheduleErrorsByVenue = {};

      scheduleResults.forEach((result, index) => {
        const venueId = venueData[index].id;
        if (result.status === "fulfilled") {
          nextSchedulesByVenue[venueId] = Array.isArray(result.value)
            ? result.value
            : [];
        } else {
          nextSchedulesByVenue[venueId] = [];
          nextScheduleErrorsByVenue[venueId] =
            result.reason?.message ||
            "Unable to load schedules for this venue.";
        }
      });

      setVenues(venueData);
      setShows(showData);
      setScreens(screenData);
      setSchedulesByVenue(nextSchedulesByVenue);
      setScheduleErrorsByVenue(nextScheduleErrorsByVenue);
    } catch (err) {
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAdminData();
  }, []);

  function getScreensForVenue(venueId) {
    return screens.filter(
      (screen) => Number(screen.venue_id) === Number(venueId),
    );
  }

  function getShowIdsForVenue(venueId) {
    const scheduledShowIds = (schedulesByVenue[venueId] || [])
      .map(
        (schedule) =>
          showLookupByKey.get(
            `${String(schedule.show_title || "")
              .trim()
              .toLowerCase()}::${Number(schedule.show_duration || 0)}`,
          )?.id,
      )
      .filter(Boolean);

    const addedShowIds = addedShowsByVenue[venueId] || [];
    return Array.from(new Set([...scheduledShowIds, ...addedShowIds]));
  }

  function getScreenForm(venueId) {
    return screenFormsByVenue[venueId] || { name: "", capacity: "" };
  }

  function getScheduleForm(venueId) {
    return (
      scheduleFormsByVenue[venueId] || {
        show_id: "",
        screen_id: "",
        start_time: "",
      }
    );
  }

  function updateScreenForm(venueId, patch) {
    const current = getScreenForm(venueId);
    setScreenFormsByVenue((prev) => ({
      ...prev,
      [venueId]: { ...current, ...patch },
    }));
  }

  function updateScheduleForm(venueId, patch) {
    const current = getScheduleForm(venueId);
    setScheduleFormsByVenue((prev) => ({
      ...prev,
      [venueId]: { ...current, ...patch },
    }));
  }

  function normalizeTimeForInput(value) {
    return String(value || "").trim().slice(0, 5);
  }

  function normalizeOptionalText(value) {
    const next = String(value ?? "").trim();
    return next || null;
  }

  function startVenueEdit(venue) {
    setEditingVenueId(venue.id);
    setVenueEditForm({
      name: venue.name,
      location: venue.location,
      opening_time: normalizeTimeForInput(venue.opening_time),
      closing_time: normalizeTimeForInput(venue.closing_time),
    });
  }

  function cancelVenueEdit() {
    setEditingVenueId(null);
    setVenueEditForm({
      name: "",
      location: "",
      opening_time: "",
      closing_time: "",
    });
  }

  async function submitVenueEdit(venue, event) {
    event.preventDefault();
    setMessage("");

    const nextName = venueEditForm.name.trim();
    const nextLocation = venueEditForm.location.trim();
    const nextOpening = venueEditForm.opening_time.trim();
    const nextClosing = venueEditForm.closing_time.trim();

    if (!nextName || !nextLocation || !nextOpening || !nextClosing) {
      setMessage("Venue name, location, opening time, and closing time are required.");
      return;
    }

    const payload = {};
    if (nextName !== venue.name) payload.name = nextName;
    if (nextLocation !== venue.location) payload.location = nextLocation;
    if (nextOpening !== normalizeTimeForInput(venue.opening_time)) {
      payload.opening_time = nextOpening;
    }
    if (nextClosing !== normalizeTimeForInput(venue.closing_time)) {
      payload.closing_time = nextClosing;
    }

    if (Object.keys(payload).length === 0) {
      setMessage("No venue changes to save.");
      return;
    }

    try {
      await apiRequest(`/venues/${venue.id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      cancelVenueEdit();
      await loadAdminData();
      setMessage("Venue updated.");
    } catch (err) {
      setMessage(err.message);
    }
  }

  function startShowEdit(show) {
    setEditingShowId(show.id);
    setShowEditForm({
      title: show.title,
      description: show.description,
      duration_minutes: String(show.duration_minutes),
      price: String(show.price),
      language: show.language || "",
      rating: show.rating || "",
    });
  }

  function cancelShowEdit() {
    setEditingShowId(null);
    setShowEditForm({
      title: "",
      description: "",
      duration_minutes: "",
      price: "",
      language: "",
      rating: "",
    });
  }

  async function submitShowEdit(show, event) {
    event.preventDefault();
    setMessage("");

    const nextTitle = showEditForm.title.trim();
    const nextDescription = showEditForm.description.trim();
    const nextDuration = Number(showEditForm.duration_minutes);
    const nextPrice = Number(showEditForm.price);
    const nextLanguage = normalizeOptionalText(showEditForm.language);
    const nextRating = normalizeOptionalText(showEditForm.rating);

    if (!nextTitle) {
      setMessage("Show title is required.");
      return;
    }
    if (nextDescription.length < 32) {
      setMessage("Description must be at least 32 characters.");
      return;
    }
    if (!Number.isFinite(nextDuration) || nextDuration <= 0) {
      setMessage("Duration must be a positive number.");
      return;
    }
    if (!Number.isFinite(nextPrice) || nextPrice <= 0) {
      setMessage("Price must be a positive number.");
      return;
    }

    const payload = {};
    if (nextTitle !== show.title) payload.title = nextTitle;
    if (nextDescription !== show.description) payload.description = nextDescription;
    if (nextDuration !== Number(show.duration_minutes)) {
      payload.duration_minutes = nextDuration;
    }
    if (nextPrice !== Number(show.price)) payload.price = nextPrice;
    if (nextLanguage !== (show.language ?? null)) payload.language = nextLanguage;
    if (nextRating !== (show.rating ?? null)) payload.rating = nextRating;

    if (Object.keys(payload).length === 0) {
      setMessage("No show changes to save.");
      return;
    }

    try {
      await apiRequest(`/shows/${show.id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      cancelShowEdit();
      await loadAdminData();
      setMessage("Show updated.");
    } catch (err) {
      setMessage(err.message);
    }
  }

  function requestVenueDelete(venue) {
    setPendingDelete({
      entity: "venue",
      id: venue.id,
      label: venue.name,
    });
  }

  function requestShowDelete(show) {
    setPendingDelete({
      entity: "show",
      id: show.id,
      label: show.title,
    });
  }

  function closeDeleteDialog() {
    setPendingDelete(null);
  }

  async function confirmDelete() {
    if (!pendingDelete) return;

    setMessage("");
    try {
      if (pendingDelete.entity === "venue") {
        await apiRequest(`/venues/${pendingDelete.id}`, { method: "DELETE" });
        if (expandedVenueId === pendingDelete.id) setExpandedVenueId(null);
        if (editingVenueId === pendingDelete.id) cancelVenueEdit();
        setMessage("Venue marked inactive.");
      } else if (pendingDelete.entity === "show") {
        await apiRequest(`/shows/${pendingDelete.id}`, { method: "DELETE" });
        if (editingShowId === pendingDelete.id) cancelShowEdit();
        setMessage("Show cancelled.");
      }

      closeDeleteDialog();
      await loadAdminData();
    } catch (err) {
      setMessage(err.message);
      closeDeleteDialog();
    }
  }

  function handleAddShowToVenue(venueId) {
    const showId = Number(showToAddByVenue[venueId]);
    if (!showId) {
      setMessage("Select a show before adding it to the venue.");
      return;
    }

    setAddedShowsByVenue((prev) => {
      const existing = prev[venueId] || [];
      return {
        ...prev,
        [venueId]: existing.includes(showId) ? existing : [...existing, showId],
      };
    });

    const currentSchedule = getScheduleForm(venueId);
    if (!currentSchedule.show_id) {
      updateScheduleForm(venueId, { show_id: String(showId) });
    }
    setMessage(
      "Show added to venue workspace. Create a schedule to publish it.",
    );
  }

  async function submitShow(event) {
    event.preventDefault();
    setMessage("");
    try {
      await apiRequest("/shows/", {
        method: "POST",
        body: JSON.stringify({
          ...showForm,
          duration_minutes: Number(showForm.duration_minutes),
          price: Number(showForm.price),
          language: normalizeOptionalText(showForm.language),
          rating: normalizeOptionalText(showForm.rating),
        }),
      });

      setShowForm({
        title: "",
        duration_minutes: "",
        price: "",
        description: "",
        language: "",
        rating: "",
      });
      await loadAdminData();
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
        body: JSON.stringify(venueForm),
      });

      setVenueForm({
        name: "",
        location: "",
        opening_time: "",
        closing_time: "",
      });
      await loadAdminData();
      setMessage("Venue created.");
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function submitScreen(venueId, event) {
    event.preventDefault();
    setMessage("");
    const current = getScreenForm(venueId);
    try {
      await apiRequest("/screens/", {
        method: "POST",
        body: JSON.stringify({
          venue_id: Number(venueId),
          name: current.name,
          capacity: Number(current.capacity),
        }),
      });

      setScreenFormsByVenue((prev) => ({
        ...prev,
        [venueId]: { name: "", capacity: "" },
      }));
      await loadAdminData();
      setMessage("Screen created.");
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function submitSchedule(venueId, event) {
    event.preventDefault();
    setMessage("");
    const current = getScheduleForm(venueId);
    try {
      await apiRequest("/schedules/", {
        method: "POST",
        body: JSON.stringify({
          show_id: Number(current.show_id),
          screen_id: Number(current.screen_id),
          start_time: current.start_time,
        }),
      });

      setScheduleFormsByVenue((prev) => ({
        ...prev,
        [venueId]: { ...current, start_time: "" },
      }));

      const freshSchedules = await apiRequest(`/schedules/venue/${venueId}`);
      setSchedulesByVenue((prev) => ({
        ...prev,
        [venueId]: Array.isArray(freshSchedules) ? freshSchedules : [],
      }));
      setMessage("Schedule created.");
    } catch (err) {
      setMessage(err.message);
    }
  }

  function openVenueManager(venueId) {
    setActivePanel("venues");
    setExpandedVenueId(venueId);
  }

  function renderVenuesPanel() {
    return (
      <section className="admin-panel-section">
        <form className="form-card admin-create-card" onSubmit={submitVenue}>
          <h3 className="title-row">
            <Icon name="location" size={16} /> Create venue
          </h3>
          <div className="admin-inline-form">
            <label className="admin-field">
              <span>Venue Name</span>
              <input
                placeholder="Enter venue name (e.g. Cineplex Downtown)"
                value={venueForm.name}
                onChange={(event) =>
                  setVenueForm({ ...venueForm, name: event.target.value })
                }
                required
              />
            </label>
            <label className="admin-field">
              <span>Location</span>
              <input
                placeholder="Enter address or area (e.g. 123 Main St, Downtown)"
                value={venueForm.location}
                onChange={(event) =>
                  setVenueForm({ ...venueForm, location: event.target.value })
                }
                required
              />
            </label>
            <label className="admin-field">
              <span>Opening Time</span>
              <input
                type="time"
                placeholder="Select opening time"
                value={venueForm.opening_time}
                onChange={(event) =>
                  setVenueForm({ ...venueForm, opening_time: event.target.value })
                }
                required
              />
            </label>
            <label className="admin-field">
              <span>Closing Time</span>
              <input
                type="time"
                placeholder="Select closing time"
                value={venueForm.closing_time}
                onChange={(event) =>
                  setVenueForm({ ...venueForm, closing_time: event.target.value })
                }
                required
              />
            </label>
            <button className="primary" type="submit">
              Create venue
            </button>
          </div>
        </form>

        {loading ? <p className="muted">Loading venues...</p> : null}
        {!loading && venues.length === 0 ? (
          <p className="muted">No venues found.</p>
        ) : null}

        <div className="admin-venue-list">
          {venues.map((venue) => {
            const venueScreens = getScreensForVenue(venue.id);
            const venueSchedules = schedulesByVenue[venue.id] || [];
            const venueError = scheduleErrorsByVenue[venue.id];
            const availableShowIds = getShowIdsForVenue(venue.id);
            const selectedShowToAdd = showToAddByVenue[venue.id] || "";
            const screenForm = getScreenForm(venue.id);
            const scheduleForm = getScheduleForm(venue.id);
            const isExpanded = expandedVenueId === venue.id;
            const isEditingVenue = editingVenueId === venue.id;

            return (
              <article className="form-card admin-venue-card" key={venue.id}>
                <div className="admin-venue-summary">
                  <div>
                    <h3>{venue.name}</h3>
                    <p className="muted icon-row">
                      <Icon name="location" size={12} /> {venue.location}
                    </p>
                  </div>
                  <div className="admin-venue-summary-actions">
                    <div className="admin-venue-chips">
                      <span className="meta-chip">
                        <Icon name="clock" size={12} />{" "}
                        {formatTimeRange(venue.opening_time, venue.closing_time)}
                      </span>
                      <span className={`status-pill ${String(venue.status || "ACTIVE").toLowerCase()}`}>
                        {venue.status || "ACTIVE"}
                      </span>
                      <span className="meta-chip">
                        <Icon name="seat" size={12} /> {venueScreens.length}{" "}
                        screens
                      </span>
                      <span className="meta-chip">
                        <Icon name="calendar" size={12} /> {venueSchedules.length}{" "}
                        schedules
                      </span>
                    </div>
                    <div className="admin-venue-buttons">
                      <button
                        className="ghost"
                        type="button"
                        onClick={() =>
                          isEditingVenue ? cancelVenueEdit() : startVenueEdit(venue)
                        }
                      >
                        {isEditingVenue ? "Close" : "Edit"}
                      </button>
                      <button
                        className="ghost"
                        type="button"
                        onClick={() => requestVenueDelete(venue)}
                        disabled={venue.status === "INACTIVE"}
                      >
                        {venue.status === "INACTIVE" ? "Inactive" : "Mark Inactive"}
                      </button>
                      <button
                        className="primary"
                        type="button"
                        onClick={() =>
                          setExpandedVenueId((current) =>
                            current === venue.id ? null : venue.id,
                          )
                        }
                      >
                        {isExpanded ? "Hide" : "Manage"}
                      </button>
                    </div>
                  </div>
                </div>

                {isEditingVenue ? (
                  <form
                    className="admin-inline-form admin-edit-form"
                    onSubmit={(event) => submitVenueEdit(venue, event)}
                  >
                    <label className="admin-field">
                      <span>Venue Name</span>
                      <input
                        placeholder="Update venue name"
                        value={venueEditForm.name}
                        onChange={(event) =>
                          setVenueEditForm((prev) => ({
                            ...prev,
                            name: event.target.value,
                          }))
                        }
                        required
                      />
                    </label>
                    <label className="admin-field">
                      <span>Location</span>
                      <input
                        placeholder="Update location details"
                        value={venueEditForm.location}
                        onChange={(event) =>
                          setVenueEditForm((prev) => ({
                            ...prev,
                            location: event.target.value,
                          }))
                        }
                        required
                      />
                    </label>
                    <label className="admin-field">
                      <span>Opening Time</span>
                      <input
                        type="time"
                        placeholder="Select opening time"
                        value={venueEditForm.opening_time}
                        onChange={(event) =>
                          setVenueEditForm((prev) => ({
                            ...prev,
                            opening_time: event.target.value,
                          }))
                        }
                        required
                      />
                    </label>
                    <label className="admin-field">
                      <span>Closing Time</span>
                      <input
                        type="time"
                        placeholder="Select closing time"
                        value={venueEditForm.closing_time}
                        onChange={(event) =>
                          setVenueEditForm((prev) => ({
                            ...prev,
                            closing_time: event.target.value,
                          }))
                        }
                        required
                      />
                    </label>
                    <div className="admin-edit-actions">
                      <button className="primary" type="submit">
                        Save changes
                      </button>
                    </div>
                  </form>
                ) : null}

                {isExpanded ? (
                  <div className="admin-venue-expanded">
                    <div className="admin-venue-block">
                      <p className="section-title">Screens</p>
                      <div className="admin-chip-row">
                        {venueScreens.map((screen) => (
                          <span className="meta-chip" key={screen.id}>
                            <Icon name="seat" size={12} /> {screen.name} (
                            {screen.capacity})
                          </span>
                        ))}
                      </div>
                      <form
                        className="admin-inline-form"
                        onSubmit={(event) => submitScreen(venue.id, event)}
                      >
                        <label className="admin-field">
                          <span>Screen Name</span>
                          <input
                            placeholder="Enter screen name (e.g. Screen 1)"
                            value={screenForm.name}
                            onChange={(event) =>
                              updateScreenForm(venue.id, {
                                name: event.target.value,
                              })
                            }
                            required
                          />
                        </label>
                        <label className="admin-field">
                          <span>Capacity</span>
                          <input
                            type="number"
                            placeholder="Enter total seats (e.g. 120)"
                            min={1}
                            value={screenForm.capacity}
                            onChange={(event) =>
                              updateScreenForm(venue.id, {
                                capacity: event.target.value,
                              })
                            }
                            required
                          />
                        </label>
                        <button className="primary" type="submit">
                          Add screen
                        </button>
                      </form>
                    </div>

                    <div className="admin-venue-block">
                      <p className="section-title">Add show to venue</p>
                      <div className="admin-inline-form">
                        <label className="admin-field">
                          <span>Show</span>
                          <select
                            value={selectedShowToAdd}
                            onChange={(event) =>
                              setShowToAddByVenue((prev) => ({
                                ...prev,
                                [venue.id]: event.target.value,
                              }))
                            }
                          >
                            <option value="">Choose a show to add</option>
                            {shows
                              .filter((show) => show.status === "ACTIVE")
                              .map((show) => (
                                <option value={show.id} key={show.id}>
                                  {show.title} ({show.duration_minutes} min,{" "}
                                  {formatCurrency(show.price)})
                                </option>
                              ))}
                          </select>
                        </label>
                        <button
                          className="primary"
                          type="button"
                          onClick={() => handleAddShowToVenue(venue.id)}
                        >
                          Add show
                        </button>
                      </div>
                    </div>

                    <div className="admin-venue-block">
                      <p className="section-title">Create schedule</p>
                      {availableShowIds.length === 0 ? (
                        <p className="muted">Add a show to this venue first.</p>
                      ) : (
                        <form
                          className="admin-inline-form"
                          onSubmit={(event) => submitSchedule(venue.id, event)}
                        >
                          <label className="admin-field">
                            <span>Show</span>
                            <select
                              value={scheduleForm.show_id}
                              onChange={(event) =>
                                updateScheduleForm(venue.id, {
                                  show_id: event.target.value,
                                })
                              }
                              required
                            >
                              <option value="">Choose show for this schedule</option>
                              {availableShowIds.map((showId) => {
                                const show = shows.find(
                                  (item) => Number(item.id) === Number(showId),
                                );
                                if (!show) return null;
                                return (
                                  <option
                                    value={show.id}
                                    key={`${venue.id}-show-${show.id}`}
                                  >
                                    {show.title}
                                  </option>
                                );
                              })}
                            </select>
                          </label>
                          <label className="admin-field">
                            <span>Screen</span>
                            <select
                              value={scheduleForm.screen_id}
                              onChange={(event) =>
                                updateScheduleForm(venue.id, {
                                  screen_id: event.target.value,
                                })
                              }
                              required
                            >
                              <option value="">Choose screen</option>
                              {venueScreens.map((screen) => (
                                <option
                                  value={screen.id}
                                  key={`${venue.id}-screen-${screen.id}`}
                                >
                                  {screen.name}
                                </option>
                              ))}
                            </select>
                          </label>
                          <label className="admin-field">
                            <span>Start Date and Time</span>
                            <input
                              type="datetime-local"
                              placeholder="Select start date and time"
                              value={scheduleForm.start_time}
                              onChange={(event) =>
                                updateScheduleForm(venue.id, {
                                  start_time: event.target.value,
                                })
                              }
                              required
                            />
                          </label>
                          <button className="primary" type="submit">
                            Create schedule
                          </button>
                        </form>
                      )}

                      {venueError ? (
                        <p className="notice">{venueError}</p>
                      ) : null}
                      {!venueError && venueSchedules.length === 0 ? (
                        <p className="muted">No schedules created yet.</p>
                      ) : null}
                      <div className="admin-schedule-list">
                        {venueSchedules.map((schedule) => (
                          <div
                            className="admin-schedule-item"
                            key={`${venue.id}-${schedule.id}`}
                          >
                            <strong>{schedule.show_title}</strong>
                            <span className="muted">
                              {schedule.screen_name}
                            </span>
                            <span className="meta-chip">
                              <Icon name="clock" size={12} />
                              {formatTime12Hour(schedule.start_time)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : null}
              </article>
            );
          })}
        </div>
      </section>
    );
  }

  function renderShowsPanel() {
    return (
      <section className="admin-panel-section">
        <form className="form-card admin-create-card" onSubmit={submitShow}>
          <h3 className="title-row">
            <Icon name="spark" size={16} /> Create show
          </h3>
          <label className="admin-field">
            <span>Title</span>
            <input
              placeholder="Enter show title (e.g. Interstellar)"
              value={showForm.title}
              onChange={(event) =>
                setShowForm({ ...showForm, title: event.target.value })
              }
              required
            />
          </label>
          <label className="admin-field">
            <span>Description</span>
            <textarea
              className="admin-fixed-textarea"
              placeholder="Add a detailed summary (minimum 32 characters)"
              value={showForm.description}
              onChange={(event) =>
                setShowForm({ ...showForm, description: event.target.value })
              }
              minLength={32}
              required
            />
          </label>
          <div className="admin-inline-form">
            <label className="admin-field">
              <span>Duration (Minutes)</span>
              <input
                type="number"
                placeholder="Enter duration in minutes (e.g. 120)"
                value={showForm.duration_minutes}
                onChange={(event) =>
                  setShowForm({
                    ...showForm,
                    duration_minutes: event.target.value,
                  })
                }
                required
              />
            </label>
            <label className="admin-field">
              <span>Price</span>
              <input
                type="number"
                placeholder="Enter ticket price (e.g. 499)"
                value={showForm.price}
                onChange={(event) =>
                  setShowForm({ ...showForm, price: event.target.value })
                }
                required
              />
            </label>
            <label className="admin-field">
              <span>Language</span>
              <input
                placeholder="Optional (e.g. English, Hindi)"
                value={showForm.language}
                onChange={(event) =>
                  setShowForm({ ...showForm, language: event.target.value })
                }
              />
            </label>
            <label className="admin-field">
              <span>Rating</span>
              <input
                placeholder="Optional (e.g. PG-13, U/A)"
                value={showForm.rating}
                onChange={(event) =>
                  setShowForm({ ...showForm, rating: event.target.value })
                }
              />
            </label>
            <button className="primary" type="submit">
              Create show
            </button>
          </div>
        </form>

        <div className="admin-show-list">
          {shows.map((show) => {
            const isEditingShow = editingShowId === show.id;
            return (
              <article className="form-card admin-show-card" key={show.id}>
                <div className="admin-show-card-head">
                  <div>
                    <h3>{show.title}</h3>
                    <p className="muted">{show.description}</p>
                  </div>
                  <div className="admin-venue-summary-actions">
                    <span className="meta-chip">
                      <Icon name="clock" size={12} /> {show.duration_minutes} min
                    </span>
                    <span className="meta-chip">
                      <Icon name="credit" size={12} />{" "}
                      {formatCurrency(show.price)}
                    </span>
                    <span className={`status-pill ${String(show.status || "ACTIVE").toLowerCase()}`}>
                      {show.status || "ACTIVE"}
                    </span>
                    <button
                      className="ghost"
                      type="button"
                      onClick={() =>
                        isEditingShow ? cancelShowEdit() : startShowEdit(show)
                      }
                    >
                      {isEditingShow ? "Close" : "Edit"}
                    </button>
                    <button
                      className="ghost"
                      type="button"
                      onClick={() => requestShowDelete(show)}
                      disabled={show.status === "CANCELLED"}
                    >
                      {show.status === "CANCELLED" ? "Cancelled" : "Cancel Show"}
                    </button>
                  </div>
                </div>

                {isEditingShow ? (
                  <form
                    className="admin-inline-form admin-edit-form"
                    onSubmit={(event) => submitShowEdit(show, event)}
                  >
                    <label className="admin-field">
                      <span>Title</span>
                      <input
                        placeholder="Update show title"
                        value={showEditForm.title}
                        onChange={(event) =>
                          setShowEditForm((prev) => ({
                            ...prev,
                            title: event.target.value,
                          }))
                        }
                        required
                      />
                    </label>
                    <label className="admin-field">
                      <span>Duration (Minutes)</span>
                      <input
                        type="number"
                        placeholder="Update duration in minutes"
                        min={1}
                        value={showEditForm.duration_minutes}
                        onChange={(event) =>
                          setShowEditForm((prev) => ({
                            ...prev,
                            duration_minutes: event.target.value,
                          }))
                        }
                        required
                      />
                    </label>
                    <label className="admin-field">
                      <span>Price</span>
                      <input
                        type="number"
                        placeholder="Update ticket price"
                        min={1}
                        value={showEditForm.price}
                        onChange={(event) =>
                          setShowEditForm((prev) => ({
                            ...prev,
                            price: event.target.value,
                          }))
                        }
                        required
                      />
                    </label>
                    <label className="admin-field">
                      <span>Language</span>
                      <input
                        placeholder="Optional language"
                        value={showEditForm.language}
                        onChange={(event) =>
                          setShowEditForm((prev) => ({
                            ...prev,
                            language: event.target.value,
                          }))
                        }
                      />
                    </label>
                    <label className="admin-field">
                      <span>Rating</span>
                      <input
                        placeholder="Optional rating"
                        value={showEditForm.rating}
                        onChange={(event) =>
                          setShowEditForm((prev) => ({
                            ...prev,
                            rating: event.target.value,
                          }))
                        }
                      />
                    </label>
                    <label className="admin-field">
                      <span>Description</span>
                      <textarea
                        placeholder="Update show summary (minimum 32 characters)"
                        value={showEditForm.description}
                        onChange={(event) =>
                          setShowEditForm((prev) => ({
                            ...prev,
                            description: event.target.value,
                          }))
                        }
                        minLength={32}
                        required
                      />
                    </label>
                    <div className="admin-edit-actions">
                      <button className="ghost" type="button" onClick={cancelShowEdit}>
                        Cancel
                      </button>
                      <button className="primary" type="submit">
                        Save changes
                      </button>
                    </div>
                  </form>
                ) : null}
              </article>
            );
          })}
        </div>
      </section>
    );
  }

  function renderSchedulesPanel() {
    return (
      <section className="admin-panel-section">
        <div className="form-card admin-create-card">
          <h3 className="title-row">
            <Icon name="calendar" size={16} /> Schedule board
          </h3>
          <div className="admin-inline-form">
            <label className="admin-field">
              <span>Venue Filter</span>
              <select
                value={scheduleVenueFilter}
                onChange={(event) => setScheduleVenueFilter(event.target.value)}
              >
                <option value="all">All venues</option>
                {venues.map((venue) => (
                  <option value={venue.id} key={`schedule-filter-${venue.id}`}>
                    {venue.name}
                  </option>
                ))}
              </select>
            </label>
            <button
              className="ghost"
              type="button"
              onClick={() => setScheduleVenueFilter("all")}
            >
              Reset
            </button>
          </div>
        </div>

        {filteredSchedules.length === 0 ? (
          <p className="muted">No schedules found for selected filter.</p>
        ) : (
          <div className="admin-schedule-list">
            {filteredSchedules.map((schedule) => (
              <article
                className="admin-schedule-item"
                key={`schedule-board-${schedule.id}`}
              >
                <strong>{schedule.show_title}</strong>
                <span className="muted">{schedule.venue_name}</span>
                <span className="muted">{schedule.screen_name}</span>
                <span className="meta-chip">
                  <Icon name="clock" size={12} />
                  {formatTime12Hour(schedule.start_time)} -{" "}
                  {formatTime12Hour(schedule.end_time)}
                </span>
                <button
                  className="ghost"
                  type="button"
                  onClick={() => openVenueManager(schedule.venue_id)}
                >
                  Open Venue
                </button>
              </article>
            ))}
          </div>
        )}
      </section>
    );
  }

  return (
    <section className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow">
            <Icon name="admin" size={14} /> Admin hub
          </p>
          <h2>Admin Control Center</h2>
          <p className="muted">
            Use the side panel to focus on one task at a time.
          </p>
        </div>
      </div>

      <div className="admin-shell">
        <aside className="form-card admin-sidebar">
          <div className="admin-sidebar-head">
            <h3>Workspace</h3>
            <p className="muted">Choose a section.</p>
          </div>

          <div className="admin-nav-list">
            {PANELS.map((panel) => (
              <button
                key={panel.id}
                className={`admin-nav-btn${activePanel === panel.id ? " active" : ""}`}
                type="button"
                onClick={() => setActivePanel(panel.id)}
              >
                <Icon name={panel.icon} size={14} />
                {panel.label}
              </button>
            ))}
          </div>


          <button
            className="dashboard-sidebar-btn"
            type="button"
            onClick={loadAdminData}
          >
            Refresh data
          </button>
        </aside>

        <div className="admin-main-panel">
          {activePanel === "venues" ? renderVenuesPanel() : null}
          {activePanel === "shows" ? renderShowsPanel() : null}
          {activePanel === "schedules" ? renderSchedulesPanel() : null}
          {message ? <p className="notice">{message}</p> : null}
        </div>
      </div>
      {pendingDelete ? (
        <div
          className="modal-backdrop"
          role="presentation"
          onClick={closeDeleteDialog}
        >
          <div
            className="confirm-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="admin-delete-confirm-title"
            onClick={(event) => event.stopPropagation()}
          >
            <h3 id="admin-delete-confirm-title">
              {pendingDelete.entity === "venue" ? "Mark venue inactive" : "Cancel show"} "{pendingDelete.label}"?
            </h3>
            <p className="muted">
              This will stop future bookings and trigger refunds for related cancelled bookings.
            </p>
            <div className="confirm-modal-actions">
              <button className="ghost" type="button" onClick={closeDeleteDialog}>
                Cancel
              </button>
              <button className="primary danger-btn" type="button" onClick={confirmDelete}>
                Confirm
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
