# Hito 3 — persistencia inicial con PostgreSQL

## Estado: completado y confirmado por CI

Las comprobaciones locales de backend, PostgreSQL y frontend pasaron según los resultados registrados en [testing.md](testing.md). GitHub Actions confirmó ambos jobs sobre `main` en la [ejecución 36760916434](https://github.com/J3np4y/SaaS-Documentacion-IA/actions/runs/36760916434), commit `c5ebb8b7e4ab57b5ecf4ba81eafef2e048ff9c7c`.

## Objetivo

Conectar FastAPI con PostgreSQL de forma reproducible y segura, y crear un primer modelo persistente que prepare el terreno para organizaciones y documentos.

## Incluye

1. Añadir SQLAlchemy 2 y el driver PostgreSQL `psycopg` al backend.
2. Configurar la URL de conexión mediante `DATABASE_URL`, sin secretos en el código ni en Git.
3. Crear una sesión de base de datos por petición y cerrar conexiones correctamente.
4. Configurar Alembic y añadir la migración inicial.
5. Crear las tablas iniciales `organizations` y `documents` con UUID, fechas, restricciones y una clave foránea de documento a organización.
6. Mantener `/health` como liveness y añadir `/ready` para comprobar acceso real a PostgreSQL.
7. Añadir pruebas unitarias y de integración contra PostgreSQL, incluidos estado no disponible, migración y restricciones del esquema.
8. Añadir PostgreSQL como servicio de la CI para ejecutar las pruebas de integración.
9. Documentar arranque, migraciones, pruebas y solución de errores comunes.

## Fuera de alcance

- CRUD público de organizaciones o documentos.
- Registro, autenticación, usuarios, roles o autorización multi-tenant.
- Subida de archivos y almacenamiento de binarios.
- Extracción de contenido, embeddings, pgvector, RAG o agentes.
- Despliegue público o proveedor LLM.

## Criterios de aceptación

- El backend obtiene `DATABASE_URL` del entorno y no registra su valor.
- Con PostgreSQL activo, `/ready` indica disponible; sin base de datos devuelve un error controlado que no revela credenciales ni detalles internos.
- Alembic aplica la migración inicial sobre una base vacía y deja el esquema al día.
- Se pueden crear organizaciones y asociar metadatos de documento; la clave foránea y restricciones se prueban.
- Una base de datos de prueba aislada se usa localmente y en CI.
- Pasan las pruebas backend, Ruff, las pruebas de integración, lint, tipos, pruebas frontend y build.
- CI ejecuta los checks de backend y frontend con PostgreSQL temporal; ambos jobs pasaron en la ejecución indicada arriba.

## Seguridad y buenas prácticas

- Mantener credenciales fuera del repositorio; usar `.env` local ignorado por Git y secretos administrados en CI solo si fueran necesarios.
- Validar tipos, longitudes y restricciones también en la base de datos.
- Usar SQLAlchemy con parámetros enlazados; no interpolar datos en SQL.
- No guardar el contenido binario de los documentos en las tablas.
- Mantener los errores externos genéricos y no registrar cadenas de conexión.
- Documentar decisiones de esquema mediante migraciones pequeñas y revisables.

## Pruebas previstas

La estrategia está en [testing.md](testing.md). Las pruebas de integración solo deben apuntar a la base desechable `docs_assistant_test` (servicio `db-test`, puerto local 5433), ya que cada prueba elimina y recrea su esquema.
