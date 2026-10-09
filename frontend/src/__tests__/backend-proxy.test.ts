import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GET, POST } from "@/app/api/backend/[...path]/route";

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

  it("forwards multipart file bytes without converting them to text", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: "document-id" }), {
        status: 201,
        headers: { "content-type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const boundary = "document-upload-boundary";
    const binary = new Uint8Array([0, 255, 1, 128]);
    const prefix = new TextEncoder().encode(
      `--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="sample.pdf"\r\nContent-Type: application/pdf\r\n\r\n`,
    );
    const suffix = new TextEncoder().encode(`\r\n--${boundary}--\r\n`);
    const body = new Uint8Array(prefix.length + binary.length + suffix.length);
    body.set(prefix);
    body.set(binary, prefix.length);
    body.set(suffix, prefix.length + binary.length);
    const request = new NextRequest("http://localhost:3000/api/backend/organizations/me/documents", {
      method: "POST",
      headers: {
        origin: "http://localhost:3000",
        "content-type": `multipart/form-data; boundary=${boundary}`,
      },
      body,
    });

    const response = await POST(request, {
      params: Promise.resolve({ path: ["organizations", "me", "documents"] }),
    });

    expect(response.status).toBe(201);
    const [, init] = fetchMock.mock.calls[0];
    const forwardedHeaders = init?.headers as Headers;
    expect(forwardedHeaders.get("content-type")).toContain(`boundary=${boundary}`);
    expect(new Uint8Array(init?.body as ArrayBuffer)).toEqual(body);
  });

  it("preserves binary downloads and safe response headers", async () => {
    const bytes = new Uint8Array([0, 255, 1, 128]);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(bytes, {
          status: 200,
          headers: {
            "content-type": "application/pdf",
            "content-disposition": 'attachment; filename="sample.pdf"',
            "x-content-type-options": "nosniff",
          },
        }),
      ),
    );
    const request = new NextRequest(
      "http://localhost:3000/api/backend/organizations/me/documents/123e4567-e89b-12d3-a456-426614174000/download",
    );
    const response = await GET(request, {
      params: Promise.resolve({
        path: ["organizations", "me", "documents", "123e4567-e89b-12d3-a456-426614174000", "download"],
      }),
    });

    expect(new Uint8Array(await response.arrayBuffer())).toEqual(bytes);
    expect(response.headers.get("content-disposition")).toContain("attachment");
    expect(response.headers.get("x-content-type-options")).toBe("nosniff");
    expect(response.headers.get("cache-control")).toBe("no-store");
  });

  it("forwards authorized document search paths and query parameters", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const request = new NextRequest(
      "http://localhost:3000/api/backend/organizations/me/documents/search?q=contrato",
    );

    const response = await GET(request, {
      params: Promise.resolve({ path: ["organizations", "me", "documents", "search"] }),
    });

    expect(response.status).toBe(200);
    expect(fetchMock.mock.calls[0][0]).toEqual(
      new URL("http://127.0.0.1:8000/organizations/me/documents/search?q=contrato"),
    );
  });

  it("allows only the document index endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ rag_status: "ready" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const request = new NextRequest(
      "http://localhost:3000/api/backend/organizations/me/documents/123e4567-e89b-12d3-a456-426614174000/index",
      { method: "POST", headers: { origin: "http://localhost:3000" } },
    );

    const response = await POST(request, {
      params: Promise.resolve({
        path: ["organizations", "me", "documents", "123e4567-e89b-12d3-a456-426614174000", "index"],
      }),
    });

    expect(response.status).toBe(200);
    expect(fetchMock.mock.calls[0][0]).toEqual(
      new URL("http://127.0.0.1:8000/organizations/me/documents/123e4567-e89b-12d3-a456-426614174000/index"),
    );
  });
});
