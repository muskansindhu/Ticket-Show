import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { apiRequest, getToken, setToken } from "../apiClient.js";

const AuthContext = createContext(null);

function parseJwt(token) {
  try {
    const base64 = token.split(".")[1];
    const padded = base64.replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(padded);
    return JSON.parse(json);
  } catch {
    return {};
  }
}

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(getToken());
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (token) {
      loadMe();
    } else {
      setUser(null);
    }
  }, [token]);

  async function loadMe() {
    setLoading(true);
    try {
      const payload = parseJwt(token);
      const me = await apiRequest("/auth/me");
      setUser({ ...me, role: payload.role || "USER" });
    } catch (err) {
      setError(err.message);
      setUser(null);
      setToken("");
      setTokenState("");
    } finally {
      setLoading(false);
    }
  }

  async function login(payload) {
    setLoading(true);
    setError("");
    try {
      const data = await apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify(payload)
      });
      setToken(data.access_token);
      setTokenState(data.access_token);
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function register(payload) {
    setLoading(true);
    setError("");
    try {
      await apiRequest("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload)
      });
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    setToken("");
    setTokenState("");
    setUser(null);
  }

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      error,
      setError,
      login,
      register,
      logout
    }),
    [token, user, loading, error]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
