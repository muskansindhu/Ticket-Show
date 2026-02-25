import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiRequest, formatCurrency } from "../apiClient.js";
import Icon from "../components/Icon.jsx";
import { useAuth } from "../context/auth.jsx";
import poster1 from "../assets/posters/poster-1.jpg";
import poster2 from "../assets/posters/poster-2.jpg";
import poster3 from "../assets/posters/poster-3.jpg";
import poster4 from "../assets/posters/poster-4.jpg";
import poster5 from "../assets/posters/poster-5.jpg";
import poster6 from "../assets/posters/poster-6.jpg";
import poster7 from "../assets/posters/poster-7.jpg";
import poster8 from "../assets/posters/poster-8.jpg";
import poster9 from "../assets/posters/poster-9.jpg";

const posters = [
  poster1,
  poster2,
  poster3,
  poster4,
  poster5,
  poster6,
  poster7,
  poster8,
  poster9,
];
const genres = ["Action", "Drama", "Sci-Fi", "Thriller", "Romance"];
const formats = ["2D", "IMAX", "4DX", "Dolby"];

export default function Dashboard() {
  const { user } = useAuth();
  const [shows, setShows] = useState([]);
  const [error, setError] = useState("");
  const [searchError, setSearchError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState({ shows: [], venues: [] });
  const [searchLoading, setSearchLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    async function load() {
      try {
        const data = await apiRequest("/shows/?limit=50");
        setShows(data);
      } catch (err) {
        setError(err.message);
      }
    }
    load();
  }, []);

  useEffect(() => {
    const query = searchQuery.trim();
    if (!query) {
      setSearchResults({ shows: [], venues: [] });
      setSearchLoading(false);
      setSearchError("");
      return;
    }

    const timeoutId = window.setTimeout(async () => {
      setSearchLoading(true);
      try {
        const searchParams = new URLSearchParams({
          q: query,
          limit: "8",
        });
        if (user?.city) {
          searchParams.set("city", user.city);
        }
        const data = await apiRequest(`/search?${searchParams.toString()}`);
        setSearchResults({
          shows: Array.isArray(data?.shows) ? data.shows : [],
          venues: Array.isArray(data?.venues) ? data.venues : [],
        });
        setSearchError("");
      } catch (err) {
        setSearchError(err.message);
      } finally {
        setSearchLoading(false);
      }
    }, 300);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [searchQuery, user?.city]);

  const languages = Array.from(
    new Set(shows.map((show) => show.language || "English")),
  );

  return (
    <section className="page dashboard-page apple-dashboard">
      <aside className="dashboard-sidebar">
        <h3>Filters</h3>

        <div className="dashboard-filter-card">
          <div className="dashboard-filter-head">
            <p className="icon-inline">
              <Icon name="spark" size={13} /> Languages
            </p>
            <button type="button" className="filter-clear">
              Clear
            </button>
          </div>
          <div className="dashboard-filter-grid">
            {languages.map((lang) => (
              <span key={lang} className="dashboard-filter-chip">
                {lang}
              </span>
            ))}
          </div>
        </div>

        <div className="dashboard-filter-card collapsed">
          <div className="dashboard-filter-head">
            <p className="icon-inline">
              <Icon name="star" size={13} /> Genres
            </p>
            <button type="button" className="filter-clear">
              Clear
            </button>
          </div>
          <div className="dashboard-filter-row">
            {genres.map((genre) => (
              <span key={genre} className="dashboard-filter-chip muted-chip">
                {genre}
              </span>
            ))}
          </div>
        </div>

        <div className="dashboard-filter-card collapsed">
          <div className="dashboard-filter-head">
            <p className="icon-inline">
              <Icon name="ticket" size={13} /> Format
            </p>
            <button type="button" className="filter-clear">
              Clear
            </button>
          </div>
          <div className="dashboard-filter-row">
            {formats.map((format) => (
              <span key={format} className="dashboard-filter-chip muted-chip">
                {format}
              </span>
            ))}
          </div>
        </div>

        <button
          className="dashboard-sidebar-btn"
          type="button"
          onClick={() => navigate("/venues")}
        >
          Browse by venue
        </button>
      </aside>

      <div className="dashboard-main">
        <header className="dashboard-main-head">
          <div>
            <p className="eyebrow">
              <Icon name="film" size={14} /> Now showing
            </p>
            <h2>
              {user?.city ? `Movies in ${user.city}` : "Movies In Your City"}
            </h2>
          </div>
        </header>

        <div className="form-card" style={{ marginBottom: "1rem" }}>
          <label>
            Search shows and venues
            <div className="input-wrap">
              <Icon name="search" size={16} className="input-icon" />
              <input
                type="search"
                placeholder={user?.city ? `Search in ${user.city}` : "Search by show or venue"}
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
              />
            </div>
          </label>
          {searchLoading ? <p className="muted">Searching...</p> : null}
          {searchError ? <p className="notice">{searchError}</p> : null}
          {searchQuery.trim() ? (
            <div className="dashboard-filter-grid" style={{ marginTop: "0.75rem" }}>
              {searchResults.shows.map((show) => (
                <button
                  key={`show-result-${show.id}`}
                  type="button"
                  className="dashboard-filter-chip"
                  onClick={() => navigate(`/shows/${show.id}`)}
                >
                  <Icon name="film" size={12} /> {show.title}
                </button>
              ))}
              {searchResults.venues.map((venue) => (
                <button
                  key={`venue-result-${venue.id}`}
                  type="button"
                  className="dashboard-filter-chip"
                  onClick={() =>
                    navigate("/venues", { state: { preferredVenueId: venue.id } })
                  }
                >
                  <Icon name="location" size={12} /> {venue.name} ({venue.city})
                </button>
              ))}
              {!searchLoading &&
              searchResults.shows.length === 0 &&
              searchResults.venues.length === 0 ? (
                <p className="muted">No search results found.</p>
              ) : null}
            </div>
          ) : null}
        </div>

        {/* {languages.length > 0 ? (
          <div className="dashboard-lang-strip">
            {languages.map((lang) => (
              <span key={lang} className="meta-chip">
                {lang}
              </span>
            ))}
          </div>
        ) : null} */}

        {error ? <p className="notice">{error}</p> : null}

        <div className="dashboard-grid">
          {shows.map((show, index) => {
            const poster = posters[index % posters.length];
            const posterSrc = show.poster_url || poster;
            const language = show.language || "English";
            return (
              <article
                className="dashboard-movie-card clickable reveal"
                style={{ "--delay": `${index * 0.04}s` }}
                key={show.id}
                onClick={() =>
                  navigate(`/shows/${show.id}`, { state: { show } })
                }
                >
                <div className="dashboard-movie-poster">
                  <img src={posterSrc} alt={show.title} loading="lazy" />
                  <div className="dashboard-movie-meta">
                    <span className="icon-inline">
                      <Icon name="star" size={12} /> {show.rating || "NR"}
                    </span>
                    <span className="icon-inline">
                      <Icon name="clock" size={12} /> {show.duration_minutes}{" "}
                      min
                    </span>
                  </div>
                </div>
                <div className="dashboard-movie-info">
                  <h3>{show.title}</h3>
                  <p className="muted">
                    {show.rating || "A"} • {language}
                  </p>
                  <p className="muted dashboard-desc">{show.description}</p>
                  <p className="dashboard-price">
                    {formatCurrency(show.price)}
                  </p>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
