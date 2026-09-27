# Arquitectura

## Estado actual — Hito 2 en curso

FastAPI expone `/health`. PostgreSQL está definido como servicio local en Docker Compose, pero todavía no se conecta desde FastAPI. Next.js sirve la página inicial y consulta la API desde el servidor con `API_BASE_URL`.

```text
Navegador -> Next.js (página renderizada en servidor)
                         -> FastAPI /health

Docker Compose -> PostgreSQL (sin conexión desde FastAPI aún)
```

La ruta se fuerza dinámica para que el chequeo de estado no se almacene como una respuesta estática de build. Los errores de red se convierten en un estado genérico y no se devuelven detalles de infraestructura al navegador.

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
- Los binarios no se guardarán en las tablas de negocio.
- La URL de API es configuración server-side; no se publica mediante `NEXT_PUBLIC_*`.
- El chequeo de salud tiene timeout, no almacena caché y no sigue redirecciones.
- No se integra proveedor LLM ni almacenamiento de documentos en el Hito 2.
