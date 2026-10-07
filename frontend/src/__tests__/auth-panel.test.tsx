import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthPanel } from "@/components/auth-panel";

const owner = {
  id: "owner-id",
  email: "owner@example.com",
  full_name: "Propietaria",
  organization_id: "organization-id",
  organization_name: "Equipo",
  role: "owner" as const,
};

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("AuthPanel", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  it("registers an organization owner and loads the authorized member list", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ detail: "Autenticación requerida" }, 401))
      .mockResolvedValueOnce(jsonResponse(owner, 201))
      .mockResolvedValueOnce(jsonResponse([]));

    render(<AuthPanel />);
    fireEvent.change(await screen.findByLabelText("Nombre"), {
      target: { value: "Propietaria" },
    });
    fireEvent.change(screen.getByLabelText(/Organización/), {
      target: { value: "Equipo" },
    });
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "owner@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/Contraseña/), {
      target: { value: "correct-horse-battery-staple" },
    });
    fireEvent.click(screen.getAllByRole("button", { name: "Crear cuenta" }).at(-1)!);

    expect(await screen.findByText(/Sesión iniciada como/)).toBeTruthy();
    expect(screen.getByText("Equipo")).toBeTruthy();
    expect(screen.getByText("owner")).toBeTruthy();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(JSON.parse(String(fetchMock.mock.calls[1][1]?.body))).toMatchObject({
      email: "owner@example.com",
      full_name: "Propietaria",
      organization_name: "Equipo",
    });
  });

  it("shows the one-time invitation code to the owner", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(jsonResponse(owner))
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(
        jsonResponse({ code: "manual-one-time-code", expires_at: "2026-10-08T10:00:00Z" }, 201),
      );

    render(<AuthPanel />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    fireEvent.click(
      await screen.findByRole("button", { name: "Crear invitación de un solo uso" }),
    );

    expect(await screen.findByText(/manual-one-time-code/)).toBeTruthy();
    expect(screen.getByText(/no volverá a mostrarse/)).toBeTruthy();
  });

  it("logs in and clears the authenticated state on logout", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ detail: "Autenticación requerida" }, 401))
      .mockResolvedValueOnce(jsonResponse(owner))
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));

    render(<AuthPanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Iniciar sesión" }));
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "owner@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/Contraseña/), {
      target: { value: "correct-horse-battery-staple" },
    });
    fireEvent.click(screen.getAllByRole("button", { name: "Iniciar sesión" }).at(-1)!);

    expect(await screen.findByText(/Sesión iniciada como/)).toBeTruthy();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    fireEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));
    expect(await screen.findByRole("button", { name: "Crear cuenta" })).toBeTruthy();
    expect(fetchMock.mock.calls[3][0]).toBe("/api/backend/auth/logout");
  });

  it("lets an owner update and remove a member", async () => {
    const member = {
      id: "member-id",
      email: "member@example.com",
      full_name: "Miembro",
      role: "member" as const,
    };
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(jsonResponse(owner))
      .mockResolvedValueOnce(jsonResponse([member]))
      .mockResolvedValueOnce(jsonResponse({ ...member, role: "owner" }))
      .mockResolvedValueOnce(jsonResponse([{ ...member, role: "owner" }]))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(jsonResponse([]));

    render(<AuthPanel />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    fireEvent.change(screen.getByLabelText("Rol de member@example.com"), {
      target: { value: "owner" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Guardar rol" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));
    expect(fetchMock.mock.calls[2][0]).toBe("/api/backend/organizations/me/members/member-id");
    expect(JSON.parse(String(fetchMock.mock.calls[2][1]?.body))).toEqual({ role: "owner" });

    fireEvent.click(screen.getByRole("button", { name: "Retirar" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(6));
    expect(fetchMock.mock.calls[4][0]).toBe("/api/backend/organizations/me/members/member-id");
    expect(fetchMock.mock.calls[4][1]?.method).toBe("DELETE");
  });
});
