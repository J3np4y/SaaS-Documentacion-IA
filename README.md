# SaaS de documentación empresarial con IA

Aplicación para que equipos organicen documentación interna y, en hitos posteriores, consulten sus contenidos con búsqueda semántica y respuestas fundamentadas en fuentes.

## Estado del proyecto

- **Hito 1 completado:** repositorio, API FastAPI con `/health`, PostgreSQL local con Docker Compose y documentación base.
- **Hito 2 completado:** interfaz Next.js/TypeScript, pantalla inicial con estado de API, pruebas, comprobaciones locales aprobadas y GitHub Actions en verde (confirmado por el usuario).
- **Hito 3 completado localmente:** conexión PostgreSQL, migraciones y modelos iniciales verificados. La CI de estos cambios queda pendiente. Detalles en [docs/hito-03.md](docs/hito-03.md).

Consulta la [hoja de ruta](docs/roadmap.md), [arquitectura](docs/architecture.md) y el [registro de pruebas](docs/testing.md).

## Stack

- Frontend: Next.js App Router, TypeScript y React.
- Backend: Python 3.12+ y FastAPI.
- Persistencia: PostgreSQL 16 mediante Docker Compose, SQLAlchemy 2 y Alembic.
- Calidad: pytest y Ruff para backend; Vitest, ESLint, TypeScript y build para frontend.

## Probar lo desarrollado

Abre tres terminales PowerShell desde la raíz del proyecto.

### 1. Iniciar PostgreSQL

Si todavía no existe `.env`, copia `.env.example` y configura una contraseña local. Desde la raíz:

```powershell
Copy-Item .env.example .env  # solo la primera vez; configura la contraseña local
docker compose up -d db
docker compose ps
```

Espera a que `db` aparezca como `healthy`.

### 2. Iniciar la API

En la primera terminal, entra en `backend/`. La primera vez crea e instala el entorno:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Comprueba `http://localhost:8000/health`; debe devolver `{"status":"ok"}`. La documentación interactiva está en `http://localhost:8000/docs`.

### 3. Iniciar la web

En la segunda terminal, desde la raíz del proyecto:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm.cmd ci
npm.cmd run dev
```

`Copy-Item` se necesita solo la primera vez. Abre `http://localhost:3000`; el estado de la API debe mostrarse disponible. Para comprobar el estado de error, detén la API con `Ctrl+C` y recarga la página; debe seguir cargando y mostrar que la API no está disponible. Después vuelve a iniciar la API.

Para parar PostgreSQL al terminar, desde la raíz ejecuta `docker compose down`. Los comandos de Node y npm y otros detalles están en [frontend/README.md](frontend/README.md).

## Ejecutar las comprobaciones

Desde `frontend/`:

```powershell
npm.cmd test
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
```

Desde `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

La [CI](.github/workflows/backend.yml) ejecuta los checks del backend y frontend en pushes y pull requests.

## Hito 3: migraciones y persistencia

Una vez creado `.env`, el backend deriva `DATABASE_URL` y `TEST_DATABASE_URL` de `POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD`. Las variables explícitas del entorno pueden sobrescribir esas URL. Inicia ambas bases locales (desarrollo y pruebas):

```powershell
docker compose up -d db db-test
docker compose ps
```

Desde `backend/`, aplica las migraciones a la base de desarrollo y arranca la API:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

`GET /health` comprueba que la API está viva. `GET /ready` ejecuta una consulta sencilla a PostgreSQL y devuelve 503 si no está disponible. La documentación de la API está en `http://localhost:8000/docs`.

Para probar migraciones e integridad referencial, usa exclusivamente `TEST_DATABASE_URL` (por defecto, servicio `db-test` en el puerto 5433). **Las pruebas de integración borran y recrean el esquema `public` de esa base. Nunca apuntes `TEST_DATABASE_URL` a datos que quieras conservar.** Desde `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Las pruebas unitarias de endpoints no requieren PostgreSQL; las pruebas de integración se saltan si `TEST_DATABASE_URL` no está configurada. CI las ejecuta con un PostgreSQL temporal.

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
