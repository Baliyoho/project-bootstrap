"""F16a: can a clean second machine pick up from the repository alone?

``clone`` makes the second machine's checkout with a plain ``git clone`` of one
branch: only committed files travel. Untracked or ignored files, and anything
outside the repository on the first machine (a global skill copy, a probe kept
in a chat), are absent, which is the point.

``check`` follows the entry document's start-of-work section the way a new
agent would, with ``home`` standing in for that machine's home directory (an
empty folder for a clean machine):

- every ``~/...`` path and in-repo Markdown link in the section is a
  candidate; a candidate holds the procedure when it exists and has the
  marker line (``name: handoff`` by default, the skill's frontmatter);
- the procedure must be reachable from the repository itself: a home copy
  is a convenience the new machine does not have yet;
- every in-repo link the section names must exist in the checkout; one that
  exists only in the first machine's working tree is a private attachment;
- reachable copies whose ``source:`` markers differ are listed as drift.

The result is 通過, 不通過 with the reasons, or 未知 when the entry document
or its section cannot be read. It is detection only: nothing is installed,
copied between machines or written.
"""
import re
import subprocess
from pathlib import Path

LINK = re.compile(r'\[[^\]]*\]\(([^)\s]+)\)')
HOME_PATH = re.compile(r'`(~/[^`\s]+)`')
SOURCE = re.compile(r'<!-- source: (\S+ v[0-9][0-9.-]*)')
MARKER = re.compile(r'^name: handoff$', re.M)


def clone(repo, dest, branch):
    subprocess.run(['git', 'clone', '-q', '--no-hardlinks', '--single-branch', '--branch',
                    branch, str(repo), str(dest)], check=True, capture_output=True)
    return Path(dest)


def _section(text, heading):
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r'(#+) ', line)
        if match and heading in line:
            depth = len(match.group(1))
            body = []
            for rest in lines[index + 1:]:
                other = re.match(r'(#+) ', rest)
                if other and len(other.group(1)) <= depth:
                    break
                body.append(rest)
            return '\n'.join(body)
    return None


def _candidates(section):
    found = []
    for path in HOME_PATH.findall(section):
        found.append(('home', path))
    for target in LINK.findall(section):
        if re.match(r'[a-z]+:', target) or target.startswith('#'):
            continue
        found.append(('repo', target.split('#')[0]))
    seen, unique = set(), []
    for item in found:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def check(root, home, entry='AGENTS.md', heading='開工第一件事', marker=MARKER, first=None):
    """``first``: the first machine's working tree, to name private attachments."""
    root, home = Path(root), Path(home)
    try:
        text = (root / entry).read_text(encoding='utf-8')
    except OSError:
        return {'result': '未知', 'reasons': ['entry-unreadable']}
    section = _section(text, heading)
    if section is None:
        return {'result': '未知', 'reasons': ['section-missing']}
    procedures, missing, private = [], [], []
    for kind, path in _candidates(section):
        location = home / path[2:] if kind == 'home' else root / path
        try:
            content = location.read_text(encoding='utf-8') if location.is_file() else None
        except OSError:
            content = None
        if kind == 'repo' and content is None and not location.is_dir():
            if first is not None and (Path(first) / path).exists():
                private.append(path)
            else:
                missing.append(path)
        found = marker.search(content) if content is not None else None
        if found:
            # The package holds several marked templates; take the one after the procedure's.
            source = SOURCE.search(content, found.end())
            procedures.append({'kind': kind, 'path': path,
                               'source': source.group(1) if source else None})
    in_repo = [p for p in procedures if p['kind'] == 'repo']
    reasons = []
    if not in_repo:
        reasons.append('procedure-not-in-repo')
    if missing:
        reasons.append('required-missing')
    if private:
        reasons.append('private-attachment')
    drift = sorted({p['source'] for p in procedures if p['source']})
    return {'result': '不通過' if reasons else '通過', 'reasons': reasons,
            'procedures': procedures, 'missing': missing, 'private': private,
            'drift': drift if len(drift) > 1 else []}
