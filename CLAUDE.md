@AGENTS.md

## Claude Code

- Las skills compartidas viven en `skills/`; `.claude/skills/` las enlaza. Puedes invocarlas con `/yt-video-flow`, `/yt-cut-hi`, `/yt-edit-dinamica`, `/yt-edit-zooms`, `/yt-edit-capitulos`, `/yt-edit-subtitulos` y `/yt-edit-sfx`, o mediante pedidos naturales. Mantén el criterio editorial de esas skills.
- Los hooks de `.claude/settings.json` refrescan el calendario y aportan contexto local. No eligen un proyecto de Palmier ni registran etapas, revisiones o exportaciones por ti. Después de una operación, registra su resultado real con el helper.
- `.mcp.json` conecta `palmier-pro` por HTTP local. Identifica las herramientas disponibles por su nombre lógico y esquema actual; el prefijo MCP puede variar entre agentes. Consulta `/mcp` si no están disponibles.
- Para retomar un video, lee `videos/VNNNN/estado.json`, sus notas y, si existe, `continuidad.md`; confirma el proyecto y timeline reales en Palmier. Una sesión nueva no hereda el contexto de Codex.
- Ejecuta los comandos del README desde la raíz del repositorio. Si trabajas dentro de un episodio, usa rutas desde esa carpeta o una ruta absoluta al helper. La guía específica está en `docs/claude-code.md`.
