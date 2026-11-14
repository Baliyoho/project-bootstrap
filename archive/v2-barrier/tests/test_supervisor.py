from pathlib import Path
import tempfile
import unittest

from project_bootstrap.contracts import Denied, Lab
from project_bootstrap.supervisor import Supervisor, Worker, probe_supervisor


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='bootstrap-v2-supervisor-')
        self.lab = Lab(Path(self.temp.name) / 'lab.sqlite')

    def tearDown(self):
        self.lab.close()
        self.temp.cleanup()

    def test_running_line_rebuilt_before_new_epoch(self):
        report = probe_supervisor(self.lab)
        self.assertEqual(report['result'], '通過')
        self.assertTrue(all(report['checks'].values()))

    def test_replacement_failure_stops_old_work_and_never_activates(self):
        a = self.lab.register('line-a')

        def fails_new_epoch(epoch, context):
            if epoch:
                raise Denied('injected-launch-failure')
            return Worker(epoch, context)

        supervisor = Supervisor(self.lab, {'line-a': a}, {'factor': 2}, fails_new_epoch)
        old = supervisor.workers['line-a']
        try:
            supervisor.begin('line-a', 7)
            with self.assertRaises(Denied):
                supervisor.change({'factor': 3})
            self.assertIsNotNone(old.process.poll())
            state = self.lab.db.execute('SELECT * FROM state').fetchone()
            self.assertEqual((state['epoch'], state['pending']), (0, 1))
            with self.assertRaises(Denied):
                supervisor.begin('line-a', 7)
            with self.assertRaises(Denied):
                self.lab.begin(a, 0)
        finally:
            supervisor.close()

    def test_offline_recipient_cannot_be_acknowledged_by_supervisor(self):
        a = self.lab.register('line-a')
        self.lab.register('offline-line')
        supervisor = Supervisor(self.lab, {'line-a': a}, {'factor': 2})
        try:
            with self.assertRaises(Denied):
                supervisor.change({'factor': 3})
            self.assertFalse(supervisor.ready)
            self.assertEqual(self.lab.db.execute('SELECT epoch FROM state').fetchone()[0], 0)
            self.assertTrue(all(worker.process.poll() is not None for worker in supervisor.workers.values()))
        finally:
            supervisor.close()

    def test_repeated_changes_do_not_reuse_old_pending_work(self):
        a = self.lab.register('line-a')
        supervisor = Supervisor(self.lab, {'line-a': a}, {'factor': 2})
        try:
            supervisor.begin('line-a', 7)
            supervisor.change({'factor': 3})
            with self.assertRaises(Denied):
                supervisor.finish('line-a')
            supervisor.change({'factor': 5})
            supervisor.begin('line-a', 7)
            self.assertEqual(supervisor.finish('line-a'), 35)
        finally:
            supervisor.close()


    def denied(self, code, call, *args):
        with self.assertRaises(Denied) as caught:
            call(*args)
        self.assertEqual(str(caught.exception), code)

    def test_each_refusal_has_its_own_code(self):
        a = self.lab.register('line-a')
        supervisor = Supervisor(self.lab, {'line-a': a}, {'factor': 2})
        try:
            supervisor.begin('line-a', 7)
            self.denied('supervisor-not-ready', supervisor.begin, 'line-a', 7)
            self.assertEqual(supervisor.finish('line-a'), 14)
            self.denied('no-current-work', supervisor.finish, 'line-a')
            supervisor.begin('line-a', 1)
            supervisor.close()
            # Pending work on a closed supervisor is not finishable either.
            self.denied('no-current-work', supervisor.finish, 'line-a')
            self.denied('supervisor-not-ready', supervisor.begin, 'line-a', 7)
        finally:
            supervisor.close()

    def test_failed_proposal_leaves_supervisor_closed(self):
        a = self.lab.register('line-a')
        supervisor = Supervisor(self.lab, {'line-a': a}, {'factor': 2})
        try:
            self.lab.propose('{"factor":9}')
            self.denied('change-already-pending', supervisor.change, {'factor': 3})
            self.denied('supervisor-not-ready', supervisor.begin, 'line-a', 7)
        finally:
            supervisor.close()

    def test_worker_answers_are_checked(self):
        a = self.lab.register('line-a')
        for kind, code, step in (('ready', 'worker-context-not-confirmed', 'start'),
                                 ('started', 'work-not-started', 'begin'),
                                 ('result', 'wrong-result-epoch', 'finish')):
            with self.subTest(kind=kind):
                made = []

                def factory(epoch, context, kind=kind, made=made):
                    return LyingWorker(kind, epoch, context, made)
                if step == 'start':
                    self.denied(code, Supervisor, self.lab, {'line-a': a}, {'factor': 2}, factory)
                    self.assertIsNotNone(made[0].process.poll())
                    continue
                supervisor = Supervisor(self.lab, {'line-a': a}, {'factor': 2}, factory)
                try:
                    if step == 'finish':
                        supervisor.begin('line-a', 7)
                        self.denied(code, supervisor.finish, 'line-a')
                    else:
                        self.denied(code, supervisor.begin, 'line-a', 7)
                    self.assertFalse(supervisor.ready)
                    self.assertIsNotNone(made[0].process.poll())
                finally:
                    supervisor.close()

    def test_worker_end_and_stuck_stop_are_reported(self):
        worker = Worker(0, {'factor': 2})
        try:
            worker.process.kill()
            worker.process.wait(timeout=5)
            self.denied('worker-ended', worker.read)
        finally:
            worker.stop()
        worker = Worker(0, {'factor': 2})
        real = worker.process
        worker.process = StuckProcess(real)
        try:
            self.denied('worker-not-stopped', worker.stop)
        finally:
            real.kill()
            real.wait(timeout=5)


class LyingWorker(Worker):
    """Real worker whose one reply of the given type claims the wrong epoch."""

    def __init__(self, kind, epoch, context, made):
        self.kind = kind
        made.append(self)  # before start, so a refused start is still visible
        super().__init__(epoch, context)

    def read(self):
        message = super().read()
        if message.get('type') == self.kind:
            message = dict(message, epoch=message['epoch'] + 1)
        return message


class StuckProcess:
    """Wraps a live process but ignores every attempt to end it."""

    def __init__(self, real):
        self.real, self.pid = real, real.pid
        self.stdin, self.stdout = real.stdin, real.stdout

    def poll(self):
        return None

    def terminate(self):
        pass

    def kill(self):
        pass

    def wait(self, timeout=None):
        return None


if __name__ == '__main__':
    unittest.main()
