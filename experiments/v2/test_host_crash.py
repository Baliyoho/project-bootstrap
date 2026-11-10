"""Offline survey: what a whole-host crash or power loss can leave behind.

Nothing here crashes a machine. Each test builds one state that a host crash
could plausibly leave on disk (a runner log cut at any byte, a zero-filled
tail, a ledger file cut short or gone) and records what the existing ledger
and crash-release gates do with it. No guard was added for these tests.

What they show (2026-11-10):
- A torn or zero-filled runner log is never accepted as stop evidence.
- A run whose host died mid-run stays blocked: the runner died with the
  host, so the stop line was never printed. Without a recorded boot session
  it has NO release path. With one (decision Q15 (a), added 2026-11-10) a
  different boot session at release time is the host evidence, still behind
  the local terminal confirmation; the same boot keeps it blocked.
- A ledger file cut short never reads as "nothing running".
- A ledger file that is gone (or empty) reads exactly like a first start.
  That is a known gap, kept below as an observed counterexample, not a
  guarantee: nothing outside the database anchors that a ledger existed.

Not covered: a real power loss (SQLite and filesystem durability are taken on
trust: synchronous=FULL), disk corruption that keeps the file size, and a
runner killed after printing the stop line on a real VM (only the ledger side
of that is simulated here).
"""

import gc
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
import warnings

from experiments.v2 import crash_release
from experiments.v2.contracts import Denied, Lab
from experiments.v2.guest_runs import IDENTITY_DIGESTS, GuestRunLedger, guest_identity
from experiments.v2.test_crash_release import BOOT_A, BOOT_B, CLEAN, FakeTerminal


def identity(probe_id):
    return guest_identity(probe_id, {name: format(index, 'x') * 64
                                     for index, name in enumerate(IDENTITY_DIGESTS, 1)})


