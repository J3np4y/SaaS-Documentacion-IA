"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  organization_id: string;
  organization_name: string;
  role: "owner" | "member";
};

type Member = Pick<AuthUser, "id" | "email" | "full_name" | "role">;
type AuthMode = "register" | "login";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/backend${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      accept: "application/json",
      ...(init?.body ? { "content-type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null);
    const detail =
      typeof payload === "object" &&
      payload !== null &&
      "detail" in payload &&
      typeof payload.detail === "string"
        ? payload.detail
        : "No se pudo completar la solicitud.";
    throw new Error(detail);
  }
  return response.status === 204 ? (undefined as T) : (await response.json()) as T;
}

export function AuthPanel() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<AuthMode>("register");
  const [error, setError] = useState("");
  const [members, setMembers] = useState<Member[]>([]);
  const [inviteCode, setInviteCode] = useState("");
  const [inviteExpires, setInviteExpires] = useState("");
  const [memberRoles, setMemberRoles] = useState<Record<string, Member["role"]>>({});

  const loadUser = useCallback(async () => {
    try {
      const current = await requestJson<AuthUser>("/auth/me");
      setUser(current);
      setError("");
    } catch (cause) {
      setUser(null);
      if (cause instanceof Error && cause.message !== "Autenticación requerida") {
        setError(cause.message);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const loadMembers = useCallback(async () => {
    try {
      const rows = await requestJson<Member[]>("/organizations/me/members");
      if (!Array.isArray(rows)) throw new Error("La respuesta de miembros no es válida.");
      setMembers(rows);
      setMemberRoles(Object.fromEntries(rows.map((member) => [member.id, member.role])));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudieron cargar los miembros.");
    }
  }, []);

  useEffect(() => {
    const task = window.setTimeout(() => void loadUser(), 0);
    return () => window.clearTimeout(task);
  }, [loadUser]);

  useEffect(() => {
    if (user?.role !== "owner") return;
    const task = window.setTimeout(() => void loadMembers(), 0);
    return () => window.clearTimeout(task);
  }, [user, loadMembers]);

  async function submitAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const values = new FormData(event.currentTarget);
    const invitation = String(values.get("invitation_code") ?? "").trim();
    const body = {
      email: String(values.get("email") ?? ""),
      password: String(values.get("password") ?? ""),
      ...(mode === "register"
        ? {
            full_name: String(values.get("full_name") ?? ""),
            ...(invitation
              ? { invitation_code: invitation }
              : { organization_name: String(values.get("organization_name") ?? "") }),
          }
        : {}),
    };
    try {
      const path = mode === "register" ? "/auth/register" : "/auth/login";
      const current = await requestJson<AuthUser>(path, {
        method: "POST",
        body: JSON.stringify(body),
      });
      setUser(current);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo iniciar sesión.");
    }
  }

  async function logout() {
    setError("");
    try {
      await requestJson<void>("/auth/logout", { method: "POST" });
      setUser(null);
      setMembers([]);
      setInviteCode("");
      setMode("login");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo cerrar la sesión.");
    }
  }

  async function createInvitation() {
    setError("");
    setInviteCode("");
    try {
      const invitation = await requestJson<{ code: string; expires_at: string }>(
        "/organizations/me/invitations",
        { method: "POST" },
      );
      setInviteCode(invitation.code);
      setInviteExpires(invitation.expires_at);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo crear la invitación.");
    }
  }

  async function saveRole(member: Member) {
    setError("");
    try {
      await requestJson<Member>(`/organizations/me/members/${member.id}`, {
        method: "PATCH",
        body: JSON.stringify({ role: memberRoles[member.id] }),
      });
      await loadMembers();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo cambiar el rol.");
    }
  }

  async function removeMember(member: Member) {
    setError("");
    try {
      await requestJson<void>(`/organizations/me/members/${member.id}`, { method: "DELETE" });
      await loadMembers();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo retirar al miembro.");
    }
  }

  return (
    <section className="auth-panel" aria-labelledby="auth-title">
      <div className="auth-panel__heading">
        <div>
          <p className="eyebrow">ACCESO Y PERMISOS</p>
          <h2 id="auth-title">Tu espacio de trabajo</h2>
        </div>
        {user && (
          <button className="button button--quiet" type="button" onClick={() => void logout()}>
            Cerrar sesión
          </button>
        )}
      </div>

      {error && <p className="form-error" role="alert">{error}</p>}
      {loading ? (
        <p role="status">Comprobando la sesión…</p>
      ) : user ? (
        <div className="auth-user">
          <p>Sesión iniciada como <strong>{user.full_name}</strong> ({user.email}).</p>
          <p>Organización: <strong>{user.organization_name}</strong> · Rol: <strong>{user.role}</strong></p>
          {user.role === "owner" && (
            <div className="member-tools">
              <h3>Miembros e invitaciones</h3>
              <button className="button" type="button" onClick={() => void createInvitation()}>
                Crear invitación de un solo uso
              </button>
              {inviteCode && (
                <p className="invite-code">
                  Comparte este código ahora; no volverá a mostrarse: <code>{inviteCode}</code>
                  <span>Vence: {new Date(inviteExpires).toLocaleString()}</span>
                </p>
              )}
              <ul className="member-list">
                {members.map((member) => (
                  <li key={member.id}>
                    <span>{member.full_name} · {member.email}</span>
                    <label>
                      Rol
                      <select
                        aria-label={`Rol de ${member.email}`}
                        value={memberRoles[member.id] ?? member.role}
                        onChange={(event) =>
                          setMemberRoles((current) => ({
                            ...current,
                            [member.id]: event.target.value as Member["role"],
                          }))
                        }
                      >
                        <option value="owner">Propietario</option>
                        <option value="member">Miembro</option>
                      </select>
                    </label>
                    <button
                      className="button button--quiet"
                      type="button"
                      onClick={() => void saveRole(member)}
                    >
                      Guardar rol
                    </button>
                    <button
                      className="button button--quiet"
                      type="button"
                      onClick={() => void removeMember(member)}
                    >
                      Retirar
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <>
          <div className="auth-tabs" role="group" aria-label="Acceso">
            <button
              type="button"
              aria-pressed={mode === "register"}
              onClick={() => { setMode("register"); setError(""); }}
            >
              Crear cuenta
            </button>
            <button
              type="button"
              aria-pressed={mode === "login"}
              onClick={() => { setMode("login"); setError(""); }}
            >
              Iniciar sesión
            </button>
          </div>
          <form className="auth-form" onSubmit={submitAuth}>
            {mode === "register" && (
              <>
                <label>
                  Nombre
                  <input name="full_name" autoComplete="name" required maxLength={120} />
                </label>
                <label>
                  Organización
                  <input name="organization_name" autoComplete="organization" maxLength={120} />
                  <span>Déjalo vacío si tienes un código de invitación.</span>
                </label>
                <label>
                  Código de invitación (opcional)
                  <input name="invitation_code" autoComplete="off" />
                </label>
              </>
            )}
            <label>
              Email
              <input name="email" type="email" autoComplete="email" required maxLength={254} />
            </label>
            <label>
              Contraseña
              <input
                name="password"
                type="password"
                autoComplete={mode === "register" ? "new-password" : "current-password"}
                required
                minLength={mode === "register" ? 12 : 1}
                maxLength={128}
              />
              {mode === "register" && <span>Usa al menos 12 caracteres.</span>}
            </label>
            <button className="button" type="submit">
              {mode === "register" ? "Crear cuenta" : "Iniciar sesión"}
            </button>
          </form>
          <p className="auth-notice">
            Prototipo educativo: el email no se verifica y no hay recuperación de contraseña. Usa
            una contraseña de prueba y no la reutilices.
          </p>
        </>
      )}
    </section>
  );
}
