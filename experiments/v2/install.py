"""F17: getting the system into a new or existing project with a dry run first.

``plan`` looks at a target folder and the package (``{relative path: bytes}``)
and lists one action per package file, writing nothing:

- create: the file does not exist yet;
- same: an identical file is already there;
- append: ``.gitignore`` exists; only its missing lines would be added, in
  package order, and nothing already there is removed or reordered;
- keep: any other existing file with different content (a project README,
  an AGENTS.md the project wrote). It is never overwritten; the person
  decides what to merge, and the plan says so.

It also refuses a target that is a home directory or the filesystem root,
and flags an existing project (Git history or non-package files present) so
the caller asks before touching it, as the bootstrap procedure requires.

``apply`` performs exactly a plan the caller approved: it re-plans, refuses
if anything changed since, then creates and appends only. Existing bytes of
every file are preserved; the result lists what it changed.
"""
import os
from pathlib import Path

from experiments.v2.contracts import Denied

APPEND_ONLY = {'.gitignore'}


def _safe(relative):
    parts = relative.split('/')
    if not relative or relative.startswith('/') or '\\' in relative or any(
            p in ('', '.', '..') for p in parts):
        raise Denied('invalid-package-path')
    return relative


def plan(target, package, home=None):
    target = Path(target).resolve()
    home = Path(home if home is not None else os.path.expanduser('~')).resolve()
    if target in (home, Path(target.anchor)):
        raise Denied('refuse-home-or-root')
    if not target.is_dir():
        raise Denied('target-missing')
    actions = []
    for relative in sorted(package):
        path = target / _safe(relative)
        if path.is_symlink() or (path.exists() and not path.is_file()):
            actions.append({'path': relative, 'action': 'keep', 'why': 'not-a-regular-file'})
            continue
        if not path.exists():
            actions.append({'path': relative, 'action': 'create'})
            continue
        current = path.read_bytes()
        if current == package[relative]:
            actions.append({'path': relative, 'action': 'same'})
        elif relative in APPEND_ONLY:
            have = set(current.decode('utf-8', 'replace').splitlines())
            missing = [line for line in package[relative].decode('utf-8').splitlines()
                       if line and line not in have]
            actions.append({'path': relative, 'action': 'append' if missing else 'same',
                            'lines': missing})
        else:
            actions.append({'path': relative, 'action': 'keep', 'why': 'project-content'})
    others = sorted(p.name for p in target.iterdir() if p.name not in {
        r.split('/')[0] for r in package})
    # Anything that is not a package file, .git included, means an existing project.
    return {'target': str(target), 'existing_project': bool(others), 'other_entries': others,
            'actions': actions}


def apply(target, package, approved, home=None):
    """Carry out ``approved`` only if a fresh plan is identical to it."""
    current = plan(target, package, home=home)
    if current != approved:
        raise Denied('plan-changed')
    root = Path(current['target'])
    changed = []
    for item in current['actions']:
        path = root / item['path']
        if item['action'] == 'create':
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as handle:
                handle.write(package[item['path']])
            changed.append(item['path'])
        elif item['action'] == 'append':
            before = path.read_bytes()
            text = ('' if before.endswith(b'\n') or not before else '\n') + ''.join(
                line + '\n' for line in item['lines'])
            with path.open('ab') as handle:
                handle.write(text.encode('utf-8'))
            changed.append(item['path'])
    return changed
