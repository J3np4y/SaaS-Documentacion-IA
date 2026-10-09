# Estrategia y registro de pruebas

Este es el registro de referencia para los resultados observados. Los hitos pueden resumir sus criterios y enlazar aquí, pero una comprobación solo se considera ejecutada cuando hay un resultado registrado. Para saber qué estudiar primero, consulta la [guía de aprendizaje](guia-aprendizaje.md).

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
## Hito 5 — carga y gestión de documentos

El alcance aprobado está en [hito-05.md](hito-05.md) y la decisión de almacenamiento en [ADR 0004](adr/0004-document-storage.md).

### Hito 5 — carga inicial: verificaciones locales y CI aprobadas

Alcance acordado: PDF, DOCX y TXT, máximo 10 MiB por archivo, almacenamiento local privado, permisos iguales para `owner` y `member`, borrado físico, sin cuota total por organización ni análisis antimalware.

- Frontend: `npm.cmd test` aprobó 19 pruebas; typecheck, lint y build aprobados durante el desarrollo del flujo inicial.
- Backend: `pytest -q` aprobó 48 pruebas contra PostgreSQL desechable, incluidas autenticación, migración, validación de archivos, aislamiento por organización, límites y compensación de fallos de base de datos. Ruff y compilación Python aprobados.
- Flujo funcional adicional contra SQLite temporal: registro, carga, listado, descarga con encabezados seguros y borrado físico pasaron. Esto comprueba el flujo HTTP, pero no sustituye las pruebas de integración ni la migración en PostgreSQL.
- Migraciones PostgreSQL verificadas con ciclo `upgrade head` → `downgrade base` → `upgrade head`.
- La primera ejecución encontró un archivo PDF aceptado con extensión TXT; se corrigió la validación y las 48 pruebas pasaron al repetir la suite completa.
- GitHub Actions aprobada en el commit `27db9cca4265eff5f72c2a1bd783128482fd9bea`: [ejecución 37920779623](https://github.com/J3np4y/SaaS-Documentacion-IA/actions/runs/37920779623). Los jobs `backend` (Ruff y pytest con PostgreSQL) y `frontend` (lint, typecheck, tests y build) finalizaron correctamente.

La ejecución anterior del commit `8165e9a` falló porque aún aceptaba un PDF llamado `.txt`; la corrección y prueba de regresión están incluidas en `27db9cc`.

## Hito 6 — extracción, ingesta y búsqueda textual

### Resultados locales observados

- `backend`: `pytest -q` aprobó 61 pruebas contra PostgreSQL desechable, incluyendo extracción de PDF/DOCX/TXT, límites, carga conservada tras fallo, reprocesamiento y búsqueda aislada por organización. Ruff aprobado.
- Migración PostgreSQL verificada con `upgrade head` → `downgrade base` → `upgrade head`, incluyendo la columna generada y el índice GIN de búsqueda española.
- `frontend`: 22 pruebas, lint, typecheck y build de producción aprobados.
- La suite backend mantiene una advertencia Starlette/httpx deprecada; no afectó los resultados.
- GitHub Actions aprobada en el commit `73d073af8974a085d03cd860bbfdb01e5bef9707`: [ejecución 37934434186](https://github.com/J3np4y/SaaS-Documentacion-IA/actions/runs/37934434186). Los jobs de backend (Ruff y pytest con PostgreSQL) y frontend (lint, typecheck, tests y build) finalizaron correctamente.

## Hito 7 — RAG, citas y evaluación local

- Backend: `pytest -q` aprobó 71 pruebas contra PostgreSQL desechable con pgvector. Se verificaron aislamiento por organización, indexación, persistencia ante fallos del proveedor, citas, abstención y validación de respuestas.
- Evaluación determinista: 2/2 consultas recuperaron la fuente esperada y produjeron citas correctas; 1/1 consulta sin evidencia se abstuvo. Los vectores y respuestas son sintéticos; no miden la calidad de OpenAI.
- Seguridad del prompt: una prueba confirma que el texto adversarial de un documento permanece en el mensaje de evidencia del usuario, separado de las instrucciones de sistema. Esto no demuestra inmunidad total a prompt injection.
- Ruff aprobado.
- Migraciones PostgreSQL/pgvector verificadas con `upgrade head` → `downgrade base` → `upgrade head`, incluida la extensión vectorial y el índice HNSW.
- Frontend: 25 pruebas, lint, typecheck y build de producción aprobados.
- No se configuró una clave de OpenAI ni se hicieron solicitudes reales. La advertencia Starlette/httpx deprecada continúa sin afectar la suite.
- GitHub Actions aprobada para el commit `a2e43e1231217e02b40d23adb3ed58e0e04aaeaf`: [ejecución 37969999940](https://github.com/J3np4y/SaaS-Documentacion-IA/actions/runs/37969999940). Los jobs de backend (Ruff y pytest contra pgvector) y frontend (lint, typecheck, tests y build) terminaron correctamente.

## Hito 8 — cuotas, telemetría privada y contenedores

### Resultados locales observados

- Backend: `pytest -q` aprobó 80 pruebas contra PostgreSQL desechable con pgvector; Ruff y `compileall` aprobaron. La ejecución local usó Python 3.14. Se mantiene una advertencia deprecada de Starlette/httpx, sin fallos.
- Las pruebas cubren límites diarios y mensuales, periodos UTC, concurrencia, aislamiento entre organizaciones, fallos del proveedor y fallo cerrado si no se puede consultar la cuota. También comprueban que una carga sigue disponible cuando la cuota no puede reservarse y que ni métricas ni logs registran query string o identidad.
- Migraciones PostgreSQL verificadas con `upgrade head` → `downgrade base` → `upgrade head`; la migración de Hito 8 se aplicó de nuevo al stack Compose.
- Frontend: 25 pruebas, lint, typecheck y build de producción aprobados tras actualizar el texto de la portada para reflejar el RAG implementado.
- Las imágenes de API y frontend se construyeron. El stack Compose quedó saludable; el frontend respondió HTTP 200 e indicó la API disponible, `/ready` y `/metrics` respondieron dentro de la red privada y solo `127.0.0.1:3000` se publicó en el host. La configuración no publica puertos para API ni PostgreSQL.
- Una cuenta sintética pudo iniciar sesión después de reiniciar PostgreSQL, confirmando persistencia básica del volumen. Los logs observados fueron eventos JSON sin query string, email ni contraseña; las métricas fueron consultables dentro del contenedor API.
- No se configuró una clave de OpenAI ni se hicieron solicitudes reales.
- GitHub Actions aprobada para el commit `0ec58cc615b8903f3b4bfa6f5c941026aaa21709`: [ejecución 37980325026](https://github.com/J3np4y/SaaS-Documentacion-IA/actions/runs/37980325026). Los jobs `backend` (Ruff y pytest con PostgreSQL/pgvector) y `frontend` (lint, typecheck, tests y build) finalizaron correctamente.