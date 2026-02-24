import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiRequest, formatCurrency } from "../apiClient.js";
import Icon from "../components/Icon.jsx";
import { useAuth } from "../context/auth.jsx";

function formatDate(value) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  });
}

function formatDateTime(value) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function normalizePasswordError(message) {
  const text = String(message || "").toLowerCase();
  if (!text || text.includes("not found") || text.includes("404")) {
    return "Password updates are not available yet.";
  }
  return message;
}

export default function Profile() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [form, setForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: ""
  });
  const [wallet, setWallet] = useState(null);
  const [walletLoading, setWalletLoading] = useState(false);
  const [walletError, setWalletError] = useState("");

  const displayName = useMemo(
    () =>
      user?.username ||
      user?.name ||
      (typeof user?.email === "string" ? user.email.split("@")[0] : "") ||
      "User",
    [user]
  );

  useEffect(() => {
    async function loadWallet() {
      setWalletLoading(true);
      setWalletError("");
      try {
        const data = await apiRequest("/auth/wallet");
        setWallet(data);
      } catch (err) {
        setWalletError(err.message);
      } finally {
        setWalletLoading(false);
      }
    }
    loadWallet();
  }, []);

  async function handlePasswordSubmit(event) {
    event.preventDefault();
    setPasswordMessage("");
    setPasswordError("");

    if (form.newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters.");
      return;
    }

    if (form.newPassword !== form.confirmPassword) {
      setPasswordError("New password and confirm password do not match.");
      return;
    }

    setChangingPassword(true);
    try {
      await apiRequest("/auth/change-password", {
        method: "POST",
        body: JSON.stringify({
          current_password: form.currentPassword,
          new_password: form.newPassword
        })
      });

      setPasswordMessage("Password updated successfully.");
      setForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
      setShowPasswordForm(false);
    } catch (err) {
      setPasswordError(normalizePasswordError(err.message));
    } finally {
      setChangingPassword(false);
    }
  }

  return (
    <section className="page profile-page">
      <div className="profile-hero reveal" style={{ "--delay": "0.03s" }}>
        <div className="profile-avatar">
          <Icon name="profile" size={34} />
        </div>
        <h2>{displayName}</h2>
        <p className="muted">Manage your account settings.</p>
      </div>

      <article className="form-card profile-panel reveal" style={{ "--delay": "0.08s" }}>
        <h3>Account Details</h3>
        <div className="profile-detail-grid">
          <div className="profile-detail-item">
            <span className="section-title">Username</span>
            <strong>{user?.username || "--"}</strong>
          </div>
          <div className="profile-detail-item">
            <span className="section-title">Email</span>
            <strong>{user?.email || "--"}</strong>
          </div>
          <div className="profile-detail-item">
            <span className="section-title">Joined</span>
            <strong>{formatDate(user?.created_at)}</strong>
          </div>
        </div>

        <div className="profile-password-head">
          <div>
            <p className="section-title">Password</p>
            <p className="muted">Change your account password.</p>
          </div>
          <button
            className="ghost"
            type="button"
            onClick={() => {
              setShowPasswordForm((current) => !current);
              setPasswordError("");
              setPasswordMessage("");
            }}
          >
            <Icon name="lock" size={14} />
            {showPasswordForm ? "Hide" : "Change Password"}
          </button>
        </div>

        {showPasswordForm ? (
          <form className="profile-password-form" onSubmit={handlePasswordSubmit}>
            <label>
              Current password
              <input
                type="password"
                value={form.currentPassword}
                onChange={(event) => setForm({ ...form, currentPassword: event.target.value })}
                required
              />
            </label>
            <label>
              New password
              <input
                type="password"
                value={form.newPassword}
                onChange={(event) => setForm({ ...form, newPassword: event.target.value })}
                required
              />
            </label>
            <label>
              Confirm new password
              <input
                type="password"
                value={form.confirmPassword}
                onChange={(event) => setForm({ ...form, confirmPassword: event.target.value })}
                required
              />
            </label>
            <div className="profile-password-actions">
              <button className="primary" type="submit" disabled={changingPassword}>
                {changingPassword ? "Updating..." : "Update password"}
              </button>
            </div>
          </form>
        ) : null}

        {passwordError ? <p className="notice">{passwordError}</p> : null}
        {passwordMessage ? <p className="notice">{passwordMessage}</p> : null}
      </article>

      <article className="form-card profile-panel reveal" style={{ "--delay": "0.1s" }}>
        <div className="profile-password-head" style={{ marginBottom: "0.5rem", paddingBottom: 0, border: "none" }}>
          <div>
            <h3>Wallet</h3>
          </div>
          <button
            className="ghost"
            type="button"
            onClick={() => navigate("/transactions")}
          >
            <Icon name="wallet" size={14} />
            View Transactions
          </button>
        </div>

        <div className="profile-detail-grid">
          <div className="profile-detail-item" style={{ flex: 1, border: "none" }}>
            <span className="section-title">Total Amount Available</span>
            <strong style={{ fontSize: "1.5rem" }}>{formatCurrency(wallet?.current_amount ?? user?.wallet_balance ?? 0)}</strong>
          </div>
        </div>

        {walletLoading ? <p className="muted" style={{ fontSize: "0.85rem", marginTop: 0 }}>Loading wallet...</p> : null}
        {walletError ? <p className="notice">{walletError}</p> : null}
      </article>

      <button
        className="profile-bookings-bar reveal"
        type="button"
        style={{ "--delay": "0.12s" }}
        onClick={() => navigate("/bookings")}
      >
        <span className="icon-row">
          <Icon name="ticket" size={15} />
          Bookings
        </span>
        <Icon name="arrowRight" size={16} />
      </button>
    </section>
  );
}
