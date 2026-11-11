"""Parent-only broker with a real confined synthetic agent, macOS P0 only.

Unlike isolation.py's small mechanism probe, this profile denies reads by
default and exposes only runtime directories, a synthetic read-only repo and
the child's scratch. No credentials or parent capability enter its argv/env.
Not a production sandbox or an escape audit; no real model is launched.
"""
import json
import os
from pathlib import Path
import platform
import queue
import subprocess
import sys
import tempfile
import threading
import time

from experiments.v2.broker import Broker, MAX_REQUEST_BYTES
from experiments.v2.contracts import Denied, Lab
from experiments.v2.materializer import Materializer
from experiments.v2.launcher import LaunchAuthority
from experiments.v2.lifecycle import LaunchPlan, ProcessLauncher, TicketVault


SANDBOX_EXEC = Path('/usr/bin/sandbox-exec')


PROFILE = '''(version 1)
(allow default)
(deny file-read*)
(deny file-write*)
(deny network*)
(deny process-fork)
(deny signal)
(allow file-read*
    (subpath "/System")
    (subpath "/usr")
    (subpath "/bin")
    (subpath "/Library/Developer/CommandLineTools")
    (subpath (param "PYTHON_RUNTIME"))
    (literal (param "PYTHON_EXECUTABLE"))
    (literal "/dev/null")
    (literal "/dev/urandom")
    (subpath (param "REPO"))
    (subpath (param "SCRATCH")))
(allow file-write* (subpath (param "SCRATCH")))
'''

AGENT = '''import json, os, pathlib, signal, subprocess, sys
vault, repo, scratch, sibling = map(pathlib.Path, sys.argv[1:5])
def blocked(operation):
    try:
        operation()
    except PermissionError:
        return
    raise AssertionError('direct access not blocked')
# No forked worker can survive the guarded process. Cover both fork and the
# subprocess fast path (which may use posix_spawn rather than fork).
def attempt_fork():
    pid = os.fork()
    if pid == 0:
        os._exit(0)
    os.waitpid(pid, 0)
blocked(attempt_fork)
blocked(lambda: subprocess.run([sys.executable, '-c', 'pass'], check=True))
def attempt_spawn():
    pid = os.posix_spawn(sys.executable, [sys.executable, '-c', 'pass'], {})
    os.waitpid(pid, 0)
blocked(attempt_spawn)
blocked(lambda: os.kill(os.getppid(), 0))
blocked(lambda: os.kill(os.getppid(), signal.SIGTERM))
blocked(lambda: (vault / 'private.sqlite').read_bytes())
blocked(lambda: (vault / 'private.sqlite').write_bytes(b'overwrite'))
blocked(lambda: (vault / 'private.sqlite').unlink())
blocked(lambda: list((vault / 'tickets').iterdir()))
blocked(lambda: (sibling / 'private').read_bytes())
blocked(lambda: (repo / 'note').write_bytes(b'direct-write'))
blocked(lambda: (repo / 'managed.txt').write_bytes(b'direct-write'))
assert (repo / 'note').read_text() == 'read-only-view'
(scratch / 'local').write_text('allowed')
(scratch / 'alias').symlink_to(vault / 'private.sqlite')
blocked(lambda: (scratch / 'alias').read_bytes())
def call(request):
    print(json.dumps(request), flush=True)
    return json.loads(sys.stdin.readline())
request = dict(id=1, method='write', resource='note-a', base=None, text='first', epoch=0)
first = call(request)
assert first['code'] == 'ok'
assert (repo / 'managed.txt').read_text() == 'first'
blocked(lambda: (repo / 'managed.txt').write_bytes(b'outside-broker'))
assert call(request) == first
assert call(dict(request, text='changed-replay'))['code'] == 'changed-retry'
assert call(dict(request, id=2, actor='line-b'))['code'] == 'unexpected-fields'
assert call(dict(id=3, method='grant', actor='line-a'))['code'] == 'unknown-method'
assert call(dict(request, id=4, resource='note-b'))['code'] == 'resource-not-authorized'
effect = dict(id=5, method='effect', resource='budget', kind='extra-model', epoch=0)
assert call(effect)['code'] == 'not-authorized'
effect.update(id=6, kind='paid-api')
assert call(effect)['code'] == 'ok'
assert call(effect)['code'] == 'ok'
assert call(dict(effect, id=7))['code'] == 'not-authorized'
second = call(dict(request, id=8, base=first['digest'], text='second'))
assert second['code'] == 'ok'
'''


