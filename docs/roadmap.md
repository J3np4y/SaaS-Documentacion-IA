# Hoja de ruta

## Hito 1 — base ejecutable y documentada: completado

- Repositorio independiente y estructura con responsabilidades separadas.
- API FastAPI mínima con endpoint `/health` y prueba automatizada.
- PostgreSQL local definido con Docker Compose y credenciales configurables.
- README, arquitectura, decisión técnica y guía para asistentes.
- Arranque local de la API y respuesta correcta del endpoint de salud confirmados.

## Hito 2 — interfaz web y conexión inicial con la API: validación final pendiente

- [x] Scaffold Next.js con TypeScript y App Router en `frontend/`.
- [x] Pantalla inicial adaptable y accesible.
- [x] Consulta server-side de `/health` y presentación del estado de API.
- [x] Pruebas unitarias iniciales y guía de buenas prácticas.
- [x] Instrucciones de instalación y arranque.
- [x] CI con lint, tipos, pruebas y compilación de frontend.
- [x] Generar `package-lock.json` y usarlo en instalaciones reproducibles.
- [x] Ejecutar localmente pruebas, lint, tipos y build.
- [ ] Confirmar el resultado de GitHub Actions.

Ver el alcance en [hito-02.md](hito-02.md) y el registro de comprobaciones en [testing.md](testing.md).

## Hitos posteriores

3. Modelo de dominio, conexión API-PostgreSQL y migraciones.
4. Autenticación, organizaciones, roles y permisos.
5. Subida, validación, listado y eliminación de documentos.
6. Ingesta, extracción y búsqueda textual.
7. RAG con pgvector, citas y evaluación.
8. Observabilidad, control de coste y despliegue.
