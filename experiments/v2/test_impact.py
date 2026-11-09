"""F31: one changed wiring file lists its requirements, re-check tests and projects."""

import json
from pathlib import Path
import unittest

from experiments.v2.impact import graph_from_status, impact

STATUS = {'requirements': [
    {'id': 'F9', 'evidence': [{'path': 'v2/gitclaim.py'}, {'path': 'v2/test_gitclaim.py'}]},
    {'id': 'F18', 'evidence': [{'path': 'v2/release.py'}, {'path': 'v2/test_release.py'},
                               {'path': 'hooks/git-freshness.sh'}]},
    {'id': 'F30', 'evidence': [{'path': 'v2/batch.py'}, {'path': 'v2/test_batch.py'},
                               {'path': 'v2/gitclaim.py'}, {'path': ''}, {'scope': 'x'}]},
    # 'contest_' contains 'test_' but is not a test file.
    {'id': 'F24', 'evidence': [{'path': 'v2/contest_rules.py'}]},
    {'id': 'F11', 'evidence': [], 'parts': {'a': {'evidence': [{'path': 'v2/lines.py'}]},
                                            'b': {'evidence': []}}},
    {'id': 'F1', 'evidence': []},
]}
PROJECTS = {'alpha': {'hooks/git-freshness.sh', '.claude/settings.json'},
            'beta': {'hooks/git-freshness.sh'},
            'gamma': {'.claude/settings.json'}}


class ImpactTests(unittest.TestCase):
    def setUp(self):
        self.graph = graph_from_status(STATUS)

    def test_graph_comes_from_status_evidence_including_parts(self):
        self.assertEqual(self.graph['v2/gitclaim.py'], {'F9', 'F30'})
        self.assertEqual(self.graph['v2/lines.py'], {'F11'})
        self.assertNotIn('F1', {i for ids in self.graph.values() for i in ids})
        self.assertNotIn('', self.graph)
        self.assertNotIn(None, self.graph)

    def test_changed_wiring_lists_requirements_tests_and_projects(self):
        result = impact(['hooks/git-freshness.sh'], self.graph, PROJECTS)
        self.assertEqual(result, {'scope': 'targeted', 'unclassified': [],
                                  'requirements': ['F18'], 'tests': ['v2/test_release.py'],
                                  'projects': ['alpha', 'beta']})
        shared = impact(['v2/gitclaim.py'], self.graph, PROJECTS)
        self.assertEqual((shared['requirements'], shared['tests'], shared['projects']),
                         (['F30', 'F9'], ['v2/test_batch.py', 'v2/test_gitclaim.py'], []))
        # A project-only component is classified: no requirement yet, but known projects.
        settings = impact(['.claude/settings.json'], self.graph, PROJECTS)
        self.assertEqual((settings['scope'], settings['projects'], settings['tests']),
                         ('targeted', ['alpha', 'gamma'], []))
        # A changed test is reached through its own requirement.
        self.assertIn('v2/test_gitclaim.py',
                      impact(['v2/test_gitclaim.py'], self.graph, PROJECTS)['tests'])
        self.assertEqual(impact(['v2/contest_rules.py'], self.graph, PROJECTS)['tests'], [])

    def test_unclassified_change_widens_to_everything(self):
        result = impact(['v2/gitclaim.py', 'tools/new_tool.py'], self.graph, PROJECTS)
        self.assertEqual(result['scope'], 'full')
        self.assertEqual(result['unclassified'], ['tools/new_tool.py'])
        self.assertEqual(result['projects'], ['alpha', 'beta', 'gamma'])
        self.assertEqual(result['tests'], ['v2/test_batch.py', 'v2/test_gitclaim.py',
                                           'v2/test_release.py'])
        self.assertEqual(result['requirements'], ['F11', 'F18', 'F24', 'F30', 'F9'])

    def test_real_index_maps_each_v2_test_to_some_requirement(self):
        root = Path(__file__).resolve().parent
        graph = graph_from_status(json.loads((root / 'status.json').read_text(encoding='utf-8')))
        mapped = {path for path in graph if path.startswith('experiments/v2/test_')}
        self.assertIn('experiments/v2/test_impact.py', mapped)
        result = impact(['experiments/v2/gitclaim.py'], graph, {})
        self.assertEqual(result['scope'], 'targeted')
        self.assertIn('experiments/v2/test_gitclaim.py', result['tests'])


if __name__ == '__main__':
    unittest.main()
