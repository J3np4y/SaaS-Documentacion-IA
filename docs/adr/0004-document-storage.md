# ADR 0004: almacenamiento y carga de documentos

- Estado: aceptada para el Hito 5
- Fecha: 2026-10-09

## Resumen sencillo

La primera versión acepta PDF, DOCX y TXT de hasta 10 MiB por archivo. Guarda los bytes en un directorio local privado configurable y sus datos descriptivos en PostgreSQL. Cualquier integrante autenticado puede gestionar documentos de su organización. El borrado es definitivo; no habrá cuotas ni análisis antimalware en este hito.

## Contexto

El esquema actual contiene metadatos de `Document` ligados a una organización, pero todavía no hay flujo de carga, almacenamiento de bytes ni endpoints de gestión. La hoja de ruta propone añadir subida, validación, almacenamiento y gestión antes de extracción de contenido o búsqueda.

Un archivo es entrada no confiable y puede consumir almacenamiento, memoria y conexiones. Además, una escritura a PostgreSQL y otra a almacenamiento no comparten necesariamente una única transacción. El diseño debe incluir autorización por tenant, límites, errores parciales y limpieza.

## Invariantes

- Guardar metadatos en PostgreSQL y mantener bytes fuera de las tablas de negocio.
- Mantener el almacenamiento privado; solo el backend autorizado accede a los bytes.
- Derivar organización/rol de la sesión del servidor, nunca del formulario.
- Generar claves de almacenamiento opacas en el servidor y no construir rutas con el nombre del usuario.
- Validar tamaño y contenido; no confiar exclusivamente en extensión o `Content-Type` del cliente.
- No exponer rutas internas, URLs públicas duraderas ni secretos en respuestas/logs.
- Diseñar pruebas de fallo y compensación para coordinar persistencia relacional y binaria.

Estas reglas delimitan el prototipo educativo local; no son una aprobación para producción ni para procesar documentos sensibles.

## Decisiones

- Formatos iniciales: PDF, DOCX y TXT; validar extensión y estructura/contenido, no confiar en el MIME del navegador.
- Límite: 10 MiB por archivo y una carga por solicitud; el cuerpo multipart puede añadir como máximo 64 KiB para sus cabeceras.
- Almacenamiento inicial: directorio local privado configurable con `DOCUMENT_STORAGE_DIR`; no se incorpora proveedor cloud ni adaptador multiproveedor.
- Permisos: `owner` y `member` pueden cargar, listar, descargar y borrar dentro de su organización.
- Borrado físico definitivo; no hay recuperación ni cuotas totales por organización en este hito.
- Sin análisis antimalware. No aceptar documentos sensibles ni desplegar públicamente esta versión.
- Política de descargas y encabezados para tipos activos; no servir HTML/HTML embebido del usuario desde el mismo origen de la aplicación.

## Alternativas a evaluar

- **Directorio privado local:** simple para aprender y probar; requiere rutas seguras, permisos del sistema operativo, respaldo y una historia distinta al desplegar múltiples instancias.
- **Almacenamiento de objetos compatible con S3:** apropiado para despliegues y escalado horizontal; añade configuración, coste/credenciales y elección de proveedor. Puede requerir URLs firmadas de vida corta o proxy del backend.
- **Binarios en PostgreSQL:** descartado para el alcance actual; contradice el límite arquitectónico existente y mezcla grandes objetos con metadatos/transacciones de aplicación.
- **URL pública permanente:** descartada como valor por defecto por el riesgo de exposición y falta de autorización por tenant.

No se selecciona un proveedor cloud ni se añade una dependencia. El directorio local privado es suficiente para el alcance educativo acordado.

## Consecuencias y aprendizaje

Durante el hito, explicar cómo cada control reduce una amenaza y demostrarlo con pruebas de tamaño, tipo, acceso entre tenants, fallos de escritura, descarga y borrado.

La aceptación de esta ADR no implicará que la subida de archivos sea segura para producción: despliegue, copias de seguridad, cuotas, análisis de malware, retención y respuesta a incidentes requerirán evaluación propia.
