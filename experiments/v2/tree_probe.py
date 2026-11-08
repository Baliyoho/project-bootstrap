"""Synthetic POSIX process-group feasibility probe; never a launcher authority.

An ordinary descendant and a session-escaping descendant hold the same kind
of exclusive lock. The probe observes the lock, not a saved PID or PID exit.
All spawned code and paths are fixed test fixtures under a temporary directory.
"""
import os
from pathlib import Path
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
