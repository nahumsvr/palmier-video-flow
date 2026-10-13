---
name: yt-edit-subtitulos
description: Crea y anima los subtítulos de varias palabras por clip (estilo V4 de Edición v2 y v3) en Palmier Pro: captions en Clash con palabra activa amarilla, sombra sólida, entrada que sube desde abajo con rebote y desenfoque de movimiento, posiciones seguras para no tapar precios y captions manuales centrados. Úsala al subtitular un episodio de Clash of Clans o al ajustar su estilo.
---

# yt-edit-subtitulos

Skill compartida por Codex y Claude Code, enlazada desde sus carpetas de descubrimiento. En Claude Code se invoca con `/yt-edit-subtitulos`. Resuelve los nombres lógicos de herramientas contra el MCP disponible. La coordina `yt-edit-dinamica`. Cubre **solo el estilo V4**: clips de hasta 4 palabras con la animación de entrada de la prueba V5. La variante de una palabra por clip no forma parte de esta skill.

Referencia visual: `assets-compartidos/referencias/sub.jpg` (letras gruesas con contorno negro y sombra sólida). Los subtítulos completos solo se hacen si el usuario los pide; por defecto el canal usa frases destacadas.

## 1. Estilo

| Propiedad | Valor |
| --- | --- |
| Fuente | `Clash`, negrita (instalada en `~/Library/Fonts/Clash_Bold.otf.ttf`) |
| Tamaño y caja | 64, mayúsculas, centrado, sin fondo |
| Color | blanco `#FFFFFF`; palabra activa `#F2D90F` (`highlightPop`) |
| Contorno | negro, ancho 6 (se probó 10–11: demasiado grueso) |
| Sombra | negra sólida: `opacity` 1, `blur` 0, desplazamiento `y` 7 |
| Posición | centro `y = 0.86`; `y = 0.77` donde un precio o contador quede abajo |
| Tamaño de clip | máximo 4 palabras y 24 caracteres |

`update_text` rechaza nombres de fuente no instalados y devuelve las coincidencias. Impact, por ejemplo, no admite `bold: false`. Un salto de línea en `content` debe ser un salto real, no la secuencia `\n`.

## 2. Crear los captions

```
add_captions(trackIndex=<pista A2 de voz>, maxWords=4, maxCharacters=24,
  animation="highlightPop", highlightColor="#F2D90F",
  style={fontName:"Clash", bold:true, fontCase:"uppercase", color:"#FFFFFF", fontSize:64,
         alignment:"center", background:{enabled:false},
         outline:{enabled:true,color:"#000000",width:6},
         shadow:{enabled:true,color:"#000000",opacity:1,blur:0,offset:{x:0,y:7}}},
  transform={x:0.5, y:0.86})
```

- Apunta a la pista de **voz principal**, no a clips de grabaciones antiguas. Con varias pistas de audio, `trackIndex` es la que contiene la voz (relee `get_timeline`: los índices cambian al añadir pistas).
- La transcripción puede venir de caché. Si informa de un coste de créditos de transcripción, está permitido; no uses herramientas de generación.
- Los captions que cubran un dato del juego (precio, contador inferior) suben a `y = 0.77` con `update_text` sobre sus `clipIds`. Léelos con `get_timeline` y `captionDetail: true` por ventanas de frames (máximo 200 filas).
- Añadir captions crea una pista nueva arriba y desplaza los índices; usa IDs de pista (`manage_tracks`) y relee antes de cualquier llamada por índice.

## 3. Animación de entrada (receta V5 aplicada a clips de varias palabras)

Cada clip sube desde abajo con rebote ligero y desenfoque de movimiento, a 30 fps: sube 0.045, pasa 0.012 de largo, baja 0.004 y asienta; el desenfoque va de 14 px a 0; el fundido dura 2 fotogramas. Los clips cortos comprimen la entrada y los de 1–2 fotogramas no se animan.

```bash
echo '[{"id":"D5D2C867","duration":40,"x":0.262,"yf":0.802}]' \
 | python3 skills/yt-edit-subtitulos/scripts/caption_motion.py rows
```

Devuelve `position` (4 filas), `blur` (3 filas) y `fadeInFrames`. Aplícalo con `set_keyframes` (`position`, `blur`) por clip y un solo `set_clip_properties` con `fadeInFrames: 2` y `fadeInInterpolation: "smooth"` para todos los clips.

**`position` es la esquina superior izquierda y es absoluta.** Para `x` e `yf` finales:

- Lee la última fila de `position` que ya tiene el clip (con 6 decimales desde el `project.json` del paquete: `get_timeline` redondea a 3), o
- calcula una esquina centrada con el tamaño real del texto: `python3 skills/yt-edit-subtitulos/scripts/caption_motion.py sizes RUTA/project.json ID…` devuelve `x = 0.5 − ancho/2` e `yf = centroY − alto/2`. Solo se **lee** el paquete `.palmier` (`videos/VNNNN/palmier/proyecto.palmier`); nunca se escribe.

La posición final de cada clip debe quedar **igual que antes**. Con cientos de clips son cientos de llamadas: agrúpalas en lotes de 20–30 por turno o delega la tarea con la plantilla de `yt-edit-dinamica/references/delegacion.md`. No uses el preset `slideUp`: dura 1–2 fotogramas y no se configura.

## 4. Mantenimiento

- Cambiar tamaño, texto o fuente de un clip con keyframes lo **descentra**: recalcula `x`/`yf`. Cambiar solo el ancho del contorno no movió la posición.
- Un caption manual (por ejemplo `*Clip de antes*`) copiado de otro clip hereda su `x`: léelo con `sizes` y corrígelo para centrarlo en `x = 0.5`.
- Pueden convivir una pista completa **oculta** y una pista curada visible con solo las frases clave. Si el usuario ocultó o borró una pista, **no la reactives ni la reconstruyas**: pregunta. Tus propias pistas nuevas deben quedar visibles al terminar (`hidden: false`).
- Un agente delegado no debe eliminar pistas del usuario ni dejar ocultas las propias; revisa `hidden` en `get_timeline` al final.

## 5. Verificar

1. `inspect_timeline` con fotogramas consecutivos desde el inicio de un clip (+0, +2, +4, +6, +8): debe subir, pasar ligeramente de largo, estar borroso al principio y nítido y quieto al final, con velocidad no lineal.
2. Un clip corto (3–5 fotogramas), uno del tramo con precio y uno manual: posición final y centrado (centro x ≈ 0.5).
3. Reposo en momentos con datos del juego: los captions no deben tapar precios ni contadores.
4. `get_timeline` por ventanas: ningún clip con filas antiguas de 2 posiciones; la última fila coincide con la posición original.
5. Informa que solo verificaste fotogramas compuestos, no reproducción.
