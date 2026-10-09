#!/usr/bin/env python3
"""Pruebas de persistencia, reservas y evidencia en workspaces temporales."""
import copy
from datetime import datetime, timedelta
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("video_flow.py")
spec = importlib.util.spec_from_file_location("video_flow", SCRIPT)
flow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flow)


class VideoFlowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="yt-flow-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        flow.bootstrap(self.root)

    def command(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root)] + list(args),
                                capture_output=True, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        return result

    def create(self, name="Prueba"):
        return self.command("init", "--name", name)

    def patch(self, identifier, patch, ok=True, result=None):
        path = self.root / "patch.json"
        path.write_text(json.dumps(patch), encoding="utf-8")
        args = ["update", identifier, "--patch-file", str(path), "--nota", "Cambio comprobado en ensayo"]
        if result:
            args += ["--resultado", result]
        return self.command(*args, ok=ok)

    def snapshot(self, identifier, **changes):
        timeline = {"id": "TL1", "fps": 30, "width": 1920, "height": 1080,
                    "totalFrames": 90, "currentFrame": 0,
                    "tracks": [{"index": 0, "trackId": "V1", "type": "video",
                                "clips": [{"id": "C1", "mediaRef": "M1", "frames": [0, 90]}]}]}
        timeline.update(changes)
        path = self.root / "timeline.json"
        path.write_text(json.dumps(timeline), encoding="utf-8")
        return self.command("snapshot", identifier, "--timeline-json", str(path))

    def test_init_reentry_and_editorial_preservation(self):
        state = self.create()
        self.assertEqual(state["id"], "V0001")
        folder = self.root / "videos" / "V0001"
        for directory in flow.FOLDERS:
            self.assertTrue((folder / directory).is_dir())
        notes = folder / "notas.md"
        notes.write_text(notes.read_text() + "\nDecisión personal que debe conservarse.\n", encoding="utf-8")
        same = self.command("init", "--id", "V0001", "--name", "Otro título")
        self.assertEqual(same["nombre"], "Prueba")
        self.assertEqual(len(list((self.root / "videos").glob("*/estado.json"))), 1)
        self.patch("V0001", {"nombre": "Nombre definitivo", "idea": "Idea recibida después", "etapa": "grabacion"})
        self.assertIn("Decisión personal", notes.read_text())
        self.assertIn("Nombre definitivo", (folder / "brief.md").read_text())
        self.assertIn("grabacion", (self.root / "calendario.md").read_text())

    def test_concurrent_ids_are_unique(self):
        jobs = [subprocess.Popen([sys.executable, str(SCRIPT), "--root", str(self.root), "init"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(3)]
        ids = []
        for job in jobs:
            output, error = job.communicate(timeout=20)
            self.assertEqual(job.returncode, 0, error)
            ids.append(json.loads(output)["id"])
        self.assertEqual(set(ids), {"V0001", "V0002", "V0003"})
        self.assertEqual(len(flow.load_states(self.root)), 3)

    def test_dates_skip_reservations_without_moving_other_video(self):
        first, second = self.create("Primero"), self.create("Segundo")
        first = self.command("suggest-date", first["id"])
        second = self.command("suggest-date", second["id"])
        self.assertEqual((flow.parse_day(second["fechas"]["propuesta"]) - flow.parse_day(first["fechas"]["propuesta"])).days, 1)
        self.assertEqual(flow.load_state(self.root, first["id"])["fechas"], first["fechas"])
        before = flow.load_state(self.root, second["id"])
        error = self.patch(second["id"], {"fechas": {"confirmada": first["fechas"]["propuesta"]}}, ok=False)
        self.assertIn("Fecha ocupada", error.stderr)
        self.assertEqual(flow.load_state(self.root, second["id"]), before)

    def test_confirmed_date_is_not_reproposed(self):
        state = self.create()
        day = (datetime.now(flow.ZONE).date() + timedelta(days=4)).isoformat()
        self.patch(state["id"], {"fechas": {"confirmada": day}})
        self.assertIn("Ya hay fecha", self.command("suggest-date", state["id"], ok=False).stderr)
        self.assertEqual(flow.load_state(self.root, state["id"])["fechas"]["confirmada"], day)

    def test_real_external_collision_is_recorded_and_visible(self):
        first, second = self.create(), self.create()
        for state in (first, second):
            self.patch(state["id"], {"etapa": "programado", "fechas": {"programada": "2026-10-11T01:00:00+00:00"}})
        self.assertEqual(flow.reservation_day(flow.load_state(self.root, first["id"])), "2026-10-10")
        calendar = (self.root / "calendario.md").read_text()
        self.assertIn("2026-10-10: V0001, V0002", calendar)

    def test_rejects_ambiguous_times_and_false_publication(self):
        state = self.create()
        before = copy.deepcopy(state)
        self.patch(state["id"], {"etapa": "programado", "fechas": {"programada": "2026-10-10T18:00:00"}}, ok=False)
        self.patch(state["id"], {"etapa": "publicado", "fechas": {"publicada": "2026-10-10T18:00:00-06:00"}}, ok=False)
        self.assertEqual(flow.load_state(self.root, state["id"]), before)
        self.patch(state["id"], {"etapa": "publicado", "fechas": {"publicada": "2026-10-10T18:00:00-06:00"},
                                 "youtube": {"url": "https://youtu.be/example"}})

    def test_adoption_preserves_raw_package_and_existing_notes(self):
        package = self.root / "legacy" / "example.palmier"
        package.mkdir(parents=True)
        original = package / "project.json"
        original.write_text('{"keep":true}')
        notes = self.root / "legacy" / "notes.md"
        notes.write_text("# Notas originales\n\nConservar decisiones.\n")
        arguments = ["adopt", "--path", str(package), "--project-id", "P1", "--name", "Existente",
                     "--etapa", "montaje", "--notes-source", str(notes), "--timeline-original", "T0", "--timeline-montaje", "T1"]
        state = self.command(*arguments)
        target = self.root / "videos" / state["id"] / "notas.md"
        self.assertIn("Conservar decisiones", target.read_text())
        target.write_text(target.read_text() + "\nNueva decisión aprobada.\n")
        second = self.command(*arguments)
        self.assertEqual(state["id"], second["id"])
        self.assertIn("Nueva decisión aprobada", target.read_text())
        self.assertEqual(original.read_text(), '{"keep":true}')
        self.assertEqual(notes.read_text(), "# Notas originales\n\nConservar decisiones.\n")
        self.assertEqual((target.parent / "palmier" / "proyecto.palmier").resolve(), package.resolve())

    def test_unknown_fields_and_false_resource_states_do_not_commit(self):
        state = self.create()
        self.patch(state["id"], {"etappa": "edicion"}, ok=False)
        self.patch(state["id"], {"id": "V9999"}, ok=False)
        self.patch(state["id"], {"recursos": [{"id": "M01", "nombre": "Clip", "estado": "en_video", "comprobado": True, "media_ref": "R1"}]}, ok=False)
        self.assertEqual(flow.load_state(self.root, state["id"]), state)

    def test_missing_required_source_is_reported(self):
        state = self.create()
        raw = self.root / "crudo.mov"
        raw.write_bytes(b"source fixture")
        self.patch(state["id"], {"recursos": [{"id": "M01", "nombre": "Crudo", "estado": "tenemos_no_importado",
                                             "ruta": str(raw), "comprobado": True, "imprescindible": True}]})
        raw.unlink()
        result = self.command("check", state["id"])
        self.assertFalse(result["listo_para_publicar"])
        self.assertTrue(any("Falta el archivo imprescindible" in item for item in result["pendientes"]))

    def test_snapshot_ignores_cursor_but_invalidates_changed_cut(self):
        state = self.create()
        state = self.snapshot(state["id"])
        signature = state["palmier"]["observado"]["firma"]
        self.patch(state["id"], {"notas": {"timeline_id": "TL1", "firma": signature},
                                 "revision": {"estructura": True, "audiovisual": True, "firma": signature},
                                 "publicacion": {"descripcion_revisada": True}})
        moved = self.snapshot(state["id"], currentFrame=45)
        self.assertEqual(moved["palmier"]["observado"]["firma"], signature)
        self.assertTrue(moved["publicacion"]["descripcion_revisada"])
        changed = self.snapshot(state["id"], totalFrames=60)
        self.assertNotEqual(changed["palmier"]["observado"]["firma"], signature)
        self.assertFalse(changed["publicacion"]["descripcion_revisada"])
        result = self.command("check", state["id"])
        self.assertIn("La revisión no corresponde al corte actual.", result["pendientes"])
        self.assertTrue(any("Notas/anclajes" in item for item in result["pendientes"]))

    def test_pending_failed_and_missing_exports_cannot_be_delivered(self):
        state = self.create()
        self.patch(state["id"], {"etapa": "exportacion", "exportacion": {"estado": "en_proceso", "job_id": "JOB1"}})
        self.patch(state["id"], {"etapa": "exportado"}, ok=False)
        self.patch(state["id"], {"exportacion": {"estado": "fallida"}}, result="bloqueada")
        self.patch(state["id"], {"etapa": "exportado"}, ok=False)
        self.patch(state["id"], {"exportacion": {"estado": "completada", "verificado": True, "ruta": "exports/missing.mp4"}}, ok=False)
        self.assertEqual(flow.load_state(self.root, state["id"])["exportacion"]["estado"], "fallida")

    def test_publish_readiness_requires_all_evidence_and_assets(self):
        state = self.create()
        state = self.snapshot(state["id"])
        signature = state["palmier"]["observado"]["firma"]
        folder = self.root / "videos" / state["id"]
        (folder / "evidencia" / "review.md").write_text("Fixture: resultados declarados, no una revisión real.")
        (folder / "exports" / "final.mp4").write_bytes(b"file-presence fixture, not real video")
        (folder / "miniatura" / "final.png").write_bytes(b"file-presence fixture")
        day = (datetime.now(flow.ZONE).date() + timedelta(days=2)).isoformat()
        patch = {"notas": {"timeline_id": "TL1", "firma": signature},
                 "revision": {"estructura": True, "audiovisual": False, "firma": signature, "evidencia": "evidencia/review.md"},
                 "exportacion": {"estado": "completada", "verificado": True, "ruta": "exports/final.mp4", "timeline_id": "TL1", "firma": signature},
                 "miniatura": {"estado": "lista", "ruta": "miniatura/final.png"},
                 "publicacion": {"titulo_elegido": "Reto real", "descripcion_revisada": True}, "fechas": {"confirmada": day}}
        self.patch(state["id"], patch)
        self.assertFalse(self.command("check", state["id"])["listo_para_publicar"])
        self.patch(state["id"], {"revision": {"audiovisual": True}})
        self.assertTrue(self.command("check", state["id"])["listo_para_publicar"])
        (folder / "miniatura" / "final.png").unlink()
        self.assertFalse(self.command("check", state["id"])["listo_para_publicar"])

    def test_corrupt_state_does_not_hide_calendar_reservations(self):
        state = self.create()
        self.command("suggest-date", state["id"])
        calendar = (self.root / "calendario.md").read_text()
        (self.root / "videos" / state["id"] / "estado.json").write_text("{broken")
        self.command("calendar", ok=False)
        self.assertEqual((self.root / "calendario.md").read_text(), calendar)

    def test_partial_stage_and_begin_reentry(self):
        state = self.create()
        first = self.command("begin", state["id"], "edicion")
        second = self.command("begin", state["id"], "edicion")
        self.assertEqual(first, second)
        saved = self.patch(state["id"], {"bloqueos": ["Falta B-roll"], "siguiente_paso": "Obtener la toma"}, result="parcial")
        self.assertEqual(saved["actividad"]["estado"], "parcial")
        self.assertIn("Falta B-roll", (self.root / "calendario.md").read_text())

    def test_damaged_generated_block_keeps_editorial_content(self):
        state = self.create()
        path = self.root / "videos" / state["id"] / "brief.md"
        text = path.read_text().replace("<!-- yt-video-flow:status:end -->", "")
        path.write_text(text)
        self.command("calendar", ok=False)
        self.assertEqual(path.read_text(), text)

    def test_helper_rejects_live_package_as_workspace(self):
        package = self.root / "do-not-write.palmier"
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(package), "init"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(package.exists())


if __name__ == "__main__":
    unittest.main()
