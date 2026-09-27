import { describe, expect, it, vi } from "vitest";

import { checkApiHealth } from "@/lib/api-health";

describe("checkApiHealth", () => {
  it("reports available only when the API returns the expected health payload", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      Response.json({ status: "ok" }),
    );

    await expect(checkApiHealth({ baseUrl: "http://localhost:8000", fetcher })).resolves.toBe(
      "available",
    );
    expect(fetcher).toHaveBeenCalledWith(
      new URL("http://localhost:8000/health"),
      expect.objectContaining({ cache: "no-store", redirect: "error" }),
    );
  });

  it("reports unavailable when the API returns an unsuccessful response", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response(null, { status: 503 }));

    await expect(checkApiHealth({ baseUrl: "http://localhost:8000", fetcher })).resolves.toBe(
      "unavailable",
    );
  });

  it("reports unavailable when the health response has an unexpected body", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(Response.json({ status: "unknown" }));

    await expect(checkApiHealth({ baseUrl: "http://localhost:8000", fetcher })).resolves.toBe(
      "unavailable",
    );
  });

  it("rejects non-HTTP schemes without making a request", async () => {
    const fetcher = vi.fn<typeof fetch>();

    await expect(checkApiHealth({ baseUrl: "file:///etc/passwd", fetcher })).resolves.toBe(
      "unavailable",
    );
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("rejects URLs with embedded credentials without making a request", async () => {
    const fetcher = vi.fn<typeof fetch>();

    await expect(
      checkApiHealth({ baseUrl: "http://user:password@localhost:8000", fetcher }),
    ).resolves.toBe("unavailable");
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("does not expose request failures to the caller", async () => {
    const fetcher = vi.fn<typeof fetch>().mockRejectedValue(new Error("private network detail"));

    await expect(checkApiHealth({ baseUrl: "http://localhost:8000", fetcher })).resolves.toBe(
      "unavailable",
    );
  });
});
