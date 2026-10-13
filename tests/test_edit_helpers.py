"""Comprueba los cálculos de las skills de edición sin medios ni editor conectado."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


zooms = load('zoom_rows', 'skills/yt-edit-zooms/scripts/zoom_rows.py')
captions = load('caption_motion', 'skills/yt-edit-subtitulos/scripts/caption_motion.py')
chapters = load('chapter_plan', 'skills/yt-edit-capitulos/scripts/chapter_plan.py')
sfx = load('sfx_plan', 'skills/yt-edit-sfx/scripts/sfx_plan.py')

SPEC = {'canvas': [1920, 1080], 'media': [2360, 1640], 'fit': 'contain'}


class ZoomTests(unittest.TestCase):
    def test_contain_base_keeps_the_whole_frame(self):
        result = zooms.build({**SPEC, 'rows': [{'frame': 0, 'zoom': 1}]})
        self.assertAlmostEqual(result['base']['width'], 0.8095, places=3)
        self.assertEqual(result['base']['height'], 1.0)
        self.assertEqual(result['position'][0][1:], [0.0953, 0.0])

    def test_cover_base_fills_the_width_and_crops_vertically(self):
        result = zooms.build({**SPEC, 'fit': 'cover', 'rows': [{'frame': 0, 'zoom': 1}]})
        self.assertEqual(result['base']['width'], 1.0)
        self.assertAlmostEqual(result['base']['height'], 1.2352, places=3)

    def test_focus_zoom_is_clamped_to_avoid_empty_edges(self):
        rows = [{'frame': 0, 'zoom': 1}, {'frame': 15, 'zoom': 1.5, 'focus': [0.5, 0.04]},
                {'frame': 30, 'zoom': 1.6, 'focus': [0.93, 0.28]}]
        result = zooms.build({**SPEC, 'rows': rows})
        self.assertFalse(result['scale_only_is_enough'])
        self.assertEqual(result['position'][1][1:], [-0.1071, 0.0])
        # el contador de gemas está pegado al borde derecho: x se limita a 1 - ancho
        self.assertAlmostEqual(result['position'][2][1], 1 - result['scale'][2][1], places=3)
        self.assertEqual(result['position'][2][2], 0.0)

    def test_still_zoom_by_four_stays_inside_the_canvas(self):
        rows = [{'frame': 16, 'zoom': 1}, {'frame': 26, 'zoom': 4.3, 'focus': [0.92, 0.285]},
                {'frame': 36, 'zoom': 4.0, 'focus': [0.92, 0.285]}]
        result = zooms.build({**SPEC, 'rows': rows})
        for (_, w, h), (_, x, y) in zip(result['scale'], result['position']):
            if w > 1:  # con barras laterales (zoom bajo) la imagen se centra y no llena el lienzo
                self.assertLessEqual(x, 1e-3)
                self.assertGreaterEqual(x + w, 1 - 1e-3)
            if h > 1:
                self.assertLessEqual(y, 1e-3)
                self.assertGreaterEqual(y + h, 1 - 1e-3)
        self.assertLess(result['position'][0][1] + result['scale'][0][1], 1)
        self.assertGreater(result['scale'][1][1], 3)

    def test_centered_zoom_needs_only_scale(self):
        result = zooms.build({**SPEC, 'rows': [{'frame': 0, 'zoom': 1}, {'frame': 100, 'zoom': 1.07}]})
        self.assertTrue(result['scale_only_is_enough'])

    def test_invalid_input_is_rejected(self):
        for rows in ([], [{'frame': 5, 'zoom': 1}, {'frame': 5, 'zoom': 2}], [{'frame': 0, 'zoom': 0}],
                     [{'frame': 0, 'zoom': 1, 'focus': [1.5, 0]}]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                zooms.build({**SPEC, 'rows': rows})
        with self.assertRaises(ValueError):
            zooms.build({**SPEC, 'fit': 'stretch', 'rows': [{'frame': 0, 'zoom': 1}]})


class CaptionTests(unittest.TestCase):
    def test_regular_caption_rises_with_a_bounce_and_blur(self):
        found = captions.motion(40, 0.262, 0.802)
        self.assertEqual(found['position'], [[0, 0.262, 0.847], [2, 0.262, 0.79], [4, 0.262, 0.806], [6, 0.262, 0.802]])
        self.assertEqual(found['blur'], [[0, 14], [2 + 1, 4], [5, 0]])
        self.assertEqual(found['fadeInFrames'], 2)

    def test_short_clips_compress_the_entrance(self):
        self.assertEqual([r[0] for r in captions.motion(5, 0.4, 0.8)['position']], [0, 2, 3, 5])
        self.assertEqual([r[0] for r in captions.motion(4, 0.4, 0.8)['position']], [0, 1, 3, 4])
        self.assertEqual([r[0] for r in captions.motion(3, 0.4, 0.8)['blur']], [0, 2, 3])
        self.assertIsNone(captions.motion(2, 0.4, 0.8))
        self.assertIsNone(captions.motion(1, 0.4, 0.8))

    def test_final_row_matches_the_static_position(self):
        for duration in (3, 4, 5, 6, 30):
            with self.subTest(duration=duration):
                self.assertEqual(captions.motion(duration, 0.3, 0.7)['position'][-1], [duration if duration < 6 else 6, 0.3, 0.7])

    def test_centered_corner_uses_the_real_width(self):
        corner = captions.centered_corner(0.5, 0.86, 0.33697916666666666, 0.10833333333333334)
        self.assertEqual(corner, {'x': 0.3315, 'yf': 0.8058})

    def test_sizes_reads_a_project_file_read_only(self):
        project = {'timelines': [{'tracks': [{'clips': [{'id': '097C473D-C2CA-4E7D-8971-89FAC98AB61C',
                                                         'transform': {'centerX': 0.5, 'centerY': 0.86,
                                                                       'width': 0.337, 'height': 0.108}}]}]}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'project.json'
            path.write_text(json.dumps(project), encoding='utf-8')
            before = path.read_bytes()
            found = captions.sizes(str(path), ['097c473d', 'FFFFFFFF'])
            self.assertEqual(path.read_bytes(), before)
        self.assertAlmostEqual(found[0]['x'], 0.3315, places=4)
        self.assertEqual(found[1]['error'], 'no encontrado')


class ChapterTests(unittest.TestCase):
    def test_cards_match_the_real_session(self):
        result = chapters.plan({'cuts': [5431, 1192, 4970, 2172, 4525], 'card_frames': 36,
                                'total_frames': 6351, 'map_frames': [3515, 1191, 1192]})
        self.assertEqual(result['insert_order_desc'], [5431, 4970, 4525, 2172, 1192])
        self.assertEqual([c['start'] for c in result['cards']], [1192, 2208, 4597, 5078, 5575])
        self.assertEqual(result['new_total_frames'], 6531)
        self.assertEqual(result['mapped'], {'3515': 3587, '1191': 1191, '1192': 1228})

    def test_invalid_cuts_are_rejected(self):
        for spec in ({'cuts': [10, 10], 'card_frames': 36, 'total_frames': 100},
                     {'cuts': [200], 'card_frames': 36, 'total_frames': 100},
                     {'cuts': [10], 'card_frames': 0, 'total_frames': 100}):
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                chapters.plan(spec)


class SfxTests(unittest.TestCase):
    MEDIA = {'5 - Camera Click': 'A', '3 - Whoosh 3': 'B', '4 - Whoosh 4': 'C', '17 - Camera Shutter 2': 'D'}

    def test_roles_set_lead_volume_and_rotate_effects(self):
        result = sfx.plan({'media': self.MEDIA, 'events': [
            {'frame': 100, 'role': 'zoom'}, {'frame': 300, 'role': 'zoom'},
            {'frame': 500, 'role': 'cifra'}, {'frame': 700, 'role': 'impacto_capitulo'}]})
        names = [d['effect'] for d in result['detail']]
        self.assertEqual(names, ['3 - Whoosh 3', '4 - Whoosh 4', '5 - Camera Click', '17 - Camera Shutter 2'])
        self.assertEqual(result['volume_groups'], {'-14': [100, 300], '-12': [500], '-8': [700]})

    def test_missing_and_repeated_effects_are_reported(self):
        result = sfx.plan({'media': self.MEDIA, 'min_gap': 30, 'events': [
            {'frame': 100, 'role': 'cifra'}, {'frame': 110, 'role': 'cifra'}, {'frame': 400, 'role': 'corte'}]})
        self.assertEqual(len(result['warnings']), 1)
        self.assertEqual(result['missing_effects'], ['9 - Whoosh 8'])

    def test_unknown_role_is_rejected(self):
        with self.assertRaises(ValueError):
            sfx.plan({'media': {}, 'events': [{'frame': 1, 'role': 'meme'}]})


class CommandLineTests(unittest.TestCase):
    def run_script(self, relative, payload):
        return subprocess.run([sys.executable, str(ROOT / relative)], input=json.dumps(payload),
                              text=True, capture_output=True)

    def test_scripts_read_standard_input_and_fail_cleanly(self):
        ok = self.run_script('skills/yt-edit-zooms/scripts/zoom_rows.py',
                             {**SPEC, 'rows': [{'frame': 0, 'zoom': 1}]})
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertIn('position', json.loads(ok.stdout))
        bad = self.run_script('skills/yt-edit-capitulos/scripts/chapter_plan.py', {'cuts': [1]})
        self.assertEqual(bad.returncode, 1)
        self.assertIn('Error', bad.stderr)


if __name__ == '__main__':
    unittest.main()
