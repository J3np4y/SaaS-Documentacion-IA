# Arquitectura

## Estado actual — Hito 3 completado y confirmado por CI

FastAPI expone `/health` y `/ready`; SQLAlchemy obtiene una sesión por petición y Alembic versiona el esquema inicial. Next.js sirve la página inicial y consulta la API desde el servidor con `API_BASE_URL`.

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

El primer esquema persistente cubrirá `Organization` y metadatos `Document` enlazados mediante clave foránea. Los binarios no se guardarán en PostgreSQL. Los endpoints de CRUD, autenticación y permisos quedan para hitos posteriores.

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

## Dirección objetivo

```text
Navegador -> Next.js / TypeScript -> FastAPI
                                      -> servicios de aplicación y dominio
                                      -> PostgreSQL (organizaciones y metadatos)
                                      -> almacenamiento de objetos (ficheros originales)
                                      -> pgvector (fragmentos y embeddings, hito RAG)
                                      -> proveedor LLM (tras decisión documentada)
```

## Límites de diseño y seguridad

- El backend será autoridad para identidad, permisos y acceso a datos.
- El aislamiento por organización se aplicará en las consultas de negocio y se cubrirá con pruebas.
- El backend es la autoridad para autenticar usuarios, comprobar roles y aislar datos por organización.
- Contraseñas y secretos de sesión/invitación se almacenan como hashes; los tokens no se registran ni se devuelven después de su emisión.
- Los binarios no se guardarán en tablas de negocio.
- Secretos y URL de base de datos solo se leerán del entorno; no se registrarán en logs.
- Las consultas usarán parámetros/ORM, y los metadatos se validarán antes de persistir.
- No se integra proveedor LLM ni almacenamiento de documentos en el Hito 3.
- Hito 4 no incorpora correo, verificación de email, recuperación de contraseña, MFA ni rate limiting distribuido; no considerar el login abierto listo para producción.
