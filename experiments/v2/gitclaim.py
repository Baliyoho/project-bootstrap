"""M3 start/finish gates over a real Git checkout (F9／F10 prototype).

``assess_start`` decides whether this checkout may take write eligibility.
It fails closed: a failed fetch is never answered from an old tracking ref,
and a missing owner field is unknown, not idle. ``finish`` publishes the final
tree and returns a ``HandoffReceipt`` only after the push succeeded and a
fresh fetch shows the remote equals HEAD with the marker released.

This is a coordination check, not an atomic lock: another writer can still
push between the check and the push, which is why finish refuses to force
and re-reads the remote afterwards. Synthetic fixtures only; it never
stashes, resets, rebases or force-pushes.
"""
import re
import subprocess

from experiments.v2.session import HandoffReceipt

MARKER_PREFIX = '- **工作中**：'
IDLE = '無（已交棒）'


class GitGateDenied(Exception):
    """Fixed-code refusal; the code is the whole message."""


def _git(repo, env, *args, check=True):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                            env=env, timeout=60)
    if check and result.returncode != 0:
        raise GitGateDenied('git-error')
    return result


def _out(repo, env, *args):
    return _git(repo, env, *args).stdout.decode('utf-8', 'replace').strip()


def owner_field(text):
    """Return the marker value, or None when the field is absent or repeated."""
    values = [line[len(MARKER_PREFIX):].strip() for line in text.splitlines()
              if line.startswith(MARKER_PREFIX)]
    return values[0] if len(values) == 1 and values[0] else None


_FIELD = re.compile(r'`([^`]*)`')
KNOWN_TOOLS = ('Claude Code', 'Codex CLI', 'Gemini CLI', 'Antigravity')


def owner_parts(value):
    """Split ``machine ／ tool ／ session`` (session optional); None if malformed.

    Each field must be a non-blank backticked value; text after the last field
    (the start time) is ignored. Two fields means the old format without tool.
    """
    parts = value.split(' ／ ')
    if not 2 <= len(parts) <= 3:
        return None
    fields = []
    for index, part in enumerate(parts):
        match = _FIELD.match(part.strip())
        if (match is None or not match.group(1).strip()
                or (index < len(parts) - 1 and match.end() != len(part.strip()))):
            return None
        fields.append(match.group(1).strip())
    return fields


def _busy_code(remote_owner, owner):
    theirs, mine = owner_parts(remote_owner), owner_parts(owner)
    if theirs is None:
        return 'owner-unknown'
    # Two fields are either machine／tool (session omitted) or the old
    # machine／session format. Only a known tool name settles it; both deny.
    if len(theirs) == 2 and theirs[1] not in KNOWN_TOOLS:
        return 'busy-unidentified-tool'
    if theirs[0] != mine[0]:
        return 'busy-other-machine'
    if theirs[1] != mine[1]:
        return 'busy-same-machine-other-tool'
    return 'busy-same-tool-other-session'


def _remote_owner(repo, env, ref, marker_path):
    shown = _git(repo, env, 'show', f'{ref}:{marker_path}', check=False)
    if shown.returncode != 0:
        return None
    return owner_field(shown.stdout.decode('utf-8', 'replace'))


def _locate(repo, env):
    branch = _out(repo, env, 'rev-parse', '--abbrev-ref', 'HEAD')
    if branch == 'HEAD':
        raise GitGateDenied('detached-head')
    upstream = _git(repo, env, 'rev-parse', '--abbrev-ref', '--symbolic-full-name',
                    '@{upstream}', check=False)
    if upstream.returncode != 0:
        raise GitGateDenied('no-upstream')
    upstream = upstream.stdout.decode().strip()
    remote = _git(repo, env, 'config', f'branch.{branch}.remote', check=False)
    remote = remote.stdout.decode().strip()
    if not remote or upstream != f'{remote}/{branch}':
        raise GitGateDenied('upstream-mismatch')
    return branch, remote, upstream


def _fetch(repo, env, remote):
    if _git(repo, env, 'fetch', '--quiet', remote, check=False).returncode != 0:
        raise GitGateDenied('fetch-failed')


def _dirty(repo, env):
    return bool(_out(repo, env, 'status', '--porcelain', '--untracked-files=all'))


def _counts(repo, env):
    ahead, behind = _out(repo, env, 'rev-list', '--left-right', '--count',
                         'HEAD...@{upstream}').split()
    return int(ahead), int(behind)


