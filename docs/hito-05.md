# Hito 5 — carga y gestión de documentos

## Estado: en desarrollo; decisiones de alcance acordadas

El Hito 4 ya proporciona identidad, sesión y aislamiento por organización. El modelo existente conserva metadatos básicos de `Document`; este hito añade el primer recorrido de carga y gestión sin anticipar extracción, búsqueda ni IA.

## Objetivo de aprendizaje

Aprender a recibir contenido binario no confiable de forma segura, distinguir los metadatos de los bytes, persistirlos en sistemas adecuados y hacer cumplir autorización y aislamiento de tenant en cada operación.

Cada fase explica qué amenaza o problema resuelve, qué regla se implementa y qué prueba demuestra el comportamiento. No generar una gran implementación de subida antes de decidir tipos, límites, acceso y ciclo de vida.

## Recorrido recomendado para empezar

Las decisiones de alcance iniciales ya están acordadas. Para aprender el tema sin abordar todos los detalles a la vez, sigue este orden:

1. **Separar descripción y contenido:** identifica qué datos sobre un archivo guardaríamos en PostgreSQL y por qué los bytes se guardarían aparte.
2. **Poner límites a la entrada:** acuerda formatos y tamaño máximo; piensa qué podría salir mal si se confía en el nombre o el tipo declarado por el navegador.
3. **Proteger el acceso:** dibuja quién puede cargar, ver, descargar y borrar, y de qué organización proviene el permiso.
4. **Decidir qué pasa ante un fallo:** observa que guardar datos y guardar bytes son dos operaciones distintas; define cómo detectar y recuperar un resultado incompleto.
5. **Solo entonces implementar:** empieza por una operación y su prueba, y añade el resto del recorrido de forma incremental.

No se añade una abstracción para varios proveedores. Consulta [ADR 0004](adr/0004-document-storage.md) para las decisiones aprobadas y sus limitaciones.

## Decisiones de alcance acordadas

- Formatos iniciales: PDF, DOCX y TXT, comprobando el contenido además de la extensión.
- Tamaño máximo: 10 MiB por archivo; una carga usa una solicitud por archivo. El backend limita el tamaño total de la solicitud multipart a 10 MiB más un margen fijo para sus cabeceras.
- Almacenamiento: directorio local privado, fuera de los archivos públicos del frontend. `DOCUMENT_STORAGE_DIR` permite cambiar su ubicación; el valor local predeterminado es `.data/documents/`.
- Permisos: cualquier integrante autenticado (`owner` o `member`) puede cargar, listar, descargar y borrar documentos de su propia organización.
- Borrado: físico y definitivo, sin periodo de recuperación.
- Antimalware: no se incluye en este hito; es una limitación explícita y no habilita el uso con documentos sensibles ni el despliegue público.
- No se implementan cuotas totales por organización en esta primera versión.
- No se implementa eliminación de organizaciones o cuentas; si se añade, debe borrar también sus archivos.

Estas decisiones acotan una primera versión educativa local; no equivalen a aprobar el sistema para producción.

## Alcance previsto

El objetivo funcional propuesto es que una persona autenticada pueda cargar un documento a su organización, consultar los documentos de esa organización, descargar uno autorizado y eliminarlo según una política acordada.

- PostgreSQL guardará metadatos y estado, no el binario.
- Los bytes vivirán en un almacenamiento privado al que solo accede el backend.
- La organización se tomará de la sesión autenticada; nunca se confiará en un `organization_id` del formulario.
- Se validarán tamaño, nombre y contenido antes de aceptar el archivo. La extensión y el `Content-Type` del navegador no se considerarán prueba suficiente del formato.
- Las rutas de descarga y borrado comprobarán pertenencia y permisos en el servidor.
- La UI comunicará carga, aceptación, errores de validación, fallos recuperables y lista vacía sin mostrar rutas internas.

Este alcance implementa las decisiones ya acordadas en este documento; cualquier cambio de formatos, límites, permisos o almacenamiento debe actualizar primero el ADR y este hito.

## Conceptos y fases de aprendizaje

### 1. Definir el contrato del documento

**Aprende:** separar identidad del archivo, metadatos descriptivos, ubicación de almacenamiento y estado del procesamiento futuro.

**Diseña:** campos mínimos para nombre visible, tipo detectado, tamaño, fechas, organización propietaria y referencia opaca al objeto. Revisar el modelo `Document` antes de añadir campos; no almacenar URLs públicas ni rutas arbitrarias.

**Comprueba:** reglas de nulabilidad, longitudes, índices y claves foráneas con migración reversible y pruebas PostgreSQL.

