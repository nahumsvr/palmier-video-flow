#!/usr/bin/env python3
"""Registro local de producción. No modifica Palmier ni publica en YouTube."""
import argparse
import copy
from datetime import date, datetime, timedelta, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = SKILL_ROOT.parents[1]
ZONE = ZoneInfo("America/Mexico_City")
STAGES = ("idea", "definicion", "grabacion", "preparacion", "montaje", "edicion",
          "revision", "listo", "exportacion", "exportado", "programado", "publicado",
          "archivo", "archivado")
RESOURCE_STATES = {
    "falta_obtenerlo": "Falta obtenerlo",
    "tenemos_no_importado": "Lo tenemos, no importado",
    "importado": "Ya importado",
    "en_video": "Ya en el video",
}
FOLDERS = ("crudo", "assets/clips", "assets/imagenes", "assets/audio", "assets/graficos",
           "miniatura", "palmier", "evidencia", "exports", "archivo")
DOCUMENTS = ("brief", "guion", "assets", "notas", "publicacion", "revision")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def video_id(value):
    require(isinstance(value, str) and re.fullmatch(r"V\d{4,}", value), "ID inválido: usa V0001, V0002…")
    return value


def parse_day(value):
    require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value), "Fecha: usa YYYY-MM-DD")
    return date.fromisoformat(value)


def parse_instant(value):
    require(isinstance(value, str), "La fecha con hora debe ser texto ISO 8601")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None and parsed.utcoffset() is not None,
            "Programación/publicación requieren hora y offset, por ejemplo 2026-10-10T18:00:00-06:00")
    return parsed


def local_day(value):
    return parse_instant(value).astimezone(ZONE).date().isoformat()


def resolve_file(root, state, value):
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / "videos" / state["id"] / path


def initial_state(identifier, name, idea):
    stamp = now()
    return {
        "schema_version": 1, "id": identifier, "nombre": name, "idea": idea,
        "etapa": "idea", "creado_en": stamp, "actualizado_en": stamp,
        "prioridad": {"nivel": "media", "motivo": "Episodio habitual; propuesta inicial.", "confirmada": False},
        "bloqueos": [], "siguiente_paso": "Definir la idea y la guía de grabación.",
        "actividad": {"etapa": None, "estado": "inactiva", "inicio": None},
        "fechas": {"propuesta": None, "confirmada": None, "programada": None, "publicada": None},
        "youtube": {"url": None},
        "miniatura": {"estado": "sin_iniciar", "ruta": None},
        "publicacion": {"titulo_elegido": None, "descripcion_revisada": False},
        "palmier": {"project_id": None, "nombre": None, "ruta": None,
                    "timelines": {"original": None, "montaje": None, "edicion": None, "final": None},
                    "settings": {"width": 1920, "height": 1080, "fps": 30},
                    "observado": {"timeline_id": None, "total_frames": None, "firma": None}},
        "recursos": [],
        "notas": {"timeline_id": None, "firma": None},
        "revision": {"estructura": False, "audiovisual": False, "firma": None, "evidencia": None},
        "exportacion": {"estado": "sin_exportar", "job_id": None, "ruta": None,
                        "timeline_id": None, "firma": None, "verificado": False},
        "archivo": {"estado": "pendiente", "ruta": None, "verificado": False},
        "historial": [],
    }


