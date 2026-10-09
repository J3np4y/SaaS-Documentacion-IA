# Hito 8 — observabilidad, control de coste y contenedores

## Estado: implementación local completada; CI pendiente

En el Hito 7 se añadieron preguntas con RAG y llamadas a OpenAI. Ahora necesitamos limitar el uso acumulado para que las repeticiones no sean ilimitadas, ver si los servicios responden y preparar una ejecución reproducible en contenedores sin publicar la aplicación.

## Objetivo de aprendizaje

Aprender tres ideas operativas:

- **Cuota:** limitar cuántas operaciones puede iniciar cada organización durante un periodo.
- **Observabilidad:** recoger señales técnicas útiles sin guardar documentos, preguntas, secretos ni datos personales en telemetría.
- **Contenedor:** empaquetar cada servicio y describir cómo se conecta con los demás, manteniendo datos y secretos fuera de las imágenes.

Una cuota de operaciones reduce el abuso repetido, pero no es un presupuesto en euros: indexar un documento grande puede costar más que formular una pregunta.

## Alcance acordado

- Límite inicial configurable por organización: 20 operaciones RAG por día UTC y 200 por mes UTC. Una operación es una pregunta, una indexación explícita o un intento de indexación automática.
- La reserva se guarda atómicamente antes de llamar a OpenAI. Se cuentan también los fallos del proveedor. Al alcanzar el límite, preguntar o indexar responde HTTP 429 sin enviar contenido al proveedor.
- Si una carga automática alcanza el límite, el archivo y el texto extraído se conservan y la indexación queda pendiente para reintentar más adelante.
- Mantener los topes por pregunta, respuesta y extracción del Hito 7; permitir como máximo 150 fragmentos en una operación de indexación y detener excesos antes de llamar a OpenAI.
- Exportar métricas Prometheus básicas de método, plantilla de ruta, estado y latencia, sin etiquetas por usuario, organización, documento ni texto. Los agregados viven en memoria y se reinician al reiniciar el proceso.
- Registrar eventos JSON resumidos de las peticiones sin URL completa, query string, cuerpos, cookies, emails, IDs ni contenido.
- Añadir imágenes separadas para frontend y API y una configuración Compose de ejecución. PostgreSQL y documentos deben persistir en volúmenes; la API y la base de datos no se publican en puertos del host.
- Entregar una guía de ejecución y traslado a un entorno HTTPS, pero no desplegar la aplicación ni integrar un servicio externo de observabilidad.

## No incluido

- Presupuesto monetario exacto, facturación o lectura de costes desde la cuenta de OpenAI.
- Métricas históricas compartidas entre varias réplicas, alertas administradas o integración de terceros.
- Despliegue público, TLS administrado, alta disponibilidad, copias de seguridad automatizadas o restauración verificada.
- Completar las medidas pendientes de identidad (verificación de correo, recuperación de cuenta y protección distribuida frente a abuso). El prototipo no queda listo para producción.

## Cómo comprobarlo

- Probar límites exactos diario y mensual, reinicio en UTC, fallos del proveedor, separación por organización y solicitudes concurrentes.
- Confirmar que una carga no desaparece al superar la cuota y que no se llama a OpenAI después del rechazo.
- Revisar que los logs y `/metrics` solo usan rutas plantilla y etiquetas de baja cardinalidad, sin información personal o contenido.
- Construir las imágenes, aplicar migraciones explícitamente, iniciar los contenedores, consultar salud y comprobar que los volúmenes retienen datos.
- Ejecutar pruebas backend/frontend y CI. Registrar resultados observados en [testing.md](testing.md), sin llamar a OpenAI.

## Decisión técnica

Las elecciones de periodos, contabilidad atómica, límites, telemetría, contenedores y sus consecuencias se describen en [ADR 0006](adr/0006-observability-cost-control-and-containers.md).

## Ejecutar el stack en contenedores

Esta configuración es para una prueba local. No publica la aplicación en Internet ni la convierte en un servicio listo para producción.

