# Guía de aprendizaje

Este repositorio está pensado para aprender a construir una aplicación web paso a paso. No hace falta conocer todo el stack antes de empezar. La idea es entender un problema pequeño, ver qué decisión lo resuelve y comprobar el resultado antes de seguir.

## Por dónde empezar

1. Lee la introducción y las instrucciones para arrancar en el [README](../README.md).
2. Revisa la [hoja de ruta](roadmap.md) para saber qué partes están terminadas y cuáles son propuestas.
3. Elige el hito que quieras estudiar. Si estás empezando, sigue el orden disponible: [Hito 2](hito-02.md), [Hito 3](hito-03.md), [Hito 4](hito-04.md), [Hito 5](hito-05.md) y [Hito 6](hito-06.md).
4. Consulta la [arquitectura](architecture.md) cuando quieras ver cómo se conectan las partes y la [estrategia de pruebas](testing.md) para distinguir las comprobaciones previstas de las que ya se ejecutaron.

El Hito 1 figura como completado en la hoja de ruta, pero no tiene un documento propio; su contexto inicial está en el README y en el [ADR 0001](adr/0001-base-tecnica.md).

Los hitos anteriores al actual sirven como material de estudio: no es necesario volver a implementar lo que ya está completado. El Hito 6 ya está completado; los hitos posteriores de la hoja de ruta todavía no tienen una especificación propia.

## Un ciclo corto para cada paso

Trabaja en una sola fase cada vez:

1. **Entiende el problema.** Explícalo con tus propias palabras antes de abrir el editor.
2. **Aprende solo los conceptos necesarios.** Anota los términos nuevos y busca entender para qué sirven en este paso.
3. **Lee la decisión relacionada.** En un ADR (registro de decisiones de arquitectura) encontrarás qué se eligió, por qué y qué alternativas se consideraron.
4. **Haz un cambio pequeño.** Sigue el alcance del hito; deja las mejoras futuras para su fase.
5. **Ejecuta la comprobación indicada.** Mira tanto el resultado correcto como el fallo que se espera evitar.
6. **Resume lo aprendido.** Explica qué cambió, qué regla protege y qué limitación sigue pendiente.

Si una decisión de producto todavía está abierta, detente antes de convertir una alternativa en requisito. Es mejor dejar la pregunta visible que añadir complejidad por suposición.

## Vocabulario mínimo

| Término | En palabras sencillas |
|---|---|
| Frontend | La parte de la aplicación con la que interactúa una persona en el navegador. |
| Backend o API | La parte que recibe solicitudes, aplica reglas y devuelve respuestas. |
| Base de datos | El sistema que conserva información estructurada aunque se reinicie la aplicación. |
| Migración | Un cambio versionado en la estructura de la base de datos, que permite actualizarla de forma controlada. |
| Autenticación | Comprobar quién está usando la aplicación. |
| Autorización | Comprobar qué acciones puede realizar esa persona. |
| Organización o tenant | El grupo que delimita los datos que comparten sus integrantes. |
| Almacenamiento de objetos | Un lugar para guardar archivos; no es lo mismo que guardar sus datos descriptivos en la base de datos. |

Los hitos explican los términos cuando se vuelven necesarios. Esta lista es solo una primera orientación, no hace falta memorizarla.

## Cómo leer la documentación

- **README:** qué es el proyecto, su estado y cómo ejecutarlo localmente.
- **Hitos:** qué problema se aborda, qué se aprende, qué incluye y cómo se comprueba. Las secciones técnicas detalladas quedan como referencia; no hace falta dominarlas todas en la primera lectura.
- **ADR:** por qué se tomó una decisión técnica. Un ADR aceptado describe una decisión vigente para su alcance; una propuesta o pregunta pendiente no autoriza una implementación.
- **Arquitectura:** cómo se conectan hoy los componentes y cómo podría evolucionar el sistema. Los diagramas de partes planificadas no significan que ya estén implementadas.
- **Pruebas:** qué se comprobó y con qué resultado. Una prueba prevista no equivale a una prueba ejecutada.
- **Hoja de ruta:** índice del progreso y de los siguientes hitos, no sustituto de las explicaciones ni del registro detallado de pruebas.

El proyecto es educativo y no está listo para producción. Las advertencias de seguridad y las limitaciones de cada hito siguen siendo importantes aunque las pruebas pasen.
