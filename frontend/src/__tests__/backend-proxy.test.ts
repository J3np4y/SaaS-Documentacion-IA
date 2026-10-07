import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { POST } from "@/app/api/backend/[...path]/route";

describe("backend route proxy", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("forwards the same-origin cookie and origin and relays the session cookie", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ role: "owner" }), {
        status: 201,
        headers: {
          "content-type": "application/json",
          "set-cookie": "docs_assistant_session=opaque; HttpOnly; SameSite=Lax; Path=/",
        },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const request = new NextRequest("http://localhost:3000/api/backend/auth/login", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        cookie: "docs_assistant_session=previous",
        origin: "http://localhost:3000",
      },
      body: JSON.stringify({ email: "owner@example.com", password: "not-forwarded-to-browser" }),
    });

    const response = await POST(request, {
      params: Promise.resolve({ path: ["auth", "login"] }),
    });

    expect(response.status).toBe(201);
    expect(response.headers.get("set-cookie")).toContain("HttpOnly");
    const [target, init] = fetchMock.mock.calls[0];
    const forwardedHeaders = init?.headers as Headers;
    expect(target).toEqual(new URL("http://127.0.0.1:8000/auth/login"));
    expect(init?.method).toBe("POST");
    expect(forwardedHeaders.get("cookie")).toBe("docs_assistant_session=previous");
    expect(forwardedHeaders.get("origin")).toBe("http://localhost:3000");
  });

  it("does not proxy paths outside the authentication and organization API", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const request = new NextRequest("http://localhost:3000/api/backend/admin/secrets");

    const response = await POST(request, {
      params: Promise.resolve({ path: ["admin", "secrets"] }),
    });

    expect(response.status).toBe(404);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