**Decisión:** la UI presenta nombre, tipo detectado, tamaño y fecha de carga; los bytes permanecen fuera de PostgreSQL.

### 2. Validar una entrada no confiable

**Aprende:** los nombres, extensiones y tipos MIME enviados por el navegador son datos controlados por quien sube el archivo. La validación debe limitar recursos antes de reservar almacenamiento.

**Diseña:** límites de bytes leídos, lista de tipos aceptados, detección del tipo basada en el contenido cuando sea viable, nombres Unicode seguros y rechazo de rutas/valores ambiguos. Nunca interpretar el nombre del usuario como una ruta física.

**Comprueba:** límites exactos, archivo vacío, MIME/extensión falsificados, contenido truncado, nombre malformado y payloads rechazados sin persistencia parcial.

**Decisiones:** PDF, DOCX y TXT; hasta 10 MiB; un archivo por solicitud; sin análisis antimalware ni cuotas en esta fase.

### 3. Separar PostgreSQL del almacenamiento binario

**Aprende:** una transacción SQL no suele cubrir una operación en un almacén de objetos o sistema de archivos. Diseñar compensación y estados evita metadatos huérfanos y archivos sin referencia.

**Diseña:** un módulo pequeño de almacenamiento privado, claves aleatorias creadas por backend y un ciclo claro de guardar bytes, confirmar metadatos y compensar fallos. No añadir adaptadores para proveedores que no se hayan elegido.

**Comprueba:** fallo antes/después de guardar, colisión de nombres, lectura/escritura denegada, metadatos fallidos y limpieza/compensación; probar la implementación real elegida además de dobles.

**Decisión:** directorio local privado configurable, sin asumir disponibilidad de un proveedor externo.

### 4. Aplicar permisos y ciclo de vida

**Aprende:** conocer una clave o UUID no equivale a tener permiso; todas las consultas y operaciones de bytes deben estar limitadas al tenant de la sesión.

**Diseña:** endpoints de carga, listado, descarga y eliminación con respuestas que no filtren existencia de documentos de otros tenants. Decidir qué rol puede hacer cada acción y si el borrado es lógico o físico.

**Comprueba:** acceso propio permitido, UUID ajeno denegado, manipulación de organización denegada, roles según matriz, descargas revocadas después de retirar membresía y comportamiento del borrado coherente en base y almacenamiento.

**Decisiones:** `owner` y `member` comparten los permisos; el borrado es físico e irreversible; no hay cuotas por organización en esta fase.

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
- Rechazar tipos no permitidos y comprobar contenido contra el tipo esperado. No hay análisis antimalware; no cargar documentos sensibles ni exponer el prototipo públicamente.
- Servir descargas con autorización, tipo de contenido controlado y `Content-Disposition` seguro; no exponer rutas del host ni credenciales ni URLs internas.
- No registrar contenido, nombres potencialmente sensibles, cookies, tokens ni rutas internas.
- Definir qué ocurre con bytes/metadatos al eliminar una cuenta, una membresía o una organización.
- Tratar los archivos como datos, nunca como instrucciones para un modelo; cualquier futura extracción/RAG requiere controles y citas por separado.

La aplicación continúa siendo un prototipo educativo. Este hito por sí solo no constituye una aprobación para aceptar documentos sensibles ni exponer la carga públicamente.

## Criterios de aceptación propuestos

- [x] Formatos, límites, permisos, estrategia de almacenamiento, retención y política de análisis documentados y aceptados antes de implementar.
- [ ] Migración reversible añade solo metadatos necesarios; ninguna columna almacena el binario.
- [ ] Carga valida el contenido con límites configurados y no deja filas/objetos parciales en los fallos previstos.
- [ ] Los bytes se guardan en almacenamiento privado mediante clave opaca generada por servidor.
- [ ] Listado, descarga y eliminación cumplen autorización de rol y aislamiento por organización en el backend.
- [ ] El ciclo de fallo entre base de datos y almacenamiento tiene compensación o recuperación explícita y pruebas.
- [ ] La UI permite completar el flujo acordado y comunica errores sin filtrar detalles internos.
- [ ] Pruebas backend unitarias/de integración, pruebas de almacenamiento, pruebas frontend, Ruff, lint, typecheck y build pasan; [testing.md](testing.md) registra resultados observados.
- [ ] README/arquitectura describen únicamente capacidades realmente implementadas; no se declara preparación para producción sin revisión de seguridad de cargas.

## Referencias

- [ADR 0004: almacenamiento de documentos](adr/0004-document-storage.md)
- [Arquitectura](architecture.md)
- [Pruebas previstas](testing.md#hito-5--carga-y-gestion-de-documentos-pruebas-previstas)
