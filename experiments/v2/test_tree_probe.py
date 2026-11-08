import os
import unittest
from unittest.mock import patch

from experiments.v2.tree_probe import LEADER, probe_tree, run_case


@unittest.skipUnless(os.name == 'posix', 'POSIX process-group candidate')
class TreeProbeTests(unittest.TestCase):
    def test_ordinary_descendant_exits_with_group(self):
        result = run_case(False)
        self.assertTrue(result['group_leader_exited'])
        self.assertTrue(result['descendant_exited'])

    def test_new_session_escapes_group(self):
        result = run_case(True)
        self.assertTrue(result['group_leader_exited'])
        self.assertFalse(result['descendant_exited'])

    def test_summary_keeps_candidate_unready(self):
        result = probe_tree()
        self.assertEqual(result['result'], '反例重現')
        self.assertFalse(result['escaped_session']['descendant_exited'])

    def test_escape_probe_fails_when_group_escape_is_removed(self):
        altered = LEADER.replace("start_new_session=sys.argv[3] == 'escape'",
                                 'start_new_session=False')
        self.assertNotEqual(altered, LEADER)
        with patch('experiments.v2.tree_probe.LEADER', altered):
            self.assertEqual(probe_tree()['result'], '不通過')
