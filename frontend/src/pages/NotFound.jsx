import Icon from "../components/Icon.jsx";

export default function NotFound() {
  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow"><Icon name="search" size={14} /> 404</p>
          <h2>Page not found</h2>
          <p className="muted">The page you are looking for does not exist.</p>
        </div>
      </div>
    </section>
  );
}
