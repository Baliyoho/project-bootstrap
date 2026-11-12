"""F14: one shared contract for the session-start check, thin adapters per surface.

The contract: ``.claude/hooks/git-freshness.sh`` runs at the project root and
prints the ``[git-check]``／``[handoff]`` lines; that text is the whole result.
Each surface reaches it through its own wiring file and working directory,
and an adapter only moves bytes:

- Claude Code and Codex run the wiring's ``command`` with a shell, from the
  project root or any folder under it (``$(git rev-parse --show-cdup)``), and
  inject stdout as it is;
- Antigravity runs the ``command`` from ``.agents/`` (measured, see the
  deployment package 3.20) and gets JSON from ``ag-wrap.sh``; the adapter
  decodes ``injectSteps[0].ephemeralMessage`` back to the text.

``session_start`` runs one surface's real wiring for one project, and
``compare`` runs every surface on the same project state: the decoded texts
must be identical. A surface the capability matrix marks as having no hooks
is not run; it is reported as unsupported with the matrix's reason.

Two more shared contracts follow below: the push reminder (exit code and stderr)
and the procedure entry (the instruction text and handoff skill each surface's
loader reaches, ``compare_procedure``).

What this does not show: that the tool itself fires the hook and puts the text
in front of the model (that needs the tool and a model call), and the Windows
``commandWindows``／``.cmd`` path. The run fetches from the project's origin.

Standard library only.
"""
import json
import os
from pathlib import Path
import re
import subprocess

from project_bootstrap import capabilities
from project_bootstrap import selftest
from project_bootstrap.selftest import SKILLS, WIRING, session_commands

FRESHNESS = 'git-freshness.sh'
# Antigravity runs project hooks with .agents/ as the working directory.
CWD = {'antigravity-cli': '.agents', 'antigravity-2': '.agents', 'antigravity-ide': '.agents'}
# Clock readings the hook prints; two surfaces run a minute apart must still compare equal.
STAMPS = ((re.compile(r'全綠 \d{4}-\d{2}-\d{2} \d{2}:\d{2}'), '全綠 <time>'),
          (re.compile(r'㊣　\d{8}'), '㊣　<time>'))
# A surface's own identity is what the hook may tell apart; the adapters must not.
TOOL_VARS = ('CLAUDECODE', 'CODEX_VERSION', 'CODEX_SESSION_ID', 'GEMINI_CLI')


class AdapterError(Exception):
    pass


def _commands(surface, project):
    """The wired commands that run the check. Antigravity has one per OS (3.20), the others one."""
    try:
        data = json.loads((Path(project) / WIRING[surface]).read_text(encoding='utf-8'))
    except (OSError, ValueError, UnicodeDecodeError):
        raise AdapterError('%s: %s 讀不到或不是 JSON' % (surface, WIRING[surface]))
    found = [c for c in (session_commands(surface, data) or []) if FRESHNESS in c]
    if not found or (surface not in CWD and len(found) != 1):
        raise AdapterError('%s: SessionStart 接到 %s 的命令有 %d 條' % (surface, FRESHNESS, len(found)))
    return found


def _decode(surface, stdout):
    if surface not in CWD:
        return stdout
    try:
        data = json.loads(stdout)
    except ValueError:
        raise AdapterError('%s: 轉接層輸出不是 JSON' % surface)
    if data == {}:
        return ''
    steps = data.get('injectSteps') if isinstance(data, dict) else None
    if (set(data) != {'injectSteps'} or not isinstance(steps, list) or len(steps) != 1
            or not isinstance(steps[0], dict) or set(steps[0]) != {'ephemeralMessage'}
            or not isinstance(steps[0]['ephemeralMessage'], str)):
        raise AdapterError('%s: 轉接層輸出不是 SessionStart 契約' % surface)
    return steps[0]['ephemeralMessage'] + '\n'


