import { NextRequest } from "next/server";

type RouteContext = { params: Promise<{ path: string[] }> };

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const API_TIMEOUT_MS = 5_000;
const MAX_UPLOAD_REQUEST_BYTES = 10 * 1024 * 1024 + 64 * 1024;

function isAllowedPath(path: string[]): boolean {
  const joined = path.join("/");
  return (
    ["auth/register", "auth/login", "auth/logout", "auth/me", "organizations/me/members",
      "organizations/me/invitations", "organizations/me/documents"].includes(joined) ||
    /^organizations\/me\/documents\/[0-9a-f-]{36}(\/download)?$/i.test(joined) ||
    /^organizations\/me\/members\/[0-9a-f-]{36}$/i.test(joined)
  );
}

async function readBoundedUpload(request: NextRequest): Promise<ArrayBuffer | null> {
  const contentLength = Number(request.headers.get("content-length"));
  if (Number.isFinite(contentLength) && contentLength > MAX_UPLOAD_REQUEST_BYTES) {
    throw new RangeError("El archivo supera el límite de carga.");
  }
  if (!request.body) return null;

  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > MAX_UPLOAD_REQUEST_BYTES) {
      await reader.cancel();
      throw new RangeError("El archivo supera el límite de carga.");
    }
    chunks.push(value);
  }
  const body = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return body.buffer;
}

async function forward(request: NextRequest, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  if (!isAllowedPath(path)) {
    return Response.json({ detail: "Ruta no disponible" }, { status: 404 });
  }
  const joinedPath = path.join("/");
  let requestBody: BodyInit | undefined;
  if (request.method === "POST" && joinedPath === "organizations/me/documents") {
    try {
      requestBody = (await readBoundedUpload(request)) ?? undefined;
    } catch (cause) {
      if (cause instanceof RangeError) {
        return Response.json({ detail: cause.message }, { status: 413 });
      }
      throw cause;
    }
  } else if (!["GET", "HEAD"].includes(request.method)) {
    requestBody = await request.text();
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
      body: ["GET", "HEAD"].includes(request.method) ? undefined : requestBody,
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(
        joinedPath.startsWith("organizations/me/documents")
          ? 30_000
          : API_TIMEOUT_MS,
      ),
    });
    const responseHeaders = new Headers();
    for (const name of [
      "content-type",
      "content-disposition",
      "set-cookie",
      "x-content-type-options",
      "content-security-policy",
    ]) {
      const value = upstream.headers.get(name);
      if (value) responseHeaders.set(name, value);
    }
    responseHeaders.set("cache-control", "no-store");
    const responseBody = [204, 205, 304].includes(upstream.status)
      ? null
      : await upstream.arrayBuffer();
    return new Response(responseBody, {
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
