"""M2 fact adapters for F20: what a document says versus what Git and files show.

A claim names its document, the proposition in words, an adapter and the
expected value. Each claim ends as 一致, 不一致 (with document, proposition,
expected and observed) or 未知. An adapter the caller did not authorise, an
unknown adapter or a failed query is 未知: not being able to check is never
counted as agreement. ``handoff_claims`` lifts the checkable fields out of a
HANDOFF snapshot so the real document format is exercised, not a stand-in.

Read-only queries; services and credentials are out of scope here.
"""
from pathlib import Path
import re
import subprocess


def _git(repo, env, *args):
    result = subprocess.run(['git', '--no-optional-locks', '-C', str(repo), *args],
                            capture_output=True, env=env, timeout=30)
    if result.returncode:
        raise LookupError('git query failed')
    return result.stdout.decode('utf-8', 'replace').strip()


def _inside(repo, relative):
    if (not isinstance(relative, str) or not relative or relative.startswith('/')
            or '..' in relative.split('/')):
        raise LookupError('path outside repository')
    return Path(repo) / relative


ADAPTERS = {
    'git.branch': lambda repo, env, args: _git(repo, env, 'symbolic-ref', '--short', 'HEAD'),
    'git.clean': lambda repo, env, args: _git(repo, env, 'status', '--porcelain') == '',
    'file.exists': lambda repo, env, args: _inside(repo, args['path']).is_file(),
    'file.text': lambda repo, env, args: _inside(repo, args['path']).read_text(
        encoding='utf-8').strip(),
}


def check_claims(repo, claims, allowed, env=None):
    rows = []
    for claim in claims:
        row = {'doc': claim.get('doc'), 'proposition': claim.get('proposition'),
               'expected': claim.get('expected')}
        adapter = ADAPTERS.get(claim.get('fact'))
        if adapter is None:
            row.update(state='未知', reason='no-adapter')
        elif claim['fact'] not in allowed:
            row.update(state='未知', reason='not-authorized')
        else:
            try:
                observed = adapter(repo, env, claim.get('args') or {})
            except (LookupError, OSError, KeyError, UnicodeDecodeError,
                    subprocess.TimeoutExpired):
                row.update(state='未知', reason='query-failed')
            else:
                row['observed'] = observed
                row.update(state='一致' if observed == claim.get('expected') else '不一致',
                           reason='compared')
        rows.append(row)
    states = {row['state'] for row in rows}
    overall = ('不一致' if '不一致' in states else '未知' if '未知' in states or not rows
               else '一致')
    return {'overall': overall, 'rows': rows}


_FIELD = r'^- \*\*{}\*\*：`([^`]+)`'


def handoff_claims(text, doc='HANDOFF.md'):
    """Checkable claims in a HANDOFF snapshot; a missing field yields no claim."""
    claims = []
    version = re.search(_FIELD.format('骨架版本'), text, re.MULTILINE)
    if version:
        claims.append({'doc': doc, 'proposition': f'骨架版本是 {version.group(1)}',
                       'fact': 'file.text', 'args': {'path': 'VERSION'},
                       'expected': version.group(1)})
    branch = re.search(_FIELD.format('待續分支'), text, re.MULTILINE)
    if branch:
        claims.append({'doc': doc, 'proposition': f'待續分支是 {branch.group(1)}',
                       'fact': 'git.branch', 'expected': branch.group(1)})
    return claims
