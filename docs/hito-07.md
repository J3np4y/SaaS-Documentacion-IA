# Hito 7 — RAG, citas y evaluación

## Estado: implementación y comprobaciones locales completadas; CI pendiente

El Hito 6 permite buscar texto extraído con PostgreSQL. Este hito propone recuperar pasajes relevantes y usarlos para redactar respuestas que indiquen las fuentes. El sistema debe reconocer cuándo sus documentos no aportan evidencia suficiente en lugar de inventar una respuesta.

## Objetivo de aprendizaje

Entender las partes de RAG (generación aumentada por recuperación): preparar fragmentos, representarlos mediante embeddings, encontrar los más cercanos a una pregunta y enviar ese contexto a un modelo generativo. La recuperación no concede permisos: tanto los fragmentos como las citas se filtran en el backend por la organización de la sesión.

## Alcance implementado

- Dividir el texto extraído en fragmentos trazables a su documento de origen y posición.
- Generar y guardar embeddings con una dimensión y modelo documentados.
- Recuperar los fragmentos más relevantes con pgvector, limitados a documentos de la organización actual.
- Generar respuestas basadas únicamente en las fuentes recuperadas, con citas que permitan abrir el documento correspondiente.
- Abstenerse cuando no haya evidencia suficiente; tratar los documentos recuperados como datos no confiables, nunca como instrucciones.
- Crear un pequeño conjunto de preguntas y respuestas esperadas para medir recuperación, citas y abstención.
- Mantener OCR, agentes con herramientas, carga de documentos sensibles y despliegue público fuera del hito.

## Decisiones acordadas

- Proveedor: API de OpenAI para embeddings y respuestas. El contenido de documentos indexados, las preguntas y el contexto recuperado se enviarán a OpenAI; quien despliegue debe configurar una API key propia y considerar sus condiciones de privacidad y coste.
- Modelos iniciales, configurables por entorno: `text-embedding-3-small` (1536 dimensiones) y `gpt-4o-mini`. Referencias: [embeddings](https://developers.openai.com/api/docs/models/text-embedding-3-small) y [GPT-4o mini](https://developers.openai.com/api/docs/models/gpt-4o-mini).
- Fragmentos de hasta 1.000 caracteres con 150 caracteres de solapamiento, preservando índice y texto original para citas.
- Recuperar como máximo cinco fragmentos; empezar con similitud coseno mínima de 0,45, que deberá revisarse con el conjunto de evaluación.
- Pregunta máxima: 1.000 caracteres. Respuesta máxima: 500 tokens.
- Las citas muestran nombre del documento y fragmento textual recuperado; no se inventan números de página.
- Los documentos nuevos se intentan indexar al cargarlos solo si existe configuración de OpenAI. Los documentos previos a Hito 7 no se envían durante la migración: una persona de la organización inicia explícitamente su indexación.
- Sin cuotas por persona u organización en este hito; los límites por petición reducen el coste máximo de una operación, pero no sustituyen controles de uso ni gasto.
- PostgreSQL usará la imagen `pgvector/pgvector:pg16` en Compose y CI. No se incorpora un servidor de base de datos adicional.

## Evaluación reproducible

El conjunto ficticio está en `backend/tests/fixtures/rag_evaluation.json` y se ejecuta como parte de `pytest`. Para que el resultado no dependa de internet, claves ni cambios en un modelo, la prueba sustituye el proveedor por vectores sintéticos y respuestas controladas, pero usa PostgreSQL/pgvector y las rutas reales de carga, recuperación y citas.

Resultado observado: 2 de 2 preguntas con evidencia recuperaron el documento y fragmento esperados; 2 de 2 respuestas citaron ese fragmento; 1 de 1 pregunta sin evidencia produjo abstención. El caso adversarial incluye instrucciones dentro del documento y comprueba que el backend las envía como evidencia de usuario, separadas de las instrucciones de sistema. Estos resultados comprueban el flujo y sus límites, no la calidad estadística de OpenAI ni la inmunidad absoluta a prompt injection. No se hicieron llamadas reales al proveedor.

## Seguridad y privacidad

- El backend deriva organización, usuario y acceso desde la sesión, nunca desde IDs del formulario.
- Filtrar por organización en la consulta de recuperación antes de construir el contexto enviado al generador.
- Las citas se validan contra documentos accesibles y no se aceptan rutas/URLs inventadas por el modelo.
- Los documentos pueden contener instrucciones maliciosas: el texto recuperado es evidencia no confiable, no instrucciones de sistema.
- La decisión de enviar documentos indexados, preguntas y contexto a OpenAI está acordada y documentada en ADR 0005; no se deben usar datos sensibles.
- No registrar texto, preguntas, respuestas, tokens ni secretos en logs ordinarios.
- Una respuesta generada no constituye garantía de exactitud; las citas deben apoyar el contenido y la interfaz debe mostrar límites y abstenciones.

## Criterios de aceptación iniciales

- [x] Proveedor, modelo, tratamiento de datos y límites se acuerdan antes de añadir integración.
- [x] Fragmentos, embeddings y citas mantienen relación comprobable con documento, organización y posición.
- [x] Las consultas filtran por organización autenticada; las pruebas verifican que no se devuelva evidencia de otro tenant.
- [x] Respuestas incluyen citas recuperables y se abstienen cuando no hay evidencia pertinente.
- [x] El texto de documentos se trata como dato no confiable, separado de las instrucciones del sistema; no se habilitan herramientas externas.
- [x] Pruebas reproducibles cubren recuperación, citas, abstención, permisos y documentos adversariales.
- [x] La evaluación registra resultados sintéticos observados y aclara que no son una garantía de producción.

## Referencias

- [Hito 6 — extracción y búsqueda](hito-06.md)
- [Arquitectura](architecture.md)
- [Hoja de ruta](roadmap.md)
- [Resultados de las pruebas](testing.md)
