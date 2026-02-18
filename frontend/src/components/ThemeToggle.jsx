export default function ThemeToggle({ theme, onToggle }) {
  return (
    <button className="chip" type="button" onClick={onToggle}>
      {theme === "dark" ? "Light mode" : "Dark mode"}
    </button>
  );
}
