import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiRequest, formatCurrency } from "../apiClient.js";
import Icon from "../components/Icon.jsx";
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
const genres = ["Action", "Drama", "Sci-Fi", "Thriller", "Romance"];
const formats = ["2D", "IMAX", "4DX", "Dolby"];

export default function Dashboard() {
  const [shows, setShows] = useState([]);
  const [error, setError] = useState("");
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

  const languages = Array.from(
    new Set(shows.map((show) => show.language || "English"))
  );

  return (
    <section className="page dashboard-page apple-dashboard">
      <aside className="dashboard-sidebar">
        <h3>Filters</h3>

        <div className="dashboard-filter-card">
          <div className="dashboard-filter-head">
            <p className="icon-inline"><Icon name="spark" size={13} /> Languages</p>
            <button type="button" className="filter-clear">Clear</button>
          </div>
          <div className="dashboard-filter-grid">
            {languages.map((lang) => (
              <span key={lang} className="dashboard-filter-chip">{lang}</span>
            ))}
          </div>
        </div>

        <div className="dashboard-filter-card collapsed">
          <div className="dashboard-filter-head">
            <p className="icon-inline"><Icon name="star" size={13} /> Genres</p>
            <button type="button" className="filter-clear">Clear</button>
          </div>
          <div className="dashboard-filter-row">
            {genres.map((genre) => (
              <span key={genre} className="dashboard-filter-chip muted-chip">{genre}</span>
            ))}
          </div>
        </div>

        <div className="dashboard-filter-card collapsed">
          <div className="dashboard-filter-head">
            <p className="icon-inline"><Icon name="ticket" size={13} /> Format</p>
            <button type="button" className="filter-clear">Clear</button>
          </div>
          <div className="dashboard-filter-row">
            {formats.map((format) => (
              <span key={format} className="dashboard-filter-chip muted-chip">{format}</span>
            ))}
          </div>
        </div>

        <button
          className="dashboard-sidebar-btn"
          type="button"
          onClick={() => navigate("/venues")}
        >
          <Icon name="location" size={14} /> Browse by venue
        </button>
      </aside>

      <div className="dashboard-main">
        <header className="dashboard-main-head">
          <div>
            <p className="eyebrow"><Icon name="film" size={14} /> Now showing</p>
            <h2>Movies In Your City</h2>
          </div>
          <span className="meta-chip dashboard-count"><Icon name="ticket" size={12} /> {shows.length} shows</span>
        </header>

        {languages.length > 0 ? (
          <div className="dashboard-lang-strip">
            {languages.map((lang) => (
              <span key={lang} className="meta-chip">{lang}</span>
            ))}
          </div>
        ) : null}

        {error ? <p className="notice">{error}</p> : null}

        <div className="dashboard-grid">
          {shows.map((show, index) => {
            const poster = posters[index % posters.length];
            const language = show.language || "English";
            return (
              <article
                className="dashboard-movie-card clickable reveal"
                style={{ "--delay": `${index * 0.04}s` }}
                key={show.id}
                onClick={() => navigate(`/shows/${show.id}`, { state: { show } })}
              >
                <div className="dashboard-movie-poster">
                  <img src={poster} alt={show.title} loading="lazy" />
                  <div className="dashboard-movie-meta">
                    <span className="icon-inline"><Icon name="star" size={12} /> {show.rating || "NR"}</span>
                    <span className="icon-inline"><Icon name="clock" size={12} /> {show.duration_minutes} min</span>
                  </div>
                </div>
                <div className="dashboard-movie-info">
                  <h3>{show.title}</h3>
                  <p className="muted">{show.rating || "A"} • {language}</p>
                  <p className="muted dashboard-desc">{show.description}</p>
                  <p className="dashboard-price">{formatCurrency(show.price)}</p>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