def sandbox_plan(repo, scratch, program, *args):
    # Python resolves its prefix through these entries. Allow each ancestor
    # itself without exposing its subtree.
    runtime = Path(sys.base_prefix).resolve()
    ancestor_params, ancestor_rules = [], []
    for index, path in enumerate(runtime.parents):
        key = 'RUNTIME_ANCESTOR_' + str(index)
        ancestor_params.extend(['-D', key + '=' + str(path)])
        ancestor_rules.append('(literal (param "' + key + '"))')
    profile = PROFILE + '\n(allow file-read* ' + ' '.join(ancestor_rules) + ')\n'
    handshake = "import sys; print('bootstrap-v2-ready', flush=True); assert sys.stdin.readline() == 'bootstrap-v2-go\\n'\n"
    # Start the resolved base interpreter: a virtualenv's python is a symlink
    # (and pyvenv.cfg) outside the allowed reads, and the agent needs only stdlib.
    executable = str(Path(sys.executable).resolve())
    command = [str(SANDBOX_EXEC), '-D', 'REPO=' + str(repo),
        '-D', 'SCRATCH=' + str(scratch), '-D', 'PYTHON_RUNTIME=' + str(runtime),
        '-D', 'PYTHON_EXECUTABLE=' + executable] + ancestor_params + [
        '-p', profile, executable, '-B', '-u', '-c', handshake + program, *map(str, args)]
    return LaunchPlan(tuple(command), str(scratch))


def launch_agent(broker, channel, command, scratch, process=None, check=None, stop=None):
    """Bounded fixed-fixture transport; the parent chooses the channel object."""
    if process is None:
        process = subprocess.Popen(command, cwd=scratch, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env={'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1'}, close_fds=True)
    received = queue.Queue(maxsize=2)
    stopping = threading.Event()

    def enqueue(line):
        while not stopping.is_set():
            try:
                received.put(line, timeout=0.1)
                return
            except queue.Full:
                pass

    def reader():
        while not stopping.is_set():
            line = process.stdout.readline(MAX_REQUEST_BYTES + 1)
            enqueue(line)
            if not line or len(line) > MAX_REQUEST_BYTES:
                return

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    requests = 0
    last_message = time.monotonic()
    try:
        while True:
            # Keep lease checks on the parent/SQLite thread, including while a
            # child is idle. No background thread gets administrative access.
            if check is not None:
                check()
            try:
                line = received.get(timeout=0.1)
            except queue.Empty:
                if time.monotonic() - last_message >= 10:
                    raise
                continue
            if not line:
                break
            last_message = time.monotonic()
            if len(line) > MAX_REQUEST_BYTES or requests >= 32:
                return {'completed': False, 'reason': 'transport-limit'}
            response = broker.dispatch(channel, line)
            process.stdin.write(response)
            process.stdin.flush()
            requests += 1
        code = process.wait(timeout=5)
        return {'completed': code == 0, 'requests': requests, 'exit_code': code}
    except (queue.Empty, OSError, subprocess.TimeoutExpired):
        return {'completed': False, 'reason': 'agent-timeout-or-pipe-failure'}
    except Denied:
        return {'completed': False, 'reason': 'agent-authority-or-lifecycle-ended'}
    finally:
        broker.detach(channel)
        stopping.set()
        if stop is not None:
            stop()
        else:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
        thread.join(timeout=2)
        process.stdin.close()
        process.stdout.close()


