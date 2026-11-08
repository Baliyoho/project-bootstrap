"""Single confined worker integrating the premise barrier and durable outbox."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import platform
import queue
import subprocess
import tempfile
import threading
import time

from experiments.v2.broker import Broker
from experiments.v2.broker_fixture import sandbox_plan
from experiments.v2.contracts import Denied, Lab
from experiments.v2.launcher import LaunchAuthority, RequestJournal
from experiments.v2.lifecycle import ProcessLauncher, TicketVault
from experiments.v2.materializer import Materializer
from experiments.v2.supervisor import WORK_PROTOCOL


PROGRAM = '''import hashlib, json, sys
epoch, context_bytes = json.loads(sys.stdin.readline())
''' + WORK_PROTOCOL


class ManagedFixture:
    """Trusted parent event loop. Only the fixed worker can use this pipe."""
    def __init__(self, launcher, handle, plan):
        self.launcher, self.lab = launcher, launcher.lab
        self.handle, self.plan = handle, plan
        self.child = self.pending = None
        self.epoch = 0
        self.ready = False
        self.lab.db.execute('''CREATE TABLE IF NOT EXISTS managed_initial_context (
            actor TEXT PRIMARY KEY, context TEXT NOT NULL)''')

    def receive(self):
        result = queue.Queue(maxsize=1)
        child = self.child

        def read():
            try:
                result.put(child.process.stdout.readline(1025))
            except OSError:
                result.put(b'')

        child.reader.join(timeout=self.launcher.timeout)
        if child.reader.is_alive():
            raise Denied('previous-reader-still-running')
        child.reader = threading.Thread(target=read, daemon=True)
        child.reader.start()
        deadline = time.monotonic() + self.launcher.timeout
        while True:
            self.launcher.check()
            try:
                raw = result.get(timeout=0.05)
                break
            except queue.Empty:
                if time.monotonic() >= deadline:
                    raise Denied('worker-timeout') from None
        if not raw.endswith(b'\n') or len(raw) > 1024:
            raise Denied('invalid-worker-message')
        try:
            message = json.loads(raw)
        except (ValueError, RecursionError):
            raise Denied('invalid-worker-message') from None
        self.launcher.check()
        return message

    def exchange(self, payload):
        self.launcher.check()
        try:
            self.child.process.stdin.write(json.dumps(payload).encode() + b'\n')
            self.child.process.stdin.flush()
        except (OSError, ValueError):
            raise Denied('worker-unavailable') from None
        return self.receive()

    def load(self, epoch, context):
        self.child = self.launcher.start(self.handle, self.plan)
        reply = self.exchange([epoch, context])
        if reply != {'type': 'ready', 'epoch': epoch,
                     'context_digest': hashlib.sha256(context.encode()).hexdigest()}:
            raise Denied('worker-context-not-confirmed')

    def start(self, factor):
        context = self.context(factor)
        ticket = self.launcher.ticket(self.handle)
        authority = self.launcher.authority
        with self.lab.transaction():
            self.lab.require_epoch(0)
            actor = authority.permit(authority.ticket_hash(ticket))['actor']
            if self.lab.db.execute('SELECT 1 FROM managed_initial_context UNION ALL '
                                   'SELECT 1 FROM managed_launches LIMIT 1').fetchone():
                raise Denied('already-started')
            self.lab.db.execute('INSERT INTO managed_initial_context VALUES (?, ?)', (actor, context))
        try:
            self.load(0, context)
        except BaseException:
            self.close()
            raise
        self.ready = True

    @staticmethod
    def context(factor):
        if type(factor) is not int or abs(factor) > 1000:
            raise Denied('invalid-fixture-factor')
        return json.dumps({'factor': factor}, separators=(',', ':'))

    def change(self, factor):
        if not self.ready:
            raise Denied('managed-fixture-not-ready')
        context = self.context(factor)
        self.ready = False
        try:
            # Commit the notice and close the use barrier before asking the
            # guardian to stop. If any step fails the change stays pending.
            epoch = self.lab.propose(context)
            actor = self.lab.actor(self.child.channel.capability)
            self.launcher.stop(actor)
            self.pending = None
            self.activate(epoch, context)
        except BaseException:
            self.close()
            raise

    def resume(self):
        """Rebuild only from a verified stop and the original durable context."""
        if self.child is not None:
            raise Denied('already-started')
        try:
            actor = self.launcher.reconcile(self.handle, self.plan)
            with self.lab.transaction():
                epoch, context, pending = self.recovery_context(actor)
                # A replacement cannot complete an interrupted computation
                # even when the premise itself did not change.
                self.lab.db.execute("UPDATE operations SET status='invalid' WHERE actor=? AND status='running'",
                                    (actor,))
            if pending:
                self.activate(epoch, context)
            else:
                self.load(epoch, context)
                self.epoch, self.ready = epoch, True
        except BaseException:
            self.close()
            raise

    def recovery_context(self, actor):
        state = self.lab.db.execute('SELECT epoch, pending, change FROM state').fetchone()
        pending = state['pending'] is not None
        epoch = state['pending'] if pending else state['epoch']
        if pending and (type(epoch) is not int or epoch != state['epoch'] + 1):
            raise Denied('invalid-pending-epoch')
        row = self.lab.db.execute('SELECT context FROM managed_initial_context WHERE actor=?', (actor,)).fetchone()
        if row is not None and epoch != 0:
            row = self.lab.db.execute('SELECT change FROM notices WHERE actor=? AND epoch=? AND acknowledged=?',
                                      (actor, epoch, int(not pending))).fetchone()
        if row is None or (pending and row[0] != state['change']):
            raise Denied('missing-or-inconsistent-context')
        context = row[0]
        try:
            fields = json.loads(context)
            if self.context(fields['factor']) != context:
                raise ValueError
        except (Denied, KeyError, TypeError, ValueError, RecursionError):
            raise Denied('invalid-durable-context') from None
        return epoch, context, pending

    def activate(self, epoch, context):
        self.load(epoch, context)
        self.launcher.check()
        with self.lab.transaction():
            self.lab.acknowledge(self.child.channel.capability, epoch, context, application=True)
            self.lab.activate()
        self.epoch, self.ready = epoch, True

    def begin(self, value):
        if not self.ready or self.pending is not None:
            raise Denied('managed-fixture-not-ready')
        if type(value) is not int or abs(value) > 1000:
            raise Denied('invalid-fixture-value')
        try:
            self.launcher.check()
            ticket = self.lab.begin(self.child.channel.capability, self.epoch)
            if self.exchange({'type': 'begin', 'value': value}) != {'type': 'started', 'epoch': self.epoch}:
                raise Denied('work-not-started')
        except BaseException:
            self.close()
            raise
        self.pending = ticket
        return ticket

    def stage_result(self, base=None):
        if not self.ready or self.pending is None:
            raise Denied('no-current-work')
        try:
            result = self.exchange({'type': 'finish'})
            if (not isinstance(result, dict) or result.get('type') != 'result'
                    or result.get('epoch') != self.epoch or type(result.get('value')) is not int):
                raise Denied('wrong-worker-result')
            journal = self.outbox()
            with self.launcher.broker.lock, self.lab.transaction():
                self.lab.complete(self.child.channel.capability, self.pending)
                request_id = journal.prepare({
                    'method': 'write', 'resource': 'note', 'base': base,
                    'text': str(result['value']), 'epoch': self.epoch})
        except BaseException:
            self.close()
            raise
        self.pending = None
        return request_id

    def outbox(self):
        self.launcher.check()
        return RequestJournal(self.launcher.authority, self.child.channel)

    def send(self):
        if not self.ready:
            raise Denied('managed-fixture-not-ready')
        # Parent-only recovery. Historical receipts are never sent to the new
        # worker or presented as a result computed under its new premise.
        return json.loads(self.outbox().send())

    def close(self):
        self.ready = False
        self.launcher.close()


def supported():
    return platform.system() == 'Darwin' and Path('/usr/bin/sandbox-exec').is_file()


@contextmanager
def open_managed(root, handle=None):
    repo, scratch, tickets = (root / name for name in ('repo', 'scratch', 'tickets'))
    if handle is None:
        for path in (repo, scratch, tickets):
            path.mkdir(mode=0o700)
    vault = TicketVault(tickets)
    try:
        lab = Lab(root / 'private.sqlite')
        try:
            materializer = Materializer(lab, repo, {'note': 'managed.txt'})
            broker = Broker(lab, materializer)
            authority = LaunchAuthority(broker)
            if handle is None:
                handle = vault.save(authority.issue(('note',), 'synthetic-parent-approval', time.time() + 60))
            launcher = ProcessLauncher(authority, vault)
            fixture = ManagedFixture(launcher, handle, sandbox_plan(repo, scratch, PROGRAM))
            try:
                yield fixture, repo
            finally:
                fixture.close()
        finally:
            lab.close()
    finally:
        vault.close()


@contextmanager
def managed_environment():
    with tempfile.TemporaryDirectory(prefix='bootstrap-v2-managed-') as directory:
        with open_managed(Path(directory).resolve()) as fixture:
            yield fixture


def probe_managed():
    if not supported():
        return {'result': '未驗證', 'reason': '受管執行探針限 macOS'}
    try:
        with managed_environment() as (fixture, repo):
            lab = fixture.lab
            fixture.start(2)
            old = fixture.child
            fixture.begin(7)
            stale_id = fixture.stage_result()
            interrupted = fixture.begin(8)
            fixture.change(3)
            actor = lab.actor(fixture.child.channel.capability)
            old_status = lab.db.execute('SELECT status FROM operations WHERE ticket=?',
                                        (interrupted,)).fetchone()[0]
            stale = fixture.send()
            absent_before_write = not (repo / 'managed.txt').exists()
            fixture.begin(7)
            fresh_id = fixture.stage_result()
            fresh = fixture.send()
            requests = list(lab.db.execute(
                'SELECT raw, completed FROM client_requests WHERE actor=? ORDER BY request_id', (actor,)))
            events = list(lab.db.execute('SELECT writes.actor, writes.after, write_epochs.epoch '
                                         'FROM writes JOIN write_epochs USING(event)'))
            checks = {
                'old_worker_reaped': old.reaped and old.process.poll() is not None and old.channel.closed,
                'old_work_invalidated': old_status == 'invalid',
                'new_context_acknowledged': fixture.epoch == 1
                    and lab.inbox(fixture.child.channel.capability)[-1]['acknowledged'] == 1,
                'stale_request_denied': stale == {'id': stale_id, 'code': 'premise-not-current'}
                    and absent_before_write,
                'exact_requests_retained': len(requests) == 2 and all(row['completed'] for row in requests)
                    and [(json.loads(row['raw'])['epoch'], json.loads(row['raw'])['text'])
                         for row in requests] == [(0, '14'), (1, '21')],
                'only_fresh_content_applied': fresh.get('id') == fresh_id and fresh.get('code') == 'ok'
                    and [tuple(event) for event in events] == [(actor, b'21', 1)]
                    and (repo / 'managed.txt').read_bytes() == b'21',
            }
    except (Denied, OSError, subprocess.TimeoutExpired) as error:
        return {'result': '不通過', 'reason': str(error) if isinstance(error, Denied) else type(error).__name__}
    return {'result': '通過' if all(checks.values()) else '不通過', 'checks': checks,
            'scope': 'macOS 單 worker；舊工作失效、監護回收、載入新前提、outbox 拒絕舊寫入並套用新結果',
            'unknown': '回收證據缺失、多程序樹、一般工具或跨機通知未驗收；重啟另見合成 SIGKILL 測試'}
