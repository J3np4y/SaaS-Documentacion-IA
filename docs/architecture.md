# Arquitectura

Esta página muestra las piezas y cómo se comunican; no es necesario aprender todos los detalles de una vez. Para estudiar el proyecto por etapas, consulta la [guía de aprendizaje](guia-aprendizaje.md). Las secciones indican si describen capacidades actuales o trabajo planificado.

## Estado actual — persistencia, acceso y gestión de documentos

FastAPI expone `/health` y `/ready`; SQLAlchemy obtiene una sesión por petición y Alembic versiona el esquema. Next.js presenta el flujo y usa un proxy same-origin para las rutas de autenticación y documentos. PostgreSQL conserva organizaciones, usuarios, membresías, sesiones, invitaciones, metadatos y texto extraído con un índice de búsqueda en español; los bytes se guardan en un directorio privado configurado por `DOCUMENT_STORAGE_DIR`.

```text
Navegador -> Next.js (página renderizada en servidor) -> FastAPI /health
FastAPI -> SQLAlchemy -> PostgreSQL
Alembic -> migraciones versionadas
```

El chequeo de la API es dinámico. Tiene timeout, no usa caché ni sigue redirecciones; los errores de red se convierten en un estado genérico y no se devuelven detalles de infraestructura al navegador.

## Persistencia inicial (Hito 3)

```text
Navegador -> Next.js -> FastAPI -> servicios de aplicación
                                  -> SQLAlchemy 2 / sesión por petición
                                  -> PostgreSQL 16
Alembic -> migraciones versionadas de esquema
```

FastAPI conserva `/health` como comprobación de vida independiente de la base de datos y expone `/ready` como comprobación de preparación que verifica una conexión real a PostgreSQL. Si la base de datos no está disponible, `/ready` responderá con estado no disponible sin revelar detalles de conexión.

El esquema inicial añadió `Organization` y metadatos `Document` enlazados mediante clave foránea. Los binarios no se guardan en PostgreSQL. El Hito 5 añadió la gestión de documentos con bytes en un directorio local privado.

## Acceso y permisos (Hito 4)

```text
Navegador -> Next.js (formularios y rutas proxy same-origin)
                -> FastAPI -> autenticación por cookie HttpOnly
                           -> sesión revocable (hash del identificador) en PostgreSQL
                           -> User -> Membership (una organización y rol) -> Organization
                           -> invitación (hash de secreto, un uso y expiración)
```

Registro con email/contraseña crea una organización y a su primer usuario como `owner`; con una invitación válida crea una cuenta `member` en la organización destino. Cada cuenta pertenece a una organización en esta fase. La API deriva el usuario, el rol y el tenant de la sesión; nunca concede permisos a partir de un rol u organización enviados por el cliente. El propietario administra invitaciones y membresías; el backend conserva siempre al menos un propietario.

Las rutas proxy de Next.js reenvían cookies al backend sin exponerlas a JavaScript. La sesión vive en PostgreSQL para revocarla; el navegador solo conserva un identificador aleatorio `HttpOnly`, `SameSite=Lax`, con vencimiento y `Secure` en despliegues HTTPS. El backend valida el encabezado `Origin` en operaciones que cambian estado. Las invitaciones se comparten manualmente y no verifican la dirección de correo.

## Gestión de documentos (Hito 5 completado)

```text
Navegador -> Next.js -> FastAPI
                         -> identidad y organización de la sesión
                         -> validar tamaño, tipo y nombre del archivo
                         -> PostgreSQL: metadatos y estado
                         -> almacenamiento privado: bytes originales
```

El backend asigna la organización desde la sesión, no desde campos confiados al navegador; las claves de almacenamiento las genera el servidor y no se derivan de rutas/nombres proporcionados por el usuario. Los formatos, límites, permisos y política de retención del prototipo están acordados en [hito-05.md](hito-05.md) y [ADR 0004](adr/0004-document-storage.md). No se exponen enlaces públicos por defecto.

## Extracción e ingesta (Hito 6 implementado)

El backend extrae texto de PDF con `pypdf`, de DOCX con las bibliotecas estándar y de TXT como UTF-8. El texto se guarda en PostgreSQL junto a su estado; una columna generada y un índice GIN permiten búsqueda de texto completo con la configuración española. Las consultas se limitan a la organización de la sesión. El procesamiento es síncrono y acotado; si falla, se conserva el original y se puede reintentar. OCR y embeddings quedan fuera del Hito 6. El recorrido y las limitaciones están en [hito-06.md](hito-06.md).

## RAG, citas y evaluación (Hito 7 completado; CI aprobada)

La aplicación usa la API de OpenAI para embeddings y generación, y PostgreSQL con pgvector para recuperar fragmentos de la organización autenticada. El texto del documento, la pregunta y el contexto se envían a OpenAI cuando el proveedor está configurado. Los documentos antiguos requieren indexación explícita; los nuevos se indexan durante la carga solo con una clave configurada. Las decisiones de modelos, fragmentación, citas, límites y privacidad están en [ADR 0005](adr/0005-rag-models-and-retrieval.md) y [hito-07.md](hito-07.md). La evaluación local usa vectores y respuestas sintéticos y no sustituye una medición de calidad del modelo real.

## Dirección objetivo

```text
Navegador -> Next.js / TypeScript -> FastAPI
                                      -> servicios de aplicación y dominio
                                      -> PostgreSQL (organizaciones y metadatos)
                                      -> almacenamiento de objetos (ficheros originales)
                                      -> pgvector (fragmentos y embeddings, hito RAG)
                                      -> proveedor LLM (OpenAI, según ADR 0005)
```

## Límites de diseño y seguridad

- El backend será autoridad para identidad, permisos y acceso a datos.
- El aislamiento por organización se aplicará en las consultas de negocio y se cubrirá con pruebas.
- Contraseñas y secretos de sesión/invitación se almacenan como hashes; los tokens no se registran ni se devuelven después de su emisión.
- Los binarios no se guardarán en tablas de negocio.
- Los archivos cargados se tratarán como datos no confiables: validar límites y contenido antes de aceptar, no confiar en nombre/extensión/MIME declarados, y nunca ejecutar ni interpretar archivos como instrucciones.
- El almacenamiento de documentos será privado y aislado por organización; acceso y borrado deberán autorizarse en el servidor.
- Secretos y URL de base de datos solo se leerán del entorno; no se registrarán en logs.
- Las consultas usarán parámetros/ORM, y los metadatos se validarán antes de persistir.
- Las solicitudes RAG envían documentos indexados, preguntas y contexto recuperado a OpenAI; no se deben usar datos sensibles sin aprobación explícita.
- Hito 4 no incorpora correo, verificación de email, recuperación de contraseña, MFA ni rate limiting distribuido; no considerar el login abierto listo para producción.