def session_start(surface, project, env, subdir=''):
    """Run one surface's real wiring; {'exit', 'raw', 'text'}.

    ``subdir`` is where a Claude Code／Codex session was opened; Antigravity
    always runs from ``.agents/``.
    """
    project = Path(project)
    cwd = project / (CWD.get(surface) or subdir)
    payload = json.dumps({'hook_event_name': 'SessionStart', 'cwd': str(cwd)})
    runs = []
    for command in _commands(surface, project):
        try:
            done = subprocess.run(['/bin/sh', '-c', command], cwd=cwd, env=env,
                                  input=payload, capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            raise AdapterError('%s: 逾時' % surface)
        runs.append(done)
    # The handler for the other OS fails without stdout and is harmless (3.20); two
    # handlers printing would inject the check twice.
    spoke = [done for done in runs if done.stdout.strip()]
    if len(runs) > 1 and len(spoke) != 1:
        raise AdapterError('%s: %d 條命令有輸出，要恰好 1 條' % (surface, len(spoke)))
    done = spoke[0] if len(runs) > 1 else runs[0]
    return {'exit': done.returncode, 'raw': done.stdout, 'stderr': done.stderr,
            'text': _decode(surface, done.stdout)}


def normalise(text):
    for pattern, stamp in STAMPS:
        text = pattern.sub(stamp, text)
    return text


def neutral_env(base=None):
    """The caller's environment without any tool's identity variables."""
    env = dict(os.environ if base is None else base)
    for name in TOOL_VARS:
        env.pop(name, None)
    return env


def _unsupported(matrix, surface, version, capability):
    """The matrix's reason when this surface at this version does not have the capability, else None."""
    row = next(r for r in capabilities.report(matrix, surface, version)['rows'] if r['capability'] == capability)
    return row['why'] if row['state'] == 'missing' else None


def compare(project, surfaces, env, matrix=None, versions=None, subdir=''):
    """Run every supported surface on the same project state; equal means identical decoded text."""
    matrix = matrix if matrix is not None else capabilities.read_matrix()
    versions = versions or {}
    runs, unsupported = {}, {}
    for surface in surfaces:
        why = _unsupported(matrix, surface, versions.get(surface), 'hooks')
        if why:
            unsupported[surface] = why
            continue
        result = session_start(surface, project, env, subdir)
        result['text'] = normalise(result['text'])
        runs[surface] = result
    texts = {r['text'] for r in runs.values()}
    exits = {r['exit'] for r in runs.values()}
    # ag-wrap.sh folds stderr into the injected message (2>&1); the other surfaces do not
    # show it to the model. A hook that writes stderr is therefore not equivalent.
    quiet = all(not r.get('stderr') for s, r in runs.items() if s not in CWD)
    return {'equal': len(texts) <= 1 and exits <= {0} and quiet, 'runs': runs, 'unsupported': unsupported}


# The push reminder (3.11) is the second shared check. Its contract is the exit
# code (2 blocks the tool call) and stderr (what the model is shown). Claude Code
# and Codex wire it to PreToolUse; Antigravity deliberately does not (3.20).
PUSH = 'pre-push-handoff.sh'


def _push_handler(surface, project):
    """(matcher or None, command) of the one PreToolUse handler that runs the push reminder."""
    wiring = WIRING[surface]
    try:
        data = json.loads((Path(project) / wiring).read_text(encoding='utf-8'))
    except (OSError, ValueError, UnicodeDecodeError):
        raise AdapterError('%s: %s 讀不到或不是 JSON' % (surface, wiring))
    hooks = data.get('hooks') if isinstance(data, dict) else None
    groups = hooks.get('PreToolUse') if isinstance(hooks, dict) else None
    found = [(group.get('matcher'), handler['command'])
             for group in (groups if isinstance(groups, list) else []) if isinstance(group, dict)
             for handler in (group.get('hooks') or []) if isinstance(handler, dict)
             if handler.get('type') == 'command' and PUSH in str(handler.get('command', ''))]
    if len(found) != 1:
        raise AdapterError('%s: PreToolUse 接到 %s 的命令有 %d 條，要恰好 1 條' % (surface, PUSH, len(found)))
    return found[0]


def _matches(matcher, tool):
    """Both tools: no matcher, "" or "*" is every call; otherwise a regex on the whole tool name."""
    if matcher in (None, '', '*'):
        return True
    return re.fullmatch(matcher, tool) is not None


def pre_tool_use(surface, project, env, payload, subdir=''):
    """Run one surface's push-reminder wiring for one tool call; {'ran', 'exit', 'stderr'}."""
    matcher, command = _push_handler(surface, project)
    if not _matches(matcher, str(payload.get('tool_name', ''))):
        return {'ran': False, 'exit': 0, 'stderr': ''}
    cwd = Path(project) / subdir
    body = json.dumps(dict(payload, hook_event_name='PreToolUse', cwd=str(cwd)), ensure_ascii=False)
    try:
        done = subprocess.run(['/bin/sh', '-c', command], cwd=cwd, env=env, input=body,
                              capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        raise AdapterError('%s: 逾時' % surface)
    return {'ran': True, 'exit': done.returncode, 'stderr': done.stderr}


def compare_push(project, surfaces, env, payload, matrix=None, versions=None, subdir=''):
    """The same tool call on every supported surface; equal means the same exit code and stderr."""
    matrix = matrix if matrix is not None else capabilities.read_matrix()
    versions = versions or {}
    runs, unsupported = {}, {}
    for surface in surfaces:
        why = _unsupported(matrix, surface, versions.get(surface), 'push-reminder')
        if why:
            unsupported[surface] = why
            continue
        runs[surface] = pre_tool_use(surface, project, env, payload, subdir)
    outcomes = {(r['exit'], r['stderr']) for r in runs.values()}
    return {'equal': len(outcomes) <= 1, 'runs': runs, 'unsupported': unsupported}


# The procedure itself is the third shared thing. Every surface must reach the same
# instruction text (AGENTS.md, through CLAUDE.md's import or GEMINI.md's pointer)
# and, through its own skill loader, the same handoff skill: the same description the
# loader matches against, and the same entry and mode files. A pointer skill
# (.agents/skills/) is followed to the file it names; its description is the
# authoritative one with a fixed lead in front (3.16: written out in full).
POINTER = re.compile(r'權威版：\*{0,2}\[[^\]]*\]\(([^)\s]+)\)')
POINTER_LEAD = re.compile(r'^指標檔，權威版在 \S+——')


def _frontmatter(text):
    lines = text.split('\n')
    if not lines or lines[0].strip() != '---' or '---' not in [l.strip() for l in lines[1:]]:
        return None
    end = [l.strip() for l in lines[1:]].index('---') + 1
    fields = {}
    for line in lines[1:end]:
        key, sep, value = line.partition(':')
        if sep and key.strip():
            fields[key.strip()] = value.strip()
    return fields


def _skill_entry(surface, project, home):
    """(label, path) of the first handoff skill the surface's loader finds."""
    for entry in SKILLS[surface]:
        where, relative = entry.split(':', 1)
        path = (project if where == 'project' else home) / relative
        if path.is_file():
            return ('專案 ' if where == 'project' else '家目錄 ~/') + relative, path
    raise AdapterError('%s: 找不到 handoff skill' % surface)


def procedure(surface, project, home):
    """What one surface reaches: {'entry', 'instructions', 'description', 'files'}."""
    project, home = Path(project), Path(home)
    check = selftest._instructions(surface, project)
    if not check['ok']:
        raise AdapterError('%s: %s' % (surface, check['detail']))
    instructions = selftest._read(project / 'AGENTS.md')
    label, path = _skill_entry(surface, project, home)
    text = selftest._read(path)
    meta = _frontmatter(text or '')
    if not meta or meta.get('name') != 'handoff' or not meta.get('description'):
        raise AdapterError('%s: %s 的 frontmatter 沒有 name: handoff 與 description' % (surface, label))
    description = meta['description']
    link = POINTER.search(text)
    if link:
        target = (path.parent / link.group(1)).resolve()
        if not target.is_file():
            raise AdapterError('%s: %s 指向的 %s 不存在' % (surface, label, link.group(1)))
        if not POINTER_LEAD.match(description):
            raise AdapterError('%s: %s 是指標，但 description 沒有指標開頭' % (surface, label))
        description = POINTER_LEAD.sub('', description)
        path = target
    files = {f.name: selftest._read(f) for f in sorted(path.parent.glob('*.md'))}
    return {'entry': label, 'instructions': instructions, 'description': description, 'files': files}


def compare_procedure(project, surfaces, home, matrix=None, versions=None):
    """Every supported surface on the same project; 'differ' names the parts that are not identical."""
    matrix = matrix if matrix is not None else capabilities.read_matrix()
    versions = versions or {}
    runs, unsupported = {}, {}
    for surface in surfaces:
        why = (_unsupported(matrix, surface, versions.get(surface), 'reads-agents-md')
               or _unsupported(matrix, surface, versions.get(surface), 'loads-skill'))
        if why:
            unsupported[surface] = why
            continue
        runs[surface] = procedure(surface, project, home)
    differ = [part for part in ('instructions', 'description', 'files')
              if len({json.dumps(r[part], sort_keys=True, ensure_ascii=False) for r in runs.values()}) > 1]
    return {'equal': not differ, 'differ': differ, 'runs': runs, 'unsupported': unsupported}
