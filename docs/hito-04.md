# Hito 4 — identidad, organizaciones y permisos

## Estado: completado; verificación local aprobada

La verificación de este hito está resumida en [testing.md](testing.md). El Hito 3 está confirmado por CI: [ejecución 36760916434](https://github.com/J3np4y/SaaS-Documentacion-IA/actions/runs/36760916434), ambos jobs correctos sobre `main` (`c5ebb8b`, 30 de septiembre de 2026). El alcance de este hito se acordó antes de implementar autenticación.

## Objetivo de aprendizaje

Construir un flujo pequeño, completo y explicable para demostrar quién usa la aplicación, cómo inicia sesión y qué puede hacer dentro de una organización. La interfaz ayuda a recorrerlo; el backend es la autoridad para permisos y aislamiento de datos.

## Recorrido recomendado para empezar

No intentes aprender todos los conceptos de autenticación a la vez. Sigue este orden y usa las secciones detalladas de abajo como referencia cuando llegues a cada tema:

1. **Quién es quién:** distingue usuario, organización y pertenencia. Primero entiende qué dato relaciona a una persona con un grupo.
2. **Entrar y salir:** aprende qué comprueba el login y qué significa mantener una sesión. Una cookie es un dato que el navegador envía en solicitudes; la contraseña no debe guardarse como texto legible.
3. **Qué se permite:** diferencia autenticación (“¿quién eres?”) de autorización (“¿puedes hacer esto?”). Comprueba una regla sencilla para `owner` y otra para `member`.
4. **Compartir acceso:** entiende que una invitación funciona como una llave temporal y de un solo uso; estudia vencimiento y consumo antes de mirar los detalles de implementación.
5. **Recorrer la aplicación:** prueba el flujo desde la interfaz y confirma que el backend aplica las mismas reglas, aunque alguien cambie los datos enviados desde el navegador.

Al terminar cada fase, explica la regla con tus palabras y ejecuta las pruebas asociadas. Si quieres revisar la justificación de las decisiones, consulta [ADR 0003](adr/0003-authentication-and-access.md). Los términos técnicos, rutas y casos límite que siguen son una referencia completa; no hace falta memorizarlos para empezar.

## Decisiones de producto y alcance

- Registro abierto con email y contraseña. Un registro sin invitación crea una organización y asigna al primer usuario el rol `owner`.
- Una cuenta pertenece a una sola organización en esta primera versión.
- Roles iniciales: `owner` y `member`. Los miembros pueden consultar la información de su organización; el propietario puede ver/administrar sus miembros y roles, crear invitaciones y retirar miembros.
- El propietario puede ascender un miembro a propietario o cambiar otro propietario a miembro, pero no se puede dejar la organización sin propietario.
- Un propietario genera una invitación de un solo uso con vencimiento; comparte manualmente el código/enlace. El invitado lo presenta al registrarse y queda como `member` de esa organización. Un invitado que ya tenga cuenta no puede usarla para cambiar de organización en este hito.
- La invitación es un secreto bearer: quien obtenga el código puede usarlo. No se integra correo ni se liga la invitación a un email verificado. La interfaz solo muestra el código al crearlo.
- Se incluyen pantallas web mínimas para registro, inicio/cierre de sesión, estado de sesión, miembros y administración de invitaciones/roles.
- No se incluyen verificación de email, recuperación de contraseña, SSO, autenticación multifactor, cambio de organización ni carga de documentos.

## Conceptos y fases de trabajo

### 1. Identidad, organización y pertenencia

**Aprende:** identidad responde “quién es”; una organización es el límite del tenant; una pertenencia relaciona un usuario con una organización y un rol. Autenticación no es autorización.

**Construye:** tablas `users`, `memberships` e `invitations` sobre las organizaciones existentes. La base impone email normalizado único y, en este hito, una pertenencia por usuario. La pertenencia guarda el rol; no se confía en un `organization_id` arbitrario enviado por el cliente.

**Comprueba:** migración hacia delante y hacia atrás; registro que crea organización y propietario atómicamente; invitación válida que añade un miembro; restricciones de unicidad y relaciones.

La migración preserva organizaciones/documentos preexistentes, pero no inventa propietarios ni credenciales para identidades antiguas. En una base con datos previos, esas organizaciones quedan sin acceso de usuario hasta que se defina un aprovisionamiento administrativo explícito. Revertir la migración elimina los datos nuevos de usuarios, sesiones, pertenencias e invitaciones; hacer respaldo antes de revertir datos que se quieran conservar.

### 2. Contraseñas, sesión y cookies

**Aprende:** una contraseña no se cifra ni se guarda en claro; se almacena un hash lento con sal mediante una biblioteca estándar. La cookie lleva un identificador aleatorio opaco, no la contraseña ni datos de usuario. El hash del identificador permite revocar una sesión desde el servidor.

**Construye:** hash de contraseñas Argon2id con `pwdlib`; sesiones de PostgreSQL con identificador aleatorio de alta entropía, persistiendo solo SHA-256 del identificador. La cookie `docs_assistant_session` es `HttpOnly`, `SameSite=Lax`, `Path=/`, tiene duración máxima de 7 días y usa `Secure` en despliegues HTTPS. La configuración local puede desactivar `Secure`; producción debe activarlo explícitamente. Logout revoca la sesión y elimina la cookie.

**Comprueba:** contraseña incorrecta y cuenta inexistente producen el mismo error de login; cookies y hashes no aparecen en respuestas ni logs; las sesiones vencidas/revocadas no autentican. El backend comprueba `Origin` contra `FRONTEND_ORIGIN` en operaciones que cambian estado, además de las restricciones de cookie.

### 3. Autorización por rol y tenant

**Aprende:** autenticarse no concede automáticamente permiso. Las reglas deben verificarse en el servidor en cada operación y cada consulta debe quedar dentro de la organización de la sesión.

**Construye:** dependencias reutilizables para usuario actual y rol `owner`; rutas para consultar miembros, crear invitaciones, cambiar roles y retirar miembros. El navegador no decide ni puede elevar el rol.

**Comprueba:** el miembro no puede administrar personas/invitaciones; un propietario de otra organización no puede acceder a los miembros o recursos de esta; no se elimina al último propietario; se rechazan roles inválidos.

### 4. Invitación de un solo uso

**Aprende:** un enlace de invitación es una capacidad secreta: poseerla concede el derecho descrito por la invitación. Debe tener entropía, vencimiento, uso único y almacenamiento seguro.

**Construye:** código aleatorio mostrado una vez, hash almacenado, rol siempre `member`, organización de destino, creador, fecha de expiración y fecha de consumo. Al registrarse con el código, la creación del usuario/pertenencia y el consumo del código ocurren en una transacción.

**Comprueba:** código válido, desconocido, vencido y ya consumido; dos consumos concurrentes no crean dos membresías. Duración inicial de invitación: 24 horas.

### 5. Interfaz y flujo completo

**Aprende:** la interfaz mejora la experiencia, pero no reemplaza controles del servidor. Los datos de sesión se consultan al backend; los secretos de sesión permanecen en cookie HttpOnly.

**Construye:** formularios accesibles de registro/login, cierre de sesión y estado autenticado; el propietario puede crear y copiar una invitación, ver miembros, cambiar roles y retirar miembros. El frontend usa rutas proxy server-side para enviar solicitudes al backend y reenviar la cookie sin exponer credenciales de servicio al navegador.

**Comprueba:** estados de carga, éxito y error; formularios no exponen respuestas técnicas; cierre de sesión actualiza el estado visible.

## API prevista

- `POST /auth/register`: crea una cuenta; sin invitación crea organización y `owner`; con invitación crea `member` en la organización de la invitación. Emite la cookie de sesión.
- `POST /auth/login`: verifica email y contraseña y emite una sesión.
- `POST /auth/logout`: revoca la sesión actual y elimina cookie.
- `GET /auth/me`: devuelve solo identidad pública, organización y rol de la sesión actual.
- `GET /organizations/me/members`: lista miembros de la organización actual (solo `owner`).
- `POST /organizations/me/invitations`: genera invitación de un solo uso (solo `owner`).
- `PATCH /organizations/me/members/{user_id}`: cambia entre roles `owner` y `member` (solo `owner`, conserva al menos un propietario).
- `DELETE /organizations/me/members/{user_id}`: retira una pertenencia de la organización actual (solo `owner`, conserva al menos un propietario).

Los esquemas HTTP nunca devuelven hashes de contraseña, identificadores de sesión, hashes/tokens de invitación ni campos internos.

## Seguridad y limitaciones conocidas

- Las consultas de miembros/invitaciones siempre se acotan a la organización derivada de la sesión, nunca a una organización seleccionada libremente por el cliente.
- Cookies `HttpOnly`, `SameSite=Lax`, vencimiento, revocación en servidor y validación de `Origin` reducen riesgos de robo de sesión y CSRF. `Secure` debe activarse al usar HTTPS.
- Login no diferencia entre email desconocido y contraseña errónea. Validar longitudes y normalizar email antes de persistir.
- Invitaciones son bearer secrets; no incluir el código en logs, persistir solo su hash y ocultarlo después de mostrarlo una vez. Sin verificación de email, el proyecto no puede probar que el registrante controla esa dirección.
- No hay rate limiting distribuido ni recuperación de cuenta. No desplegar el login abierto a Internet sin añadir limitación de intentos/abuso, recuperación segura y verificación de email.
- Las rutas de frontend actúan como proxy del backend; `API_BASE_URL` sigue siendo configuración solo de servidor. El navegador no recibe tokens en JavaScript.
- Los datos de documentos y salidas de modelos continúan siendo datos no confiables; este hito no añade RAG ni lectura de documentos.

## Criterios de aceptación

- [x] La migración añade las tablas/restricciones necesarias y puede revertirse; se comprobó `upgrade head` → `downgrade base` → `upgrade head` contra PostgreSQL.
- [x] Registro normal crea usuario, organización y rol `owner` en una sola transacción.
- [x] Registro con invitación válida crea una cuenta `member` en la organización indicada y consume el secreto una sola vez.
- [x] Login/logout/`/auth/me` implementan sesiones persistentes, vencibles y revocables.
- [x] No se persisten contraseñas ni tokens en claro; no se devuelven secretos internos.
- [x] Permisos `owner`/`member`, último propietario y aislamiento entre organizaciones se prueban en backend.
- [x] UI mínima permite el recorrido acordado, con estados accesibles de carga, éxito y error.
- [x] Las 19 pruebas backend (incluidas las 12 de integración PostgreSQL), las 14 pruebas frontend, Ruff, lint, typecheck y build pasaron; [testing.md](testing.md) registra los resultados observados.

## Cómo avanzar para aprender

Completar una fase cada vez. Antes de codificar, describir en lenguaje normal el dato y la regla que se implementan; al terminar, ejecutar la prueba que demuestra esa regla y revisar el fallo esperado. Mantener las migraciones pequeñas, comparar el modelo ORM con el esquema real y revisar cada endpoint preguntando: “¿quién autentica esta solicitud, qué rol tiene y de qué organización proviene?”.
