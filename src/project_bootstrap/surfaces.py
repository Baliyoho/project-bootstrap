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
from project_bootstrap.selftest import WIRING, session_commands

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
    return {'exit': done.returncode, 'raw': done.stdout, 'text': _decode(surface, done.stdout)}


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


def compare(project, surfaces, env, matrix=None, versions=None, subdir=''):
    """Run every supported surface on the same project state; equal means identical decoded text."""
    matrix = matrix if matrix is not None else capabilities.read_matrix()
    versions = versions or {}
    runs, unsupported = {}, {}
    for surface in surfaces:
        row = next(r for r in capabilities.report(matrix, surface, versions.get(surface))['rows']
                   if r['capability'] == 'hooks')
        if row['state'] == 'missing':
            unsupported[surface] = row['why']
            continue
        result = session_start(surface, project, env, subdir)
        result['text'] = normalise(result['text'])
        runs[surface] = result
    texts = {r['text'] for r in runs.values()}
    exits = {r['exit'] for r in runs.values()}
    return {'equal': len(texts) <= 1 and exits <= {0}, 'runs': runs, 'unsupported': unsupported}
