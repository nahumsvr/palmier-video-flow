---
name: yt-edit-zooms
description: Fija el encuadre del gameplay y crea zooms con keyframes en Palmier Pro: encuadre completo sin recortar la interfaz, golpes de zoom al entrar a un corte, empujes lentos, zoom a un contador o a una captura fija (hasta ×4) y verificación en fotogramas. Úsala para dar dinamismo a una edición de Clash of Clans sin ocultar gemas, constructores ni precios.
---

# yt-edit-zooms

Skill compartida por Codex y Claude Code, enlazada desde sus carpetas de descubrimiento. En Claude Code se invoca con `/yt-edit-zooms`. Resuelve los nombres lógicos de herramientas contra el MCP disponible. La coordina `yt-edit-dinamica`; úsala sola cuando el pedido sea solo de zooms o de encuadre. No cambia el corte, no exporta y no toca timelines que el usuario no pidió.

## 1. Modelo de coordenadas (comprobado en Palmier Pro)

- `set_keyframes` con `scale` recibe `[frame, ancho, alto]` **normalizados al lienzo**, no un factor. `position` recibe `[frame, x, y]` de la **esquina superior izquierda**, también en 0–1. Los frames son relativos al clip (0 = su primer frame). Cada llamada **reemplaza toda la pista** de esa propiedad: manda todas las filas.
- Una escala sin filas de posición se ancla en el **centro**. Si el clip tiene filas de `position`, mandan sobre la transformación estática. Para apuntar a un dato usa las dos propiedades con filas en los mismos frames.
- Un clip enlazado conserva su audio; los keyframes visuales no lo afectan. Una imagen admite `scale`, `position` y `blur`.

## 2. Encuadre: decide uno y úsalo en todo

El gameplay del iPad mide 2360 × 1640 (1.439). En un proyecto 1920 × 1080:

| Encuadre | Tamaño base | Resultado |
| --- | --- | --- |
| **Completo (`contain`)** | 0.8095 × 1.0 | Se ve toda la interfaz, con barras negras a los lados. |
| Relleno (`cover`) | 1.0 × 1.235 | Recorta ≈ 9.5 % arriba y abajo; desaparece la barra superior (contador de constructores). |

El usuario eligió **encuadre completo** el 12 de octubre de 2026. Aplícalo a todos los segmentos de V1 y a las capturas que cubran gameplay, incluidos los clips cortos de 3–10 fotogramas: un clip con otro encuadre se ve como un destello. Para fijarlo: `set_clip_properties` con `transform {width, height, centerX: 0.5, centerY: 0.5}` en cada clip visual, y después reescribe sus keyframes.

**Si cambia la resolución del proyecto** (por ejemplo 2360 × 1640 → 1920 × 1080), Palmier convierte los keyframes de forma incoherente: las filas «1.0» y las mayores terminan en encuadres distintos y una toma puede arrancar a ×2.1 en lugar de ×1.1. No repares los valores existentes: fija la transformación estática nueva y **rehaz todas las filas desde los factores de zoom** que quieras.

## 3. Calcular las filas

```bash
echo '{"canvas":[1920,1080],"media":[2360,1640],"fit":"contain","rows":[
  {"frame":25,"zoom":1},{"frame":40,"zoom":1.5,"focus":[0.5,0.04]},
  {"frame":105,"zoom":1.5,"focus":[0.5,0.04]},{"frame":125,"zoom":1}]}' \
 | python3 skills/yt-edit-zooms/scripts/zoom_rows.py
```

Devuelve `scale` y `position` listas para `set_keyframes`. `focus` es el punto de la fuente (0–1) que debe quedar centrado; el script lo limita para que no aparezcan bordes vacíos. Si ninguna fila trae `focus`, `scale_only_is_enough` es `true` y puedes omitir `position`. `interp` opcional por fila (`smooth` por defecto).

## 4. Recetas a 30 fps

| Efecto | Filas de zoom (relativas al clip) | Uso |
| --- | --- | --- |
| Golpe de entrada | `[0, 1.08]`, `[20, 1.0]`, `[fin, 1.04–1.05]` | Primer plano tras un corte largo; alternarlo con el empuje lento. |
| Empuje lento | `[0, 1.0]`, `[fin, 1.06–1.07]` | Planos largos sin foco; cierres: hasta 1.15–1.25. |
| Zoom a un dato | entrar en 10–15 fotogramas antes de la palabra, mantener la frase, salir en 15–20 | Un contador, una etiqueta o un precio. |
| Captura fija ×4 | `1.0` → `4.3` (10 fotogramas) → `3.9` (6) → `4.0` (4) → `4.15` (≈ 45) | Cifra clave sobre una imagen estática. Añade `blur` `[0,0]`, `[5,10]`, `[12,3]`, `[18,0]`. |

Focos usados en V0001 (coordenadas de la fuente): contador de constructores `(0.5, 0.04)` ×1.5; gemas `(0.93, 0.28)` ×1.6–1.7; tarjeta de la oferta `(0.5, 0.6)` ×1.35; etiqueta «Builder Hall Level 4» `(0.5, 0.22)` ×1.9; fecha del clan `(0.30, 0.31)` ×1.6; contador de gemas de una captura `(0.92, 0.285)` ×4. **Comprueba cada foco mirando el fotograma**: el diseño de la pantalla cambia entre momentos.

Criterio editorial: hay zoom cuando se menciona una cifra, un problema o un remate; no hay zoom continuo durante explicaciones largas. Con contadores en las esquinas no pases de ×1.08 en golpes de entrada. Un ×4 sobre una captura de 2360 px pierde nitidez: avisa al usuario. No hagas ×4 sobre video en movimiento.

## 5. Aplicar y verificar

1. Lee `get_timeline` (si es enorme, Palmier lo guarda en un archivo: analízalo con un script y no lo leas completo). Identifica clips con keyframes previos y su encuadre.
2. Fija la transformación estática, luego `set_keyframes` de `scale` y, si hay foco, de `position`. Un clip puede tener cambios del usuario (recortes, color): respétalos.
3. Verifica con `inspect_timeline` en entrada, mantenimiento y salida de cada zoom, y en dos fotogramas a ambos lados de cada corte para confirmar que no hay salto de encuadre ni barras vacías.
4. Empareja cada zoom con su efecto de sonido (`yt-edit-sfx`, rol `zoom` o `impacto_grande`). Si luego mueves un clip con zoom, mueve también su efecto.
5. Registra en las notas del episodio los clips, frames y factores. Las comprobaciones en fotogramas no equivalen a reproducción.
