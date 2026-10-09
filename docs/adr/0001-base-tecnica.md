# ADR 0001: base técnica inicial

- Estado: aceptada para el primer hito
- Fecha: 2026-09-26

## Resumen sencillo

Para comenzar el proyecto se eligieron herramientas distintas para la interfaz web, la API, los datos y el entorno local. El objetivo es tener una base reproducible y poder añadir capacidades poco a poco, sin depender de servicios externos desde el principio. La selección fija un punto de partida; no significa que haya que aprender todas las herramientas antes de hacer el primer cambio.

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
