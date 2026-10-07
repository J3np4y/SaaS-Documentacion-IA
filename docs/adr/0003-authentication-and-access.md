# ADR 0003: autenticación y acceso del Hito 4

- Estado: aceptada
- Fecha: 2026-10-07

## Contexto

El Hito 3 dejó persistencia para organizaciones, pero no usuarios ni permisos. La aplicación necesita un primer flujo seguro y comprensible que prepare el aislamiento multi-tenant sin introducir proveedor de identidad o correo externo.

## Decisiones

- Email y contraseña con hash Argon2id mediante `pwdlib`; nunca guardar la contraseña en claro ni implementar criptografía propia.
- Mantener sesiones revocables en PostgreSQL. La cookie contiene un identificador aleatorio opaco; la base solo almacena su hash.
- Registro abierto crea una organización y el rol inicial `owner`. La cuenta tiene una sola organización durante el Hito 4.
- Roles `owner` y `member` se guardan en la pertenencia. El servidor verifica autorización y deriva el tenant de la sesión.
- El propietario invita con un secreto aleatorio de un solo uso, con duración limitada, compartido manualmente. La base conserva solo el hash. El invitado se convierte en `member` al registrarse.
- El frontend usa rutas proxy server-side para que el navegador no lea el secreto de sesión; el backend valida el origen de operaciones que cambian estado.
- No integrar correo en este hito; verificación de email, recuperación de contraseña y rate limiting distribuido quedan como limitaciones explícitas antes de cualquier despliegue público.

## Alternativas consideradas

- JWT bearer sin estado: descartado para el primer flujo porque la revocación y el logout son menos directos para aprender y demostrar.
- Estado de sesión firmado íntegramente en cookie: descartado porque la revocación centralizada no es directa y el contenido queda ligado a la cookie.
- Proveedor externo OIDC: aplazado para mantener el flujo didáctico y evitar un servicio/configuración externa antes de comprender sesiones y autorización.
- Enviar invitaciones por email: aplazado hasta decidir proveedor y verificación de dominio/dirección.

## Consecuencias

El backend controla login, sesión, membresía y permisos. Se añaden dependencias de hashing y validación de email solo si la implementación las requiere y se justifican en el cambio. Los tokens son secretos bearer y requieren alta entropía, almacenamiento como hash, vencimiento, uso único y ausencia de logs. La arquitectura no está lista para un despliegue público hasta añadir controles de abuso, verificación de email y recuperación de cuenta.

Las organizaciones/documentos ya existentes se conservan; sin una identidad confiable no se asigna automáticamente un propietario. Revertir la migración elimina las nuevas cuentas y datos de acceso, por lo que requiere respaldo si deben conservarse.
