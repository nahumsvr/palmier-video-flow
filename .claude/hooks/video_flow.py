#!/usr/bin/env python3
"""Hooks de Claude Code: sincronizar documentos y aportar contexto, sin editar Palmier."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "skills/yt-video-flow/scripts/video_flow.py"
EVENTS = {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop"}
PALMIER = re.compile(r"^mcp__palmier[-_]pro__(.+)$")
READ_TOOLS = {"get_timeline", "get_media", "get_transcript", "get_assets", "get_multicam",
              "inspect_media", "inspect_timeline", "inspect_color", "search_media", "list_models",
              "detect_scenes", "detect_beats", "send_feedback"}


def short(value, limit=240):
    """Keep context bounded and each user-authored value on one line."""
    return " ".join(str(value).split())[:limit]


def context(root, payload):
    """Mention explicit IDs or the episode cwd; otherwise list records without selecting one."""
    identifiers = list(dict.fromkeys(re.findall(r"\bV\d{4,}\b", payload.get("prompt", "").upper())))
    if not identifiers:
        cwd = Path(payload.get("cwd") or root).resolve()
        try:
            parts = cwd.relative_to(root / "videos").parts
        except ValueError:
            parts = ()
        if parts and re.fullmatch(r"V\d{4,}", parts[0]):
            identifiers = [parts[0]]
    if not identifiers:
        identifiers = [p.parent.name for p in sorted((root / "videos").glob("V*/estado.json"))]
    lines = ["Palmier Video Flow: calendario y bloques operativos sincronizados desde estado.json.",
             "Estos registros no seleccionan el proyecto del editor. Lee los documentos de la etapa solicitada y confirma Palmier con manage_project/list."]
    for identifier in identifiers[:5]:
        path = root / "videos" / identifier / "estado.json"
        if not path.is_file():
            lines.append(identifier + ": registro no encontrado; no crear otro si el pedido es retomar.")
            continue
        state = json.loads(path.read_text(encoding="utf-8"))
        activity = state["actividad"]
        lines.append("{} · {} — {} / {}. Fuente: videos/{}/estado.json; notas: videos/{}/notas.md.".format(
            identifier, short(state["nombre"], 100), state["etapa"], activity["estado"], identifier, identifier))
        lines.append("Siguiente paso registrado: " + short(state["siguiente_paso"]))
        for blockage in state["bloqueos"][:3]:
            lines.append("Bloqueo registrado: " + short(blockage))
        if (path.parent / "continuidad.md").is_file():
            lines.append("Continuidad local: videos/{}/continuidad.md (leer junto al estado actual).".format(identifier))
    if len(identifiers) > 5:
        lines.append("Hay más registros: consulta calendario.md e identifica el ID antes de trabajar.")
    return "\n".join(lines)


def run(root, payload):
    event = payload.get("hook_event_name")
    if event not in EVENTS:
        raise ValueError("Evento de hook no compatible")
    result = subprocess.run([sys.executable, str(HELPER), "--root", str(root), "calendar"],
                            capture_output=True, text=True, timeout=20)
    if result.returncode:
        raise ValueError("No se pudo sincronizar el flujo: " + short(result.stderr, 800))
    if event in {"SessionStart", "UserPromptSubmit"}:
        return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": context(root, payload)}}
    if event == "PreToolUse":
        return {"hookSpecificOutput": {"hookEventName": event, "additionalContext":
                "Calendario actualizado. Usa el proyecto vinculado al video solicitado; verifica ID y timeline antes de mutar Palmier."}}
    match = PALMIER.fullmatch(payload.get("tool_name", ""))
    if event == "PostToolUse" and match and match.group(1) not in READ_TOOLS:
        return {"hookSpecificOutput": {"hookEventName": event, "additionalContext":
                "Revisa la respuesta de Palmier. Registra IDs y resultado comprobado; tras cambiar el corte, actualiza snapshot y anclajes. Una llamada iniciada no demuestra éxito, escucha ni exportación completada."}}
    # PostToolUse local y Stop solo sincronizan. No bloquear el cierre ni marcar etapas.
    return None


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--root", type=Path, default=REPO_ROOT,
                     help="Workspace alternativo para pruebas; por defecto la raíz real del hook")
    args = cli.parse_args()
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("La entrada debe ser un objeto JSON")
        for key in ("hook_event_name", "prompt", "cwd", "tool_name"):
            if key in payload and not isinstance(payload[key], str):
                raise ValueError(key + " debe ser texto")
        output = run(args.root.expanduser().resolve(), payload)
        if output is not None:
            print(json.dumps(output, ensure_ascii=False))
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print("Palmier Video Flow hook: " + str(exc), file=sys.stderr)
        return 1  # Error visible, sin bloquear prompts de reparación ni crear bucles Stop.
    return 0


if __name__ == "__main__":
    sys.exit(main())
