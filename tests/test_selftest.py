"""F47: version detection and install self-test never guess and never upgrade a capability."""

import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile
import unittest

from project_bootstrap import capabilities as cap
from project_bootstrap import package, pointer, selftest
from project_bootstrap.contracts import Denied

from tests.test_capabilities import synthetic

SETTINGS = {'hooks': {'SessionStart': [{'hooks': [
    {'type': 'command', 'command': 'bash "$(git rev-parse --show-cdup).claude/hooks/git-freshness.sh"'}]}]}}
AG = {'handoff-git-check': {'enabled': True, 'SessionStart': [
    {'type': 'command', 'command': '../.claude/hooks/ag-wrap.sh git-freshness.sh'}]}}


class Done:
    def __init__(self, code, out):
        self.returncode, self.stdout = code, out


def runner(table):
    def run(argv, **kwargs):
        value = table[argv[0]]
        if isinstance(value, Exception):
            raise value
        return Done(*value)
    return run


class DetectTests(unittest.TestCase):
    def test_command_on_path(self):
        found = selftest.detect_version('codex-cli', which=lambda n: '/bin/' + n,
                                        run=runner({'/bin/codex': (0, 'codex-cli 0.166.0\n')}), environ={})
        self.assertEqual(found['version'], '0.166.0')

    def test_failures_are_none_not_guesses(self):
        cases = [
            (lambda n: None, {}),
            (lambda n: '/bin/' + n, {'/bin/codex': (1, 'codex-cli 0.166.0')}),
            (lambda n: '/bin/' + n, {'/bin/codex': (0, 'codex-cli dev build')}),
            (lambda n: '/bin/' + n, {'/bin/codex': subprocess.TimeoutExpired('codex', 15)}),
            (lambda n: '/bin/' + n, {'/bin/codex': OSError('gone')}),
        ]
        for which, table in cases:
            found = selftest.detect_version('codex-cli', which=which, run=runner(table), environ={})
            self.assertIsNone(found['version'], table)
        self.assertIsNone(selftest.detect_version('antigravity-sdk')['version'])

    def test_claude_falls_back_to_running_executable(self):
        found = selftest.detect_version(
            'claude-code', which=lambda n: None, environ={'CLAUDE_CODE_EXECPATH': '/x/claude'},
            run=runner({'/x/claude': (0, '2.1.321 (Claude Code)\n')}))
        self.assertEqual(found['version'], '2.1.321')
        # A broken PATH copy does not hide the running one; a bad running one is not used.
        found = selftest.detect_version(
            'claude-code', which=lambda n: '/bin/claude', environ={'CLAUDE_CODE_EXECPATH': '/x/claude'},
            run=runner({'/bin/claude': (1, ''), '/x/claude': (0, '2.1.300 (Claude Code)')}))
        self.assertEqual(found['version'], '2.1.300')
        self.assertIsNone(selftest.detect_version(
            'codex-cli', which=lambda n: None, environ={'CLAUDE_CODE_EXECPATH': '/x/claude'},
            run=runner({'/x/claude': (0, '2.1.321')}))['version'])

    def app(self, apps, name, version):
        folder = Path(apps) / name / 'Contents'
        folder.mkdir(parents=True)
        with open(folder / 'Info.plist', 'wb') as handle:
            plistlib.dump({'CFBundleShortVersionString': version}, handle)

    def test_app_bundle_and_major_version(self):
        with tempfile.TemporaryDirectory() as apps:
            self.assertIsNone(selftest.detect_version('codex-app', apps=apps)['version'])
            self.app(apps, 'Antigravity.app', '2.31.0')
            self.assertEqual(selftest.detect_version('antigravity-2', apps=apps)['version'], '2.31.0')
            self.assertIsNone(selftest.detect_version('antigravity-ide', apps=apps)['version'])
            self.app(apps, 'Codex.app', 'beta')
            self.assertIsNone(selftest.detect_version('codex-app', apps=apps)['version'])
        with tempfile.TemporaryDirectory() as apps:
            self.app(apps, 'Antigravity.app', 'beta')
            self.assertIsNone(selftest.detect_version('antigravity-2', apps=apps)['version'])
        with tempfile.TemporaryDirectory() as apps:
            self.app(apps, 'Antigravity.app', '1.107.0')
            self.assertEqual(selftest.detect_version('antigravity-ide', apps=apps)['version'], '1.107.0')
            self.assertIsNone(selftest.detect_version('antigravity-2', apps=apps)['version'])
            (Path(apps) / 'Codex.app' / 'Contents').mkdir(parents=True)
            (Path(apps) / 'Codex.app' / 'Contents' / 'Info.plist').write_bytes(b'not a plist')
            self.assertIsNone(selftest.detect_version('codex-app', apps=apps)['version'])


