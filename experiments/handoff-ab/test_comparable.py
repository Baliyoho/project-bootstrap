"""Offline paired-fixture and remote-confirmation checks; never calls a model."""
import pathlib
import json
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import comparable
from common import out


class ComparableTest(unittest.TestCase):
    def test_paired_snapshots_and_pure_tasks(self):
        with tempfile.TemporaryDirectory(prefix='pb-paired-test-') as folder:
            root = pathlib.Path(folder)
            pairs = comparable.prepare(root)
            self.assertEqual(len(pairs), 6)
            for kind in comparable.KINDS:
                hashes = set()
                for n in range(1, comparable.REPEATS + 1):
                    a = root / 'runs' / comparable.cell_name(kind, 'A', n)
                    b = root / 'runs' / comparable.cell_name(kind, 'B', n)
                    self.assertEqual(comparable.snapshot(a), comparable.snapshot(b))
                    self.assertEqual(out(a / 'work', 'rev-parse', 'HEAD'),
                                     out(b / 'work', 'rev-parse', 'HEAD'))
                    hashes.add(comparable.snapshot(a))
                    self.assertNotIn('codex-events.jsonl', [p.name for p in a.iterdir()])
                    meta = json.loads((a / 'meta.json').read_text(encoding='utf-8'))
                    self.assertEqual(comparable.starting_state_errors(a, meta), [])
                    if kind == 'takeover' and n == 1:
                        (a / 'work' / 'README.md').write_text('tampered', encoding='utf-8')
                        self.assertIn('work 有未提交變更', comparable.starting_state_errors(a, meta))
                        (a / 'work' / 'README.md').write_text(
                            comparable.git(a / 'work', 'show', 'HEAD:README.md').stdout,
                            encoding='utf-8')
                        with (a / 'work' / 'README.md').open('a', encoding='utf-8') as fh:
                            fh.write('\nprobe\n')
                        env = comparable.fixture_env(root)
                        comparable.git(a / 'work', 'add', '--', 'README.md', env=env)
                        comparable.git(a / 'work', 'commit', '-qm', 'probe', env=env)
                        comparable.git(a / 'work', 'push', '-q', 'origin', 'main', env=env)
                        self.assertIn('origin snapshot 已變', comparable.starting_state_errors(a, meta))
                self.assertEqual(len(hashes), 1)
            self.assertNotEqual(pairs[0]['snapshot_sha256'], pairs[1]['snapshot_sha256'])

    def test_nonzero_or_missing_exit_cannot_pass(self):
        pending = {'subject_verification': None, 'task_scope': None,
                   'remote_confirmation': None}
        approved = {key: True for key in pending}
        self.assertEqual(comparable.classify([], [], 0, pending), 'PENDING_REVIEW')
        self.assertEqual(comparable.classify([], [], 0, approved), 'PASS')
        self.assertEqual(comparable.classify([], [], 0, {**approved, 'task_scope': False}), 'FAIL')
        self.assertEqual(comparable.classify([], [], 1, approved), 'INVALID')
        self.assertEqual(comparable.classify([], [], 'timeout', approved), 'INVALID')
        self.assertEqual(comparable.classify([], [], None, approved), 'INVALID')
        for bad in ({'subject_verification': 'not_applicable'},
                    {'subject_verification': 1}, {'subject_verification': 0}):
            with self.assertRaises(ValueError):
                comparable.review_values(bad, 'takeover')
        self.assertEqual(comparable.review_values({}, 'handoff')['remote_confirmation'],
                         'not_applicable')


if __name__ == '__main__':
    unittest.main()
