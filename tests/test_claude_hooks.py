"""Comprueba los hooks reales en workspaces aislados, sin modelo, MCP ni medios privados."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'skills/yt-video-flow/scripts/video_flow.py'
HOOK = ROOT / '.claude/hooks/video_flow.py'


class ClaudeHooksTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='video flow ')
        self.addCleanup(self.directory.cleanup)
        self.workspace = Path(self.directory.name)
        self.state = self.helper('init', '--name', 'Episodio de prueba')
        self.video = self.workspace / 'videos' / self.state['id']

    def helper(self, *arguments):
        result = subprocess.run([sys.executable, str(HELPER), '--root', str(self.workspace), *arguments],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def hook(self, event, **values):
        payload = {'hook_event_name': event, 'cwd': str(self.workspace), **values}
        return subprocess.run([sys.executable, str(HOOK), '--root', str(self.workspace)],
                              input=json.dumps(payload), text=True, capture_output=True,
                              cwd=self.video, timeout=30)

    def test_session_start_and_prompt_restore_context_without_changing_state(self):
        state_file = self.video / 'estado.json'
        before = state_file.read_bytes()
        (self.video / 'continuidad.md').write_text('Decisiones locales conservadas.\n')
        (self.workspace / 'calendario.md').write_text('Calendario antiguo\n')
        for event in ('SessionStart', 'UserPromptSubmit'):
            for source in ('startup', 'resume', 'compact') if event == 'SessionStart' else ('prompt',):
                with self.subTest(event=event, source=source):
                    result = self.hook(event, prompt='Retoma V0001', source=source)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    output = json.loads(result.stdout)['hookSpecificOutput']
                    self.assertEqual(output['hookEventName'], event)
                    self.assertIn('V0001', output['additionalContext'])
                    self.assertIn('continuidad.md', output['additionalContext'])
                    self.assertEqual(state_file.read_bytes(), before)
        self.assertIn('Episodio de prueba', (self.workspace / 'calendario.md').read_text())

    def test_nested_cwd_selects_episode_and_explicit_prompt_takes_precedence(self):
        second = self.helper('init', '--name', 'Segundo episodio')
        (self.video / 'assets/clips').mkdir(exist_ok=True)
        for prompt, expected, absent in (('continuemos', 'V0001', second['id']),
                                         ('Retoma ' + second['id'], second['id'], 'V0001')):
            result = self.hook('UserPromptSubmit', cwd=str(self.video / 'assets/clips'), prompt=prompt)
            output = json.loads(result.stdout)['hookSpecificOutput']['additionalContext']
            self.assertIn(expected, output)
            self.assertNotIn(absent, output)

    def test_unknown_id_does_not_create_episode(self):
        result = self.hook('UserPromptSubmit', prompt='Retoma V9999')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('registro no encontrado', json.loads(result.stdout)['hookSpecificOutput']['additionalContext'])
        self.assertFalse((self.workspace / 'videos/V9999').exists())

    def test_stop_and_post_write_regenerate_blocks_and_preserve_editorial_notes(self):
        note = self.video / 'notas.md'
        note.write_text(note.read_text() + '\nDecisión editorial local que debemos conservar.\n')
        before = (self.video / 'estado.json').read_bytes()
        for event in ('PostToolUse', 'Stop'):
            result = self.hook(event, tool_name='Write', stop_hook_active=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, '')
            self.assertIn('Decisión editorial local que debemos conservar.', note.read_text())
            self.assertEqual((self.video / 'estado.json').read_bytes(), before)

    def test_mcp_mutation_gets_reminder_but_reads_do_not_claim_results(self):
        before = (self.video / 'estado.json').read_bytes()
        for prefix in ('mcp__palmier-pro__', 'mcp__palmier_pro__'):
            result = self.hook('PreToolUse', tool_name=prefix + 'add_clips')
            self.assertEqual(json.loads(result.stdout)['hookSpecificOutput']['hookEventName'], 'PreToolUse')
            result = self.hook('PostToolUse', tool_name=prefix + 'add_clips')
            self.assertIn('snapshot', json.loads(result.stdout)['hookSpecificOutput']['additionalContext'])
            result = self.hook('PostToolUse', tool_name=prefix + 'get_timeline')
            self.assertEqual(result.stdout, '')
        self.assertEqual((self.video / 'estado.json').read_bytes(), before)

    def test_invalid_state_reports_error_and_keeps_previous_calendar(self):
        calendar = self.workspace / 'calendario.md'
        before = calendar.read_bytes()
        state_file = self.video / 'estado.json'
        state_file.write_text('{invalid json')
        result = self.hook('Stop')
        self.assertEqual(result.returncode, 1)
        self.assertIn('No se pudo sincronizar', result.stderr)
        self.assertEqual(calendar.read_bytes(), before)
        self.assertEqual(state_file.read_text(), '{invalid json')

    def test_malformed_hook_input_fails_before_writing(self):
        for payload in ('[]', '{broken', '{"hook_event_name":"SessionStart","prompt":12}',
                        '{"hook_event_name":"Unexpected"}'):
            before = (self.video / 'estado.json').read_bytes()
            result = subprocess.run([sys.executable, str(HOOK), '--root', str(self.workspace)],
                                    input=payload, text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, '')
            self.assertEqual((self.video / 'estado.json').read_bytes(), before)

    def test_configured_commands_work_in_checkout_with_spaces_and_nested_project_dir(self):
        # Ejecutar la configuración distribuida, no una reconstrucción del comando del hook.
        checkout = self.workspace / 'clon con espacios'
        shutil.copytree(ROOT / '.claude', checkout / '.claude', symlinks=True,
                        ignore=shutil.ignore_patterns('settings.local.json', '__pycache__', 'worktrees'))
        shutil.copytree(ROOT / 'skills', checkout / 'skills', ignore=shutil.ignore_patterns('__pycache__'))
        subprocess.run(['git', 'init', '-q', str(checkout)], check=True, capture_output=True)
        subprocess.run([sys.executable, str(checkout / 'skills/yt-video-flow/scripts/video_flow.py'),
                        'init', '--name', 'Retomable'], check=True, capture_output=True)
        nested = checkout / 'videos/V0001'
        config = json.loads((checkout / '.claude/settings.json').read_text())
        before = (nested / 'estado.json').read_bytes()
        for event, groups in config['hooks'].items():
            for group in groups:
                hook = group['hooks'][0]
                payload = {'hook_event_name': event, 'cwd': str(nested),
                           'tool_name': 'mcp__palmier-pro__add_clips', 'prompt': 'Retoma V0001'}
                result = subprocess.run(hook['command'], shell=True, cwd=nested,
                                        env={**os.environ, 'CLAUDE_PROJECT_DIR': str(nested)},
                                        input=json.dumps(payload), text=True, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((nested / 'estado.json').read_bytes(), before)

    def test_shared_instructions_and_mcp_config_have_no_private_credentials(self):
        claude = (ROOT / 'CLAUDE.md').read_text()
        self.assertIn('@AGENTS.md', claude)
        self.assertTrue((ROOT / 'AGENTS.md').is_file())
        server = json.loads((ROOT / '.mcp.json').read_text())['mcpServers']['palmier-pro']
        self.assertEqual(server, {'type': 'http', 'url': 'http://127.0.0.1:19789/mcp'})
        hooks = json.loads((ROOT / '.claude/settings.json').read_text())['hooks']
        for event in ('PreToolUse', 'PostToolUse'):
            matcher = re.compile(hooks[event][0]['matcher'])
            self.assertIsNotNone(matcher.fullmatch('mcp__palmier-pro__add_clips'))
            self.assertIsNotNone(matcher.fullmatch('mcp__palmier_pro__get_timeline'))
        self.assertNotIn('permissions', json.loads((ROOT / '.claude/settings.json').read_text()))


if __name__ == '__main__':
    unittest.main()
