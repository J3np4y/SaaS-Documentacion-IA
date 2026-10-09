# Hoja de ruta

Esta página resume el recorrido y el estado de cada hito. Para aprender paso a paso, empieza por la [guía de aprendizaje](guia-aprendizaje.md); cada documento de hito explica los conceptos, las decisiones, los límites y cómo comprobarlos. Los resultados observados se registran en [testing.md](testing.md).

## Estado general

Los ocho hitos definidos hasta ahora están implementados. El Hito 8 cuenta con verificación local y CI aprobadas. El siguiente hito aún no tiene alcance acordado: antes de abrir trabajo nuevo, se revisarán las limitaciones pendientes y se decidirá su objetivo por separado. El prototipo no es un servicio listo para producción.

## Hito 1 — base ejecutable y documentada: completado

- Repositorio y estructura inicial con separación de API, interfaz y documentación.
- API FastAPI con comprobación de vida `/health`.
- PostgreSQL local definido con Docker Compose y configuración por entorno.
- README, arquitectura, decisiones iniciales y guía para asistentes.

## Hito 2 — interfaz web y conexión inicial con la API: completado

- Next.js con TypeScript y App Router; página accesible y adaptable.
- Estado de salud de la API consultado server-side con timeout y mensajes genéricos.
- Lockfile, instalación reproducible y CI para backend y frontend.

## Hito 3 — persistencia inicial con PostgreSQL: completado; CI confirmada

- SQLAlchemy y Alembic para datos y migraciones versionadas.
- Entidades iniciales de organización y documentos.
- `/health` separa la vida de la API de `/ready`, que comprueba PostgreSQL.
- Referencias: [ADR 0002](adr/0002-persistence.md), [Hito 3](hito-03.md).

## Hito 4 — autenticación, usuarios y permisos: completado; verificación local aprobada

- Registro, sesiones revocables, cookies y roles `owner`/`member`.
- Invitaciones manuales de un uso y autorización por organización en el servidor.
- Verificación y limitaciones de producción: [Hito 4](hito-04.md), [ADR 0003](adr/0003-authentication-and-access.md).

## Hito 5 — carga y gestión de documentos: completado; CI aprobada

- Carga, listado, descarga y borrado autorizado para PDF, DOCX y TXT de hasta 10 MiB.
- Bytes en almacenamiento local privado y metadatos en PostgreSQL.
- Política y límites: [Hito 5](hito-05.md), [ADR 0004](adr/0004-document-storage.md).

## Hito 6 — extracción, ingesta y búsqueda textual: completado; CI aprobada

- Extraer texto de PDF, DOCX y TXT, conservar el original y permitir reintentos.
- Búsqueda de texto completo en español, filtrada por la organización autenticada.
- OCR y respuestas generadas por IA quedaron fuera de este hito.
- Recorrido: [Hito 6](hito-06.md).

## Hito 7 — RAG con pgvector, citas y evaluación: completado; CI aprobada

- Indexación de fragmentos y embeddings; recuperación limitada a la organización actual.
- Respuestas fundamentadas con citas y abstención cuando falta evidencia.
- Evaluación determinista reproducible con datos sintéticos; no mide la calidad real de OpenAI.
- Recorrido y decisiones: [Hito 7](hito-07.md), [ADR 0005](adr/0005-rag-models-and-retrieval.md).

## Hito 8 — cuotas, observabilidad privada y contenedores: completado; CI aprobada

- Cuotas RAG por organización de 20 operaciones diarias y 200 mensuales por defecto, configurables por entorno.
- Métricas Prometheus de baja cardinalidad y logs JSON sin contenido ni identidad.
- Imágenes de frontend y API; Compose local con datos persistentes y exposición solo en loopback del frontend.
- Ejecutor PowerShell en la raíz: [`iniciar.ps1`](../iniciar.ps1).
- Instrucciones y limitaciones: [Hito 8](hito-08.md), [ADR 0006](adr/0006-observability-cost-control-and-containers.md).

## Próxima decisión

No se presupone un Hito 9. Antes de ampliarlo, revisar las limitaciones documentadas de autenticación, privacidad, backups y operación; acordar alcance y criterios de aceptación con quien mantiene el proyecto.
