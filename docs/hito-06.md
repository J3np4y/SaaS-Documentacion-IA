# Hito 6 — extracción de contenido, ingesta y búsqueda textual

## Estado: completado; verificaciones locales y CI aprobadas

El Hito 5 permite guardar PDF, DOCX y TXT. Este hito añade el primer paso para encontrar información dentro de esos archivos: extraer su texto y ofrecer una búsqueda limitada a la organización de la persona autenticada. Las respuestas generadas por IA y RAG no forman parte de este hito.

## Objetivo de aprendizaje

Entender que aceptar y guardar un archivo no significa que la aplicación pueda comprenderlo. Aprender a extraer texto de formatos distintos, guardar el resultado de forma coherente con los metadatos y consultar solo la información autorizada.

## Recorrido recomendado

1. **Seguir el documento:** identificar cuándo una carga está recibida, cuándo se procesa y cómo se comunica un error.
2. **Extraer texto:** observar que PDF, DOCX y TXT tienen estructuras distintas; conservar el original y tratar el texto extraído como dato no confiable.
3. **Persistir el resultado:** relacionar el texto con el documento y comprender qué ocurre al borrar o volver a procesar el original.
4. **Buscar con aislamiento:** devolver resultados relevantes solo para la organización actual, sin confiar en identificadores enviados por el cliente.
5. **Comprobar límites:** probar archivos sin texto, corruptos, grandes, con codificaciones distintas y búsquedas vacías o entre organizaciones.

## Alcance implementado

- Extraer texto de PDF, DOCX y TXT ya admitidos por el Hito 5.
- Conservar los bytes originales y hacer que el procesamiento pueda fallar sin perder el documento cargado.
- Guardar el texto extraído asociado al documento y permitir su reprocesamiento.
- Añadir búsqueda textual autenticada, restringida en el servidor a la organización de la sesión.
- Mostrar en la interfaz el resultado de procesamiento y los resultados de búsqueda.
- Registrar en pruebas qué sucede ante archivos vacíos, dañados, sin texto extraíble y ante errores de extracción o base de datos.

## Cómo recorrer la implementación

Sigue una carga desde `POST /organizations/me/documents`: el servidor valida y guarda primero los bytes originales, registra los metadatos y después intenta extraer texto. El estado de extracción permite distinguir un documento recibido de uno cuyo texto se puede buscar. Si el análisis falla, la carga no se convierte en un error silencioso ni se pierde el original; la persona puede descargarlo e intentar extraerlo otra vez.

La búsqueda se solicita a `GET /organizations/me/documents/search?q=...`. El navegador no decide la organización que se consulta: el backend obtiene la membresía desde la sesión y filtra resultados en PostgreSQL. Al leer el código, localiza por separado el almacenamiento binario, el servicio de extracción, la consulta de búsqueda y el endpoint; cada capa tiene una responsabilidad distinta.

## Fuera de alcance

- OCR de documentos escaneados o imágenes.
- Embeddings, búsqueda semántica, pgvector, RAG o respuestas generadas por IA.
- Proveedores externos de extracción, almacenamiento o modelos.
- Exponer contenido extraído o archivos mediante enlaces públicos.

## Decisión acordada: momento del procesamiento

**Decisión acordada:** extraer el texto durante la carga. Para este hito educativo se prefiere un flujo directo y fácil de seguir; una solicitud podrá tardar más mientras se procesa el documento.

No se añadirá un trabajador en segundo plano en esta fase. La interfaz y la API deben comunicar de forma explícita si la extracción termina o falla, sin perder el documento original.

## Decisiones acordadas: texto y búsqueda

- El texto extraído se guarda en PostgreSQL asociado al documento; los bytes originales siguen en el almacenamiento privado.
- La búsqueda utiliza la búsqueda de texto completo integrada en PostgreSQL, con configuración lingüística española y resultados ordenados por relevancia. No se añade un servicio de búsqueda externo.
- Se limita el texto extraído a 100 000 caracteres y los PDF a 1 000 páginas para acotar recursos en el flujo síncrono. Si se supera un límite o no se extrae texto, el original queda guardado con estado de extracción fallida.
- Se añade `pypdf` para leer PDF. TXT se decodifica como UTF-8 y DOCX se lee con las bibliotecas estándar de Python.
- Los documentos que ya existían al aplicar la migración quedan pendientes de extracción; se pueden procesar de nuevo desde la interfaz.

## Criterios de aceptación iniciales

- [x] La estrategia de procesamiento, extracción, persistencia y búsqueda queda documentada antes de codificarla.
- [x] El resultado extraído nunca sustituye ni expone el archivo original.
- [x] El backend aplica aislamiento por organización en la búsqueda y en la lectura del contenido.
- [x] Un fallo de extracción se representa explícitamente y no se confunde con un documento listo para buscar.
- [x] Se prueban formatos admitidos, entradas vacías/corruptas, límites, errores y acceso entre organizaciones.
- [x] La UI presenta estados y errores comprensibles sin filtrar detalles internos.
- [x] CI valida backend y frontend; `docs/testing.md` registra los resultados observados.

## Comprobación y resultado

La suite backend aprobó 61 pruebas contra PostgreSQL desechable. Incluye extracción PDF/DOCX/TXT, archivos vacíos y dañados, límites, reintento, conservación del original, aislamiento por organización y búsqueda textual española. Ruff aprobó y el ciclo de migraciones `upgrade head` → `downgrade base` → `upgrade head` se verificó en PostgreSQL.

El frontend aprobó 22 pruebas, lint, comprobación de tipos y build de producción. GitHub Actions aprobó los jobs de backend y frontend en la [ejecución 37934434186](https://github.com/J3np4y/SaaS-Documentacion-IA/actions/runs/37934434186). El detalle y las limitaciones de esta verificación están en [testing.md](testing.md).

## Referencias

- [Hito 5 — carga y gestión](hito-05.md)
- [ADR 0004 — almacenamiento de documentos](adr/0004-document-storage.md)
- [Arquitectura](architecture.md)
- [Hoja de ruta](roadmap.md)
- [Resultados de las pruebas](testing.md)