def validate(state):
    require(isinstance(state, dict), "El estado debe ser un objeto JSON")
    identifier = video_id(state.get("id"))
    expected = initial_state(identifier, "", "")
    require(set(state) == set(expected), "Campos de estado faltantes o desconocidos")
    require(state["schema_version"] == 1, "Versión de esquema no compatible")
    require(state["etapa"] in STAGES, "Etapa desconocida")
    for key in ("nombre", "idea", "siguiente_paso", "creado_en", "actualizado_en"):
        require(isinstance(state[key], str), key + " debe ser texto")
    require(bool(state["nombre"].strip()), "El nombre no puede estar vacío")
    parse_instant(state["creado_en"])
    parse_instant(state["actualizado_en"])
    require(isinstance(state["bloqueos"], list) and all(isinstance(x, str) and x.strip() for x in state["bloqueos"]),
            "Los bloqueos deben ser una lista de textos no vacíos")
    for key in ("prioridad", "actividad", "fechas", "youtube", "miniatura", "publicacion",
                "palmier", "notas", "revision", "exportacion", "archivo"):
        require(isinstance(state[key], dict) and set(state[key]) == set(expected[key]), "Campos inválidos en " + key)
    require(state["prioridad"]["nivel"] in ("alta", "media", "baja"), "Prioridad desconocida")
    require(isinstance(state["prioridad"]["motivo"], str), "Motivo de prioridad inválido")
    require(type(state["prioridad"]["confirmada"]) is bool, "prioridad.confirmada debe ser booleano")
    require(state["actividad"]["estado"] in ("inactiva", "en_curso", "completada", "bloqueada", "parcial"), "Actividad inválida")
    require(state["actividad"]["etapa"] is None or state["actividad"]["etapa"] in STAGES, "Etapa de actividad inválida")
    if state["actividad"]["inicio"] is not None:
        parse_instant(state["actividad"]["inicio"])
    for key, value in state["fechas"].items():
        if value is not None:
            (parse_day if key in ("propuesta", "confirmada") else parse_instant)(value)
    require(state["miniatura"]["estado"] in ("sin_iniciar", "en_diseno", "lista"), "Estado de miniatura inválido")
    for key in ("descripcion_revisada",):
        require(type(state["publicacion"][key]) is bool, key + " debe ser booleano")
    title = state["publicacion"]["titulo_elegido"]
    require(title is None or isinstance(title, str) and bool(title.strip()), "Título elegido inválido")
    for key in ("estructura", "audiovisual"):
        require(type(state["revision"][key]) is bool, "revision." + key + " debe ser booleano")
    require(type(state["exportacion"]["verificado"]) is bool and type(state["archivo"]["verificado"]) is bool,
            "verificado debe ser booleano")
    require(state["exportacion"]["estado"] in ("sin_exportar", "en_proceso", "completada", "fallida"), "Exportación inválida")
    require(state["archivo"]["estado"] in ("pendiente", "en_proceso", "completado", "fallido"), "Archivo inválido")
    palmier = state["palmier"]
    for key in ("settings", "timelines", "observado"):
        require(isinstance(palmier[key], dict) and set(palmier[key]) == set(expected["palmier"][key]), "palmier." + key + " inválido")
    for key in ("width", "height", "fps"):
        require(type(palmier["settings"][key]) in (int, float) and math.isfinite(palmier["settings"][key]) and palmier["settings"][key] > 0,
                "Settings Palmier inválidos")
    for item in (state["notas"], state["revision"], state["exportacion"], palmier["observado"]):
        require(item["firma"] is None or isinstance(item["firma"], str) and re.fullmatch(r"[0-9a-f]{64}", item["firma"]), "Firma inválida")
    for key, container in (("ruta", state["miniatura"]), ("ruta", palmier), ("ruta", state["exportacion"]),
                           ("ruta", state["archivo"]), ("evidencia", state["revision"])):
        require(container[key] is None or isinstance(container[key], str) and bool(container[key]), "Ruta inválida")
    url = state["youtube"]["url"]
    if url is not None:
        require(isinstance(url, str), "URL inválida")
        parsed = urlparse(url)
        require(parsed.scheme == "https" and parsed.hostname in ("youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"),
                "Usa una URL HTTPS de YouTube")
    require(isinstance(state["recursos"], list), "recursos debe ser una lista")
    seen = set()
    for resource in state["recursos"]:
        require(isinstance(resource, dict), "Recurso inválido")
        require(isinstance(resource.get("id"), str) and re.fullmatch(r"M\d{2,}", resource["id"]), "ID de recurso inválido")
        require(resource["id"] not in seen, "ID de recurso duplicado")
        seen.add(resource["id"])
        require(isinstance(resource.get("nombre"), str) and bool(resource["nombre"]), "Recurso sin nombre")
        require(resource.get("estado") in RESOURCE_STATES, "Estado de recurso inválido")
        require(type(resource.get("comprobado", False)) is bool and type(resource.get("imprescindible", False)) is bool,
                "comprobado/imprescindible deben ser booleanos")
        for key in ("ruta", "media_ref", "asset_ref", "timeline_id", "notas", "rol"):
            require(resource.get(key) is None or isinstance(resource[key], str), "Campo de recurso inválido: " + key)
        require(isinstance(resource.get("clip_ids", []), list) and all(isinstance(x, str) for x in resource.get("clip_ids", [])), "clip_ids inválidos")
        if resource["estado"] != "falta_obtenerlo":
            require(resource.get("comprobado") is True, "Inspecciona el contenido antes de marcar disponible " + resource["id"])
        if resource["estado"] == "tenemos_no_importado":
            require(bool(resource.get("ruta")), "El recurso local necesita ruta")
        if resource["estado"] in ("importado", "en_video"):
            require(bool(resource.get("media_ref") or resource.get("asset_ref")), "El recurso importado necesita media_ref o asset_ref")
        if resource["estado"] == "en_video":
            require(bool(resource.get("clip_ids")) and bool(resource.get("timeline_id")), "El recurso colocado necesita clip_ids y timeline_id")
    require(isinstance(state["historial"], list), "Historial inválido")
    if state["etapa"] == "programado":
        require(bool(state["fechas"]["programada"]), "Programado requiere fecha/hora real informada")
    if state["etapa"] == "publicado":
        require(bool(state["fechas"]["publicada"] and url), "Publicado requiere fecha/hora y URL reales")
    if state["etapa"] == "exportado":
        require(state["exportacion"]["estado"] == "completada" and state["exportacion"]["verificado"], "Exportado requiere resultado completado y verificado")
    if state["etapa"] == "archivado":
        require(state["archivo"]["estado"] == "completado" and state["archivo"]["verificado"], "Archivado requiere respaldo completado y verificado")


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_text(encoding="utf-8") == content:
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=str(path.parent), delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def write_json(path, value):
    atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def load_states(root):
    states = []
    for path in sorted((root / "videos").glob("V*/estado.json")):
        state = json.loads(path.read_text(encoding="utf-8"))
        validate(state)
        require(path.parent.name == state["id"], "ID/carpeta no coinciden en " + str(path))
        states.append(state)
    return states


