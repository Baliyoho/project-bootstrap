from pathlib import Path
import tempfile
import unittest

from experiments.v2.contracts import Denied, Lab
from experiments.v2.supervisor import Supervisor, Worker, probe_supervisor


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


if __name__ == '__main__':
    unittest.main()
