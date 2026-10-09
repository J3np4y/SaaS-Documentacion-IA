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
      .mockResolvedValueOnce(jsonResponse([]))
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
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));
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
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(
        jsonResponse({ code: "manual-one-time-code", expires_at: "2026-10-08T10:00:00Z" }, 201),
      );

    render(<AuthPanel />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
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
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));
    fireEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));
    expect(await screen.findByRole("button", { name: "Crear cuenta" })).toBeTruthy();
    expect(fetchMock.mock.calls[4][0]).toBe("/api/backend/auth/logout");
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
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse({ ...member, role: "owner" }))
      .mockResolvedValueOnce(jsonResponse([{ ...member, role: "owner" }]))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(jsonResponse([]));

    render(<AuthPanel />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    fireEvent.change(screen.getByLabelText("Rol de member@example.com"), {
      target: { value: "owner" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Guardar rol" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(5));
    expect(fetchMock.mock.calls[3][0]).toBe("/api/backend/organizations/me/members/member-id");
    expect(JSON.parse(String(fetchMock.mock.calls[3][1]?.body))).toEqual({ role: "owner" });

    fireEvent.click(screen.getByRole("button", { name: "Retirar" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(7));
    expect(fetchMock.mock.calls[5][0]).toBe("/api/backend/organizations/me/members/member-id");
    expect(fetchMock.mock.calls[5][1]?.method).toBe("DELETE");
  });

  it("uploads and lists a document without overriding the multipart content type", async () => {
    const document = {
      id: "document-id",
      filename: "manual.txt",
      content_type: "text/plain",
      size_bytes: 12,
      created_at: "2026-10-09T10:00:00Z",
    };
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(jsonResponse(owner))
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse(document, 201))
      .mockResolvedValueOnce(jsonResponse([document]));

    render(<AuthPanel />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    fireEvent.change(screen.getByLabelText("Elige un documento"), {
      target: { files: [new File(["hello world!"], "manual.txt", { type: "text/plain" })] },
    });
    fireEvent.submit(screen.getByRole("button", { name: "Cargar documento" }).closest("form")!);

    expect(await screen.findByText("manual.txt")).toBeTruthy();
    expect(screen.getByText(/Cargado/)).toBeTruthy();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(5));
    expect(fetchMock.mock.calls[3][0]).toBe("/api/backend/organizations/me/documents");
    expect(fetchMock.mock.calls[3][1]?.body).toBeInstanceOf(FormData);
    expect(new Headers(fetchMock.mock.calls[3][1]?.headers).has("content-type")).toBe(false);
  });

  it("asks before permanently deleting a document", async () => {
    const document = {
      id: "document-id",
      filename: "manual.txt",
      content_type: "text/plain",
      size_bytes: 12,
      created_at: "2026-10-09T10:00:00Z",
    };
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(jsonResponse(owner))
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse([document]))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(jsonResponse([]));

    render(<AuthPanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Borrar" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(5));
    expect(confirm).toHaveBeenCalledWith('¿Borrar "manual.txt" definitivamente?');
    expect(fetchMock.mock.calls[3][0]).toBe(
      "/api/backend/organizations/me/documents/document-id",
    );
    expect(await screen.findByText("Todavía no hay documentos cargados.")).toBeTruthy();
    confirm.mockRestore();
  });

  it("shows the backend validation error when a document upload fails", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(jsonResponse(owner))
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse({ detail: "El contenido no parece ser un PDF." }, 400));

    render(<AuthPanel />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    fireEvent.change(screen.getByLabelText("Elige un documento"), {
      target: { files: [new File(["not a pdf"], "manual.pdf", { type: "application/pdf" })] },
    });
    fireEvent.submit(screen.getByRole("button", { name: "Cargar documento" }).closest("form")!);

    expect((await screen.findByRole("alert")).textContent).toContain(
      "El contenido no parece ser un PDF.",
    );
    expect(fetchMock).toHaveBeenCalledTimes(4);
  });
});
