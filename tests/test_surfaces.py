"""F14: the adapters only move bytes, and compare demands identical text from every supported surface."""

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from project_bootstrap import capabilities as cap
from project_bootstrap import surfaces
from project_bootstrap.surfaces import AdapterError

from tests.test_selftest import AG, SETTINGS, write

AG2 = {'handoff-git-check': dict(AG['handoff-git-check'], SessionStart=AG['handoff-git-check']['SessionStart'] + [
    {'type': 'command', 'command': '.\\ag-hook.cmd git-freshness.sh'}])}


def matrix(ide_missing=True):
    data = cap.read_matrix()
    if not ide_missing:
        cell = next(c for c in data['cells'] if c['id'] == 'antigravity-ide/hooks')
        cell['status'] = 'supported'
    return data


class DecodeTests(unittest.TestCase):
    def test_plain_surfaces_pass_text_through(self):
        for surface in ('claude-code', 'codex-cli', 'codex-app'):
            self.assertEqual(surfaces._decode(surface, '{"x": 1}\n'), '{"x": 1}\n')

    def test_antigravity_contract(self):
        ok = json.dumps({'injectSteps': [{'ephemeralMessage': 'a\n"b"\tc'}]})
        self.assertEqual(surfaces._decode('antigravity-2', ok), 'a\n"b"\tc\n')
        self.assertEqual(surfaces._decode('antigravity-cli', '{}\n'), '')
        bad = ['not json', '[]', json.dumps({'injectSteps': []}),
               json.dumps({'injectSteps': [{'ephemeralMessage': 'a'}, {'ephemeralMessage': 'b'}]}),
               json.dumps({'injectSteps': [{'ephemeralMessage': 1}]}),
               json.dumps({'injectSteps': [{'ephemeralMessage': 'a', 'x': 1}]}),
               json.dumps({'injectSteps': [{'ephemeralMessage': 'a'}], 'extra': 1}),
               json.dumps({'injectSteps': ['a']})]
        for text in bad:
            with self.assertRaises(AdapterError, msg=text):
                surfaces._decode('antigravity-ide', text)


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_exactly_one_wired_command(self):
        write(self.root, '.claude/settings.json', json.dumps(SETTINGS))
        self.assertEqual(len(surfaces._commands('claude-code', self.root)), 1)
        # A project's own SessionStart hook is not the check and is not run as one.
        own = {'hooks': {'SessionStart': SETTINGS['hooks']['SessionStart'] + [
            {'hooks': [{'type': 'command', 'command': 'echo project hook'}]}]}}
        write(self.root, '.claude/settings.json', json.dumps(own))
        self.assertEqual(len(surfaces._commands('claude-code', self.root)), 1)
        twice = {'hooks': {'SessionStart': SETTINGS['hooks']['SessionStart'] * 2}}
        write(self.root, '.claude/settings.json', json.dumps(twice))
        with self.assertRaises(AdapterError):
            surfaces._commands('claude-code', self.root)
        with self.assertRaises(AdapterError):
            surfaces._commands('codex-cli', self.root)
        write(self.root, '.codex/hooks.json', '{')
        with self.assertRaises(AdapterError):
            surfaces._commands('codex-cli', self.root)
        write(self.root, '.agents/hooks.json', json.dumps(AG2))
        self.assertEqual(len(surfaces._commands('antigravity-2', self.root)), 2)
        write(self.root, '.agents/hooks.json', json.dumps({'x': {'enabled': True, 'SessionStart': []}}))
        with self.assertRaises(AdapterError):
            surfaces._commands('antigravity-2', self.root)

    def test_antigravity_needs_exactly_one_speaking_handler(self):
        write(self.root, '.agents/hooks.json', json.dumps(AG2))
        message = json.dumps({'injectSteps': [{'ephemeralMessage': 'hi'}]})
        cases = [(['', message], 'hi\n'), ([message, ''], 'hi\n'), (['', ''], None), ([message, message], None)]
        for outputs, expected in cases:
            queue = list(outputs)

            def fake(argv, **kwargs):
                out = queue.pop(0)
                return mock.Mock(returncode=0 if out else 127, stdout=out)
            with mock.patch('subprocess.run', fake):
                if expected is None:
                    with self.assertRaises(AdapterError, msg=outputs):
                        surfaces.session_start('antigravity-cli', self.root, {})
                else:
                    result = surfaces.session_start('antigravity-cli', self.root, {})
                    self.assertEqual((result['text'], result['exit']), (expected, 0))

    def test_runs_from_the_surface_working_directory(self):
        seen = []
        write(self.root, '.agents/hooks.json', json.dumps(AG))
        write(self.root, '.claude/settings.json', json.dumps(SETTINGS))
        (self.root / 'sub').mkdir()

        def fake(argv, cwd, **kwargs):
            seen.append(Path(cwd))
            return mock.Mock(returncode=0, stdout='{}')
        with mock.patch('subprocess.run', fake):
            surfaces.session_start('antigravity-2', self.root, {}, subdir='sub')
            surfaces.session_start('claude-code', self.root, {}, subdir='sub')
        self.assertEqual(seen, [self.root / '.agents', self.root / 'sub'])


