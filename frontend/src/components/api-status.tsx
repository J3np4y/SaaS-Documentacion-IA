import type { ApiHealth } from "@/lib/api-health";

type ApiStatusProps = {
  status: ApiHealth;
};

export function ApiStatus({ status }: ApiStatusProps) {
  const isAvailable = status === "available";

  return (
    <div className={`api-status ${isAvailable ? "api-status--up" : "api-status--down"}`}>
      <span className="api-status__dot" aria-hidden="true" />
      <span role="status" aria-live="polite">
        API {isAvailable ? "disponible" : "no disponible"}
      </span>
    </div>
  );
}
