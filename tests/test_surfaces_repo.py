"""F14 on the real package: the same project state gives the same session-start text on every surface.

A project is seeded from the package built from src/kit, with a local bare
origin. Each case puts the project in one state; every surface then runs its
own real wiring from its own working directory, and the decoded texts must be
identical. No tool and no model is involved: this is the wiring and adapter
layer only.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from project_bootstrap import package, surfaces

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import build_package  # noqa: E402

ALL = ('claude-code', 'codex-cli', 'codex-app', 'antigravity-cli', 'antigravity-2', 'antigravity-ide')
FREE = '- **工作中**：無（已交棒）\n'


class Fixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder, manifest = build_package.build_once()
        cls.package, cls.files = Path(folder), sorted(manifest['components'])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.package)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.env = surfaces.neutral_env({'PATH': os.environ.get('PATH', os.defpath)})
        self.env.update({'HOME': str(self.tmp), 'HOSTNAME': 'test-host', 'GIT_CONFIG_NOSYSTEM': '1',
                         'BOOTSTRAP_VERSION_CHECK': 'off', 'LC_ALL': 'C.UTF-8',
                         'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@example.invalid',
                         'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@example.invalid'})
        self.git('init', '-q', '--bare', '-b', 'main', str(self.tmp / 'origin.git'), cwd=self.tmp)
        self.work = self.tmp / 'work'
        self.git('clone', '-q', str(self.tmp / 'origin.git'), str(self.work), cwd=self.tmp)
        for relative in self.files:
            target = self.work / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.package / relative, target)
        self.handoff(FREE)
        self.git('add', '-A')
        self.git('commit', '-q', '-m', 'seed')
        self.git('push', '-q', '-u', 'origin', 'main')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def git(self, *args, cwd=None):
        return subprocess.run(['git', *args], cwd=cwd or self.work, env=self.env, check=True,
                              capture_output=True, text=True).stdout

    def handoff(self, line, where=None):
        (where or self.work).joinpath('HANDOFF.md').write_text(
            '# HANDOFF\n\n## Git 狀態\n\n' + line, encoding='utf-8')

    def other_clone(self):
        other = self.tmp / 'other'
        self.git('clone', '-q', str(self.tmp / 'origin.git'), str(other), cwd=self.tmp)
        return other

    def compare(self, env=None, versions=None):
        result = surfaces.compare(self.work, ALL, env or self.env, versions=versions, subdir='docs')
        texts = {s: r['text'] for s, r in result['runs'].items()}
        self.assertTrue(result['equal'], texts)
        self.assertEqual(set(result['runs']) | set(result['unsupported']), set(ALL))
        return next(iter(texts.values()))


class RepoSurfaceTests(Fixture):
    def test_green(self):
        text = self.compare()
        self.assertIn('[git-check] 全綠 <time>', text)
        self.assertIn('「工作中」是「無（已交棒）」', text)
        self.assertIn('[handoff] 開工改名用', text)

    def test_ide_is_named_unsupported_on_its_measured_version(self):
        result = surfaces.compare(self.work, ALL, self.env, versions={'antigravity-ide': '1.107.0'}, subdir='docs')
        self.assertTrue(result['equal'])
        self.assertEqual(list(result['unsupported']), ['antigravity-ide'])
        self.assertEqual(len(result['runs']), 5)

    def test_behind(self):
        other = self.other_clone()
        (other / 'note.txt').write_text('x\n', encoding='utf-8')
        self.git('add', 'note.txt', cwd=other)
        self.git('commit', '-q', '-m', 'ahead', cwd=other)
        self.git('push', '-q', cwd=other)
        self.assertIn('本地過時：落後 origin 1 個 commit', self.compare())

    def test_dirty(self):
        (self.work / 'scratch.txt').write_text('x\n', encoding='utf-8')
        self.assertIn('工作區有 1 個未提交變更', self.compare())

    def test_occupied_by_another_machine(self):
        other = self.other_clone()
        self.handoff('- **工作中**：`desk-win` ／ `Codex CLI` ／ `㊣　26111201｜x｜工作中｜交棒0次`，開工\n', other)
        self.git('commit', '-q', '-am', 'busy', cwd=other)
        self.git('push', '-q', cwd=other)
        self.git('pull', '-q', '--ff-only')
        text = self.compare()
        self.assertIn('另一台機器正在 main 上工作', text)
        self.assertNotIn('[git-check] 全綠', text)
        self.assertIn('不是全綠', text)

    def test_same_machine_other_tool_with_the_same_identity_everywhere(self):
        # The hook may tell tools apart; the adapters must not change what it sees.
        self.handoff('- **工作中**：`test-host` ／ `Codex CLI` ／ `x`，開工\n')
        self.git('commit', '-q', '-am', 'busy')
        self.git('push', '-q')
        env = dict(self.env, CLAUDECODE='1')
        self.assertIn('同一台機器（test-host）上另一個工具', self.compare(env))

    def test_no_upstream(self):
        self.git('switch', '-q', '-c', 'feature')
        self.assertIn('branch=feature 沒有 upstream', self.compare())

    def test_fetch_fails(self):
        self.git('remote', 'set-url', 'origin', str(self.tmp / 'gone.git'))
        self.assertIn('無法 fetch origin', self.compare())


if __name__ == '__main__':
    unittest.main()


PUSH_SURFACES = ('claude-code', 'codex-cli', 'codex-app', 'antigravity-cli', 'antigravity-2', 'antigravity-ide')


class RepoPushTests(Fixture):
    """The push reminder (3.11) on the same states; Antigravity is named unsupported (3.20)."""

    def unpushed(self, touch_handoff=False):
        self.commits = getattr(self, 'commits', 0) + 1
        (self.work / 'work.txt').write_text('%d\n' % self.commits, encoding='utf-8')
        if touch_handoff:
            self.handoff('- **工作中**：無（已交棒）\n\n交棒\n')
        self.git('add', '-A')
        self.git('commit', '-q', '-m', 'work')

    def push_compare(self, payload):
        result = surfaces.compare_push(self.work, PUSH_SURFACES, self.env, payload, subdir='docs')
        self.assertEqual(sorted(result['unsupported']), ['antigravity-2', 'antigravity-cli', 'antigravity-ide'])
        return result

    def bash(self, command):
        return {'tool_name': 'Bash', 'tool_input': {'command': command}}

    def test_push_without_handoff_is_blocked_the_same_way(self):
        self.unpushed()
        result = self.push_compare(self.bash('git push'))
        self.assertTrue(result['equal'], result['runs'])
        self.assertEqual({r['exit'] for r in result['runs'].values()}, {2})
        self.assertIn('[handoff-check]', result['runs']['claude-code']['stderr'])

    def test_allowed_cases_are_the_same(self):
        self.unpushed()
        for payload in (self.bash('git status -sb'), dict(self.bash('git push'))):
            env = dict(self.env, HANDOFF_HOOK='off') if payload['tool_input']['command'] == 'git push' else self.env
            result = surfaces.compare_push(self.work, PUSH_SURFACES, env, payload, subdir='docs')
            self.assertTrue(result['equal'], payload)
            self.assertEqual({r['exit'] for r in result['runs'].values()}, {0})

    def test_handoff_in_the_commits_and_feature_branch_pass(self):
        self.unpushed(touch_handoff=True)
        result = self.push_compare(self.bash('git push'))
        self.assertEqual(({r['exit'] for r in result['runs'].values()}, result['equal']), ({0}, True))
        self.git('switch', '-q', '-c', 'feature')
        self.unpushed()
        self.git('push', '-q', '-u', 'origin', 'feature')
        self.unpushed()
        result = self.push_compare(self.bash('git push'))
        self.assertEqual(({r['exit'] for r in result['runs'].values()}, result['equal']), ({0}, True))

    def test_non_shell_tool_mentioning_git_push_is_allowed_everywhere(self):
        # Found 2026-11-12 (decision Q27): Codex wires PreToolUse without a matcher (3.17),
        # and the hook used to match the literal text anywhere in the payload, so a patch
        # mentioning git push was blocked on Codex only. Since Q27 (a) the hook reads only
        # the command field: Codex runs it and allows, Claude Code never runs it.
        self.unpushed()
        payload = {'tool_name': 'apply_patch', 'tool_input': {'input': '*** 說明：收工再 git push\n'}}
        result = self.push_compare(payload)
        self.assertTrue(result['equal'], result['runs'])
        self.assertEqual((result['runs']['claude-code']['ran'], result['runs']['claude-code']['exit']), (False, 0))
        self.assertEqual((result['runs']['codex-cli']['ran'], result['runs']['codex-cli']['exit']), (True, 0))


class RepoProcedureTests(Fixture):
    """The instruction text and handoff skill each surface reaches, on the real package."""

    def test_every_surface_reaches_the_same_procedure(self):
        result = surfaces.compare_procedure(self.work, ALL, self.tmp / 'home')
        self.assertEqual((result['equal'], result['differ'], result['unsupported']), (True, [], {}))
        claude, codex = result['runs']['claude-code'], result['runs']['codex-cli']
        self.assertEqual(claude['entry'], '專案 .claude/skills/handoff/SKILL.md')
        self.assertEqual(codex['entry'], '專案 .agents/skills/handoff/SKILL.md')
        self.assertEqual(sorted(codex['files']), ['SKILL.md', 'mode-0.md', 'mode-a-stop.md', 'mode-a.md',
                                                  'mode-b.md', 'reasons.md'])
        # Found 2026-11-12: the pointer's description had lost the mode 0 sentence and
        # three trigger words the authoritative one gained, so Codex and Antigravity
        # would not load the procedure on words that load it in Claude Code.
        self.assertIn('幫我建 HANDOFF', codex['description'])

    def test_a_stale_global_copy_is_not_the_same_procedure(self):
        # Without the project pointer Codex falls back to ~/.codex/skills/handoff/.
        shutil.rmtree(self.work / '.agents' / 'skills')
        stale = self.tmp / 'home' / '.codex' / 'skills' / 'handoff'
        shutil.copytree(self.work / '.claude' / 'skills' / 'handoff', stale)
        (stale / 'mode-a.md').write_text('# 舊版\n', encoding='utf-8')
        result = surfaces.compare_procedure(self.work, ('claude-code', 'codex-cli', 'codex-app'), self.tmp / 'home')
        self.assertEqual((result['equal'], result['differ']), (False, ['files']))

    def test_a_different_global_claude_skill_shadows_the_project(self):
        # Measured 2026-11-12 on Claude Code 2.1.321: with a handoff skill in both
        # ~/.claude/skills/ and the project, the Skill tool loaded the home copy.
        home = self.tmp / 'home' / '.claude' / 'skills' / 'handoff'
        shutil.copytree(self.work / '.claude' / 'skills' / 'handoff', home)
        result = surfaces.compare_procedure(self.work, ALL, self.tmp / 'home')
        self.assertTrue(result['equal'], result['differ'])
        (home / 'mode-b.md').write_text('# 別版\n', encoding='utf-8')
        result = surfaces.compare_procedure(self.work, ALL, self.tmp / 'home')
        self.assertEqual((result['equal'], result['differ']), (False, ['files']))
        self.assertEqual(result['runs']['claude-code']['entry'], '家目錄 ~/.claude/skills/handoff/SKILL.md')
