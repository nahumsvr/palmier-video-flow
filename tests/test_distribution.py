"""Comprueba la distribución y los ejemplos sin medios ni editor conectado."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/yt-video-flow/scripts/video_flow.py'
spec = importlib.util.spec_from_file_location('ranges', ROOT / 'skills/yt-cut-hi/scripts/plan_ranges.py')
ranges = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ranges)

SKILLS = {'yt-video-flow': 'video_flow.py', 'yt-cut-hi': 'plan_ranges.py',
          'yt-edit-dinamica': None, 'yt-edit-zooms': 'zoom_rows.py',
          'yt-edit-subtitulos': 'caption_motion.py', 'yt-edit-sfx': 'sfx_plan.py',
          'yt-edit-capitulos': 'chapter_plan.py'}


class DistributionTests(unittest.TestCase):
    def test_skill_discovery_links_resolve(self):
        for name, script_name in SKILLS.items():
            with self.subTest(name=name):
                link = ROOT / '.agents/skills' / name
                self.assertTrue(link.is_symlink())
                self.assertEqual(link.resolve(), ROOT / 'skills' / name)
                self.assertTrue((link / 'SKILL.md').is_file())
                self.assertTrue((link / 'agents' / 'openai.yaml').is_file())
                if script_name is None:
                    continue
                result = subprocess.run([sys.executable, str(link / 'scripts' / script_name), '--help'],
                                        text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_skill_front_matter_names_match_their_folders(self):
        for name in SKILLS:
            with self.subTest(name=name):
                lines = (ROOT / 'skills' / name / 'SKILL.md').read_text(encoding='utf-8').splitlines()
                self.assertEqual(lines[0], '---')
                self.assertIn('name: ' + name, lines[:4])
                self.assertTrue(any(line.startswith('description: ') for line in lines[:6]))

    def test_documented_examples_execute_in_clean_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            def command(*args):
                result = subprocess.run([sys.executable, str(SCRIPT), '--root', directory, *args],
                                        text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)
            state = command('init', '--name', 'Ejemplo')
            for example in ('definir-video.json', 'registrar-programacion.json'):
                state = command('update', state['id'], '--patch-file', str(ROOT / 'examples' / example),
                                '--nota', 'Ejemplo comprobado')
            self.assertEqual(state['etapa'], 'programado')
            self.assertEqual(state['fechas']['programada'], '2030-01-15T18:00:00-06:00')
            self.assertTrue((Path(directory) / 'calendario.md').is_file())

    def test_private_runtime_files_are_ignored(self):
        paths = ['videos/V0001/estado.json', 'assets-compartidos/music.wav', 'calendario.md',
                 'palmier/project.palmier/info.json', 'videos-ipad/game.mov', '.env', 'raw.mp4']
        result = subprocess.run(['git', 'check-ignore', '--no-index', '--stdin'], cwd=ROOT,
                                input='\n'.join(paths) + '\n', text=True, capture_output=True)
        self.assertEqual(set(result.stdout.splitlines()), set(paths), result.stderr)

    def test_overlapping_editorial_drops_count_frames_once(self):
        plan = ranges.build({'fps': 30, 'clip_frames': [0, 300],
                             'drop_frames': [[30, 90], [60, 120]]})
        self.assertEqual(plan['delete_ranges_frames'], [[30, 120]])
        self.assertEqual(plan['removed_frames'], 90)
        self.assertEqual(plan['kept_frames'], 210)

    def test_pauses_are_clipped_to_clip_boundaries(self):
        plan = ranges.build({'fps': 30, 'clip_frames': [60, 300],
                             'pauses_seconds': [[0, 4], [12, 15]]})
        self.assertEqual(plan['delete_ranges_frames'], [[60, 112]])
        self.assertTrue(all(60 < position < 300 for position in plan['split_frames']))

    def test_invalid_ranges_and_nonfinite_values_are_rejected(self):
        for data in ({'fps': float('nan'), 'clip_frames': [0, 300]},
                     {'fps': 30, 'clip_frames': [0, 300], 'drop_frames': [[0, 301]]},
                     {'fps': 30, 'clip_frames': [0, 300], 'split_frames': [300]}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                ranges.build(data)


if __name__ == '__main__':
    unittest.main()
