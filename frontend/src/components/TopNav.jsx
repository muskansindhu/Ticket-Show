import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/auth.jsx";
import Icon from "./Icon.jsx";

export default function TopNav({ items, variant = "user" }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [logoutConfirmOpen, setLogoutConfirmOpen] = useState(false);
  const menuRef = useRef(null);
  const username =
    user?.username ||
    user?.name ||
    (typeof user?.email === "string" ? user.email.split("@")[0] : "") ||
    "user";
  const isProfileRoute =
    location.pathname.startsWith("/profile") ||
    location.pathname.startsWith("/bookings");

  useEffect(() => {
    function handleClickOutside(event) {
      if (!menuRef.current?.contains(event.target)) {
        setMenuOpen(false);
      }
    }

    function handleEscape(event) {
      if (event.key === "Escape") {
        if (logoutConfirmOpen) {
          setLogoutConfirmOpen(false);
          return;
        }
        setMenuOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [logoutConfirmOpen]);

  function handleLogout() {
    setMenuOpen(false);
    setLogoutConfirmOpen(true);
  }

  function handleCancelLogout() {
    setLogoutConfirmOpen(false);
  }

  function handleConfirmLogout() {
    setLogoutConfirmOpen(false);
    logout();
    navigate("/");
  }

  function handleProfileOpen() {
    setMenuOpen(false);
    navigate("/profile");
  }

  return (
    <header className={`topbar ${variant}`}>
      <Link
        className="brand brand-link"
        to="/landing"
        aria-label="Go to landing page"
      >
        <div className="brand-badge">TS</div>
        <div>
          <p className="brand-title">Ticket Show</p>
          <p className="brand-sub">Premium ticketing</p>
        </div>
      </Link>
      <div className="nav-actions">
        <nav className="nav-links">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              aria-label={item.label}
              title={item.label}
              className={({ isActive }) =>
                `nav-link icon-only${isActive ? " active" : ""}`
              }
            >
              <Icon name={item.icon} size={18} />
              <span className="sr-only">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="profile-menu-wrap" ref={menuRef}>
          <button
            className={`profile-trigger icon-only${menuOpen || isProfileRoute ? " active" : ""}`}
            type="button"
            aria-label="Open profile menu"
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((prev) => !prev)}
          >
            <Icon name="profile" size={18} />
          </button>
          {menuOpen ? (
            <div className="profile-menu" role="menu">
              <p className="profile-menu-name">{username}</p>
              <button
                className="profile-menu-item"
                type="button"
                onClick={handleProfileOpen}
              >
                <Icon name="profile" size={14} /> Profile
              </button>
              <button
                className="profile-menu-item"
                type="button"
                onClick={handleLogout}
              >
                <Icon name="logout" size={14} /> Logout
              </button>
            </div>
          ) : null}
        </div>
      </div>
      {logoutConfirmOpen ? (
        <div
          className="modal-backdrop"
          role="presentation"
          onClick={handleCancelLogout}
        >
          <div
            className="confirm-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="logout-confirm-title"
            onClick={(event) => event.stopPropagation()}
          >
            <h3 id="logout-confirm-title">Logout from Ticket Show?</h3>
            <p className="muted">
              You will need to login again to continue booking tickets.
            </p>
            <div className="confirm-modal-actions">
              <button
                className="ghost"
                type="button"
                onClick={handleCancelLogout}
              >
                Cancel
              </button>
              <button
                className="primary danger-btn"
                type="button"
                onClick={handleConfirmLogout}
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </header>
  );
}
