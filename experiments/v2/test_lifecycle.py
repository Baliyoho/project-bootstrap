import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from experiments.v2.broker import Broker
from experiments.v2.broker_fixture import launch_agent
from experiments.v2.contracts import Denied, Lab
from experiments.v2.launcher import LaunchAuthority
from experiments.v2.lifecycle import LaunchPlan, ProcessLauncher, TicketVault


WORKER = "import sys; print('bootstrap-v2-ready', flush=True); sys.stdin.read()"


@unittest.skipUnless(os.name == 'posix', 'POSIX ticket custody; Windows adapter is unverified')
class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='bootstrap-v2-lifecycle-')
        self.root = Path(self.temp.name).resolve()
        self.private = self.root / 'tickets'
        self.private.mkdir(mode=0o700)
        self.lab = Lab(self.root / 'lab.sqlite', authority_clock=lambda: self.now)
        self.now = 1000
        self.broker = Broker(self.lab)
        self.authority = LaunchAuthority(self.broker)
        self.vault = TicketVault(self.private)
        self.ticket = self.authority.issue(('note',), 'synthetic-parent', 1100)
        self.handle = self.vault.save(self.ticket)
        self.launcher = ProcessLauncher(self.authority, self.vault, timeout=0.5)
        self.plan = LaunchPlan((sys.executable, '-B', '-u', '-c', WORKER), str(self.root))

    def tearDown(self):
        self.launcher.close()
        self.vault.close()
        self.lab.close()
        self.temp.cleanup()

    def actor(self):
        return self.lab.db.execute('SELECT actor FROM launch_permits').fetchone()[0]

    def state(self):
        return self.lab.db.execute('SELECT state FROM managed_launches').fetchone()[0]

    def test_replacement_waits_for_exit_and_revokes_previous_pipe(self):
        first = self.launcher.start(self.handle, self.plan)
        self.assertIsNone(first.process.poll())
        connect = self.authority.connect
        def only_after_exit(ticket):
            self.assertIsNotNone(first.process.poll())
            self.assertTrue(first.channel.closed)
            return connect(ticket)
        with patch.object(self.authority, 'connect', only_after_exit):
            second = self.launcher.start(self.handle, self.plan)
        self.assertNotEqual(first.process.pid, second.process.pid)
        self.assertIsNone(second.process.poll())
        request = json.dumps(dict(id=1, method='write', resource='note', base=None, text='ok', epoch=0)).encode()
        self.assertEqual(json.loads(self.broker.dispatch(first.channel, request))['code'], 'closed-channel')
        self.assertEqual(json.loads(self.broker.dispatch(second.channel, request))['code'], 'ok')

    def test_unresolved_parent_restart_never_adopts_pid_or_spawns(self):
        first = self.launcher.start(self.handle, self.plan)
        restarted = ProcessLauncher(self.authority, self.vault, timeout=0.5)
        with patch('experiments.v2.lifecycle.subprocess.Popen') as spawn:
            with self.assertRaisesRegex(Denied, 'unresolved-previous-process'):
                restarted.start(self.handle, self.plan)
            spawn.assert_not_called()
        self.assertIsNone(first.process.poll())
        self.launcher.close()
        self.launcher = restarted
        second = self.launcher.start(self.handle, self.plan)
        self.assertIsNone(second.process.poll())

    def test_plan_change_stops_old_child_and_does_not_launch_new_command(self):
        old = self.launcher.start(self.handle, self.plan)
        changed = LaunchPlan(self.plan.argv + ('different',), self.plan.cwd)
        with patch('experiments.v2.lifecycle.subprocess.Popen') as spawn:
            with self.assertRaisesRegex(Denied, 'launch-plan-changed'):
                self.launcher.start(self.handle, changed)
            spawn.assert_not_called()
        self.assertIsNotNone(old.process.poll())
        self.assertTrue(old.channel.closed)
        self.assertEqual(self.state(), 'stopped')

    def test_expired_or_revoked_permit_stops_owned_child(self):
        old = self.launcher.start(self.handle, self.plan)
        self.now = 1100
        with self.assertRaises(Denied):
            self.launcher.check()
        self.assertIsNotNone(old.process.poll())
        self.assertTrue(old.channel.closed)
        with self.assertRaises(Denied):
            self.launcher.start(self.handle, self.plan)
        self.assertEqual(self.state(), 'stopped')

    def test_revocation_during_startup_never_hands_out_a_channel(self):
        connect = self.authority.connect
        def revoked(ticket):
            self.authority.revoke(ticket)
            return connect(ticket)
        with patch.object(self.authority, 'connect', revoked), self.assertRaises(Denied):
            self.launcher.start(self.handle, self.plan)
        self.assertEqual(self.state(), 'stopped')
        self.assertFalse(self.launcher.children)
        self.assertFalse(self.broker.channels)

    def test_idle_transport_checks_expiry_and_stops_the_child(self):
        child = self.launcher.start(self.handle, self.plan)
        self.now = 1100
        def check():
            with self.lab.transaction():
                child.channel.authorize(child.channel)
        result = launch_agent(self.broker, child.channel, (), self.root, process=child.process, check=check)
        self.assertFalse(result['completed'])
        self.assertEqual(result['reason'], 'agent-authority-or-lifecycle-ended')
        self.assertIsNotNone(child.process.poll())
        self.assertTrue(child.channel.closed)
        self.launcher.close()
        self.assertEqual(self.state(), 'stopped')

    def test_bad_or_missing_handshake_cleans_up_and_issues_no_pipe(self):
        for code in ("print('wrong', flush=True)", 'import time; time.sleep(10)'):
            # Separate principal because a plan cannot silently change on retry.
            ticket = self.authority.issue(('note',), 'synthetic-parent', 1100)
            handle = self.vault.save(ticket)
            plan = LaunchPlan((sys.executable, '-B', '-u', '-c', code), str(self.root))
            with self.subTest(code=code), self.assertRaises(Denied):
                self.launcher.start(handle, plan)
            self.assertFalse(self.launcher.children)
            self.assertFalse(self.broker.channels)

    def test_ignoring_terminate_requires_kill_and_wait_before_replacement(self):
        code = "import signal, sys; signal.signal(signal.SIGTERM, signal.SIG_IGN); " + WORKER
        plan = LaunchPlan((sys.executable, '-B', '-u', '-c', code), str(self.root))
        first = self.launcher.start(self.handle, plan)
        self.launcher.start(self.handle, plan)
        self.assertEqual(first.process.returncode, -9)
        self.assertTrue(first.channel.closed)

    def test_stop_failure_forbids_rotation_and_replacement(self):
        first = self.launcher.start(self.handle, self.plan)
        with patch.object(self.launcher, 'stop', side_effect=Denied('synthetic-stop-failure')):
            with patch.object(self.authority, 'connect') as connect:
                with self.assertRaises(Denied):
                    self.launcher.start(self.handle, self.plan)
                connect.assert_not_called()
        self.assertIsNone(first.process.poll())
        self.assertEqual(self.state(), 'running')

    def test_journal_failure_still_stops_child_but_blocks_replacement(self):
        child = self.launcher.start(self.handle, self.plan)
        with patch.object(self.launcher, 'state', side_effect=OSError('synthetic journal failure')):
            with self.assertRaises(OSError):
                self.launcher.start(self.handle, self.plan)
        self.assertIsNotNone(child.process.poll())
        self.assertTrue(child.channel.closed)
        self.assertEqual(self.state(), 'running')
        self.assertIn(self.actor(), self.launcher.children)

    def test_ticket_survives_vault_reopen_but_not_insecure_mode_or_alias(self):
        self.vault.close()
        self.vault = TicketVault(self.private)
        self.assertEqual(self.vault.load(self.handle), self.ticket)
        file = self.private / self.handle
        file.chmod(0o644)
        with self.assertRaises(Denied):
            self.vault.load(self.handle)
        file.chmod(0o600)
        alias = self.private / ('a' * 64)
        os.link(file, alias)
        with self.assertRaises(Denied):
            self.vault.load(self.handle)
        alias.unlink()
        alias.symlink_to(file)
        with self.assertRaises(OSError):
            self.vault.load('a' * 64)
        self.private.chmod(0o755)
        with self.assertRaises(Denied):
            self.vault.load(self.handle)
        self.private.chmod(0o700)

    def test_missing_malformed_and_fifo_ticket_never_launch(self):
        for handle in ('../escape', 'a' * 64):
            with self.subTest(handle=handle), self.assertRaises((Denied, OSError)):
                self.launcher.start(handle, self.plan)
        fifo = self.private / ('b' * 64)
        os.mkfifo(fifo, 0o600)
        with self.assertRaises(Denied):
            self.vault.load('b' * 64)
        self.assertFalse(self.launcher.children)

    def test_removing_stop_guard_reproduces_two_running_children(self):
        # Negative control for the former capability-only replacement boundary.
        first = self.launcher.start(self.handle, self.plan)
        try:
            with patch.object(self.launcher, 'stop', return_value=None):
                second = self.launcher.start(self.handle, self.plan)
            self.assertIsNone(first.process.poll())
            self.assertIsNone(second.process.poll())
        finally:
            first.process.kill()
            first.process.wait(timeout=2)
            first.process.stdin.close()
            first.process.stdout.close()


if __name__ == '__main__':
    unittest.main()
