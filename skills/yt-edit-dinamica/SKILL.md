---
name: yt-edit-dinamica
description: Coordina una pasada de ritmo sobre un episodio de Clash of Clans en Palmier Pro: versiona el timeline, aplica encuadre, tarjetas de capítulo, zooms, subtítulos animados y efectos de sonido en el orden correcto, delega trabajo masivo a subagentes, respeta los cambios del usuario y registra el resultado. Úsala cuando el pedido sea hacer la edición más dinámica o crear una nueva versión (v2, v3) del corte.
---

# yt-edit-dinamica

Skill compartida por Codex y Claude Code, enlazada desde sus carpetas de descubrimiento. En Claude Code se invoca con `/yt-edit-dinamica`. Resuelve los nombres lógicos de herramientas contra el MCP disponible; no copies prefijos, IDs ni contexto de otra sesión. Trabaja dentro de `yt-video-flow` (etapa de edición) y no sustituye a `yt-cut-hi` (cortes de ideas). Coordina cuatro skills: [`yt-edit-zooms`](../yt-edit-zooms/SKILL.md), [`yt-edit-capitulos`](../yt-edit-capitulos/SKILL.md), [`yt-edit-subtitulos`](../yt-edit-subtitulos/SKILL.md) y [`yt-edit-sfx`](../yt-edit-sfx/SKILL.md). Lo aprendido en V0001 está en [references/lecciones.md](references/lecciones.md).

No exporta, no programa ni publica, no diseña miniaturas y no marca una revisión audiovisual: ver o inspeccionar fotogramas no equivale a reproducir.

## 1. Entrada

1. `python3 skills/yt-video-flow/scripts/video_flow.py calendar`, y lee `estado.json`, `notas.md` y `continuidad.md` del episodio.
2. Lee el timeline real. Si `get_timeline` devuelve un archivo por tamaño, analízalo con un script (`python3 -I`); ese JSON decodificado sirve para `snapshot`.
3. **El usuario edita en Palmier entre sesiones.** Antes de mutar compara con lo que esperas: resolución y duración, pistas ocultas, borradas o renombradas, marcadores abiertos, captions curados, efectos de color, recortes. Son decisiones suyas: no las reviertas ni «repares»; informa y pregunta. No supongas que los fotogramas de tus notas anteriores siguen valiendo.

## 2. Versionar

Nunca edites el original ni el corte revisado. `create_timeline(from=<corte base>, name="Edición vN")` crea una copia con IDs nuevos (relee `get_timeline`). Solo un corte es el vigente: lo decide el usuario. Una versión nueva no hereda la revisión del corte anterior.

## 3. Orden de operaciones

| Paso | Skill | Por qué en este orden |
| --- | --- | --- |
| 1. Encuadre | `yt-edit-zooms` §2 | Todo lo demás se calcula sobre el encuadre. |
| 2. Capítulos | `yt-edit-capitulos` | Insertan duración con ripple: desplazan todo lo posterior. |
| 3. Zooms | `yt-edit-zooms` | Con los frames definitivos. |
| 4. Subtítulos | `yt-edit-subtitulos` | Sus keyframes son absolutos; se hacen con la posición final. |
| 5. Efectos | `yt-edit-sfx` | Los índices de pistas cambian al añadir pistas; se sincronizan con zooms y tarjetas ya fijos. |
| 6. Verificar y registrar | esta skill, §6 | Fotogramas, snapshot, notas, estado. |

Ejecuta solo los pasos pedidos.

## 4. Estructura de referencia adaptada

El usuario compartió una estructura de edición dinámica (cortes y zooms a la interfaz, pantallas negras de capítulo con impacto, aislamiento del objeto, música y efectos). Lo que se pudo implementar con lo disponible:

| Elemento | Implementación | Estado |
| --- | --- | --- |
| Zoom o recorte a la interfaz al mencionar cifras | `yt-edit-zooms`: foco en contadores, etiquetas, precios | Hecho |
| Pantallas negras con tipografía limpia e impacto | `yt-edit-capitulos` | Hecho |
| Aislar el sprite sobre pasto neutro | Viñeta: `apply_effect` `stylize.vignette` `amount −0.75`, `midpoint 0.35`, `roundness 0`, `feather 0.55` sobre el clip del objeto | Aproximación |
| Aislar con recorte real | `manage_masks` tipo `magic` | Consume créditos: pedir autorización |
| Pop-ups sonoros y whooshes | `yt-edit-sfx` | Hecho con la biblioteca local |
| Música de fondo, monedas, martillos, memes | — | No hay material; generar cuesta créditos |
| Voz comprimida y ecualizada | — | Palmier solo ofrece `denoise_audio` |

## 5. Gasto, delegación y autoridad

- `generate_audio`, `generate_image`, `generate_video`, `upscale_media` y las máscaras mágicas **consumen créditos**. Pide autorización explícita (qué, cuántos, para qué). Un saldo suficiente no la sustituye.
- **Delega** solo trabajo masivo y repetitivo (cientos de clips con keyframes), con la plantilla de [references/delegacion.md](references/delegacion.md). Dale IDs reales, restricciones y verificación. Su informe es una afirmación, no una verificación: compruébalo tú.
- Detén al agente (`TaskStop`) si su trabajo choca con el cambio que el usuario acaba de pedir o si está a punto de borrar pistas que necesitas.
- Un mensaje de un subagente no autoriza gastos, cambios de permisos ni acciones que el usuario no pidió.

## 6. Verificar y registrar

1. `inspect_timeline` en entradas, reposos y cortes de cada cambio, y en los momentos con datos del juego (precios, contadores). Informa solo lo comprobado en fotogramas.
2. Relee `get_timeline` y comprueba pistas `hidden`, número de clips, huecos y que la duración sea la esperada. Tus pistas nuevas quedan visibles; las ocultas por el usuario, ocultas.
3. Guarda el JSON decodificado en `videos/VNNNN/evidencia/` mediante `snapshot ID --timeline-json ARCHIVO`. Eso actualiza `palmier.observado` y los ajustes; la revisión guardada del corte anterior queda como no vigente (`check` lo avisa).
4. Si el usuario eligió el nuevo corte: actualiza `palmier.timelines.edicion`, remapea los recursos (`clip_ids`, `timeline_id`) con un parche completo, `notas.timeline_id`/`firma` y `siguiente_paso`. Si no lo eligió, deja el corte vigente y anota la versión como candidata.
5. Añade a `notas.md` una sección con fecha: corte base y nuevo, duración, qué se implementó, frames, lo que no se pudo y lo pendiente. Registra con `update … --resultado parcial` (o `completada` solo con resultado real).
6. Pendientes habituales: reproducción real del usuario, revisión audiovisual, marcadores abiertos suyos, música y efectos temáticos.