def write(root, relative, text, mode=0o644):
    path = Path(root) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    path.chmod(mode)


def wired_project(root):
    write(root, 'AGENTS.md', '# rules\n')
    write(root, 'CLAUDE.md', '@AGENTS.md\n')
    write(root, 'GEMINI.md', '讀 AGENTS.md\n')
    for skill in ('.claude/skills/handoff/SKILL.md', '.agents/skills/handoff/SKILL.md'):
        write(root, skill, 'skill\n')
    write(root, '.claude/settings.json', json.dumps(SETTINGS))
    write(root, '.codex/hooks.json', json.dumps(SETTINGS))
    write(root, '.agents/hooks.json', json.dumps(AG))
    write(root, '.claude/hooks/git-freshness.sh', '#!/bin/sh\n', 0o755)
    write(root, '.claude/hooks/ag-wrap.sh', '#!/bin/sh\n', 0o755)


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.home = Path(tempfile.mkdtemp())
        wired_project(self.root)

    def tearDown(self):
        shutil.rmtree(self.root)
        shutil.rmtree(self.home)

    def checks(self, surface):
        return selftest.install_checks(surface, self.root, self.home)

    def failed(self, surface):
        return sorted(k for k, v in self.checks(surface).items() if not v['ok'])

    def test_wired_project_passes_everywhere(self):
        for surface in selftest.SKILLS:
            self.assertEqual(self.failed(surface), [], surface)
        self.assertEqual(selftest.install_checks('antigravity-sdk', self.root, self.home), {})

    def test_instruction_files(self):
        write(self.root, 'CLAUDE.md', '去讀 AGENTS.md\n')
        self.assertEqual(self.failed('claude-code'), ['reads-agents-md'])
        write(self.root, 'CLAUDE.md', '規則見 @AGENTS.md 的開頭\n')
        self.assertEqual(self.failed('claude-code'), ['reads-agents-md'])
        self.assertEqual(self.failed('codex-cli'), [])
        (self.root / 'CLAUDE.md').unlink()
        self.assertEqual(self.failed('claude-code'), [])
        write(self.root, 'GEMINI.md', '# gemini\n')
        self.assertEqual(self.failed('antigravity-cli'), ['reads-agents-md'])
        self.assertEqual(self.failed('claude-code'), [])
        (self.root / 'GEMINI.md').unlink()
        (self.root / 'AGENTS.md').unlink()
        self.assertIn('reads-agents-md', self.failed('codex-cli'))

    def test_skill_in_project_or_home(self):
        shutil.rmtree(self.root / '.claude' / 'skills')
        self.assertEqual(self.failed('claude-code'), ['loads-skill'])
        write(self.home, '.claude/skills/handoff/SKILL.md', 'skill\n')
        self.assertEqual(self.failed('claude-code'), [])
        write(self.root, '.agents/skills/handoff/SKILL.md', '  \n')
        self.assertEqual(self.failed('codex-cli'), ['loads-skill'])
        self.assertEqual(self.failed('antigravity-2'), ['loads-skill'])
        write(self.home, '.codex/skills/handoff/SKILL.md', 'skill\n')
        self.assertEqual(self.failed('codex-app'), [])
        # Antigravity has no home skill folder in the matrix: the Codex one does not count.
        self.assertEqual(self.failed('antigravity-2'), ['loads-skill'])

    def test_hook_wiring(self):
        bad = [('{', 'claude-code'), ('[]', 'codex-cli'), ('{"hooks": []}', 'claude-code'),
               (json.dumps({'hooks': {'SessionStart': [{'hooks': [
                   {'type': 'command', 'command': 'bash .claude/hooks/repo-check.sh'}]}]}}), 'claude-code'),
               (json.dumps({'hooks': {'SessionStart': [{'hooks': [
                   {'type': 'prompt', 'command': 'git-freshness.sh'}]}]}}), 'codex-cli')]
        for text, surface in bad:
            write(self.root, selftest.WIRING[surface], text)
            self.assertEqual(self.failed(surface), ['hooks'], text)
            write(self.root, selftest.WIRING[surface], json.dumps(SETTINGS))
        (self.root / '.claude/settings.json').unlink()
        self.assertEqual(self.failed('claude-code'), ['hooks'])
        self.assertEqual(self.failed('codex-cli'), [])
        (self.root / '.claude/hooks/git-freshness.sh').unlink()
        self.assertEqual(self.failed('codex-cli'), ['hooks'])

    def test_antigravity_wiring(self):
        write(self.root, '.agents/hooks.json', json.dumps(
            {'handoff-git-check': dict(AG['handoff-git-check'], enabled=False)}))
        self.assertEqual(self.failed('antigravity-cli'), ['hooks'])
        write(self.root, '.agents/hooks.json', json.dumps({'x': {'enabled': True, 'SessionStart': [
            {'type': 'command', 'command': 'bash ../.claude/hooks/git-freshness.sh'}]}}))
        self.assertEqual(self.failed('antigravity-cli'), ['hooks'])
        write(self.root, '.agents/hooks.json', json.dumps(AG))
        (self.root / '.claude/hooks/ag-wrap.sh').chmod(0o644)
        self.assertEqual(self.failed('antigravity-2'), ['hooks'])
        # Claude Code runs the scripts through bash; the wrapper's mode is not its business.
        self.assertEqual(self.failed('claude-code'), [])


