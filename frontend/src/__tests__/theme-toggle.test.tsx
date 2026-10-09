import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ThemeToggle } from "@/components/theme-toggle";

describe("ThemeToggle", () => {
  afterEach(() => {
    document.documentElement.removeAttribute("data-theme");
    window.localStorage.clear();
  });

  it("switches between light and dark themes and persists the choice", async () => {
    document.documentElement.dataset.theme = "light";
    render(<ThemeToggle />);

    fireEvent.click(screen.getByRole("button", { name: "Activar modo oscuro" }));
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(window.localStorage.getItem("nexora-theme")).toBe("dark");
    expect(screen.getByRole("button", { name: "Activar modo claro" }).getAttribute("aria-pressed")).toBe("true");

    fireEvent.click(screen.getByRole("button", { name: "Activar modo claro" }));
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(window.localStorage.getItem("nexora-theme")).toBe("light");
  });

  it("reflects the theme already selected on the document", async () => {
    document.documentElement.dataset.theme = "dark";
    render(<ThemeToggle />);

    expect(await screen.findByRole("button", { name: "Activar modo claro" })).toBeTruthy();
  });
});
