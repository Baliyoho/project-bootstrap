"""Synthetic P0 counterexamples; never use a real project or remote."""
from dataclasses import asdict, replace
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest

from project_bootstrap.contracts import Denied, Lab, digest, mask_summary, scan_snapshot
from project_bootstrap.session import HandoffReceipt, Session, rename


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.session = Session('26110621', '重建骨架v2')
        self.receipt = HandoffReceipt('handoff-1', True, True, True, True)

    def test_resume_wait_finish_preserve_identity(self):
        waiting = self.session.transition('wait_for_user')
        self.assertTrue(waiting.title().startswith('※　26110621'))
        done = waiting.transition('handoff', self.receipt)
        resumed = done.transition('message')
        self.assertEqual((resumed.started, resumed.topic, resumed.count),
                         ('26110621', '重建骨架v2', 1))
        self.assertTrue(resumed.title().startswith('㊣　'))

    def test_each_missing_handoff_condition_rejected(self):
        for field in ('final_checks_passed', 'push_succeeded', 'remote_released', 'upstream_aligned'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.session.transition('handoff', replace(self.receipt, **{field: False}))
        with self.assertRaises(ValueError):
            self.session.transition('handoff')
        with self.assertRaises(ValueError):
            self.session.transition('handoff', replace(self.receipt, event_id=''))
        # Callers other than Session (gitclaim) rely on the receipt itself.
        self.assertFalse(replace(self.receipt, event_id='').valid())
        self.assertFalse(replace(self.receipt, push_succeeded=1).valid())

    def test_invalid_session_fields_are_rejected_not_repaired(self):
        for kwargs in ({'started': '2611062'}, {'started': '2611062x'}, {'topic': ''},
                       {'topic': '一二三四五六七八九十十'}, {'topic': '主題｜分隔'},
                       {'topic': '換\n行'}, {'topic': '換\r行'}, {'count': -1}, {'count': '1'},
                       {'state': 'done'}, {'completed': ('a', 'a')}, {'completed': ('',)}):
            values = dict(started='26110621', topic='重建骨架v2')
            values.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Session(**values)
        self.assertEqual(Session('26110621', '一二三四五六七八九十').topic, '一二三四五六七八九十')

    def test_checkpoint_and_title_retry_do_not_increment(self):
        self.assertEqual(self.session.transition('checkpoint').count, 0)
        done = self.session.transition('handoff', self.receipt)
        restored = Session(**json.loads(json.dumps(asdict(done))))
        self.assertEqual(restored.transition('handoff', self.receipt).count, 1)
        self.assertEqual(restored.transition('message').transition(
            'handoff', replace(self.receipt, event_id='second')).count, 2)
        self.assertEqual(done.transition('message').transition('handoff', self.receipt).state, 'working')

    def test_second_handoff_requires_resume_and_new_event(self):
        done = self.session.transition('handoff', self.receipt)
        second = replace(self.receipt, event_id='handoff-2')
        with self.assertRaises(ValueError):
            done.transition('handoff', second)
        self.assertEqual(done.transition('message').transition('handoff', second).count, 2)

    def test_old_lower_bound_is_not_reset(self):
        old = Session.from_title('↗　26110621｜重建骨架v2｜已交棒｜交棒≥2次')
        done = old.transition('message').transition('handoff', self.receipt)
        self.assertTrue(done.title().endswith('交棒≥3次'))
        with self.assertRaises(ValueError):
            Session.from_title('↗　26110621｜重建骨架v2｜已交棒')

    def test_invalid_title_not_silently_repaired(self):
        for title in ('↗　26110621｜重建骨架v2｜工作中｜交棒1次',
                      '㊣　26110621｜重建骨架v2｜工作中｜交棒-1次'):
            with self.subTest(title=title), self.assertRaises(ValueError):
                Session.from_title(title)

    def test_provider_failures_and_normalization(self):
        class Adapter:
            def set_title(self, value):
                self.value = value.replace('　', ' ', 1)
            def get_title(self):
                return self.value
        class Broken(Adapter):
            def get_title(self):
                raise RuntimeError('SYNTHETIC_PRIVATE_EXCEPTION')
        class Mismatch(Adapter):
            def get_title(self):
                return 'stale title'
        self.assertEqual(rename(self.session, Adapter())['status'], 'applied')
        self.assertEqual(rename(self.session, None)['status'], 'unavailable')
        self.assertEqual(rename(self.session, Mismatch())['status'], 'mismatch')
        result = rename(self.session, Broken())
        self.assertEqual(result['status'], 'error')
        self.assertNotIn('SYNTHETIC_PRIVATE_EXCEPTION', str(result))


class LabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='bootstrap-v2-test-')
        self.path = Path(self.temp.name) / 'lab.sqlite'
        self.lab = Lab(self.path, clock=lambda: '2026-11-06T13:00:00+00:00')
        self.a = self.lab.register('session-a')
        self.b = self.lab.register('session-b')

    def tearDown(self):
        self.lab.close()
        self.temp.cleanup()

    def test_write_event_has_same_event_truth_not_joined_fields(self):
        first = self.lab.write(self.a, 'note', None, b'before\nfull content')
        second = self.lab.write(self.b, 'note', digest(b'before\nfull content'), b'after')
        event = self.lab.event(second)
        self.assertEqual((event['actor'], event['before'], event['after'], event['at']),
                         ('session-b', b'before\nfull content', b'after', '2026-11-06T13:00:00+00:00'))
        self.assertNotEqual(first, second)
        self.assertGreater(event['seq'], self.lab.event(first)['seq'])

    def test_invalid_identity_and_stale_base_leave_no_write(self):
        self.lab.write(self.a, 'note', None, b'first')
        for capability, expected in (('session-a', digest(b'first')), (self.b, digest(b'old'))):
            with self.assertRaises(Denied):
                self.lab.write(capability, 'note', expected, b'wrong')
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM writes').fetchone()[0], 1)
        self.assertEqual(self.lab.db.execute('SELECT content FROM files').fetchone()[0], b'first')

    def test_journal_failure_rolls_back_content(self):
        self.lab.write(self.a, 'note', None, b'before')
        self.lab.db.execute("CREATE TRIGGER fail_journal BEFORE INSERT ON writes "
                            "BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.lab.write(self.a, 'note', digest(b'before'), b'after')
        self.assertEqual(self.lab.db.execute('SELECT content FROM files').fetchone()[0], b'before')

    def test_content_failure_rolls_back_journal(self):
        self.lab.db.execute("CREATE TRIGGER fail_content BEFORE INSERT ON files "
                            "BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.lab.write(self.a, 'note', None, b'after')
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM writes').fetchone()[0], 0)

    def test_restart_retains_original_event(self):
        event = self.lab.write(self.a, 'note', None, b'persisted')
        self.lab.close()
        self.lab = Lab(self.path)
        self.assertEqual(self.lab.event(event)['after'], b'persisted')
        self.assertEqual(self.lab.event(event)['actor'], 'session-a')

    def test_running_old_operation_invalidated_and_new_blocked(self):
        ticket = self.lab.begin(self.b, 0)
        self.lab.propose('premise-v1')
        with self.assertRaises(Denied):
            self.lab.complete(self.b, ticket)
        with self.assertRaises(Denied):
            self.lab.begin(self.b, 0)
        with self.assertRaises(Denied):
            self.lab.activate()
        self.assertEqual(self.lab.inbox(self.b)[0]['change'], 'premise-v1')

    def test_all_recipients_application_ack_before_activation(self):
        epoch = self.lab.propose('premise-v1')
        with self.assertRaises(Denied):
            self.lab.acknowledge(self.a, epoch, 'premise-v1')
        with self.assertRaises(Denied):
            self.lab.acknowledge(self.a, epoch, 'wrong', application=True)
        self.lab.acknowledge(self.a, epoch, 'premise-v1', application=True)
        with self.assertRaises(Denied):
            self.lab.activate()
        self.lab.acknowledge(self.b, epoch, 'premise-v1', application=True)
        self.lab.acknowledge(self.b, epoch, 'premise-v1', application=True)
        self.lab.activate()
        with self.assertRaises(Denied):
            self.lab.begin(self.a, 0)
        ticket = self.lab.begin(self.a, 1)
        with self.assertRaises(Denied):
            self.lab.complete(self.b, ticket)
        self.lab.complete(self.a, ticket)
        with self.assertRaises(Denied):
            self.lab.complete(self.a, ticket)

    def test_restart_and_new_line_cannot_lose_pending_notice(self):
        self.lab.propose('premise-v1')
        self.lab.acknowledge(self.a, 1, 'premise-v1', application=True)
        self.lab.close()
        self.lab = Lab(self.path)
        c = self.lab.register('session-c')
        self.assertEqual(self.lab.inbox(c)[0]['acknowledged'], 0)
        self.assertEqual(self.lab.inbox(self.b)[0]['acknowledged'], 0)
        with self.assertRaises(Denied):
            self.lab.activate()

    def test_second_pending_change_does_not_erase_first(self):
        self.lab.propose('first')
        with self.assertRaises(Denied):
            self.lab.propose('second')
        self.assertEqual(self.lab.inbox(self.a)[0]['change'], 'first')

    def test_unapproved_actions_have_zero_effects(self):
        for kind in ('delete', 'rewrite-history', 'force-push', 'batch-data',
                     'schema', 'move-credential', 'extra-model', 'paid-api', 'cloud-resource'):
            with self.subTest(kind=kind), self.assertRaises(Denied):
                self.lab.effect(self.a, kind, 'synthetic-resource')
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM effects').fetchone()[0], 0)

    def test_authorization_is_scoped_counted_and_revocable(self):
        grant = self.lab.grant('session-a', 'extra-model', 'fixture', 2, 'synthetic-subscription')
        for capability, kind, resource in ((self.b, 'extra-model', 'fixture'),
                (self.a, 'paid-api', 'fixture'), (self.a, 'extra-model', 'other')):
            with self.assertRaises(Denied):
                self.lab.effect(capability, kind, resource)
        self.lab.effect(self.a, 'extra-model', 'fixture')
        self.lab.revoke(grant)
        with self.assertRaises(Denied):
            self.lab.effect(self.a, 'extra-model', 'fixture')
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM effects').fetchone()[0], 1)

    def test_spent_authorization_cannot_be_reused_after_restart(self):
        self.lab.grant('session-a', 'paid-api', 'fixture', 1, 'synthetic-budget')
        self.lab.effect(self.a, 'paid-api', 'fixture')
        self.lab.close()
        self.lab = Lab(self.path)
        with self.assertRaises(Denied):
            self.lab.effect(self.a, 'paid-api', 'fixture')


class ScanTests(unittest.TestCase):
    def test_all_candidates_checked_before_git_object_creation(self):
        with tempfile.TemporaryDirectory(prefix='bootstrap-v2-git-') as directory:
            subprocess.run(['git', 'init', '-q', directory], check=True)
            objects = Path(directory) / '.git' / 'objects'
            before = sorted(str(path.relative_to(objects)) for path in objects.rglob('*'))
            secret = b'SYNTHETIC_BLOCKED_VALUE'
            with self.assertRaises(Denied):
                snapshot = scan_snapshot({'a.txt': b'clean', 'z.txt': secret}, 'safe', (secret,))
                for _, content in snapshot:
                    subprocess.run(['git', '-C', directory, 'hash-object', '-w', '--stdin'],
                                   input=content, check=True, capture_output=True)
            self.assertEqual(before, sorted(str(path.relative_to(objects)) for path in objects.rglob('*')))
            self.assertFalse((Path(directory) / '.git' / 'index').exists())

    def test_path_message_and_missing_policy_rejected(self):
        forbidden = (b'SYNTHETIC_PRIVATE',)
        for files, message, policy in (({'SYNTHETIC_PRIVATE.txt': b'clean'}, 'safe', forbidden),
                ({'safe': b'clean'}, 'SYNTHETIC_PRIVATE', forbidden),
                ({'../escape': b'clean'}, 'safe', forbidden),
                ({'safe': b'clean'}, 'safe', ())):
            with self.subTest(files=files), self.assertRaises(Denied):
                scan_snapshot(files, message, policy)

    def test_frozen_snapshot_not_mutable_file_used_after_scan(self):
        source = bytearray(b'clean')
        files = {'note': source}
        snapshot = scan_snapshot(files, 'safe', (b'SYNTHETIC_PRIVATE',))
        source[:] = b'SYNTHETIC_PRIVATE'
        files['note'] = source
        self.assertEqual(snapshot, (('note', b'clean'),))

    def test_mask_before_truncate_and_multiline(self):
        secret = b'SYNTHETIC\nPRIVATE'
        for limit in (200, 300):
            result = mask_summary(b'x' * (limit - 4) + secret, (secret,), limit)
            self.assertNotIn(b'SYNT', result)
            self.assertTrue(result.endswith(b'***'))


if __name__ == '__main__':
    unittest.main()
