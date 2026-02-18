import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Landing from "./pages/Landing.jsx";
import AuthPage from "./pages/Auth.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import ShowDetail from "./pages/ShowDetail.jsx";
import Seats from "./pages/Seats.jsx";
import Payment from "./pages/Payment.jsx";
import Profile from "./pages/Profile.jsx";
import Venues from "./pages/Venues.jsx";
import Admin from "./pages/Admin.jsx";
import NotFound from "./pages/NotFound.jsx";
import { useAuth } from "./context/auth.jsx";

export default function App() {
  const { token, user, loading } = useAuth();

  if (!token) {
    return (
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/landing" element={<Landing />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    );
  }

  if (loading && !user) {
    return <div className="page"><p className="muted">Loading...</p></div>;
  }

  const isAdmin = user?.role === "ADMIN";
  const navItems = isAdmin
    ? [
        { to: "/", label: "Dashboard", end: true, icon: "dashboard" },
        { to: "/admin", label: "Admin", icon: "admin" }
      ]
    : [{ to: "/", label: "Dashboard", end: true, icon: "dashboard" }];

  return (
    <Routes>
      <Route path="/landing" element={<Landing />} />
      <Route
        path="/"
        element={<Layout items={navItems} variant={isAdmin ? "admin" : "user"} />}
      >
        <Route index element={<Dashboard />} />
        <Route path="venues" element={<Venues />} />
        <Route path="shows/:showId" element={<ShowDetail />} />
        <Route path="seats/:scheduleId" element={<Seats />} />
        <Route path="payment" element={<Payment />} />
        <Route path="profile" element={<Profile />} />
        <Route path="auth" element={<Navigate to="/" replace />} />
        <Route
          path="admin"
          element={isAdmin ? <Admin /> : <Navigate to="/" replace />}
        />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
