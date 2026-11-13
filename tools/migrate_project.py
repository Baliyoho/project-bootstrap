#!/usr/bin/env python3
"""Move old copy-based projects onto the package and a pointer (P2 slice 5, decision Q25).

    python3 -X utf8 tools/migrate_project.py ../SOME_PROJECT              # dry run, one project
    python3 -X utf8 tools/migrate_project.py --inventory PRIVATE.json      # dry run, listed projects
    python3 -X utf8 tools/migrate_project.py --all --root DIR              # dry run, one level under DIR
    python3 -X utf8 tools/migrate_project.py ../SOME_PROJECT --write --owner '<工作中欄位完整值>' \\
        --archive X.tar.gz --record X.record.json --signature X.sig \\
        --channel beta --source https://github.com/OWNER/REPO.git --cache DIR

A dry run reads and writes nothing in the projects: no fetch, no index
refresh (``git --no-optional-locks``). It compares every released file with
the target package and with every version this repository has published, and
prints one row per target. ``--json FILE`` also saves the report; keep that
file private, it names real projects.

A project with a customised shared file stops (Q25 (a)): nothing is written
there and it needs one manual comparison. ``--write`` takes one project only,
after A1–A5 in that project (the same owner check as ``sync_project.py``):
it verifies the signed release into the cache, replaces known old copies, adds
missing released files, merges the mixed files keeping the project's own
parts, writes the pointer and checks the result. It does not commit or push.

``sync_project.py`` stays the current sync tool until the switch is decided;
this tool reuses its merges, history scan and owner check instead of a copy.
"""
import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import types

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tools'))

import build_package  # noqa: E402
import install_package  # noqa: E402
import sync_project as sp  # noqa: E402
from project_bootstrap import channel, distribute, migrate, package, pointer  # noqa: E402
from project_bootstrap.contracts import Denied  # noqa: E402

RELEASED = sp.WHOLE + (sp.SURGICAL,)
MIXED = sp.WIRING + sp.PARTIAL


def observe(project, rel):
    """What the migrator saw for one released file: ('digest', d), 'missing' or 'unreadable'."""
    path = project / rel
    if path.is_symlink():
        return 'unreadable'
    if not path.exists():
        return 'missing'
    try:
        data = path.read_bytes()
        if rel != sp.SURGICAL:
            return ('digest', package.copy_digest(data))  # CRLF counts as LF (Q26 (a))
        text = data.decode('utf-8').replace('\r\n', '\n')
    except (OSError, UnicodeDecodeError):
        return 'unreadable'
    try:
        return ('digest', sp.shared_digest(rel, text))
    except ValueError:
        # The shared region cannot be found: nobody published that shape.
        return ('digest', 'unsplit:' + hashlib.sha256(data).hexdigest())


def package_digests(folder, manifest):
    out = {}
    for rel in RELEASED:
        if rel == sp.SURGICAL:
            out[rel] = sp.shared_digest(rel, sp.read(folder / rel))
        else:
            out[rel] = manifest['components'][rel]
    return out


def read_pointer(project):
    path = project / pointer.POINTER
    if not path.exists():
        return None, []
    try:
        data = pointer.parse(path.read_text(encoding='utf-8'))
    except (Denied, OSError, UnicodeDecodeError):
        return None, ['invalid-pointer']
    return data['installed'], (['pointer-exception'] if data['exception'] is not None else [])


def git_quiet(project, *args):
    r = subprocess.run(['git', '--no-optional-locks', '-C', str(project), *args],
                       capture_output=True, encoding='utf-8', errors='replace')
    return r.stdout if r.returncode == 0 else None


def busy_notes(project):
    notes = []
    status = git_quiet(project, 'status', '--porcelain')
    if status is None:
        notes.append('git-status-failed')
    elif status.strip():
        notes.append('dirty')
    handoff = sp.read(project / 'HANDOFF.md') or ''
    fields = [l.split('：', 1)[-1].strip() for l in handoff.splitlines() if l.startswith('- **工作中**：')]
    if fields != ['無（已交棒）']:
        notes.append('busy-or-no-field')
    return notes


