"""F47: version detection and the install self-test for one surface (P2 slice 4 gaps).

``capabilities.report`` answers for one surface at one version; this module
supplies the two inputs it cannot know by itself:

- ``detect_version``: run the surface's own ``--version`` (no model call, no
  network) or read the app bundle's ``Info.plist``. Nothing found is ``None``,
  never a guessed version, and the report then refuses to use tested cells.
- ``install_checks``: look at one project's files for what each capability
  needs there (the instruction file the tool reads, the skill, the hook wiring
  and the scripts it names). Files only: a passed check shows the wiring is in
  place, not that the tool calls it, so ``report`` lets a failed check make a
  capability missing but never lets a passed one upgrade it.

The matrix comes from the package the project has installed (its pointer and
the cache), so a project is judged by the release it runs; without ``--cache``
the source copy is used and the output says so. Running the hooks and asking
the tool itself (a startup self-test) is not done here: the hook fetches from
the remote, and the tool can only be asked through a model call.

    PYTHONPATH=src python3 -X utf8 -m project_bootstrap.selftest claude-code --project DIR [--cache DIR] [--version V]

Standard library only.
"""
import argparse
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys

from project_bootstrap import capabilities, package, pointer
from project_bootstrap.contracts import Denied

COMMANDS = {'claude-code': 'claude', 'codex-cli': 'codex', 'antigravity-cli': 'agy'}
# The app bundle, and the major versions that belong to the surface. Antigravity
# IDE (1.x) and Antigravity 2.0 (2.x) both ship as Antigravity.app; only the
# major version tells them apart, and the output names that as the source.
APPS = {'codex-app': ('Codex.app', None),
        'antigravity-ide': ('Antigravity.app', (1,)),
        'antigravity-2': ('Antigravity.app', (2,))}
VERSION_IN = re.compile(r'(?<![\d.])(\d+(?:\.\d+)+)(?![\d.])')
SKILL = 'skills/handoff/SKILL.md'
SKILLS = {'claude-code': ('project:.claude/' + SKILL, 'home:.claude/' + SKILL),
          'codex-cli': ('project:.agents/' + SKILL, 'home:.codex/' + SKILL),
          'codex-app': ('project:.agents/' + SKILL, 'home:.codex/' + SKILL),
          'antigravity-cli': ('project:.agents/' + SKILL,),
          'antigravity-2': ('project:.agents/' + SKILL,),
          'antigravity-ide': ('project:.agents/' + SKILL,)}
WIRING = {'claude-code': '.claude/settings.json', 'codex-cli': '.codex/hooks.json',
          'codex-app': '.codex/hooks.json', 'antigravity-cli': '.agents/hooks.json',
          'antigravity-2': '.agents/hooks.json', 'antigravity-ide': '.agents/hooks.json'}
FRESHNESS = '.claude/hooks/git-freshness.sh'
AG_WRAP = '.claude/hooks/ag-wrap.sh'


def _first_version(text):
    match = VERSION_IN.search(text or '')
    return match.group(1) if match else None


