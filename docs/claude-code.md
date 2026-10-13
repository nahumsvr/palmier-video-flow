# Claude Code

El mismo clon funciona con Codex y Claude Code. Los episodios siguen en `videos/VNNNN/` y conservan estado, historial, fuentes y referencias a Palmier. Cambiar de agente no crea otro registro ni otra versión del video.

## Archivos compartidos

| Archivo | Función |
| --- | --- |
| `AGENTS.md` | Reglas comunes de producción y mantenimiento |
| `CLAUDE.md` | Importa `@AGENTS.md` y añade instrucciones de Claude |
| `skills/` | Fuente única de skills, scripts, referencias y plantillas |
| `.agents/skills/` | Enlaces de descubrimiento para Codex |
| `.claude/skills/` | Enlaces de descubrimiento para Claude Code |
| `.claude/settings.json` | Hooks del proyecto |
| `.claude/hooks/video_flow.py` | Adaptador de eventos a `calendar` y contexto local |
| `.mcp.json` | Servidor `palmier-pro`, HTTP en `127.0.0.1:19789/mcp` |
| `.claude/settings.local.json` | Ajustes privados de esta computadora, ignorados por Git |

Claude Code admite enlaces de carpetas de skills y imports `@ruta` de instrucciones. Los enlaces llevan al mismo contenido y no requieren instalación global. `agents/openai.yaml` sigue siendo metadata de Codex; Claude usa `SKILL.md`. [Skills oficiales](https://code.claude.com/docs/en/skills), [memoria e imports](https://code.claude.com/docs/en/memory).

## Inicio

Instala Claude Code siguiendo su [guía oficial](https://code.claude.com/docs/en/setup). Necesitas también Git y Python 3.9+, y Palmier abierto en macOS para editar. Los helpers y pruebas funcionan en macOS/Linux sin dependencias adicionales; no admiten Windows nativo.

Desde la raíz del clon:

```bash
claude --version
python3 skills/yt-video-flow/scripts/video_flow.py calendar
claude
```

En Claude revisa `/mcp`, `/context` y los comandos `/yt-video-flow`, `/yt-cut-hi` y los de edición dinámica (`/yt-edit-dinamica`, `/yt-edit-zooms`, `/yt-edit-capitulos`, `/yt-edit-subtitulos`, `/yt-edit-sfx`). `.mcp.json` ya contiene el servidor del editor; no ejecutes `mcp add` otra vez con el mismo nombre. Claude Code puede pedir aprobación nativa de la configuración de un proyecto nuevo. La conexión usa el servidor local de Palmier y no necesita secretos en el repositorio. [Configuración MCP por proyecto](https://code.claude.com/docs/en/mcp).

Si prefieres configurar Palmier fuera del proyecto, el equivalente es:

```bash
claude mcp add --transport http --scope local palmier-pro http://127.0.0.1:19789/mcp
```

Elige esa alternativa solo cuando no utilices la declaración del clon. Si cambias el nombre del servidor, adapta los matchers de hooks que contienen `palmier[-_]pro`.

## Hooks

Todos llaman al helper canónico con la raíz real del clon. El comando de configuración obtiene esa raíz con `git -C "$CLAUDE_PROJECT_DIR" rev-parse --show-toplevel`; funciona con rutas con espacios y cuando Claude aporta una carpeta anidada como directorio de proyecto. No depende de `jq` ni de rutas personales.

| Evento | Comportamiento |
| --- | --- |
| `SessionStart` | Regenera el calendario y aporta registros/continuidad al iniciar, retomar, limpiar o compactar una sesión |
| `UserPromptSubmit` | Regenera y aporta contexto de los IDs mencionados, de la carpeta del episodio o del inventario de registros |
| `PreToolUse` de Palmier | Refresca el calendario y recuerda comprobar proyecto/timeline antes de mutar |
| `PostToolUse` de Edit/Write/Bash/Palmier | Refresca los bloques; tras operaciones de Palmier recuerda registrar resultados, snapshot y anclajes |
| `Stop` | Última regeneración del calendario; termina sin bloquear el cierre |

La selección de contexto no abre proyectos: un ID explícito del prompt tiene prioridad sobre el cwd. Si no hay un ID ni carpeta de episodio, muestra hasta cinco registros y deja al agente identificar el correcto. No guarda un «video activo» global que pudiera retargetear otras sesiones. Los mensajes de contexto son breves y no vuelcan transcripciones, historial ni listas de clips.

Los hooks no llaman a Palmier, no cambian campos de `estado.json` y no marcan etapas o revisiones. El agente debe guardar `begin`/`update`/`snapshot` con los resultados reales. Tampoco autorizan exportaciones, generaciones pagadas, miniaturas ni publicaciones. Usa el helper después de cambios hechos fuera de Claude; no hay vigilancia de fondo.

Cada hook tiene timeout de 30 s y su llamada al helper, 20 s. Los errores se reportan por stderr con código 1; no bloquean prompts de reparación ni provocan bucles `Stop`. Si falla la regeneración, corrige el dato o entorno antes de trabajar en el video. El helper conserva el calendario anterior cuando el estado no puede validarse. [Referencia oficial de hooks y contratos JSON](https://code.claude.com/docs/en/hooks).

## Retomar un video existente

Abre la raíz de este clon y pide, por ejemplo:

```text
Retoma V0001. Lee estado.json, notas.md y continuidad.md si existe.
Comprueba el proyecto real de Palmier y retoma su timeline de edición registrado.
Ejecuta solamente la etapa que te pida.
```

Claude debe listar proyectos, vincular el ID correcto si hace falta y releer timeline/medios. Una revisión audiovisual anterior solo vale para la firma registrada. Si cambia la estructura, vuelve a revisar los anclajes y las comprobaciones afectadas. Alternar entre agentes requiere releer el editor porque la otra sesión puede haber cambiado el corte.

Puedes trabajar con archivos dentro de `videos/VNNNN/`; el helper debe ejecutarse por su ruta desde la raíz o con la ruta relativa `../../skills/yt-video-flow/scripts/video_flow.py`. Iniciar Claude desde la raíz es la opción recomendada para cargar toda la configuración. Un `CLAUDE.md` local del episodio puede importar `@../../CLAUDE.md` y orientar la continuidad.

Si las fuentes adoptadas están fuera del clon, conserva sus enlaces y rutas. Autoriza esas carpetas en tu sesión con `--add-dir /ruta/de/las/fuentes` o mediante `permissions.additionalDirectories` en `.claude/settings.local.json`; no muevas paquetes abiertos. Los permisos personales no se versionan. El MCP sigue siendo quien edita el paquete nativo. [Directorios adicionales y configuración](https://code.claude.com/docs/en/settings).

Para trabajar en un episodio local usa el clon que contiene sus registros y fuentes. Un worktree nuevo o clon descargado desde GitHub no incluye `videos/`, porque sus documentos y medios están ignorados. Trasladar el episodio necesita un respaldo separado de esos documentos y de las fuentes, además del proyecto Palmier.

## Diagnóstico y pruebas

Diagnóstico local del hook, desde la raíz:

```bash
printf '%s\n' '{"hook_event_name":"SessionStart","cwd":".","source":"startup"}' | python3 .claude/hooks/video_flow.py
python3 -m unittest discover -s skills/yt-video-flow/scripts -p 'test_*.py' -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
git diff --check
```

El primer comando refresca el calendario real y devuelve contexto JSON. Las suites usan workspaces temporales: prueban regeneración, continuidad, ambos formatos de prefijo MCP, rutas con espacios, cwd anidado, estado inválido y preservación de notas/estados. No lanzan un modelo de Claude, no consumen tokens y no llaman al editor. La reproducción audiovisual requiere reproducción real o revisión explícita del usuario, según la skill.

Para comprobar la configuración con el CLI instalado puedes ejecutar `claude doctor`. Para comprobar la conexión del editor, usa `/mcp` dentro de una sesión y pide `manage_project/list`; una configuración JSON válida no demuestra por sí sola que Palmier esté abierto y conectado.
