"""Disposable synthetic workers: abort, rebuild context, then activate epoch.

This proves a controllable-process protocol, not that an arbitrary model or
desktop App received/understood a changed premise. Only the fixed worker below
is launched; no external model or untrusted program is accepted.
"""
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tempfile

from project_bootstrap.contracts import Denied, Lab


WORK_PROTOCOL = '''
fingerprint = hashlib.sha256(context_bytes.encode()).hexdigest()
context = json.loads(context_bytes)
print(json.dumps({'type':'ready', 'epoch':epoch, 'context_digest':fingerprint}), flush=True)
pending = None
for line in sys.stdin:
    message = json.loads(line)
    if message['type'] == 'begin':
        pending = message['value']
        print(json.dumps({'type':'started', 'epoch':epoch}), flush=True)
    elif message['type'] == 'finish' and pending is not None:
        print(json.dumps({'type':'result', 'epoch':epoch, 'value':pending * context['factor']}), flush=True)
        pending = None
    else:
        raise RuntimeError('invalid worker message')
'''

WORKER = '''import hashlib, json, sys
epoch = int(sys.argv[1])
context_bytes = sys.argv[2]
''' + WORK_PROTOCOL


class Worker:
    def __init__(self, epoch, context):
        self.context = json.dumps(context, sort_keys=True, separators=(',', ':'))
        self.process = subprocess.Popen(
            [sys.executable, '-B', '-u', '-c', WORKER, str(epoch), self.context],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, env={'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.messages = queue.Queue()

        def receive():
            try:
                for line in self.process.stdout:
                    self.messages.put(json.loads(line))
            except (ValueError, OSError):
                pass
            finally:
                self.messages.put(None)

        self.reader = threading.Thread(target=receive, daemon=True)
        self.reader.start()
        try:
            ready = self.read()
            if ready != {'type': 'ready', 'epoch': epoch,
                         'context_digest': hashlib.sha256(self.context.encode()).hexdigest()}:
                raise Denied('worker-context-not-confirmed')
        except BaseException:
            self.stop()
            raise

    def read(self):
        try:
            message = self.messages.get(timeout=10)
        except queue.Empty:
            raise Denied('worker-timeout') from None
        if message is None:
            raise Denied('worker-ended')
        return message

    def send(self, message):
        try:
            self.process.stdin.write(json.dumps(message) + '\n')
            self.process.stdin.flush()
        except (BrokenPipeError, OSError, ValueError):
            raise Denied('worker-unavailable') from None

    def stop(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.reader.join(timeout=2)
        self.process.stdin.close()
        self.process.stdout.close()
        if self.process.poll() is None or self.reader.is_alive():
            raise Denied('worker-not-stopped')


class Supervisor:
    def __init__(self, lab, capabilities, context, worker_factory=Worker):
        self.lab, self.capabilities = lab, dict(capabilities)
        self.context, self.epoch = dict(context), 0
        self.workers, self.pending_work = {}, {}
        self.worker_factory = worker_factory
        self.ready = False
        try:
            for name in self.capabilities:
                self.workers[name] = worker_factory(0, context)
            self.ready = True
        except BaseException:
            self.close()
            raise

    def begin(self, name, value):
        if not self.ready or name in self.pending_work:
            raise Denied('supervisor-not-ready')
        ticket = self.lab.begin(self.capabilities[name], self.epoch)
        worker = self.workers[name]
        try:
            worker.send({'type': 'begin', 'value': value})
            message = worker.read()
            if message != {'type': 'started', 'epoch': self.epoch}:
                raise Denied('work-not-started')
        except BaseException:
            self.close()
            raise
        self.pending_work[name] = ticket
        return ticket

    def finish(self, name):
        if not self.ready or name not in self.pending_work:
            raise Denied('no-current-work')
        worker = self.workers[name]
        try:
            worker.send({'type': 'finish'})
            result = worker.read()
            if result.get('type') != 'result' or result.get('epoch') != self.epoch:
                raise Denied('wrong-result-epoch')
            self.lab.complete(self.capabilities[name], self.pending_work.pop(name))
        except BaseException:
            self.close()
            raise
        return result['value']

    def change(self, context):
        """No new epoch becomes active until every old process is confirmed dead.

        Fixed replacement workers report their actual loaded context digest.
        We forward that application-level evidence, not a transport delivery ACK.
        A missing/offline recipient or failed worker leaves the pending epoch
        blocked; never recover by silently continuing with the old workers.
        """
        self.ready = False
        change = json.dumps(context, sort_keys=True, separators=(',', ':'))
        epoch = self.lab.propose(change)
        old_pids = [worker.process.pid for worker in self.workers.values()]
        for worker in self.workers.values():
            worker.stop()
        old_stopped = all(worker.process.poll() is not None for worker in self.workers.values())
        if not old_stopped:
            raise Denied('old-context-still-running')
        self.workers = {}
        self.pending_work.clear()
        try:
            for name, capability in self.capabilities.items():
                worker = self.worker_factory(epoch, context)
                self.workers[name] = worker
                self.lab.acknowledge(capability, epoch, change, application=True)
            self.lab.activate()
        except BaseException:
            self.close()
            raise
        self.context, self.epoch, self.ready = dict(context), epoch, True
        return {'old_pids': old_pids, 'old_stopped': old_stopped,
                'new_pids': [worker.process.pid for worker in self.workers.values()], 'epoch': epoch}

    def close(self):
        self.ready = False
        for worker in self.workers.values():
            worker.stop()


def probe_supervisor(lab):
    capabilities = {name: lab.register(name) for name in ('line-a', 'line-b')}
    supervisor = Supervisor(lab, capabilities, {'factor': 2})
    try:
        stale = supervisor.begin('line-b', 7)
        transition = supervisor.change({'factor': 3})
        rejected = False
        try:
            lab.complete(capabilities['line-b'], stale)
        except Denied:
            rejected = True
        supervisor.begin('line-b', 7)
        current = supervisor.finish('line-b')
        checks = {'old_workers_stopped': transition['old_stopped'],
                  'old_ticket_rejected': rejected, 'new_context_used': current == 21,
                  'new_epoch_active': transition['epoch'] == 1,
                  'all_lines_acknowledged': all(
                      lab.inbox(capability)[-1]['acknowledged'] == 1 for capability in capabilities.values())}
        return {'result': '通過' if all(checks.values()) else '不通過', 'checks': checks,
                'scope': '固定合成子程序：舊工作中止、程序退場、替代程序回報新 context digest 後啟用',
                'unknown': '非任意模型／桌面工具；跨機推送、失聯控制、正式可信 launcher 尚未驗收'}
    finally:
        supervisor.close()


def run_supervisor_probe():
    with tempfile.TemporaryDirectory(prefix='bootstrap-v2-supervisor-probe-') as directory:
        lab = Lab(Path(directory) / 'lab.sqlite')
        try:
            return probe_supervisor(lab)
        finally:
            lab.close()
