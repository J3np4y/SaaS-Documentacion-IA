# Arquitectura inicial

## Estado del hito

FastAPI expone `/health`. PostgreSQL está definido como servicio local; todavía no hay conexión desde la API, migraciones, autenticación ni interfaz funcional.

## Dirección objetivo

```text
Navegador -> Next.js / TypeScript -> FastAPI
                                      -> servicios de aplicación y dominio
                                      -> PostgreSQL (organizaciones y metadatos)
                                      -> almacenamiento de objetos (ficheros originales)
                                      -> pgvector (fragmentos y embeddings, hito RAG)
                                      -> proveedor LLM (tras decisión documentada)
```

## Límites

- El backend será autoridad para identidad, permisos y acceso a datos.
- El aislamiento por organización se aplicará en las consultas de negocio y se cubrirá con pruebas.
- Los binarios no se guardarán en las tablas de negocio.
- No se integra proveedor LLM ni almacenamiento de documentos en este hito.
