#!/usr/bin/env python3
"""Build bootstrap.py from its source in src/kit/ (P1 slice 3, 2026-11-11; v3 Q49, Q50).

Source layout:
- src/kit/kit.md: the deployment package's prose. Inside a section 3.x fenced
  block, a single line ``<!-- kit-file: <deploy path> -->`` stands for the body.
- src/kit/files/<deploy path>.tmpl: one template file per deployed file. The
  .tmpl suffix keeps a template .gitignore, .gitattributes, skill or hook config
  from taking effect inside this repo.

- src/kit/capabilities.json: the capability matrix (P2 slice 4). A line
  ``<!-- kit-table: <name> -->`` in kit.md stands for that rendered table, so
  the cross-tool tables have one home. Rendering lives in
  src/project_bootstrap/capabilities.py.

One committed build output:

- bootstrap.py: the installer projects run (v3 Q49). It is
  src/project_bootstrap/installer.py, the templates and owners.json embedded,
  and the merge functions of tools/sync_project.py copied verbatim (SHARED), so
  install, update and sync share one implementation.

build() still assembles kit.md and the templates into one text, the way the
deployment package PROJECT-BOOTSTRAP.md used to be committed. Since v3 Q50 that
text is not a file any more: verify_bootstrap.py and sync_project.py build it in
memory with kit_text(). The Git history of PROJECT-BOOTSTRAP.md stays readable
for sync_project.py's list of published versions.

Edit the source and rerun:

    python3 -X utf8 tools/build_kit.py            # write bootstrap.py
    python3 -X utf8 tools/build_kit.py --check    # exit 1 if it is out of date

Standard library only (Python 3.8+), like verify_bootstrap.py.
"""
import argparse
import ast
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))
from project_bootstrap import capabilities  # noqa: E402

SOURCE = ROOT / 'src' / 'kit'
PROSE = SOURCE / 'kit.md'
FILES = SOURCE / 'files'
# Retired output (v3 Q50). Kept as a name so a stray copy can be refused.
RETIRED = ROOT / 'PROJECT-BOOTSTRAP.md'
INSTALLER = ROOT / 'src' / 'project_bootstrap' / 'installer.py'
SYNC = ROOT / 'tools' / 'sync_project.py'
BOOTSTRAP = ROOT / 'bootstrap.py'
# Names bootstrap.py takes verbatim from sync_project.py, in that file's order.
# sync() and apply_plan() are the update mode; the rest is what they call.
SHARED = (
    'read', 'write', 'by_update',
    'SKILL_DIR', 'SKILL_ENTRY', 'SKILL_PARTS', 'WHOLE', 'SURGICAL', 'SETTINGS_START', 'SETTINGS_END',
    'WIRING', 'OWNED_SCRIPTS', 'CODEX_WIRING', 'CODEX_LAUNCHER', 'PARTIAL', 'INSTANCE',
    'BUSY_FIELD', 'GITIGNORE_LINES', 'CLAUDE_IMPORT', 'SHARED_START', 'SHARED_END',
    'LEGACY_HANDOFF_HEADINGS',
    'split_settings', 'merge_check_docs', 'known_hook_commands', 'handler_scripts', 'scripts_in',
    'merge_group', 'merge_wiring', 'ensure_busy_field', 'ensure_gitignore', 'ensure_claude_import',
    'shared_block', 'merge_shared_section', 'legacy_handoff_sections', 'Plan', 'apply_plan',
    'sync_wiring', 'sync_shared_section', 'sync',
)
SUFFIX = '.tmpl'
DIRECTIVE_RE = re.compile(r'^<!-- kit-file: (\S+) -->$')
HEAD_RE = re.compile(r'^### 3\.\d+ ')
FENCE_RE = re.compile(r'^(`{3,})(\w*)\s*$')


class KitError(Exception):
    pass


def read_lf(path):
    with open(path, encoding='utf-8', newline='') as handle:
        return handle.read().replace('\r\n', '\n')


