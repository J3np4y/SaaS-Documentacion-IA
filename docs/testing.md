# Estrategia y registro de pruebas

## Enfoque

- Escribir una prueba junto a cada comportamiento nuevo relevante.
- Probar resultados observables, límites y fallos; no acoplar pruebas a detalles internos sin necesidad.
- Mantener datos ficticios y no usar documentos reales ni secretos.
- La CI ejecuta las comprobaciones automáticas en cada push y pull request.
- No declarar una comprobación como aprobada hasta haber ejecutado el comando y conservar su resultado.

## Hito 2 — frontend

### Pruebas unitarias automatizadas

`frontend/src/__tests__/api-health.test.ts` cubre:

1. La API devuelve el payload esperado y el chequeo apunta a `/health` sin caché.
2. Una respuesta HTTP no satisfactoria produce estado no disponible.
3. Un payload inesperado produce estado no disponible.
4. Una URL con esquema `file:` se rechaza antes de hacer una petición.
5. Una URL con credenciales embebidas se rechaza antes de hacer una petición.
6. Un fallo de red se transforma en un estado seguro y genérico.

`frontend/src/__tests__/api-status.test.tsx` verifica los mensajes accesibles para los estados disponible y no disponible. `frontend/src/test/setup.ts` limpia el DOM después de cada test para mantenerlos aislados.

### Comprobaciones de proyecto

- `npm.cmd test`: Vitest.
- `npm.cmd run lint`: ESLint.
- `npm.cmd run typecheck`: TypeScript estricto.
- `npm.cmd run build`: compilación de producción de Next.js.

### Estado de ejecución — 2026-09-27

Entorno: Node.js `v24.21.0`, npm `12.1.0`; `npm ls --depth=0` confirmó las dependencias instaladas.

- `npm.cmd run lint`: aprobado.
- `npm.cmd run typecheck`: aprobado.
- `npm.cmd run build`: aprobado según la salida local compartida. Next.js compiló `/` como ruta dinámica y `/_not-found` como estática.
- `npm.cmd test`: aprobado según la confirmación del usuario después de añadir limpieza del DOM entre tests con `afterEach(cleanup)`.
- `git diff --check`: aprobado.

La CI contiene los mismos checks de frontend y backend. Su ejecución en GitHub Actions queda pendiente de confirmar.
