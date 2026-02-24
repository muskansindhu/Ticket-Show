import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/auth.jsx";
import Icon from "../components/Icon.jsx";
import poster1 from "../assets/posters/poster-1.jpg";
import poster2 from "../assets/posters/poster-5.jpg";
import poster3 from "../assets/posters/poster-6.jpg";

const initialRegister = { email: "", username: "", password: "" };
const initialLogin = { email: "", password: "" };

const posters = [poster1, poster2, poster3];

export default function AuthPage() {
  const { login, register, loading, error, setError, token } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [registerForm, setRegisterForm] = useState(initialRegister);
  const [loginForm, setLoginForm] = useState(initialLogin);
  const [notice, setNotice] = useState("");
  const [showLoginPass, setShowLoginPass] = useState(false);
  const [showRegisterPass, setShowRegisterPass] = useState(false);

  useEffect(() => {
    if (token) {
      navigate("/", { replace: true });
    }
  }, [token, navigate]);

  async function handleLogin(event) {
    event.preventDefault();
    setNotice("");
    await login(loginForm);
  }

  async function handleRegister(event) {
    event.preventDefault();
    setNotice("");
    const ok = await register(registerForm);
    if (ok) {
      setNotice("Account created. Please sign in.");
      setLoginForm({
        email: registerForm.email,
        password: registerForm.password,
      });
      setRegisterForm(initialRegister);
      setMode("login");
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-left">
        <header className="auth-top reveal" style={{ "--delay": "0.05s" }}>
          <div className="brand">
            <div className="brand-badge">TS</div>
            <div>
              <p className="brand-title">Ticket Show</p>
              <p className="brand-sub">Premium ticketing</p>
            </div>
          </div>
        </header>

        <div className="auth-card reveal" style={{ "--delay": "0.12s" }}>
          <div className="auth-header">
            <p className="eyebrow">
              <Icon name="ticket" size={14} /> Access pass
            </p>
            <h1>{mode === "login" ? "Welcome back" : "Create your account"}</h1>
            <p className="muted">
              No guest mode. Sign in to explore schedules, seats, and bookings.
            </p>
          </div>

          <div className="tab-row">
            <button
              className={mode === "login" ? "tab active" : "tab"}
              type="button"
              onClick={() => {
                setError("");
                setMode("login");
              }}
            >
              Login
            </button>
            <button
              className={mode === "register" ? "tab active" : "tab"}
              type="button"
              onClick={() => {
                setError("");
                setMode("register");
              }}
            >
              Register
            </button>
          </div>

          {mode === "login" ? (
            <form onSubmit={handleLogin} className="form-grid">
              <label>
                Email
                <div className="input-wrap">
                  <Icon name="mail" size={16} className="input-icon" />
                  <input
                    type="email"
                    value={loginForm.email}
                    onChange={(event) =>
                      setLoginForm({ ...loginForm, email: event.target.value })
                    }
                    required
                  />
                </div>
              </label>
              <label>
                Password
                <div className="input-wrap">
                  <Icon name="lock" size={16} className="input-icon" />
                  <input
                    type={showLoginPass ? "text" : "password"}
                    value={loginForm.password}
                    onChange={(event) =>
                      setLoginForm({
                        ...loginForm,
                        password: event.target.value,
                      })
                    }
                    required
                  />
                  <button
                    className="icon-btn"
                    type="button"
                    onClick={() => setShowLoginPass((prev) => !prev)}
                    aria-label={
                      showLoginPass ? "Hide password" : "Show password"
                    }
                  >
                    <Icon name={showLoginPass ? "eyeOff" : "eye"} size={16} />
                  </button>
                </div>
              </label>
              <button className="primary" type="submit" disabled={loading}>
                {loading ? "Signing in..." : "Sign in"}
              </button>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="form-grid">
              <label>
                Email
                <div className="input-wrap">
                  <Icon name="mail" size={16} className="input-icon" />
                  <input
                    type="email"
                    value={registerForm.email}
                    onChange={(event) =>
                      setRegisterForm({
                        ...registerForm,
                        email: event.target.value,
                      })
                    }
                    required
                  />
                </div>
              </label>
              <label>
                Username
                <div className="input-wrap">
                  <Icon name="user" size={16} className="input-icon" />
                  <input
                    value={registerForm.username}
                    onChange={(event) =>
                      setRegisterForm({
                        ...registerForm,
                        username: event.target.value,
                      })
                    }
                    required
                  />
                </div>
              </label>
              <label>
                Password
                <div className="input-wrap">
                  <Icon name="lock" size={16} className="input-icon" />
                  <input
                    type={showRegisterPass ? "text" : "password"}
                    value={registerForm.password}
                    onChange={(event) =>
                      setRegisterForm({
                        ...registerForm,
                        password: event.target.value,
                      })
                    }
                    required
                  />
                  <button
                    className="icon-btn"
                    type="button"
                    onClick={() => setShowRegisterPass((prev) => !prev)}
                    aria-label={
                      showRegisterPass ? "Hide password" : "Show password"
                    }
                  >
                    <Icon
                      name={showRegisterPass ? "eyeOff" : "eye"}
                      size={16}
                    />
                  </button>
                </div>
              </label>
              <button className="primary" type="submit" disabled={loading}>
                {loading ? "Creating..." : "Create account"}
              </button>
            </form>
          )}

          {(notice || error) && <div className="notice">{notice || error}</div>}
        </div>
      </div>

      <div className="auth-right">
        <div className="auth-copy reveal" style={{ "--delay": "0.15s" }}>
          <h2>Own your night.</h2>
          <p>
            Pick seats with confidence, track availability, and confirm payments
            in seconds.
          </p>
          <div className="auth-inline-points">
            <span className="auth-inline-item">
              <Icon name="seat" size={14} /> Seat map
            </span>
            <span className="auth-sep" aria-hidden="true">
              |
            </span>
            <span className="auth-inline-item">
              <Icon name="calendar" size={14} /> Smart schedules
            </span>
            <span className="auth-sep" aria-hidden="true">
              |
            </span>
            <span className="auth-inline-item">
              <Icon name="credit" size={14} /> Fast checkout
            </span>
          </div>
        </div>
        <div className="poster-stack reveal" style={{ "--delay": "0.22s" }}>
          {posters.map((src, index) => (
            <img
              key={src}
              className={`poster p${index + 1}`}
              src={src}
              alt="Poster"
            />
          ))}
        </div>
      </div>
    </div>
  );
}
