import { Link } from "react-router-dom";
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

const heroColumns = [
  [
    { title: "War of the Gods", src: poster1 },
    { title: "Interstellar", src: poster2 },
    { title: "The Hobbit", src: poster3 }
  ],
  [
    { title: "Arcane Forest", src: poster4 },
    { title: "Neon Streets", src: poster5 },
    { title: "Silent Moon", src: poster6 }
  ],
  [
    { title: "Frost Gate", src: poster7 },
    { title: "Shadow City", src: poster8 },
    { title: "Last Orbit", src: poster9 }
  ]
];

const highlights = [
  {
    icon: "seat",
    title: "Live Seat Locking"
  },
  {
    icon: "calendar",
    title: "Fast Show Discovery"
  },
  {
    icon: "credit",
    title: "Clear Checkout"
  }
];

const steps = [
  {
    id: "01",
    title: "Pick a show",
    sub: "Browse available titles and timings."
  },
  {
    id: "02",
    title: "Lock your seats",
    sub: "Choose seats while they stay reserved."
  },
  {
    id: "03",
    title: "Pay and confirm",
    sub: "Finish checkout and get instant confirmation."
  }
];

export default function Landing() {
  const { token } = useAuth();
  const isLoggedIn = Boolean(token);

  return (
    <section className="landing apple-landing">
      <div className="landing-glow"></div>
      <div className="landing-shell clean-shell">
        <header className="landing-top reveal" style={{ "--delay": "0.04s" }}>
          <div className="brand">
            <div className="brand-badge">TS</div>
            <div>
              <p className="brand-title">Ticket Show</p>
              <p className="brand-sub">Modern booking platform</p>
            </div>
          </div>
          <div className="landing-actions">
            {!isLoggedIn ? (
              <>
                <Link className="ghost" to="/auth"><Icon name="user" size={14} /> Login</Link>
                <Link className="primary" to="/auth"><Icon name="spark" size={14} /> Create account</Link>
              </>
            ) : null}
          </div>
        </header>

        <section className="apple-hero reveal" style={{ "--delay": "0.1s" }}>
          <div className="apple-copy">
            <p className="eyebrow"><Icon name="spark" size={14} /> Black + Neon Experience</p>
            <h1>Book tickets with a cleaner, calmer flow.</h1>
            <p className="lead">
              Live availability, smooth seat selection, and fast checkout.
            </p>
            <div className="apple-actions">
              {isLoggedIn ? (
                <>
                  <Link className="primary" to="/"><Icon name="ticket" size={16} /> Explore movies now</Link>
                  <Link className="ghost" to="/venues"><Icon name="location" size={14} /> Browse by venue</Link>
                </>
              ) : (
                <>
                  <Link className="primary" to="/auth"><Icon name="ticket" size={16} /> Get started</Link>
                  <Link className="ghost" to="/auth"><Icon name="arrowRight" size={14} /> Explore dashboard</Link>
                </>
              )}
            </div>
            <div className="apple-metrics">
              <span className="meta-chip"><Icon name="film" size={12} /> 200+ shows</span>
              <span className="meta-chip"><Icon name="location" size={12} /> 64 venues</span>
            </div>
          </div>

          <div className="apple-visual" aria-hidden="true">
            <div className="apple-reel">
              {heroColumns.map((column, columnIndex) => {
                const looped = [...column, ...column];
                return (
                  <div className={`apple-reel-column c${columnIndex + 1}`} key={`column-${columnIndex}`}>
                    {looped.map((poster, posterIndex) => (
                      <article className="apple-reel-card" key={`${poster.title}-${posterIndex}`}>
                        <img src={poster.src} alt={poster.title} loading="lazy" />
                        <div className="apple-reel-info">{poster.title}</div>
                      </article>
                    ))}
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        <section className="apple-feature-row reveal" style={{ "--delay": "0.16s" }}>
          {highlights.map((item) => (
            <article className="apple-feature" key={item.title}>
              <p className="eyebrow"><Icon name={item.icon} size={13} /> {item.title}</p>
            </article>
          ))}
        </section>

        <section className="apple-steps reveal" style={{ "--delay": "0.2s" }}>
          <div className="section-head">
            <p className="eyebrow"><Icon name="calendar" size={13} /> How It Works</p>
            <h2>Three quick steps.</h2>
          </div>
          <div className="apple-step-grid">
            {steps.map((step) => (
              <article className="apple-step" key={step.id}>
                <span className="apple-step-id">{step.id}</span>
                <h3>{step.title}</h3>
                <p className="apple-step-sub">{step.sub}</p>
              </article>
            ))}
          </div>
        </section>

        <footer className="apple-footer reveal" style={{ "--delay": "0.24s" }}>
          <p className="apple-footer-text">
            © {new Date().getFullYear()} Ticket Show. Built for better booking.
          </p>
        </footer>
      </div>
    </section>
  );
}
