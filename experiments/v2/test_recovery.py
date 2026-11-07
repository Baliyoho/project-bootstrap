import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

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


if __name__ == '__main__':
    unittest.main()
