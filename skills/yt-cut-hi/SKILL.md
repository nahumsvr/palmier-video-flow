---
name: yt-cut-hi
description: Limpia un clip hablado ya colocado en Palmier Pro, corta pausas sin borrar material y crea un timeline separado con ideas completas, quitando intentos fallidos y repeticiones. Conserva sincronizados video y audios. Úsala para este montaje de diálogo, completo o por fases.
---

# yt-cut-hi

Skill compartida por Codex y Claude Code, enlazada desde sus carpetas de descubrimiento. En Claude Code se invoca con `/yt-cut-hi`. Resuelve los nombres lógicos de herramientas contra el MCP disponible; no copies prefijos, IDs ni contexto de otra sesión. Los hooks del agente no reemplazan la evidencia acústica ni el criterio editorial de este montaje.

El flujo completo deja el original con cortes, sin pérdidas ni desplazamientos, y un timeline nuevo con las mejores versiones de las ideas, en orden y sin huecos. Ejecuta solo las fases solicitadas: cortar no autoriza eliminar; preparar un montaje no autoriza exportar.

## 1. Obtener evidencia una vez

- Consulta los esquemas actuales de las herramientas necesarias por nombre. No imprimas las instrucciones compartidas de todas las herramientas.
- `manage_project(action="list")` identifica el proyecto visible/activo; `open` vincula la sesión cuando haga falta. Lee `get_timeline` y `get_media`. Registra ID del timeline, fps, rango del clip, trims, velocidad, tracks, audios vinculados y duración. Si varios candidatos son ambiguos, pide el dato que falta.
- Obtén una transcripción **antes de cortar** con `get_transcript(granularity="words", language=idioma, trackIndex=pista_de_voz)`. Guarda el resultado completo como datos locales y lee el discurso como prosa; muestra solo texto y rangos relevantes.
- Si solo hay inicios de palabra, no inventes finales ni detectes silencio restando inicios consecutivos. Una palabra larga también ocupa tiempo. Para límites finales usa `inspect_media(wordTimestamps=true)` solo en ventanas ambiguas, sin retranscribir todo por sistema.
- Mide pausas en el audio real de la voz. Si el host accede al archivo, `ffprobe` verifica streams y tiempos; `ffmpeg` con `silencedetect` aporta evidencia acústica rápidamente. Elige voz, no juego o música. Empieza alrededor de -45 dB y 0.5 s; ajusta según ruido y nivel observado. Estos valores son heurísticas, no prueba de silencio.
- Une pausas separadas por clics breves solo tras comprobar que no hay habla. Contrasta límites con palabras cercanas. Respiraciones, finales suaves y nivel bajo no son equivocaciones. Ante discrepancias entre transcripciones, inspecciona únicamente el rango conflictivo y conserva material incierto.
- Si falta un stream y la reparación está dentro del pedido, verifica el contenedor, extrae ese stream con `-map 0:a:N -c:a copy`, importa con `import_media`, espera estado listo y coloca según el offset real. Mantén el archivo en una ubicación persistente fuera del paquete vivo. Omite esta reparación si ambas pistas ya existen.

## 2. Cortar sin eliminar

- Prepara un plan único en **frames del proyecto**: límites de pausas y rangos de intentos fallidos. Todas las pistas sincronizadas deben recibir las mismas posiciones.
- Pausas de >=0.5 s son candidatas. Deja unos 0.1–0.2 s junto al habla; no cortes palabras. Si dos límites quedan a pocos frames, unifica la posición cuando sea semánticamente seguro para evitar microclips.
- Selecciona errores por contenido: frase abandonada, reinicio, repetición involuntaria o corrección explícita seguida de una versión completa. No clasifiques énfasis, terminología, opiniones, pausas retóricas ni errores del transcriptor como errores del hablante.
- Usa `split_clips(trackIndex=video, frames=[...])` en una llamada por track. El video corta automáticamente su audio vinculado; corta aparte los audios independientes. No vuelvas a cortar la pista vinculada.
- Verifica una vez: duración original, cobertura continua, mismos límites y relación fuente/timeline de video y audios. En esta fase no uses `remove_silence`, `remove_words` ni `ripple_delete_ranges`.

