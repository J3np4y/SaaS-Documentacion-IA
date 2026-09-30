# Hoja de ruta

## Hito 1 — base ejecutable y documentada: completado

- Repositorio independiente y estructura con responsabilidades separadas.
- API FastAPI mínima con `/health` y prueba automatizada.
- PostgreSQL local definido con Docker Compose y credenciales configurables.
- README, arquitectura, decisión técnica y guía para asistentes.
- Arranque local de la API y respuesta correcta del endpoint confirmados.

## Hito 2 — interfaz web y conexión inicial con la API: completado

- Next.js con TypeScript y App Router.
- Página adaptable y accesible con indicador del estado de API consultado server-side.
- Timeout, validación de URL, errores genéricos y pruebas automatizadas.
- Lockfile, instalación reproducible, README y CI de backend y frontend.
- Pruebas, lint, tipos y build locales aprobados; el usuario confirmó GitHub Actions en verde.

## Hito 3 — persistencia inicial con PostgreSQL: completado localmente; CI pendiente

- Conectar FastAPI a PostgreSQL con SQLAlchemy 2 y configuración por entorno.
- Añadir migraciones con Alembic.
- Crear las entidades iniciales de organización y metadatos de documento.
- Separar disponibilidad de la API (`/health`) y disponibilidad de base de datos (`/ready`).
- Añadir pruebas de integración contra PostgreSQL y servicio PostgreSQL en CI.

Alcance y criterios: [hito-03.md](hito-03.md). La selección técnica aceptada se registra en [ADR 0002](adr/0002-persistence.md).

## Hitos siguientes

4. Autenticación, usuarios, pertenencia a organizaciones, roles y permisos.
5. Subida, validación, almacenamiento y gestión de documentos.
6. Extracción de contenido, ingesta y búsqueda textual.
7. RAG con pgvector, citas y evaluación.
8. Observabilidad, control de coste y despliegue.
