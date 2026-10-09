---
name: yt-video-flow
description: >-
  Organiza y produce videos largos de Clash of Clans por etapas con Palmier Pro: crea o adopta proyectos, conserva crudos, prepara guion y recursos, reutiliza yt-cut-hi, mantiene notas y calendario, propone títulos y miniaturas y verifica exportaciones. Úsala también para retomar un video o registrar su publicación; el usuario diseña miniaturas y publica en YouTube.
---

# yt-video-flow

Esta skill vive en el workspace de producción. Lee `canal.md` al comenzar una sesión. El helper funciona con Python 3.9+ y biblioteca estándar; organiza documentos y estados, **no edita Palmier ni publica en YouTube**. Tú coordinas las herramientas del editor según el pedido del usuario.

## Entrada y continuidad

1. Ejecuta `python3 skills/yt-video-flow/scripts/video_flow.py calendar` antes de buscar un proyecto, consultar fechas o ejecutar una etapa.
2. Identifica el ID permanente `VNNNN` por estado, nombre, idea o ruta Palmier. Si el pedido retoma un video, no crees otro. Cuando falte el tema, crea el proyecto vacío y registra qué necesitamos después.
3. Lee `estado.json` y los documentos de la etapa. Usa [references/etapas.md](references/etapas.md) para sus resultados y [references/helper.md](references/helper.md) para los comandos y campos. Las etapas no se ejecutan todas por defecto.
4. Antes de mutar Palmier: consulta `manage_project(action="list")`, vincula el proyecto correcto con `open` cuando haga falta y lee timeline/medios. No retargetees silenciosamente otro proyecto si cambió la ventana visible.
5. Registra el inicio con `begin ID ETAPA`. En éxito o bloqueo, guarda un parche JSON con `update ID --patch-file ARCHIVO --nota TEXTO`. Cada comando refresca documentos y calendario; no hace falta un hook nativo del editor.

## Creación y adopción

- `init --name NOMBRE [--idea IDEA]` crea el workspace de un video. Guarda su ID **antes** de crear el proyecto Palmier; si el editor falla, conserva ese ID y registra el bloqueo para reintentar.
- Crea el proyecto con `manage_project(action="create", name="VNNNN · nombre", aspectRatio="16:9", fps=30, quality="1080p")`, lee su respuesta y registra ID, ruta y settings con `bind`. La carpeta `palmier/` contendrá un enlace al paquete real. No hagas exportaciones para ubicarlo ni escribas sus JSON internos.
- Para adoptar, consulta los datos reales y usa `adopt --path RUTA --project-id ID --name NOMBRE --etapa ETAPA`. El helper identifica rutas ya registradas y no duplica el video. Copia notas anteriores solo con `--notes-source`; nunca reemplaza notas de un registro existente.
- Retén las fuentes antiguas donde están. Identifica sus rutas comprobadas, sin copiar videos grandes ni extraer streams que ya existen.

## Edición, notas y evidencia

- Preparación: inspecciona fuentes, selecciona la voz, comprueba streams y offsets y registra recursos antes de importar. La existencia de un archivo no demuestra su contenido. Usa estados comprobables: `falta_obtenerlo`, `tenemos_no_importado`, `importado`, `en_video`.
- Montaje: lee y aplica [yt-cut-hi](../yt-cut-hi/SKILL.md). Guarda transcript/plan/verificaciones en `evidencia/`; reutiliza los IDs de original y montaje ya registrados. El original puede recibir cortes sin pérdidas según esa skill.
- Edición: duplica el montaje como `Edición` una sola vez, registra su ID y retómalo. Usa pistas de apoyo para cubrir gameplay sin sobrescribirlo. Para insertar duración usa la operación de inserción/ripple con sincronización verificada. Relee notas y transcripción tras cambios temporales.
- Selecciona énfasis por función editorial, no por una frecuencia fija de efectos. Resalta problema, humor, tentación, dato decisivo o remate. Mantén legibles gemas, constructores, precios y evidencia en pantalla. No deduzcas cifras ausentes ni crees promesas que el video no cumple.
- Cada nota lleva ID, frase, timeline, `[inicio, fin)` en frames, propósito, recurso, modo (por encima/en medio/énfasis), prioridad, decisión y estado de tarea. Si se usan marcadores Palmier, registra sus IDs y relee su posición tras ripple; no resuelvas automáticamente una revisión del usuario.
- Guarda una lectura decodificada de `get_timeline` y usa `snapshot ID --timeline-json ARCHIVO`. El helper firma la estructura y detecta notas/revisiones/exportaciones que correspondan a otro corte. Tras actualizar anclajes de notas, registra `notas.firma` y `notas.timeline_id` del snapshot actual.
- Lee `get_media` antes de reimportar y verifica mediaRef/clipIds para cambiar estados. Mantén localmente los archivos referenciados por Palmier.

## Publicación y cierre

- En `publicacion.md`, prepara cinco títulos con un recomendado, tres opciones de miniatura y descripción lista para copiar. Para miniaturas indica composición, captura/fotograma, texto corto, colores y título compatible. No generes la miniatura del usuario.
- Título elegido y revisión de descripción se registran en el estado; las opciones y el texto editorial viven fuera de los bloques generados. Sugiere prioridad con motivo según los criterios de `canal.md`.
- Usa `suggest-date ID` antes de proponer una fecha; es una reserva tentativa desde mañana. Diferencia propuesta, fecha confirmada, programación y publicación reales. No muevas fechas ajenas para resolver un conflicto. La hora se guarda con zona/offset cuando el usuario la fija.
- Revisión: verifica estructura/sincronía, frases de las uniones, apoyos prometidos, textos y composición. Ver imágenes o leer transcript no equivale a escuchar. Marca `revision.audiovisual` solo tras reproducción real o revisión explícita del usuario, y conserva evidencia y firma.
- Solo ante pedido de exportar: toma snapshot final, llama `export_project` para el timeline concreto y registra jobId/estado `en_proceso`. Consulta `manage_exports` hasta resultado terminal, inspecciona archivo y advertencias; `ffprobe` comprueba streams/duración y reproducción permite comprobar percepción. No reenvíes un trabajo por tardar.
- Registra `completada` y `verificado=true` solo con archivo comprobado y la firma exportada. Un fallo queda como `fallida`; no avances a `exportado` sin resultado verificado. Los nombres `exports/VNNNN-v01.mp4`, `v02`, etc. evitan sobrescribir entregas previas.
- La exportación puede terminar antes de la miniatura. `check ID` calcula pendientes para publicación; no declares listo un video con bloqueos imprescindibles, revisión pendiente o entregable de otro corte.
- Tú no programas ni publicas en YouTube. Cuando el usuario informe el resultado, registra `fechas.programada`/`fechas.publicada`, URL y etapa correspondiente; una publicación externa es un hecho aunque falten datos locales.
- Archiva solo cuando se solicite: exporta paquete autocontenido a `archivo/`, espera resultado y verifica advertencias/medios. Registrar respaldo no autoriza borrar fuentes ni modificar el paquete vivo.

## Terminar cada pedido

Actualiza las notas o evidencia afectadas y luego el estado con resultados reales, bloqueo principal y siguiente paso. El helper regenera calendario y bloques operativos conservando el texto editorial. Resume lo realizado, la etapa, los pendientes materiales y el próximo pedido útil; no prometas trabajo de fondo.
