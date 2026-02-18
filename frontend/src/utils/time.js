function withUpperMeridiem(value) {
  return String(value || "").replace(/\b(am|pm)\b/gi, (match) => match.toUpperCase());
}

function parseTimeLike(value) {
  if (value === null || value === undefined || value === "") return null;
  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : new Date(value.getTime());
  }
  const raw = String(value).trim();
  const timeOnlyMatch = raw.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/);
  if (timeOnlyMatch) {
    const hours = Number(timeOnlyMatch[1]);
    const minutes = Number(timeOnlyMatch[2]);
    const seconds = Number(timeOnlyMatch[3] || "0");
    const parsed = new Date(0);
    parsed.setHours(hours, minutes, seconds, 0);
    return parsed;
  }
  const parsed = new Date(raw);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function formatTime12Hour(value, fallback = "--") {
  const parsed = parseTimeLike(value);
  if (!parsed) return fallback;
  return withUpperMeridiem(
    parsed.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true
    })
  );
}

export function formatTimeRange(startValue, endValue, fallback = "--") {
  return `${formatTime12Hour(startValue, fallback)} - ${formatTime12Hour(endValue, fallback)}`;
}
