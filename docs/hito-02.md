# Hito 2 — interfaz web y conexión inicial con la API

## Objetivo

Construir la primera interfaz del producto y conectarla con la API existente, manteniendo el alcance pequeño y entendible. Al terminar, se podrá abrir una página web local y ver si el backend responde.

## Incluye

1. Inicializar `frontend/` con Next.js, TypeScript y App Router.
2. Crear una página inicial sencilla, adaptable y accesible.
3. Consultar `GET /health` desde el servidor Next.js usando `API_BASE_URL`.
4. Mostrar estados disponibles y no disponibles sin filtrar errores de red al navegador.
5. Añadir pruebas unitarias para la respuesta, los fallos, la validación de URL y los anuncios accesibles.
6. Documentar instalación, configuración, pruebas y arranque local.
7. Añadir a CI las comprobaciones de lint, tipos, pruebas y compilación del frontend.

## Fuera de alcance

- Registro, inicio de sesión y gestión de usuarios.
- Organizaciones, roles y permisos.
- Subida o consulta de documentos.
- Conexión de FastAPI a PostgreSQL, modelos de datos o migraciones.
- RAG, agentes, proveedores LLM o almacenamiento vectorial.
- Despliegue público.

## Criterios de aceptación

- El frontend se instala siguiendo solo los pasos documentados y el lockfile queda versionado.
- Arranca en local y pasa lint, verificación de tipos, pruebas y build.
- Con FastAPI activa, muestra el estado disponible basándose en `/health`.
- Si FastAPI no responde, la página sigue cargando y presenta un estado no disponible claro.
- `API_BASE_URL` solo se consume del lado servidor.
- CI ejecuta las comprobaciones del backend y frontend.
- Las pruebas locales y CI quedan registradas en [testing.md](testing.md).

## Seguridad y mantenibilidad aplicadas

- Solo se permiten esquemas `http` y `https` para la URL configurada; las credenciales embebidas se rechazan.
- La petición tiene timeout, no usa caché y no sigue redirecciones.
- No se envían detalles internos de red al navegador ni se usan variables `NEXT_PUBLIC_*` para la URL.
- Los comentarios del código explican decisiones y límites que no resultan obvios; evitan repetir lo que ya expresa el código.
- Cada comportamiento nuevo relevante recibe pruebas para resultados correctos y fallos previsibles.

## Estado de trabajo

- [x] Scaffold Next.js, TypeScript y App Router.
- [x] Pantalla inicial con estado de API.
- [x] Chequeo server-side y casos de prueba iniciales.
- [x] Instrucciones de desarrollo y estrategia de pruebas.
- [x] Instalar dependencias y generar `package-lock.json`.
- [x] Ejecutar pruebas, lint, tipos y build localmente.
- [ ] Confirmar los checks en GitHub Actions.
