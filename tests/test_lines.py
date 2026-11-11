"""F12: real Git worktrees, clones and the ways two lines end up sharing one tree."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from project_bootstrap.lines import assess_lines


class LineTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='bootstrap-v2-lines-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(os.path.realpath(self.directory.name))
        (self.root / 'home').mkdir()
        self.env = {'PATH': os.environ.get('PATH', ''), 'HOME': str(self.root / 'home'),
                    'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                    'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@example.invalid',
                    'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@example.invalid'}
        self.main = self.root / 'main'
        self.git(self.root, 'init', '--quiet', '--initial-branch=main', str(self.main))
        (self.main / 'sub').mkdir()
        (self.main / 'sub' / 'a.txt').write_text('a')
        self.git(self.main, 'add', '-A')
        self.git(self.main, 'commit', '--quiet', '-m', 'init')

    def git(self, cwd, *args):
        result = subprocess.run(['git', *args], cwd=cwd, env=self.env, capture_output=True)
        if result.returncode:
            raise AssertionError(result.stderr.decode())

    def worktree(self, name, branch):
        path = self.root / name
        self.git(self.main, 'worktree', 'add', '--quiet', '-b', branch, str(path))
        return path

    def codes(self, report):
        return {row['line']: sorted(row['codes']) for row in report['lines']}

    def test_separate_worktrees_and_clones_are_independent_lines(self):
        a = self.worktree('wt-a', 'line-a')
        clone = self.root / 'clone'
        self.git(self.root, 'clone', '--quiet', str(self.main), str(clone))
        self.git(clone, 'switch', '--quiet', '-c', 'line-c')
        report = assess_lines([('main', self.main, 'main'), ('a', a, 'line-a'),
                               ('c', clone, 'line-c')], env=self.env)
        self.assertTrue(report['ok'], self.codes(report))
        # Each really has its own index: staging in one leaves the other untouched.
        (a / 'new.txt').write_text('x')
        self.git(a, 'add', 'new.txt')
        status = subprocess.run(['git', 'status', '--porcelain'], cwd=self.main, env=self.env,
                                capture_output=True).stdout
        self.assertEqual(status, b'')

    def test_different_branch_in_the_same_tree_is_still_shared(self):
        # The second line "works on" another branch by switching inside main's tree.
        report = assess_lines([('main', self.main, 'main'), ('b', self.main, 'line-b')],
                              env=self.env)
        self.assertFalse(report['ok'])
        self.assertEqual(self.codes(report),
                         {'main': ['shared-index', 'shared-worktree'],
                          'b': ['branch-mismatch', 'shared-index', 'shared-worktree']})

    def test_subdirectory_and_symlink_resolve_to_the_same_tree(self):
        link = self.root / 'link'
        link.symlink_to(self.main, target_is_directory=True)
        for other in (self.main / 'sub', link):
            with self.subTest(other=other.name):
                report = assess_lines([('main', self.main, 'main'), ('x', other, 'main')],
                                      env=self.env)
                self.assertEqual(self.codes(report)['x'],
                                 ['shared-branch', 'shared-index', 'shared-worktree'])

    def test_copied_git_file_shares_the_index_under_another_directory(self):
        a = self.worktree('wt-a', 'line-a')
        copy = self.root / 'copy'
        copy.mkdir()
        (copy / '.git').write_bytes((a / '.git').read_bytes())
        report = assess_lines([('a', a, 'line-a'), ('copy', copy, 'line-a')], env=self.env)
        self.assertEqual(self.codes(report)['copy'], ['shared-branch', 'shared-index'])
        self.assertFalse(report['ok'])

    def test_bad_inputs_are_reported_not_dropped(self):
        a = self.worktree('wt-a', 'line-a')
        self.git(a, 'switch', '--quiet', '--detach')
        plain = self.root / 'plain'
        plain.mkdir()
        report = assess_lines([('a', a, 'line-a'), ('gone', self.root / 'missing', 'x'),
                               ('plain', plain, 'y'), ('a', self.main, 'main'),
                               ('', self.root / 'missing2', 'z')], env=self.env)
        self.assertEqual([row['line'] for row in report['lines']], ['a', 'gone', 'plain', 'a', ''])
        self.assertEqual([row['codes'] for row in report['lines']],
                         [['branch-mismatch'], ['not-a-checkout'], ['not-a-checkout'],
                          ['duplicate-line'], ['duplicate-line', 'not-a-checkout']])
        self.assertFalse(assess_lines([], env=self.env)['ok'])


if __name__ == '__main__':
    unittest.main()
