"""Synthetic POSIX process-group feasibility probe; never a launcher authority.

An ordinary descendant and a session-escaping descendant hold the same kind
of exclusive lock. The probe observes the lock, not a saved PID or PID exit.
All spawned code and paths are fixed test fixtures under a temporary directory.
"""
import os
from pathlib import Path
import platform
import select
import signal
import subprocess
import sys
import tempfile
import time


CHILD = '''import fcntl, pathlib, sys, time
root = pathlib.Path(sys.argv[1])
with (root / 'held').open('w') as stream:
    fcntl.flock(stream, fcntl.LOCK_EX)
    print('locked', flush=True)
    while not (root / 'finish').exists():
        time.sleep(0.02)
'''

LEADER = '''import subprocess, sys
child = subprocess.Popen((sys.executable, '-B', '-u', '-c', sys.argv[1], sys.argv[2]),
    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    start_new_session=sys.argv[3] == 'escape')
assert child.stdout.readline() == b'locked\\n'
child.stdout.close()
print('ready', flush=True)
sys.stdin.read()
'''


def lock_held(root):
    import fcntl
    with (root / 'held').open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        return False


def wait_for_unlock(root, timeout=3):
    until = time.monotonic() + timeout
    while lock_held(root) and time.monotonic() < until:
        time.sleep(0.02)
    return not lock_held(root)


def run_case(escape):
    if os.name != 'posix':
        raise RuntimeError('POSIX-only synthetic probe')
    with tempfile.TemporaryDirectory(prefix='bootstrap-v2-tree-') as temporary:
        root = Path(temporary)
        leader = subprocess.Popen((sys.executable, '-B', '-u', '-c', LEADER, CHILD,
                                   str(root), 'escape' if escape else 'ordinary'),
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, start_new_session=True)
        try:
            if not select.select([leader.stdout], [], [], 5)[0]:
                raise RuntimeError('tree fixture did not become ready')
            if leader.stdout.readline() != b'ready\n' or not lock_held(root):
                raise RuntimeError('tree fixture lacked live descendant evidence')
            # Only the fresh test leader's still-owned group is signaled. Never
            # persist this numeric identity or use it for restart recovery.
            os.killpg(leader.pid, signal.SIGTERM)
            leader.wait(timeout=5)
            return {'group_leader_exited': True,
                    'descendant_exited': wait_for_unlock(root, timeout=1)}
        finally:
            (root / 'finish').touch()
            if leader.poll() is None:
                os.killpg(leader.pid, signal.SIGKILL)
            leader.wait(timeout=5)
            if not wait_for_unlock(root):
                raise RuntimeError('synthetic descendant did not release test lock')
            leader.stdin.close()
            leader.stdout.close()


def probe_tree():
    if os.name != 'posix':
        return {'result': '未驗證', 'reason': '需要 POSIX；Windows Job Object 尚未實測'}
    ordinary = run_case(False)
    escaped = run_case(True)
    return {'result': '反例重現' if ordinary['descendant_exited'] and
            not escaped['descendant_exited'] else '不通過',
            'ordinary_group': ordinary, 'escaped_session': escaped,
            'scope': '本機合成程序群組；脫離 session 的後代仍存活，不提供任意程序樹退場證明'}


ES_CLIENT_SOURCE = r'''#include <EndpointSecurity/EndpointSecurity.h>
#include <stdio.h>
int main(void) {
    es_client_t *client = NULL;
    es_new_client_result_t result = es_new_descendants_client(&client,
        ^(es_client_t *c, const es_message_t *m) { (void)c; (void)m; });
    printf("%d\n", (int)result);
    if (client != NULL) es_delete_client(client);
    return 0;
}
'''


def _es_assessment(code):
    # ES_NEW_CLIENT_RESULT_ERR_NOT_ENTITLED is 3 in the macOS 27 SDK.
    # Even a successful client has not proved delivery, teardown, or recovery.
    if code == 3:
        return {'result': '無權限', 'reason': '本機未獲 Endpoint Security client entitlement'}
    if code == 0:
        return {'result': '可建立但未驗收', 'reason': '尚未測 fork／exit 事件、監護失效與可重啟退場核對'}
    return {'result': '未驗證', 'reason': f'Endpoint Security client 回傳 {code}'}


def probe_descendant_api():
    """Check an unsigned local helper's ES admission; no event subscription or deployment."""
    if sys.platform != 'darwin':
        return {'result': '未驗證', 'reason': '只在 macOS 27+ 探測', 'strict_boundary': '未通過'}
    release = platform.mac_ver()[0]
    try:
        major = int(release.split('.', 1)[0])
    except (ValueError, IndexError):
        return {'result': '未驗證', 'reason': '無法判定 macOS 版本', 'strict_boundary': '未通過'}
    if major < 27:
        return {'result': '未驗證', 'reason': '此 API 從 macOS 27 起提供', 'strict_boundary': '未通過'}
    try:
        with tempfile.TemporaryDirectory(prefix='bootstrap-v2-es-') as directory:
            binary = str(Path(directory) / 'probe')
            compiled = subprocess.run(['xcrun', 'clang', '-fblocks', '-lEndpointSecurity',
                                       '-x', 'c', '-', '-o', binary], input=ES_CLIENT_SOURCE,
                                      capture_output=True, text=True, timeout=20)
            if compiled.returncode != 0:
                return {'result': '未驗證', 'reason': '本機 SDK 或編譯鏈無法建立探針',
                        'strict_boundary': '未通過'}
            executed = subprocess.run([binary], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return {'result': '未驗證', 'reason': '本機探針未能完成', 'strict_boundary': '未通過'}
    if executed.returncode != 0:
        return {'result': '未驗證', 'reason': '探針執行失敗', 'strict_boundary': '未通過'}
    try:
        code = int(executed.stdout.strip())
    except ValueError:
        return {'result': '未驗證', 'reason': '探針回應格式無效', 'strict_boundary': '未通過'}
    return {'api': 'es_new_descendants_client', 'macos': release,
            'client_result': code, **_es_assessment(code),
            'strict_boundary': '未通過'}
