# ADR 0002: persistencia PostgreSQL para el Hito 3

- Estado: aceptada
- Fecha: 2026-09-27

## Contexto

El Hito 2 deja una API funcional y PostgreSQL en Docker Compose, pero todavía no hay conexión entre ellos ni un esquema versionado. Antes de autenticación, organizaciones y documentos deben persistirse de forma reproducible.

## Propuesta

- SQLAlchemy 2 con sesiones síncronas por petición para minimizar conceptos nuevos en esta fase.
- Driver `psycopg` para PostgreSQL.
- Alembic para migraciones versionadas y revisables.
- `DATABASE_URL` como configuración del backend, cargada del entorno.
- `/health` para liveness de la API y `/ready` para comprobar la conexión a la base de datos.
- Esquema inicial con organización y metadatos de documento; no almacenar binarios.
- Pruebas de integración contra PostgreSQL, con base de datos aislada en local y un servicio efímero en CI.

## Alternativas consideradas

- SQLite para desarrollo: descartada para este hito porque difiere de PostgreSQL en tipos, restricciones y comportamiento de migraciones.
- SQLAlchemy asíncrono: se puede evaluar después; para el primer flujo persistente, la API y las operaciones simples se benefician de una secuencia síncrona más fácil de depurar.
- SQLModel: se prefiere separar modelos de persistencia y esquemas HTTP mediante SQLAlchemy y Pydantic para aprender explícitamente cada límite.

## Consecuencias

La conexión y las migraciones se prueban contra el motor real que usa el proyecto. Cada prueba de integración requiere una base disponible. Las sesiones deben cerrarse de forma predecible y las credenciales no pueden aparecer en logs.
