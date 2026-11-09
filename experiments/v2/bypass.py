"""F21: bypassing a rule is blocked where the decision book says block, and
left on record everywhere else.

Block, in-place edit of shared rules: ``guard_commit`` reads what is staged in
a deployed project's Git index for every released (core or adapter) path of
the installed manifest. Staged content that differs from the release, or a
released file deleted from the index, refuses the commit: shared rules are
changed at the source and synced, never edited in one project. Releasing an
unverified source is blocked by ``publish.py``.

Record, other skipped steps: ``record`` appends an event to a JSON-lines log
where each line carries the SHA-256 of the previous line, and ``audit`` walks
the chain. A required step is accounted for when it was done or its skip was
recorded with a reason; a step that is neither is a silent skip. A truncated
or edited log breaks the chain and the audit says so, but whoever can rewrite
the whole file can rewrite the chain too: this finds accidents and partial
edits, it does not prove the log is genuine.
"""
import hashlib
import json
import subprocess

from experiments.v2.contracts import Denied

GENESIS = '0' * 64


def guard_commit(repo, manifest, owners, env=None):
    """``owners``: {path: 'core'|'adapter'|...}; only released paths are guarded."""
    for path in sorted(manifest['components']):
        if owners.get(path) not in ('core', 'adapter'):
            continue
        result = subprocess.run(['git', '-C', str(repo), 'show', ':' + path],
                                capture_output=True, env=env, timeout=30)
        if result.returncode:
            raise Denied('in-place-core-delete:' + path)
        if hashlib.sha256(result.stdout).hexdigest() != manifest['components'][path]:
            raise Denied('in-place-core-edit:' + path)
    return True


def _line_digest(line):
    return hashlib.sha256(line.encode('utf-8')).hexdigest()


def record(log, event):
    """Append ``event`` (step, status 'done'|'skipped', by, at, reason) to the chain."""
    if event.get('status') not in ('done', 'skipped') or not event.get('step'):
        raise Denied('event-invalid')
    if event['status'] == 'skipped' and not str(event.get('reason') or '').strip():
        raise Denied('skip-without-reason')
    previous = GENESIS
    if log.exists():
        lines = log.read_text(encoding='utf-8').splitlines()
        if lines:
            previous = _line_digest(lines[-1])
    line = json.dumps(dict(event, prev=previous), ensure_ascii=False, sort_keys=True)
    with log.open('a', encoding='utf-8', newline='\n') as handle:
        handle.write(line + '\n')


def audit(log, required):
    """Return {'chain': 'ok'|'broken'|'missing', 'steps': {step: state}, 'findings': [...]}."""
    findings, events = [], []
    if not log.exists():
        chain = 'missing'
        findings.append(('log', 'log-missing'))
    else:
        chain, previous = 'ok', GENESIS
        for number, line in enumerate(log.read_text(encoding='utf-8').splitlines(), 1):
            try:
                event = json.loads(line)
            except ValueError:
                event = None
            if not isinstance(event, dict) or event.get('prev') != previous:
                chain = 'broken'
                findings.append((f'line {number}', 'chain-broken'))
                break
            events.append(event)
            previous = _line_digest(line)
    steps = {}
    for event in events:
        if event.get('status') == 'done':
            steps[event['step']] = 'done'
        elif event.get('status') == 'skipped' and str(event.get('reason') or '').strip():
            steps.setdefault(event['step'], 'skipped')
        else:
            findings.append((str(event.get('step')), 'event-unaccounted'))
    for step in required:
        if step not in steps:
            steps[step] = 'silent-skip'
            findings.append((step, 'silent-skip'))
    return {'chain': chain, 'steps': steps, 'findings': findings}
