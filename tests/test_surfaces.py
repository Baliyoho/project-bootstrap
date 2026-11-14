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
        self.assertEqual(surfaces.normalise('全綠 2026-11-12 18:59：x ㊣　11.12.18｜y'), '全綠 <time>：x ㊣　<time>｜y')
        self.assertEqual(surfaces.normalise('落後 2026-11-12 18:59'), '落後 2026-11-12 18:59')

    def test_neutral_env_drops_tool_identity_only(self):
        env = surfaces.neutral_env({'CLAUDECODE': '1', 'CODEX_SESSION_ID': 'x', 'CODEX_VERSION': '1',
                                    'GEMINI_CLI': '1', 'PATH': '/bin'})
        self.assertEqual(env, {'PATH': '/bin'})


if __name__ == '__main__':
    unittest.main()


PUSH_SETTINGS = {'hooks': {'PreToolUse': [{'matcher': 'Bash|PowerShell', 'hooks': [
    {'type': 'command', 'command': 'bash "$(git rev-parse --show-cdup).claude/hooks/pre-push-handoff.sh"'}]}]}}
PUSH_CODEX = {'hooks': {'PreToolUse': [{'hooks': [
    {'type': 'command', 'command': 'bash "$(git rev-parse --show-cdup).claude/hooks/pre-push-handoff.sh"'}]}]}}


class PushAdapterTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        write(self.root, '.claude/settings.json', json.dumps(PUSH_SETTINGS))
        write(self.root, '.codex/hooks.json', json.dumps(PUSH_CODEX))

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_one_handler_with_its_matcher(self):
        self.assertEqual(surfaces._push_handler('claude-code', self.root)[0], 'Bash|PowerShell')
        self.assertIsNone(surfaces._push_handler('codex-cli', self.root)[0])
        for broken in ({'hooks': {}}, {'hooks': {'PreToolUse': {}}}, [],
                       {'hooks': {'PreToolUse': PUSH_CODEX['hooks']['PreToolUse'] * 2}},
                       {'hooks': {'PreToolUse': [{'hooks': [{'type': 'prompt', 'command': 'pre-push-handoff.sh'}]}]}}):
            write(self.root, '.codex/hooks.json', json.dumps(broken))
            with self.assertRaises(AdapterError, msg=broken):
                surfaces._push_handler('codex-cli', self.root)
        write(self.root, '.codex/hooks.json', '{')
        with self.assertRaises(AdapterError):
            surfaces._push_handler('codex-cli', self.root)

    def test_matcher_is_a_whole_name_regex(self):
        for matcher in (None, '', '*'):
            self.assertTrue(surfaces._matches(matcher, 'apply_patch'))
        self.assertTrue(surfaces._matches('Bash|PowerShell', 'PowerShell'))
        self.assertFalse(surfaces._matches('Bash|PowerShell', 'apply_patch'))
        self.assertFalse(surfaces._matches('Bash', 'BashOutput'))

    def test_skipped_by_matcher_is_not_run(self):
        calls = []

        def fake(argv, **kwargs):
            calls.append(kwargs['input'])
            return mock.Mock(returncode=2, stderr='blocked')
        with mock.patch('subprocess.run', fake):
            skipped = surfaces.pre_tool_use('claude-code', self.root, {}, {'tool_name': 'Edit'})
            ran = surfaces.pre_tool_use('codex-cli', self.root, {}, {'tool_name': 'Edit'})
        self.assertEqual(skipped, {'ran': False, 'exit': 0, 'stderr': ''})
        self.assertEqual(ran, {'ran': True, 'exit': 2, 'stderr': 'blocked'})
        self.assertEqual(json.loads(calls[0])['hook_event_name'], 'PreToolUse')

    def test_compare_push_needs_same_exit_and_stderr(self):
        def run_with(results, versions=None):
            def fake(surface, project, env, payload, subdir=''):
                exit_code, stderr = results[surface]
                return {'ran': True, 'exit': exit_code, 'stderr': stderr}
            with mock.patch.object(surfaces, 'pre_tool_use', fake):
                return surfaces.compare_push('/p', list(results), {}, {}, matrix(), versions)
        self.assertTrue(run_with({'claude-code': (2, 'x'), 'codex-cli': (2, 'x')})['equal'])
        self.assertFalse(run_with({'claude-code': (2, 'x'), 'codex-cli': (0, '')})['equal'])
        self.assertFalse(run_with({'claude-code': (2, 'x'), 'codex-cli': (2, 'y')})['equal'])
        out = run_with({'claude-code': (0, ''), 'antigravity-2': (2, 'never run')})
        self.assertTrue(out['equal'])
        self.assertEqual(list(out['unsupported']), ['antigravity-2'])
        self.assertIn('刻意不接', out['unsupported']['antigravity-2'])


class StderrTests(unittest.TestCase):
    def test_hook_stderr_breaks_equivalence_except_on_antigravity(self):
        # ag-wrap.sh folds stderr into the message (2>&1); Claude Code and Codex do not show it.
        for errors, equal in (({}, True), ({'codex-cli': 'warn\n'}, False), ({'antigravity-cli': 'warn\n'}, True)):
            def fake(surface, project, env, subdir=''):
                return {'exit': 0, 'raw': 'x\n', 'text': 'x\n', 'stderr': errors.get(surface, '')}
            with mock.patch.object(surfaces, 'session_start', fake):
                out = surfaces.compare('/p', ['claude-code', 'codex-cli', 'antigravity-cli'], {}, matrix())
            self.assertEqual(out['equal'], equal, errors)


AUTH = 'Triggers on 接棒、建立交接機制。'
LEAD = '指標檔，權威版在 .claude/skills/handoff/SKILL.md——'
POINTER_BODY = '**權威版：[`.claude/skills/handoff/SKILL.md`](../../../.claude/skills/handoff/SKILL.md)**\n'


