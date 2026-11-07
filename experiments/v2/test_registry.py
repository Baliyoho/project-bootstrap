import copy
import importlib.util
import json
from pathlib import Path
import unittest

from experiments.v2.registry import requirement_ids, validate


class RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[2]
        cls.decision = (cls.root / 'project-bootstrap-requirements-decision.md').read_text(encoding='utf-8')
        cls.data = json.loads((cls.root / 'experiments/v2/status.json').read_text(encoding='utf-8'))

    def test_decision_and_registry_cover_same_stable_ids(self):
        self.assertEqual(len(requirement_ids(self.decision)), 51)
        self.assertEqual(validate(self.data, self.decision, self.root), [])

    def test_missing_duplicate_extra_and_unavailable_evidence_rejected(self):
        for mutation in ('missing', 'duplicate', 'extra', 'evidence', 'part', 'success'):
            data = copy.deepcopy(self.data)
            rows = data['requirements']
            if mutation == 'missing':
                rows.pop()
            elif mutation == 'duplicate':
                rows.append(copy.deepcopy(rows[0]))
            elif mutation == 'extra':
                rows[0]['id'] = 'F999'
            elif mutation == 'evidence':
                rows[0]['evidence'] = [{'path': 'does-not-exist.json', 'scope': 'fixture'}]
            elif mutation == 'part':
                next(row for row in rows if row['id'] == 'F11')['parts'].pop('b')
            else:
                rows[0]['result'] = '通過'
            with self.subTest(mutation=mutation):
                self.assertTrue(validate(data, self.decision, self.root))

    def test_legacy_entry_rejects_empty_skipped_or_optimistic_report(self):
        spec = importlib.util.spec_from_file_location('legacy_for_test', self.root / 'tools/verify_bootstrap.py')
        legacy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(legacy)
        report = {'harness_passed': True, 'strict_ready': False,
                  'tests': {'run': 1, 'failed': 0, 'errors': 0, 'skipped': 0},
                  'findings': [{'id': name, 'counterexample_observed': True, 'requirement_result': '不通過'}
                               for name in ('same-uid-journal-bypass', 'direct-git-object-bypass',
                                            'running-context-still-uses-old-premise')],
                  'isolation_probe': {'result': '未驗證'}, 'supervisor_probe': {'result': '通過'}}
        self.assertEqual(legacy.v2_report_problem(report), '')
        for change in ('empty', 'skip', 'ready', 'missing', 'false-pass', 'no-reproduction', 'supervisor'):
            mutant = copy.deepcopy(report)
            if change == 'empty':
                mutant['tests']['run'] = 0
            elif change == 'skip':
                mutant['tests']['skipped'] = 1
            elif change == 'ready':
                mutant['strict_ready'] = True
            elif change == 'missing':
                mutant['findings'].pop()
            elif change == 'false-pass':
                mutant['findings'][0]['requirement_result'] = '通過'
            elif change == 'supervisor':
                mutant.pop('supervisor_probe')
            else:
                mutant['findings'][0]['counterexample_observed'] = False
            with self.subTest(change=change):
                self.assertTrue(legacy.v2_report_problem(mutant))


if __name__ == '__main__':
    unittest.main()
