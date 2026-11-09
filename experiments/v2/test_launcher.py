import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

from experiments.v2.broker import Broker
from experiments.v2.contracts import Denied, Lab
from experiments.v2.launcher import LaunchAuthority, RequestJournal
from experiments.v2.materializer import Materializer


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='bootstrap-v2-launch-')
        self.root = Path(self.temp.name)
        self.path = self.root / 'private.sqlite'
        self.now = 1000
        self.lab = Lab(self.path, authority_clock=lambda: self.now)
        self.broker = Broker(self.lab)
        self.authority = LaunchAuthority(self.broker)
        self.ticket = self.authority.issue(('note', 'budget'), 'synthetic-parent-approval', 1100)
        self.channel = self.authority.connect(self.ticket)
        self.client = RequestJournal(self.authority, self.channel)

    def tearDown(self):
        self.lab.close()
        self.temp.cleanup()

    def write(self):
        return dict(method='write', resource='note', base=None, text='first', epoch=0)

    def effect(self):
        return dict(method='effect', resource='budget', kind='paid-api', epoch=0)

    def count(self, table):
        return self.lab.db.execute('SELECT count(*) FROM ' + table).fetchone()[0]

    def restart(self):
        self.lab.close()
        self.lab = Lab(self.path, authority_clock=lambda: self.now)
        self.broker = Broker(self.lab)
        self.authority = LaunchAuthority(self.broker)
        self.channel = self.authority.connect(self.ticket)
        self.client = RequestJournal(self.authority, self.channel)

    def test_principal_name_or_forged_ticket_cannot_resume(self):
        actor = self.lab.actor(self.channel.capability)
        for forged in (actor, '0' * 64, '', self.ticket[:-1]):
            with self.subTest(forged=forged[:3]), self.assertRaises(Denied):
                self.authority.connect(forged)
        self.assertEqual(self.count('sessions'), 1)
        self.client.prepare(self.write())
        self.assertEqual(json.loads(self.client.send())['code'], 'ok')

    def test_exact_child_request_is_durable_and_sequence_is_parent_checked(self):
        raw = b'{"id":1,"method":"write","resource":"note","base":null,"text":"10","epoch":0}\n'
        for bad in (raw.replace(b'"id":1', b'"id":2'),
                    raw.replace(b'"id":1', b'"id":1,"id":1')):
            with self.subTest(raw=bad), self.assertRaises(Denied):
                self.client.prepare_raw(bad)
        self.assertEqual(self.count('client_requests'), 0)
        self.assertEqual(self.client.prepare_raw(raw), 1)
        self.assertEqual(self.lab.db.execute('SELECT raw FROM client_requests').fetchone()[0], raw)
        with self.assertRaises(Denied):
            self.client.prepare_raw(raw)
        self.restart()
        self.assertEqual(json.loads(self.client.send())['code'], 'ok')
        self.assertEqual(self.lab.db.execute('SELECT raw, completed FROM client_requests').fetchone()[:],
                         (raw, 1))
        self.assertEqual(self.count('writes'), 1)

    def test_rotation_invalidates_old_pipe_and_restart_preserves_scope(self):
        old = self.channel
        replacement = self.authority.connect(self.ticket)
        raw = json.dumps(dict(self.write(), id=1)).encode()
        self.assertEqual(json.loads(self.broker.dispatch(old, raw))['code'], 'session-no-longer-valid')
        self.assertEqual(self.count('writes'), 0)
        self.assertEqual(json.loads(self.broker.dispatch(replacement, raw))['code'], 'ok')
        self.restart()
        self.assertEqual(self.channel.resources, frozenset(('note', 'budget')))

    def test_expired_and_revoked_permits_block_existing_pipe_and_resume(self):
        for revoke in (False, True):
            with self.subTest(revoke=revoke):
                deadline = self.now + 10
                ticket = self.authority.issue(('note',), 'synthetic-parent', deadline)
                channel = self.authority.connect(ticket)
                if revoke:
                    self.authority.revoke(ticket)
                else:
                    self.now = deadline
                raw = json.dumps(dict(self.write(), id=1)).encode()
                self.assertEqual(json.loads(self.broker.dispatch(channel, raw))['code'], 'session-no-longer-valid')
                with self.assertRaises(Denied):
                    self.authority.connect(ticket)
                self.assertEqual(self.count('writes'), 0)
                self.assertEqual(self.count('receipts'), 0)

    def test_process_exit_after_outbox_or_broker_commit_recovers(self):
        script = '''import json, os, sys
from experiments.v2.contracts import Lab
from experiments.v2.broker import Broker
from experiments.v2.launcher import LaunchAuthority, RequestJournal
path, stage = sys.argv[1:]
ticket = sys.stdin.readline().strip()
lab = Lab(path, authority_clock=lambda: 1001)
broker = Broker(lab)
authority = LaunchAuthority(broker)
channel = authority.connect(ticket)
client = RequestJournal(authority, channel)
client.prepare(dict(method='effect', resource='budget', kind='paid-api', epoch=0))
if stage == 'after-broker':
    dispatch = broker.dispatch
    def crash(channel, raw):
        dispatch(channel, raw)
        os._exit(73)
    broker.dispatch = crash
    client.send()
os._exit(73)
'''
        for stage in ('after-outbox', 'after-broker'):
            with self.subTest(stage=stage):
                ticket = self.authority.issue(('budget',), 'synthetic-parent', 1100)
                self.authority.grant(ticket, 'paid-api', 'budget', 2, 'synthetic-human', 1090)
                before = self.count('effects')
                result = subprocess.run([sys.executable, '-B', '-c', script, str(self.path), stage],
                    input=ticket + '\n', text=True, capture_output=True, timeout=10,
                    cwd=Path(__file__).resolve().parents[2],
                    env={'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1'})
                self.assertEqual(result.returncode, 73, result.stderr)
                self.now = 1002
                client = RequestJournal(self.authority, self.authority.connect(ticket))
                self.assertEqual(json.loads(client.send())['code'], 'ok')
                self.assertEqual(self.count('effects'), before + 1)
                # Next iteration's child clock must not roll back.
                script = script.replace('lambda: 1001', 'lambda: 1002')

    def test_action_expiry_checked_at_use_not_only_at_issue(self):
        grant = self.authority.grant(self.ticket, 'paid-api', 'budget', 2, 'synthetic-human', 1005)
        self.client.prepare(self.effect())
        self.now = 1005
        self.assertEqual(json.loads(self.client.send())['code'], 'not-authorized')
        self.assertEqual(self.count('effects'), 0)
        self.assertEqual(self.lab.db.execute('SELECT remaining FROM grants WHERE id=?', (grant,)).fetchone()[0], 2)
        self.authority.grant(self.ticket, 'paid-api', 'budget', 1, 'synthetic-human', 1010)
        self.client.prepare(self.effect())
        self.assertEqual(json.loads(self.client.send())['code'], 'ok')
        self.assertEqual(self.count('effects'), 1)

    def test_scope_deadline_and_clock_cannot_expand_authority(self):
        for deadline in (None, True, float('nan'), float('inf'), 999, 1101):
            with self.subTest(deadline=deadline), self.assertRaises(Denied):
                self.authority.grant(self.ticket, 'paid-api', 'budget', 1, 'synthetic-human', deadline)
        with self.assertRaises(Denied):
            self.authority.grant(self.ticket, 'paid-api', 'other', 1, 'synthetic-human', 1005)
        self.now = 1003
        self.authority.connect(self.ticket)
        self.now = 1002
        self.lab.close()
        self.lab = Lab(self.path, authority_clock=lambda: self.now)
        self.authority = LaunchAuthority(Broker(self.lab))
        with self.assertRaisesRegex(Denied, 'invalid-authority-clock'):
            self.authority.connect(self.ticket)

    def test_lost_response_restarts_with_exact_request_and_one_effect(self):
        self.authority.grant(self.ticket, 'paid-api', 'budget', 2, 'synthetic-human', 1090)
        self.client.prepare(self.effect())
        original = self.lab.db.execute('SELECT raw FROM client_requests').fetchone()[0]
        dispatch = self.broker.dispatch
        def lose_response(channel, raw):
            dispatch(channel, raw)
            raise OSError('synthetic lost reply')
        with patch.object(self.broker, 'dispatch', lose_response), self.assertRaises(OSError):
            self.client.send()
        self.assertEqual(self.count('effects'), 1)
        self.restart()
        with patch.object(self.broker, 'dispatch', wraps=self.broker.dispatch) as observed:
            self.assertEqual(json.loads(self.client.send())['code'], 'ok')
            self.assertEqual(observed.call_args.args[1], original)
        self.assertEqual(self.count('effects'), 1)
        self.assertEqual(self.count('receipts'), 1)
        self.assertEqual(self.lab.db.execute('SELECT remaining FROM grants').fetchone()[0], 1)

    def test_pending_before_delivery_survives_restart_and_blocks_replacement(self):
        self.client.prepare(self.write())
        with self.assertRaisesRegex(Denied, 'request-already-pending'):
            self.client.prepare(dict(self.write(), text='different'))
        self.restart()
        self.assertEqual(json.loads(self.client.send())['code'], 'ok')
        self.assertEqual(self.count('writes'), 1)

    def test_missing_request_never_reconstructed_even_without_receipt(self):
        self.client.prepare(self.effect())
        with self.lab.transaction():
            self.lab.db.execute('DELETE FROM client_requests')
        self.restart()
        with self.assertRaisesRegex(Denied, 'request-journal-incomplete'):
            self.client.prepare(self.effect())
        self.assertEqual(self.count('effects'), 0)

    def test_missing_or_changed_request_after_acceptance_blocks_recovery(self):
        self.client.prepare(self.write())
        raw = self.lab.db.execute('SELECT raw FROM client_requests').fetchone()[0]
        self.broker.dispatch(self.channel, raw)
        with self.lab.transaction():
            self.lab.db.execute("UPDATE client_requests SET raw=X'00'")
        with self.assertRaisesRegex(Denied, 'request-journal-inconsistent'):
            self.client.send()
        with self.lab.transaction():
            self.lab.db.execute('DELETE FROM client_requests')
        with self.assertRaisesRegex(Denied, 'request-journal-incomplete'):
            self.client.send()
        self.assertEqual(self.count('writes'), 1)

    def test_journal_insert_failure_prevents_delivery(self):
        self.lab.db.execute("CREATE TRIGGER fail_outbox BEFORE INSERT ON client_requests "
                            "BEGIN SELECT RAISE(ABORT, 'synthetic journal unavailable'); END")
        with self.assertRaises(Exception):
            self.client.prepare(self.write())
        self.assertEqual(self.count('writes'), 0)
        self.assertEqual(self.lab.db.execute('SELECT next_id FROM client_cursor').fetchone()[0], 1)

    def test_expired_permit_cannot_finish_previously_accepted_disk_write(self):
        tree = self.root / 'tree'
        tree.mkdir()
        materializer = Materializer(self.lab, tree, {'note': 'note.txt'})
        self.broker.materializer = materializer
        self.client.prepare(self.write())
        with patch.object(materializer, 'apply', side_effect=OSError('synthetic disk unavailable')):
            self.assertEqual(json.loads(self.client.send())['code'], 'materialization-pending')
        self.assertEqual(self.count('writes'), 1)
        self.assertFalse((tree / 'note.txt').exists())
        self.now = 1100
        raw = self.lab.db.execute('SELECT raw FROM client_requests').fetchone()[0]
        self.assertEqual(json.loads(self.broker.dispatch(self.channel, raw))['code'], 'session-no-longer-valid')
        self.assertFalse((tree / 'note.txt').exists())
        self.assertEqual(self.lab.db.execute('SELECT completed FROM client_requests').fetchone()[0], 0)

    def test_removing_pipe_guard_reproduces_unauthorized_write(self):
        # Negative control: pre-launcher broker never rechecked a permit.
        # The same expired operation succeeds if that new guard is removed.
        self.now = 1100
        raw = json.dumps(dict(self.write(), id=1)).encode()
        self.channel.authorize = None
        self.assertEqual(json.loads(self.broker.dispatch(self.channel, raw))['code'], 'ok')
        self.assertEqual(self.count('writes'), 1)

    def test_removing_deadline_record_reproduces_expired_effect(self):
        # Legacy grants have no deadline: this mutation recreates that boundary.
        self.authority.grant(self.ticket, 'paid-api', 'budget', 1, 'synthetic-human', 1005)
        self.now = 1005
        with self.lab.transaction():
            self.lab.db.execute('DELETE FROM grant_deadlines')
        self.client.prepare(self.effect())
        self.assertEqual(json.loads(self.client.send())['code'], 'ok')
        self.assertEqual(self.count('effects'), 1)


if __name__ == '__main__':
    unittest.main()
