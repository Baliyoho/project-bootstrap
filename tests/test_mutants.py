"""F29: the mutation runner tells killed, survived and stale apart and never edits the tree."""

from pathlib import Path
import tempfile
import unittest

from project_bootstrap.mutants import run

GUARD = '''def allowed(owner):
    if not owner:
        return False
    return owner != 'other'
'''
TEST = '''import unittest
from demo.guard import allowed


class T(unittest.TestCase):
    def test_other_is_refused(self):
        self.assertFalse(allowed('other'))
        self.assertTrue(allowed('me'))
'''


class MutantRunnerTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='bootstrap-v2-mutant-test-')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        package = self.root / 'src' / 'demo'
        package.mkdir(parents=True)
        (package / '__init__.py').write_text('')
        (package / 'guard.py').write_text(GUARD)
        (self.root / 'tests').mkdir()
        (self.root / 'tests' / '__init__.py').write_text('')
        (self.root / 'tests' / 'test_guard.py').write_text(TEST)

    def spec(self, *mutants):
        return {'groups': [{'tests': ['tests.test_guard'], 'mutants': [
            {'file': 'src/demo/guard.py', 'old': old, 'new': new} for old, new in mutants]}]}

    def test_outcomes_are_told_apart_and_source_is_untouched(self):
        report = run(self.spec(
            ("    return owner != 'other'\n", "    return True\n"),   # tested guard
            ("    if not owner:\n        return False\n", ""),      # untested guard
            ("    if owner is None:\n", ""),                          # text not present
            ("    return", "    return"),                             # occurs twice
        ), source_root=self.root)
        self.assertEqual([row['outcome'] for row in report['results']],
                         ['killed', 'survived', 'stale', 'stale'])
        self.assertFalse(report['ok'])
        self.assertEqual(report['counts'], {'killed': 1, 'survived': 1, 'stale': 2})
        self.assertEqual((self.root / 'src/demo/guard.py').read_text(), GUARD)

    def test_only_all_killed_is_ok_and_missing_file_is_stale(self):
        good = self.spec(("    return owner != 'other'\n", "    return True\n"))
        self.assertTrue(run(good, source_root=self.root)['ok'])
        self.assertFalse(run({'groups': []}, source_root=self.root)['ok'])
        missing = {'groups': [{'tests': ['tests.test_guard'], 'mutants': [
            {'file': 'src/demo/gone.py', 'old': 'x', 'new': 'y'}]}]}
        self.assertEqual(run(missing, source_root=self.root)['results'][0]['outcome'], 'stale')
        # Filtering by test module skips other groups entirely.
        self.assertEqual(run(good, source_root=self.root, only=['tests.other'])['results'], [])


if __name__ == '__main__':
    unittest.main()