def _ask(argv, run):
    try:
        done = run(argv, capture_output=True, text=True, timeout=15, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    return _first_version(done.stdout)


def detect_version(surface, which=shutil.which, run=subprocess.run, environ=os.environ,
                   apps=Path('/Applications')):
    """{'version': str|None, 'source': text}; never a guess."""
    if surface in COMMANDS:
        found = which(COMMANDS[surface])
        candidates = [(found, 'PATH 上的 %s' % COMMANDS[surface])] if found else []
        if surface == 'claude-code' and environ.get('CLAUDE_CODE_EXECPATH'):
            candidates.append((environ['CLAUDE_CODE_EXECPATH'], '執行中這個 Claude Code 的執行檔'))
        for path, source in candidates:
            version = _ask([path, '--version'], run)
            if version:
                return {'version': version, 'source': source + ' --version'}
        return {'version': None, 'source': '找不到 %s，或 --version 沒有給版本' % COMMANDS[surface]}
    if surface in APPS:
        bundle, majors = APPS[surface]
        try:
            with open(Path(apps) / bundle / 'Contents' / 'Info.plist', 'rb') as handle:
                version = _first_version(str(plistlib.load(handle).get('CFBundleShortVersionString', '')))
        except (OSError, plistlib.InvalidFileException, ValueError):
            return {'version': None, 'source': '讀不到 %s 的 Info.plist' % bundle}
        if version is None:
            return {'version': None, 'source': '%s 沒有版本字串' % bundle}
        if majors is not None and int(version.split('.')[0]) not in majors:
            return {'version': None, 'source': '%s 是 %s，主版號不屬於這個 surface' % (bundle, version)}
        source = '%s 的 Info.plist' % bundle
        if majors is not None:
            source += '（以主版號判斷是哪個 surface）'
        return {'version': version, 'source': source}
    return {'version': None, 'source': '這個 surface 沒有偵測版本的方法'}


def _ok(detail):
    return {'ok': True, 'detail': detail}


def _fail(detail):
    return {'ok': False, 'detail': detail}


def _read(path):
    try:
        return path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return None


def _instructions(surface, project):
    if not (project / 'AGENTS.md').is_file():
        return _fail('沒有 AGENTS.md')
    if surface == 'claude-code' and (project / 'CLAUDE.md').exists():
        text = _read(project / 'CLAUDE.md')
        if text is None or '@AGENTS.md' not in [line.strip() for line in text.split('\n')]:
            return _fail('CLAUDE.md 沒有單獨一行 @AGENTS.md；Claude Code 有 CLAUDE.md 就不讀 AGENTS.md')
    if surface.startswith('antigravity-') and (project / 'GEMINI.md').exists():
        text = _read(project / 'GEMINI.md')
        if text is None or 'AGENTS.md' not in text:
            return _fail('GEMINI.md 沒有指向 AGENTS.md；兩者的優先序官方沒排')
    return _ok('AGENTS.md 在，指示檔指向它')


def _skill(surface, project, home):
    tried = []
    for entry in SKILLS[surface]:
        where, relative = entry.split(':', 1)
        path = (project if where == 'project' else home) / relative
        tried.append(('專案 ' if where == 'project' else '家目錄 ~/') + relative)
        if path.is_file() and (_read(path) or '').strip():
            return _ok('找到 ' + tried[-1])
    return _fail('找不到 handoff skill：' + '、'.join(tried))


def session_commands(surface, data):
    """POSIX commands wired to SessionStart, or None when the shape is wrong."""
    if not isinstance(data, dict):
        return None
    if surface.startswith('antigravity-'):
        groups = [v for v in data.values() if isinstance(v, dict) and v.get('enabled') is True]
        entries = [e for g in groups for e in (g.get('SessionStart') or []) if isinstance(e, dict)]
    else:
        hooks = data.get('hooks')
        if not isinstance(hooks, dict):
            return None
        entries = [h for g in (hooks.get('SessionStart') or []) if isinstance(g, dict)
                   for h in (g.get('hooks') or []) if isinstance(h, dict)]
    return [e['command'] for e in entries
            if e.get('type') == 'command' and isinstance(e.get('command'), str)]


def _runnable(path):
    return path.is_file() and os.access(path, os.X_OK)


def _hooks(surface, project):
    wiring = WIRING[surface]
    text = _read(project / wiring)
    if text is None:
        return _fail('沒有 ' + wiring)
    try:
        data = json.loads(text)
    except ValueError:
        return _fail(wiring + ' 不是 JSON')
    commands = session_commands(surface, data)
    if commands is None:
        return _fail(wiring + ' 的形狀不對')
    wired = [c for c in commands if 'git-freshness.sh' in c]
    if not wired:
        return _fail(wiring + ' 的 SessionStart 沒有接 git-freshness.sh')
    if not (project / FRESHNESS).is_file():
        return _fail('接線指向的 %s 不在' % FRESHNESS)
    if surface.startswith('antigravity-'):
        # Antigravity runs the command itself from .agents/, so the wrapper must be executable.
        if not any(c.split()[0] == '../' + AG_WRAP for c in wired):
            return _fail(wiring + ' 的 SessionStart 沒有經 ' + AG_WRAP)
        if not _runnable(project / AG_WRAP):
            return _fail('%s 不在或不能執行' % AG_WRAP)
    return _ok('%s 的 SessionStart 接到 %s，檔案都在' % (wiring, FRESHNESS))


def install_checks(surface, project, home=None):
    """{capability: {'ok', 'detail'}} for what one project's files can show."""
    project = Path(project)
    home = Path(home) if home is not None else Path.home()
    if surface not in SKILLS:
        return {}
    return {'reads-agents-md': _instructions(surface, project),
            'loads-skill': _skill(surface, project, home),
            'hooks': _hooks(surface, project)}


def installed_matrix(project, cache):
    """The matrix of the package the project's pointer names, checked like a write would."""
    try:
        record = pointer.parse((Path(project) / pointer.POINTER).read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise Denied('no-pointer') from None
    except (OSError, UnicodeDecodeError):
        raise Denied('invalid-pointer') from None
    folder = Path(cache) / record['installed']
    try:
        manifest = json.loads((folder / package.MANIFEST).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        raise Denied('package-not-cached') from None
    problems = package.check(folder)
    if problems:
        raise Denied('package-damaged:' + ','.join(problems))
    if package.digest(manifest) != record['installed']:
        raise Denied('package-mismatch')
    try:
        return capabilities.from_manifest(manifest), record['installed']
    except capabilities.MatrixError:
        raise Denied('package-without-capabilities') from None


def run(surface, project, cache=None, version=None, home=None, detect=detect_version):
    if cache is None:
        matrix, origin = capabilities.read_matrix(), 'source（src/kit/capabilities.json，不是已安裝的包）'
    else:
        matrix, digest = installed_matrix(project, cache)
        origin = 'installed ' + digest
    found = {'version': version, 'source': '呼叫端指定'} if version else detect(surface)
    checks = install_checks(surface, project, home)
    unused = sorted(set(checks) - set(matrix['capabilities']))
    result = capabilities.report(matrix, surface, found['version'],
                                 checks={k: v for k, v in checks.items() if k not in unused})
    if unused:
        result['checks_without_capability'] = unused
    result['version_source'] = found['source']
    result['matrix'] = origin
    result['not_tested'] = '沒有跑 hook、沒有問工具本身（啟動自測要模型呼叫，另行授權）'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description='Detect a surface version and self-test one project\'s wiring.')
    parser.add_argument('surface')
    parser.add_argument('--project', default='.')
    parser.add_argument('--cache', help='package cache; the matrix then comes from the installed package')
    parser.add_argument('--version', help='use this version instead of detecting one')
    args = parser.parse_args(argv)
    try:
        result = run(args.surface, args.project, args.cache, args.version)
    except (capabilities.MatrixError, Denied, OSError) as exc:
        print('selftest: %s' % exc, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['strict_ready'] else 1


if __name__ == '__main__':
    sys.exit(main())