def assess(project, folder, manifest, known):
    """Row for one project plus the sync plan that would merge its mixed files."""
    observed = {rel: observe(project, rel) for rel in RELEASED}
    installed, problems = read_pointer(project)
    plan = sp.sync(project, folder)
    problems += ['merge:' + e for e in plan.errors]
    merges = [(path, text, rel) for path, text, rel in plan.writes if rel in MIXED]
    row = migrate.target(str(project), observed, package_digests(folder, manifest), known,
                         package.digest(manifest), installed, problems, len(merges))
    row['notes'] = [m.strip() for m in plan.msgs if 'MIGRATE' in m or 'EXTRA' in m]
    row['notes'] += ['crlf:' + rel for rel in RELEASED if crlf(project / rel)]
    return row, merges


def crlf(path):
    """Shown, not decisive: the comparison counts CRLF as LF (Q26 (a))."""
    try:
        return not path.is_symlink() and path.is_file() and b'\r\n' in path.read_bytes()
    except OSError:
        return False


def decisions(args):
    if args.inventory:
        return sp.inventory_decisions(args.inventory.resolve())
    if args.all:
        return sp.discover_decisions(args.root, args.exclude)
    return [(pathlib.Path(args.project).resolve(), None)]


def target_package(args):
    """(folder, manifest, cleanup folder). Dry run builds a debug package unless an archive is given."""
    if args.archive:
        work = tempfile.mkdtemp(prefix='migrate-package-')
        folder = distribute.unpack(args.archive, work)
    else:
        folder, _ = build_package.build_once()
        work = folder
    manifest = json.loads((pathlib.Path(folder) / package.MANIFEST).read_text(encoding='utf-8'))
    return pathlib.Path(folder), manifest, work


def dry_run(args):
    folder, manifest, work = target_package(args)
    try:
        known = sp.published_hashes(folder)
        rows, requested = [], []
        for project, reason in decisions(args):
            name = str(project)
            requested.append(name)
            if reason and reason.startswith('inventory active 無法處理：'):
                rows.append(migrate.failed(name, reason))
            elif reason:
                rows.append(migrate.excluded(name, reason))
            elif project == ROOT:
                rows.append(migrate.failed(name, 'authority-repo'))
            elif not project.is_dir():
                rows.append(migrate.failed(name, 'not-found'))
            elif sp.target_reason(project):
                rows.append(migrate.failed(name, sp.target_reason(project)))
            else:
                try:
                    row, _ = assess(project, folder, manifest, known)
                    row['notes'] = busy_notes(project) + row['notes']
                except (Denied, OSError, ValueError) as exc:
                    row = migrate.failed(name, 'error:' + str(exc))
                rows.append(row)
        result = migrate.report(requested, rows)
        result['package'] = {'digest': package.digest(manifest), 'release': manifest.get('release'),
                             'version': manifest.get('version')}
        return result
    finally:
        shutil.rmtree(work, ignore_errors=True)


