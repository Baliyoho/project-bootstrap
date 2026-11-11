"""F23: a read turn may fetch and read, but owner, commit, stage and push are seen."""

import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

from project_bootstrap.gitclaim import IDLE
from project_bootstrap.readonly import read_only

ME = '`mac` ／ `Claude Code` ／ `㊣　26110923｜問答｜工作中｜交棒0次`'


def handoff(owner):
    return f'# HANDOFF\n\n- **工作中**：{owner}\n'


class ReadOnlyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='bootstrap-v2-readonly-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'home').mkdir()
        self.env = {'PATH': os.environ.get('PATH', ''), 'HOME': str(self.root / 'home'),
                    'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                    'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@example.invalid',
                    'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@example.invalid'}
        self.origin = self.root / 'origin.git'
        self.git(self.root, 'init', '--quiet', '--bare', '--initial-branch=main', str(self.origin))
        self.repo = self.root / 'work'
        self.git(self.root, 'clone', '--quiet', str(self.origin), str(self.repo))
        (self.repo / 'HANDOFF.md').write_text(handoff(IDLE), encoding='utf-8')
        self.git(self.repo, 'add', 'HANDOFF.md')
        self.git(self.repo, 'commit', '--quiet', '-m', 'init')
        self.git(self.repo, 'push', '--quiet', '-u', 'origin', 'main')

    def git(self, cwd, *args):
        result = subprocess.run(['git', *args], cwd=cwd, env=self.env, capture_output=True)
        if result.returncode:
            raise AssertionError(result.stderr.decode())
        return result.stdout.decode()

    def run_read(self, action):
        return read_only(self.repo, action, env=self.env)[1]

    def test_answering_with_reads_and_fetch_is_clean(self):
        other = self.root / 'other'
        self.git(self.root, 'clone', '--quiet', str(self.origin), str(other))

        def answer():
            text = (self.repo / 'HANDOFF.md').read_text(encoding='utf-8')
            self.git(self.repo, 'log', '--oneline')
            self.git(self.repo, 'fetch', '--quiet')
            return '工作中' in text
        result, report = read_only(self.repo, answer, env=self.env)
        self.assertTrue(result)
        self.assertEqual(report, {'ok': True, 'changes': [], 'unverified': []})
        # Stale stat info: a plain `git status` would rewrite the index here.
        later = time.time() + 5
        os.utime(self.repo / 'HANDOFF.md', (later, later))
        self.assertTrue(self.run_read(lambda: None)['ok'])

    def test_each_escalation_is_reported(self):
        marker = lambda: (self.repo / 'HANDOFF.md').write_text(handoff(ME), encoding='utf-8')
        self.assertEqual(self.run_read(marker)['changes'], ['worktree-changed'])
        # Already dirty: a second edit of the same file still counts.
        again = lambda: (self.repo / 'HANDOFF.md').write_text(handoff(ME) + 'x\n',
                                                               encoding='utf-8')
        self.assertEqual(self.run_read(again)['changes'], ['worktree-changed'])
        stage = lambda: self.git(self.repo, 'add', 'HANDOFF.md')
        self.assertEqual(self.run_read(stage)['changes'], ['index-changed'])
        commit = lambda: self.git(self.repo, 'commit', '--quiet', '-m', 'claim')
        # The committed file also leaves the changed-file list.
        self.assertEqual(self.run_read(commit)['changes'],
                         ['local-refs-changed', 'index-changed', 'worktree-changed'])
        push = lambda: self.git(self.repo, 'push', '--quiet')
        self.assertEqual(self.run_read(push)['changes'], ['remote-changed'])
        note = lambda: (self.repo / 'scratch.txt').write_text('x')
        self.assertEqual(self.run_read(note)['changes'], ['worktree-changed'])
        branch = lambda: self.git(self.repo, 'switch', '--quiet', '-c', 'side')
        self.assertEqual(self.run_read(branch)['changes'], ['local-refs-changed'])
        # Only a ref (HEAD untouched), then only HEAD (no ref changes).
        tag = lambda: self.git(self.repo, 'branch', 'kept')
        self.assertEqual(self.run_read(tag)['changes'], ['local-refs-changed'])
        detach = lambda: self.git(self.repo, 'switch', '--quiet', '--detach')
        self.assertEqual(self.run_read(detach)['changes'], ['local-refs-changed'])

    def test_unlistable_remote_is_unverified_not_clean(self):
        self.origin.rename(self.root / 'moved.git')
        report = self.run_read(lambda: None)
        self.assertEqual(report, {'ok': False, 'changes': [], 'unverified': ['remote']})
        self.git(self.repo, 'branch', '--quiet', '--unset-upstream')
        self.assertEqual(self.run_read(lambda: None)['unverified'], ['remote'])

    def test_failed_answer_still_reports_what_it_changed(self):
        def crash():
            (self.repo / 'HANDOFF.md').write_text(handoff(ME), encoding='utf-8')
            raise RuntimeError('synthetic')
        with self.assertRaises(RuntimeError) as caught:
            read_only(self.repo, crash, env=self.env)
        self.assertEqual(caught.exception.read_report['changes'], ['worktree-changed'])

    def test_not_a_repository_is_unverified(self):
        plain = self.root / 'plain'
        plain.mkdir()
        report = read_only(plain, lambda: None, env=self.env)[1]
        self.assertFalse(report['ok'])
        self.assertEqual(report['unverified'], ['local-refs', 'remote'])


if __name__ == '__main__':
    unittest.main()
