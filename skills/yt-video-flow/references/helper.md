# Helper y fuente de verdad

Ejecutar desde la raíz de `coc`:

```bash
python3 skills/yt-video-flow/scripts/video_flow.py --help
python3 skills/yt-video-flow/scripts/video_flow.py calendar
python3 skills/yt-video-flow/scripts/video_flow.py init --name 'Video sin idea'
python3 skills/yt-video-flow/scripts/video_flow.py show V0001
python3 skills/yt-video-flow/scripts/video_flow.py begin V0001 definicion
python3 skills/yt-video-flow/scripts/video_flow.py update V0001 --patch-file /tmp/video-patch.json --nota 'Idea definida y guía de grabación preparada' --resultado completada
python3 skills/yt-video-flow/scripts/video_flow.py suggest-date V0001
python3 skills/yt-video-flow/scripts/video_flow.py check V0001
```

`--root /ruta/al/workspace` es una opción global **antes del subcomando**, útil para ensayos aislados. El helper no permite trabajar dentro de un paquete `.palmier`. Python 3.9+; sin dependencias externas ni servicio de fondo.

## Hooks y persistencia

Cada comando, incluso `show`/`check`, sincroniza calendario y bloques Markdown antes y después. Este es el hook del flujo: no depende de callbacks de Palmier. Al volver a una sesión, regenerar antes de consultar fechas; no supone que se observan cambios de YouTube o de archivos mientras nadie ejecuta el flujo.

Claude Code añade hooks de sesión en `.claude/settings.json` que ejecutan este mismo `calendar`. Aportan contexto y refrescan los bloques, sin cambiar `estado.json`, llamar a Palmier ni certificar resultados. El agente sigue usando `begin`, `update` y `snapshot` según la evidencia real. Detalles: [Claude Code](../../../docs/claude-code.md).

Los estados se escriben de forma atómica y el helper serializa sus propias escrituras con un lock local. El lock no protege contra edición manual simultánea de JSON o cambios externos en Palmier: releer antes de mutar. La parte editorial fuera de `<!-- yt-video-flow:… -->` permanece intacta. Si alguien edita manualmente `estado.json`, ejecutar `calendar` después; si tiene errores, el helper falla sin publicar un calendario incompleto.

`init --id V0001` retoma el registro existente sin sobrescribir nombre, idea o documentos. `init` sin ID crea un video nuevo. Antes de crear, identificar si el usuario pide retomar o realmente crear otro.

## Parche de estado

Guardar JSON literal usando herramientas de escritura/argumentos estructurados; pasarlo por `--patch-file`, sin interpolar textos arbitrarios en shell. Los objetos se fusionan; **listas como recursos/bloqueos se reemplazan completas**. Leer el estado actual antes de construir el parche. No se pueden editar identidad, versión, timestamps ni historial por este comando.

Ejemplo de definición:

```json
{
  "nombre": "Rescatar mi TH9 de 2017",
  "idea": "Recuperar la cuenta original y establecer el reto de maxear TH9.",
  "etapa": "grabacion",
  "prioridad": {"nivel": "media", "motivo": "Episodio inicial de recuperación; propuesta.", "confirmada": false},
  "bloqueos": ["Falta la grabación del estado inicial"],
  "siguiente_paso": "Grabar las tomas iniciales y comprobar voz/gameplay."
}
```

Etapas admitidas: `idea`, `definicion`, `grabacion`, `preparacion`, `montaje`, `edicion`, `revision`, `listo`, `exportacion`, `exportado`, `programado`, `publicado`, `archivo`, `archivado`. Las formas `exportacion` y `archivo` indican trabajo activo; `exportado` y `archivado` requieren resultados terminados/verificados. `begin` no admite etapas que declaren resultados comprobados.

`actividad` registra `en_curso`, `completada`, `bloqueada` o `parcial`; `update --resultado` termina/describe la actividad. La etapa resume dónde está el video y puede retroceder para hacer correcciones. El historial conserva los cambios.

## Palmier y snapshot

Después de crear o abrir un proyecto, registrar IDs/ruta reales:

```bash
python3 skills/yt-video-flow/scripts/video_flow.py bind V0001 --path '/ruta/real/video.palmier' --project-id 'ID-DEVUELTO' --name 'V0001 · Nombre'
python3 skills/yt-video-flow/scripts/video_flow.py adopt --path '/ruta/real/video.palmier' --project-id 'ID-DEVUELTO' --name 'Nombre existente' --etapa montaje --notes-source '/ruta/notas.md' --timeline-original 'ID-ORIGINAL' --timeline-montaje 'ID-MONTAJE'
python3 skills/yt-video-flow/scripts/video_flow.py snapshot V0001 --timeline-json /tmp/timeline-decodificado.json
```

