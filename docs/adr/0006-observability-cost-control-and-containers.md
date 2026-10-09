# ADR 0006: observabilidad, control de coste y contenedores

- Estado: aceptada para el Hito 8
- Fecha: 2026-10-09

## Resumen sencillo

Cada organización tendrá un límite diario y otro mensual para operaciones que usan RAG. La API guardará de forma atómica cada intento antes de llamar a OpenAI, para impedir que solicitudes simultáneas superen el límite y para contar también los fallos del proveedor. La aplicación expondrá métricas técnicas generales y logs resumidos, sin registrar documentos, preguntas ni datos de identidad. Añadiremos imágenes de contenedor para preparar un despliegue; no publicaremos la aplicación ni la declararemos lista para producción.

## Decisiones

- Contabilizar una operación por cada pregunta, indexación explícita o intento de indexación automática de un documento nuevo. La operación se reserva antes de contactar con OpenAI; los fallos del proveedor también consumen cuota.
- Límite inicial por organización: 20 operaciones por día UTC y 200 por mes UTC. Configurables con `RAG_DAILY_OPERATION_LIMIT` y `RAG_MONTHLY_OPERATION_LIMIT`.
- Una pregunta o indexación explícita agotada responde HTTP 429 con un mensaje genérico y sin llamar al proveedor. Si se agota la cuota durante una carga, la carga y la extracción se guardan y la indexación permanece pendiente para que pueda reintentarse en el siguiente periodo.
- Conservar los límites de consulta y generación de Hito 7. Añadir un máximo de 150 fragmentos por documento y evitar divisiones de fragmentos menores de 850 caracteres antes del solapamiento. El máximo de extracción existente (100.000 caracteres) mantiene una indexación normal bajo ese tope; cualquier exceso se detecta antes de llamar a OpenAI.
- Guardar contadores diarios y mensuales por organización y periodo UTC. La clave compuesta y el `UPSERT` condicional en PostgreSQL garantizan que operaciones simultáneas no superen la cuota. Rechazar la reserva mensual revierte también el incremento diario.
- Exportar métricas Prometheus de peticiones HTTP y latencia con etiquetas acotadas (método, plantilla de ruta y código HTTP); no etiquetar por usuario, organización, documento ni pregunta. Las métricas son agregados en memoria y se reinician al reiniciar el proceso.
- Escribir un evento JSON por petición con método, plantilla de ruta, estado y latencia. No registrar URL completa, query string, cuerpos, cookies, emails, contenido, IDs ni errores del proveedor.
- No incorporar una plataforma ni servicio externo de telemetría.
- Construir imágenes separadas de API y frontend. PostgreSQL y almacenamiento de archivos persisten mediante volúmenes; el backend no publica puerto en el host en la configuración de contenedores. El proxy Next.js accede a la API por la red privada de Compose.
- La guía será agnóstica a proveedor de nube y solo preparará el traslado; no se hará despliegue público, exposición de métricas ni procesamiento con claves/datos reales.

## Consecuencias y límites

- Contar operaciones hace el control fácil de explicar y probar, pero no equivale a coste monetario: una indexación puede procesar más texto que una pregunta. El tope por documento y los límites por operación reducen el riesgo sin garantizar una factura máxima.
- Los periodos se calculan en UTC. La cuota no se libera por fallos de OpenAI, ya que una petición puede haber incurrido en coste.
- Las métricas en memoria no sustituyen una plataforma histórica ni son compartidas entre varios procesos. El prototipo desplegado con un único proceso mantiene comportamiento coherente; escalar horizontalmente requerirá telemetría y coordinación compartidas.
- Las imágenes y la guía no resuelven por sí solas HTTPS, copias de seguridad verificadas, almacenamiento compartido, recuperación de cuentas, verificación de email ni protección distribuida de autenticación.
- No usar datos sensibles ni exponer el prototipo públicamente hasta completar las medidas pendientes de sus hitos anteriores.
