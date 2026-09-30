# Estrategia y registro de pruebas

## Enfoque

- Escribir pruebas junto a cada comportamiento nuevo relevante.
- Probar resultados observables, límites y fallos previsibles.
- Mantener datos ficticios; no usar documentos reales ni secretos.
- No declarar una comprobación aprobada hasta ejecutarla o recibir un resultado verificable.

## Hito 2 — frontend: completado

### Pruebas automatizadas

`frontend/src/__tests__/api-health.test.ts` cubre respuesta válida, respuesta HTTP fallida, payload inesperado, esquema URL no permitido, credenciales embebidas y fallo de red.

`frontend/src/__tests__/api-status.test.tsx` comprueba los textos accesibles de estado y el atributo `aria-live`. `frontend/src/test/setup.ts` limpia el DOM después de cada prueba para mantenerlas aisladas.

### Comprobaciones y resultado

- `npm.cmd test`: aprobado según confirmación del usuario después de configurar la limpieza del DOM.
- `npm.cmd run lint`: aprobado.
- `npm.cmd run typecheck`: aprobado.
- `npm.cmd run build`: aprobado; `/` se renderiza bajo demanda y `/_not-found` se prerenderiza.
- GitHub Actions para backend y frontend: el usuario confirmó que la ejecución está en verde.

Entorno local confirmado: Node.js `v24.21.0`, npm `12.1.0`. El lockfile está versionado para instalaciones reproducibles.

## Hito 3 — persistencia: completado localmente; CI pendiente

### Resultados confirmados por el usuario

- PostgreSQL `db` y `db-test` arrancan correctamente; Alembic aplicó la migración.
- `GET /health` devolvió `{"status":"ok"}` y `GET /ready` indicó que PostgreSQL estaba disponible.
- `backend`: `pytest` aprobó las 6 pruebas (incluidas 3 de integración), con una advertencia deprecada de Starlette/httpx; `ruff check .` aprobó.
- `frontend`: el usuario confirmó que `npm.cmd test`, `npm.cmd run lint`, `npm.cmd run typecheck` y `npm.cmd run build` terminaron correctamente.
- El usuario confirmó que la aplicación web arranca y muestra la API disponible.
- GitHub Actions para estos cambios todavía no está confirmado.

Las pruebas de integración usan únicamente `TEST_DATABASE_URL`, que debe apuntar a la base desechable `docs_assistant_test`: el fixture elimina y recrea su esquema `public`.