def assess_start(repo, owner, env=None, marker_path='HANDOFF.md'):
    """Return the facts that grant eligibility, or raise GitGateDenied(code).

    ``owner`` is the full marker value this session would write; an exact
    match means the remote marker already names this session.
    """
    if not isinstance(owner, str) or len(owner_parts(owner.strip()) or ()) != 3:
        raise GitGateDenied('invalid-owner')
    branch, remote, upstream = _locate(repo, env)
    _fetch(repo, env, remote)
    if _dirty(repo, env):
        raise GitGateDenied('dirty-unknown')
    ahead, behind = _counts(repo, env)
    if ahead and behind:
        raise GitGateDenied('diverged')
    if ahead:
        raise GitGateDenied('ahead-only')
    if behind:
        raise GitGateDenied('behind-pull-required')
    remote_owner = _remote_owner(repo, env, upstream, marker_path)
    if remote_owner is None:
        raise GitGateDenied('owner-unknown')
    if remote_owner not in (IDLE, owner.strip()):
        raise GitGateDenied(_busy_code(remote_owner, owner.strip()))
    return {'branch': branch, 'upstream': upstream,
            'remote_sha': _out(repo, env, 'rev-parse', upstream),
            'remote_owner': remote_owner}


def run_check(repo, argv, env=None):
    """Run one verifier on a clean checkout and bind its result to HEAD's tree.

    A dirty tree before or after the run yields no receipt: the result would
    describe content that is not the commit being published.
    """
    if not argv or not all(isinstance(item, str) and item for item in argv):
        raise GitGateDenied('invalid-check')
    if _dirty(repo, env):
        raise GitGateDenied('final-tree-dirty')
    tree = _out(repo, env, 'rev-parse', 'HEAD^{tree}')
    result = subprocess.run(argv, cwd=str(repo), env=env, capture_output=True, timeout=600)
    if _dirty(repo, env) or _out(repo, env, 'rev-parse', 'HEAD^{tree}') != tree:
        raise GitGateDenied('check-changed-tree')
    text = result.stdout.decode('utf-8', 'replace') + result.stderr.decode('utf-8', 'replace')
    skipped = len(re.findall(r'(?im)^\s*\[?\s*skip\b', text))
    return {'command': list(argv), 'exit': result.returncode, 'skipped': skipped, 'tree': tree}


def _require_checks(repo, env, receipts):
    if not isinstance(receipts, (list, tuple)) or not receipts:
        raise GitGateDenied('final-checks-missing')
    tree = _out(repo, env, 'rev-parse', 'HEAD^{tree}')
    for receipt in receipts:
        if (not isinstance(receipt, dict)
                or set(receipt) != {'command', 'exit', 'skipped', 'tree'}
                or type(receipt['exit']) is not int or type(receipt['skipped']) is not int):
            raise GitGateDenied('final-checks-missing')
        if receipt['exit'] != 0 or receipt['skipped'] != 0:
            raise GitGateDenied('final-checks-failed')
        if receipt['tree'] != tree:
            raise GitGateDenied('final-checks-stale')


def finish(repo, receipts, env=None, marker_path='HANDOFF.md'):
    """Publish HEAD and prove the release; never force, never claim on failure.

    ``receipts`` come from ``run_check`` on this exact tree; a boolean or a
    result for an earlier tree is not accepted.
    """
    branch, remote, upstream = _locate(repo, env)
    if _dirty(repo, env):
        raise GitGateDenied('final-tree-dirty')
    _require_checks(repo, env, receipts)
    if _remote_owner(repo, env, 'HEAD', marker_path) != IDLE:
        raise GitGateDenied('marker-not-released')
    _fetch(repo, env, remote)
    remote_sha = _out(repo, env, 'rev-parse', upstream)
    if _git(repo, env, 'merge-base', '--is-ancestor', remote_sha, 'HEAD',
            check=False).returncode != 0:
        raise GitGateDenied('remote-advanced')
    if _git(repo, env, 'push', '--quiet', remote, f'HEAD:refs/heads/{branch}',
            check=False).returncode != 0:
        raise GitGateDenied('push-failed')
    _fetch(repo, env, remote)
    head = _out(repo, env, 'rev-parse', 'HEAD')
    aligned = _out(repo, env, 'rev-parse', upstream) == head and not _dirty(repo, env)
    # Implied by the HEAD check above once aligned, so no input fails it alone;
    # it is read back so the receipt field comes from the remote, not from HEAD.
    released = _remote_owner(repo, env, upstream, marker_path) == IDLE
    if not (aligned and released):
        raise GitGateDenied('remote-not-confirmed')
    return HandoffReceipt(event_id=head, final_checks_passed=True, push_succeeded=True,
                          remote_released=released, upstream_aligned=aligned)