`bind` registra la ruta real y crea un enlace local; no mueve paquetes. `adopt` reutiliza una ruta ya registrada y no reemplaza sus notas. Si hay un registro local sin vincular tras un fallo, retomar ese ID con `bind`, no repetir `adopt`.

`snapshot` recibe el objeto decodificado de `get_timeline`, con `id`, `fps`, `width`, `height`, `totalFrames` y `tracks`. Firma esas propiedades, ignorando cursor/ventana, y guarda evidencia por firma. `palmier.observado` es la referencia actual para revisiones y entregas; `palmier.timelines` conserva roles `original`, `montaje`, `edicion`, `final`.

Tras revisar anclajes, guardar `notas.timeline_id` y `notas.firma` del observado. Después de revisión real guardar `revision.estructura`, `revision.audiovisual`, `revision.firma` y `revision.evidencia`. Una firma distinta hace que `check` declare pendiente aunque los booleanos de la revisión anterior sigan registrados.

## Recursos

`recursos` es una lista de objetos como:

```json
{
  "id": "M01", "nombre": "Gameplay principal", "rol": "Crudo",
  "estado": "en_video", "ruta": "/ruta/persistente/crudo.mov",
  "media_ref": "ID-MEDIA", "asset_ref": null,
  "clip_ids": ["ID-CLIP"], "timeline_id": "ID-TIMELINE",
  "comprobado": true, "imprescindible": true,
  "notas": "Inspeccionado; gameplay bajo la voz actual."
}
```

IDs únicos `M01`, `M02`… Estados: `falta_obtenerlo`, `tenemos_no_importado`, `importado`, `en_video`. Un material disponible necesita `comprobado=true`; local no importado necesita ruta; importado necesita mediaRef/assetRef; colocado necesita también clipIds/timeline. Al duplicar timeline, actualizar referencias nuevas antes de declarar recursos comprobados en ese corte. Un recurso imprescindible ausente o no colocado bloquea la condición lista para publicar; recursos opcionales pueden seguir como ideas sin impedirla.

Las rutas relativas se resuelven desde la carpeta del video. Rutas absolutas son útiles para fuentes antiguas/adoptadas. No conservar en `/tmp` recursos que Palmier referencia: usar carpetas persistentes.

## Fechas y hechos de publicación

`fechas.propuesta` y `fechas.confirmada`: `YYYY-MM-DD`. `fechas.programada` y `fechas.publicada`: ISO 8601 con hora/offset, por ejemplo `2026-10-10T18:00:00-06:00`. Si el usuario solo da día para una programación, pedir la hora faltante; no inventarla. La reserva efectiva sigue precedencia **publicada, programada, confirmada, propuesta** y usa el día local de México.

`suggest-date` busca desde mañana o una fecha posterior con `--from-date`; no sustituye fechas confirmadas/reales. Rechaza otra reserva del mismo día al proponer/confirmar y devuelve alternativa. Fechas reales informadas se registran aunque colisionen; el calendario señala el conflicto. Cambiar una reserva exige un parche explícito y no modifica otros videos.

Para informar programación/publicación, actualizar fecha real y `etapa`, además de `youtube.url` al publicar. `programado` exige fecha/hora y `publicado` exige fecha/hora y URL HTTPS de YouTube. No es una integración con YouTube.

## Entregas y condición lista para publicar

- `publicacion`: `titulo_elegido` y `descripcion_revisada`; no confundir la recomendación con elección.
- `miniatura`: `estado` (`sin_iniciar`, `en_diseno`, `lista`) y `ruta` del archivo final.
- `exportacion`: `estado` (`sin_exportar`, `en_proceso`, `completada`, `fallida`), `job_id`, `ruta`, `timeline_id`, `firma`, `verificado`.
- `archivo`: `estado` (`pendiente`, `en_proceso`, `completado`, `fallido`), `ruta`, `verificado`.

El helper verifica archivos y coherencia de referencias; **no reproduce ni analiza codecs** y no justifica marcar verificado sin inspección real. Registrar estas comprobaciones en evidencia/revisión. `check` calcula `listo_para_publicar` por corte, notas, revisiones, evidencia, exportación, título, descripción, miniatura, fecha y ausencia de bloqueos. La etapa publicada registra un hecho externo aunque falten entregables locales.
