# Hito 2 — interfaz web y conexión inicial con la API

## Estado: completado

El usuario confirmó que las pruebas, lint, tipos y build locales están correctos y que GitHub Actions termina en verde.

## Objetivo

Construir la primera interfaz del producto y conectarla con la API existente, manteniendo el alcance pequeño y entendible.

## Incluyó

1. Inicializar `frontend/` con Next.js, TypeScript y App Router.
2. Crear una página inicial sencilla, adaptable y accesible.
3. Consultar `GET /health` desde el servidor Next.js usando `API_BASE_URL`.
4. Mostrar estados disponibles y no disponibles sin filtrar errores de red al navegador.
5. Añadir pruebas unitarias para respuesta, fallos, validación de URL y anuncios accesibles.
6. Documentar instalación, configuración, pruebas y arranque local.
7. Añadir a CI las comprobaciones de lint, tipos, pruebas y compilación del frontend.

## Seguridad y mantenibilidad aplicadas

- Solo se permiten esquemas `http` y `https` para la URL configurada; las credenciales embebidas se rechazan.
- La petición tiene timeout, no usa caché y no sigue redirecciones.
- No se envían detalles internos de red al navegador ni se usan variables `NEXT_PUBLIC_*` para la URL.
- Los comentarios explican decisiones y límites no obvios; cada comportamiento nuevo relevante tiene pruebas de éxito y fallo.

## Criterios de aceptación

- [x] Instalación reproducible con `package-lock.json`.
- [x] Página inicial arranca y compila.
- [x] Estado disponible y no disponible cubiertos.
- [x] `API_BASE_URL` solo se consume del lado servidor.
- [x] Pruebas, lint, tipos y build locales aprobados.
- [x] Checks de GitHub Actions confirmados en verde.
- [x] Resultados registrados en [testing.md](testing.md).
