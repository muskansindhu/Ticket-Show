const icons = {
  dashboard: (
    <path d="M4 13.5h7.5V4H4v9.5Zm8.5 6.5H20V4h-7.5v16Zm-8.5 0H11v-5.5H4V20Z" />
  ),
  profile: (
    <>
      <path d="M12 12.5a4 4 0 1 0-4-4 4 4 0 0 0 4 4Z" />
      <path d="M20 20c0-3.3-3.6-6-8-6s-8 2.7-8 6" />
    </>
  ),
  admin: (
    <path d="M12 3 4 6v6c0 5 3.6 9.7 8 10 4.4-.3 8-5 8-10V6l-8-3Zm0 5.5 3.2 3.2-3.2 3.2-3.2-3.2L12 8.5Z" />
  ),
  ticket: (
    <path d="M5 7h14a2 2 0 0 1 2 2v2a2 2 0 1 0 0 4v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-2a2 2 0 1 0 0-4V9a2 2 0 0 1 2-2Z" />
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="8" />
      <path d="M12 8v5l3 2" />
    </>
  ),
  location: (
    <>
      <path d="M12 21s6-6.2 6-11a6 6 0 0 0-12 0c0 4.8 6 11 6 11Z" />
      <circle cx="12" cy="10" r="2" />
    </>
  ),
  seat: (
    <>
      <path d="M7 12V7a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v5" />
      <path d="M5 12v4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4" />
    </>
  ),
  credit: (
    <>
      <rect x="2" y="5" width="20" height="14" rx="2" />
      <path d="M2 10h20" />
    </>
  ),
  wallet: (
    <>
      <path d="M3 7h18a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z" />
      <path d="M16 11h4v4h-4z" />
      <path d="M3 7V6a2 2 0 0 1 2-2h14" />
    </>
  ),
  spark: (
    <path d="m12 3 1.7 4.3L18 9l-4.3 1.7L12 15l-1.7-4.3L6 9l4.3-1.7L12 3Z" />
  ),
  play: (
    <path d="m9 7 8 5-8 5Z" />
  ),
  calendar: (
    <path d="M7 3v3m10-3v3M4 8h16m-2 2v9H6V10h12Z" />
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </>
  ),
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </>
  ),
  moon: (
    <path d="M21 12.8A8.5 8.5 0 1 1 11.2 3 6.5 6.5 0 0 0 21 12.8Z" />
  ),
  mail: (
    <>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m3 7 9 6 9-6" />
    </>
  ),
  lock: (
    <>
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11V8a4 4 0 1 1 8 0v3" />
    </>
  ),
  user: (
    <>
      <path d="M12 12.5a4 4 0 1 0-4-4 4 4 0 0 0 4 4Z" />
      <path d="M20 20c0-3.3-3.6-6-8-6s-8 2.7-8 6" />
    </>
  ),
  eye: (
    <>
      <path d="M2 12s4-6 10-6 10 6 10 6-4 6-10 6-10-6-10-6Z" />
      <circle cx="12" cy="12" r="2.5" />
    </>
  ),
  eyeOff: (
    <>
      <path d="M3 3l18 18" />
      <path d="M2 12s4-6 10-6a9.7 9.7 0 0 1 6.6 2.6" />
      <path d="M22 12s-4 6-10 6a9.7 9.7 0 0 1-6.6-2.6" />
    </>
  ),
  film: (
    <>
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <path d="M7 4v16M17 4v16M2 8h5M2 16h5M17 8h5M17 16h5" />
    </>
  ),
  logout: (
    <>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="m16 17 5-5-5-5" />
      <path d="M21 12H9" />
    </>
  ),
  arrowRight: (
    <path d="M5 12h14m-6-6 6 6-6 6" />
  ),
  star: (
    <path d="m12 3 2.6 5.4 6 .9-4.3 4.2 1 6-5.3-2.8-5.3 2.8 1-6L3.4 9.3l6-.9L12 3Z" />
  )
};

export default function Icon({ name, size = 18, className = "" }) {
  const path = icons[name];
  if (!path) return null;
  return (
    <span className={`icon ${className}`} aria-hidden="true">
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {path}
      </svg>
    </span>
  );
}
