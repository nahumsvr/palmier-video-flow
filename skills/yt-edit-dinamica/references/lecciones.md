# Lecciones de V0001 (12 de octubre de 2026)

Errores y comportamientos comprobados en Palmier Pro al hacer Edición v2 y v3. Cada punto indica la consecuencia y qué hacer.

## Estado y lectura

1. **`get_timeline` completo no cabe en el contexto** y se guarda en un archivo. Analízalo con `python3 -I` (resumen por pista, huecos, claves). Ese JSON es el que acepta `snapshot`.
2. **El usuario cambia el proyecto entre sesiones**: resolución (2360 × 1640 → 1920 × 1080), duración, pistas borradas, captions curados, marcadores, un efecto de color. Relee todo y compara antes de editar.
3. **Pistas ocultas**: `hidden: true` no se ve en un `get_timeline` abreviado. Un subagente dejó una pista oculta y otro la «visibilizó» sin saber quién la ocultó. Comprueba `hidden` al terminar; no reactives lo que el usuario ocultó.
4. **Los índices de pista cambian** al añadir o quitar pistas arriba (`add_captions`, `add_texts` sin `trackIndex`, `manage_tracks remove`). Usa `trackId` con `manage_tracks` y relee antes de llamadas por índice (`add_clips`, `insert_clips`).

## Keyframes y encuadre

5. `set_keyframes` **reemplaza toda la pista** de la propiedad. `scale` es `[frame, ancho, alto]` normalizado; `position` es la esquina superior izquierda.
6. Una escala sin posición se ancla en el centro; con filas de posición, estas mandan.
7. **Cambiar la resolución deforma los keyframes** de escala y posición. Rehaz todas las filas desde los factores de zoom.
8. Encuadre `cover` recorta la barra superior con los contadores. Usa encuadre completo y el mismo en todos los clips, también los de 3 fotogramas.
9. El preset `slideUp` de texto dura 1–2 fotogramas y no se configura: no sirve para entradas con curva.
10. **Los keyframes de posición de un texto son absolutos**: si cambia su tamaño, fuente o contenido, el texto se descentra. Primero estilo, después keyframes. Cambiar solo el ancho del contorno no movió la posición.
11. `inspect_timeline` renderiza en baja resolución: un rebote de 4 px no se distingue. Los valores de keyframes sí se pueden leer.

## Texto y audio

12. `update_text` con `bold: false` en una fuente sin cara no negrita (Impact) falla. Los nombres de fuente no instalados se rechazan con una lista de coincidencias. `Clash` está instalada.
13. En `content`, `\n` literal queda como barra y `n`: usa un salto de línea real.
14. `add_clips` de audio entra a **0 dB**: fija el volumen enseguida.
15. Si el apoyo se coloca sin audio vinculado (`includeAudio: false`) no suena aunque el transcript detecte su voz.
16. Al mover una imagen o un clip con zoom hay que mover su efecto; si no, queda desfasado o duplicado.

## Ripple e insertar

17. `insert_clips` mueve solo las pistas con `syncLocked: true` y la pista de destino. Actívalo en todas antes. Los marcadores se desplazan; un clip que cruza el punto de inserción se parte.
18. Inserta de **atrás hacia adelante** para conservar los fotogramas de los cortes anteriores.
19. `set_clip_properties` con `transform {width}` fija el ancho y deja el alto por defecto; pasa ancho y alto cuando importen.

## Gasto, agentes y estado

20. Generar audio, imágenes, video, upscale y máscaras mágicas consumen créditos y piden autorización explícita. El saldo no la sustituye.
21. Los informes de subagentes son afirmaciones: verifica pistas, `hidden` y fotogramas tú. Detén al agente antes de que borre una pista que necesitas.
22. Un `snapshot` nuevo cambia `palmier.observado` y `settings`; la revisión del corte anterior deja de corresponder y `check` lo avisa. Tras elegir el nuevo corte remapea recursos y notas con un parche que reemplace la lista completa de recursos.
23. Solo se lee el `project.json` del paquete `.palmier` (por ejemplo para tamaños de texto). Nunca se escribe ni se mueve un paquete abierto.
