"""P2 slice 3b prep: what the release and install command lines need (Q21).

``tools/release_package.py`` (run by CI) and ``tools/install_package.py`` (run
by a person) only wire these pieces together, so everything that can refuse
lives here and is tested here:

- ``report_from_verifier``: turn the verifier's own output and exit code into
  the evidence report ``channel.release`` requires. Every check line becomes
  a claim and the overall line is always claimed, so a failed, skipped or
  missing check keeps the report from passing.
- ``load_keys``: the committed key file (one ``ssh-ed25519`` key per line;
  ``#`` comments and blank lines ignored). No key refuses.
- ``next_epoch``: one past the newest channel tag, or 1 for an empty channel.
- ``report_bytes``: the report published next to a release. Its SHA-256 is
  the ``report`` field of the signed record, so anyone can check that the
  uploaded report is the one CI signed.
- ``pack``／``unpack``: a release asset is a tar.gz of the formal package.
  Packing is byte-for-byte reproducible; unpacking refuses absolute paths,
  ``..``, links, devices and anything outside one ``package/`` folder.
- ``seed``: put a package into an empty project folder (first install).
- ``write_pointer``: point a project at the installed package. A declared D4
  exception pins the old package, so it must be removed by a person first.
"""
import gzip
import io
import json
from pathlib import Path
import shutil
import tarfile
import time

from project_bootstrap import channel, evidence, ingest, package, pointer
from project_bootstrap.contracts import Denied

ROOT_NAME = 'package'
MTIME = 0


def report_from_verifier(text, exit_code, commit, round_id, now=None):
    """Evidence report for one verifier run on ``commit``, all rows from this round."""
    meta = {'round': round_id, 'command': 'python3 -X utf8 tools/verify_bootstrap.py',
            'commit': commit, 'scope': 'release',
            'acquired_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now)),
            'depends': {'commit': commit}}
    records = ingest.from_bootstrap(text, exit_code, meta)
    claims = [r['claim'] for r in records if r['claim'] != 'verify_bootstrap'] + ['verify_bootstrap']
    return evidence.resolve(claims, records, lambda name: None, round_id)


def load_keys(text):
    keys = [line.strip() for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith('#')]
    if not keys:
        raise Denied('no-release-keys')
    for key in keys:
        if not channel.KEY_RE.fullmatch(key):
            raise Denied('invalid-release-key')
    return sorted(set(keys))


def next_epoch(tags):
    if not tags:
        return 1
    return channel.newest(tags)[0] + 1


def asset_names(channel_name, epoch, digest):
    stem = '%s-%d-%s' % (channel_name, epoch, digest[:12])
    return {'package': stem + '.tar.gz', 'record': stem + '.record.json', 'signature': stem + '.sig',
            'report': stem + '.report.json'}


def report_bytes(report):
    """The report as published: the same canonical JSON whose SHA-256 the signed record carries."""
    return json.dumps(report, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')


def pack(folder, out):
    """Reproducible tar.gz of a package folder, under one top folder named ``package``."""
    root = Path(folder)
    if package.check(root):
        raise Denied('bad-package')
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w', format=tarfile.PAX_FORMAT) as tar:
        names = sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file())
        dirs = sorted({'/'.join(n.split('/')[:i]) for n in names for i in range(1, n.count('/') + 1)})
        for name in [None] + dirs:
            info = tarfile.TarInfo(ROOT_NAME if name is None else ROOT_NAME + '/' + name)
            info.type, info.mode, info.mtime = tarfile.DIRTYPE, 0o755, MTIME
            tar.addfile(info)
        for name in names:
            data = (root / name).read_bytes()
            info = tarfile.TarInfo(ROOT_NAME + '/' + name)
            info.size, info.mtime = len(data), MTIME
            info.mode = 0o755 if (root / name).stat().st_mode & 0o111 else 0o644
            tar.addfile(info, io.BytesIO(data))
    with open(out, 'wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=MTIME) as zipped:
            zipped.write(buffer.getvalue())
    return Path(out)


def unpack(archive, dest):
    """Extract a release asset into ``dest``/package and check it; Denied on anything unexpected."""
    dest = Path(dest)
    try:
        tar = tarfile.open(archive, mode='r:gz')
    except (OSError, tarfile.TarError, EOFError):
        raise Denied('invalid-archive') from None
    with tar:
        try:
            members = tar.getmembers()
        except (OSError, tarfile.TarError, EOFError):
            raise Denied('invalid-archive') from None
        names = [member.name for member in members]
        if len(set(names)) != len(names):
            raise Denied('unsafe-archive-path:duplicate')
        for member in members:
            parts = member.name.split('/')
            # A leading '/' leaves an empty first part, so the ROOT_NAME test covers absolute paths.
            if ('\\' in member.name or parts[0] != ROOT_NAME
                    or any(part in ('', '.', '..') for part in parts)):
                raise Denied('unsafe-archive-path:' + member.name)
            if not (member.isfile() or member.isdir()):
                raise Denied('unsafe-archive-member:' + member.name)
        for member in members:
            target = dest.joinpath(*member.name.split('/'))
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as source, open(target, 'xb') as handle:
                shutil.copyfileobj(source, handle)
            target.chmod(0o755 if member.mode & 0o111 else 0o644)
    folder = dest / ROOT_NAME
    problems = package.check(folder)
    if problems:
        raise Denied('bad-package:' + ','.join(problems))
    return folder


def seed(project, folder):
    """Copy every package file into an empty or missing project folder."""
    project = Path(project)
    if project.exists() and any(project.iterdir()):
        raise Denied('project-not-empty')
    manifest = json.loads((Path(folder) / package.MANIFEST).read_text(encoding='utf-8'))
    for relative in sorted(manifest['components']):
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(folder) / relative, target)
    return sorted(manifest['components'])


def write_pointer(project, channel_name, digest, source):
    """Write or update the pointer; an existing exception stops the update."""
    path = Path(project) / pointer.POINTER
    if path.exists():
        current = pointer.parse(path.read_text(encoding='utf-8'))
        if current['exception'] is not None:
            raise Denied('exception-present')
    data = {'schema': 1, 'channel': channel_name, 'installed': digest, 'exception': None,
            'source': source}
    text = json.dumps(data, indent=1, sort_keys=True) + '\n'
    pointer.parse(text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return data
