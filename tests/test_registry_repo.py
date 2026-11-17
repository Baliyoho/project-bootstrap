"""registry and the legacy v2 entry on this repo's real files.

Kept apart from test_registry so mutation runs, which copy only src/ and tests/,
never depend on the repo's documents (2026-11-17, v3 Q39). The decision book read
here is v3: v2 is a frozen archive that no program reads.
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from project_bootstrap.registry import requirement_ids, validate

ROOT = Path(__file__).resolve().parents[1]
BOOK = 'project-bootstrap-requirements-decision-v3.md'


class RepoRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decision = (ROOT / BOOK).read_text(encoding='utf-8')
        cls.data = json.loads((ROOT / 'experiments/v2/status.json').read_text(encoding='utf-8'))

    def test_decision_and_registry_cover_same_stable_ids(self):
        self.assertEqual(len(requirement_ids(self.decision)), 51)
        self.assertEqual(validate(self.data, self.decision, ROOT), [])

    def test_real_registry_still_rejects_a_missing_row(self):
        data = copy.deepcopy(self.data)
        data['requirements'].pop()
        self.assertTrue(validate(data, self.decision, ROOT))

    def test_legacy_entry_rejects_empty_skipped_or_optimistic_report(self):
        spec = importlib.util.spec_from_file_location('legacy_for_test', ROOT / 'tools/verify_bootstrap.py')
        legacy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(legacy)
        report = {'harness_passed': True, 'strict_ready': False,
                  'tests': {'run': 1, 'failed': 0, 'errors': 0, 'skipped': 0, 'needs_uv': []},
                  'archived': 'archive/v2-barrier/（v3 Q33）'}
        self.assertEqual(legacy.v2_report_problem(report), '')
        for change in ('empty', 'skip', 'ready', 'archived-missing', 'archived-elsewhere',
                       'needs-uv-missing'):
            mutant = copy.deepcopy(report)
            if change == 'empty':
                mutant['tests']['run'] = 0
            elif change == 'skip':
                mutant['tests']['skipped'] = 1
            elif change == 'ready':
                mutant['strict_ready'] = True
            elif change == 'archived-missing':
                mutant.pop('archived')
            elif change == 'archived-elsewhere':
                mutant['archived'] = 'somewhere/else'
            else:
                mutant['tests'].pop('needs_uv')
            with self.subTest(change=change):
                self.assertTrue(legacy.v2_report_problem(mutant))


if __name__ == '__main__':
    unittest.main()
