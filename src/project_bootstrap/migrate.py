"""P2 slice 5: moving old copy-based projects onto the package (decision Q25).

The old sync tool kept every project's copy of the shared files up to date.
The migrator moves a project once from that model to the pointer model of
slices 2 and 3: every whole core／adapter file equal to the installed package,
the mixed files merged so the project's own parts stay, and a pointer.

This module decides; ``tools/migrate_project.py`` observes the project and
writes. For each released file the tool reports what it saw:

- ``('digest', d)``: the file's shared content hashes to ``d`` (for a
  ``region`` file only the shared region counts), with CRLF counted as LF
  like the per-write check (decision Q26 (a));
- ``'missing'`` or ``'unreadable'``.

``classify`` compares that with the target package and with every version
this repository has published:

- ``current``: already the target content;
- ``known``: an earlier published version, safe to replace;
- ``missing``: will be added, because the per-write check requires every
  whole core／adapter file;
- ``customised``: content nobody published. It may be a project's own change
  that belongs in a declared override, so the migrator never replaces it;
- ``unreadable``: cannot be judged.

``target`` turns one project's observations into exactly one row. A
customised file stops that whole project (decision Q25 (a)): nothing is
written there and it costs one manual comparison; the other projects go on.
``report`` lists every requested target exactly once; it is ok only when no
target failed or needs a manual comparison.

Standard library only.
"""
from project_bootstrap.contracts import Denied

STATES = ('current', 'known', 'missing', 'customised', 'unreadable')
ACTIONS = ('current', 'migrate', 'manual', 'failed', 'excluded')


def classify(observed, target, known):
    """State of one released file. ``target`` is the package digest, ``known`` the published ones."""
    if observed in ('missing', 'unreadable'):
        return observed
    if (not isinstance(observed, tuple) or len(observed) != 2
            or observed[0] != 'digest' or not isinstance(observed[1], str)):
        raise Denied('invalid-observation')
    digest = observed[1]
    if digest == target:
        return 'current'
    if digest in known:
        return 'known'
    return 'customised'


def target(name, observed, package, known, package_digest, pointer_digest, problems=(), merges=0):
    """One row for one project.

    ``observed``: {path: observation} for every released file the tool looked
    at; ``package``: {path: digest} of the same files in the target package;
    ``known``: {path: set of published digests}; ``package_digest``: the
    target package's manifest digest; ``pointer_digest``: the package the
    project's pointer names, or None; ``problems``: reasons the
    tool already found (not a Git root, merge conflict, bad pointer, ...);
    ``merges``: how many mixed files the merge would change.
    """
    if set(observed) != set(package):
        raise Denied('observation-mismatch')
    files = {path: classify(observed[path], package[path], known.get(path, ()))
             for path in sorted(observed)}
    row = {'target': name, 'files': files, 'problems': list(problems)}
    unreadable = sorted(p for p, s in files.items() if s == 'unreadable')
    customised = sorted(p for p, s in files.items() if s == 'customised')
    if customised:
        row['compare'] = customised
    if row['problems'] or unreadable:
        row['problems'] += ['unreadable:' + p for p in unreadable]
        row['action'] = 'failed'
    elif customised:
        row['action'] = 'manual'
    elif (all(s == 'current' for s in files.values()) and not merges
          and pointer_digest is not None and pointer_digest == package_digest):
        row['action'] = 'current'
    else:
        row['action'] = 'migrate'
        row['replace'] = sorted(p for p, s in files.items() if s == 'known')
        row['add'] = sorted(p for p, s in files.items() if s == 'missing')
        row['merges'] = merges
    return row


def excluded(name, reason):
    return {'target': name, 'action': 'excluded', 'files': {}, 'problems': [reason]}


def failed(name, reason):
    return {'target': name, 'action': 'failed', 'files': {}, 'problems': [reason]}


def report(requested, rows):
    """Every requested target exactly once; a missing or repeated one is a failure."""
    by_name, out, seen = {}, [], set()
    for row in rows:
        if row.get('action') not in ACTIONS:
            raise Denied('invalid-row')
        by_name.setdefault(row['target'], []).append(row)
    for name in requested:
        if name in seen:
            out.append(failed(name, 'duplicate-target'))
            continue
        seen.add(name)
        found = by_name.get(name, [])
        out.append(found[0] if len(found) == 1 else
                   failed(name, 'no-result' if not found else 'several-results'))
    for name in sorted(set(by_name) - seen):
        out.append(failed(name, 'not-requested'))
    totals = {action: sum(r['action'] == action for r in out) for action in ACTIONS}
    return {'results': out, 'totals': totals, 'targets': len(out),
            'manual_prompts': totals['manual'],
            'ok': not totals['failed'] and not totals['manual']}
