# ADR 0004: almacenamiento y carga de documentos

- Estado: propuesta; requiere decisiones de producto antes de implementar
- Fecha: 2026-10-07

## Resumen sencillo

Todavía no se ha decidido dónde ni cómo guardar los archivos. La propuesta separa los datos que describen un archivo de su contenido, y exige que el servidor compruebe quién puede acceder. Las preguntas pendientes deben responderse antes de programar la subida; las alternativas de abajo sirven para comparar, no son decisiones aprobadas.

## Contexto

El esquema actual contiene metadatos de `Document` ligados a una organización, pero todavía no hay flujo de carga, almacenamiento de bytes ni endpoints de gestión. La hoja de ruta propone añadir subida, validación, almacenamiento y gestión antes de extracción de contenido o búsqueda.

Un archivo es entrada no confiable y puede consumir almacenamiento, memoria y conexiones. Además, una escritura a PostgreSQL y otra a almacenamiento no comparten necesariamente una única transacción. El diseño debe incluir autorización por tenant, límites, errores parciales y limpieza.

## Invariantes propuestas

- Guardar metadatos en PostgreSQL y mantener bytes fuera de las tablas de negocio.
- Mantener el almacenamiento privado; solo el backend autorizado accede a los bytes.
- Derivar organización/rol de la sesión del servidor, nunca del formulario.
- Generar claves de almacenamiento opacas en el servidor y no construir rutas con el nombre del usuario.
- Validar tamaño y contenido; no confiar exclusivamente en extensión o `Content-Type` del cliente.
- No exponer rutas internas, URLs públicas duraderas ni secretos en respuestas/logs.
- Diseñar pruebas de fallo y compensación para coordinar persistencia relacional y binaria.

Estas invariantes son una propuesta de diseño basada en la arquitectura existente, no una aprobación para aceptar archivos hasta fijar los límites y controles.

## Decisiones pendientes

- Formatos permitidos inicialmente y método de detección/verificación.
- Tamaño máximo por archivo, archivos por petición y cuotas de almacenamiento.
- Implementación inicial: directorio local privado, almacenamiento compatible con S3 u otra opción; entorno objetivo.
- Permisos de `owner` y `member` para cargar, listar, descargar y eliminar.
- Borrado físico o lógico, retención, recuperación y comportamiento al retirar usuarios/organizaciones.
- Análisis antimalware: integrado, provisto por el entorno o diferido con limitación explícita.
- Política de descargas y encabezados para tipos activos; no servir HTML/HTML embebido del usuario desde el mismo origen de la aplicación.

La persona responsable debe cerrar estas decisiones en `docs/hito-05.md` antes de cambiar el estado de esta ADR a aceptada.

## Alternativas a evaluar

- **Directorio privado local:** simple para aprender y probar; requiere rutas seguras, permisos del sistema operativo, respaldo y una historia distinta al desplegar múltiples instancias.
- **Almacenamiento de objetos compatible con S3:** apropiado para despliegues y escalado horizontal; añade configuración, coste/credenciales y elección de proveedor. Puede requerir URLs firmadas de vida corta o proxy del backend.
- **Binarios en PostgreSQL:** descartado para el alcance actual; contradice el límite arquitectónico existente y mezcla grandes objetos con metadatos/transacciones de aplicación.
- **URL pública permanente:** descartada como valor por defecto por el riesgo de exposición y falta de autorización por tenant.

No se selecciona aún proveedor ni se añade una dependencia. La interfaz de almacenamiento debe ser la mínima que el caso de uso aprobado requiera; no abstraer por anticipado múltiples proveedores.

## Consecuencias y aprendizaje

Antes de implementar, actualizar esta ADR con decisión y consecuencias, y completar las preguntas de `hito-05.md`. Durante el hito, explicar cómo cada control reduce una amenaza y demostrarlo con pruebas de tamaño, tipo, acceso entre tenants, fallos de escritura, descarga y borrado.

La aceptación de esta ADR no implicará que la subida de archivos sea segura para producción: despliegue, copias de seguridad, cuotas, análisis de malware, retención y respuesta a incidentes requerirán evaluación propia.
