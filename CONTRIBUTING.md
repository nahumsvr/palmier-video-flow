# Contribuir

Trabaja en una rama breve desde `main`, con un propósito por cambio. Usa Conventional Commits, por ejemplo `docs(usage): explain publication tracking` o `fix(calendar): preserve confirmed dates`.

## Comprobaciones

```bash
python3 -m unittest discover -s skills/yt-video-flow/scripts -p 'test_*.py' -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
git diff --check
```

Las pruebas del flujo cubren workspaces temporales, reservas, estados de recursos, anclajes y entregas. Las del repositorio comprueban distribución, enlaces, ejemplos, el planificador de rangos y los cálculos de las skills de edición (`tests/test_edit_helpers.py`: filas de zoom, keyframes de captions, tarjetas de capítulo y plan de efectos). No necesitan Palmier ni acceso a Internet; no prueban la calidad audiovisual de una edición real.

`tests/test_claude_hooks.py` ejecuta los hooks con eventos JSON reales en workspaces temporales. Comprueba regeneración, contexto al retomar y compactar, selección por ID/carpeta, preservación del estado y notas, errores sin bucles de cierre, y los comandos distribuidos en un clon con espacios y cwd anidado. No inicia un modelo de Claude ni consume tokens. CI ejecuta ambas suites en Linux con Python 3.9/3.13 y macOS con Python 3.13.

Mantén una sola copia de las skills en `skills/`. Las entradas de `.agents/skills/` y `.claude/skills/` son enlaces relativos. `CLAUDE.md` importa `AGENTS.md`; cambios en reglas compartidas van allí. Cambios en eventos de hook o el transporte MCP deben actualizar `.claude/settings.json`, `.mcp.json`, pruebas y `docs/claude-code.md`.

Conserva la fuente de verdad y los bloques editoriales del usuario. Para cambios de esquema define cómo se conservarán registros existentes y agrega una prueba del comportamiento. Si cambias comandos, actualiza guías y ejemplos.

Los episodios y medios son datos locales ignorados. Stagea rutas explícitas de herramientas/documentación y revisa el diff antes de guardar. No publiques rutas personales, transcripciones reales ni credenciales en fixtures.

No se eligió una licencia de distribución todavía. No añadas ni cambies una licencia sin decisión del titular.
