"""Offline negative controls for the Mac VM probe's evidence checks."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.v2.vm_probe import check_guest, stable_after_exit


class _Running:
    def poll(self):
        return None


class VMProbeEvidenceTests(unittest.TestCase):
    def test_live_guest_requires_a_separate_session(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "heartbeat-case").write_text("tick\ntick\ntick\n")
            log = root / "guest.log"
            log.write_text("GUEST_PROBE_ID=case\nGUEST_CHILD_PID=383\nGUEST_CHILD_SESSION=1\nGUEST_LOCK_HELD\n")
            with self.assertRaisesRegex(RuntimeError, "own session"):
                check_guest(log, root, _Running(), "case")

    def test_guest_effect_after_host_exit_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            heartbeat = root / "heartbeat-case"
            heartbeat.write_text("tick\n")

            def late_write(_seconds):
                with heartbeat.open("a") as output:
                    output.write("tick\n")

            with patch("experiments.v2.vm_probe.time.sleep", side_effect=late_write):
                with self.assertRaisesRegex(RuntimeError, "continued after host exit"):
                    stable_after_exit(root, "case")


if __name__ == "__main__":
    unittest.main()