class CompareTests(unittest.TestCase):
    def run_compare(self, results, versions=None, data=None):
        calls = []

        def fake(surface, project, env, subdir=''):
            calls.append(surface)
            exit_code, text = results[surface]
            return {'exit': exit_code, 'raw': text, 'text': text}
        with mock.patch.object(surfaces, 'session_start', fake):
            out = surfaces.compare('/p', list(results), {}, data or matrix(), versions)
        return out, calls

    def test_identical_text_and_zero_exit_only(self):
        same = {'claude-code': (0, '[git-check] 全綠 2026-11-12 18:59：ok\n'),
                'codex-cli': (0, '[git-check] 全綠 2026-11-12 19:00：ok\n')}
        self.assertTrue(self.run_compare(same)[0]['equal'])
        differ = dict(same, **{'codex-cli': (0, '[git-check] 🔴 other\n')})
        self.assertFalse(self.run_compare(differ)[0]['equal'])
        failed = dict(same, **{'codex-cli': (1, same['claude-code'][1])})
        self.assertFalse(self.run_compare(failed)[0]['equal'])

    def test_matrix_missing_is_reported_not_run(self):
        results = {'claude-code': (0, 'x\n'), 'antigravity-ide': (0, 'different\n')}
        out, calls = self.run_compare(results, versions={'antigravity-ide': '1.107.0'})
        self.assertEqual(calls, ['claude-code'])
        self.assertTrue(out['equal'])
        self.assertIn('實測', out['unsupported']['antigravity-ide'])
        # Without a version the tested "missing" does not apply, so it is run and compared.
        out, calls = self.run_compare(results)
        self.assertEqual((calls, out['equal']), (['claude-code', 'antigravity-ide'], False))
        out, calls = self.run_compare(results, versions={'antigravity-ide': '1.107.0'}, data=matrix(False))
        self.assertEqual(calls, ['claude-code', 'antigravity-ide'])

    def test_normalise_only_clock_readings(self):
        self.assertEqual(surfaces.normalise('全綠 2026-11-12 18:59：x ㊣　26111218｜y'), '全綠 <time>：x ㊣　<time>｜y')
        self.assertEqual(surfaces.normalise('落後 2026-11-12 18:59'), '落後 2026-11-12 18:59')

    def test_neutral_env_drops_tool_identity_only(self):
        env = surfaces.neutral_env({'CLAUDECODE': '1', 'CODEX_SESSION_ID': 'x', 'CODEX_VERSION': '1',
                                    'GEMINI_CLI': '1', 'PATH': '/bin'})
        self.assertEqual(env, {'PATH': '/bin'})


if __name__ == '__main__':
    unittest.main()
