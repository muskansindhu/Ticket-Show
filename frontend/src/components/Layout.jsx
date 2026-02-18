import { Outlet } from "react-router-dom";
import TopNav from "./TopNav.jsx";

export default function Layout({ items, variant }) {
  return (
    <div className={`app-shell ${variant}`}>
      <TopNav items={items} variant={variant} />
      <main className="main-content">
        <Outlet />
      </main>
      <footer className="apple-footer">
        <p className="apple-footer-text">
          © {new Date().getFullYear()} Ticket Show. Built for better booking.
        </p>
      </footer>
    </div>
  );
}
