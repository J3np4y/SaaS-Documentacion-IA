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

## Hito 3 — persistencia: completado y CI confirmada

### Resultados confirmados por el usuario

- PostgreSQL `db` y `db-test` arrancan correctamente; Alembic aplicó la migración.
- `GET /health` devolvió `{"status":"ok"}` y `GET /ready` indicó que PostgreSQL estaba disponible.
- `backend`: `pytest` aprobó las 6 pruebas (incluidas 3 de integración), con una advertencia deprecada de Starlette/httpx; `ruff check .` aprobó.
- `frontend`: el usuario confirmó que `npm.cmd test`, `npm.cmd run lint`, `npm.cmd run typecheck` y `npm.cmd run build` terminaron correctamente.
- El usuario confirmó que la aplicación web arranca y muestra la API disponible.
- GitHub Actions: [run 36760916434](https://github.com/J3np4y/SaaS-Documentacion-IA/actions/runs/36760916434), commit `c5ebb8b7e4ab57b5ecf4ba81eafef2e048ff9c7c` en `main`; jobs `backend` y `frontend` terminaron correctamente. El backend arrancó PostgreSQL, ejecutó Ruff y pytest; frontend ejecutó instalación reproducible, lint, tipos, tests y build.

Las pruebas de integración usan únicamente `TEST_DATABASE_URL`, que debe apuntar a la base desechable `docs_assistant_test`: el fixture elimina y recrea su esquema `public`.

## Hito 4 — identidad, sesiones y permisos: implementación y verificación local completadas

La especificación didáctica está en [hito-04.md](hito-04.md). Antes de registrar resultados, cubrir:

- Registro normal: usuario, organización y rol `owner` en una transacción; email normalizado único y contraseña validada.
- Registro con invitación: alta `member` en la organización prevista, secreto de invitación vencido/desconocido/reutilizado y uso concurrente.
- Hash Argon2id; login con credenciales erróneas y respuesta indistinguible para usuario desconocido/contraseña errónea.
- Cookies HttpOnly, Secure según configuración, SameSite, vencimiento; sesión activa, vencida, revocada y logout.
- Validación de `Origin` en cambios de estado, entrada malformada y respuestas genéricas sin detalles internos.
- Matriz de permisos `owner`/`member`, cambio/eliminación de roles, último propietario y denegación de acceso entre organizaciones.
- Formularios y estados accesibles de registro, login, logout, invitaciones y administración en las pruebas frontend.

Las pruebas de integración continúan usando solo `TEST_DATABASE_URL` apuntada a `docs_assistant_test`.

### Resultados locales observados

- `backend`: `pytest -q` aprobó las 19 pruebas (7 unitarias y 12 de integración) contra el PostgreSQL desechable `docs_assistant_test`. La suite emitió una advertencia deprecada de Starlette/httpx, sin fallos.
- `backend`: `ruff check .` aprobado.
- Migraciones aplicadas a PostgreSQL real en el ciclo `upgrade head` → `downgrade base` → `upgrade head`.
- `frontend`: lint, typecheck, 14 pruebas y build aprobados.
- `npm ci` informó 9 avisos de vulnerabilidad (1 moderado, 6 altos y 2 críticos) en el árbol de dependencias instalado; no se actualizaron dependencias frontend fuera del alcance del Hito 4.

La verificación local del hito está completa; no se ha ejecutado una CI de GitHub para estos cambios. La falta de rate limiting distribuido, verificación de correo y recuperación de contraseña debe permanecer visible como limitación: el hito no implica que el login esté listo para producción.
## Hito 5 — carga y gestión de documentos: pruebas previstas

El plan de alcance y aprendizaje está en [hito-05.md](hito-05.md). No se ha implementado ni ejecutado todavía comportamiento de subida.

Cuando se aprueben las decisiones de formatos y límites, almacenamiento, permisos y borrado, cubrir:

- Rechazo de archivo vacío, demasiado grande, extensión/tipo no permitido, contenido que no corresponde con el tipo declarado y nombre malformado; aceptación de cada formato permitido.
- Tratamiento seguro de nombres Unicode, separadores, rutas relativas, nombres duplicados y caracteres de control; las claves físicas deben generarse en servidor.
- Persistencia de metadatos y bytes, estado ante error de almacenamiento o escritura de base de datos, y borrado sin dejar contenido huérfano (o documentar explícitamente la recuperación/compensación).
- Propietario y miembro según la matriz de permisos acordada; denegar lectura, descarga, modificación y borrado entre organizaciones, incluso alterando UUID o nombre de objeto.
- Descarga autenticada y privada, encabezados seguros, errores que no revelan ruta física/URL interna y ausencia de bytes, datos personales o secretos en logs.
- Pruebas de UI para carga, progreso si se implementa, éxito, validación, error recuperable, lista vacía y acciones no autorizadas.
- Prueba real contra el backend de almacenamiento elegido además de dobles para fallos; mantener PostgreSQL aislado para metadatos e integridad.

No se reportarán resultados para estos casos hasta implementar las pruebas y ejecutarlas. Antimalware, cuotas y límites de tasa necesitan decisión explícita o una limitación visible antes de exponer la subida fuera de un entorno local de aprendizaje.