1. Desde la raíz, crea `.env` copiando `.env.example` y cambia `POSTGRES_PASSWORD` por una contraseña local. No guardes `.env` ni copias de seguridad en Git. Si quieres probar RAG con OpenAI, añade una clave propia a `OPENAI_API_KEY`; las pruebas descritas abajo no la necesitan.
2. Inicia PostgreSQL y espera a que esté saludable:

   ```powershell
   docker compose --env-file .env -f docker-compose.deploy.yml up -d db
   docker compose --env-file .env -f docker-compose.deploy.yml ps
   ```

3. Aplica las migraciones explícitamente. La API no modifica el esquema al arrancar:

   ```powershell
   docker compose --env-file .env -f docker-compose.deploy.yml run --rm api alembic upgrade head
   ```

4. Construye e inicia frontend y API:

   ```powershell
   docker compose --env-file .env -f docker-compose.deploy.yml up --build -d
   docker compose --env-file .env -f docker-compose.deploy.yml ps
   ```

   Solo el frontend se publica, ligado por defecto a `127.0.0.1:3000`. La API y PostgreSQL permanecen en la red privada de Compose. El frontend consulta la API por el nombre interno `api`; la API encuentra PostgreSQL como `db`.

5. Abre `http://localhost:3000`. Para comprobar preparación y métricas desde la red interna:

   ```powershell
   docker compose --env-file .env -f docker-compose.deploy.yml exec api python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/ready').read().decode())"
   docker compose --env-file .env -f docker-compose.deploy.yml exec api python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/metrics').read().decode())"
   docker compose --env-file .env -f docker-compose.deploy.yml logs --no-color api
   ```

   `/metrics` no está publicado en el host. Los logs de aplicación son resúmenes JSON; no incluyen documentos, preguntas, cookies, identidad ni query strings. Las métricas viven en memoria y se reinician al reiniciar la API.

### Límites, datos y mantenimiento

- Los límites iniciales son 20 operaciones RAG diarias y 200 mensuales por organización; configura `RAG_DAILY_OPERATION_LIMIT` y `RAG_MONTHLY_OPERATION_LIMIT` en `.env` si necesitas otros valores positivos. Son operaciones, no una cantidad de dinero.
- PostgreSQL y los documentos usan volúmenes de Docker. Estos volúmenes sobreviven al reinicio de contenedores, pero **no son copias de seguridad**. Los documentos permanecen hasta que una persona autorizada los borra; los contadores de periodos antiguos se eliminan oportunistamente al reservar una cuota.
- Una copia de seguridad de PostgreSQL puede generarse fuera del repositorio con:

   ```powershell
   docker compose --env-file .env -f docker-compose.deploy.yml exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup.sql
   ```

   Este volcado contiene datos de la aplicación. Guárdalo cifrado y con acceso restringido, define una retención adecuada a tus datos y elimina las copias cuando ya no se necesiten. Este hito no automatiza ni verifica la restauración. El volumen de documentos necesita además su propia copia coordinada y protegida; el volcado SQL no contiene los bytes originales.
- Detén los servicios conservando los volúmenes:

   ```powershell
   docker compose --env-file .env -f docker-compose.deploy.yml down
   ```

   No añadas `--volumes` si quieres conservar los datos.
- Para trasladar el prototipo detrás de HTTPS hay que configurar el dominio y `FRONTEND_ORIGIN`, publicar el frontend solo detrás del proxy TLS, activar `SESSION_COOKIE_SECURE=true` y revisar secretos, backups, retención de logs, restauración y monitorización. No cambies `WEB_BIND_ADDRESS` para exponer el puerto directamente a Internet. La guía no sustituye una revisión de seguridad ni un despliegue real.

## Referencias

- [Hito 7 — RAG, citas y evaluación](hito-07.md)
- [Arquitectura](architecture.md)
- [Hoja de ruta](roadmap.md)
- [Resultados de las pruebas](testing.md)
