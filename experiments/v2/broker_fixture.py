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

from experiments.v2.broker import Broker, MAX_REQUEST_BYTES
from experiments.v2.contracts import Lab
from experiments.v2.materializer import Materializer


PROFILE = '''(version 1)
(allow default)
(deny file-read*)
(deny file-write*)
(deny network*)
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

AGENT = '''import json, pathlib, sys
vault, repo, scratch, sibling = map(pathlib.Path, sys.argv[1:5])
def blocked(operation):
    try:
        operation()
    except PermissionError:
        return
    raise AssertionError('direct access not blocked')
blocked(lambda: (vault / 'private.sqlite').read_bytes())
blocked(lambda: (vault / 'private.sqlite').write_bytes(b'overwrite'))
blocked(lambda: (vault / 'private.sqlite').unlink())
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


def launch_agent(broker, channel, command, scratch):
    """Bounded fixed-fixture transport; the parent chooses the channel object."""
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
    try:
        while True:
            line = received.get(timeout=10)
            if not line:
                break
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
    finally:
        broker.detach(channel)
        stopping.set()
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        thread.join(timeout=2)
        process.stdin.close()
        process.stdout.close()


def probe_broker():
    if platform.system() != 'Darwin' or not Path('/usr/bin/sandbox-exec').is_file():
        return {'result': '未驗證', 'reason': '本管道／OS 整合探針限 macOS；其他 OS 尚無 adapter'}
    with tempfile.TemporaryDirectory(prefix='bootstrap-v2-broker-') as directory:
        root = Path(directory).resolve()
        vault, repo, scratch, sibling = (root / name for name in ('vault', 'repo', 'scratch', 'sibling'))
        for path in (vault, repo, scratch, sibling):
            path.mkdir()
        (repo / 'note').write_text('read-only-view')
        (sibling / 'private').write_text('SYNTHETIC_OTHER_SESSION')
        lab = Lab(vault / 'private.sqlite')
        try:
            materializer = Materializer(lab, repo, {'note-a': 'managed.txt', 'note-b': 'other.txt'})
            broker = Broker(lab, materializer)
            channel = broker.attach('line-a', ('note-a', 'budget'))
            broker.attach('line-b', ('note-b',))
            lab.grant('line-a', 'paid-api', 'budget', 1, 'synthetic-human-authorization')
            # Python's launcher resolves its prefix via these directory entries.
            # Permit only each ancestor itself, never its entire subtree. Without
            # this, the runtime may abort before testing the intended boundary.
            runtime = Path(sys.base_prefix).resolve()
            ancestor_params, ancestor_rules = [], []
            for index, path in enumerate(runtime.parents):
                key = 'RUNTIME_ANCESTOR_' + str(index)
                ancestor_params.extend(['-D', key + '=' + str(path)])
                ancestor_rules.append('(literal (param "' + key + '"))')
            profile = PROFILE + '\n(allow file-read* ' + ' '.join(ancestor_rules) + ')\n'
            command = ['/usr/bin/sandbox-exec', '-D', 'REPO=' + str(repo),
                '-D', 'SCRATCH=' + str(scratch), '-D', 'PYTHON_RUNTIME=' + str(runtime),
                '-D', 'PYTHON_EXECUTABLE=' + str(Path(sys.executable).resolve())] + ancestor_params + ['-p', profile,
                sys.executable, '-B', '-u', '-c', AGENT, str(vault), str(repo), str(scratch), str(sibling)]
            transport = launch_agent(broker, channel, command, scratch)
            events = list(lab.db.execute('SELECT actor, before, after FROM writes ORDER BY seq'))
            effects = list(lab.db.execute('SELECT actor, kind, resource FROM effects'))
            checks = {
                'confined_agent_completed': transport['completed'],
                'requests_exercised': transport.get('requests') == 11,
                'pipe_principal_recorded': len(events) == 2 and all(row['actor'] == 'line-a' for row in events),
                'full_content_linked': len(events) == 2 and events[0]['before'] is None
                    and events[0]['after'] == events[1]['before'] == b'first' and events[1]['after'] == b'second',
                'grant_and_replay_scoped': len(effects) == 1 and tuple(effects[0]) == ('line-a', 'paid-api', 'budget'),
                'readonly_view_unchanged': (repo / 'note').read_text() == 'read-only-view',
                'managed_file_applied': (repo / 'managed.txt').is_file() and (repo / 'managed.txt').read_bytes() == b'second',
                'materializations_recorded': lab.db.execute(
                    "SELECT count(*) FROM materializations WHERE phase='applied'").fetchone()[0] == 2,
                'scratch_writable': (scratch / 'local').is_file(),
                'closed_pipe_revoked': channel.closed,
            }
            return {'result': '通過' if all(checks.values()) else '不通過', 'checks': checks,
                'transport': transport,
                'scope': 'parent-only 管理 API＋管道身分＋受隔離合成 agent；代理將已受理事件套用到 POSIX 合成工作樹',
                'unknown': '非正式 launcher／真實專案；未驗 Windows、逃逸、斷電、多 writer、跨機或模型／桌面工具整合'}
        finally:
            lab.close()
