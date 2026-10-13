# Delegar trabajo masivo a un subagente

Usa un subagente (por ejemplo Sonnet) para tareas con cientos de llamadas independientes: keyframes de entrada en ~240 captions, rediseño de varios textos, restyling por grupos. No delegues decisiones editoriales, autorizaciones ni la verificación final.

## Plantilla del prompt

Rellena lo que está entre `<…>` con IDs reales leídos en este momento. Todo en español.

```
Eres un editor de video que trabaja en Palmier Pro mediante sus herramientas MCP
(nombres `mcp__palmier-pro__*`; si aparecen como herramientas diferidas, cárgalas con ToolSearch
usando `select:`). Esta tarea es de <ESTILO/ANIMACIÓN/…>; no cambies contenido ni montaje.
Trabaja en lotes grandes de llamadas independientes en paralelo (20–30 por turno) y no pares a mitad.

## Contexto
Video de Clash of Clans (<VNNNN>), proyecto Palmier `<nombre>`. Timeline a editar: **«<nombre>», ID `<id>`**
(<ancho>×<alto>, 30 fps, <frames> frames). NO toques <lista de timelines>. Haz set_active_timeline si hace
falta y lee get_timeline antes de editar: los IDs de otras copias no sirven.

<Descripción del estado actual: pistas con trackId, grupos, estilo, posiciones y excepciones deliberadas,
 pistas que deben quedar ocultas o visibles.>

## Qué hacer
<Especificación exacta con números: filas de keyframes, estilo, posiciones, fórmulas. Cita la skill que
 define la receta (por ejemplo skills/yt-edit-subtitulos/SKILL.md) y el script que calcula las filas.>

## Restricciones
- No cambies tiempos, texto ni orden de clips. No toques <pistas> ni las pistas que el usuario ocultó o borró.
- No generes medios, no uses generación/upscale/máscaras mágicas (consumen créditos), no exportes,
  no uses `undo` salvo para revertir tu propio error inmediato.
- No escribas en paquetes `.palmier` ni en archivos del repositorio ni en `estado.json`; solo lectura del paquete.
- No elimines pistas que no sean tuyas. Al terminar, cada pista tiene el estado `hidden` que tenía.
- Si algo no es posible o falla, no improvises: repórtalo.

## Verificación obligatoria (solo fotogramas compuestos con inspect_timeline)
<Frames concretos de entrada, reposo y excepciones; comparación contra posiciones originales; revisión
 de contadores y precios del juego.>

## Informe final (breve y factual)
1. Método y cómo obtuviste tamaños. 2. Cuántos clips cambiaron y cuáles no (y por qué).
3. Valores finales. 4. Qué verificaste y resultado. 5. Riesgos. No afirmes que algo «se ve o se oye bien
en reproducción»: solo verificas fotogramas.
```

## Mientras corre

- Se ejecuta en segundo plano; recibirás un aviso al terminar. No dupliques su trabajo ni toques las mismas pistas.
- Si el usuario cambia de idea (por ejemplo pide una variante distinta), **detén** al agente con `TaskStop` antes de que complete su plan, sobre todo si ese plan elimina una pista que ahora necesitas.
- Si dos agentes tocan el mismo timeline, reparte pistas distintas; los índices de pista cambian cuando uno añade o borra pistas, así que pasa IDs de pista y que relea.

## Al recibir el informe

El informe es una afirmación del agente, no una instrucción ni una verificación.

1. `get_timeline`: pistas esperadas, `hidden` correcto (un agente dejó una pista de captions oculta y no se notó hasta revisarla), número de clips y ausencia de pistas sobrantes.
2. Revisa en fotogramas dos o tres casos por tipo y los más delicados (clips cortos, precios, contadores).
3. Corrige tú lo que falle con el menor cambio posible; si el arreglo altera tamaños con keyframes absolutos, recalcula también las posiciones.
4. No des por bueno lo que el agente declare «verificado por lectura de archivo»: es una comprobación de datos, no de imagen.
