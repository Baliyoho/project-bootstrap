"""Offline negative controls for the Mac VM probe's evidence checks."""

from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

from experiments.v2.vm_probe import VMRetirementGate, check_guest, stable_after_exit


class _Running:
    def poll(self):
        return None


class VMProbeEvidenceTests(unittest.TestCase):
    def test_guest_result_symlink_cannot_make_host_read_outside_scratch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            share = root / "share"
            share.mkdir()
            private = root / "private"
            private.write_text("synthetic-private-data")
            request_id = "a" * 32
            (share / ("result-" + request_id)).symlink_to(private)
            gate = VMRetirementGate(root / "runner", root / "kernel", root / "ramdisk",
                                    share, root / "guest.log", "case")
            gate.process = _Running()
            with patch("experiments.v2.vm_probe.secrets.token_hex", return_value=request_id):
                with self.assertRaisesRegex(RuntimeError, "not a regular file"):
                    gate.compute(0, 2, 5)
            self.assertEqual(private.read_text(), "synthetic-private-data")

    def test_guest_result_hardlink_cannot_make_host_read_outside_scratch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            share = root / "share"
            share.mkdir()
            private = root / "private"
            private.write_text("synthetic-private-data")
            request_id = "b" * 32
            os.link(private, share / ("result-" + request_id))
            gate = VMRetirementGate(root / "runner", root / "kernel", root / "ramdisk",
                                    share, root / "guest.log", "case")
            gate.process = _Running()
            with patch("experiments.v2.vm_probe.secrets.token_hex", return_value=request_id):
                with self.assertRaisesRegex(RuntimeError, "not a regular file"):
                    gate.compute(0, 2, 5)
            self.assertEqual(private.read_text(), "synthetic-private-data")

    def test_guest_result_from_another_epoch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_id = "c" * 32
            (root / ("result-" + request_id)).write_text(f"{request_id} 1 10\n")
            gate = VMRetirementGate(root / "runner", root / "kernel", root / "ramdisk",
                                    root, root / "guest.log", "case")
            gate.process = _Running()
            with patch("experiments.v2.vm_probe.secrets.token_hex", return_value=request_id):
                with self.assertRaisesRegex(RuntimeError, "wrong guest result identity or epoch"):
                    gate.compute(0, 2, 5)

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
