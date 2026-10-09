# Hoja de ruta

Esta página es el índice del progreso: resume qué está terminado y qué viene después. Para aprender los conceptos paso a paso, empieza por la [guía de aprendizaje](guia-aprendizaje.md) y abre el documento de cada hito. Los resultados detallados de comprobaciones se mantienen en [testing.md](testing.md).

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

## Hito 3 — persistencia inicial con PostgreSQL: completado; CI confirmada

- Conectar FastAPI a PostgreSQL con SQLAlchemy 2 y configuración por entorno.
- Añadir migraciones con Alembic.
- Crear las entidades iniciales de organización y metadatos de documento.
- Separar disponibilidad de la API (`/health`) y disponibilidad de base de datos (`/ready`).
- Añadir pruebas de integración contra PostgreSQL y servicio PostgreSQL en CI.
- CI confirmada sobre `main`; enlace y resultados detallados en [testing.md](testing.md).

Alcance y criterios: [hito-03.md](hito-03.md). La selección técnica aceptada se registra en [ADR 0002](adr/0002-persistence.md).

## Hito 4 — autenticación, usuarios y permisos: completado; verificación local aprobada

- Email y contraseña, sesiones de servidor revocables y cookie segura.
- Registro que crea organización y propietario; una organización por usuario.
- Roles `owner`/`member`, invitaciones manuales de un solo uso y UI mínima.
- Autorización en el backend probada por organización y rol.
- Sin correo, verificación de email ni recuperación de contraseña en esta fase.
- La verificación local y sus resultados están detallados en [testing.md](testing.md).

El recorrido de aprendizaje está en [hito-04.md](hito-04.md); la decisión técnica, en [ADR 0003](adr/0003-authentication-and-access.md). El login no se considera listo para producción mientras falten los controles de abuso y recuperación indicados en el hito.

## Hito 5 — carga y gestión de documentos: completado; CI aprobada

- Decisiones acordadas: PDF/DOCX/TXT, 10 MiB por archivo, almacenamiento local privado, permisos iguales para ambos roles, borrado físico y sin antimalware/cuotas totales por organización.
- Carga, listado, descarga y borrado con permisos por organización.
- Validación de tipos y límite de tamaño; bytes en almacenamiento local privado.
- Extracción, indexación, búsqueda y respuestas de IA siguen fuera del alcance.

El recorrido de aprendizaje y los criterios están en [hito-05.md](hito-05.md). Las decisiones y sus consecuencias están en el [ADR 0004](adr/0004-document-storage.md). Los resultados locales y de CI están en [testing.md](testing.md).

## Hitos posteriores

## Hito 6 — extracción de contenido, ingesta y búsqueda textual: completado; CI aprobada

- Extraer texto de PDF, DOCX y TXT durante la carga; preservar el original si falla.
- Guardar el texto y habilitar búsqueda PostgreSQL en español, aislada por organización.
- Mantener fuera de alcance OCR, embeddings, RAG y respuestas generadas por IA.

El recorrido, las decisiones y la comprobación local están en [hito-06.md](hito-06.md) y [testing.md](testing.md).

7. RAG con pgvector, citas y evaluación.
8. Observabilidad, control de coste y despliegue.
