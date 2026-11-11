"""Offline tests for the guest-side shell scripts (no VM, no busybox).

The scripts are run under the host's POSIX shells from a copy with exactly two
substitutions: `/usr/bin/busybox` becomes `command` (so `$BB printf` is the
shell's own printf) and `>/dev/hvc0` becomes an append to a temporary file
standing in for the guest console (a plain `>` would truncate a regular file
on every line, which the console device does not do). Replies are then fed to the host parsers in vm_probe, so a
change on either side of that wire format fails here.

Boundaries: the guest runs busybox ash; these run under dash (ash's close
relative) and /bin/sh when present, which is not the same binary. Mounts,
virtiofs, the serial ports and everything in vm_guest_init.sh above its
request loop are only covered by the real VM probe. The Swift runner has no
offline test at all.
"""

import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import unittest

from project_bootstrap import vm_probe

HERE = Path(__file__).resolve().parents[1] / 'src' / 'project_bootstrap'
SHELLS = [shell for shell in ('/bin/dash', '/bin/sh') if os.path.exists(shell)]
NONCE = '0123456789abcdef' * 2
BASE = 'ab' * 32


def host_copy(text, console):
    """The only two edits made to a guest script before running it on the host."""
    if (text.count('BB=/usr/bin/busybox\n') != 1 or '>/dev/hvc0' not in text
            or text.count('/dev/hvc0') != text.count('>/dev/hvc0')):
        raise AssertionError('guest script no longer matches the offline harness')
    return (text.replace('BB=/usr/bin/busybox\n', 'BB=command\n')
            .replace('/usr/bin/busybox', 'command').replace('>/dev/hvc0', f'>>{console}'))


