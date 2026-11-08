import json
import os
from pathlib import Path
import sqlite3
import sys
import subprocess
import select
import signal
import tempfile
import time
import unittest
from unittest.mock import patch

from experiments.v2.broker import Broker
from experiments.v2.broker_fixture import launch_agent
from experiments.v2.contracts import Denied, Lab
from experiments.v2.launcher import LaunchAuthority, RequestJournal
from experiments.v2 import lifecycle
from experiments.v2.lifecycle import LaunchPlan, ProcessLauncher, TicketVault


WORKER = "import sys; print('bootstrap-v2-ready', flush=True); sys.stdin.read()"

# Fixed evidence worker: its exclusive lock is released only on process exit.
# A stop file lets tests clean up negative controls without signaling saved PIDs.
LOCK_WORKER = '''import fcntl, pathlib, sys, time
root = pathlib.Path(sys.argv[1])
lock = (root / 'held').open('w')
fcntl.flock(lock, fcntl.LOCK_EX)
print('bootstrap-v2-ready', flush=True)
while not (root / 'finish').exists():
    time.sleep(0.02)
'''

PARENT = '''import pathlib, sys, time
from experiments.v2.contracts import Lab
from experiments.v2.broker import Broker
from experiments.v2.launcher import LaunchAuthority
from experiments.v2.lifecycle import TicketVault, ProcessLauncher, LaunchPlan
root = pathlib.Path(sys.argv[1])
lab = Lab(root / 'crash.sqlite')
authority = LaunchAuthority(Broker(lab))
vault = TicketVault(root / 'tickets')
ttl = 2 if sys.argv[3] == 'freeze' else 60
handle = vault.save(authority.issue(('note',), 'synthetic-parent', time.time() + ttl))
launcher = ProcessLauncher(authority, vault, timeout=0.2)
plan = LaunchPlan((sys.executable, '-B', '-u', '-c', sys.argv[2], str(root)), str(root))
if sys.argv[3] == 'unguarded':
    import subprocess
    child = subprocess.Popen(plan.argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    assert child.stdout.readline() == launcher.READY
else:
    if sys.argv[3] == 'starting':
        print(handle, flush=True)
    launcher.start(handle, plan)
if sys.argv[3] != 'starting':
    print(handle, flush=True)
sys.stdin.read()
'''


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

    def lock_held(self):
        import fcntl
        with (self.root / 'held').open('a') as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return True
            return False

    def await_unlock(self):
        until = time.monotonic() + 5
        while self.lock_held() and time.monotonic() < until:
            time.sleep(0.02)
        self.assertFalse(self.lock_held(), 'fixed worker has not exited')

    def test_real_parent_kill_reaps_worker_and_allows_explicit_reconciliation(self):
        self.run_parent_kill('guarded')

    def test_without_guardian_parent_kill_leaves_live_worker(self):
        self.run_parent_kill('unguarded')

    def test_parent_kill_during_handshake_reaps_worker(self):
        self.run_parent_kill('starting')

    def test_guardian_reaps_at_deadline_even_while_parent_is_frozen(self):
        with subprocess.Popen((sys.executable, '-B', '-u', '-c', PARENT, str(self.root), LOCK_WORKER, 'freeze'),
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE) as parent:
            try:
                self.assertTrue(select.select([parent.stdout], [], [], 5)[0])
                self.assertTrue(TicketVault.valid(parent.stdout.readline().decode().strip()))
                self.assertTrue(self.lock_held())
                parent.send_signal(signal.SIGSTOP)
                self.await_unlock()
                self.assertIsNone(parent.poll(), 'worker must exit before the parent dies or closes its pipe')
            finally:
                parent.kill()
                parent.wait(timeout=5)
                (self.root / 'finish').touch()
                self.await_unlock()

    def run_parent_kill(self, mode):
        worker = LOCK_WORKER
        if mode == 'starting':
            worker = worker.replace("print('bootstrap-v2-ready', flush=True)", 'pass')
        parent = subprocess.Popen((sys.executable, '-B', '-u', '-c', PARENT,
                                  str(self.root), worker, mode),
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        try:
            self.assertTrue(select.select([parent.stdout], [], [], 5)[0])
            handle = parent.stdout.readline().decode().strip()
            self.assertEqual(len(handle), 64)
            until = time.monotonic() + 5
            while not self.lock_held() and time.monotonic() < until:
                time.sleep(0.01)
            self.assertTrue(self.lock_held())
            parent.kill()
            parent.wait(timeout=5)
            if mode == 'unguarded':
                time.sleep(0.3)
                self.assertTrue(self.lock_held(), 'negative control must leave an orphan')
            else:
                self.await_unlock()
                lab = Lab(self.root / 'crash.sqlite')
                try:
                    restarted = ProcessLauncher(LaunchAuthority(Broker(lab)), self.vault)
                    plan = LaunchPlan((sys.executable, '-B', '-u', '-c', worker, str(self.root)), str(self.root))
                    # Startup still refuses unknown state. Explicit recovery
                    # uses the bound guardian record rather than a PID or lock.
                    with patch('os.kill') as kill, patch('subprocess.Popen') as spawn:
                        with self.assertRaisesRegex(Denied, 'unresolved-previous-process'):
                            restarted.start(handle, plan)
                        until = time.monotonic() + 5
                        while True:
                            try:
                                restarted.reconcile(handle, plan)
                                break
                            except Denied as error:
                                if str(error) != 'worker-reap-unconfirmed' or time.monotonic() >= until:
                                    raise
                                time.sleep(0.01)
                        self.assertEqual(lab.db.execute('SELECT state FROM managed_launches').fetchone()[0],
                                         'stopped')
                        kill.assert_not_called()
                        spawn.assert_not_called()
                finally:
                    lab.close()
        finally:
            if parent.poll() is None:
                parent.kill()
            parent.wait(timeout=5)
            (self.root / 'finish').touch()
            self.await_unlock()
            parent.stdin.close()
            parent.stdout.close()

    def test_guardian_kill_is_not_proof_of_worker_exit(self):
        plan = LaunchPlan((sys.executable, '-B', '-u', '-c', LOCK_WORKER, str(self.root)), str(self.root))
        child = self.launcher.start(self.handle, plan)
        try:
            self.assertTrue(self.lock_held())
            child.process.kill()
            child.process.wait(timeout=5)
            with self.assertRaisesRegex(Denied, 'worker-reap-unconfirmed'):
                self.launcher.stop(self.actor())
            self.assertTrue(self.lock_held())
            self.assertEqual(self.state(), 'stopping')
            with patch('subprocess.Popen') as spawn:
                with self.assertRaises(Denied):
                    self.launcher.start(self.handle, plan)
                spawn.assert_not_called()
            restarted = ProcessLauncher(self.authority, self.vault)
            with self.assertRaisesRegex(Denied, 'worker-reap-unconfirmed'):
                restarted.reconcile(self.handle, plan)
        finally:
            (self.root / 'finish').touch()
            self.await_unlock()
            # Explicit test fixture disposal, never an application recovery API.
            self.launcher.children.clear()
            child.process.stdin.close()
            child.process.stdout.close()

    def test_worker_does_not_inherit_lifetime_or_reap_report_descriptors(self):
        code = '''import os, sys
for fd in range(3, 256):
    try:
        os.fstat(fd)
    except OSError:
        continue
    raise AssertionError('unexpected inherited descriptor')
print('bootstrap-v2-ready', flush=True)
sys.stdin.read()
'''
        plan = LaunchPlan((sys.executable, '-B', '-u', '-c', code), str(self.root))
        self.launcher.start(self.handle, plan)
        self.launcher.stop(self.actor())
        self.assertEqual(self.state(), 'stopped')

    def test_spawn_failure_closes_control_descriptors_and_blocks_retry(self):
        pipe = os.pipe
        opened = []

        def track_pipe():
            pair = pipe()
            opened.extend(pair)
            return pair

        with patch('os.pipe', side_effect=track_pipe), patch(
                'subprocess.Popen', side_effect=OSError('synthetic spawn failure')), self.assertRaises(OSError):
            self.launcher.start(self.handle, self.plan)
        for fd in opened:
            with self.assertRaises(OSError):
                os.fstat(fd)
        self.assertEqual(self.state(), 'unresolved')
        with patch('subprocess.Popen') as spawn, self.assertRaises(Denied):
            self.launcher.start(self.handle, self.plan)
        spawn.assert_not_called()
        with self.assertRaisesRegex(Denied, 'worker-reap-unconfirmed'):
            self.launcher.reconcile(self.handle, self.plan)

    def test_unconfined_descendant_outlives_guarded_direct_worker(self):
        # Scope counterexample: a guardian is NOT a process-tree container.
        # The Mac fixture must independently deny fork/spawn before claiming
        # its single-worker boundary. General multiprocess tools remain unmet.
        code = '''import subprocess, sys
descendant = subprocess.Popen((sys.executable, '-B', '-u', '-c', sys.argv[1], sys.argv[2]),
    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
assert descendant.stdout.readline() == b'bootstrap-v2-ready\\n'
descendant.stdout.close()
print('bootstrap-v2-ready', flush=True)
sys.stdin.read()
'''
        plan = LaunchPlan((sys.executable, '-B', '-u', '-c', code, LOCK_WORKER, str(self.root)),
                          str(self.root))
        try:
            self.launcher.start(self.handle, plan)
            self.launcher.stop(self.actor())
            self.assertTrue(self.lock_held(), 'unconfined descendant counterexample disappeared')
        finally:
            (self.root / 'finish').touch()
            self.await_unlock()

    def test_unresolved_state_never_signals_an_unrelated_live_process(self):
        # A simulated stale numeric identity must not become kill authority.
        # There is deliberately no PID field in durable managed_launches.
        unrelated = subprocess.Popen((sys.executable, '-c', 'import sys; sys.stdin.read()'),
                                     stdin=subprocess.PIPE)
        try:
            with self.lab.transaction():
                self.lab.db.execute('INSERT INTO managed_launches VALUES (?, ?, ?)',
                                    (self.actor(), str(unrelated.pid), 'running'))
            with patch('os.kill') as kill, patch('subprocess.Popen') as spawn:
                with self.assertRaisesRegex(Denied, 'unresolved-previous-process'):
                    self.launcher.start(self.handle, self.plan)
                kill.assert_not_called()
                spawn.assert_not_called()
            self.assertIsNone(unrelated.poll())
        finally:
            unrelated.stdin.close()
            unrelated.wait(timeout=5)

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
        with self.assertRaisesRegex(Denied, 'worker-reap-unconfirmed'):
            restarted.reconcile(self.handle, self.plan)
        self.assertIsNone(first.process.poll())
        self.launcher.close()
        self.launcher = restarted
        second = self.launcher.start(self.handle, self.plan)
        self.assertIsNone(second.process.poll())

    def test_previous_attempt_proof_cannot_clear_a_live_replacement(self):
        first = self.launcher.start(self.handle, self.plan)
        second = self.launcher.start(self.handle, self.plan)
        previous = self.private / first.record
        current = self.private / second.record
        held = self.private / 'test-held-record'
        current.rename(held)
        try:
            previous.rename(current)
            restarted = ProcessLauncher(self.authority, self.vault)
            with self.assertRaisesRegex(Denied, 'worker-reap-unconfirmed'):
                restarted.reconcile(self.handle, self.plan)
            self.assertIsNone(second.process.poll())
            self.assertEqual(self.state(), 'running')
        finally:
            current.rename(previous)
            held.rename(current)

    def test_guardian_bytes_change_blocks_replacement_and_reconciliation(self):
        entry = self.root / 'test-guardian.py'
        entry.write_bytes(lifecycle.GUARDIAN_ENTRY.read_bytes())
        with patch.object(lifecycle, 'GUARDIAN_ENTRY', entry):
            old = self.launcher.start(self.handle, self.plan)
            entry.write_bytes(entry.read_bytes() + b'\n# synthetic drift\n')
            with patch('subprocess.Popen') as spawn:
                with self.assertRaisesRegex(Denied, 'launch-plan-changed'):
                    self.launcher.start(self.handle, self.plan)
                with self.assertRaisesRegex(Denied, 'launch-plan-changed'):
                    self.launcher.reconcile(self.handle, self.plan)
                spawn.assert_not_called()
            self.assertTrue(old.reaped)

    def test_renewal_keeps_principal_and_scope_and_revokes_old_ticket(self):
        old = self.launcher.start(self.handle, self.plan)
        journal = RequestJournal(self.authority, old.channel)
        journal.prepare(dict(method='renew', resource='note', epoch=0))
        self.assertEqual(json.loads(journal.send())['code'], 'unknown-method')
        with self.assertRaisesRegex(Denied, 'invalid-launch-renewal'):
            self.launcher.renew(self.handle, self.plan, '', 1200)
        self.assertIsNone(old.process.poll())
        self.launcher.renew(self.handle, self.plan, 'synthetic-parent-renewal', 1200)
        self.assertTrue(old.reaped and old.channel.closed)
        with self.assertRaisesRegex(Denied, 'launch-not-authorized'):
            self.authority.connect(self.ticket)
        restarted = ProcessLauncher(self.authority, self.vault)
        try:
            fresh = restarted.start(self.handle, self.plan)
            self.assertEqual(self.lab.actor(fresh.channel.capability), self.actor())
            self.assertEqual(fresh.channel.resources, frozenset({'note'}))
            self.assertEqual(RequestJournal(self.authority, fresh.channel).prepare(
                dict(method='write', resource='note', base=None, text='after renewal', epoch=0)), 2)
            self.assertEqual(tuple(self.lab.db.execute(
                'SELECT old_expiry, new_expiry, source FROM launch_renewals').fetchone()),
                (1100, 1200, 'synthetic-parent-renewal'))
        finally:
            restarted.close()

    def test_failed_renewal_commit_retains_original_ticket_and_missing_current_ticket_fails_closed(self):
        self.launcher.start(self.handle, self.plan)
        self.lab.db.execute("""CREATE TRIGGER reject_ticket_locator BEFORE INSERT ON renewed_tickets
            BEGIN SELECT RAISE(ABORT, 'synthetic-locator-failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.launcher.renew(self.handle, self.plan, 'synthetic-parent-renewal', 1200)
        self.assertEqual(self.launcher.ticket(self.handle), self.ticket)
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM launch_renewals').fetchone()[0], 0)
        self.lab.db.execute('DROP TRIGGER reject_ticket_locator')
        self.launcher.renew(self.handle, self.plan, 'synthetic-parent-renewal', 1200)
        physical = self.lab.db.execute('SELECT physical FROM renewed_tickets').fetchone()[0]
        (self.private / ('renew-' + physical)).unlink()
        self.assertTrue((self.private / self.handle).exists())
        with patch('subprocess.Popen') as spawn, self.assertRaises(FileNotFoundError):
            self.launcher.start(self.handle, self.plan)
        spawn.assert_not_called()
        with self.assertRaises(FileNotFoundError):
            self.launcher.renew(self.handle, self.plan, 'synthetic-parent-renewal', 1300)

    def test_revoked_ticket_cannot_be_renewed(self):
        self.launcher.start(self.handle, self.plan)
        self.authority.revoke(self.ticket)
        with self.assertRaisesRegex(Denied, 'launch-not-renewable'):
            self.launcher.renew(self.handle, self.plan, 'synthetic-parent-renewal', 1200)
        self.assertIsNone(self.lab.db.execute('SELECT 1 FROM renewed_tickets').fetchone())

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
        result = launch_agent(self.broker, child.channel, (), self.root, process=child.process, check=check,
                             stop=lambda: self.launcher.stop(self.actor()))
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
        self.assertEqual(first.process.returncode, 137)
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
            os.close(first.lifetime)
            first.process.wait(timeout=2)
            first.process.stdin.close()
            first.process.stdout.close()


if __name__ == '__main__':
    unittest.main()
