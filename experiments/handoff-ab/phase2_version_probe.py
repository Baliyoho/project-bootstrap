#!/usr/bin/env python3
"""Isolated model probe for the authority-repo version cache change.

Usage: phase2_version_probe.py prepare OLD|NEW ROOT
       phase2_version_probe.py run OLD|NEW ROOT --approved
       phase2_version_probe.py assess OLD|NEW ROOT
Raw events stay under ROOT, outside this repository.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import codex_run
import usage

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
OLD = 'd6d6218'
NEW = 'eae27b0'
PROMPT = ('只根據這次 SessionStart 的 [facts] 回覆：上游共用制度版本是多少、'
          '本地共用制度是否落後？若 [facts] 沒提供上游版本，回答「未知」。'
          '不要讀檔、不要執行命令、不要修改專案。')


def call(args, cwd=None, env=None):
    return subprocess.run([str(x) for x in args], cwd=cwd, env=env,
                          check=True, capture_output=True, text=True)


def git(cwd, *args):
    return call(['git', *args], cwd=cwd)


def prepare(arm, root):
    run = root / arm.lower()
    if run.exists():
        raise SystemExit('fixture 已存在，不覆寫')
    run.mkdir(parents=True)
    origin, writer, work = run / 'origin.git', run / 'writer', run / 'work'
    git(run, 'init', '-q', '--bare', '-b', 'main', origin)
    git(run, 'clone', '-q', origin, writer)
    git(writer, 'config', 'user.name', 'Fixture')
    git(writer, 'config', 'user.email', 'fixture@example.invalid')
    (writer / 'AGENTS.md').write_text('<!-- 共用制度開始 source: PROJECT-BOOTSTRAP.md v2026-11-14 -->\n', encoding='utf-8')
    (writer / 'HANDOFF.md').write_text('- **工作中**：無（已交棒）\n', encoding='utf-8')
    (writer / 'VERSION').write_text('2026-11-14\n', encoding='utf-8')
    git(writer, 'add', 'AGENTS.md', 'HANDOFF.md', 'VERSION')
    git(writer, 'commit', '-qm', 'baseline')
    git(writer, 'push', '-q', 'origin', 'main')
    git(run, 'clone', '-q', origin, work)
    (writer / 'VERSION').write_text('2026-11-14.4\n', encoding='utf-8')
    git(writer, 'add', 'VERSION')
    git(writer, 'commit', '-qm', 'new version')
    git(writer, 'push', '-q', 'origin', 'main')
    (work / '.claude' / 'hooks').mkdir(parents=True)
    (work / '.codex').mkdir()
    (work / '.codex' / 'hooks.json').write_bytes((REPO / 'src/kit/files/.codex/hooks.json.tmpl').read_bytes())
    (work / '.claude' / 'settings.json').write_bytes((REPO / 'src/kit/files/.claude/settings.json.tmpl').read_bytes())
    rev = OLD if arm == 'OLD' else NEW
    hook = git(REPO, 'show', rev + ':src/kit/files/.claude/hooks/git-freshness.sh.tmpl').stdout
    (work / '.claude' / 'hooks' / 'git-freshness.sh').write_text(hook, encoding='utf-8')
    (work / '.claude' / '.bootstrap-version').write_text('2026-11-14', encoding='utf-8')
    bindir = run / 'bin'
    bindir.mkdir()
    real_git = shutil.which('git')
    wrapper = ('#!/bin/sh\nif [ "$1" = remote ] && [ "$2" = get-url ]; then\n'
               '  printf "%s\\n" https://github.com/Baliyoho/project-bootstrap.git\n'
               'else\n  exec "' + real_git + '" "$@"\nfi\n')
    (bindir / 'git').write_text(wrapper, encoding='utf-8')
    (bindir / 'git').chmod(0o755)
    meta = {'arm': arm, 'commit': rev, 'old_cache': '2026-11-14',
            'upstream_version': '2026-11-14.4', 'model': 'gpt-6-sol',
            'reasoning': 'medium', 'origin_is_local_bare': True,
            'remote_get_url_is_mocked': True,
            'local_head': git(work, 'rev-parse', 'HEAD').stdout.strip()}
    (run / 'meta.json').write_text(json.dumps(meta, indent=2) + '\n', encoding='utf-8')
    print(run)


def run(arm, root):
    folder = root / arm.lower()
    work = folder / 'work'
    if (folder / 'events.jsonl').exists():
        raise SystemExit('已有模型事件，不覆寫')
    codex = shutil.which('codex')
    if not codex:
        raise SystemExit('Codex CLI 不可用')
    home = folder / 'codex-home'
    home.mkdir(exist_ok=True)
    auth = home / 'auth.json'
    if not auth.exists():
        auth.symlink_to(Path.home() / '.codex/auth.json')
    if codex_run.preflight(folder):
        raise SystemExit('Codex 隔離或訂閱登入檢查失敗')
    if codex_run.calls(folder) >= 12:
        raise SystemExit('fixture 呼叫次數達 12')
    env = {'PATH': str(folder / 'bin') + os.pathsep + os.environ['PATH'],
           'HOME': str(Path.home()), 'CODEX_HOME': str(home),
           'LANG': 'en_US.UTF-8', 'TZ': 'Asia/Taipei',
           'GIT_TERMINAL_PROMPT': '0', 'HOSTNAME': 'lab-mac'}
    status_result = call([codex, 'login', 'status'], env=env)
    status = status_result.stdout + status_result.stderr
    if 'Logged in using ChatGPT' not in status:
        raise SystemExit('不是 ChatGPT 訂閱登入')
    command = [codex, 'exec', '--json',
               '--dangerously-bypass-hook-trust', '--trust', '-m', 'gpt-6-sol',
               '-c', 'model_reasoning_effort="medium"',
               '-c', 'approval_policy="never"', '-s', 'danger-full-access',
               '-C', str(work), PROMPT]
    with (folder / 'calls.log').open('a', encoding='utf-8') as log:
        log.write(arm + '\n')
    with (folder / 'events.jsonl').open('w', encoding='utf-8') as out, \
            (folder / 'stderr.txt').open('w', encoding='utf-8') as err:
        result = subprocess.run(command, env=env, stdin=subprocess.DEVNULL,
                                stdout=out, stderr=err, timeout=300)
    print('exit', result.returncode)


def assess(arm, root):
    folder = root / arm.lower()
    events = [json.loads(line) for line in (folder / 'events.jsonl').read_text(encoding='utf-8').splitlines()]
    ids = [row.get('thread_id') for row in events if row.get('type') == 'thread.started']
    if len(ids) != 1:
        raise SystemExit('thread.started 數量不是 1')
    rollouts = list((folder / 'codex-home' / 'sessions').rglob('*%s*.jsonl' % ids[0]))
    if len(rollouts) != 1:
        raise SystemExit('rollout 數量不是 1')
    rows = [json.loads(line) for line in rollouts[0].read_text(encoding='utf-8').splitlines()]
    turns = [row.get('payload', {}).get('turn_id') for row in rows
             if row.get('type') == 'event_msg' and row.get('payload', {}).get('type') == 'task_started']
    models = {row.get('payload', {}).get('model') for row in rows if row.get('type') == 'turn_context'}
    facts = '\n'.join(json.dumps(row.get('payload', {}).get('content'), ensure_ascii=False)
                      for row in rows if row.get('type') == 'response_item'
                      and row.get('payload', {}).get('role') == 'developer'
                      and 'hooks.additional_context' in str(row.get('payload', {}).get(
                          'internal_chat_message_metadata_passthrough', {})))
    messages = [row.get('item', {}).get('text', '') for row in events
                if row.get('type') == 'item.completed'
                and row.get('item', {}).get('type') == 'agent_message']
    final = messages[-1] if messages else ''
    meta = json.loads((folder / 'meta.json').read_text(encoding='utf-8'))
    expected_head = meta.get('local_head') or git(folder / 'origin.git', 'rev-parse', 'main^').stdout.strip()
    got_new = '上游 v2026-11-14.4' in facts
    expect_new = arm == 'NEW'
    checks = {'model': models == {'gpt-6-sol'}, 'facts': '[facts]' in facts,
              'version_fact': got_new == expect_new,
              'answer': ('2026-11-14.4' in final and '落後' in final) if expect_new
                        else ('未知' in final and '2026-11-14.4' not in final),
              'no_commands': not any(row.get('type') == 'item.started' and
                                     row.get('item', {}).get('type') == 'command_execution'
                                     for row in events),
              'complete': any(row.get('type') == 'turn.completed' for row in events),
              'tracked_work_unchanged': subprocess.run(['git', 'diff', 'HEAD', '--quiet'],
                                                       cwd=folder / 'work').returncode == 0
                                        and git(folder / 'work', 'rev-parse', 'HEAD').stdout.strip() == expected_head}
    metrics = usage.codex(rollouts[0], turns[-1]) if turns else None
    print(json.dumps({'arm': arm, 'verdict': 'PASS' if all(checks.values()) else 'FAIL',
                      'checks': checks, 'usage': metrics}, ensure_ascii=False, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    if len(sys.argv) not in (4, 5) or sys.argv[1] not in ('prepare', 'run', 'assess') or sys.argv[2] not in ('OLD', 'NEW'):
        raise SystemExit(__doc__)
    if sys.argv[1] == 'run' and (len(sys.argv) != 5 or sys.argv[4] != '--approved'):
        raise SystemExit('模型呼叫需 --approved；每格前另查訂閱用量')
    if sys.argv[1] != 'run' and len(sys.argv) != 4:
        raise SystemExit(__doc__)
    action, arm, root = sys.argv[1], sys.argv[2], Path(sys.argv[3]).resolve()
    {'prepare': prepare, 'run': run, 'assess': assess}[action](arm, root)
