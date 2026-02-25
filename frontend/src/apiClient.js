const DEFAULT_BASE = "";
const INR_FORMATTER = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
});

export function getApiBase() {
  return import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE;
}

export function getToken() {
  return localStorage.getItem("ts_token") || "";
}

export function setToken(token) {
  if (token) {
    localStorage.setItem("ts_token", token);
  } else {
    localStorage.removeItem("ts_token");
  }
}

export async function apiRequest(path, options = {}) {
  const base = getApiBase();
  const headers = new Headers(options.headers || {});
  const isFormData =
    typeof FormData !== "undefined" && options.body instanceof FormData;
  if (!headers.has("Content-Type") && options.body && !isFormData) {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const url = base ? `${base}${path}` : path;
  const response = await fetch(url, {
    ...options,
    headers
  });

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    let message = "Request failed";
    if (typeof data === "string") {
      message = data;
    } else if (data?.detail) {
      message =
        typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } else if (data) {
      message = JSON.stringify(data);
    }
    throw new Error(message);
  }

  return data;
}

export function toQuery(params) {
  const search = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, value);
    }
  });
  const str = search.toString();
  return str ? `?${str}` : "";
}

export function formatCurrency(amount) {
  if (amount === undefined || amount === null) return "--";
  const num = Number(amount);
  return Number.isFinite(num) ? INR_FORMATTER.format(num) : INR_FORMATTER.format(0);
}

export function parseSeatIds(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => Number(item))
    .filter((item) => Number.isFinite(item));
}

export function makeIdempotencyKey() {
  if (crypto?.randomUUID) return crypto.randomUUID();
  return `key-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
