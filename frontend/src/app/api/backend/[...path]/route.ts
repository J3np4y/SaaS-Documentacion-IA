import { NextRequest } from "next/server";

type RouteContext = { params: Promise<{ path: string[] }> };

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const API_TIMEOUT_MS = 5_000;

function isAllowedPath(path: string[]): boolean {
  const joined = path.join("/");
  return (
    ["auth/register", "auth/login", "auth/logout", "auth/me", "organizations/me/members",
      "organizations/me/invitations"].includes(joined) ||
    /^organizations\/me\/members\/[0-9a-f-]{36}$/i.test(joined)
  );
}

async function forward(request: NextRequest, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  if (!isAllowedPath(path)) {
    return Response.json({ detail: "Ruta no disponible" }, { status: 404 });
  }

  const baseUrl = process.env.API_BASE_URL ?? DEFAULT_API_BASE_URL;
  let target: URL;
  try {
    target = new URL(`/${path.map(encodeURIComponent).join("/")}`, baseUrl);
    if (!["http:", "https:"].includes(target.protocol) || target.username || target.password) {
      return Response.json({ detail: "Servicio no disponible" }, { status: 503 });
    }
  } catch {
    return Response.json({ detail: "Servicio no disponible" }, { status: 503 });
  }

  const headers = new Headers({ accept: "application/json" });
  const contentType = request.headers.get("content-type");
  const cookie = request.headers.get("cookie");
  const origin = request.headers.get("origin");
  if (contentType) headers.set("content-type", contentType);
  if (cookie) headers.set("cookie", cookie);
  if (origin) headers.set("origin", origin);

  try {
    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body: ["GET", "HEAD"].includes(request.method) ? undefined : await request.text(),
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(API_TIMEOUT_MS),
    });
    const responseHeaders = new Headers();
    const upstreamContentType = upstream.headers.get("content-type");
    const setCookie = upstream.headers.get("set-cookie");
    if (upstreamContentType) responseHeaders.set("content-type", upstreamContentType);
    if (setCookie) responseHeaders.set("set-cookie", setCookie);
    responseHeaders.set("cache-control", "no-store");
    return new Response(upstream.status === 204 ? null : await upstream.text(), {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch {
    return Response.json({ detail: "Servicio no disponible" }, { status: 503 });
  }
}

export const GET = forward;
export const POST = forward;
export const PATCH = forward;
export const DELETE = forward;