def write_one(args, run=None):
    """Migrate one project. Returns the row; raises Denied before any project write when refused."""
    project = pathlib.Path(args.project).resolve()
    if project == ROOT:
        raise Denied('authority-repo')
    reason = sp.target_reason(project)
    if reason:
        raise Denied('target:' + reason)
    if sp.git_output(project, 'status', '--porcelain'):
        raise Denied('dirty')
    try:
        head = sp.sync_owner_check(project, args.owner, True)
    except ValueError as exc:
        raise Denied('owner:' + str(exc)) from None
    keys, _ = install_package.trusted_keys(project, args.cache, install_package.KEYS.read_text(encoding='utf-8'))
    document = pathlib.Path(args.record).read_bytes()
    signature = pathlib.Path(args.signature).read_bytes()
    if channel.parse_record(document)['channel'] != args.channel:
        raise Denied('wrong-channel')
    work = tempfile.mkdtemp(prefix='migrate-write-')
    try:
        folder = pathlib.Path(distribute.unpack(args.archive, work))
        # Signature first: the files compared and copied below come from a verified release.
        # This writes only the cache, never the project.
        fields = channel.install(args.cache, folder, document, signature, keys)
        manifest = json.loads((folder / package.MANIFEST).read_text(encoding='utf-8'))
        if fields['manifest'] != package.digest(manifest):
            raise Denied('record-mismatch')
        known = sp.published_hashes(folder)
        row, merges = assess(project, folder, manifest, known)
        if row['action'] not in ('migrate', 'current'):
            raise Denied('%s:%s' % (row['action'], ','.join(row.get('compare') or row['problems'])))
        writes = list(merges)
        for rel in row.get('replace', []) + row.get('add', []):
            writes.append((project / rel, sp.read(folder / rel), rel))
        try:
            if sp.sync_owner_check(project, args.owner, True) != head:
                raise Denied('owner:remote-moved')
        except ValueError as exc:
            raise Denied('owner:' + str(exc)) from None
        plan = types.SimpleNamespace(writes=writes)
        done, failed = sp.apply_plan(plan)
        for rel in row.get('add', []):
            if rel in done and rel in manifest.get('executable', ()):
                os.chmod(project / rel, 0o755)
        row['applied'] = done
        if failed:
            row['action'] = 'failed'
            row['problems'].append('write-failed:%s:%s' % failed)
            return row
        distribute.write_pointer(project, args.channel, fields['manifest'], args.source)
        pointer.check_components(project, manifest)
        row['pointer'] = fields['manifest']
        return row
    finally:
        shutil.rmtree(work, ignore_errors=True)


def show(result):
    for row in result['results']:
        print('%-8s %s' % (row['action'].upper(), row['target']))
        for key in ('replace', 'add', 'compare', 'problems', 'notes'):
            if row.get(key):
                print('         %s: %s' % (key, ', '.join(row[key])))
        if row.get('merges'):
            print('         merges: %d' % row['merges'])
    t = result['totals']
    print('\n%d targets: %s；人工比對 %d 次；%s' % (
        result['targets'], '、'.join('%s %d' % (k, v) for k, v in t.items()),
        result['manual_prompts'], 'ok' if result['ok'] else 'NOT ok'))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('project', nargs='?')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--root', action='append', type=pathlib.Path)
    ap.add_argument('--exclude', action='append', default=[])
    ap.add_argument('--inventory', type=pathlib.Path)
    ap.add_argument('--json', type=pathlib.Path, help='also save the report here (keep it private)')
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--owner')
    for name in ('archive', 'record', 'signature', 'channel', 'source', 'cache'):
        ap.add_argument('--' + name)
    args = ap.parse_args(argv)
    if sum(bool(x) for x in (args.project, args.all, args.inventory)) != 1:
        ap.error('project、--all、--inventory 必須擇一')
    if (args.root or args.exclude) and not args.all:
        ap.error('--root／--exclude 必須搭配 --all')
    if args.write:
        missing = [n for n in ('owner', 'archive', 'record', 'signature', 'channel', 'source', 'cache')
                   if not getattr(args, n)]
        if not args.project or missing:
            ap.error('--write 只能單一專案，並且要 --' + '、--'.join(missing or ['owner']))
        try:
            row = write_one(args)
        except (Denied, OSError, ValueError) as exc:
            print('migrate_project: 拒絕，專案沒有被改：' + str(exc))
            return 1
        print(json.dumps(row, ensure_ascii=False, indent=1, sort_keys=True))
        print('還沒 commit：到專案照 B 模式收尾。' if row['action'] != 'failed' else
              '寫到一半失敗：上面 applied 是已經改的檔。')
        return 0 if row['action'] != 'failed' else 1
    try:
        result = dry_run(args)
    except (Denied, OSError, ValueError) as exc:
        print('migrate_project: ' + str(exc))
        return 2
    show(result)
    if args.json:
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=1, sort_keys=True) + '\n',
                             encoding='utf-8')
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