def probe_broker(grant_effect=None):
    if platform.system() != 'Darwin' or not SANDBOX_EXEC.is_file():
        return {'result': '未驗證', 'reason': '本管道／OS 整合探針限 macOS；其他 OS 尚無 adapter'}
    with tempfile.TemporaryDirectory(prefix='bootstrap-v2-broker-') as directory:
        root = Path(directory).resolve()
        vault, repo, scratch, sibling = (root / name for name in ('vault', 'repo', 'scratch', 'sibling'))
        for path in (vault, repo, scratch, sibling):
            path.mkdir()
        (repo / 'note').write_text('read-only-view')
        (sibling / 'private').write_text('SYNTHETIC_OTHER_SESSION')
        lab = Lab(vault / 'private.sqlite')
        (vault / 'tickets').mkdir(mode=0o700)
        ticket_vault = TicketVault(vault / 'tickets')
        launcher = None
        try:
            materializer = Materializer(lab, repo, {'note-a': 'managed.txt', 'note-b': 'other.txt'})
            broker = Broker(lab, materializer)
            authority = LaunchAuthority(broker)
            expires = time.time() + 60
            ticket = authority.issue(('note-a', 'budget'), 'synthetic-parent-approval', expires)
            handle = ticket_vault.save(ticket)
            launcher = ProcessLauncher(authority, ticket_vault)
            authority.connect(authority.issue(('note-b',), 'synthetic-parent-approval', expires))
            if grant_effect is None:
                authority.grant(ticket, 'paid-api', 'budget', 1, 'synthetic-human-authorization', expires)
            else:
                grant_effect(authority, ticket)
            plan = sandbox_plan(repo, scratch, AGENT, vault, repo, scratch, sibling)
            command = plan.argv
            try:
                child = launcher.start(handle, plan)
            except (Denied, OSError):
                return {'result': '不通過', 'reason': 'launcher-start-failed',
                        'checks': {'confined_agent_completed': False},
                        'transport': {'completed': False, 'reason': 'launcher-start-failed'}}
            channel = child.channel
            actor = lab.actor(channel.capability)
            # A normal process exit is handled by transport EOF, not a failed
            # authority check. Permit checks still run while waiting for bytes.
            def check_authority():
                with lab.transaction():
                    channel.authorize(channel)
            transport = launch_agent(broker, channel, command, scratch,
                                     process=child.process, check=check_authority,
                                     stop=lambda: launcher.stop(actor))
            launcher.close()
            events = list(lab.db.execute('SELECT actor, before, after FROM writes ORDER BY seq'))
            effects = list(lab.db.execute('SELECT actor, kind, resource FROM effects'))
            checks = {
                'confined_agent_completed': transport['completed'],
                'requests_exercised': transport.get('requests') == 11,
                'pipe_principal_recorded': len(events) == 2 and all(row['actor'] == actor for row in events),
                'full_content_linked': len(events) == 2 and events[0]['before'] is None
                    and events[0]['after'] == events[1]['before'] == b'first' and events[1]['after'] == b'second',
                'grant_and_replay_scoped': len(effects) == 1 and tuple(effects[0]) == (actor, 'paid-api', 'budget'),
                'readonly_view_unchanged': (repo / 'note').read_text() == 'read-only-view',
                'managed_file_applied': (repo / 'managed.txt').is_file() and (repo / 'managed.txt').read_bytes() == b'second',
                'materializations_recorded': lab.db.execute(
                    "SELECT count(*) FROM materializations WHERE phase='applied'").fetchone()[0] == 2,
                'scratch_writable': (scratch / 'local').is_file(),
                'closed_pipe_revoked': channel.closed,
                'managed_lifecycle_stopped': child.process.poll() is not None and lab.db.execute(
                    'SELECT state FROM managed_launches WHERE actor=?', (actor,)).fetchone()[0] == 'stopped',
                'private_ticket_roundtrip': ticket_vault.load(handle) == ticket,
                'ticket_not_in_child_command': all(ticket not in argument for argument in command),
            }
            return {'result': '通過' if all(checks.values()) else '不通過', 'checks': checks,
                'transport': transport,
                'scope': 'parent 限期資格＋監護退場／回收證據＋私有票據＋Mac 禁 fork／spawn／signal 合成 agent；代理套用 POSIX 合成工作樹',
                'unknown': '非正式人類服務／真實工具；guardian 被殺後回收、任意後代、Windows、逃逸、斷電、多 writer、跨機未驗收'}
        finally:
            if launcher is not None:
                launcher.close()
            ticket_vault.close()
            lab.close()
