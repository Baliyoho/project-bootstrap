"""F23 prototype: a read-only turn leaves no owner, commit, stage or push behind.

``read_only(repo, action)`` snapshots the checkout, runs the answer, and
compares. Fetching is allowed (an answer may need fresh facts), so
remote-tracking refs are not part of the snapshot. What is compared:

- local branch and tag refs and HEAD (a commit or branch switch),
- the index file (staging),
- every changed or untracked file's bytes (a marker written but not committed),
- the remote's advertised refs (a push).

A remote that cannot be listed is reported as unverified, never as unchanged.
A remote that moved is reported, but the guard cannot tell our push from a
concurrent writer's, so the code says the remote changed, not who changed it.
Detection only: it does not undo anything.
"""
import hashlib
import subprocess


def _git(repo, env, *args):
    # --no-optional-locks: a plain status refreshes and rewrites the index itself.
    result = subprocess.run(['git', '--no-optional-locks', '-C', str(repo), *args],
                            capture_output=True,
                            env=env, timeout=60)
    return result.returncode, result.stdout


def _remote(repo, env):
    code, name = _git(repo, env, 'rev-parse', '--abbrev-ref', '--symbolic-full-name',
                      '@{upstream}')
    if code:
        return None
    return name.decode().strip().split('/', 1)[0]


def snapshot(repo, env=None):
    code, refs = _git(repo, env, 'for-each-ref', '--format=%(refname) %(objectname)',
                      'refs/heads', 'refs/tags')
    _, head = _git(repo, env, 'symbolic-ref', '--quiet', 'HEAD')
    _, head_sha = _git(repo, env, 'rev-parse', '--verify', '--quiet', 'HEAD')
    _, index_path = _git(repo, env, 'rev-parse', '--path-format=absolute', '--git-path', 'index')
    try:
        with open(index_path.decode().strip(), 'rb') as handle:
            index = hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        index = None
    _, status = _git(repo, env, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
    files = {}
    for entry in status.split(b'\0'):
        if len(entry) > 3:
            path = entry[3:].decode('utf-8', 'surrogateescape')
            code_, data = _git(repo, env, 'hash-object', '--no-filters', '--', path)
            files[path] = data.strip() if code_ == 0 else b'unreadable'
    remote = _remote(repo, env)
    advertised = None
    if remote is not None:
        listed, data = _git(repo, env, 'ls-remote', remote)
        advertised = data if listed == 0 else None
    return {'refs': refs if code == 0 else None, 'head': (head, head_sha), 'index': index,
            'files': files, 'remote': advertised}


def compare(before, after):
    changes, unverified = [], []
    if before['refs'] is None or after['refs'] is None:
        unverified.append('local-refs')
    elif before['refs'] != after['refs'] or before['head'] != after['head']:
        changes.append('local-refs-changed')
    if before['index'] != after['index']:
        changes.append('index-changed')
    if before['files'] != after['files']:
        changes.append('worktree-changed')
    if before['remote'] is None or after['remote'] is None:
        unverified.append('remote')
    elif before['remote'] != after['remote']:
        changes.append('remote-changed')
    return {'ok': not changes and not unverified, 'changes': changes, 'unverified': unverified}


def read_only(repo, action, env=None):
    """Run ``action()`` and return (its result, report).

    If the action raises, the report is attached as ``read_report`` before the
    exception propagates, so a failed answer still shows what it changed.
    """
    before = snapshot(repo, env)
    try:
        result = action()
    except BaseException as error:
        error.read_report = compare(before, snapshot(repo, env))
        raise
    return result, compare(before, snapshot(repo, env))
