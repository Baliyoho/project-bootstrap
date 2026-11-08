import json
from unittest import TestCase
from unittest.mock import patch

from experiments.v2 import managed_fixture as managed
from experiments.v2.contracts import Denied


class ManagedFixtureTests(TestCase):
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