def load_state(root, identifier):
    path = root / "videos" / video_id(identifier) / "estado.json"
    require(path.is_file(), "Video no registrado: " + identifier)
    state = json.loads(path.read_text(encoding="utf-8"))
    validate(state)
    return state


def deep_merge(target, patch):
    require(isinstance(patch, dict), "El parche debe ser un objeto JSON")
    for key, value in patch.items():
        require(key in target, "Campo desconocido: " + key)
        if isinstance(target[key], dict):
            require(isinstance(value, dict), "El campo " + key + " requiere un objeto")
            deep_merge(target[key], value)
        else:
            target[key] = copy.deepcopy(value)


def reservation_day(state):
    dates = state["fechas"]
    if dates["publicada"]:
        return local_day(dates["publicada"])
    if dates["programada"]:
        return local_day(dates["programada"])
    return dates["confirmada"] or dates["propuesta"]


def next_free_day(states, identifier, start):
    occupied = {reservation_day(x) for x in states if x["id"] != identifier}
    while start.isoformat() in occupied:
        start += timedelta(days=1)
    return start.isoformat()


def nonempty_file(root, state, value):
    if not value:
        return False
    path = resolve_file(root, state, value)
    return path.is_file() and path.stat().st_size > 0


def check_state(root, state):
    validate(state)
    problems = list(state["bloqueos"])
    warnings = []
    palmier = state["palmier"]
    observed = palmier["observado"]
    if not palmier["ruta"]:
        warnings.append("Proyecto Palmier todavía no vinculado.")
    elif not resolve_file(root, state, palmier["ruta"]).exists():
        warnings.append("No está disponible la ruta del proyecto Palmier.")
    for resource in state["recursos"]:
        label = resource["id"] + " — " + resource["nombre"]
        if resource.get("ruta") and not resolve_file(root, state, resource["ruta"]).exists():
            warnings.append("Archivo de recurso no disponible: " + label)
            if resource.get("imprescindible"):
                problems.append("Falta el archivo imprescindible " + label)
        if resource.get("imprescindible") and (resource["estado"] != "en_video" or resource.get("timeline_id") != observed["timeline_id"]):
            problems.append("Apoyo imprescindible no confirmado en el corte actual: " + label)
    signature = observed["firma"]
    if not signature:
        problems.append("Falta snapshot del corte actual.")
    notes = state["notas"]
    if signature and (notes["firma"] != signature or notes["timeline_id"] != observed["timeline_id"]):
        problems.append("Notas/anclajes pendientes de revisar para el corte actual.")
    review = state["revision"]
    if not review["estructura"]:
        problems.append("Revisión estructural pendiente.")
    if not review["audiovisual"]:
        problems.append("Reproducción audiovisual pendiente de revisión real.")
    if signature and review["firma"] != signature:
        problems.append("La revisión no corresponde al corte actual.")
    if not nonempty_file(root, state, review["evidencia"]):
        problems.append("Falta evidencia de la revisión.")
    export = state["exportacion"]
    if export["estado"] != "completada" or not export["verificado"] or not nonempty_file(root, state, export["ruta"]):
        problems.append("Falta exportación completada, verificada y disponible.")
    if signature and (export["firma"] != signature or export["timeline_id"] != observed["timeline_id"]):
        problems.append("La exportación no corresponde al corte actual.")
    if not state["publicacion"]["titulo_elegido"]:
        problems.append("Título pendiente de elegir.")
    if not state["publicacion"]["descripcion_revisada"]:
        problems.append("Descripción pendiente de revisión.")
    if state["miniatura"]["estado"] != "lista" or not nonempty_file(root, state, state["miniatura"]["ruta"]):
        problems.append("Miniatura pendiente o archivo final no disponible.")
    if not (state["fechas"]["confirmada"] or state["fechas"]["programada"] or state["fechas"]["publicada"]):
        problems.append("Fecha de publicación pendiente de confirmar.")
    if state["fechas"]["propuesta"] and state["bloqueos"] and not state["fechas"]["confirmada"]:
        warnings.append("Fecha tentativa: hay pendientes de producción.")
    if state["archivo"]["verificado"] and (not state["archivo"]["ruta"] or not resolve_file(root, state, state["archivo"]["ruta"]).exists()):
        warnings.append("Respaldo declarado verificado pero no disponible.")
    return {"id": state["id"], "etapa": state["etapa"], "listo_para_publicar": not problems,
            "pendientes": list(dict.fromkeys(problems)), "avisos": warnings}


