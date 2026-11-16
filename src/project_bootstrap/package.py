"""P2 slice 1: the formal package format (D7／F36, toward F18／F32).

A package is a folder with one file per deployed path plus ``manifest.json``.
The manifest says, for every file, who owns it and how an update may touch it,
so a project's own content is kept and an unknown file stops the build:

- ``core``: shared system content (skill, the two hook scripts). ``whole``
  files are replaced as a whole; ``region`` means only a marked region of a
  file that also holds project settings (check_docs.py).
- ``adapter``: platform wiring. ``whole`` files, or only the package's own
  entries inside a project file (``wiring`` hook groups, a ``key``).
- ``project``: the project's file. ``seed`` is written once at install;
  ``lines`` means the package only adds named lines or fields.

The ownership table is ``src/kit/owners.json``. Every template must have an
entry and every entry a template; otherwise the build stops instead of
guessing (F36: unknown ownership stops).

A build is reproducible: same source, same bytes, same manifest digest. It
reuses ``release.build_manifest`` for component digests, so the write gate
prototype can read the result. Builds made here are ``debug``; a ``formal``
package only comes out of the publish step (P2 slice 3), never from this
module.

Standard library only, like the rest of what A4 runs.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile

from project_bootstrap import capabilities
from project_bootstrap.contracts import Denied
from project_bootstrap.release import build_manifest, manifest_digest

MANIFEST = 'manifest.json'
OWNERS = {'core': {'whole', 'region'},
          'adapter': {'whole', 'wiring', 'key'},
          'project': {'seed', 'lines'}}
EXECUTABLE_SUFFIX = '.sh'
# Windows 沒有 POSIX 執行位元：os.chmod 只認唯讀旗標，Git 取出的檔案一律沒有 x，
# 連「設了又讀回來」都辦不到。所以這一項在本平台不適用——不是放寬守門：POSIX 上
# 的判準一字未改，Windows 上則是檔案系統記不住這件事，查了也只會永遠判錯。
# 2026-11-16（本 repo AGENTS「Windows 的 exit 2 要用哪種解法」）：選平台感知，
# 不做預期失敗清單；清單會隨文件內容漂移，基線不穩（39→45 只因改了一行 HANDOFF）。
RECORDS_EXECUTE_BIT = os.name != 'nt'
VERSION_RE = re.compile(r'^> 版本：\*\*([0-9]{4}-[0-9]{2}-[0-9]{2}(?:\.[0-9]+)?)\*\*', re.M)


def load_owners(text):
    """Parse owners.json text into {path: {'owner', 'update'}}, or Denied."""
    try:
        data = json.loads(text)
    except ValueError:
        raise Denied('invalid-owners') from None
    if not isinstance(data, dict) or set(data) != {'schema', 'files'} or data['schema'] != 1:
        raise Denied('invalid-owners')
    files = data['files']
    if not isinstance(files, dict) or not files:
        raise Denied('invalid-owners')
    for path, entry in files.items():
        if not isinstance(entry, dict) or set(entry) != {'owner', 'update'}:
            raise Denied('invalid-owner:' + path)
        if entry['owner'] not in OWNERS or entry['update'] not in OWNERS[entry['owner']]:
            raise Denied('invalid-owner:' + path)
    return files


def kit_version(prose):
    match = VERSION_RE.search(prose)
    if not match:
        raise Denied('no-version-line')
    return match.group(1)


def contents(files, owners):
    """{deploy path: bytes}; every template owned, every owner backed by a template."""
    unowned = sorted(set(files) - set(owners))
    if unowned:
        raise Denied('unknown-owner:' + ','.join(unowned))
    orphan = sorted(set(owners) - set(files))
    if orphan:
        raise Denied('owner-without-file:' + ','.join(orphan))
    if MANIFEST in files:
        raise Denied('reserved-path:' + MANIFEST)
    return {path: text.encode('utf-8') for path, text in files.items()}


def _write(root, relative, data):
    path = Path(root) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'xb') as handle:
        handle.write(data)
    path.chmod(0o755 if relative.endswith(EXECUTABLE_SUFFIX) else 0o644)


def build(prose, files, owners, kit_text, matrix=None):
    """Write a debug package into a fresh temporary folder; return (folder, manifest).

    ``kit_text`` is the built PROJECT-BOOTSTRAP.md, recorded by digest so a
    package can be traced to the document generated from the same source.
    ``matrix`` is the capability matrix (``src/kit/capabilities.json``). It goes
    into the manifest, so the manifest digest, and with it the release
    signature, covers it; it is not a file deployed into projects.
    """
    version = kit_version(prose)
    data = contents(files, owners)
    if matrix is not None:
        try:
            capabilities.validate(matrix)
        except capabilities.MatrixError:
            raise Denied('invalid-capabilities') from None
    folder = tempfile.mkdtemp(prefix='bootstrap-package-')
    try:
        os.chmod(folder, 0o755)
        for relative in sorted(data):
            _write(folder, relative, data[relative])
        manifest = build_manifest(folder, data, version, 'debug')
        manifest['owners'] = {path: dict(owners[path]) for path in sorted(data)}
        manifest['executable'] = sorted(p for p in data if p.endswith(EXECUTABLE_SUFFIX))
        manifest['kit'] = hashlib.sha256(kit_text.encode('utf-8')).hexdigest()
        if matrix is not None:
            manifest['capabilities'] = matrix
        _write(folder, MANIFEST, _dump(manifest))
    except BaseException:
        force_rmtree(folder, ignore_errors=True)
        raise
    return folder, manifest


def _dump(manifest):
    return (json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True) + '\n').encode('utf-8')


def check(folder):
    """List what is wrong with a package folder; empty means it matches its manifest."""
    root = Path(folder)
    try:
        manifest = json.loads((root / MANIFEST).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return ['manifest-unreadable']
    if not isinstance(manifest, dict) or not isinstance(manifest.get('components'), dict):
        return ['manifest-invalid']
    problems = []
    components = manifest['components']
    owners = manifest.get('owners')
    if not isinstance(owners, dict) or set(owners) != set(components):
        problems.append('owners-mismatch')
    else:
        for path, entry in sorted(owners.items()):
            if (not isinstance(entry, dict) or set(entry) != {'owner', 'update'}
                    or entry['owner'] not in OWNERS
                    or entry['update'] not in OWNERS[entry['owner']]):
                problems.append('invalid-owner:' + path)
    if 'capabilities' in manifest:
        try:
            capabilities.validate(manifest['capabilities'])
        except capabilities.MatrixError:
            problems.append('capabilities-invalid')
    present = set()
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            problems.append('symlink:' + relative)
        elif path.is_file() and relative != MANIFEST:
            present.add(relative)
    for relative in sorted(present - set(components)):
        problems.append('extra:' + relative)
    executable = set(manifest.get('executable') or ())
    for relative, digest in sorted(components.items()):
        path = root / relative
        if relative not in present:
            problems.append('missing:' + relative)
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            problems.append('digest:' + relative)
        if RECORDS_EXECUTE_BIT:
            runnable = bool(stat.S_IMODE(path.stat().st_mode) & 0o111)
            if runnable != (relative in executable):
                problems.append('mode:' + relative)
    return problems


def force_rmtree(path, ignore_errors=False):
    """``shutil.rmtree`` that also removes read-only files.

    Git marks everything under ``.git/objects`` read-only, and Windows refuses
    to delete a read-only file: 2026-11-16 on Windows this raised
    ``PermissionError [WinError 5]`` in 15 teardowns of the surface tests and
    twice in ``install``, which failed runs that had otherwise passed. POSIX
    allows the delete (the directory's write bit is what counts), so this only
    changes what happens on Windows.
    """
    def retry(func, target, exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            if not ignore_errors:
                raise
    shutil.rmtree(path, onexc=retry)

def install(folder, out):
    """Move a checked package to ``out``. ``out`` must be absent or an earlier package."""
    problems = check(folder)
    if problems:
        raise Denied('bad-package:' + ','.join(problems))
    target = Path(out)
    if target.is_symlink():
        raise Denied('out-is-symlink')
    if target.exists():
        if not (target / MANIFEST).is_file():
            raise Denied('out-not-a-package')
        if not _only_package_files(target):
            raise Denied('out-has-other-files')
        force_rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    os.replace(folder, target)
    return target


def _only_package_files(folder):
    """An edited earlier package may be replaced; one holding foreign files may not."""
    root = Path(folder)
    try:
        manifest = json.loads((root / MANIFEST).read_text(encoding='utf-8'))
        known = set(manifest['components']) | {MANIFEST}
    except (OSError, ValueError, KeyError, TypeError):
        return False
    return all(p.relative_to(root).as_posix() in known
               for p in root.rglob('*') if p.is_file() or p.is_symlink())


def whole_owned(manifest):
    """{path: owner} for whole core／adapter files: what inventory and bypass compare."""
    return {path: entry['owner'] for path, entry in manifest['owners'].items()
            if entry['owner'] in ('core', 'adapter') and entry['update'] == 'whole'}


def digest(manifest):
    return manifest_digest(manifest)


def copy_digest(data):
    """Digest of a project's copy of a package file, with CRLF counted as LF (decision Q26 (a)).

    A project's ``.gitattributes`` may make Git check text files out with CRLF
    (``*.cmd eol=crlf``); writing LF would only last until the next checkout.
    The content is what is compared, not the line endings. A lone CR is still
    a difference. The package itself (``check``) is still compared byte for byte.
    """
    return hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()
