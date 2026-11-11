import platform
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from project_bootstrap import broker_fixture
from project_bootstrap.contracts import Denied

SUPPORTED = platform.system() == 'Darwin' and Path('/usr/bin/sandbox-exec').is_file()


class BrokerFixtureTests(TestCase):
    def test_launcher_failure_is_reported_as_failure_not_blocking_success(self):
        if not SUPPORTED:
            self.assertEqual(broker_fixture.probe_broker()['result'], '未驗證')
            return
        with patch.object(broker_fixture.ProcessLauncher, 'start', side_effect=Denied('child-not-ready')):
            result = broker_fixture.probe_broker()
        self.assertEqual(result['result'], '不通過')
        self.assertEqual(result['reason'], 'launcher-start-failed')
        self.assertFalse(result['checks']['confined_agent_completed'])

    def test_real_confined_agent_has_no_admin_identity_or_direct_write_access(self):
        result = broker_fixture.probe_broker()
        if not SUPPORTED:
            self.assertEqual(result['result'], '未驗證')
            return
        self.assertEqual(result['result'], '通過')
        self.assertTrue(all(result['checks'].values()))

    def test_relaxing_private_read_guard_breaks_probe(self):
        if not SUPPORTED:
            self.assertEqual(broker_fixture.probe_broker()['result'], '未驗證')
            return
        with patch.object(broker_fixture, 'PROFILE', broker_fixture.PROFILE + '\n(allow file-read*)'):
            result = broker_fixture.probe_broker()
        self.assertEqual(result['result'], '不通過')
        self.assertFalse(result['checks']['confined_agent_completed'])
        self.assertFalse(result['checks']['pipe_principal_recorded'])

    def test_child_start_failure_is_not_reported_as_successful_blocking(self):
        if not SUPPORTED:
            self.assertEqual(broker_fixture.probe_broker()['result'], '未驗證')
            return
        with patch.object(broker_fixture, 'AGENT', 'raise SystemExit(7)'):
            result = broker_fixture.probe_broker()
        self.assertEqual(result['result'], '不通過')
        self.assertEqual(result['transport']['exit_code'], 7)
        self.assertEqual(result['transport']['requests'], 0)

    def test_relaxing_fork_or_signal_guard_breaks_probe(self):
        if not SUPPORTED:
            self.assertEqual(broker_fixture.probe_broker()['result'], '未驗證')
            return
        for rule in ('(deny process-fork)', '(deny signal)'):
            with self.subTest(rule=rule):
                with patch.object(broker_fixture, 'PROFILE', broker_fixture.PROFILE.replace(rule, '')):
                    result = broker_fixture.probe_broker()
                self.assertEqual(result['result'], '不通過')
                self.assertFalse(result['checks']['confined_agent_completed'])
                self.assertFalse(result['checks']['pipe_principal_recorded'])

    def test_oversized_pipe_message_closes_channel_without_mutation(self):
        if not SUPPORTED:
            self.assertEqual(broker_fixture.probe_broker()['result'], '未驗證')
            return
        with patch.object(broker_fixture, 'AGENT', "print('x' * 10000, flush=True)"):
            result = broker_fixture.probe_broker()
        self.assertEqual(result['result'], '不通過')
        self.assertEqual(result['transport']['reason'], 'transport-limit')
        self.assertTrue(result['checks']['closed_pipe_revoked'])
        self.assertFalse(result['checks']['pipe_principal_recorded'])