class HostCrashStateTests(unittest.TestCase):
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
        lab.close()  # the host is gone; only what reached the disk remains
        self.opened = []

    def tearDown(self):
        self.directory.cleanup()

    def opener(self, terminal):
        def open_terminal():
            self.opened.append(terminal)
            return terminal
        return open_terminal

    def denied(self, code, call, *args, **kwargs):
        with self.assertRaises(Denied) as caught:
            call(*args, **kwargs)
        self.assertEqual(str(caught.exception), code)

    def run_state(self):
        lab = Lab(self.db)
        try:
            return GuestRunLedger(lab).runs('parent')[0]['state']
        finally:
            lab.close()

    def test_runner_log_cut_at_any_byte_is_not_stop_evidence(self):
        data = CLEAN.encode('ascii')
        accepted = []
        for size in range(len(data) + 1):
            Path(self.log).write_bytes(data[:size])
            try:
                crash_release.host_evidence(self.log, 'crash')
            except Denied as error:
                self.assertEqual(str(error), 'crash-release-unconfirmed')
            else:
                accepted.append(size)
        # Only the complete log, or one missing nothing but its final newline.
        self.assertEqual(accepted, [len(data) - 1, len(data)])

    def test_zero_filled_runner_log_is_not_stop_evidence(self):
        data = CLEAN.encode('ascii')
        torn = {
            'all zeros, same length': b'\0' * len(data),
            'zeros after a clean log': data + b'\0' * 512,
            'zeros where the stop line would be': data[:data.index(b'HOST_STOPPED')]
                                                  + b'\0' * len('HOST_STOPPED state=0\n'),
            'zeros then a stop line': b'\0' * 64 + data,
        }
        for name, content in torn.items():
            with self.subTest(log=name):
                Path(self.log).write_bytes(content)
                self.denied('crash-release-unconfirmed', crash_release.release, self.db,
                            self.run, self.opener(FakeTerminal()))
                self.assertEqual(self.opened, [])
        self.assertEqual(self.run_state(), 'running')

    def test_host_death_mid_run_stays_blocked_with_no_release_path(self):
        """The runner dies with the host, so the stop line is never written."""
        leftovers = {
            'log up to the start line': 'HOST_NO_SHARED_DIRECTORY\nHOST_CONFIG_VALID\nHOST_STARTED\n',
            'log never reached the disk': None,
        }
        for name, text in leftovers.items():
            with self.subTest(log=name):
                if os.path.lexists(self.log):
                    os.remove(self.log)
                if text is not None:
                    Path(self.log).write_text(text, encoding='ascii')
                lab = Lab(self.db)
                try:
                    ledger = GuestRunLedger(lab)
                    self.denied('vm-retirement-unconfirmed', ledger.require_quiescent, 'parent')
                    self.denied('vm-retirement-unconfirmed', ledger.open_run, 'parent', 0,
                                identity('after-reboot'), self.log + '.2')
                finally:
                    lab.close()
                self.denied('crash-release-unconfirmed', crash_release.release, self.db,
                            self.run, self.opener(FakeTerminal()))
                self.assertEqual(self.opened, [])
                self.assertEqual(self.run_state(), 'running')

    def test_host_death_mid_run_with_a_recorded_boot_needs_a_reboot(self):
        """Q15 (a): same leftovers, but the parent recorded the boot session first."""
        lab = Lab(self.db)
        try:
            capability = lab.register('booted')
            ledger = GuestRunLedger(lab)
            run = ledger.open_run('booted', 0, identity('booted'), host_log=self.log + '.b',
                                  boot_session=BOOT_A)
            ledger.mark_running(run, {'probe_id': 'booted', 'shared_directory': False},
                                capability)
        finally:
            lab.close()
        Path(self.log + '.b').write_text(
            'HOST_NO_SHARED_DIRECTORY\nHOST_CONFIG_VALID\nHOST_STARTED\n', encoding='ascii')
        self.denied('crash-release-unconfirmed', crash_release.release, self.db, run,
                    self.opener(FakeTerminal()), lambda: BOOT_A)
        self.assertEqual(self.opened, [])
        crash_release.release(self.db, run, self.opener(FakeTerminal()), lambda: BOOT_B)
        self.assertEqual(len(self.opened), 1)
        lab = Lab(self.db)
        try:
            GuestRunLedger(lab).require_quiescent('booted')
        finally:
            lab.close()

    def test_host_death_before_boot_confirmation_is_the_same_dead_end(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        db = Path(directory.name) / 'lab.sqlite'
        log = str(Path(directory.name) / 'guest.log.host')
        lab = Lab(db)
        lab.register('parent')
        run = GuestRunLedger(lab).open_run('parent', 0, identity('early'), host_log=log)
        lab.close()
        self.denied('crash-release-unconfirmed', crash_release.release, db, run,
                    self.opener(FakeTerminal()))
        self.assertEqual(self.opened, [])
        lab = Lab(db)
        try:
            self.denied('vm-retirement-unconfirmed',
                        GuestRunLedger(lab).require_quiescent, 'parent')
        finally:
            lab.close()

    def test_runner_killed_after_its_stop_line_needs_the_release_path(self):
        """Ledger side only: the stop line is on disk but the runner did not exit 0."""
        Path(self.log).write_text(CLEAN, encoding='ascii')
        lab = Lab(self.db)
        try:
            ledger = GuestRunLedger(lab)
            self.denied('vm-retirement-unconfirmed', ledger.retire, self.run,
                        {'probe_id': 'crash', 'stop_marker': 'HOST_STOPPED state=0',
                         'host_exit': -9})
        finally:
            lab.close()
        self.assertEqual(self.run_state(), 'running')
        crash_release.release(self.db, self.run, self.opener(FakeTerminal()))
        self.assertEqual(len(self.opened), 1)
        self.assertEqual(self.run_state(), 'retired')

    def test_ledger_file_cut_short_never_reads_as_quiescent(self):
        data = self.db.read_bytes()
        self.assertGreater(len(data), 4096)
        outcomes = set()
        # Lab() raising on a broken file leaves its connection to the garbage collector.
        catcher = warnings.catch_warnings()
        catcher.__enter__()
        self.addCleanup(catcher.__exit__, None, None, None)
        self.addCleanup(gc.collect)
        warnings.simplefilter('ignore', ResourceWarning)
        for size in range(512, len(data), 512):
            self.db.write_bytes(data[:size])
            try:
                lab = Lab(self.db)
            except sqlite3.DatabaseError:
                outcomes.add('unreadable')
                continue
            try:
                GuestRunLedger(lab).require_quiescent('parent')
            except sqlite3.DatabaseError:
                outcomes.add('unreadable')
            except Denied as error:
                self.assertEqual(str(error), 'vm-retirement-unconfirmed')
                outcomes.add('blocked')
            else:
                self.fail(f'ledger cut to {size} bytes read as quiescent')
            finally:
                lab.close()
            with self.assertRaises((sqlite3.DatabaseError, Denied)):
                crash_release.release(self.db, self.run, self.opener(FakeTerminal()))
        self.assertIn('unreadable', outcomes)
        self.assertEqual(self.opened, [])

    def test_counterexample_lost_ledger_file_reads_as_a_first_start(self):
        """Known gap, recorded on purpose: nothing outside the database says it existed."""
        for name, lose in (('deleted', self.db.unlink),
                           ('emptied', lambda: self.db.write_bytes(b''))):
            with self.subTest(ledger=name):
                lose()
                lab = Lab(self.db)
                try:
                    ledger = GuestRunLedger(lab)
                    ledger.require_quiescent('parent')  # passes: no row survived
                    self.assertEqual(ledger.runs('parent'), [])
                    # The old principal is gone too, so a guest cannot start by accident...
                    self.denied('unknown-guest-actor', ledger.open_run, 'parent', 0,
                                identity('fresh'), self.log + '.2')
                    self.denied('unknown-session', lab.actor, self.capability)
                    # ...but a parent that simply registers again is back at epoch 0.
                    lab.register('parent')
                    again = ledger.open_run('parent', 0, identity('fresh'), self.log + '.2')
                    self.assertNotEqual(again, self.run)
                finally:
                    lab.close()
                self.denied('unknown-guest-run', crash_release.release, self.db, self.run,
                            self.opener(FakeTerminal()))
        self.assertEqual(self.opened, [])


if __name__ == '__main__':
    unittest.main()
