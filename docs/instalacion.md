# Instalación

## 1. Requisitos

- **macOS y Palmier Pro instalado y abierto** para crear/editar proyectos mediante MCP.
- **Codex local o Claude Code:** app/CLI con acceso al workspace. Para Claude sigue también su [guía específica](claude-code.md).
- **Git y Python 3.9 o superior.** El helper usa la biblioteca estándar y funciona en macOS/Linux; no admite Windows nativo porque usa locks POSIX.
- **FFmpeg/ffprobe**, recomendado para inspeccionar streams, silencios y archivos exportados. Consulta sus [descargas oficiales](https://ffmpeg.org/download.html).

Comprueba lo que ya tienes:

```bash
git --version
python3 --version
ffprobe -version
```

La organización local y las pruebas funcionan sin Palmier. Para editar videos necesitas el editor y su conexión MCP.

## 2. Clonar y abrir

```bash
git clone https://github.com/nahumsvr/palmier-video-flow.git
cd palmier-video-flow
python3 skills/yt-video-flow/scripts/video_flow.py calendar
```

El último comando crea las carpetas compartidas y el calendario desde los registros existentes. Abre **la raíz de este clon** como carpeta principal de trabajo. Codex usa `AGENTS.md` y los enlaces de `.agents/skills/`. Claude Code usa `CLAUDE.md`, que importa `AGENTS.md`, y los enlaces de `.claude/skills/`. Ambos cargan las mismas skills y scripts. [Skills de Codex](https://learn.chatgpt.com/docs/build-skills), [instrucciones con AGENTS.md](https://developers.openai.com/codex/guides/agents-md), [skills de Claude Code y enlaces simbólicos](https://code.claude.com/docs/en/skills).

No hace falta copiar las skills a una carpeta global: el helper calcula el workspace desde su ubicación real. Mantén el clon en una ubicación persistente porque allí residirán los documentos y referencias de producción.

## 3. Conectar Palmier

Con Palmier abierto, registra su servidor en Codex CLI:

```bash
codex mcp add palmier-pro --url http://127.0.0.1:19789/mcp
```

En la app también puedes agregar un servidor **Streamable HTTP** en la configuración de MCPs con esa URL. Si el servidor ya está configurado, reutilízalo. La conexión es local y requiere que Palmier esté abierto. [Guía oficial de Palmier](https://www.palmier.io/docs/agent-and-mcp)

Para **Claude Code**, `.mcp.json` ya declara ese servidor como `palmier-pro` de tipo `http`. Ejecuta `claude` en el clon y revisa la conexión con `/mcp`. Claude Code puede solicitar su autorización nativa al cargar un servidor del proyecto; revisa la configuración local que está en el repositorio. No hace falta copiar la configuración global de Codex ni añadir el mismo servidor otra vez. [MCP de Claude Code](https://code.claude.com/docs/en/mcp).

Inicia una sesión en esta carpeta y pide:

```text
Usa el flujo de este repositorio y comprueba qué proyecto de Palmier está activo.
```

Debe poder listar proyectos y leer la línea de tiempo. Para pedir la skill explícitamente en Codex CLI puedes escribir `$yt-video-flow`; `AGENTS.md` también permite enrutar pedidos naturales al flujo. [Invocación de skills](https://learn.chatgpt.com/docs/build-skills)

En Claude Code escribe `/yt-video-flow` o `/yt-cut-hi`. Los hooks y la continuidad de episodios existentes están explicados en [Claude Code](claude-code.md).

## 4. Personalizar el canal

Edita `canal.md`: público, tono, preferencias visuales, formato y enlaces conocidos. Los valores iniciales son videos largos en español, énfasis selectivo, 1080p/30 fps para proyectos nuevos y zona `America/Mexico_City`. Los proyectos adoptados conservan su formato.

Si cambias el canal/tema, actualiza las instrucciones y plantillas que mencionan Clash of Clans. Esta versión está especializada en esa producción; cambiar solo el nombre de la carpeta no la convierte en una skill genérica.

## 5. Verificar

```bash
python3 -m unittest discover -s skills/yt-video-flow/scripts -p 'test_*.py' -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Los ensayos no generan episodios reales ni usan credenciales. Puedes abrir el calendario después y comenzar con «Crea un proyecto de video».

## Problemas habituales

| Problema | Cómo resolverlo |
| --- | --- |
| No aparece la skill | Abre la raíz del clon; revisa que `.agents/skills/` (Codex) o `.claude/skills/` (Claude) resuelva hacia `skills/`. Reinicia la sesión si no se detecta. |
| Palmier no responde | Comprueba que esté abierto y que el MCP use la URL local correcta; vuelve a vincular el proyecto de la sesión. |
| El helper escribe en otra carpeta | Ejecútalo desde este clon o especifica `--root /ruta/workspace` antes del subcomando. No copies solo el script: necesita sus plantillas. |
| Falta `canal.md` en otro workspace | Copia y adapta la configuración del canal antes de usar el agente allí; `--root` solo dirige el helper, no instala instrucciones en esa carpeta. |
| Calendario antiguo | Ejecuta `calendar`. Una fecha en YouTube no se conoce hasta que la informes. |
| Falta un archivo importado | Restablece su ruta persistente. Palmier puede referenciar archivos externos; no borres los crudos después de importar. |
| JSON o bloque generado inválido | Corrige el dato o el par de marcadores indicado. El helper conserva el calendario anterior si no puede regenerarlo correctamente. |
| Hook de Claude falla | Revisa Python/Git y `.claude/settings.json`; ejecuta el diagnóstico manual de la guía de Claude. Sus errores no bloquean los prompts de reparación. |
