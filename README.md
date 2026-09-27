# SaaS de documentación empresarial con IA

Aplicación para que equipos organicen documentación interna y, en hitos posteriores, consulten sus contenidos con búsqueda semántica y respuestas fundamentadas en fuentes.

## Estado del proyecto

- **Hito 1 completado:** repositorio, API FastAPI con `/health`, PostgreSQL local con Docker Compose y documentación base.
- **Hito 2 implementado:** interfaz Next.js y TypeScript, pantalla inicial con estado de la API, pruebas y CI configurada. Las comprobaciones locales pasan; la ejecución de GitHub Actions todavía debe confirmarse.

El alcance está en [docs/hito-02.md](docs/hito-02.md), la [hoja de ruta](docs/roadmap.md) y el [registro de pruebas](docs/testing.md).

## Stack

- Frontend: Next.js App Router, TypeScript y React.
- Backend: Python 3.12+ y FastAPI.
- Base de datos: PostgreSQL 16 mediante Docker Compose; pgvector se añadirá en el hito RAG.
- Calidad: pytest y Ruff para backend; Vitest, ESLint, TypeScript y build para frontend.

## Arranque local

### 1. PostgreSQL

Si aún no tienes `.env`, copia `.env.example` y configura una contraseña local. Desde la raíz del proyecto:

```powershell
docker compose up -d db
docker compose ps
```

### 2. API

En una terminal, desde `backend/`, crea el entorno e instala dependencias la primera vez:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload
```

La API queda en `http://localhost:8000`; salud: `http://localhost:8000/health`; OpenAPI: `http://localhost:8000/docs`.

### 3. Frontend

En otra terminal, desde `frontend/`, copia `.env.example` a `.env.local` la primera vez e inicia la aplicación:

```powershell
Copy-Item .env.example .env.local
npm.cmd ci
npm.cmd run dev
```

Abre `http://localhost:3000`. El frontend consulta `/health` desde el servidor Next.js. Consulta [frontend/README.md](frontend/README.md) para requisitos de Node, configuración y solución de problemas en PowerShell.

## Pruebas y calidad

Desde `frontend/`:

```powershell
npm.cmd test
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
```

Desde `backend/`, ejecuta `pytest` y `ruff check .`. La [CI](.github/workflows/backend.yml) ejecuta los checks de backend y frontend en pushes y pull requests.

## Estructura

```text
backend/       API FastAPI, configuración Python y pruebas
frontend/      aplicación web Next.js y pruebas
.github/       automatización CI
docs/          arquitectura, hitos, decisiones y registro de pruebas
```

Las pautas de desarrollo asistido están en [AGENTS.md](AGENTS.md).

## Git y seguridad

Este proyecto es un repositorio independiente. Revisa `git status` antes de cada commit. No incluyas `.env`, secretos, documentos reales ni datos personales. La autorización se validará en el backend; los documentos cargados y las salidas de modelos se tratarán como datos no confiables. No se conectará un proveedor LLM hasta documentar el tratamiento de datos.