@unittest.skipUnless(SHELLS, 'no POSIX shell to run the guest scripts')
class ManagedWorkerScriptTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.console = self.root / 'console'
        self.script = self.root / 'worker.sh'
        self.script.write_text(
            host_copy((HERE / 'vm_managed_worker.sh').read_text(encoding='ascii'), self.console),
            encoding='ascii')

    def tearDown(self):
        self.directory.cleanup()

    def run_lines(self, shell, lines):
        self.console.write_text('', encoding='ascii')
        done = subprocess.run([shell, str(self.script)], input=''.join(lines).encode('ascii'),
                              capture_output=True, timeout=10)
        return done.returncode, done.stdout.decode('ascii'), self.console.read_text('ascii').split()

    def start(self, shell):
        self.console.write_text('', encoding='ascii')
        process = subprocess.Popen([shell, str(self.script)], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, bufsize=0)
        process.guest_request, process.guest_reply = process.stdin, process.stdout
        self.addCleanup(process.wait)
        self.addCleanup(process.stdout.close)
        self.addCleanup(process.stdin.close)
        return process

    def test_replies_satisfy_the_host_parsers(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                process = self.start(shell)
                process.stdin.write(f'L {NONCE} 4 -3\n'.encode('ascii'))
                vm_probe.read_guest_context_ack(process, NONCE, 4, -3, time.monotonic() + 5)
                process.stdin.write(f'W {NONCE} 7 2 null\n'.encode('ascii'))
                first = vm_probe.read_guest_write_request(process, NONCE, 4, 2,
                                                          time.monotonic() + 5)
                self.assertEqual(first, b'{"id":2,"method":"write","resource":"note",'
                                        b'"base":null,"text":"-21","epoch":4}\n')
                process.stdin.write(f'W {NONCE} 0 3 {BASE}\n'.encode('ascii'))
                second = vm_probe.read_guest_write_request(process, NONCE, 4, 3,
                                                           time.monotonic() + 5,
                                                           expected_base=BASE)
                self.assertIn(f'"base":"{BASE}","text":"0"'.encode('ascii'), second)
                process.stdin.close()
                self.assertEqual(process.wait(timeout=5), 0)
                self.assertEqual(self.console.read_text('ascii').split(),
                                 [f'GUEST_TOOL_WRITE_REQUEST={NONCE}'] * 2
                                 + ['GUEST_TOOL_CHANNEL_CLOSED'])

    def test_each_malformed_line_gets_its_code_and_no_reply(self):
        load = f'L {NONCE} 0 3\n'
        cases = [
            ('GUEST_TOOL_BAD_NONCE', [f'L {NONCE.upper()} 0 3\n']),
            ('GUEST_TOOL_BAD_NONCE', ['L\n']),
            ('GUEST_TOOL_BAD_REQUEST', [f'L {NONCE[:31]} 0 3\n']),
            ('GUEST_TOOL_BAD_REQUEST', [f'X {NONCE} 0 3\n']),
            ('GUEST_TOOL_BAD_CONTEXT', [f'L {NONCE} 0 3 extra\n']),
            ('GUEST_TOOL_BAD_CONTEXT', [f'L {NONCE} 0\n']),
            ('GUEST_TOOL_BAD_CONTEXT', [f'L {NONCE} -1 3\n']),
            ('GUEST_TOOL_BAD_CONTEXT', [f'L {NONCE} 0 3-1\n']),
            ('GUEST_TOOL_BAD_CONTEXT', [f'L {NONCE} 0 -\n']),
            ('GUEST_TOOL_BAD_CONTEXT', [f'L {NONCE} 0 --3\n']),
            ('GUEST_TOOL_BAD_CONTEXT', [f'L {NONCE} 0 010\n']),
            ('GUEST_TOOL_BAD_CONTEXT', [f'L {NONCE} 0 1234567\n']),
            ('GUEST_TOOL_NOT_LOADED', [f'W {NONCE} 5 1 null\n']),
            ('GUEST_TOOL_ALREADY_LOADED', [load, f'L {NONCE} 1 9\n']),
            ('GUEST_TOOL_BAD_REQUEST', [load, f'W {NONCE} 1-2 1 null\n']),
            ('GUEST_TOOL_BAD_REQUEST', [load, f'W {NONCE} - 1 null\n']),
            ('GUEST_TOOL_BAD_REQUEST', [load, f'W {NONCE} 08 1 null\n']),
            ('GUEST_TOOL_BAD_REQUEST', [load, f'W {NONCE} 5 -1 null\n']),
            ('GUEST_TOOL_BAD_REQUEST', [load, f'W {NONCE} 5 x null\n']),
            ('GUEST_TOOL_BAD_BASE', [load, f'W {NONCE} 5 1\n']),
            ('GUEST_TOOL_BAD_BASE', [load, f'W {NONCE} 5 1 {BASE[:63]}\n']),
            ('GUEST_TOOL_BAD_BASE', [load, f'W {NONCE} 5 1 {BASE.upper()}\n']),
            ('GUEST_TOOL_BAD_BASE', [load, f'W {NONCE} 5 1 null x\n']),
        ]
        for shell in SHELLS:
            for code, lines in cases:
                with self.subTest(shell=shell, line=lines[-1].strip()):
                    status, replies, console = self.run_lines(shell, lines)
                    self.assertEqual(status, 0)
                    expected = f'{NONCE} 0 3 READY\n' if lines[0] == load else ''
                    self.assertEqual(replies, expected)
                    self.assertEqual(console, [code, 'GUEST_TOOL_CHANNEL_CLOSED'])

    def test_a_refused_line_does_not_end_the_worker_or_change_its_premise(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                status, replies, console = self.run_lines(shell, [
                    f'L {NONCE} 2 3\n', f'W {NONCE} - 1 null\n', f'L {NONCE} 9 9\n',
                    f'W {NONCE} 5 1 null\n'])
                self.assertEqual(status, 0)
                self.assertEqual(replies.splitlines()[-1],
                                 f'{NONCE} ' + '{"id":1,"method":"write","resource":"note",'
                                 '"base":null,"text":"15","epoch":2}')
                self.assertEqual(console, ['GUEST_TOOL_BAD_REQUEST', 'GUEST_TOOL_ALREADY_LOADED',
                                           f'GUEST_TOOL_WRITE_REQUEST={NONCE}',
                                           'GUEST_TOOL_CHANNEL_CLOSED'])


@unittest.skipUnless(SHELLS, 'no POSIX shell to run the guest scripts')
class SharedPathRequestLoopTests(unittest.TestCase):
    """Only the request loop at the end of vm_guest_init.sh (the superseded shared path)."""

    MARK = 'while read -r first second third fourth fifth sixth <&3; do\n'

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.console = self.root / 'console'
        text = (HERE / 'vm_guest_init.sh').read_text(encoding='ascii')
        if text.count(self.MARK) != 1 or text.count('PROBE_ID=\n') != 1:
            raise AssertionError('vm_guest_init.sh no longer matches the offline harness')
        head = text[:text.index('PROBE_ID=\n')]
        # Keep the interpreter line, BB and the number helpers; drop the three mounts.
        head = ''.join(line for line in head.splitlines(keepends=True) if ' mount ' not in line)
        self.script = self.root / 'loop.sh'
        self.script.write_text(host_copy(head + text[text.index(self.MARK):], self.console),
                               encoding='ascii')

    def tearDown(self):
        self.directory.cleanup()

    def exchange(self, shell, lines):
        """fd 3 is one bidirectional socket, like the guest's /dev/hvc1."""
        self.console.write_text('', encoding='ascii')
        ours, theirs = socket.socketpair()
        with ours, theirs:
            process = subprocess.Popen([shell, '-c', 'exec 3<&0; . "$1"', 'loop', str(self.script)],
                                       stdin=theirs, stdout=subprocess.DEVNULL)
            theirs.close()
            ours.sendall(''.join(lines).encode('ascii'))
            ours.shutdown(socket.SHUT_WR)
            ours.settimeout(10)
            replies = b''
            while chunk := ours.recv(4096):
                replies += chunk
            status = process.wait(timeout=10)
        return status, replies.decode('ascii'), self.console.read_text('ascii').split()

    def test_compute_and_write_lines_keep_their_wire_format(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                status, replies, console = self.exchange(shell, [
                    f'{NONCE} 1 -3 7\n', f'W {NONCE} 1 3 7 4\n'])
                self.assertEqual(status, 0)
                self.assertEqual(replies, f'{NONCE} 1 -21\n{NONCE} ' + '{"id":4,"method":"write",'
                                 '"resource":"note","base":null,"text":"21","epoch":1}\n')
                self.assertEqual(console, [f'GUEST_COMPUTED={NONCE}',
                                           f'GUEST_WRITE_REQUEST={NONCE}', 'GUEST_CHANNEL_CLOSED'])

    def test_malformed_numbers_are_refused_and_the_loop_survives(self):
        bad = [f'{NONCE} 1 3 1-2\n', f'{NONCE} 1 - 2\n', f'{NONCE} -1 3 2\n', f'{NONCE} 1 3 08\n',
               f'{NONCE} 1 3\n', f'{NONCE} 1 3 2 9\n', f'{NONCE.upper()} 1 3 2\n',
               f'W {NONCE} 1 3 2 -4\n', f'W {NONCE} 1 3 2\n', f'W {NONCE} 1 3 1-2 4\n']
        for shell in SHELLS:
            with self.subTest(shell=shell):
                status, replies, console = self.exchange(shell, bad + [f'{NONCE} 0 2 5\n'])
                self.assertEqual(status, 0)
                self.assertEqual(replies, f'{NONCE} 0 10\n')
                self.assertEqual(console, ['GUEST_BAD_REQUEST'] * len(bad)
                                 + [f'GUEST_COMPUTED={NONCE}', 'GUEST_CHANNEL_CLOSED'])


class HarnessTests(unittest.TestCase):
    def test_harness_refuses_a_script_it_no_longer_understands(self):
        with self.assertRaises(AssertionError):
            host_copy('#!/usr/bin/sh\necho hello\n', '/tmp/x')
        self.assertIsNotNone(shutil.which('sh'))


if __name__ == '__main__':
    unittest.main()