def check_claims(root, state):
    if state["miniatura"]["estado"] == "lista":
        require(nonempty_file(root, state, state["miniatura"]["ruta"]), "Miniatura lista requiere archivo final disponible")
    export = state["exportacion"]
    if export["estado"] == "completada":
        require(nonempty_file(root, state, export["ruta"]), "Exportación completada requiere archivo disponible")
        require(bool(export["timeline_id"] and export["firma"]), "Exportación completada requiere timeline y firma exportados")
    if state["archivo"]["estado"] == "completado":
        path = state["archivo"]["ruta"]
        require(bool(path) and resolve_file(root, state, path).exists(), "Archivo completado requiere respaldo disponible")
    if state["etapa"] == "listo":
        signature = state["palmier"]["observado"]["firma"]
        require(bool(signature) and state["revision"]["firma"] == signature and state["revision"]["estructura"] and state["revision"]["audiovisual"],
                "Listo requiere revisión estructural/audiovisual del corte actual")
        require(nonempty_file(root, state, state["revision"]["evidencia"]), "Listo requiere evidencia de revisión")
        require(not state["bloqueos"], "Listo no puede tener bloqueos imprescindibles")
        observed = state["palmier"]["observado"]
        require(state["notas"]["firma"] == signature and state["notas"]["timeline_id"] == observed["timeline_id"], "Listo requiere notas vigentes")
        for resource in state["recursos"]:
            if resource.get("imprescindible"):
                require(resource["estado"] == "en_video" and resource.get("timeline_id") == observed["timeline_id"], "Apoyo imprescindible pendiente: " + resource["id"])
                require(not resource.get("ruta") or resolve_file(root, state, resource["ruta"]).exists(), "Archivo imprescindible ausente: " + resource["id"])


def record(root, state, note, collisions=True):
    validate(state)
    check_claims(root, state)
    states = load_states(root)
    day = reservation_day(state)
    # Hechos externos se registran aunque incumplan un video/día; el calendario avisa.
    if collisions and day and not (state["fechas"]["programada"] or state["fechas"]["publicada"]):
        conflicts = [s["id"] for s in states if s["id"] != state["id"] and reservation_day(s) == day]
        if conflicts:
            alternative = next_free_day(states, state["id"], parse_day(day))
            raise ValueError("Fecha ocupada por " + ", ".join(conflicts) + "; alternativa: " + alternative)
    path = state["palmier"]["ruta"]
    if path:
        actual = resolve_file(root, state, path).resolve()
        for existing in states:
            other = existing["palmier"]["ruta"]
            require(not (existing["id"] != state["id"] and other and resolve_file(root, existing, other).resolve() == actual),
                    "Ese proyecto Palmier ya está registrado en " + existing["id"])
    stamp = now()
    state["actualizado_en"] = stamp
    state["historial"].append({"fecha": stamp, "etapa": state["etapa"], "nota": note})
    write_json(root / "videos" / state["id"] / "estado.json", state)
    return state


def md(value):
    return str(value if value is not None else "Pendiente").replace("|", "\\|").replace("\n", "<br>")


