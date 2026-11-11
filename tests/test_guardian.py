"""Direct controls for the POSIX child guardian (fast; lifecycle covers the full path)."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

GUARDIAN = Path(__file__).resolve().parents[1] / 'src' / 'project_bootstrap' / 'guardian.py'
SLEEPER = [sys.executable, '-c', 'import time; time.sleep(30)']
STUBBORN = [sys.executable, '-c',
            'import signal, sys, time\n'
            'signal.signal(signal.SIGTERM, signal.SIG_IGN)\n'
            'print("armed", flush=True)\n'
            'time.sleep(30)']


class GuardianTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.report = Path(self.directory.name) / 'report'
        self.marker = Path(self.directory.name) / 'started'

    def tearDown(self):
        self.directory.cleanup()

    def start(self, argv, grace=0.5, deadline=30.0, close_parent=False):
        watch, parent_end = os.pipe()
        report = os.open(self.report, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        if close_parent:
            os.close(parent_end)
            parent_end = None
        guardian = subprocess.Popen(
            [sys.executable, '-B', str(GUARDIAN), str(watch), str(report), str(grace),
             str(time.monotonic() + deadline), json.dumps(argv)],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            pass_fds=(watch, report))
        os.close(watch)
        os.close(report)
        self.addCleanup(self.cleanup, guardian, parent_end)
        return guardian, parent_end

    @staticmethod
    def cleanup(guardian, parent_end):
        if parent_end is not None:
            try:
                os.close(parent_end)
            except OSError:
                pass
        if guardian.poll() is None:
            guardian.kill()
        guardian.wait(timeout=10)
        guardian.stdout.close()

    def finished(self, guardian):
        code = guardian.wait(timeout=10)
        return code, self.report.read_text(encoding='ascii')

    def child_writes_marker(self):
        return [sys.executable, '-c',
                f'open({str(self.marker)!r}, "w").close(); import time; time.sleep(30)']

    def test_dead_parent_before_start_spawns_nothing(self):
        guardian, _ = self.start(self.child_writes_marker(), close_parent=True)
        self.assertEqual(self.finished(guardian), (1, 'not-started\n'))
        self.assertFalse(self.marker.exists())

    def test_expired_deadline_spawns_nothing(self):
        guardian, _ = self.start(self.child_writes_marker(), deadline=-1)
        self.assertEqual(self.finished(guardian), (1, 'not-started\n'))
        self.assertFalse(self.marker.exists())

    def test_parent_eof_terminates_and_reaps_the_child(self):
        guardian, parent_end = self.start(SLEEPER)
        time.sleep(0.3)
        os.close(parent_end)
        self.assertEqual(self.finished(guardian), (128 + signal.SIGTERM,
                                                   f'reaped:-{signal.SIGTERM}\n'))

    def test_unexpected_data_on_the_pipe_also_stops(self):
        guardian, parent_end = self.start(SLEEPER)
        time.sleep(0.3)
        os.write(parent_end, b'x')
        self.assertEqual(self.finished(guardian)[1], f'reaped:-{signal.SIGTERM}\n')

    def test_child_that_ignores_terminate_is_killed_after_grace(self):
        guardian, parent_end = self.start(STUBBORN, grace=0.3)
        self.assertEqual(guardian.stdout.readline(), b'armed\n')
        os.close(parent_end)
        self.assertEqual(self.finished(guardian), (128 + signal.SIGKILL,
                                                   f'reaped:-{signal.SIGKILL}\n'))

    def test_deadline_stops_a_running_child(self):
        guardian, _ = self.start(SLEEPER, deadline=0.5)
        self.assertEqual(self.finished(guardian)[1], f'reaped:-{signal.SIGTERM}\n')

    def test_child_exit_is_reported(self):
        guardian, _ = self.start([sys.executable, '-c', 'raise SystemExit(3)'])
        self.assertEqual(self.finished(guardian), (3, 'reaped:3\n'))

    def test_terminating_the_guardian_still_reaps_the_child(self):
        guardian, _ = self.start(SLEEPER)
        time.sleep(0.3)
        guardian.terminate()
        self.assertEqual(self.finished(guardian)[1], f'reaped:-{signal.SIGTERM}\n')

    def test_worker_never_inherits_the_control_descriptors(self):
        probe = [sys.executable, '-c',
                 'import os\n'
                 'leaked = []\n'
                 'for fd in range(3, 64):\n'
                 '    try:\n'
                 '        os.fstat(fd)\n'
                 '        leaked.append(fd)\n'
                 '    except OSError:\n'
                 '        pass\n'
                 'print(leaked, flush=True)']
        guardian, _ = self.start(probe)
        line = guardian.stdout.readline()
        self.assertEqual(line, b'[]\n')
        self.assertEqual(self.finished(guardian)[1], 'reaped:0\n')


if __name__ == '__main__':
    unittest.main()
