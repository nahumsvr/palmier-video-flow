---
name: yt-edit-sfx
description: Coloca efectos de sonido sincronizados en Palmier Pro con los archivos de assets-compartidos/efectos: whooshes en zooms y cortes, impacto en tarjetas de capítulo, clics en cifras clave, con volúmenes que dejan la voz al frente y sin efectos duplicados. Úsala al dar cadencia sonora a una edición de Clash of Clans o al sincronizar efectos tras mover clips.
---

# yt-edit-sfx

Skill compartida por Codex y Claude Code, enlazada desde sus carpetas de descubrimiento. En Claude Code se invoca con `/yt-edit-sfx`. Resuelve los nombres lógicos de herramientas contra el MCP disponible. La coordina `yt-edit-dinamica`. Para música, monedas, martillos o efectos de meme no hay material local: ver «Lo que falta».

## 1. Biblioteca disponible

Carpeta `assets-compartidos/efectos/Sound Effects/` (21 archivos MP3: 17 whooshes y 4 de cámara). Catálogo con duraciones y usos en [references/catalogo.md](references/catalogo.md). **Antes de importar, revisa `get_media`** (carpeta «Efectos») y `canal.md`: si ya están, reutiliza sus `mediaRef`. Los IDs son propios de cada proyecto.

```
import_media(source={path:"/ruta/absoluta/assets-compartidos/efectos/Sound Effects"}, folder="Efectos")
```

Importar no cuesta créditos. La carpeta del repositorio solo contiene lo que el usuario puso; compruébala antes de afirmar que existe una biblioteca (a veces hay dos carpetas `assets-compartidos`: la del clon y la del workspace superior).

## 2. Roles, volumen y adelanto

| Rol | Efecto | Adelanto | Volumen |
| --- | --- | --- | --- |
| `impacto_capitulo` | Camera Shutter 2 | 0 | −8 dB |
| `salida_capitulo` | Quick Whoosh / 2 | 0 (a los 24 fotogramas de la tarjeta) | −14 dB |
| `zoom` | Whoosh 3, 4, 1, 2 (rotar) | 0 (al inicio del zoom) | −14 dB |
| `corte` | Whoosh 8, 7, 6, 9, Swish (rotar) | 2 fotogramas antes del corte | −18 dB |
| `cifra` | Camera Click | 0 (en la palabra de la cifra) | −12 dB |
| `remate` | Camera Shutter | 0 | −14 dB |
| `impacto_grande` | Jet Whoosh | 4 antes del zoom fuerte | −12 dB |
| `transicion` | Smooth Whoosh / Whoosh Wind / Remembering | 2 antes | −14 dB |

El agente no puede escuchar: los volúmenes son un punto de partida conservador para que la voz siga al frente. Deja la mezcla final al oído del usuario.

## 3. Planificar y colocar

```bash
echo '{"min_gap":12,"media":{"5 - Camera Click":"F6DEABC9","3 - Whoosh 3":"7577A628"},
  "events":[{"frame":1289,"role":"cifra"},{"frame":1215,"role":"zoom"}]}' \
 | python3 skills/yt-edit-sfx/scripts/sfx_plan.py
```

Devuelve `add_clips_entries` (para una sola llamada a `add_clips` con `trackIndex` de la pista SFX en **todas** las entradas), `volume_groups` (frames por volumen para `set_clip_properties`), `missing_effects` y `warnings` por repeticiones demasiado juntas.

1. Crea o reutiliza una pista de audio llamada «SFX» (`manage_tracks`). Los índices cambian cuando se añaden o quitan pistas arriba: relee `get_timeline` antes de `add_clips`.
2. `add_clips` deja cada efecto en 0 dB: **fija el volumen enseguida** (`set_clip_properties volumeDb`, una llamada por grupo de volumen).
3. Sincroniza con el evento: el inicio del zoom, la palabra de la cifra o la tarjeta, no con el corte de la voz. Un zoom que empieza 16 fotogramas después del inicio de su clip lleva el efecto en ese fotograma.

## 4. Reglas de uso

- Un efecto por evento; no apiles dos whooshes a menos de ~12 fotogramas. Evita repetir el mismo archivo en eventos seguidos (rotar la lista).
- No pongas efectos sobre la voz en frases importantes ni en cada subtítulo. Cadencia alta no significa constante: prioriza zooms a datos, tarjetas, cifras y remates.
- Al mover una imagen o un clip con zoom, **mueve también su efecto**: en V0001 un Jet Whoosh quedó 60 fotogramas después del zoom tras mover la imagen, y había uno duplicado.
- Si hay ripple (tarjetas insertadas, cortes), los efectos de una pista con `syncLocked` se desplazan solos; comprueba que ninguno quede cortado a la mitad por una inserción.
- El usuario puede borrar efectos al curar la edición: no los restituyas sin pedirlo.

## 5. Lo que falta

- **Música de fondo**: `assets-compartidos/musica` suele estar vacía. Se puede aportar o generar con Palmier.
- **Monedas, elixir, martillo, gritos y efectos de meme**: la biblioteca solo tiene whooshes y sonidos de cámara.
- Generar audio (`generate_audio`) y otros medios consume créditos: **requiere autorización explícita del usuario** y, si es necesario, su alcance (cantidad y tipo). Un saldo suficiente no autoriza el gasto.
- Palmier no tiene compresor ni ecualizador de voz; solo `denoise_audio` local. No alteres la voz sin pedirlo.

## 6. Verificar

`get_timeline` de la pista SFX: cantidad, frames, volúmenes y huecos. Comprueba que cada efecto coincide con su evento (zoom, tarjeta, cifra) y que no hay dos iguales seguidos. Registra la lista en las notas del episodio.
