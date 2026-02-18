import { useEffect, useState } from "react";
import { apiRequest, formatCurrency } from "../apiClient.js";

export default function Shows() {
  const [shows, setShows] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await apiRequest("/shows?limit=50");
        setShows(data);
      } catch (err) {
        setError(err.message);
      }
    }
    load();
  }, []);

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h2>Shows</h2>
          <p>Browse all active shows and highlights.</p>
        </div>
      </div>
      {error ? <p className="notice">{error}</p> : null}
      <div className="grid-cards">
        {shows.map((show) => (
          <article className="show-card" key={show.id}>
            <div>
              <h3>{show.title}</h3>
              <p>{show.description}</p>
            </div>
            <div className="show-meta">
              <span>{show.language || "EN"}</span>
              <span>{show.duration_minutes} min</span>
              <span>{show.rating || "NR"}</span>
              <span>{formatCurrency(show.price)}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
