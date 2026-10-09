# SaaS de documentación empresarial con IA

Aplicación web para que equipos colaboren alrededor de su documentación y, en una siguiente etapa, puedan encontrar información y obtener respuestas fundamentadas en sus fuentes.

Este repositorio es también un **proyecto de aprendizaje guiado**: cada parte se construye entendiendo primero el problema, los conceptos y las decisiones de diseño. La meta no es producir código a ciegas, sino aprender cómo las piezas de una aplicación real se relacionan y cómo tomar decisiones técnicas con criterio.

> **Estado actual:** la aplicación incluye cuentas, organizaciones, invitaciones, permisos básicos, gestión de documentos, extracción y búsqueda textual en español, además de preguntas con recuperación y citas mediante RAG. El Hito 7 está verificado localmente; su CI está pendiente. Es un prototipo educativo, no un servicio listo para producción.

## Cómo funciona

1. Una persona crea una cuenta y una organización, o se incorpora a una organización mediante una invitación.
2. Inicia sesión y usa la aplicación dentro de su organización. Los permisos determinan qué acciones puede realizar cada integrante.
3. El backend valida la identidad, los permisos y la organización de cada solicitud; el frontend presenta el flujo y sus estados.
4. La carga y gestión de documentos usa almacenamiento local privado. El backend extrae texto durante la carga, permite buscarlo en la organización y puede responder preguntas a partir de fragmentos citados.

## Aprendizaje guiado

El recorrido explica los conceptos antes de implementarlos: identidad y autenticación, autorización, organizaciones y pertenencia, persistencia y migraciones, y separación entre interfaz y API. Cada funcionalidad se acompaña de decisiones razonadas y comprobaciones para entender tanto el camino correcto como los límites y fallos previsibles.

Si estás empezando, sigue la [guía de aprendizaje](docs/guia-aprendizaje.md): explica por dónde empezar, cómo avanzar una fase cada vez y cómo leer los hitos, las decisiones y las pruebas sin tener que conocer todo el stack de antemano.

## Stack

- **Frontend:** Next.js, React, TypeScript y CSS.
- **Backend:** Python 3.12+ y FastAPI.
- **Datos:** PostgreSQL 16, SQLAlchemy y Alembic.
- **Acceso:** contraseñas protegidas con Argon2id, sesiones revocables y permisos por organización.
- **Desarrollo local:** Docker Compose.

## Estructura

```text
backend/    API, acceso a datos y reglas de la aplicación
frontend/   interfaz web
docs/       explicación del diseño y material de aprendizaje
```

## Ejecutar localmente

Necesitas Docker Compose, Python 3.12 o posterior y Node.js con npm. En una copia nueva, crea `.env` a partir de `.env.example` y cambia la contraseña local de PostgreSQL; luego inicia la base de datos:

```powershell
Copy-Item .env.example .env
docker compose up -d db
```

En una terminal, instala e inicia la API:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

En otra terminal, inicia la interfaz:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm.cmd ci
npm.cmd run dev
```

Abre `http://localhost:3000`. La API está disponible en `http://localhost:8000` y su interfaz interactiva en `http://localhost:8000/docs`.

El Hito 5 admite PDF, DOCX y TXT de hasta 10 MiB y guarda los archivos en `.data/documents/` (ignorado por Git). Puedes cambiar esa ruta con `DOCUMENT_STORAGE_DIR`. No subas archivos sensibles: esta versión no incluye análisis antimalware, cuotas ni controles de producción.

El Hito 7 utiliza OpenAI para indexar documentos y responder preguntas. Si quieres probarlo, configura `OPENAI_API_KEY` en `.env`; las solicitudes enviarán a OpenAI el contenido que se indexe, las preguntas y los fragmentos recuperados, y pueden generar costes. Sin clave, las funciones anteriores siguen disponibles, pero RAG no puede indexar ni responder.

## Uso responsable

La autenticación actual es didáctica: no incluye verificación de correo, recuperación de cuenta ni protección distribuida frente a intentos abusivos. No expongas esta versión a Internet ni la uses para datos reales. Antes de una puesta en producción habría que completar esos controles y revisar la configuración del despliegue.
