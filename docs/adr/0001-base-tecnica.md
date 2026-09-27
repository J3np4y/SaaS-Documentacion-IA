# ADR 0001: base técnica inicial

- Estado: aceptada para el primer hito
- Fecha: 2026-09-26

## Contexto

El proyecto debe demostrar ingeniería de producto y permitir añadir IA gradualmente, con un arranque local reproducible.

## Decisión

- Frontend previsto: Next.js + TypeScript.
- API: FastAPI y Python 3.12+.
- Persistencia: PostgreSQL 16; pgvector al implementar recuperación semántica.
- Entorno local: Docker Compose.
- Pruebas: pytest; lint/formato Python: Ruff.
- Sin proveedor LLM, autenticación o cloud en el scaffold.

## Consecuencias

Se valida pronto la API sin fijar proveedor de IA. El scaffold del frontend se agrega en el paso de interfaz. Se fijarán versiones mediante lockfiles al instalar dependencias por plataforma.
