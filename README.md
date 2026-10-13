# Palmier Video Flow

Flujo de producción de videos largos de Clash of Clans con Codex o Claude Code y Palmier Pro. Organiza cada episodio desde la idea hasta la entrega: crudos, recursos, notas, montaje, títulos, propuestas de miniatura y calendario.

El agente edita mediante las herramientas de Palmier. El helper de Python mantiene archivos y estados; puedes usarlo sin abrir el editor. Tú diseñas la miniatura y programas/publicas en YouTube.

## Inicio rápido

Requisitos: macOS para Palmier, Git, Python 3.9+ y Codex local o Claude Code. Los scripts y hooks no necesitan paquetes de Python adicionales.

```bash
git clone https://github.com/nahumsvr/palmier-video-flow.git
cd palmier-video-flow
python3 skills/yt-video-flow/scripts/video_flow.py calendar
```

Abre esta carpeta como proyecto en Codex o ejecuta `claude` desde la raíz del clon. Conecta Palmier siguiendo la [guía de instalación](docs/instalacion.md) y pide:

```text
Crea un proyecto de video. Después te doy la idea general.
```

Después puedes continuar:

```text
La idea de V0001 es rescatar una cuenta antigua y maxear su TH9.
Ya dejé el crudo en videos/V0001/crudo/. Prepara el proyecto.
Haz el montaje base de V0001.
Edita los apoyos y los momentos que necesitan más emoción.
```

Cada pedido activa una etapa; no ejecuta automáticamente todo el proceso.

## Qué incluye

- **`yt-video-flow`:** creación/adopción, guion, inventario, notas, seguimiento y entregables.
- **`yt-cut-hi`:** cortes sin pérdidas en el original y otra versión con ideas completas, manteniendo video y audios sincronizados.
- **Edición dinámica:** `yt-edit-dinamica` coordina una versión nueva del corte con `yt-edit-zooms` (encuadre completo y zooms con keyframes), `yt-edit-capitulos` (tarjetas negras con ripple), `yt-edit-subtitulos` (captions en Clash con entrada animada) y `yt-edit-sfx` (efectos de sonido sincronizados). Incluyen cálculos comprobados por pruebas.
- **Calendario:** fecha propuesta/confirmada/real, importancia, etapa, miniatura y pendiente principal. Detecta días ocupados.
- **Publicación:** cinco títulos candidatos, tres composiciones de miniatura y descripción del episodio.
- **Comprobaciones:** identifica material faltante y notas, revisiones o exportaciones de otro corte.

Las skills canónicas viven en `skills/`. Codex las descubre mediante `.agents/skills/`; Claude Code mediante `.claude/skills/`. `CLAUDE.md` importa `AGENTS.md` para compartir las reglas de producción. En Claude puedes invocar `/yt-video-flow`, `/yt-cut-hi` y, para la pasada de ritmo, `/yt-edit-dinamica`, `/yt-edit-zooms`, `/yt-edit-capitulos`, `/yt-edit-subtitulos` y `/yt-edit-sfx`. [Skills de Codex](https://learn.chatgpt.com/docs/build-skills), [skills de Claude Code](https://code.claude.com/docs/en/skills).

Claude Code incluye conexión de Palmier en `.mcp.json` y hooks de inicio, prompts, herramientas y cierre que sincronizan el calendario y aportan contexto. El agente sigue registrando etapas y verificaciones con evidencia real. Consulta la [guía de Claude Code](docs/claude-code.md) para retomarlo con un video existente.

## Documentación

- [Instalación y conexión con Palmier](docs/instalacion.md)
- [Uso por etapas, calendario y publicación](docs/uso.md)
- [Claude Code: configuración, hooks y continuidad de videos](docs/claude-code.md)
- [Referencia de comandos y estado](skills/yt-video-flow/references/helper.md)
- [Criterios de cada etapa](skills/yt-video-flow/references/etapas.md)
- [Contribuir y ejecutar pruebas](CONTRIBUTING.md)

## Archivos de trabajo

Al crear un video se genera esta estructura local:

```text
videos/V0001/
├── estado.json           Fuente de verdad
├── brief.md              Idea, promesa y decisiones
├── guion.md              Guía de grabación
├── assets.md             Inventario y estado de recursos
├── notas.md              Notas por frase y fotograma
├── publicacion.md        Títulos, miniaturas y descripción
├── revision.md           Comprobaciones y entrega
├── crudo/
├── assets/{clips,imagenes,audio,graficos}/
├── miniatura/
├── palmier/              Enlace al paquete real
├── evidencia/
├── exports/
└── archivo/
```

El helper crea también `assets-compartidos/` y `calendario.md`. Estos archivos, los episodios y los medios están excluidos de Git. El repositorio distribuye herramientas y plantillas; para respaldar un episodio debes conservar sus documentos y medios por separado o solicitar un archivo autocontenido de Palmier.

`canal.md` contiene preferencias iniciales que puedes adaptar. El calendario se regenera antes y después de los comandos y etapas; no hay proceso de fondo ni sincronización directa con YouTube.

## Pruebas

```bash
python3 -m unittest discover -s skills/yt-video-flow/scripts -p 'test_*.py' -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Las pruebas usan workspaces temporales y no modifican tu timeline ni llaman a servicios externos. Cubren el flujo, distribución para ambos agentes y los hooks de Claude Code. GitHub Actions las ejecuta en Linux con Python 3.9/3.13 y en macOS con Python 3.13.