def file_link(value, label="archivo"):
    return "[" + label + "](<" + str(value).replace(">", "%3E") + ">)" if value else "Pendiente"


def replace_block(text, kind, body):
    start = "<!-- yt-video-flow:" + kind + ":start -->"
    end = "<!-- yt-video-flow:" + kind + ":end -->"
    require(text.count(start) == text.count(end) and text.count(start) <= 1, "Bloque generado incompleto/duplicado: " + kind)
    block = start + "\n" + body.strip() + "\n" + end
    if start not in text:
        return text.rstrip() + "\n\n" + block + "\n"
    a, b = text.index(start), text.index(end)
    require(b > a, "Orden de marcadores inválido: " + kind)
    return text[:a] + block + text[b + len(end):]


def rendered_documents(root, state):
    folder = root / "videos" / state["id"]
    dates = state["fechas"]
    observed = state["palmier"]["observado"]
    problems = check_state(root, state)
    status = "\n".join([
        "**Datos operativos generados desde `estado.json`; no editar este bloque.**",
        "", "| Campo | Valor |", "| --- | --- |",
        "| Nombre de trabajo | " + md(state["nombre"]) + " |",
        "| Etapa | " + md(state["etapa"]) + " |",
        "| Actividad | " + md(state["actividad"]["estado"]) + " |",
        "| Importancia | " + md(state["prioridad"]["nivel"] + " — " + state["prioridad"]["motivo"]) + " |",
        "| Idea registrada | " + md(state["idea"] or "Pendiente") + " |",
        "| Pendiente principal | " + md(next(iter(state["bloqueos"]), "Sin bloqueo registrado")) + " |",
        "| Siguiente paso | " + md(state["siguiente_paso"]) + " |",
        "| Proyecto Palmier | " + file_link(state["palmier"]["ruta"], "proyecto") + " |",
        "| Actualizado | " + md(state["actualizado_en"]) + " |",
    ])
    publication = "\n".join([
        "**Datos operativos generados desde `estado.json`; opciones y descripción se editan debajo.**", "",
        "| Campo | Valor |", "| --- | --- |",
        "| Título elegido | " + md(state["publicacion"]["titulo_elegido"]) + " |",
        "| Descripción revisada | " + ("Sí" if state["publicacion"]["descripcion_revisada"] else "No") + " |",
        "| Miniatura | " + md(state["miniatura"]["estado"]) + " · " + file_link(state["miniatura"]["ruta"]) + " |",
        "| Fecha propuesta (tentativa) | " + md(dates["propuesta"]) + " |",
        "| Fecha confirmada | " + md(dates["confirmada"]) + " |",
        "| Programación real informada | " + md(dates["programada"]) + " |",
        "| Publicación real informada | " + md(dates["publicada"]) + " |",
        "| URL | " + md(state["youtube"]["url"]) + " |",
        "| Listo para publicar | " + ("Sí" if problems["listo_para_publicar"] else "No") + " |",
    ])
    resources = ["**Inventario generado desde `estado.json`.**", "",
                 "| ID | Material / función | Estado | Archivo | Referencia Palmier | Imprescindible | Observaciones |",
                 "| --- | --- | --- | --- | --- | --- | --- |"]
    for resource in state["recursos"]:
        refs = ", ".join(filter(None, [resource.get("media_ref"), resource.get("asset_ref"), resource.get("timeline_id")]))
        resources.append("| " + " | ".join([md(resource["id"]), md(resource["nombre"] + " / " + (resource.get("rol") or "Por definir")),
                        RESOURCE_STATES[resource["estado"]], file_link(resource.get("ruta")), md(refs or None),
                        "Sí" if resource.get("imprescindible") else "No", md(resource.get("notas") or "")]) + " |")
    notes = state["notas"]
    anchors = "\n".join([
        "**Anclajes registrados; actualizar tras editar duración o contenido.**", "",
        "- Timeline observado: `" + str(observed["timeline_id"]) + "`; total de frames: " + str(observed["total_frames"]) + ".",
        "- Timeline de las notas: `" + str(notes["timeline_id"]) + "`.",
        "- Firma registrada: `" + str(notes["firma"]) + "`.",
        "- Estado: " + ("vigentes para el snapshot registrado" if observed["firma"] and notes["firma"] == observed["firma"] and notes["timeline_id"] == observed["timeline_id"] else "**pendientes de revisar para el corte actual**") + ".",
    ])
    review = ["**Resultado operativo generado desde `estado.json`.**", "",
              "- Estructura revisada: " + str(state["revision"]["estructura"]) + ".",
              "- Reproducción audiovisual revisada: " + str(state["revision"]["audiovisual"]) + ".",
              "- Exportación: " + state["exportacion"]["estado"] + "; verificada: " + str(state["exportacion"]["verificado"]) + ".",
              "- Archivo: " + state["archivo"]["estado"] + ".", "", "Pendientes para publicación:", ""]
    review.extend("- " + item for item in problems["pendientes"])
    if not problems["pendientes"]:
        review.append("- Ninguno registrado.")
    return [(folder / (name + ".md"), kind, body) for name, kind, body in (
        ("brief", "status", status), ("publicacion", "publication", publication),
        ("assets", "resources", "\n".join(resources)), ("notas", "anchors", anchors),
        ("revision", "review", "\n".join(review)))]