WIN_SETTINGS = {'hooks': {'SessionStart': [{'hooks': [dict(
    SETTINGS['hooks']['SessionStart'][0]['hooks'][0],
    commandWindows='cmd /d /c ".claude\\hooks\\codex-hook.cmd" git-freshness.sh')]}]}}
WIN_AG = {'handoff-git-check': dict(AG['handoff-git-check'], SessionStart=AG['handoff-git-check']['SessionStart'] + [
    {'type': 'command', 'command': '.\\ag-hook.cmd git-freshness.sh'}])}


class WindowsCheckTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        wired_project(self.root)
        write(self.root, '.codex/hooks.json', json.dumps(WIN_SETTINGS))
        write(self.root, '.agents/hooks.json', json.dumps(WIN_AG))
        write(self.root, '.claude/hooks/codex-hook.cmd', '@echo off\n')
        write(self.root, '.agents/ag-hook.cmd', '@echo off\n')

    def tearDown(self):
        shutil.rmtree(self.root)

    def failed(self, surface, platform='windows'):
        checks = selftest.install_checks(surface, self.root, self.root, platform)
        return sorted(k for k, v in checks.items() if not v['ok'])

    def test_both_platforms_pass_on_full_wiring(self):
        for surface in selftest.SKILLS:
            self.assertEqual(self.failed(surface), [], surface)
            self.assertEqual(self.failed(surface, 'posix'), [], surface)
        with self.assertRaises(ValueError):
            selftest.install_checks('codex-cli', self.root, self.root, 'beos')

    def test_codex_needs_command_windows_and_launcher(self):
        write(self.root, '.codex/hooks.json', json.dumps(SETTINGS))
        self.assertEqual(self.failed('codex-cli'), ['hooks'])
        self.assertEqual(self.failed('codex-cli', 'posix'), [])
        bad = json.loads(json.dumps(WIN_SETTINGS))
        bad['hooks']['SessionStart'][0]['hooks'][0]['commandWindows'] = 'cmd /d /c ".claude\\hooks\\codex-hook.cmd" pre-push-handoff.sh'
        write(self.root, '.codex/hooks.json', json.dumps(bad))
        self.assertEqual(self.failed('codex-app'), ['hooks'])
        write(self.root, '.codex/hooks.json', json.dumps(WIN_SETTINGS))
        (self.root / '.claude/hooks/codex-hook.cmd').unlink()
        self.assertEqual(self.failed('codex-cli'), ['hooks'])
        self.assertEqual(self.failed('codex-cli', 'posix'), [])

    def test_antigravity_needs_the_shim_handler_and_files(self):
        write(self.root, '.agents/hooks.json', json.dumps(AG))
        self.assertEqual(self.failed('antigravity-2'), ['hooks'])
        self.assertEqual(self.failed('antigravity-2', 'posix'), [])
        write(self.root, '.agents/hooks.json', json.dumps(WIN_AG))
        (self.root / '.claude/hooks/ag-wrap.sh').chmod(0o644)
        # Windows runs ag-wrap.sh through Git Bash: the mode bit is not needed there.
        self.assertEqual(self.failed('antigravity-cli'), [])
        self.assertEqual(self.failed('antigravity-cli', 'posix'), ['hooks'])
        for needed in ('.agents/ag-hook.cmd', '.claude/hooks/ag-wrap.sh'):
            moved = self.root / (needed + '.bak')
            (self.root / needed).rename(moved)
            self.assertEqual(self.failed('antigravity-ide'), ['hooks'], needed)
            moved.rename(self.root / needed)

    def test_claude_code_has_one_command_for_both(self):
        self.assertEqual(self.failed('claude-code'), [])
        (self.root / '.claude/hooks/git-freshness.sh').unlink()
        self.assertEqual(self.failed('claude-code'), ['hooks'])

    def test_run_reports_the_platform(self):
        (self.root / '.claude/hooks/codex-hook.cmd').unlink()
        result = selftest.run('codex-cli', self.root, version='0.164.0', home=self.root, platform='windows')
        self.assertEqual(result['platform'], 'windows')
        self.assertIn('hooks', result['gaps'])
        result = selftest.run('codex-cli', self.root, version='0.164.0', home=self.root, platform='posix')
        self.assertNotIn('hooks', result['gaps'])
        self.assertEqual(selftest.run('codex-cli', self.root, version='1', home=self.root)['platform'],
                         selftest.THIS_PLATFORM)


