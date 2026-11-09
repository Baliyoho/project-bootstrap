"""F30: twenty real Git targets with mixed states; one bad target is never hidden."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import unittest.mock

from experiments.v2.batch import assess_many, summary
from experiments.v2.gitclaim import IDLE

ME = '`mac` ／ `Claude Code` ／ `㊣　26110922｜批次｜工作中｜交棒0次`'
OTHER = '`win` ／ `Codex CLI` ／ `㊣　26110901｜別人｜工作中｜交棒0次`'


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        (self.root / 'home').mkdir()
        self.env = {'PATH': os.environ.get('PATH', ''), 'HOME': str(self.root / 'home'),
                    'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                    'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@example.invalid',
                    'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@example.invalid'}

    def tearDown(self):
        self.directory.cleanup()

    def git(self, cwd, *args):
        subprocess.run(['git', *args], cwd=cwd, env=self.env, check=True, capture_output=True)

    def project(self, name, owner=IDLE, extra=None):
        origin = self.root / (name + '.git')
        work = self.root / name
        self.git(self.root, 'init', '--quiet', '--bare', '--initial-branch=main', str(origin))
        self.git(self.root, 'clone', '--quiet', str(origin), str(work))
        (work / 'HANDOFF.md').write_text(f'- **工作中**：{owner}\n', encoding='utf-8')
        self.git(work, 'add', 'HANDOFF.md')
        self.git(work, 'commit', '--quiet', '-m', 'init')
        self.git(work, 'push', '--quiet', '-u', 'origin', 'main')
        if extra == 'dirty':
            (work / 'stray.txt').write_text('x')
        elif extra == 'ahead':
            (work / 'a.txt').write_text('x')
            self.git(work, 'add', 'a.txt')
            self.git(work, 'commit', '--quiet', '-m', 'ahead')
        elif extra == 'offline':
            origin.rename(self.root / (name + '-moved.git'))
        return work

    def test_twenty_mixed_targets_are_all_listed_and_failures_counted(self):
        targets = [(self.project(f'ok{i}'), 'active') for i in range(14)]
        targets.append((self.project('busy', owner=OTHER), 'active'))
        targets.append((self.project('dirty', extra='dirty'), 'active'))
        targets.append((self.project('ahead', extra='ahead'), 'active'))
        targets.append((self.project('offline', extra='offline'), 'active'))
        targets.append((self.root / 'moved-away', 'active'))
        targets.append((self.project('old'), 'archived'))
        self.assertEqual(len(targets), 20)
        report = assess_many(targets, ME, env=self.env)
        self.assertEqual([row['target'] for row in report['results']],
                         [str(path) for path, _ in targets])
        self.assertFalse(report['ok'])
        self.assertEqual(report['counts'], {'eligible': 14, 'excluded': 1, 'failed': 5})
        codes = {Path(row['target']).name: row['code'] for row in report['results']
                 if row['outcome'] != 'eligible'}
        self.assertEqual(codes, {'busy': 'busy-other-machine', 'dirty': 'dirty-unknown',
                                 'ahead': 'ahead-only', 'offline': 'fetch-failed',
                                 'moved-away': 'missing-target', 'old': 'archived'})
        self.assertEqual(summary(report),
                         'NOT OK: 14 eligible, 5 failed, 1 excluded of 20 listed')

    def test_only_a_clean_batch_is_ok_and_edge_inputs_fail(self):
        good = self.project('good')
        report = assess_many([(good, 'active'), (self.project('arch'), 'archived')],
                             ME, env=self.env)
        self.assertTrue(report['ok'])
        self.assertTrue(summary(report).startswith('ALL ELIGIBLE: 1 eligible'))
        for targets, code in (
            ([(good, 'active'), (good / '.' , 'active')], 'duplicate-target'),
            ([(good, 'active'), (good, 'archived')], 'duplicate-target'),
            ([(good, 'paused')], 'invalid-target-state'),
        ):
            with self.subTest(code=code):
                report = assess_many(targets, ME, env=self.env)
                self.assertFalse(report['ok'])
                self.assertEqual(report['results'][-1]['code'], code)
        # Nothing processed is not success, even with no failures.
        self.assertFalse(assess_many([], ME, env=self.env)['ok'])
        self.assertFalse(assess_many([(good, 'archived')], ME, env=self.env)['ok'])

    def test_unexpected_error_in_one_target_does_not_stop_the_rest(self):
        good = self.project('good')
        plain = self.root / 'not-a-repo'
        plain.mkdir()
        report = assess_many([(plain, 'active'), (good, 'active')], ME, env=self.env)
        self.assertEqual([row['outcome'] for row in report['results']], ['failed', 'eligible'])
        self.assertFalse(report['ok'])
        from experiments.v2 import batch
        real = batch.assess_start

        def flaky(path, owner, env=None):
            if Path(path) == plain:
                raise RuntimeError('synthetic crash')
            return real(path, owner, env=env)

        with unittest.mock.patch.object(batch, 'assess_start', flaky):
            report = assess_many([(plain, 'active'), (good, 'active')], ME, env=self.env)
        self.assertEqual([(row['outcome'], row['code']) for row in report['results']],
                         [('failed', 'target-error'), ('eligible', 'ok')])


if __name__ == '__main__':
    unittest.main()
