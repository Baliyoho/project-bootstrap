"""F39 (wanted, one-off): find projects that edited the shared system in place.

``scan`` reads each listed project's installed copies of the released
(core／adapter) files and compares them with the manifest the project says it
installed (CRLF counts as LF, decision Q26). Each file is ok, edited,
missing or unreadable; a project whose
recorded manifest is unknown cannot be judged and is listed as such, never as
clean. Nothing is written or overwritten: an edited file is reported for a
person to look at, because the edit may be a project customisation that has
to be moved into a declared override rather than discarded.

This is an on-demand inventory over an explicit list, not a scheduled scan of
the whole disk.
"""
from pathlib import Path

from project_bootstrap import package


def scan(projects, manifests, owners):
    """``projects``: {name: (path, manifest version)}; ``manifests``: {version: manifest}."""
    report = []
    for name, (path, version) in sorted(projects.items()):
        manifest = manifests.get(version)
        if manifest is None:
            report.append({'project': name, 'state': 'unknown-manifest', 'files': {}})
            continue
        files = {}
        for relative, digest in sorted(manifest['components'].items()):
            if owners.get(relative) not in ('core', 'adapter'):
                continue
            target = Path(path) / relative
            try:
                data = target.read_bytes()
            except FileNotFoundError:
                files[relative] = 'missing'
                continue
            except OSError:
                files[relative] = 'unreadable'
                continue
            files[relative] = 'ok' if package.copy_digest(data) == digest else 'edited'
        states = set(files.values())
        state = ('edited' if 'edited' in states else 'incomplete' if states - {'ok'}
                 else 'clean' if files else 'nothing-to-check')
        report.append({'project': name, 'state': state, 'files': files})
    return report
