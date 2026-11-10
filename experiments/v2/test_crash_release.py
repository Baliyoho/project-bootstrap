"""Offline controls for releasing a guest run after its parent crashed (Q1 (a))."""

import contextlib
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from experiments.v2 import crash_release
from experiments.v2.contracts import Denied, Lab
from experiments.v2.guest_runs import IDENTITY_DIGESTS, GuestRunLedger, guest_identity

CLEAN = 'HOST_NO_SHARED_DIRECTORY\nHOST_CONFIG_VALID\nHOST_STARTED\nHOST_STOPPED state=0\n'


def identity(probe_id):
    return guest_identity(probe_id, {name: format(index, 'x') * 64
                                     for index, name in enumerate(IDENTITY_DIGESTS, 1)})


class FakeTerminal:
    """Answers the challenge it was shown, unless told to answer something else."""

    def __init__(self, answer=None, pending=()):
        self.name = '/dev/ttys999'
        self.answer, self.pending = answer, list(pending)
        self.shown, self.closed = '', False

    def discard_pending(self):
        self.pending.clear()

    def write(self, text):
        self.shown += text

    def read_line(self):
        if self.pending:
            return self.pending.pop(0)
        if self.answer is not None:
            return self.answer
        return self.shown.split('type exactly:\n  ', 1)[1].split('\n', 1)[0]

    def close(self):
        self.closed = True


class CrashReleaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.db = self.root / 'lab.sqlite'
        self.log = str(self.root / 'guest.log.host')
        lab = Lab(self.db)
        self.capability = lab.register('parent')
        ledger = GuestRunLedger(lab)
        self.run = ledger.open_run('parent', 0, identity('crash'), host_log=self.log)
        ledger.mark_running(self.run, {'probe_id': 'crash', 'shared_directory': False},
                            self.capability)
        lab.close()  # the parent is gone; only the database remains
        self.opened = []

    def tearDown(self):
        self.directory.cleanup()

    def host(self, text):
        Path(self.log).write_text(text, encoding='utf-8')

    def opener(self, terminal):
        def open_terminal():
            self.opened.append(terminal)
            return terminal
        return open_terminal

    def state(self):
        lab = Lab(self.db)
        try:
            return GuestRunLedger(lab).runs('parent')[0]
        finally:
            lab.close()

    def denied(self, code, call, *args, **kwargs):
        with self.assertRaises(Denied) as caught:
            call(*args, **kwargs)
        self.assertEqual(str(caught.exception), code)

    def test_host_stop_and_local_answer_release_the_run(self):
        self.host(CLEAN)
        terminal = FakeTerminal()
        evidence, confirmation = crash_release.release(self.db, self.run, self.opener(terminal))
        self.assertTrue(terminal.closed)
        self.assertIn(self.run, terminal.shown)
        self.assertEqual(confirmation['tty'], '/dev/ttys999')
        run = self.state()
        self.assertEqual(run['state'], 'retired')
        self.assertEqual(run['evidence']['kind'], 'crash-release')
        self.assertEqual(run['evidence']['host'], evidence)
        lab = Lab(self.db)
        try:
            ledger = GuestRunLedger(lab)
            ledger.require_quiescent('parent')
            # The crashed guest's channel died with the release.
            self.denied('unknown-session', lab.actor, self.capability)
            pending = lab.propose('{"factor":3}')
            ledger.open_run('parent', pending, identity('next'), host_log=self.log + '.2')
        finally:
            lab.close()
        self.denied('vm-run-not-current', crash_release.release, self.db, self.run,
                    self.opener(FakeTerminal()))

    def test_no_host_proof_means_nobody_is_asked(self):
        bad_logs = {
            'missing': None,
            'empty': '',
            'no stop': 'HOST_NO_SHARED_DIRECTORY\nHOST_CONFIG_VALID\nHOST_STARTED\n',
            'stop error': 'HOST_NO_SHARED_DIRECTORY\nHOST_CONFIG_VALID\nHOST_STARTED\n'
                          'HOST_STOP_ERROR boom\n',
            'never started': 'HOST_NO_SHARED_DIRECTORY\nHOST_CONFIG_VALID\nHOST_STOPPED state=0\n',
            'shared directory': 'HOST_CONFIG_VALID\nHOST_STARTED\nHOST_STOPPED state=0\n',
            'guest console mixed in': 'HOST_NO_SHARED_DIRECTORY\nHOST_CONFIG_VALID\n'
                                      'HOST_STARTED\nGUEST_PROBE_ID=crash\nHOST_STOPPED state=0\n',
            'stop twice': CLEAN + 'HOST_STOPPED state=0\n',
            'activity after stop': CLEAN + 'HOST_STARTED\n',
            'not ascii': CLEAN.replace('STARTED', 'STARTÉD'),
            # A clean prefix must not hide what comes after the read limit.
            'too long': CLEAN + '\n' * crash_release.MAX_LOG + 'HOST_STOP_ERROR boom\n',
        }
        for name, text in bad_logs.items():
            with self.subTest(log=name):
                if os.path.lexists(self.log):
                    os.remove(self.log)
                if text is not None:
                    self.host(text)
                self.denied('crash-release-unconfirmed', crash_release.release, self.db,
                            self.run, self.opener(FakeTerminal()))
                self.assertEqual(self.opened, [])
                self.assertEqual(self.state()['state'], 'running')

    def test_symlinked_or_non_file_log_is_not_proof(self):
        real = self.root / 'elsewhere.host'
        real.write_text(CLEAN, encoding='ascii')
        os.symlink(real, self.log)
        self.denied('crash-release-unconfirmed', crash_release.release, self.db, self.run,
                    self.opener(FakeTerminal()))
        os.remove(self.log)
        os.mkdir(self.log)
        self.denied('crash-release-unconfirmed', crash_release.release, self.db, self.run,
                    self.opener(FakeTerminal()))
        self.assertEqual(self.state()['state'], 'running')

    def test_wrong_or_pre_typed_answer_keeps_the_block(self):
        self.host(CLEAN)
        for answer in ('', 'yes', f'release {self.run[:8]} 000000'):
            with self.subTest(answer=answer):
                self.denied('crash-release-not-approved', crash_release.release, self.db,
                            self.run, self.opener(FakeTerminal(answer=answer)))
                self.assertEqual(self.state()['state'], 'running')
        # Input queued before the challenge appeared is thrown away, not used.
        terminal = FakeTerminal(pending=['yes'])
        crash_release.release(self.db, self.run, self.opener(terminal))
        self.assertEqual(self.state()['state'], 'retired')

    def test_run_recorded_without_host_log_can_never_be_released(self):
        lab = Lab(self.db)
        try:
            lab.register('legacy')
            run = GuestRunLedger(lab).open_run('legacy', 0, identity('old'))
        finally:
            lab.close()
        self.host(CLEAN)
        self.denied('crash-release-unavailable', crash_release.release, self.db, run,
                    self.opener(FakeTerminal()))
        self.assertEqual(self.opened, [])
        # Even a well-formed record cannot point the ledger at some other log.
        lab = Lab(self.db)
        try:
            evidence = {**crash_release.host_evidence(self.log, 'old')}
            self.denied('crash-release-unavailable', GuestRunLedger(lab).release_crashed, run,
                        evidence, {'method': 'local-terminal', 'run_id': run,
                                   'tty': '/dev/ttys1', 'confirmed_at': 'now'})
        finally:
            lab.close()

    def test_ledger_rejects_forged_evidence_or_confirmation(self):
        self.host(CLEAN)
        good = crash_release.host_evidence(self.log, 'crash')
        approved = {'method': 'local-terminal', 'run_id': self.run, 'tty': '/dev/ttys1',
                    'confirmed_at': '2026-11-10T08:00:00+00:00'}
        lab = Lab(self.db)
        try:
            ledger = GuestRunLedger(lab)
            for evidence in (None, {**good, 'host_log': self.log + '.other'},
                             {**good, 'probe_id': 'other'},
                             {**good, 'stop_marker': 'GUEST_STOPPED'},
                             {**good, 'host_log_sha256': 'x'}, {**good, 'pid': 1},
                             {key: value for key, value in good.items() if key != 'host_log'}):
                with self.subTest(evidence=evidence):
                    self.denied('crash-release-unconfirmed', ledger.release_crashed,
                                self.run, evidence, approved)
            for confirmation in (None, {**approved, 'method': 'agent'},
                                 {**approved, 'run_id': 'f' * 32},
                                 {**approved, 'tty': 'ssh'}, {**approved, 'remote': True},
                                 {**approved, 'confirmed_at': 0}):
                with self.subTest(confirmation=confirmation):
                    self.denied('crash-release-not-approved', ledger.release_crashed,
                                self.run, good, confirmation)
            self.assertEqual(ledger.runs('parent')[0]['state'], 'running')
            ledger.release_crashed(self.run, good, approved)
            self.denied('vm-run-not-current', ledger.release_crashed, self.run, good, approved)
        finally:
            lab.close()

    def test_terminal_must_be_local_and_real(self):
        self.denied('crash-release-not-local', crash_release.open_local_terminal,
                    env={'SSH_CONNECTION': '10.0.0.1 22 10.0.0.2 22'},
                    open_tty=lambda: self.fail('opened a terminal over SSH'))

        def no_tty():
            raise OSError(6, 'Device not configured')
        self.denied('crash-release-no-terminal', crash_release.open_local_terminal,
                    env={}, open_tty=no_tty)
        read_end, write_end = os.pipe()
        os.close(write_end)
        self.denied('crash-release-no-terminal', crash_release.open_local_terminal,
                    env={}, open_tty=lambda: read_end)
        with self.assertRaises(OSError):
            os.fstat(read_end)  # closed on refusal

    def test_host_log_must_be_a_plain_absolute_path(self):
        lab = Lab(self.db)
        try:
            lab.register('other')
            ledger = GuestRunLedger(lab)
            for path in ('relative.host', '/tmp/../etc/x.host', 7, ''):
                with self.subTest(path=path):
                    self.denied('invalid-host-log', ledger.open_run,
                                'other', 0, identity('x'), host_log=path)
        finally:
            lab.close()

    def test_old_ledger_gains_the_column_and_stays_blocked(self):
        path = self.root / 'old.sqlite'
        lab = Lab(path)
        lab.register('parent')
        lab.db.execute('''CREATE TABLE guest_runs (
            run_id TEXT PRIMARY KEY, actor TEXT NOT NULL, epoch INTEGER NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('starting', 'running', 'retired')),
            identity TEXT NOT NULL, channel TEXT, evidence TEXT)''')
        lab.db.execute("INSERT INTO guest_runs VALUES (?, 'parent', 0, 'running', ?, NULL, NULL)",
                       ('a' * 32, json.dumps(identity('old'), sort_keys=True)))
        lab.db.commit()
        lab.close()
        self.host(CLEAN)
        self.denied('crash-release-unavailable', crash_release.release, path, 'a' * 32,
                    self.opener(FakeTerminal()))
        columns = [row[1] for row in sqlite3.connect(path).execute('PRAGMA table_info(guest_runs)')]
        self.assertIn('host_log', columns)

    def test_cli_refuses_without_a_terminal_or_with_bad_arguments(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(crash_release.main([]), 2)
        self.host(CLEAN)
        old = os.environ.get('SSH_TTY')
        os.environ['SSH_TTY'] = '/dev/ttys5'
        try:
            with contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(crash_release.main([str(self.db), self.run]), 1)
            self.assertIn('crash-release-not-local', err.getvalue())
        finally:
            if old is None:
                del os.environ['SSH_TTY']
            else:
                os.environ['SSH_TTY'] = old
        self.assertEqual(self.state()['state'], 'running')


if __name__ == '__main__':
    unittest.main()
