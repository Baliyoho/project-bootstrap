import os
import sys
import unittest
from unittest.mock import patch

from experiments.v2.tree_probe import LEADER, _es_assessment, probe_descendant_api, probe_tree, run_case


class DescendantApiTests(unittest.TestCase):
    def test_entitlement_denial_cannot_be_called_a_boundary(self):
        self.assertEqual(_es_assessment(3)['result'], '無權限')
        self.assertNotEqual(_es_assessment(3)['result'], '通過')

    def test_client_creation_alone_is_not_tree_retirement(self):
        self.assertEqual(_es_assessment(0)['result'], '可建立但未驗收')
        self.assertNotEqual(_es_assessment(0)['result'], '通過')

    def test_compiler_failure_is_unverified_and_not_ready(self):
        with patch('experiments.v2.tree_probe.sys.platform', 'darwin'), \
                patch('experiments.v2.tree_probe.platform.mac_ver', return_value=('27.2', '', '')), \
                patch('experiments.v2.tree_probe.subprocess.run') as runner:
            runner.return_value.returncode = 1
            result = probe_descendant_api()
        self.assertEqual(result['result'], '未驗證')
        self.assertEqual(result['strict_boundary'], '未通過')

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS-only ES admission')
    def test_unsigned_local_helper_reports_no_strict_boundary(self):
        self.assertNotEqual(probe_descendant_api().get('strict_boundary'), '通過')


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
