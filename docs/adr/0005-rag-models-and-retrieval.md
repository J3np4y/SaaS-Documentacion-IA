# ADR 0005: modelos y recuperación para RAG

- Estado: aceptada para el Hito 7
- Fecha: 2026-10-09

## Resumen sencillo

La primera versión enviará a OpenAI el texto de documentos indexados y las preguntas para generar embeddings y respuestas. PostgreSQL con pgvector encontrará fragmentos de la misma organización; las respuestas devuelven el nombre del documento y el texto exacto que sirve de cita. La clave se configura fuera de Git. No se indexarán documentos ya existentes hasta que una persona lo solicite.

## Contexto

El Hito 6 ya extrae y permite buscar texto, pero todavía no recupera fragmentos por significado ni responde preguntas con fuentes. RAG combina recuperación y generación, pero introduce una frontera nueva de privacidad y coste al enviar texto a un proveedor externo. La recuperación y la comprobación de citas deben seguir bajo control del backend.

## Decisiones

- Usar la API de OpenAI para embeddings y respuestas; no se ejecutan modelos localmente en este hito.
- Valores iniciales configurables: `text-embedding-3-small` con 1536 dimensiones y `gpt-4o-mini`.
- Guardar fragmentos y embeddings en PostgreSQL con pgvector; limitar todas las consultas por organización autenticada.
- Crear fragmentos de hasta 1.000 caracteres, con solapamiento de 150; recuperar hasta cinco por pregunta y aplicar un mínimo inicial de similitud coseno de 0,45.
- Limitar pregunta a 1.000 caracteres y generación a 500 tokens.
- Citar nombre de documento y extracto literal guardado; no pedir al modelo que fabrique IDs, enlaces o páginas.
- No indexar en la migración el texto de documentos antiguos: la indexación de cada uno será una acción explícita.
- Mantener los documentos originales y el texto extraído aunque falle OpenAI; representar el estado de indexación y permitir reintentar.
- Cambiar las imágenes PostgreSQL de desarrollo y CI a `pgvector/pgvector:pg16`.
- No implementar cuotas ni rate limiting en esta fase; los topes por consulta no limitan la cantidad total de solicitudes.

## Seguridad y privacidad

- La clave OpenAI solo se obtiene del entorno y nunca se devuelve ni se registra.
- El texto enviado al proveedor es dato no confiable; las instrucciones recuperadas no sustituyen el prompt del sistema ni autorizan herramientas.
- La consulta vectorial aplica el tenant en base de datos antes de formar el contexto externo.
- Las citas se construyen desde filas recuperadas y se validan contra los mismos resultados; no se confía en identificadores sugeridos por el modelo.
- Las respuestas quedan limitadas a evidencia recibida; si no hay fragmentos suficientes, se devuelve una abstención sin llamar al generador.
- La integración externa puede fallar, tener coste, retener datos o cambiar condiciones. No usar documentos sensibles ni exponer el prototipo públicamente.

## Consecuencias

- Requiere internet, una cuenta/API key de OpenAI y puede generar costes variables.
- Una dimensión de embedding fija hace que cambiar de modelo requiera migrar y regenerar embeddings.
- El umbral de similitud es inicial, no una garantía: se revisa con ejemplos de evaluación y puede requerir recalibración.
- Sin cuota/rate limit, un usuario autenticado puede realizar solicitudes repetidas; esto debe resolverse antes de cualquier despliegue público.