## 3. Reunir las ideas completas

- Define qué quitar usando tiempos **anteriores** a cualquier eliminación. Conserva una versión completa de cada idea importante, el contexto necesario y el orden narrativo. Quita pruebas previas, frases abandonadas y primeras tomas cuando la posterior completa la misma idea.
- No recicles automáticamente rangos de error tentativos: revisa el reinicio. Una palabra repetida puede requerir quitar solo esa palabra, no toda la oración. Conserva la toma que realmente termina la idea.
- Los cortes de silencio no implican que todas las pausas deban eliminarse. Para el montaje empieza por pausas >=1.5 s, con unos 0.4 s después de la voz y 0.25 s antes de la siguiente entrada. Acorta pausas menores solo con evidencia clara y cuando mejora el ritmo. Evita finales cortados y uniones que cambian el sentido.
- `create_timeline(from=originalId, name="Ideas completas")` duplica el original y normalmente activa la copia; respeta la respuesta. Lee `get_timeline` después de crear/cambiar timeline: los IDs de clips y tracks son nuevos.
- Une rangos solapados y ejecuta **una** `ripple_delete_ranges(trackIndex=video, units="frames", ranges=[...])`. Las pistas con sync-lock participan según el contrato actual. No elimines otra vez los mismos tiempos en A1/A2: la primera operación ya cambió las posiciones. Si la herramienta se niega o una pista no participa, resuelve el motivo antes de mutar; no ignores una pista de voz para pasar la validación.
- Lee `get_timeline` y una transcripción actualizada al terminar. Lee las frases a ambos lados de cada unión: no deben quedar conectores, palabras truncadas ni ideas sin remate. Los microclips pueden hacer que el transcript omita voz conservada: compara trims y fuente antes de borrar o afirmar que falta una palabra.
- Verifica cobertura sin huecos, duración calculada, mismo desplazamiento y trims de todas las pistas, y existencia del original. Corrige solo problemas concretos. Para rehacer la última eliminación, usa `undo` y relee el estado antes de aplicar el plan corregido; evita copias sucesivas innecesarias.
- Si puedes reproducir el montaje, escucha las uniones relevantes. Transcripción e imágenes no verifican reproducción audiovisual. No afirmes haber escuchado lo que no reprodujiste.

## Cálculos y eficiencia

- Usa [scripts/plan_ranges.py](scripts/plan_ranges.py) para normalizar evidencia, cortes y eliminaciones; `--help` documenta el JSON de entrada. No reconoce errores ni modifica Palmier: recibe decisiones editoriales revisadas.
- El helper recibe pausas en segundos **del timeline**, `drop_frames` y `split_frames` en frames del proyecto. Para trims, posición distinta de cero o velocidad modificada, transforma los tiempos con el mapping real antes de usarlo. No conviertas segundos de fuente multiplicando por fps si hay cambios de velocidad.
- Guarda transcript, plan y verificaciones fuera del paquete vivo. Actualiza la vista de trabajo con deltas; relee en límites de fase, tras cambios externos o errores de estado. No vuelques JSON completo después de cada llamada.
- Procesa rangos juntos, no palabra por palabra. Paraleliza solo lecturas independientes; mutaciones y dependencias van en secuencia. Descubre únicamente herramientas necesarias, no modelos de generación.
- Prioriza precisión editorial y después número de llamadas. Inspecciona ventanas ambiguas en vez de retranscribir el video entero. No generes medios ni exportes para verificar este flujo.
- Deja activo el nuevo timeline solicitado. Informa nombre, duración, preservación del original e incertidumbres materiales; distingue verificaciones estructurales de reproducción real.
