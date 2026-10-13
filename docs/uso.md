# Uso del flujo

## Trabajar con el agente

Abre el clon como workspace, conecta Palmier y usa estos pedidos:

| Pedido | Resultado |
| --- | --- |
| «Crea un proyecto de video» | ID permanente, carpetas, documentos y proyecto Palmier. La idea puede llegar después. |
| «La idea de V0001 es…» | Brief, estructura, guía de grabación, materiales necesarios, importancia y fecha propuestas. |
| «Ya está el crudo; prepara V0001» | Inspección de archivos/audio, importación y registro del original. |
| «Haz el montaje base» | Original con cortes sin pérdida y versión `Ideas completas`, mediante `yt-cut-hi`. |
| «Edita los apoyos y la emoción» | Versión de edición con apoyos, énfasis selectivo y notas actualizadas. |
| «Haz una versión más dinámica (v2, v3)» | Copia del corte con encuadre completo, capítulos, zooms, subtítulos animados y efectos de sonido, mediante `yt-edit-dinamica`. Nunca toca el corte revisado; el usuario decide cuál queda vigente. |
| «Añade zooms / subtítulos animados / efectos / capítulos» | Solo esa parte, con su skill: `yt-edit-zooms`, `yt-edit-subtitulos`, `yt-edit-sfx` o `yt-edit-capitulos`. Música, efectos temáticos y máscaras mágicas necesitan material o autorización de gasto. |
| «Revisa el video» | Comprobaciones estructurales y audiovisuales según lo que pueda revisarse realmente. |
| «Exporta el video» | Archivo versionado, espera del resultado y comprobación del entregable. |
| «Lo programé para el día… a las…» | Registro de programación real y actualización del calendario. |
| «Lo publiqué; este es el enlace…» | Fecha, URL y etapa de publicación registradas. |
| «Archiva el proyecto» | Respaldo autocontenido de Palmier comprobado; fuentes conservadas. |

Al retomar un episodio, menciona su ID. Cambiar el título no cambia `V0001` ni sus rutas.

Para incorporar un proyecto antiguo:

```text
Adopta el proyecto de Palmier que tengo abierto. Reutiliza mis notas y conserva las fuentes donde están.
```

El agente identifica proyecto/timelines reales y no vuelve a montar lo que ya existe.

## Colocar y seguir recursos

Guarda grabaciones nuevas en `videos/V0001/crudo/` y apoyos en sus carpetas de `assets/`. Las fuentes antiguas también pueden conservarse en otras ubicaciones estables.

| Estado | Qué sabemos |
| --- | --- |
| Falta obtenerlo | No hay una fuente confirmada. |
| Lo tenemos, no importado | Archivo localizado y contenido inspeccionado. |
| Ya importado | Disponible en Palmier con referencia real. |
| Ya en el video | Colocación comprobada en el timeline registrado. |

Un recurso disponible no implica que la tarea editorial esté terminada. `notas.md` conserva propósito, frase, frames, recurso, prioridad y decisión. Las inserciones **por encima** mantienen narración/duración; **en medio** añaden un segmento y desplazan contenido sincronizado.

Después de cortes, se actualizan anclajes por frase y fuente. La firma del timeline identifica si notas, revisión y exportación pertenecen al mismo corte; no reemplaza la reproducción audiovisual.

## Calendario y publicación

`estado.json` es la fuente de verdad. `calendario.md` y los bloques marcados en Markdown se generan desde esos registros. Edita las propuestas y notas fuera de los bloques; actualiza datos operativos con el helper o pide al agente que lo haga.

- **Propuesta:** reserva tentativa de un día, desde mañana o una fecha posterior.
- **Confirmada:** fecha que elegiste para el episodio.
- **Programada:** fecha/hora real informada desde YouTube.
- **Publicada:** fecha/hora y enlace reales.

El calendario considera el día en `America/Mexico_City`. Propone otra fecha si un video ya la ocupa; no mueve reservas ajenas. Si realmente programaste dos videos el mismo día, registra ambos y señala el conflicto.

Las actualizaciones ocurren al trabajar con el agente o ejecutar comandos. No hay vigilancia en segundo plano ni conexión automática a YouTube.

`publicacion.md` reúne cinco títulos, tres composiciones de miniatura y descripción. La miniatura la haces tú. El archivo final, título elegido y revisión de descripción se registran cuando estén decididos. Exportar puede terminar antes de la miniatura; listo para publicar exige además revisión del corte, apoyos imprescindibles, archivo verificado y fecha confirmada.

## Uso manual del helper

Estos comandos organizan el registro local; **no crean por sí solos proyectos nativos de Palmier**:

```bash
python3 skills/yt-video-flow/scripts/video_flow.py init --name 'Rescate de un TH9'
python3 skills/yt-video-flow/scripts/video_flow.py begin V0001 definicion
python3 skills/yt-video-flow/scripts/video_flow.py update V0001 --patch-file examples/definir-video.json --nota 'Idea y guía de grabación definidas' --resultado completada
python3 skills/yt-video-flow/scripts/video_flow.py suggest-date V0001
python3 skills/yt-video-flow/scripts/video_flow.py check V0001
```

Adapta el ejemplo antes de usarlo en un episodio real. Los objetos del parche se fusionan; las listas se reemplazan completas. No edites identidad ni historial.

Al programar el episodio tú mismo en YouTube, puedes adaptar el ejemplo:

```bash
python3 skills/yt-video-flow/scripts/video_flow.py update V0001 --patch-file examples/registrar-programacion.json --nota 'Programación real informada por el usuario'
```

La hora requiere offset; el ejemplo **no programa el video**. Para completar la publicación necesitas también su URL. Para más comandos (`bind`, `adopt`, `snapshot`) y campos, consulta la [referencia del helper](../skills/yt-video-flow/references/helper.md).

## Respaldo y actualización del repositorio

Los documentos de los episodios, calendario y medios están ignorados por Git. Respáldalos por separado; clonar el repositorio en otra computadora solo instala el flujo. Un archivo autocontenido de Palmier respalda el proyecto nativo y sus medios disponibles; no incluye necesariamente todos los Markdown externos.

Para actualizar herramientas, revisa cambios propios en archivos versionados y usa `git pull --ff-only` cuando tengas un remoto y la rama local esté lista para avanzar. El `.gitignore` mantiene los episodios locales fuera del código distribuido. No uses limpiezas de archivos ignorados para actualizar.
