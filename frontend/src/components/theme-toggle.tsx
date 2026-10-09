"use client";

import { useSyncExternalStore } from "react";

type Theme = "light" | "dark";

function subscribeToTheme(callback: () => void) {
  window.addEventListener("nexora-theme-change", callback);
  return () => window.removeEventListener("nexora-theme-change", callback);
}

function getTheme(): Theme {
  return document.documentElement.dataset.theme === "dark" ? "dark" : "light";
}

export function ThemeToggle() {
  const theme = useSyncExternalStore(subscribeToTheme, getTheme, () => "light");

  function toggleTheme() {
    const nextTheme: Theme = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = nextTheme;
    window.dispatchEvent(new Event("nexora-theme-change"));
    window.localStorage.setItem("nexora-theme", nextTheme);
  }

  const nextThemeLabel = theme === "dark" ? "claro" : "oscuro";

  return (
    <button
      className="theme-toggle"
      type="button"
      aria-label={`Activar modo ${nextThemeLabel}`}
      aria-pressed={theme === "dark"}
      onClick={toggleTheme}
    >
      {theme === "dark" ? (
        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42" />
        </svg>
      ) : (
        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none">
          <path d="M20.2 15.3A8.7 8.7 0 0 1 8.7 3.8 8.9 8.9 0 1 0 20.2 15.3Z" />
        </svg>
      )}
      <span>{theme === "dark" ? "Oscuro" : "Claro"}</span>
    </button>
  );
}
