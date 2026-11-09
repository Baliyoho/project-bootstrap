import json
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time
from unittest import TestCase
from unittest.mock import patch

from experiments.v2 import managed_fixture as managed
from experiments.v2.contracts import Denied


CRASH_PARENT = '''from pathlib import Path
import sys
from experiments.v2.managed_fixture import open_managed
with open_managed(Path(sys.argv[1])) as (fixture, repo):
    fixture.start(2)
    phase = sys.argv[2]
    if phase == 'active-changed':
        fixture.change(3)
    fixture.begin(7)
    fixture.stage_result()
    interrupted = fixture.begin(8)
    def pause():
        print(fixture.handle + ' ' + interrupted, flush=True)
        sys.stdin.read()
    if phase.startswith('active-'):
        pause()
    elif phase == 'replacement':
        activate = fixture.lab.activate
        def pause_before_activate():
            pause()
            activate()
        fixture.lab.activate = pause_before_activate
    else:
        stop = fixture.launcher.stop
        def pause_before_stop(actor):
            pause()
            stop(actor)
        fixture.launcher.stop = pause_before_stop
    if not phase.startswith('active-'):
        fixture.change(3)
'''


class ManagedFixtureTests(TestCase):
    def crash_parent(self, root, phase):
        with subprocess.Popen([sys.executable, '-B', '-u', '-c', CRASH_PARENT, str(root), phase],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE) as parent:
            try:
                self.assertTrue(select.select([parent.stdout], [], [], 5)[0])
                handle, interrupted = parent.stdout.readline().decode().split()
                self.assertTrue(managed.TicketVault.valid(handle))
                return handle, interrupted
            finally:
                parent.kill()
                parent.wait(timeout=5)

    def resume_after_reap(self, fixture):
        until = time.monotonic() + 5
        while True:
            try:
                fixture.resume()
                return
            except Denied as error:
                if str(error) != 'worker-reap-unconfirmed' or time.monotonic() >= until:
                    raise
                time.sleep(0.01)

    def test_real_worker_switches_context_and_only_new_result_reaches_disk(self):
        result = managed.probe_managed()
        if not managed.supported():
            self.assertEqual(result['result'], '未驗證')
            return
        self.assertEqual(result['result'], '通過', result)
        self.assertTrue(all(result['checks'].values()))

    def test_stop_failure_keeps_barrier_closed_and_does_not_launch_replacement(self):
        if not managed.supported():
            self.assertEqual(managed.probe_managed()['result'], '未驗證')
            return
        with managed.managed_environment() as (fixture, repo):
            fixture.start(2)
            old = fixture.child
            fixture.begin(7)
            fixture.stage_result()
            launcher = fixture.launcher
            real_stop = launcher.stop
            failed_once = False

            def unconfirmed_stop(actor):
                nonlocal failed_once
                if failed_once:
                    return real_stop(actor)
                failed_once = True
                self.assertIsNone(old.process.poll())
                stale = json.loads(fixture.outbox().send())
                self.assertEqual(stale['code'], 'premise-not-current')
                raise Denied('worker-reap-unconfirmed')

            with patch.object(launcher, 'stop', side_effect=unconfirmed_stop), patch.object(
                    launcher, 'start', wraps=launcher.start) as start:
                with self.assertRaisesRegex(Denied, 'worker-reap-unconfirmed'):
                    fixture.change(3)
                start.assert_not_called()
            self.assertTrue(old.reaped)
            self.assertFalse((repo / 'managed.txt').exists())
            self.assertEqual(tuple(fixture.lab.db.execute('SELECT epoch, pending FROM state').fetchone()), (0, 1))
            with self.assertRaisesRegex(Denied, 'managed-fixture-not-ready'):
                fixture.begin(8)

    def test_vm_retirement_failure_blocks_activation_and_restart(self):
        if not managed.supported():
            self.skipTest('macOS confined worker required')

        class FailedGate:
            probe_id = 'synthetic-failed-stop'
            closed = False

            def start(self):
                pass

            def retire(self):
                raise RuntimeError('synthetic-vm-stop-unconfirmed')

            def close(self):
                self.closed = True

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with managed.open_managed(root) as (fixture, repo):
                fixture.start(2)
                handle = fixture.handle
                gate = FailedGate()
                fixture.attach_vm_gate(gate)
                fixture.begin(7)
                fixture.stage_result()
                with self.assertRaisesRegex(RuntimeError, 'synthetic-vm-stop-unconfirmed'):
                    fixture.change(3)
                self.assertTrue(gate.closed)
                self.assertEqual(tuple(fixture.lab.db.execute(
                    'SELECT epoch, pending FROM state').fetchone()), (0, 1))
                self.assertEqual(fixture.lab.db.execute(
                    'SELECT state FROM managed_vm_runs').fetchone()[0], 'running')
                self.assertFalse((repo / 'managed.txt').exists())
            with managed.open_managed(root, handle) as (fixture, _):
                until = time.monotonic() + 5
                while True:
                    try:
                        fixture.resume()
                    except Denied as error:
                        if str(error) == 'worker-reap-unconfirmed' and time.monotonic() < until:
                            time.sleep(0.01)
                            continue
                        self.assertEqual(str(error), 'vm-retirement-unconfirmed')
                        break
                    self.fail('resume accepted an unconfirmed VM retirement')

    def test_vm_launch_failure_is_recorded_before_a_guest_can_start(self):
        if not managed.supported():
            self.skipTest('macOS confined worker required')

        class FailedStart:
            probe_id = 'synthetic-start-failure'

            def start(self):
                row = fixture.lab.db.execute(
                    'SELECT state FROM managed_vm_runs').fetchone()
                self.test.assertEqual(row[0], 'unconfirmed')
                raise RuntimeError('synthetic-vm-start-failure')

            def close(self):
                pass

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with managed.open_managed(root) as (fixture, _):
                fixture.start(2)
                gate = FailedStart()
                gate.test = self
                with self.assertRaisesRegex(RuntimeError, 'synthetic-vm-start-failure'):
                    fixture.attach_vm_gate(gate)
                self.assertFalse(fixture.ready)
                self.assertEqual(fixture.lab.db.execute(
                    'SELECT state FROM managed_vm_runs').fetchone()[0], 'unconfirmed')

    def test_new_epoch_guest_does_not_reopen_retired_vm_record(self):
        if not managed.supported():
            self.skipTest('macOS confined worker required')

        class SyntheticGate:
            def __init__(self, probe_id):
                self.probe_id = probe_id

            def start(self):
                pass

            def retire(self):
                return {'probe_id': self.probe_id, 'stop_marker': 'synthetic-stop'}

            def close(self):
                pass

        with managed.managed_environment() as (fixture, _):
            fixture.start(2)
            fixture.attach_vm_gate(SyntheticGate('old'))
            fixture.change(3)
            fixture.attach_vm_gate(SyntheticGate('new'))
            rows = list(fixture.lab.db.execute(
                'SELECT epoch, state, probe_id FROM managed_vm_runs ORDER BY epoch'))
            self.assertEqual([tuple(row) for row in rows],
                             [(0, 'retired', 'old'), (1, 'running', 'new')])
            fixture.change(4)
            rows = list(fixture.lab.db.execute(
                'SELECT epoch, state, probe_id FROM managed_vm_runs ORDER BY epoch'))
            self.assertEqual([tuple(row) for row in rows],
                             [(0, 'retired', 'old'), (1, 'retired', 'new')])

    def test_real_replacement_with_wrong_context_digest_cannot_acknowledge(self):
        if not managed.supported():
            self.assertEqual(managed.probe_managed()['result'], '未驗證')
            return
        receive_context = 'epoch, context_bytes = json.loads(sys.stdin.readline())'
        wrong_context = managed.PROGRAM.replace(receive_context,
            receive_context + '\nif epoch: context_bytes = \'{"factor":2}\'')
        with patch.object(managed, 'PROGRAM', wrong_context), managed.managed_environment() as (fixture, repo):
            fixture.start(2)
            old = fixture.child
            fixture.begin(7)
            with self.assertRaisesRegex(Denied, 'worker-context-not-confirmed'):
                fixture.change(3)
            self.assertTrue(old.reaped and fixture.child.reaped)
            self.assertEqual(tuple(fixture.lab.db.execute('SELECT epoch, pending FROM state').fetchone()), (0, 1))
            self.assertEqual(fixture.lab.db.execute('SELECT acknowledged FROM notices').fetchone()[0], 0)
            self.assertFalse((repo / 'managed.txt').exists())

    def test_offline_recipient_blocks_activation_and_rolls_back_replacement_ack(self):
        if not managed.supported():
            self.assertEqual(managed.probe_managed()['result'], '未驗證')
            return
        with managed.managed_environment() as (fixture, _):
            fixture.lab.register('synthetic-offline')
            fixture.start(2)
            with self.assertRaisesRegex(Denied, 'unacknowledged-line'):
                fixture.change(3)
            self.assertTrue(fixture.child.reaped)
            self.assertEqual(tuple(fixture.lab.db.execute('SELECT epoch, pending FROM state').fetchone()), (0, 1))
            self.assertEqual(fixture.lab.db.execute('SELECT SUM(acknowledged) FROM notices').fetchone()[0], 0)

    def test_lost_response_retries_same_bytes_without_applying_another_write(self):
        if not managed.supported():
            self.assertEqual(managed.probe_managed()['result'], '未驗證')
            return
        with managed.managed_environment() as (fixture, repo):
            fixture.start(2)
            fixture.change(3)
            fixture.begin(7)
            request_id = fixture.stage_result()
            broker = fixture.launcher.broker
            dispatch = broker.dispatch
            raw = fixture.lab.db.execute('SELECT raw FROM client_requests').fetchone()[0]

            def lose_response(channel, request):
                self.assertEqual(request, raw)
                self.assertEqual(json.loads(dispatch(channel, request))['code'], 'ok')
                raise OSError('synthetic response loss')

            with patch.object(broker, 'dispatch', side_effect=lose_response):
                with self.assertRaises(OSError):
                    fixture.send()
            self.assertEqual(fixture.lab.db.execute('SELECT completed FROM client_requests').fetchone()[0], 0)
            with patch.object(broker, 'dispatch', wraps=dispatch) as retry:
                response = fixture.send()
                retry.assert_called_once_with(fixture.child.channel, raw)
            self.assertEqual(response['id'], request_id)
            self.assertEqual(response['code'], 'ok')
            self.assertEqual(fixture.lab.db.execute('SELECT count(*) FROM writes').fetchone()[0], 1)
            self.assertEqual(fixture.lab.db.execute('SELECT completed FROM client_requests').fetchone()[0], 1)
            self.assertEqual((repo / 'managed.txt').read_bytes(), b'21')

    def test_sigkill_before_stop_or_activation_resumes_the_same_pending_notice(self):
        if not managed.supported():
            self.assertEqual(managed.probe_managed()['result'], '未驗證')
            return
        for phase in ('old-worker', 'replacement'):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                handle, _ = self.crash_parent(root, phase)
                with managed.open_managed(root, handle) as (fixture, repo):
                    lab = fixture.lab
                    self.assertEqual(tuple(lab.db.execute('SELECT epoch, pending FROM state').fetchone()), (0, 1))
                    self.assertEqual(lab.db.execute('SELECT acknowledged FROM notices').fetchone()[0], 0)
                    self.resume_after_reap(fixture)
                    self.assertEqual(fixture.epoch, 1)
                    self.assertEqual(lab.db.execute('SELECT count(*) FROM notices').fetchone()[0], 1)
                    self.assertEqual(fixture.send()['code'], 'premise-not-current')
                    self.assertFalse((repo / 'managed.txt').exists())
                    fixture.begin(7)
                    fixture.stage_result()
                    self.assertEqual(fixture.send()['code'], 'ok')
                    self.assertEqual((repo / 'managed.txt').read_bytes(), b'21')

    def test_sigkill_in_active_epoch_restores_context_and_invalidates_unfinished_work(self):
        if not managed.supported():
            self.assertEqual(managed.probe_managed()['result'], '未驗證')
            return
        for phase, epoch, factor in (('active-initial', 0, 2), ('active-changed', 1, 3)):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                handle, interrupted = self.crash_parent(root, phase)
                with managed.open_managed(root, handle) as (fixture, repo):
                    self.resume_after_reap(fixture)
                    self.assertEqual(fixture.epoch, epoch)
                    with self.assertRaisesRegex(Denied, 'invalid-operation'):
                        fixture.lab.complete(fixture.child.channel.capability, interrupted)
                    first = fixture.send()
                    self.assertEqual(first['code'], 'ok')
                    self.assertEqual((repo / 'managed.txt').read_text(), str(7 * factor))
                    fixture.begin(9)
                    fixture.stage_result(base=first['digest'])
                    self.assertEqual(fixture.send()['code'], 'ok')
                    self.assertEqual((repo / 'managed.txt').read_text(), str(9 * factor))

    def test_expired_ticket_requires_explicit_renewal_before_crash_recovery(self):
        if not managed.supported():
            self.assertEqual(managed.probe_managed()['result'], '未驗證')
            return
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            handle, _ = self.crash_parent(root, 'active-changed')
            with managed.open_managed(root, handle) as (fixture, _):
                expiry = fixture.lab.db.execute('SELECT expires FROM launch_permits').fetchone()[0]
                fixture.lab.authority_clock = lambda: expiry + 1
                with self.assertRaisesRegex(Denied, 'launch-not-authorized'):
                    fixture.resume()
                until = time.monotonic() + 5
                while True:
                    try:
                        fixture.launcher.renew(handle, fixture.plan, 'synthetic-parent-renewal', expiry + 60)
                        break
                    except Denied as error:
                        if str(error) != 'worker-reap-unconfirmed' or time.monotonic() >= until:
                            raise
                        time.sleep(0.01)
            with managed.open_managed(root, handle) as (fixture, repo):
                fixture.lab.authority_clock = lambda: expiry + 1
                fixture.resume()
                self.assertEqual(fixture.epoch, 1)
                self.assertEqual(fixture.send()['code'], 'ok')
                self.assertEqual((repo / 'managed.txt').read_bytes(), b'21')
