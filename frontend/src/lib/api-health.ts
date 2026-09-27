export type ApiHealth = "available" | "unavailable";

type Fetcher = typeof fetch;

type CheckApiHealthOptions = {
  baseUrl?: string;
  fetcher?: Fetcher;
};

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const HEALTH_TIMEOUT_MS = 3_000;

export async function checkApiHealth({
  baseUrl = process.env.API_BASE_URL ?? DEFAULT_API_BASE_URL,
  fetcher = fetch,
}: CheckApiHealthOptions = {}): Promise<ApiHealth> {
  try {
    const apiUrl = new URL(baseUrl);

    // API_BASE_URL is server-only configuration; validate its scheme before making a request.
    if (!["http:", "https:"].includes(apiUrl.protocol) || apiUrl.username || apiUrl.password) {
      return "unavailable";
    }

    const response = await fetcher(new URL("/health", apiUrl), {
      cache: "no-store",
      headers: { accept: "application/json" },
      redirect: "error",
      signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS),
    });

    if (!response.ok) {
      return "unavailable";
    }

    const payload: unknown = await response.json();
    return isHealthyPayload(payload) ? "available" : "unavailable";
  } catch {
    // Keep network details and internal URLs out of the rendered page and browser response.
    return "unavailable";
  }
}

function isHealthyPayload(payload: unknown): payload is { status: "ok" } {
  return (
    typeof payload === "object" &&
    payload !== null &&
    "status" in payload &&
    payload.status === "ok"
  );
}
