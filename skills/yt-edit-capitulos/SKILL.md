---
name: yt-edit-capitulos
description: Inserta tarjetas negras de capítulo con ripple en Palmier Pro: elige cortes en fronteras de frase, planifica las posiciones finales, inserta de atrás hacia adelante sin romper audio ni subtítulos, rotula con tipografía Clash y añade sonido de impacto. Úsala para separar un episodio de Clash of Clans en capítulos que reinician la atención del espectador.
---

# yt-edit-capitulos

Skill compartida por Codex y Claude Code, enlazada desde sus carpetas de descubrimiento. En Claude Code se invoca con `/yt-edit-capitulos`. Resuelve los nombres lógicos de herramientas contra el MCP disponible. La coordina `yt-edit-dinamica`. **Añade duración** al episodio: úsala solo cuando el usuario quiera capítulos, y siempre en un timeline versionado (`create_timeline(from=...)`), nunca sobre el original ni sobre el corte revisado.

Es la adaptación de las «pantallas negras de separación con tipografía limpia y efectos de impacto» de la estructura de referencia que dio el usuario. Se hace **antes** que zooms, captions y efectos porque desplaza todo.

## 1. Elegir los cortes

- Un capítulo por cambio de tema (reto, problema, oferta, bloqueo, reorganización, opinión). En V0001: 5 tarjetas en 3.5 minutos.
- Cada corte cae en una **frontera de frase**: lee `get_transcript` y elige el inicio de un clip de V1 o un silencio entre frases. Un corte a media frase queda cortado en seco y obliga a partir clips con zoom.
- Evita capítulo al inicio del video y dos tarjetas a menos de unos 20 s.
- Antes de insertar, comprueba con `get_timeline` qué clips **cruzan** cada corte (captions, apoyos, efectos). Un clip que cruza se parte con el ripple (en V0001 se partió un caption de la pista oculta).

## 2. Planificar

```bash
echo '{"cuts":[1192,2172,4525,4970,5431],"card_frames":36,"total_frames":6351,"map_frames":[3515]}' \
 | python3 skills/yt-edit-capitulos/scripts/chapter_plan.py
```

`cuts` van en fotogramas **del timeline actual**. Devuelve el orden de inserción (descendente), el inicio final de cada tarjeta (`start = corte + 36·n`), la duración nueva y los fotogramas de interés trasladados (zooms, efectos, notas). Duración de tarjeta: 36 fotogramas (1.2 s).

## 3. Insertar

1. `import_media(source={matte:{hex:"#000000", aspectRatio:"Project"}}, name:"Tarjeta negra", folder:"Capitulos")`.
2. `manage_tracks set` con `syncLocked: true` en **todas** las pistas: si no, el ripple no mueve esas pistas. Comprueba también los marcadores: se desplazan con el ripple.
3. `insert_clips(trackIndex=<V1>, atFrame=<corte>, entries=[{mediaRef:<matte>, durationFrames:36}])` **de atrás hacia adelante**, así los cortes anteriores siguen siendo válidos. La respuesta lista qué pistas se movieron y cuántos clips. Revisa `get_timeline` en una ventana alrededor del primer corte: voz y audio vinculado en hueco, captions desplazados.

## 4. Rotular

Con `add_texts` (sin `trackIndex`, crea pistas nuevas arriba; **los índices de pistas inferiores cambian**: relee antes de seguir). Dos textos por tarjeta, mismo rango `[inicio, inicio+36)`:

| Texto | Estilo | Posición |
| --- | --- | --- |
| Rótulo «CAPÍTULO N» | Clash 64, blanco, mayúsculas, `tracking` 6, sin contorno ni sombra, `slideUp` | `x 0.5`, `y 0.40` |
| Título | Clash 120 (110 si pasa de ~20 caracteres), color del capítulo, contorno negro 6, sombra sólida oscura con `y` 8, `popIn` | `x 0.5`, `y 0.54` |

Colores por capítulo (rotar para distinguirlos): amarillo `#F2D90F` con sombra `#FF5A1F`; cian `#16D6FF` con `#0A6E8F`; naranja `#FF5A1F` con `#7A2A0C`; verde `#3DB10E` con `#1F5A07`. Títulos de ≤ 22 caracteres caben en un 90 % del ancho; verifícalo con `inspect_timeline`.

## 5. Sonido

Con `yt-edit-sfx`: `impacto_capitulo` (Camera Shutter 2, −8 dB) al inicio de cada tarjeta y `salida_capitulo` (Quick Whoosh, −14 dB) hacia el fotograma 24 de la tarjeta. `add_clips` entra a 0 dB: fija el volumen después. La voz calla durante la tarjeta.

## 6. Verificar y registrar

- `inspect_timeline` en 4 fotogramas de cada tarjeta: texto centrado, legible, sin cortarse y sin gameplay detrás.
- La duración total coincide con `new_total_frames`. Los marcadores y las notas deben trasladarse con `map_frames`.
- Registra en las notas la tabla de tarjetas (inicio, fin, título, frase de referencia) y actualiza los fotogramas de zooms y efectos posteriores. Un corte nuevo requiere snapshot y repetir la revisión: no heredes la revisión del corte anterior.