def sync(root):
    states = load_states(root)
    writes = []
    for state in states:
        for path, kind, body in rendered_documents(root, state):
            require(path.is_file(), "Documento faltante: " + str(path))
            writes.append((path, replace_block(path.read_text(encoding="utf-8"), kind, body)))
    lines = ["# Calendario de videos — Clash of Clans", "",
             "Vista generada desde `videos/VNNNN/estado.json`. No editar esta tabla directamente.", "",
             "Zona horaria: **America/Mexico_City**. Las propuestas reservan un día, pero no significan programación real en YouTube.",
             "Se actualiza al trabajar con el agente; la programación y publicación reales las informa el usuario.", "",
             "| Video | Fecha propuesta | Fecha confirmada / programación real | Publicado | Importancia | Etapa / actividad | Miniatura | Pendiente principal |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    ordered = sorted(states, key=lambda s: (reservation_day(s) or "9999-12-31", {"alta": 0, "media": 1, "baja": 2}[s["prioridad"]["nivel"]], s["id"]))
    occupied = {}
    for state in ordered:
        day = reservation_day(state)
        if day:
            occupied.setdefault(day, []).append(state["id"])
        dates = state["fechas"]
        title = state["publicacion"]["titulo_elegido"] or state["nombre"]
        lines.append("| " + " | ".join([
            "[" + state["id"] + " · " + md(title).replace("[", "\\[").replace("]", "\\]") + "](videos/" + state["id"] + "/brief.md)",
            md(dates["propuesta"]), md(dates["programada"] or dates["confirmada"]), md(dates["publicada"]),
            md(state["prioridad"]["nivel"] + (" (confirmada)" if state["prioridad"]["confirmada"] else " (propuesta)")),
            md(state["etapa"] + " / " + state["actividad"]["estado"]), md(state["miniatura"]["estado"]),
            md(next(iter(state["bloqueos"]), "Sin bloqueo registrado")),
        ]) + " |")
    lines += ["", "## Conflictos de fechas", ""]
    conflicts = [(day, ids) for day, ids in sorted(occupied.items()) if len(ids) > 1]
    lines += ["- " + day + ": " + ", ".join(ids) + ". Revisar; no se movió ningún video." for day, ids in conflicts] or ["Sin conflictos registrados."]
    lines += ["", "## Cómo continuar", "",
              "- «Crea un proyecto de video» / «La idea de V0001 es…».",
              "- «Prepara V0001» / «Haz el montaje base» / «Edita los apoyos y la emoción».",
              "- «Revisa V0001» / «Exporta el video» / «Archiva el proyecto».",
              "- «Lo programé para…» / «Ya lo publiqué; este es el enlace…».", ""]
    writes.append((root / "calendario.md", "\n".join(lines)))
    for path, content in writes:
        atomic_write(path, content)
    return states


def bootstrap(root):
    for folder in ("videos", "assets-compartidos/marca", "assets-compartidos/musica", "assets-compartidos/efectos", "assets-compartidos/referencias"):
        (root / folder).mkdir(parents=True, exist_ok=True)


def create_video(root, identifier, name, idea):
    if identifier:
        video_id(identifier)
        if (root / "videos" / identifier / "estado.json").is_file():
            return load_state(root, identifier)
    else:
        numbers = [int(p.name[1:]) for p in (root / "videos").iterdir() if re.fullmatch(r"V\d{4,}", p.name)]
        identifier = "V" + str(max(numbers, default=0) + 1).zfill(4)
    folder = root / "videos" / identifier
    require(not folder.exists(), "Carpeta ya existente sin estado válido: " + identifier)
    state = initial_state(identifier, name, idea)
    validate(state)
    for path in FOLDERS:
        (folder / path).mkdir(parents=True, exist_ok=True)
    for document in DOCUMENTS:
        template = (SKILL_ROOT / "assets" / "templates" / (document + ".md")).read_text(encoding="utf-8")
        for key, value in (("video_id", identifier), ("nombre", name), ("idea", idea or "Idea todavía pendiente de proporcionar.")):
            template = template.replace("{{" + key + "}}", value)
        atomic_write(folder / (document + ".md"), template)
    return record(root, state, "Creado registro local; proyecto Palmier pendiente de vincular.")


def bind_project(root, state, path, project_id, name, original=None, montage=None):
    actual = Path(path).expanduser().resolve()
    require(actual.exists() and actual.suffix == ".palmier", "Debe existir el paquete .palmier registrado por la app")
    require(bool(project_id.strip()), "Falta ID real del proyecto Palmier")
    link = root / "videos" / state["id"] / "palmier" / "proyecto.palmier"
    if link.is_symlink():
        require(link.resolve() == actual, "El enlace ya apunta a otro proyecto; no se reemplazará")
    else:
        require(not link.exists(), "La ubicación del enlace ya está ocupada")
    candidate = copy.deepcopy(state)
    candidate["palmier"].update({"project_id": project_id, "nombre": name, "ruta": str(actual)})
    if original:
        candidate["palmier"]["timelines"]["original"] = original
    if montage:
        candidate["palmier"]["timelines"]["montaje"] = montage
    saved = record(root, candidate, "Vinculado proyecto Palmier real; archivos conservados en su ubicación.")
    if not link.is_symlink():
        link.symlink_to(os.path.relpath(actual, link.parent), target_is_directory=True)
    return saved


def snapshot(root, state, source):
    timeline = json.loads(Path(source).read_text(encoding="utf-8"))
    require(isinstance(timeline, dict) and all(k in timeline for k in ("id", "fps", "width", "height", "totalFrames", "tracks")),
            "Usa el JSON decodificado de get_timeline, no el envoltorio MCP")
    require(isinstance(timeline["id"], str) and bool(timeline["id"]), "ID de timeline inválido")
    require(type(timeline["totalFrames"]) is int and timeline["totalFrames"] >= 0, "totalFrames inválido")
    require(isinstance(timeline["tracks"], list), "Tracks inválidos")
    relevant = {k: timeline[k] for k in ("id", "fps", "width", "height", "totalFrames", "tracks")}
    signature = hashlib.sha256(json.dumps(relevant, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
    evidence = root / "videos" / state["id"] / "evidencia" / ("timeline-" + signature[:16] + ".json")
    write_json(evidence, timeline)
    if state["palmier"]["observado"]["firma"] and state["palmier"]["observado"]["firma"] != signature:
        state["publicacion"]["descripcion_revisada"] = False
    state["palmier"]["observado"] = {"timeline_id": timeline["id"], "total_frames": timeline["totalFrames"], "firma": signature}
    state["palmier"]["settings"] = {k: timeline[k] for k in ("width", "height", "fps")}
    return record(root, state, "Leído snapshot del corte; evidencia: " + evidence.name)


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Workspace coc; por defecto el que contiene la skill")
    commands = cli.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Crear carpeta/documentos; Palmier se crea mediante MCP")
    init.add_argument("--name", default="Video sin idea")
    init.add_argument("--idea", default="")
    init.add_argument("--id", help="Reanudar creación del mismo registro, sin sobrescribirlo")
    adopt = commands.add_parser("adopt", help="Registrar un proyecto existente, sin moverlo")
    adopt.add_argument("--path", required=True)
    adopt.add_argument("--project-id", required=True)
    adopt.add_argument("--name", required=True)
    adopt.add_argument("--etapa", choices=STAGES, default="preparacion")
    adopt.add_argument("--notes-source", type=Path)
    adopt.add_argument("--timeline-original")
    adopt.add_argument("--timeline-montaje")
    bind = commands.add_parser("bind", help="Vincular ID y ruta reales devueltos por Palmier")
    bind.add_argument("id")
    bind.add_argument("--path", required=True)
    bind.add_argument("--project-id", required=True)
    bind.add_argument("--name", required=True)
    bind.add_argument("--timeline-original")
    bind.add_argument("--timeline-montaje")
    update = commands.add_parser("update", help="Aplicar parche y regenerar documentos/calendario")
    update.add_argument("id")
    update.add_argument("--patch-file", type=Path, required=True)
    update.add_argument("--nota", required=True)
    update.add_argument("--resultado", choices=("completada", "bloqueada", "parcial"))
    begin = commands.add_parser("begin", help="Registrar inicio de una etapa autorizada")
    begin.add_argument("id")
    begin.add_argument("etapa", choices=STAGES)
    snap = commands.add_parser("snapshot", help="Guardar/firma de una lectura real del timeline")
    snap.add_argument("id")
    snap.add_argument("--timeline-json", type=Path, required=True)
    suggest = commands.add_parser("suggest-date", help="Reservar fecha tentativa sin mover otros videos")
    suggest.add_argument("id")
    suggest.add_argument("--from-date", help="No anterior a mañana; YYYY-MM-DD")
    for command in ("show", "check"):
        sub = commands.add_parser(command)
        sub.add_argument("id")
    commands.add_parser("calendar", help="Regenerar y listar todos los proyectos")
    return cli


def execute(root, args):
    if args.command == "calendar":
        return {"calendario": str(root / "calendario.md"), "videos": len(load_states(root))}
    if args.command == "init":
        return create_video(root, args.id, args.name, args.idea)
    if args.command == "adopt":
        actual = Path(args.path).expanduser().resolve()
        require(actual.exists() and actual.suffix == ".palmier", "Debe existir el paquete .palmier")
        if args.notes_source:
            require(args.notes_source.is_file(), "No existe el documento de notas anterior")
        existing = next((s for s in load_states(root) if s["palmier"]["ruta"] and resolve_file(root, s, s["palmier"]["ruta"]).resolve() == actual), None)
        if existing:
            require(existing["palmier"]["project_id"] == args.project_id, "La ruta coincide pero el ID Palmier difiere; revisar antes de retomar")
            return existing
        state = create_video(root, None, args.name, "")
        state["etapa"] = args.etapa
        state = bind_project(root, state, args.path, args.project_id, args.name, args.timeline_original, args.timeline_montaje)
        if args.notes_source:
            atomic_write(root / "videos" / state["id"] / "notas.md", args.notes_source.read_text(encoding="utf-8"))
        return state
    state = load_state(root, args.id)
    if args.command == "show":
        return state
    if args.command == "check":
        return check_state(root, state)
    if args.command == "bind":
        return bind_project(root, state, args.path, args.project_id, args.name, args.timeline_original, args.timeline_montaje)
    if args.command == "snapshot":
        return snapshot(root, state, args.timeline_json)
    if args.command == "begin":
        require(args.etapa not in ("listo", "exportado", "programado", "publicado", "archivado"), "Usa update para resultados comprobados")
        if state["actividad"]["estado"] == "en_curso" and state["actividad"]["etapa"] == args.etapa:
            return state
        state["etapa"] = args.etapa
        state["actividad"] = {"etapa": args.etapa, "estado": "en_curso", "inicio": now()}
        return record(root, state, "Inicio de etapa autorizada: " + args.etapa)
    if args.command == "suggest-date":
        require(not any(state["fechas"][k] for k in ("confirmada", "programada", "publicada")), "Ya hay fecha confirmada/real; no se modificará")
        tomorrow = datetime.now(ZONE).date() + timedelta(days=1)
        start = max(tomorrow, parse_day(args.from_date)) if args.from_date else tomorrow
        state["fechas"]["propuesta"] = next_free_day(load_states(root), state["id"], start)
        return record(root, state, "Fecha tentativa propuesta según calendario y pendientes de producción.")
    if args.command == "update":
        patch = json.loads(args.patch_file.read_text(encoding="utf-8"))
        require(isinstance(patch, dict), "El parche debe ser un objeto")
        require(not (set(patch) & {"id", "schema_version", "creado_en", "actualizado_en", "historial"}), "No se pueden cambiar identidad, versión ni historial")
        deep_merge(state, patch)
        if args.resultado:
            state["actividad"]["estado"] = args.resultado
        return record(root, state, args.nota)
    raise ValueError("Comando no implementado")


def main():
    cli = parser()
    args = cli.parse_args()
    root = args.root.expanduser().resolve()
    if any(p.suffix == ".palmier" for p in (root,) + tuple(root.parents)):
        cli.exit(2, "Error: el workspace no puede estar dentro de un paquete Palmier\n")
    root.mkdir(parents=True, exist_ok=True)
    try:
        with (root / ".yt-video-flow.lock").open("a", encoding="utf-8") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            bootstrap(root)
            sync(root)  # Hook previo: nunca consultar un calendario desactualizado.
            try:
                result = execute(root, args)
            finally:
                sync(root)  # Hook posterior, incluso tras un fallo o bloqueo.
            print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        cli.exit(2, "Error: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
