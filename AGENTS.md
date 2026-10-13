# Producción de videos de Clash of Clans

- Para crear, adoptar, preparar, editar, revisar, exportar o registrar la publicación de un video, lee `skills/yt-video-flow/SKILL.md` y ejecuta solo las etapas solicitadas.
- Para cortar pausas y reunir ideas completas, usa `skills/yt-cut-hi/SKILL.md`; la skill de producción la reutiliza sin reemplazar su criterio editorial.
- Para una pasada de ritmo (encuadre, capítulos, zooms, subtítulos animados, efectos de sonido) lee `skills/yt-edit-dinamica/SKILL.md`; coordina `yt-edit-zooms`, `yt-edit-capitulos`, `yt-edit-subtitulos` y `yt-edit-sfx`. Trabaja siempre en una copia del timeline (`create_timeline from`), respeta lo que el usuario haya cambiado en Palmier y no gastes créditos (generación, máscaras mágicas) sin autorización.
- Antes de consultar fechas o trabajar en un video, ejecuta `python3 skills/yt-video-flow/scripts/video_flow.py calendar`. Consulta después su `estado.json`, los Markdown pertinentes y el estado real de Palmier.
- `videos/VNNNN/estado.json` es la fuente de verdad. `calendario.md` y los bloques señalados como generados se regeneran; no los edites directamente. Las notas y propuestas fuera de esos bloques se conservan.
- Actualiza el estado y el calendario al terminar una etapa, registrar un cambio o encontrar un bloqueo. No marques una acción como completada por haberla iniciado.
- Los originales y los archivos importados deben permanecer disponibles. No escribas dentro de paquetes `.palmier`, no muevas paquetes abiertos y no borres fuentes al archivar.
- Trabaja por etapas. Exportar requiere un pedido de exportación; programar/publicar en YouTube lo hace el usuario y se registra cuando informa el resultado. Las miniaturas las hace el usuario; propone tres composiciones.

## Mantenimiento y compatibilidad del repositorio

- Las instrucciones de producción son compartidas por Codex y Claude Code. `CLAUDE.md` importa este archivo; las skills canónicas están en `skills/`, enlazadas desde `.agents/skills/` y `.claude/skills/`. Edita el destino, no crees copias divergentes.
- Para cambios en herramientas, hooks o documentación, consulta `CONTRIBUTING.md` y ejecuta las suites allí indicadas. Las pruebas usan workspaces temporales y no deben modificar videos reales ni llamar a Palmier.
- Un cambio de compatibilidad no es una etapa nueva de edición. Conserva los estados comprobados, IDs y fuentes del episodio. Sus instrucciones y documentos de continuidad permanecen en `videos/VNNNN/`, fuera del repositorio público.
