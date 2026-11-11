"""F12 prototype: registered parallel lines must not share a working tree or index.

A line is (line id, checkout path, branch). Two lines may run at once only if
each has its own working tree and its own index; a different branch name is
not enough, because a branch switch inside one shared tree drags the other
line's uncommitted files and staged entries along. Separate clones and
``git worktree`` checkouts both qualify.

Identity comes from Git, not from the path string: a subdirectory, a symlink
or a copied ``.git`` file pointing at another checkout's git dir all resolve
to the same tree or index. Detection only; nothing is locked or moved.
"""
import subprocess


def _facts(path, env):
    """(toplevel, index, branch) as Git sees them, or None if not a checkout."""
    def ask(*args):
        result = subprocess.run(['git', '-C', str(path), *args], capture_output=True,
                                env=env, timeout=30)
        return result.stdout.decode('utf-8', 'replace').strip() if result.returncode == 0 else None

    top = ask('rev-parse', '--show-toplevel')
    index = ask('rev-parse', '--path-format=absolute', '--git-path', 'index')
    if not top or not index:
        return None
    branch = ask('symbolic-ref', '--quiet', '--short', 'HEAD')
    # Git reports physical paths (symlinks resolved), so equal strings mean one tree.
    return top, index, branch


def assess_lines(lines, env=None):
    """``lines``: iterable of (line_id, path, branch). Every line is reported once."""
    rows, by_tree, by_index, by_branch, ids = [], {}, {}, {}, set()
    for line_id, path, branch in lines:
        row = {'line': line_id, 'path': str(path), 'branch': branch, 'codes': []}
        rows.append(row)
        if not isinstance(line_id, str) or not line_id or line_id in ids:
            row['codes'].append('duplicate-line')
        ids.add(line_id)
        facts = _facts(path, env)
        if facts is None:
            row['codes'].append('not-a-checkout')
            continue
        top, index, actual = facts
        if actual != branch:
            row['codes'].append('branch-mismatch')
        by_tree.setdefault(top, []).append(row)
        by_index.setdefault(index, []).append(row)
        by_branch.setdefault(branch, []).append(row)
    for groups, code in ((by_tree, 'shared-worktree'), (by_index, 'shared-index'),
                         (by_branch, 'shared-branch')):
        for members in groups.values():
            if len(members) > 1:
                for row in members:
                    row['codes'].append(code)
    for row in rows:
        row['ok'] = not row['codes']
    return {'ok': bool(rows) and all(row['ok'] for row in rows), 'lines': rows}
