# SaaS de documentación empresarial con IA

Aplicación para que equipos organicen documentación interna y, en hitos posteriores, consulten sus contenidos con búsqueda semántica y respuestas fundamentadas en fuentes.

## Estado

Hito inicial: API FastAPI mínima con endpoint de salud, PostgreSQL local con Docker Compose y documentación. Aún no implementa usuarios, organizaciones, subida de documentos ni funciones de IA.

## Stack inicial

- Frontend previsto: Next.js + TypeScript (el scaffold de interfaz se añadirá en su hito).
- Backend: Python 3.12+ y FastAPI.
- Base de datos: PostgreSQL 16; pgvector cuando se implemente la búsqueda semántica.
- Entorno local: Docker Compose.
- Calidad backend: pytest y Ruff.

## Arranque

1. Copia `.env.example` a `.env` y cambia la contraseña local.
2. Inicia PostgreSQL con `docker compose up -d db`.
3. En `backend/`, crea e instala el entorno Python:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Si PowerShell bloquea la activación, ejecuta `.venv\Scripts\python.exe -m uvicorn app.main:app --reload`.

4. API: `http://localhost:8000`; salud: `http://localhost:8000/health`; OpenAPI: `http://localhost:8000/docs`.
5. Comprueba el backend desde `backend/` con `pytest` y `ruff check .`.

## Estructura

```text
backend/       API, configuración Python y pruebas
frontend/      reservado para Next.js + TypeScript
docs/          arquitectura, hoja de ruta y decisiones
```

Consulta [arquitectura](docs/architecture.md), [hitos](docs/roadmap.md) y [ADR 0001](docs/adr/0001-base-tecnica.md). Las instrucciones para asistentes están en `AGENTS.md`.

## Git y seguridad

Este es un repositorio independiente. No hay remoto configurado; inspecciona `git status` antes de cada commit. No incluyas `.env`, secretos, documentos reales ni datos personales. Las comprobaciones de autorización se implementarán en el backend. Los documentos cargados y las salidas de modelos se tratarán como datos no confiables. No se conectará un proveedor LLM hasta documentar el tratamiento de datos.
