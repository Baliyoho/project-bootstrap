"""Verifier execution changes must preserve failures, skips and child cleanup."""
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import verify_bootstrap as verifier


class VerifierExecutionTests(unittest.TestCase):
    def test_background_keeps_large_output_and_failure(self):
        command = [sys.executable, '-c',
                   'import sys; print("x"*200000); print("bad",file=sys.stderr); sys.exit(7)']
        with verifier.background_command(command, verifier.ROOT) as collect:
            result = collect()
        self.assertEqual(result.returncode, 7)
        self.assertEqual(len(result.stdout.strip()), 200000)
        self.assertEqual(result.stderr.strip(), 'bad')

    def test_exception_reaps_child(self):
        real_popen = subprocess.Popen
        children = []
        def capture(*args, **kwargs):
            child = real_popen(*args, **kwargs)
            children.append(child)
            return child
        with patch.object(verifier.subprocess, 'Popen', capture):
            with self.assertRaisesRegex(RuntimeError, 'fixture'):
                with verifier.background_command(
                        [sys.executable, '-c', 'import time; time.sleep(30)'], verifier.ROOT):
                    raise RuntimeError('fixture')
        self.assertIsNotNone(children[0].poll())

    def test_invalid_or_failed_regression_is_not_success(self):
        valid = json.dumps({'harness_passed': True, 'strict_ready': False,
                            'tests': {'run': 1, 'failed': 0, 'errors': 0,
                                      'skipped': 0, 'needs_uv': []},
                            'archived': 'archive/v2-barrier/'})
        for code, output, expected in [(0, valid, 'OK'), (7, valid, 'FAIL'),
                                        (0, '{}', 'FAIL'), (0, 'not json', 'FAIL')]:
            with self.subTest(code=code, output=output):
                with patch.object(verifier, 'results', []), redirect_stdout(io.StringIO()):
                    verifier.step_v2(subprocess.CompletedProcess([], code, output, ''))
                    self.assertEqual(verifier.results[-1][0], expected)

    def test_quiet_keeps_failures_skips_and_exit_codes(self):
        for status, expected in [('OK', 0), ('FAIL', 2), ('SKIP', 1)]:
            with self.subTest(status=status):
                output = io.StringIO()
                with patch.object(sys, 'argv', ['verify_bootstrap.py', '--quiet']), \
                        patch.object(verifier, 'results', []), \
                        patch.object(verifier, 'QUIET', False), \
                        patch.object(verifier, 'run_checks',
                                     lambda d, t: verifier.record(status, 'fixture', 'detail')), \
                        redirect_stdout(output):
                    self.assertEqual(verifier.main(), expected)
                self.assertEqual('fixture' in output.getvalue(), status != 'OK')
                if status != 'OK':
                    self.assertIn('detail', output.getvalue())


if __name__ == '__main__':
    unittest.main()