class ReportWithChecksTests(unittest.TestCase):
    def setUp(self):
        self.data = cap.validate(synthetic())

    def rows(self, **kwargs):
        return {r['capability']: r for r in cap.report(self.data, 'a-cli', '1.2.0', **kwargs)['rows']}

    def test_failed_check_makes_missing_passed_never_upgrades(self):
        rows = self.rows(checks={'hooks': {'ok': False, 'detail': 'no wiring'}})
        self.assertEqual((rows['hooks']['state'], rows['hooks']['check']), ('missing', 'fail'))
        self.assertIn('no wiring', rows['hooks']['why'])
        self.assertIn('alternative', rows['hooks'])
        rows = self.rows(checks={'docs-only': {'ok': True, 'detail': 'wired'}})
        self.assertEqual((rows['docs-only']['state'], rows['docs-only']['check']), ('unverified', 'pass'))
        result = cap.report(self.data, 'a-cli', '1.2.0', checks={'gate': {'ok': True, 'detail': 'x'}})
        self.assertFalse(result['strict_ready'])
        # A failed install check wins over a passed runtime probe.
        rows = self.rows(probes={'hooks': lambda: True}, checks={'hooks': {'ok': False, 'detail': 'gone'}})
        self.assertEqual(rows['hooks']['state'], 'missing')
        self.assertEqual(self.rows()['hooks']['check'], 'not-run')

    def test_bad_checks_are_refused(self):
        for checks in ({'nope': {'ok': True, 'detail': ''}}, {'hooks': {'ok': 1, 'detail': ''}},
                       {'hooks': {'ok': True}}, {'hooks': True},
                       {'hooks': {'ok': True, 'detail': None}}):
            with self.assertRaises(cap.MatrixError, msg=checks):
                cap.report(self.data, 'a-cli', '1.2.0', checks=checks)


PROSE = '# kit\n> 版本：**2026-11-12**\n'
FILES = {'AGENTS.md': '# a\n'}
OWNERS = {'AGENTS.md': {'owner': 'project', 'update': 'seed'}}


class PackagedMatrixTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def cached(self, matrix):
        folder, manifest = package.build(PROSE, FILES, OWNERS, 'kit', matrix)
        digest = package.digest(manifest)
        package.install(folder, self.tmp / 'cache' / digest)
        project = self.tmp / ('p-' + digest[:8])
        write(project, pointer.POINTER, json.dumps(
            {'schema': 1, 'channel': 'beta', 'installed': digest, 'exception': None}))
        wired_project(project)
        return project, digest

    def test_matrix_is_signed_with_the_manifest(self):
        folder, manifest = package.build(PROSE, FILES, OWNERS, 'kit', synthetic())
        _, without = package.build(PROSE, FILES, OWNERS, 'kit')
        self.assertNotEqual(package.digest(manifest), package.digest(without))
        self.assertEqual(cap.from_manifest(manifest), synthetic())
        with self.assertRaises(cap.MatrixError):
            cap.from_manifest(without)
        with self.assertRaises(cap.MatrixError):
            cap.from_manifest(dict(manifest, capabilities={'schema': 2}))
        self.assertEqual(package.check(folder), [])
        data = json.loads((Path(folder) / package.MANIFEST).read_text(encoding='utf-8'))
        data['capabilities']['schema'] = 2
        (Path(folder) / package.MANIFEST).write_text(json.dumps(data), encoding='utf-8')
        self.assertIn('capabilities-invalid', package.check(folder))
        shutil.rmtree(folder)
        broken = synthetic()
        broken['cells'][0]['status'] = 'maybe'
        with self.assertRaises(Denied):
            package.build(PROSE, FILES, OWNERS, 'kit', broken)

    def test_run_reads_the_installed_package_only(self):
        changed = synthetic()
        changed['surfaces']['claude-code'] = {'tool': 'C', 'label': 'C'}
        project, digest = self.cached(changed)
        result = selftest.run('claude-code', project, self.tmp / 'cache', version='9.9',
                              home=self.tmp / 'home')
        self.assertEqual(result['matrix'], 'installed ' + digest)
        self.assertEqual(result['version_source'], '呼叫端指定')
        self.assertEqual({r['capability'] for r in result['rows']}, set(changed['capabilities']))
        self.assertEqual(result['checks_without_capability'], ['loads-skill', 'reads-agents-md'])
        checked = {r['capability']: r['check'] for r in result['rows']}
        self.assertEqual(checked, {'hooks': 'pass', 'docs-only': 'not-run', 'gate': 'not-run'})
        old, _ = self.cached(None)
        with self.assertRaisesRegex(Denied, 'package-without-capabilities'):
            selftest.run('claude-code', old, self.tmp / 'cache', version='1')
        (project / pointer.POINTER).unlink()
        with self.assertRaisesRegex(Denied, 'no-pointer'):
            selftest.run('claude-code', project, self.tmp / 'cache', version='1')
        write(project, pointer.POINTER, json.dumps(
            {'schema': 1, 'channel': 'beta', 'installed': 'f' * 64, 'exception': None}))
        with self.assertRaisesRegex(Denied, 'package-not-cached'):
            selftest.run('claude-code', project, self.tmp / 'cache', version='1')

    def test_damaged_or_renamed_package_is_refused(self):
        project, digest = self.cached(synthetic())
        manifest_path = self.tmp / 'cache' / digest / package.MANIFEST
        data = json.loads(manifest_path.read_text(encoding='utf-8'))
        data['capabilities']['capabilities']['hooks']['strict'] = True
        manifest_path.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaisesRegex(Denied, 'package-mismatch'):
            selftest.run('a-cli', project, self.tmp / 'cache', version='1.2.0')
        (self.tmp / 'cache' / digest / 'AGENTS.md').write_text('# changed\n', encoding='utf-8')
        with self.assertRaisesRegex(Denied, 'package-damaged'):
            selftest.run('a-cli', project, self.tmp / 'cache', version='1.2.0')

    def test_detects_when_no_version_given(self):
        project, _ = self.cached(synthetic())
        seen = []
        result = selftest.run('a-cli', project, self.tmp / 'cache', home=self.tmp,
                              detect=lambda s: seen.append(s) or {'version': None, 'source': 'none'})
        self.assertEqual((seen, result['version'], result['version_source']), (['a-cli'], None, 'none'))


if __name__ == '__main__':
    unittest.main()