def skill(description, body='# 入口\n'):
    return '---\nname: handoff\ndescription: %s\n---\n\n%s' % (description, body)


class ProcedureTests(unittest.TestCase):
    """Which instruction text and which skill files each surface reaches."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.project, self.home = self.tmp / 'p', self.tmp / 'home'
        self.put('AGENTS.md', '# AGENTS\n')
        self.put('CLAUDE.md', '@AGENTS.md\n')
        self.put('GEMINI.md', '請讀 [AGENTS.md](AGENTS.md)\n')
        self.put('.claude/skills/handoff/SKILL.md', skill(AUTH))
        self.put('.claude/skills/handoff/mode-a.md', 'A\n')
        self.put('.agents/skills/handoff/SKILL.md', skill(LEAD + AUTH, POINTER_BODY))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def put(self, relative, text, root=None):
        path = (root or self.project) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def compare(self, names=('claude-code', 'codex-cli', 'antigravity-cli'), data=None):
        return surfaces.compare_procedure(self.project, list(names), self.home, data or matrix())

    def test_pointer_is_followed_and_its_lead_dropped(self):
        out = self.compare()
        self.assertTrue(out['equal'], out['differ'])
        codex = out['runs']['codex-cli']
        self.assertEqual(codex['entry'], '專案 .agents/skills/handoff/SKILL.md')
        self.assertEqual(codex['description'], AUTH)
        self.assertEqual(sorted(codex['files']), ['SKILL.md', 'mode-a.md'])
        self.assertEqual(codex['files']['SKILL.md'], skill(AUTH))
        self.assertEqual(codex['instructions'], '# AGENTS\n')

    def test_pointer_missing_a_trigger_differs(self):
        self.put('.agents/skills/handoff/SKILL.md', skill(LEAD + 'Triggers on 接棒。', POINTER_BODY))
        out = self.compare()
        self.assertEqual((out['equal'], out['differ']), (False, ['description']))

    def test_pointer_needs_its_lead_and_an_existing_target(self):
        self.put('.agents/skills/handoff/SKILL.md', skill(AUTH, POINTER_BODY))
        with self.assertRaisesRegex(AdapterError, '指標開頭'):
            self.compare()
        self.put('.agents/skills/handoff/SKILL.md',
                 skill(LEAD + AUTH, POINTER_BODY.replace('(../../../.claude/skills/handoff/', '(../../../.claude/skills/gone/')))
        with self.assertRaisesRegex(AdapterError, '不存在'):
            self.compare()

    def test_frontmatter_must_name_handoff(self):
        self.put('.claude/skills/handoff/SKILL.md', skill(AUTH).replace('name: handoff', 'name: other'))
        with self.assertRaisesRegex(AdapterError, 'frontmatter'):
            self.compare(['claude-code'])
        self.put('.claude/skills/handoff/SKILL.md', '# no frontmatter\n')
        with self.assertRaisesRegex(AdapterError, 'frontmatter'):
            self.compare(['claude-code'])

    def test_codex_falls_back_to_home_and_a_stale_copy_differs(self):
        shutil.rmtree(self.project / '.agents')
        self.put('.codex/skills/handoff/SKILL.md', skill(AUTH), root=self.home)
        out = self.compare(['claude-code', 'codex-cli'])
        self.assertEqual(out['runs']['codex-cli']['entry'], '家目錄 ~/.codex/skills/handoff/SKILL.md')
        self.assertEqual(out['differ'], ['files'])
        # Antigravity has no home location to fall back to.
        with self.assertRaisesRegex(AdapterError, '找不到 handoff skill'):
            self.compare(['antigravity-cli'])

    def test_claude_code_home_skill_shadows_the_project_one(self):
        # Measured on Claude Code 2.1.321 (2026-11-12): the home copy wins.
        self.put('.claude/skills/handoff/SKILL.md', skill('Triggers on 舊。'), root=self.home)
        out = self.compare(['claude-code', 'codex-cli'])
        self.assertEqual(out['runs']['claude-code']['entry'], '家目錄 ~/.claude/skills/handoff/SKILL.md')
        self.assertEqual(out['runs']['claude-code']['description'], 'Triggers on 舊。')
        self.assertEqual(out['differ'], ['description', 'files'])
        # Codex still reaches the project copy through its pointer.
        self.assertEqual(out['runs']['codex-cli']['description'], AUTH)

    def test_instruction_files_must_lead_to_agents_md(self):
        self.put('CLAUDE.md', '請去讀 AGENTS.md\n')
        with self.assertRaisesRegex(AdapterError, '@AGENTS.md'):
            self.compare(['claude-code'])
        self.put('CLAUDE.md', '@AGENTS.md\n')
        self.put('GEMINI.md', '# 自己的規則\n')
        with self.assertRaisesRegex(AdapterError, 'GEMINI.md'):
            self.compare(['antigravity-cli'])
        self.put('AGENTS.md', '# changed\n')
        self.assertEqual(self.compare(['claude-code', 'codex-cli'])['runs']['codex-cli']['instructions'], '# changed\n')

    def test_matrix_missing_skill_loader_is_reported_not_run(self):
        data = matrix()
        cell = next(c for c in data['cells'] if c['id'] == 'codex-cli/loads-skill')
        cell.update(status='missing', basis='design', why='測試用')
        cell.pop('tested', None)
        shutil.rmtree(self.project / '.agents')
        out = self.compare(['claude-code', 'codex-cli'], data)
        self.assertEqual((list(out['runs']), list(out['unsupported'])), (['claude-code'], ['codex-cli']))
