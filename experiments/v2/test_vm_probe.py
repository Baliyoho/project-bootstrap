"""Offline negative controls for the Mac VM probe's evidence checks."""

from pathlib import Path
import io
import os
import tempfile
import unittest
from unittest.mock import patch

from experiments.v2.vm_probe import (VMRetirementGate, check_guest, host_log,
                                     read_guest_context_ack, read_guest_write_request,
                                     stable_after_exit)


class _Running:
    def __init__(self, reply=b""):
        read_fd, write_fd = os.pipe()
        os.write(write_fd, reply)
        os.close(write_fd)
        self.guest_reply = os.fdopen(read_fd, "rb", buffering=0)
        self.guest_request = io.BytesIO()

    def poll(self):
        return None

    def close(self):
        self.guest_reply.close()


class _Exited(_Running):
    def poll(self):
        return 0


class VMProbeEvidenceTests(unittest.TestCase):
    def test_unshared_guest_requires_both_host_and_guest_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "guest.log"
            ready = "GUEST_NO_SHARED_DIRECTORY\nGUEST_CHANNEL_READY\nGUEST_PROBE_ID=case\n"
            process = _Exited()
            try:
                for host, output in (
                    ("HOST_NO_SHARED_DIRECTORY\n", "GUEST_CHANNEL_READY\nGUEST_PROBE_ID=case\n"),
                    ("", ready),
                    # The guest console cannot supply the host marker.
                    ("", "HOST_NO_SHARED_DIRECTORY\n" + ready),
                    ("HOST_NO_SHARED_DIRECTORY\n", ready + "GUEST_MOUNTED\n"),
                    ("HOST_NO_SHARED_DIRECTORY\n", ready + "GUEST_UNEXPECTED_SHARED_DIRECTORY\n"),
                ):
                    with self.subTest(host=host, output=output):
                        log.write_text(output)
                        host_log(log).write_text(host)
                        with self.assertRaisesRegex(RuntimeError, "unshared guest was ready"):
                            check_guest(log, None, process, "case")
                log.write_text(ready)
                host_log(log).write_text("HOST_CONFIG_VALID\nHOST_NO_SHARED_DIRECTORY\n")
                self.assertEqual(check_guest(log, None, process, "case"), 0)
            finally:
                process.close()

    def test_guest_broker_request_is_bound_to_nonce_epoch_and_sequence(self):
        nonce = "a" * 32
        payload = b'{"id":1,"method":"write","resource":"note","base":null,"text":"10","epoch":0}'
        process = _Running(nonce.encode() + b" " + payload + b"\n")
        try:
            self.assertEqual(read_guest_write_request(process, nonce, 0, 1, 10**20),
                             payload + b"\n")
        finally:
            process.close()

    def test_guest_broker_request_rejects_wrong_epoch_and_extra_authority(self):
        nonce = "b" * 32
        for payload, message in (
            (b'{"id":1,"method":"write","resource":"note","base":null,"text":"10","epoch":1}',
             "wrong guest broker request identity or epoch"),
            (b'{"id":1,"method":"write","resource":"note","base":null,"text":"10","epoch":0,"actor":"other"}',
             "invalid guest broker request"),
        ):
            with self.subTest(payload=payload):
                process = _Running(nonce.encode() + b" " + payload + b"\n")
                try:
                    with self.assertRaisesRegex(RuntimeError, message):
                        read_guest_write_request(process, nonce, 0, 1, 10**20)
                finally:
                    process.close()

    def test_guest_broker_request_rejects_truncation(self):
        process = _Running(b"c" * 32 + b" {\"id\":1")
        try:
            with self.assertRaisesRegex(RuntimeError, "capability channel closed"):
                read_guest_write_request(process, "c" * 32, 0, 1, 10**20)
        finally:
            process.close()

    def test_guest_tool_context_ack_requires_exact_epoch_and_factor(self):
        nonce = "d" * 32
        for response in (f"{nonce} 1 2 READY\n", f"{nonce} 0 3 READY\n"):
            with self.subTest(response=response):
                process = _Running(response.encode())
                try:
                    with self.assertRaisesRegex(RuntimeError, "loaded context"):
                        read_guest_context_ack(process, nonce, 0, 2, 10**20)
                finally:
                    process.close()

    def test_guest_tool_write_requires_expected_base(self):
        nonce = "e" * 32
        base = "a" * 64
        raw = (f'{nonce} {{"id":2,"method":"write","resource":"note",'
               f'"base":"{base}","text":"21","epoch":1}}\n').encode()
        process = _Running(raw)
        try:
            self.assertEqual(read_guest_write_request(process, nonce, 1, 2, 10**20,
                                                      expected_base=base), raw[33:])
        finally:
            process.close()
        process = _Running(raw)
        try:
            with self.assertRaisesRegex(RuntimeError, "identity or epoch"):
                read_guest_write_request(process, nonce, 1, 2, 10**20,
                                         expected_base="b" * 64)
        finally:
            process.close()

    def test_guest_result_symlink_in_scratch_is_ignored(self):
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
            gate.process = _Running(f"{request_id} 0 10\n".encode())
            try:
                with patch("experiments.v2.vm_probe.secrets.token_hex", return_value=request_id):
                    self.assertEqual(gate.compute(0, 2, 5), 10)
                self.assertEqual(gate.process.guest_request.getvalue(),
                                 f"{request_id} 0 2 5\n".encode())
            finally:
                gate.process.close()
            self.assertEqual(private.read_text(), "synthetic-private-data")

    def test_guest_result_hardlink_in_scratch_is_ignored(self):
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
            gate.process = _Running(f"{request_id} 0 10\n".encode())
            try:
                with patch("experiments.v2.vm_probe.secrets.token_hex", return_value=request_id):
                    self.assertEqual(gate.compute(0, 2, 5), 10)
            finally:
                gate.process.close()
            self.assertEqual(private.read_text(), "synthetic-private-data")

    def test_guest_result_from_another_epoch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_id = "c" * 32
            (root / ("result-" + request_id)).write_text(f"{request_id} 1 10\n")
            gate = VMRetirementGate(root / "runner", root / "kernel", root / "ramdisk",
                                    root, root / "guest.log", "case")
            gate.process = _Running(f"{request_id} 1 10\n".encode())
            try:
                with patch("experiments.v2.vm_probe.secrets.token_hex", return_value=request_id):
                    with self.assertRaisesRegex(RuntimeError, "wrong guest result identity or epoch"):
                        gate.compute(0, 2, 5)
            finally:
                gate.process.close()

    def test_guest_reply_without_newline_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_id = "d" * 32
            gate = VMRetirementGate(root / "runner", root / "kernel", root / "ramdisk",
                                    root, root / "guest.log", "case")
            gate.process = _Running(f"{request_id} 0 10".encode())
            try:
                with patch("experiments.v2.vm_probe.secrets.token_hex", return_value=request_id):
                    with self.assertRaisesRegex(RuntimeError, "capability channel closed"):
                        gate.compute(0, 2, 5)
            finally:
                gate.process.close()

    def test_live_guest_requires_a_separate_session(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "heartbeat-case").write_text("tick\ntick\ntick\n")
            log = root / "guest.log"
            log.write_text("GUEST_PROBE_ID=case\nGUEST_CHILD_PID=383\nGUEST_CHILD_SESSION=1\nGUEST_LOCK_HELD\nGUEST_CHANNEL_READY\n")
            process = _Running()
            try:
                with self.assertRaisesRegex(RuntimeError, "own session"):
                    check_guest(log, root, process, "case")
            finally:
                process.close()

    def test_retirement_ignores_stop_marker_from_guest_console(self):
        class _Stopped(_Running):
            def poll(self):
                return None

            def wait(self, timeout=None):
                return 0

        class _Sink:
            def __init__(self):
                self.closed = []

            def write(self, data):
                self.closed.append(data)

            def close(self):
                pass

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "guest.log"
            for host, guest, accepted in (
                ("", "HOST_STOPPED state=0\n", False),
                ("HOST_STOPPED state=1\n", "HOST_STOPPED state=0\n", False),
                ("HOST_STARTED\nHOST_STOPPED state=0\n", "", True),
            ):
                with self.subTest(host=host, guest=guest):
                    log.write_text(guest)
                    host_log(log).write_text(host)
                    gate = VMRetirementGate(root / "runner", root / "kernel", root / "ramdisk",
                                            None, log, "case")
                    gate.process, gate.output, gate.control = _Stopped(), _Sink(), _Sink()
                    try:
                        if accepted:
                            self.assertEqual(gate.retire(), {
                                "probe_id": "case", "stop_marker": "HOST_STOPPED state=0",
                                "host_exit": 0})
                        else:
                            with self.assertRaisesRegex(RuntimeError, "not confirmed"):
                                gate.retire()
                    finally:
                        gate.process.close()

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