def write_lf(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as handle:
        handle.write(text)


def section_blocks(lines):
    """Yield (paths, [(open, close) line indexes]) per section 3.x, the way extract() reads it."""
    heads = [i for i, line in enumerate(lines) if HEAD_RE.match(line)]
    for n, i in enumerate(heads):
        end = heads[n + 1] if n + 1 < len(heads) else len(lines)
        paths = [p for p in re.findall(r'`([^`]+)`', lines[i]) if '.' in p or '/' in p]
        blocks, j = [], i
        while j < end:
            match = FENCE_RE.match(lines[j])
            if not match:
                j += 1
                continue
            k = j + 1
            while k < end and lines[k].rstrip() != match.group(1):
                k += 1
            blocks.append((j, k))
            j = k + 1
        yield paths, blocks


def split(kit):
    """Turn a built PROJECT-BOOTSTRAP.md into (prose, {deploy path: content})."""
    lines = kit.split('\n')
    files, replace = {}, {}
    for paths, blocks in section_blocks(lines):
        if not paths or not blocks:
            continue
        if len(blocks) < len(paths):
            raise KitError('section has fewer blocks than files: %s' % ', '.join(paths))
        for path, (start, end) in zip(paths, blocks):
            if path in files:
                raise KitError('file appears twice: ' + path)
            files[path] = '\n'.join(lines[start + 1:end]) + '\n'
            replace[start] = (end, path)
    out, i = [], 0
    while i < len(lines):
        out.append(lines[i])
        if i in replace:
            end, path = replace[i]
            out.append('<!-- kit-file: %s -->' % path)
            out.append(lines[end])
            i = end
        i += 1
    return '\n'.join(out), files


def build(prose, files):
    """Inverse of split: put every template back into its fenced block."""
    lines = prose.split('\n')
    out, used, fence = [], [], None
    for line in lines:
        if capabilities.TABLE_RE.match(line):
            raise KitError('kit-table not expanded (load_source renders it): ' + line)
        match = FENCE_RE.match(line)
        directive = DIRECTIVE_RE.match(line)
        if directive:
            path = directive.group(1)
            if fence is None:
                raise KitError('kit-file outside a fenced block: ' + path)
            if path in used:
                raise KitError('kit-file used twice: ' + path)
            if path not in files:
                raise KitError('kit-file has no template: ' + path)
            body = files[path]
            if not body.endswith('\n'):
                raise KitError('template must end with a newline: ' + path)
            if any(row.rstrip() == fence for row in body[:-1].split('\n')):
                raise KitError('template contains its own closing fence: ' + path)
            used.append(path)
            out.append(body[:-1])
            continue
        if match and fence is None:
            fence = match.group(1)
        elif fence is not None and line.rstrip() == fence:
            fence = None
        out.append(line)
    unused = sorted(set(files) - set(used))
    if unused:
        raise KitError('templates not used by kit.md: ' + ', '.join(unused))
    return '\n'.join(out)


def expand_tables(prose, matrix_text):
    """Render every kit-table line from capabilities.json text."""
    try:
        return capabilities.render_tables(prose, capabilities.load(matrix_text))
    except capabilities.MatrixError as exc:
        raise KitError('capabilities.json: %s' % exc)


def load_source(source=SOURCE):
    prose, files = load_raw(source)
    return expand_tables(prose, read_lf(source / 'capabilities.json')), files


def load_raw(source=SOURCE):
    """kit.md with its kit-table lines still in place, and the templates."""
    files = {}
    root = source / 'files'
    for path in sorted(root.rglob('*')):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            if not rel.endswith(SUFFIX):
                raise KitError('template without %s suffix: %s' % (SUFFIX, rel))
            files[rel[:-len(SUFFIX)]] = read_lf(path)
    return read_lf(source / 'kit.md'), files


def write_source(prose, files, source=SOURCE):
    write_lf(source / 'kit.md', prose)
    for rel, text in files.items():
        write_lf(source / 'files' / (rel + SUFFIX), text)


def node_names(node):
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        return {node.name}
    if isinstance(node, ast.Assign):
        return {t.id for t in node.targets if isinstance(t, ast.Name)}
    return set()


def shared_source(sync_text):
    """The SHARED definitions of sync_project.py, verbatim and in file order."""
    tree = ast.parse(sync_text)
    chunks, found = [], set()
    for node in tree.body:
        names = node_names(node) & set(SHARED)
        if names:
            found |= names
            chunks.append(ast.get_source_segment(sync_text, node))
    missing = [n for n in SHARED if n not in found]
    if missing:
        raise KitError('sync_project.py has no ' + ', '.join(missing))
    return '\n\n\n'.join(chunks)


def installer_body(text):
    """installer.py without its module docstring (bootstrap.py has its own)."""
    tree = ast.parse(text)
    first = tree.body[0]
    if not (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)):
        raise KitError('installer.py must start with a docstring')
    return '\n'.join(text.split('\n')[first.end_lineno:]).lstrip('\n')


