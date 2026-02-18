import { useEffect, useMemo, useState } from "react";
import { apiRequest, formatCurrency } from "../apiClient.js";

export default function Home() {
  const [shows, setShows] = useState([]);
  const [venues, setVenues] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [showsData, venuesData] = await Promise.all([
          apiRequest("/shows"),
          apiRequest("/venues/?limit=100")
        ]);
        setShows(showsData);
        setVenues(venuesData);
      } catch (err) {
        setError(err.message);
      }
    }
    load();
  }, []);

  const featured = useMemo(() => shows.slice(0, 4), [shows]);

  return (
    <section className="page">
      <div className="hero">
        <div>
          <p className="eyebrow">Now playing</p>
          <h1>Design-forward ticketing for premium shows.</h1>
          <p className="lead">
            Manage venues, schedules, and bookings with a cohesive experience
            for teams and audiences.
          </p>
          {error ? <p className="notice">{error}</p> : null}
          <div className="stat-grid">
            <div className="stat">
              <span>Shows</span>
              <strong>{shows.length}</strong>
            </div>
            <div className="stat">
              <span>Venues</span>
              <strong>{venues.length}</strong>
            </div>
            <div className="stat">
              <span>Active cities</span>
              <strong>12</strong>
            </div>
          </div>
        </div>
        <div className="hero-panel">
          <h2>Featured shows</h2>
          <div className="card-stack">
            {featured.map((show) => (
              <div className="show-card" key={show.id}>
                <div>
                  <h3>{show.title}</h3>
                  <p>{show.description}</p>
                </div>
                <div className="show-meta">
                  <span>{show.language || "EN"}</span>
                  <span>{show.duration_minutes} min</span>
                  <span>{formatCurrency(show.price)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
