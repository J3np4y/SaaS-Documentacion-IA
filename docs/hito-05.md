# Hito 5 — carga y gestión de documentos

## Estado: planificación propuesta; decisiones de alcance pendientes

El Hito 4 ya proporciona identidad, sesión y aislamiento por organización. El modelo existente conserva metadatos básicos de `Document`, pero todavía no recibe ni almacena archivos. Este hito debe construir el primer recorrido completo de documento sin anticipar extracción, búsqueda ni IA.

## Objetivo de aprendizaje

Aprender a recibir contenido binario no confiable de forma segura, distinguir los metadatos de los bytes, persistirlos en sistemas adecuados y hacer cumplir autorización y aislamiento de tenant en cada operación.

Cada fase explica qué amenaza o problema resuelve, qué regla se implementa y qué prueba demuestra el comportamiento. No generar una gran implementación de subida antes de decidir tipos, límites, acceso y ciclo de vida.

## Alcance previsto

El objetivo funcional propuesto es que una persona autenticada pueda cargar un documento a su organización, consultar los documentos de esa organización, descargar uno autorizado y eliminarlo según una política acordada.

- PostgreSQL guardará metadatos y estado, no el binario.
- Los bytes vivirán en un almacenamiento privado al que solo accede el backend.
- La organización se tomará de la sesión autenticada; nunca se confiará en un `organization_id` del formulario.
- Se validarán tamaño, nombre y contenido antes de aceptar el archivo. La extensión y el `Content-Type` del navegador no se considerarán prueba suficiente del formato.
- Las rutas de descarga y borrado comprobarán pertenencia y permisos en el servidor.
- La UI comunicará carga, aceptación, errores de validación, fallos recuperables y lista vacía sin mostrar rutas internas.

Este alcance es una propuesta derivada de la hoja de ruta, no una decisión sobre formatos, cuotas, proveedor de almacenamiento ni permisos concretos.

## Conceptos y fases de aprendizaje

### 1. Definir el contrato del documento

**Aprende:** separar identidad del archivo, metadatos descriptivos, ubicación de almacenamiento y estado del procesamiento futuro.

**Diseña:** campos mínimos para nombre visible, tipo detectado, tamaño, fechas, organización propietaria y referencia opaca al objeto. Revisar el modelo `Document` antes de añadir campos; no almacenar URLs públicas ni rutas arbitrarias.

**Comprueba:** reglas de nulabilidad, longitudes, índices y claves foráneas con migración reversible y pruebas PostgreSQL.

**Decisión pendiente:** formato y campos que necesita presentar la UI.

### 2. Validar una entrada no confiable

**Aprende:** los nombres, extensiones y tipos MIME enviados por el navegador son datos controlados por quien sube el archivo. La validación debe limitar recursos antes de reservar almacenamiento.

**Diseña:** límites de bytes leídos, lista de tipos aceptados, detección del tipo basada en el contenido cuando sea viable, nombres Unicode seguros y rechazo de rutas/valores ambiguos. Nunca interpretar el nombre del usuario como una ruta física.

**Comprueba:** límites exactos, archivo vacío, MIME/extensión falsificados, contenido truncado, nombre malformado y payloads rechazados sin persistencia parcial.

**Decisiones pendientes:** formatos iniciales, tamaño máximo por archivo, número de archivos por petición y si se añade análisis antimalware.

### 3. Separar PostgreSQL del almacenamiento binario

**Aprende:** una transacción SQL no suele cubrir una operación en un almacén de objetos o sistema de archivos. Diseñar compensación y estados evita metadatos huérfanos y archivos sin referencia.

**Diseña:** una interfaz pequeña de almacenamiento privado, claves aleatorias creadas por backend y un ciclo claro de guardar bytes, confirmar metadatos y compensar fallos. Mantener el proveedor intercambiable solo si el segundo destino está justificado.

**Comprueba:** fallo antes/después de guardar, colisión de nombres, lectura/escritura denegada, metadatos fallidos y limpieza/compensación; probar la implementación real elegida además de dobles.

**Decisión pendiente:** almacenamiento local privado para desarrollo, almacenamiento de objetos compatible en un servicio concreto u otra opción. La aplicación no debe suponer disponibilidad de un proveedor que todavía no se haya elegido.

### 4. Aplicar permisos y ciclo de vida

**Aprende:** conocer una clave o UUID no equivale a tener permiso; todas las consultas y operaciones de bytes deben estar limitadas al tenant de la sesión.

**Diseña:** endpoints de carga, listado, descarga y eliminación con respuestas que no filtren existencia de documentos de otros tenants. Decidir qué rol puede hacer cada acción y si el borrado es lógico o físico.

