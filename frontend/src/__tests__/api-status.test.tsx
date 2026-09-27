import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ApiStatus } from "@/components/api-status";

describe("ApiStatus", () => {
  it("announces an available API in an accessible live status region", () => {
    render(<ApiStatus status="available" />);

    const status = screen.getByRole("status");
    expect(status.getAttribute("aria-live")).toBe("polite");
    expect(screen.getByText(/^API\s+disponible$/)).toBe(status);
  });

  it("announces an unavailable API without exposing technical details", () => {
    render(<ApiStatus status="unavailable" />);

    const status = screen.getByRole("status");
    expect(status.getAttribute("aria-live")).toBe("polite");
    expect(screen.getByText(/^API\s+no disponible$/)).toBe(status);
  });
});
