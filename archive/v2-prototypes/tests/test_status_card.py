"""F22／F23: the read-only status card reports each abnormal state and writes nothing."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from project_bootstrap.readonly import read_only
from project_bootstrap.status_card import card, main, render

IDLE_HANDOFF = '# HANDOFF\n\n- **工作中**：無（已交棒）\n\n## 服務查證與期望快照\n\n- 2026-11-11 驗證 exit 0\n'
BUSY = '- **工作中**：`desk` ／ `Codex CLI` ／ `㊣　26111108｜x｜工作中｜交棒0次`，2026-11-11 08:00 (+08) 開工'


class StatusCardTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='bootstrap-v2-card-')
        self.addCleanup(directory.cleanup)
        self.root = Path(os.path.realpath(directory.name))
        (self.root / 'home').mkdir()
        self.env = {'PATH': os.environ.get('PATH', ''), 'HOME': str(self.root / 'home'),
                    'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                    'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@example.invalid',
                    'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@example.invalid'}
        patcher = patch.dict(os.environ, self.env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.origin = self.root / 'origin.git'
        self.git(self.root, 'init', '--quiet', '--bare', '--initial-branch=main', str(self.origin))
        self.repo = self.clone('work')
        (self.repo / 'HANDOFF.md').write_text(IDLE_HANDOFF, encoding='utf-8')
        self.commit(self.repo, 'init')
        self.git(self.repo, 'push', '--quiet', '-u', 'origin', 'main')

    def git(self, cwd, *args):
        result = subprocess.run(['git', *args], cwd=cwd, env=self.env, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.decode().strip()

    def clone(self, name):
        target = self.root / name
        self.git(self.root, 'clone', '--quiet', str(self.origin), str(target))
        return target

    def commit(self, repo, message):
        self.git(repo, 'add', '-A')
        self.git(repo, 'commit', '--quiet', '-m', message)

    def other_pushes(self, text=None):
        self.pushes = getattr(self, 'pushes', 0) + 1
        other = self.clone('other-%d' % self.pushes)
        handoff = other / 'HANDOFF.md'
        handoff.write_text(text or handoff.read_text(encoding='utf-8') + '\n', encoding='utf-8')
        self.commit(other, 'other')
        self.git(other, 'push', '--quiet')

    def test_clean_idle_and_in_sync_is_all_green(self):
        facts = card(self.repo)
        self.assertEqual(facts['problems'], [])
        self.assertEqual((facts['fetch'], facts['ahead'], facts['behind']), ('ok', 0, 0))
        self.assertEqual(facts['remote_marker']['state'], 'idle')
        self.assertEqual(facts['last_evidence'], '2026-11-11 驗證 exit 0')
        self.assertIn('全綠', render(facts))

    def test_card_changes_nothing_but_remote_tracking_refs(self):
        self.other_pushes()
        (self.repo / 'note.txt').write_text('dirty', encoding='utf-8')
        facts, report = read_only(self.repo, lambda: card(self.repo), env=self.env)
        self.assertTrue(report['ok'], report)
        self.assertEqual(facts['problems'], ['dirty', 'behind'])

    def test_each_abnormal_state_is_named(self):
        cases = {}
        (self.repo / 'x.txt').write_text('x', encoding='utf-8')
        cases['dirty'] = card(self.repo)['problems']
        self.commit(self.repo, 'local')
        cases['ahead'] = card(self.repo)['problems']
        self.other_pushes()
        cases['diverged'] = card(self.repo)['problems']
        self.assertEqual(cases, {'dirty': ['dirty'], 'ahead': ['ahead'], 'diverged': ['diverged']})

    def test_remote_busy_marker_is_reported_not_judged(self):
        self.other_pushes(IDLE_HANDOFF.replace('- **工作中**：無（已交棒）', BUSY))
        facts = card(self.repo)
        self.assertEqual(facts['problems'], ['behind', 'remote-busy'])
        self.assertEqual(facts['remote_marker']['parts'][1], 'Codex CLI')
        self.assertIn('不是全綠', render(facts))

    def test_broken_remote_marker_is_not_read_as_idle(self):
        self.other_pushes(IDLE_HANDOFF.replace('無（已交棒）', '`desk`'))
        self.assertIn('remote-marker-malformed', card(self.repo)['problems'])
        self.other_pushes(IDLE_HANDOFF + '- **工作中**：無（已交棒）\n')
        self.assertIn('remote-marker-unreadable', card(self.repo)['problems'])

    def test_fetch_failure_and_skipped_fetch_are_not_green(self):
        self.assertEqual(card(self.repo, fetch=False)['problems'], ['fetch-skipped'])
        self.git(self.repo, 'remote', 'set-url', 'origin', str(self.root / 'gone.git'))
        facts = card(self.repo)
        self.assertEqual(facts['fetch'], 'failed')
        self.assertIn('fetch-failed', facts['problems'])

    def test_no_upstream_detached_and_not_a_repo(self):
        self.git(self.repo, 'branch', '--unset-upstream')
        self.assertEqual(card(self.repo)['problems'], ['no-upstream'])
        self.git(self.repo, 'checkout', '--quiet', '--detach')
        self.assertIn('detached-head', card(self.repo)['problems'])
        plain = self.root / 'plain'
        plain.mkdir()
        self.assertEqual(card(plain)['problems'], ['not-a-git-repo'])
        self.assertIn('不在 Git repo', render(card(plain)))

    def test_exit_code_follows_problems(self):
        with patch('builtins.print'):
            self.assertEqual(main([str(self.repo)]), 0)
            (self.repo / 'x.txt').write_text('x', encoding='utf-8')
            self.assertEqual(main([str(self.repo)]), 1)


if __name__ == '__main__':
    unittest.main()