**Comprueba:** acceso propio permitido, UUID ajeno denegado, manipulación de organización denegada, roles según matriz, descargas revocadas después de retirar membresía y comportamiento del borrado coherente en base y almacenamiento.

**Decisiones pendientes:** permisos exactos de `owner` y `member`, retención/recuperación tras borrar y cuotas por usuario u organización.

### 5. Integrar la experiencia de usuario

**Aprende:** la UI guía el flujo, pero sus restricciones no reemplazan la validación del backend.

**Diseña:** selector de archivo, confirmación de subida, lista vacía/con documentos, descarga y eliminación solo cuando se autoricen. Evitar exponer rutas locales, credenciales de almacenamiento o URLs firmadas duraderas.

**Comprueba:** mensajes accesibles, fallos de tamaño/tipo, desconexión, reintento sin duplicados inesperados, estado tras refrescar y acciones no permitidas.

## Fuera de alcance

- Extracción de texto, OCR, conversión de formatos o previsualización avanzada.
- Indexación, búsqueda textual/semántica, embeddings, pgvector, RAG y respuestas generadas.
- Versionado de documentos, colaboración en tiempo real o flujos de aprobación.
- Compartir públicamente archivos o usar enlaces de descarga permanentes.
- Elegir/configurar un proveedor cloud antes de que se decida el entorno de despliegue.

Si el análisis antimalware o cuotas no se implementan, registrar su ausencia como limitación; no representar como seguro un flujo que carezca de los controles aprobados.

## Seguridad y privacidad

- Solo usuarios autenticados pueden cargar/consultar; el backend deriva organización y rol de la sesión.
- No fiarse de nombre, extensión, MIME, tamaño declarado, ruta, UUID ni organización enviados por el cliente.
- Generar claves opacas no adivinables; almacenar objetos fuera de un directorio público; no formar rutas desde entradas del usuario.
- Limitar bytes y tiempo de lectura para reducir abuso de memoria, disco y conexiones.
- Rechazar tipos no permitidos; comprobar contenido contra el tipo esperado y decidir si se requiere escaneo antimalware antes de aceptar documentos reales.
- Servir descargas con autorización, tipo de contenido controlado y `Content-Disposition` seguro; no exponer rutas del host ni credenciales ni URLs internas.
- No registrar contenido, nombres potencialmente sensibles, cookies, tokens ni rutas internas.
- Definir qué ocurre con bytes/metadatos al eliminar una cuenta, una membresía o una organización.
- Tratar los archivos como datos, nunca como instrucciones para un modelo; cualquier futura extracción/RAG requiere controles y citas por separado.

La aplicación continúa siendo un prototipo educativo. Este hito por sí solo no constituye una aprobación para aceptar documentos sensibles ni exponer la carga públicamente.

## Criterios de aceptación propuestos

- [ ] Formatos, límites, permisos, estrategia de almacenamiento, retención y política de análisis documentados y aceptados antes de implementar.
- [ ] Migración reversible añade solo metadatos necesarios; ninguna columna almacena el binario.
- [ ] Carga valida el contenido con límites configurados y no deja filas/objetos parciales en los fallos previstos.
- [ ] Los bytes se guardan en almacenamiento privado mediante clave opaca generada por servidor.
- [ ] Listado, descarga y eliminación cumplen autorización de rol y aislamiento por organización en el backend.
- [ ] El ciclo de fallo entre base de datos y almacenamiento tiene compensación o recuperación explícita y pruebas.
- [ ] La UI permite completar el flujo acordado y comunica errores sin filtrar detalles internos.
- [ ] Pruebas backend unitarias/de integración, pruebas de almacenamiento, pruebas frontend, Ruff, lint, typecheck y build pasan; [testing.md](testing.md) registra resultados observados.
- [ ] README/arquitectura describen únicamente capacidades realmente implementadas; no se declara preparación para producción sin revisión de seguridad de cargas.

## Preguntas que deben resolverse antes de implementar

1. ¿Qué formatos se aceptan primero y cuál es el tamaño máximo por archivo?
2. ¿Qué almacenamiento queremos para la primera versión: disco local privado solo para aprendizaje o un servicio de objetos compatible con S3? Si es un servicio concreto, ¿cuál?
3. ¿Los roles `owner` y `member` pueden ambos cargar, listar, descargar y borrar, o se necesita una matriz distinta?
4. ¿Al borrar un documento se elimina definitivamente o se conserva temporalmente? ¿Se necesita cuota por organización?
5. ¿La primera versión debe incorporar análisis antimalware o solo restringir formatos y documentarlo como limitación local?

## Referencias

- [ADR 0004: almacenamiento de documentos](adr/0004-document-storage.md)
- [Arquitectura](architecture.md)
- [Pruebas previstas](testing.md#hito-5--carga-y-gestion-de-documentos-pruebas-previstas)
