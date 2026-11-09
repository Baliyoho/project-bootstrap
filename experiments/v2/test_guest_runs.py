"""Offline controls for the durable unshared guest run ledger."""

from pathlib import Path
import tempfile
import unittest

from experiments.v2.contracts import Denied, Lab
from experiments.v2.guest_runs import IDENTITY_DIGESTS, GuestRunLedger, guest_identity


def identity(probe_id):
    return guest_identity(probe_id, {name: format(index, 'x') * 64
                                     for index, name in enumerate(IDENTITY_DIGESTS, 1)})


def stopped(probe_id):
    return {'probe_id': probe_id, 'stop_marker': 'HOST_STOPPED state=0', 'host_exit': 0}


def booted(probe_id):
    return {'probe_id': probe_id, 'shared_directory': False}


class GuestRunLedgerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / 'lab.sqlite'
        self.lab = Lab(self.path)
        self.capability = self.lab.register('parent')
        self.ledger = GuestRunLedger(self.lab)

    def tearDown(self):
        self.lab.close()
        self.directory.cleanup()

    def reopen(self):
        self.lab.close()
        self.lab = Lab(self.path)
        self.ledger = GuestRunLedger(self.lab)

    def reconnect(self):
        """Trusted parent attaches a replacement channel for the same principal."""
        self.capability = self.lab.resume('parent')

    def denied(self, code, call, *args):
        with self.assertRaises(Denied) as caught:
            call(*args)
        self.assertEqual(str(caught.exception), code)

    def test_epoch_switch_requires_durable_retirement_and_survives_reopen(self):
        old = self.ledger.open_run('parent', 0, identity('old'))
        self.denied('guest-run-not-live', self.ledger.require_live, old, self.capability, 0)
        self.ledger.mark_running(old, booted('old'), self.capability)
        self.ledger.require_live(old, self.capability, 0)
        pending = self.lab.propose('{"factor":3}')
        self.denied('guest-run-not-live', self.ledger.require_live, old, self.capability, 0)
        self.denied('vm-retirement-unconfirmed', self.ledger.open_run,
                    'parent', pending, identity('new'))
        self.reopen()
        self.denied('vm-retirement-unconfirmed', self.ledger.require_quiescent, 'parent')
        self.ledger.retire(old, stopped('old'))
        self.ledger.require_quiescent('parent')
        self.reconnect()
        new = self.ledger.open_run('parent', pending, identity('new'))
        self.denied('guest-run-not-live', self.ledger.acknowledge,
                    self.capability, new, pending, '{"factor":3}')
        self.ledger.mark_running(new, booted('new'), self.capability)
        self.denied('unacknowledged-line', self.lab.activate)
        self.ledger.acknowledge(self.capability, new, pending, '{"factor":3}')
        self.lab.activate()
        self.ledger.require_live(new, self.capability, pending)
        self.denied('guest-run-not-live', self.ledger.require_live, old, self.capability, 0)
        self.reopen()
        self.denied('vm-retirement-unconfirmed', self.ledger.require_quiescent, 'parent')
        self.ledger.retire(new, stopped('new'))
        self.reopen()
        self.ledger.require_quiescent('parent')
        runs = self.ledger.runs('parent')
        self.assertEqual([(run['epoch'], run['state'], run['identity']['probe_id'])
                          for run in runs], [(0, 'retired', 'old'), (1, 'retired', 'new')])
        self.assertEqual(runs[0]['identity'], identity('old'))
        self.assertEqual(runs[1]['evidence'], stopped('new'))

    def test_retirement_kills_the_bound_channel(self):
        run = self.ledger.open_run('parent', 0, identity('case'))
        self.ledger.mark_running(run, booted('case'), self.capability)
        old_capability = self.capability
        self.ledger.retire(run, stopped('case'))
        self.denied('unknown-session', self.lab.actor, old_capability)
        self.denied('unknown-session', self.ledger.require_live, run, old_capability, 0)
        self.reconnect()
        self.assertEqual(self.lab.actor(self.capability), 'parent')

    def test_run_accepts_only_its_bound_channel(self):
        other = self.lab.register('other')
        run = self.ledger.open_run('parent', 0, identity('case'))
        self.denied('guest-channel-mismatch', self.ledger.mark_running,
                    run, booted('case'), other)
        self.denied('unknown-session', self.ledger.mark_running,
                    run, booted('case'), 'f' * 64)
        self.ledger.mark_running(run, booted('case'), self.capability)
        self.denied('guest-run-not-live', self.ledger.require_live, run, other, 0)
        # Same principal, newer channel: the guest's old binding no longer matches.
        self.reconnect()
        self.denied('guest-run-not-live', self.ledger.require_live, run, self.capability, 0)

    def test_crash_before_boot_confirmation_blocks_restart(self):
        run = self.ledger.open_run('parent', 0, identity('crash'))
        self.reopen()
        self.denied('vm-retirement-unconfirmed', self.ledger.require_quiescent, 'parent')
        self.denied('vm-retirement-unconfirmed', self.ledger.open_run,
                    'parent', 0, identity('again'))
        self.denied('guest-run-not-live', self.ledger.require_live, run, self.capability, 0)
        # A guest that never confirmed boot may still be retired by host evidence.
        self.ledger.retire(run, stopped('crash'))
        self.ledger.require_quiescent('parent')
        self.denied('vm-run-already-recorded', self.ledger.open_run,
                    'parent', 0, identity('again'))

    def test_retirement_rejects_guest_or_mismatched_evidence(self):
        run = self.ledger.open_run('parent', 0, identity('case'))
        self.ledger.mark_running(run, booted('case'), self.capability)
        for evidence in (
            None,
            {'probe_id': 'case', 'stop_marker': 'GUEST_STOPPED', 'host_exit': 0},
            {'probe_id': 'other', 'stop_marker': 'HOST_STOPPED state=0', 'host_exit': 0},
            {'probe_id': 'case', 'stop_marker': 'HOST_STOPPED state=0', 'host_exit': 1},
            {'probe_id': 'case', 'stop_marker': 'HOST_STOPPED state=0', 'host_exit': False},
            {'probe_id': 'case', 'stop_marker': 'HOST_STOPPED state=0', 'host_exit': 0,
             'pid': 123},
            {'probe_id': 'case', 'stop_marker': 'HOST_STOPPED state=0'},
        ):
            with self.subTest(evidence=evidence):
                self.denied('vm-retirement-unconfirmed', self.ledger.retire, run, evidence)
        self.ledger.require_live(run, self.capability, 0)
        self.ledger.retire(run, stopped('case'))
        self.reconnect()
        self.denied('vm-run-not-current', self.ledger.retire, run, stopped('case'))
        self.denied('vm-run-not-current', self.ledger.mark_running,
                    run, booted('case'), self.capability)

    def test_boot_confirmation_must_match_identity_and_have_no_share(self):
        run = self.ledger.open_run('parent', 0, identity('case'))
        for evidence in (None, booted('other'),
                         {'probe_id': 'case', 'shared_directory': True},
                         {'probe_id': 'case'}):
            with self.subTest(evidence=evidence):
                self.denied('guest-start-unconfirmed', self.ledger.mark_running,
                            run, evidence, self.capability)
        self.denied('unknown-guest-run', self.ledger.mark_running,
                    'f' * 32, booted('case'), self.capability)
        self.denied('unknown-guest-run', self.ledger.retire, 'not-a-run', stopped('case'))

    def test_identity_and_epoch_are_validated_before_recording(self):
        good = identity('case')
        for bad in (None, {**good, 'runner': 'A' * 64}, {**good, 'extra': 'x'},
                    {**good, 'share': '/tmp'}, {**good, 'probe_id': 'bad id'},
                    {key: value for key, value in good.items() if key != 'tool'}):
            with self.subTest(identity=bad):
                self.denied('invalid-guest-identity', self.ledger.open_run, 'parent', 0, bad)
        self.denied('premise-not-current', self.ledger.open_run, 'parent', 1, good)
        self.denied('premise-not-current', self.ledger.open_run, 'parent', True, good)
        self.denied('unknown-guest-actor', self.ledger.open_run, 'nobody', 0, good)
        self.assertEqual(self.ledger.runs('parent'), [])

    def test_acknowledge_is_bound_to_the_live_pending_run(self):
        old = self.ledger.open_run('parent', 0, identity('old'))
        self.ledger.mark_running(old, booted('old'), self.capability)
        pending = self.lab.propose('{"factor":3}')
        self.denied('guest-run-not-live', self.ledger.acknowledge,
                    self.capability, old, pending, '{"factor":3}')
        self.denied('guest-run-not-live', self.ledger.acknowledge,
                    self.capability, old, 0, '{"factor":3}')
        self.ledger.retire(old, stopped('old'))
        self.reconnect()
        new = self.ledger.open_run('parent', pending, identity('new'))
        self.ledger.mark_running(new, booted('new'), self.capability)
        self.denied('wrong-notice', self.ledger.acknowledge,
                    self.capability, new, pending, '{"factor":4}')
        other = self.lab.register('other')
        self.denied('guest-run-not-live', self.ledger.acknowledge,
                    other, new, pending, '{"factor":3}')
        self.assertEqual(self.lab.inbox(self.capability)[0]['acknowledged'], 0)


if __name__ == '__main__':
    unittest.main()