def build_bootstrap(files, installer_text, sync_text, owners):
    """bootstrap.py: one stdlib-only file with every template embedded."""
    version_match = re.search(r'共用制度開始 source: PROJECT-BOOTSTRAP\.md v([0-9][0-9.-]*)',
                              files.get('AGENTS.md', ''))
    if not version_match:
        raise KitError('AGENTS.md template has no shared-section version marker')
    version = version_match.group(1)
    out = ['#!/usr/bin/env python3',
           '# -*- coding: utf-8 -*-',
           '"""AI 協作專案管理骨架的安裝程式（v%s）。' % version,
           '',
           '用法：',
           '  python3 bootstrap.py --target <專案資料夾>            # 安裝：程式會問訪談題目',
           '  python3 bootstrap.py --target <專案資料夾> --answers answers.json --non-interactive',
           '  python3 bootstrap.py update --target <專案資料夾>     # 更新預演；加 --write 才寫入',
           '',
           '只用 Python 標準函式庫，需要 Python 3.12 以上；只寫本機檔案，不碰網路、不推送。',
           '已存在的同名檔一律不覆寫，新內容寫到旁邊的 <路徑>.bootstrap-new。',
           '"""',
           '# 產物，不要手改：由 project-bootstrap 的 tools/build_kit.py 從 src/kit/、',
           '# src/project_bootstrap/installer.py 與 tools/sync_project.py 產生（需求決策書 v3 Q49）。',
           'import copy',
           installer_body(installer_text).rstrip('\n'),
           '',
           '',
           '# ── 內嵌的部署包 ─────────────────────────────────────────────',
           'OWNERS = %s' % json.dumps(owners, ensure_ascii=False, indent=1, sort_keys=True),
           'UPDATES = {rel: entry[\'update\'] for rel, entry in OWNERS.items()}',
           'TEMPLATES = {}']
    for rel in sorted(files):
        out.append('TEMPLATES[%r] = %r' % (rel, files[rel]))
    out += ['KIT = {\'version\': %r, \'owners\': OWNERS, \'templates\': TEMPLATES}' % version,
            '',
            '',
            '# ── 以下原樣取自 tools/sync_project.py（update 模式與 sync_project.py 共用同一套合併邏輯）──',
            shared_source(sync_text),
            '',
            '',
            "if __name__ == '__main__':",
            '    sys.exit(main(sys.argv[1:], KIT, sys.modules[__name__]))',
            '']
    return '\n'.join(out)


def kit_text():
    """The deployment package text, built in memory from src/kit (v3 Q50)."""
    return build(*load_source())


def load_bootstrap(files):
    owners = json.loads(read_lf(SOURCE / 'owners.json'))['files']
    return build_bootstrap(files, read_lf(INSTALLER), read_lf(SYNC), owners)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--check', action='store_true', help='exit 1 if either output is out of date')
    args = parser.parse_args(argv)
    try:
        prose, files = load_source()
        build(prose, files)  # the package text must still assemble
        outputs = ((BOOTSTRAP, load_bootstrap(files)),)
    except (KitError, OSError, SyntaxError) as exc:
        print('build_kit: ' + str(exc))
        return 2
    stale = 0
    for path, built in outputs:
        current = read_lf(path) if path.exists() else None
        if args.check:
            if built != current:
                stale += 1
                print('build_kit: %s 與來源不一致；改來源後跑 python3 -X utf8 tools/build_kit.py' % path.name)
            else:
                print('build_kit: %s 與來源一致' % path.name)
        elif built != current:
            write_lf(path, built)
            if path.suffix == '.py' and hasattr(path, 'chmod'):
                path.chmod(0o755)
            print('build_kit: 已重生 ' + path.name)
        else:
            print('build_kit: %s 已是最新' % path.name)
    if RETIRED.exists():
        print('build_kit: PROJECT-BOOTSTRAP.md 已退休（v3 Q50），不要放回來；說明在 src/kit/kit.md')
        return 1
    return 1 if stale else 0


if __name__ == '__main__':
    sys.exit(main())
