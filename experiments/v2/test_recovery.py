import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from experiments.v2.broker import Broker
from experiments.v2.contracts import Denied, Lab, digest
from experiments.v2.materializer import Materializer, supported


ROOT = Path(__file__).resolve().parents[2]
REQUEST = json.dumps(dict(id=1, method='write', resource='note', base=digest(b'before'),
                          text='after', epoch=0)).encode()
CRASH_WORKER = '''import json, os, pathlib, sys
from experiments.v2.broker import Broker
from experiments.v2.contracts import Lab
from experiments.v2.materializer import Materializer
db, root, crash = sys.argv[1:]
lab = Lab(db)
def fault(stage, event):
    if stage == crash:
        os._exit(73)
materializer = Materializer(lab, root, {'note':'nested/note.txt'}, fault=fault)
broker = Broker(lab, materializer)
channel = broker.attach('line-a', ('note',), resume=True)
response = broker.dispatch(channel, sys.stdin.buffer.read())
raise RuntimeError('expected crash point was not reached')
'''


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='bootstrap-v2-recovery-')
        self.root = Path(self.temp.name)
        self.tree = self.root / 'tree'
        (self.tree / 'nested').mkdir(parents=True)
        self.file = self.tree / 'nested/note.txt'
        self.file.write_bytes(b'before')
        self.file.chmod(0o751)
        self.path = self.root / 'private.sqlite'
        self.lab = Lab(self.path)

    def tearDown(self):
        self.lab.close()
        self.temp.cleanup()

    def setup_broker(self, fault=None):
        materializer = Materializer(self.lab, self.tree, {'note': 'nested/note.txt'}, fault=fault)
        materializer.seed('note')
        broker = Broker(self.lab, materializer)
        return broker, broker.attach('line-a', ('note',)), materializer

    def test_process_death_at_each_disk_boundary_recovers_exactly_once(self):
        if not supported():
            self.assertRaises(Exception, Materializer, self.lab, self.tree, {})
            return
        for stage in ('after_prepare', 'after_stage_sync', 'after_replace', 'after_commit'):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory(prefix='bootstrap-v2-crash-') as directory:
                root = Path(directory)
                (root / 'tree/nested').mkdir(parents=True)
                file = root / 'tree/nested/note.txt'
                file.write_bytes(b'before')
                file.chmod(0o751)
                path = root / 'private.sqlite'
                lab = Lab(path)
                materializer = Materializer(lab, root / 'tree', {'note': 'nested/note.txt'})
                materializer.seed('note')
                lab.register('line-a')
                lab.close()
                child = subprocess.run([sys.executable, '-B', '-c', CRASH_WORKER,
                    str(path), str(root / 'tree'), stage], input=REQUEST, cwd=ROOT,
                    capture_output=True, timeout=15,
                    env={'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1'})
                self.assertEqual(child.returncode, 73, 'child must reach the intended crash boundary')
                self.assertEqual(file.read_bytes(), b'before' if stage in ('after_prepare', 'after_stage_sync') else b'after')
                lab = Lab(path)
                try:
                    broker = Broker(lab, Materializer(lab, root / 'tree', {'note': 'nested/note.txt'}))
                    channel = broker.attach('line-a', ('note',), resume=True)
                    result = json.loads(broker.dispatch(channel, REQUEST))
                    self.assertEqual(result['code'], 'ok')
                    self.assertEqual(file.read_bytes(), b'after')
                    self.assertEqual(file.stat().st_mode & 0o777, 0o751)
                    self.assertEqual(lab.db.execute('SELECT count(*) FROM writes').fetchone()[0], 1)
                    self.assertEqual(lab.db.execute('SELECT count(*) FROM receipts').fetchone()[0], 1)
                    self.assertEqual(lab.db.execute('SELECT phase FROM materializations').fetchone()[0], 'applied')
                    self.assertEqual(list((root / 'tree/nested').glob('.bootstrap-*.tmp')), [])
                    later = json.loads(REQUEST)
                    later.update(id=2, base=digest(b'after'), text='later')
                    self.assertEqual(json.loads(broker.dispatch(channel, json.dumps(later).encode()))['code'], 'ok')
                    self.assertEqual(json.loads(broker.dispatch(channel, REQUEST)), result)
                    self.assertEqual(file.read_bytes(), b'later', 'replaying an older receipt must not restore old content')
                finally:
                    lab.close()

    def test_receipt_failure_rolls_back_content_and_event(self):
        broker = Broker(self.lab)
        channel = broker.attach('line-a', ('note',))
        self.lab.db.execute("CREATE TRIGGER fail_receipt BEFORE INSERT ON receipts "
                            "BEGIN SELECT RAISE(ABORT, 'receipt unavailable'); END")
        request = json.loads(REQUEST)
        request['base'] = None
        result = json.loads(broker.dispatch(channel, json.dumps(request).encode()))
        self.assertEqual(result['code'], 'broker-error-channel-closed')
        for table in ('files', 'writes', 'write_epochs', 'receipts'):
            self.assertEqual(self.lab.db.execute('SELECT count(*) FROM ' + table).fetchone()[0], 0)

    def test_failed_commit_does_not_leave_a_transaction_to_commit_later(self):
        broker = Broker(self.lab)
        channel = broker.attach('line-a', ('note',))
        connection = self.lab.db
        class CommitFailure:
            def __getattr__(self, name):
                return getattr(connection, name)
            def commit(self):
                raise OSError('synthetic commit failure')
        self.lab.db = CommitFailure()
        request = json.loads(REQUEST)
        request['base'] = None
        result = json.loads(broker.dispatch(channel, json.dumps(request).encode()))
        self.assertEqual(result['code'], 'broker-error-channel-closed')
        self.assertFalse(connection.in_transaction)
        self.assertEqual(connection.execute('SELECT count(*) FROM writes').fetchone()[0], 0)
        self.lab.db = connection

    def test_effect_receipt_lost_response_and_restart_do_not_double_charge(self):
        broker = Broker(self.lab)
        channel = broker.attach('line-a', ('budget',))
        self.lab.grant('line-a', 'paid-api', 'budget', 2, 'synthetic-human-authorization')
        request = json.dumps(dict(id=1, method='effect', resource='budget', kind='paid-api', epoch=0)).encode()
        response = broker.dispatch(channel, request)  # Simulate response lost after durable commit.
        self.lab.close()
        self.lab = Lab(self.path)
        resumed = Broker(self.lab)
        new_channel = resumed.attach('line-a', ('budget',), resume=True)
        self.assertEqual(resumed.dispatch(new_channel, request), response)
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM effects').fetchone()[0], 1)
        self.assertEqual(self.lab.db.execute('SELECT remaining FROM grants').fetchone()[0], 1)
        changed = json.loads(request)
        changed['kind'] = 'extra-model'
        self.assertEqual(json.loads(resumed.dispatch(new_channel, json.dumps(changed).encode()))['code'], 'changed-retry')

    def test_resuming_principal_invalidates_old_capability(self):
        broker = Broker(self.lab)
        old = broker.attach('line-a', ('note',))
        broker.attach('line-a', ('note',), resume=True)
        self.assertEqual(json.loads(broker.dispatch(old, REQUEST))['code'], 'session-no-longer-valid')

    def test_retry_cannot_materialize_resource_removed_on_resume(self):
        if not supported():
            return
        def pause(stage, event):
            if stage == 'after_prepare':
                raise OSError('synthetic interruption')
        broker, channel, _ = self.setup_broker(fault=pause)
        pending = json.loads(broker.dispatch(channel, REQUEST))
        self.assertEqual(pending['code'], 'materialization-pending')
        self.lab.close()
        self.lab = Lab(self.path)
        resumed = Broker(self.lab, Materializer(self.lab, self.tree, {'note': 'nested/note.txt'}))
        restricted = resumed.attach('line-a', (), resume=True)
        result = json.loads(resumed.dispatch(restricted, REQUEST))
        self.assertEqual(result['code'], 'resource-not-authorized')
        self.assertEqual(self.file.read_bytes(), b'before')
        self.assertEqual(self.lab.db.execute('SELECT phase FROM materializations').fetchone()[0], 'prepared')
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM receipts').fetchone()[0], 1)
        restored = resumed.attach('line-a', ('note',), resume=True)
        self.assertEqual(json.loads(resumed.dispatch(restored, REQUEST))['code'], 'ok')
        self.assertEqual(self.file.read_bytes(), b'after')
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM writes').fetchone()[0], 1)

    def test_recovery_rejects_changed_mapping_or_root(self):
        if not supported():
            return
        def pause(stage, event):
            if stage == 'after_prepare':
                raise OSError('synthetic interruption')
        broker, channel, _ = self.setup_broker(fault=pause)
        self.assertEqual(json.loads(broker.dispatch(channel, REQUEST))['code'], 'materialization-pending')
        alternate = self.tree / 'nested/other.txt'
        alternate.write_bytes(b'before')
        alternate.chmod(0o751)
        other_root = self.root / 'other-tree'
        (other_root / 'nested').mkdir(parents=True)
        other_file = other_root / 'nested/note.txt'
        other_file.write_bytes(b'before')
        other_file.chmod(0o751)
        self.lab.close()
        self.lab = Lab(self.path)
        for root, mapping in ((self.tree, {'note': 'nested/other.txt'}),
                              (other_root, {'note': 'nested/note.txt'})):
            with self.subTest(root=root, mapping=mapping):
                with self.assertRaisesRegex(Denied, 'materializer-binding-conflict'):
                    Materializer(self.lab, root, mapping)
        self.assertEqual(self.file.read_bytes(), b'before')
        self.assertEqual(alternate.read_bytes(), b'before')
        self.assertEqual(other_file.read_bytes(), b'before')
        resumed = Broker(self.lab, Materializer(self.lab, self.tree, {'note': 'nested/note.txt'}))
        channel = resumed.attach('line-a', ('note',), resume=True)
        self.assertEqual(json.loads(resumed.dispatch(channel, REQUEST))['code'], 'ok')
        self.assertEqual(self.file.read_bytes(), b'after')

    def test_unbound_existing_journal_is_not_adopted(self):
        if not supported():
            return
        capability = self.lab.register('line-a')
        self.lab.write(capability, 'note', None, b'after', epoch=0)
        with self.assertRaisesRegex(Denied, 'missing-materializer-binding'):
            Materializer(self.lab, self.tree, {'note': 'nested/note.txt'})
        self.assertEqual(self.file.read_bytes(), b'before')
        self.assertFalse(self.lab.db.in_transaction)

    def test_root_replacement_after_attachment_is_rejected(self):
        if not supported():
            return
        broker, channel, _ = self.setup_broker()
        original = self.root / 'original-tree'
        self.tree.rename(original)
        (self.tree / 'nested').mkdir(parents=True)
        self.file.write_bytes(b'before')
        self.file.chmod(0o751)
        result = json.loads(broker.dispatch(channel, REQUEST))
        self.assertEqual(result['code'], 'materialization-pending')
        self.assertEqual(result['reason'], 'materializer-binding-conflict')
        self.assertEqual(self.file.read_bytes(), b'before')
        self.assertEqual((original / 'nested/note.txt').read_bytes(), b'before')

    def test_recovered_replace_requires_directory_sync_before_applied(self):
        if not supported():
            return
        def pause(stage, event):
            if stage == 'after_replace':
                raise OSError('synthetic interruption')
        broker, channel, materializer = self.setup_broker(fault=pause)
        self.assertEqual(json.loads(broker.dispatch(channel, REQUEST))['code'], 'materialization-pending')
        self.assertEqual(self.file.read_bytes(), b'after')
        materializer.fault = lambda stage, event: None
        with patch('experiments.v2.materializer.os.fsync', side_effect=OSError('synthetic fsync failure')):
            self.assertEqual(json.loads(broker.dispatch(channel, REQUEST))['code'], 'materialization-pending')
        self.assertEqual(self.lab.db.execute('SELECT phase FROM materializations').fetchone()[0], 'prepared')
        self.assertEqual(json.loads(broker.dispatch(channel, REQUEST))['code'], 'ok')

    def test_process_death_before_receipt_commit_rolls_back_effect(self):
        self.lab.register('line-a')
        self.lab.grant('line-a', 'paid-api', 'budget', 2, 'synthetic-human-authorization')
        self.lab.close()
        script = '''import os, sys
from experiments.v2.broker import Broker
from experiments.v2.contracts import Lab
lab = Lab(sys.argv[1])
broker = Broker(lab)
channel = broker.attach('line-a', ('budget',), resume=True)
original = lab.effect
def crash(*args, **kwargs):
    original(*args, **kwargs)
    os._exit(74)
lab.effect = crash
broker.dispatch(channel, sys.stdin.buffer.read())
'''
        request = json.dumps(dict(id=1, method='effect', resource='budget', kind='paid-api', epoch=0)).encode()
        child = subprocess.run([sys.executable, '-B', '-c', script, str(self.path)],
            input=request, cwd=ROOT, capture_output=True, timeout=15,
            env={'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.lab = Lab(self.path)
        self.assertEqual(child.returncode, 74)
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM effects').fetchone()[0], 0)
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM receipts').fetchone()[0], 0)
        self.assertEqual(self.lab.db.execute('SELECT remaining FROM grants').fetchone()[0], 2)
        broker = Broker(self.lab)
        channel = broker.attach('line-a', ('budget',), resume=True)
        self.assertEqual(json.loads(broker.dispatch(channel, request))['code'], 'ok')
        self.assertEqual(self.lab.db.execute('SELECT remaining FROM grants').fetchone()[0], 1)

    def test_conflict_after_preparation_never_overwrites_external_content(self):
        if not supported():
            return
        def external_edit(stage, event):
            if stage == 'after_prepare':
                self.file.write_bytes(b'external')
        broker, channel, _ = self.setup_broker(fault=external_edit)
        result = json.loads(broker.dispatch(channel, REQUEST))
        self.assertEqual(result['code'], 'materialization-pending')
        self.assertEqual(self.file.read_bytes(), b'external')
        later = json.loads(REQUEST)
        later.update(id=2, base=digest(b'after'), text='second')
        self.assertEqual(json.loads(broker.dispatch(channel, json.dumps(later).encode()))['code'],
                         'previous-materialization-pending')

    def test_symlink_hardlink_and_parent_escape_refused(self):
        if not supported():
            return
        outside = self.root / 'outside'
        outside.write_bytes(b'outside')
        materializer = Materializer(self.lab, self.tree, {'note': 'nested/note.txt'})
        self.file.unlink()
        self.file.symlink_to(outside)
        with self.assertRaises(OSError):
            materializer.seed('note')
        self.file.unlink()
        os.link(outside, self.file)
        with self.assertRaises(Exception):
            materializer.seed('note')
        self.assertEqual(outside.read_bytes(), b'outside')
        with self.assertRaises(Exception):
            Materializer(self.lab, self.tree, {'escape': '../outside'})
        with self.assertRaises(Exception):
            Materializer(self.lab, self.tree, {'git': '.git/config'})
        with self.assertRaises(Denied):
            Materializer(self.lab, self.tree, {'git': '.GIT/config'})
        with self.assertRaisesRegex(Denied, 'aliased-resources'):
            Materializer(self.lab, self.tree, {'one': 'nested/note.txt', 'two': 'nested/NOTE.txt'})
        self.file.unlink()
        (self.tree / 'nested').rmdir()
        (self.tree / 'nested').symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(OSError):
            materializer.seed('note')

    def test_epoch_change_after_preparation_blocks_disk_write(self):
        if not supported():
            return
        def change_epoch(stage, event):
            if stage == 'after_prepare':
                self.lab.propose('changed')
        broker, channel, _ = self.setup_broker(fault=change_epoch)
        self.assertEqual(json.loads(broker.dispatch(channel, REQUEST))['code'], 'materialization-pending')
        self.assertEqual(self.file.read_bytes(), b'before')
        self.assertEqual(self.lab.db.execute('SELECT phase FROM materializations').fetchone()[0], 'prepared')

    def test_unknown_recovery_phase_is_not_guessed(self):
        if not supported():
            return
        def pause(stage, event):
            if stage == 'after_prepare':
                raise OSError('synthetic interruption')
        broker, channel, materializer = self.setup_broker(fault=pause)
        response = json.loads(broker.dispatch(channel, REQUEST))
        with self.lab.transaction():
            self.lab.db.execute("UPDATE materializations SET phase='unknown'")
        with self.assertRaisesRegex(Denied, 'invalid-materialization-state'):
            materializer.apply(response['event'])
        self.assertEqual(self.file.read_bytes(), b'before')


class MaterializerGuardTests(unittest.TestCase):
    """Each materializer guard on its own, with the exact refusal code."""
    setUp, tearDown, setup_broker = (RecoveryTests.setUp, RecoveryTests.tearDown,
                                     RecoveryTests.setup_broker)

    def denied(self, code, call, *args):
        with self.assertRaises(Denied) as caught:
            call(*args)
        self.assertEqual(str(caught.exception), code)

    def accepted(self, fault=None):
        """A write the broker accepted but whose disk application is still pending."""
        def stop(stage, event):
            if stage == 'after_prepare' and not self.stopped:
                self.stopped = True
                raise OSError('synthetic pause')
            if fault:
                fault(stage, event)
        self.stopped = False
        broker, channel, materializer = self.setup_broker(fault=stop)
        response = json.loads(broker.dispatch(channel, REQUEST))
        self.assertEqual(response['code'], 'materialization-pending')
        return materializer, response['event']

    def test_mapping_inputs(self):
        if not supported():
            return
        for mapping in ({'a': 'nested/./note.txt'}, {'a': 'nested/../note.txt'}, {'a': '.git/x'},
                        {'a': 'nested/.bootstrap-x.tmp'}, {'a': ''}):
            with self.subTest(mapping=mapping):
                self.denied('unsafe-resource-mapping', Materializer, self.lab, self.tree, mapping)
        for mapping in ({'': 'nested/note.txt'}, {5: 'nested/note.txt'}):
            with self.subTest(mapping=mapping):
                self.denied('invalid-resource-id', Materializer, self.lab, self.tree, mapping)

    def test_seed_reads_once_and_refuses_unmapped_or_special_files(self):
        if not supported():
            return
        materializer = Materializer(self.lab, self.tree, {'note': 'nested/note.txt'})
        self.denied('unmapped-resource', materializer.seed, 'other')
        self.file.chmod(0o4755)
        self.denied('unsupported-file-size-or-mode', materializer.seed, 'note')
        self.file.chmod(0o751)
        materializer.seed('note')
        self.denied('resource-already-initialized', materializer.seed, 'note')

    def test_event_identity_evidence_and_state_are_checked(self):
        if not supported():
            return
        materializer, event = self.accepted()
        self.denied('invalid-event', materializer.apply, 'not-an-event')
        with self.lab.transaction():
            self.lab.db.execute('DELETE FROM write_epochs')
        self.denied('missing-materialization-evidence', materializer.apply, event)
        self.assertEqual(self.file.read_bytes(), b'before')

    def test_state_for_another_resource_is_not_applied(self):
        if not supported():
            return
        materializer, event = self.accepted()
        with self.lab.transaction():
            self.lab.db.execute("UPDATE materializations SET resource='elsewhere'")
        self.denied('invalid-materialization-state', materializer.apply, event)
        self.assertEqual(self.file.read_bytes(), b'before')

    def test_prepare_checks_epoch_size_and_disk_base_before_recording_intent(self):
        if not supported():
            return
        materializer, event = self.accepted()
        with self.lab.transaction():
            self.lab.db.execute('DELETE FROM materializations')
        self.lab.propose('changed')
        self.denied('premise-not-current', materializer.apply, event)
        self.assertIsNone(self.lab.db.execute('SELECT 1 FROM materializations').fetchone())

    def test_oversized_event_and_changed_base_record_no_intent(self):
        if not supported():
            return
        materializer, event = self.accepted()
        with self.lab.transaction():
            self.lab.db.execute('DELETE FROM materializations')
        self.file.write_bytes(b'changed outside')
        self.denied('disk-base-conflict', materializer.apply, event)
        self.assertIsNone(self.lab.db.execute('SELECT 1 FROM materializations').fetchone())
        self.file.write_bytes(b'before')
        with patch('experiments.v2.materializer.MAX_CONTENT', 2):
            self.denied('content-too-large', materializer.apply, event)
        self.assertIsNone(self.lab.db.execute('SELECT 1 FROM materializations').fetchone())

    def test_mode_change_unsafe_stage_and_late_edit_are_conflicts(self):
        if not supported():
            return
        materializer, event = self.accepted()
        self.file.chmod(0o700)
        self.denied('disk-base-conflict', materializer.apply, event)
        stage = self.tree / 'nested' / ('.bootstrap-' + event + '.tmp')
        self.assertFalse(stage.exists())  # refused before any staging write
        self.file.chmod(0o751)
        stage.write_bytes(b'')
        os.link(stage, self.root / 'second-name')
        self.denied('unsafe-stage-file', materializer.apply, event)
        stage.unlink()
        def late_edit(name, ev):
            if name == 'after_stage_sync':
                self.file.write_bytes(b'late edit')
        materializer.fault = late_edit
        self.denied('disk-base-conflict', materializer.apply, event)
        self.assertEqual(self.file.read_bytes(), b'late edit')


if __name__ == '__main__':
    unittest.main()
