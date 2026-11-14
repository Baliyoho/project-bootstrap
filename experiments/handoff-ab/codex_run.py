#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the v3 full skeleton with Codex on the existing handoff-ab fixtures.

One invocation runs one cell. The caller must check the account's subscription
usage before each invocation; Codex JSONL does not expose the quota window.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys

import build
import score
from common import (BUDGET, PROMPTS, REPEATS, SCENARIOS, TIMEOUT,
                    ancestor_problems, lab_root, prepare_root, run_env, stamp)

MODEL = 'gpt-6-sol'
ARM = 'full'


def codex_bin():
    found = shutil.which('codex')
    if not found:
        raise SystemExit('找不到 codex 執行檔')
    return found


def codex_home(root):
    return root / 'codex-home'


def subject_env(root):
    env = run_env(root)
    env.pop('CLAUDE_CONFIG_DIR', None)
    env['CODEX_HOME'] = str(codex_home(root))
    for key in ('OPENAI_API_KEY', 'OPENAI_BASE_URL', 'ANTHROPIC_API_KEY'):
        env.pop(key, None)
    return env


def preflight(root):
    problems = []
    if ancestor_problems(root):
        problems.append('工作區上層有指示檔或 repo：%s' % ancestor_problems(root))
    prepare_root(root)
    home = codex_home(root)
    home.mkdir(exist_ok=True)
    auth = home / 'auth.json'
    if not auth.is_symlink() or auth.resolve() != pathlib.Path.home() / '.codex' / 'auth.json':
        problems.append('隔離 CODEX_HOME 的 auth.json 必須連到目前帳號的登入檔')
    status = subprocess.run([codex_bin(), 'login', 'status'], env=subject_env(root),
                            capture_output=True, text=True, timeout=20)
    login_text = (status.stdout + status.stderr).strip()
    if status.returncode or 'Logged in using ChatGPT' not in login_text:
        problems.append('Codex 沒有用 ChatGPT 訂閱登入')
    print('工作區：%s' % root)
    print('模型：%s；隔離 CODEX_HOME：%s' % (MODEL, home))
    print('登入：%s' % login_text)
    print('已用呼叫次數：%d／%d' % (calls(root), BUDGET // 2))
    for item in problems:
        print('✗ ' + item)
    print('可以跑；每格前另查訂閱用量' if not problems else '還不能跑')
    return problems


def calls(root):
    path = root / 'calls.log'
    return len(path.read_text(encoding='utf-8').splitlines()) if path.exists() else 0


def prompt_isolated(items, run):
    blob = json.dumps(items, ensure_ascii=False)
    return ('# AGENTS.md instructions for' in blob and
            str(run / 'work' / '.agents' / 'skills') in blob and
            str(pathlib.Path.home() / '.codex' / 'skills' / 'handoff') not in blob)


def run_one(root, scenario, n):
    if scenario not in SCENARIOS or not (1 <= n <= REPEATS):
        raise SystemExit('情境或次數不在本輪清單')
    if calls(root) >= BUDGET // 2:
        raise SystemExit('本輪 Codex 完整組呼叫次數已達上限')
    if preflight(root):
        raise SystemExit('preflight 沒過')
    run = root / 'runs' / ('%s-%s-%s' % (scenario, ARM, n))
    if run.exists():
        if (run / 'codex-events.jsonl').exists() or not (run / 'meta.json').exists():
            raise SystemExit('這一格已有執行紀錄或缺少 fixture，不覆寫：%s' % run)
    else:
        run = build.build(root, scenario, ARM, n)
    prompt_input = subprocess.run([codex_bin(), 'debug', 'prompt-input', PROMPTS[scenario]],
                                  cwd=run / 'work', env=subject_env(root),
                                  capture_output=True, text=True, timeout=30)
    if prompt_input.returncode:
        raise SystemExit('Codex prompt-input 檢查失敗：%s' % prompt_input.stderr[:300])
    try:
        items = json.loads(prompt_input.stdout)
    except ValueError:
        raise SystemExit('Codex prompt-input 不是 JSON')
    if not prompt_isolated(items, run):
        raise SystemExit('Codex 沒載入專案 AGENTS／skill，或隔離失效')
    (run / 'prompt-input.json').write_text(prompt_input.stdout, encoding='utf-8')
    name = run.name
    with open(root / 'calls.log', 'a', encoding='utf-8', newline='') as fh:
        fh.write('%s\t%s\n' % (stamp().isoformat(timespec='seconds'), name))
    command = [codex_bin(), 'exec', '--json', '--ignore-user-config',
               '--dangerously-bypass-hook-trust',
               '-m', MODEL, '-c', 'model_reasoning_effort="medium"',
               '-c', 'approval_policy="never"', '-s', 'danger-full-access',
               '--add-dir', str(run), '-C', str(run / 'work'), PROMPTS[scenario]]
    with open(run / 'codex-events.jsonl', 'w', encoding='utf-8', newline='') as stdout, \
            open(run / 'codex-stderr.txt', 'w', encoding='utf-8', newline='') as stderr:
        try:
            result = subprocess.run(command, env=subject_env(root), stdin=subprocess.DEVNULL,
                                    stdout=stdout, stderr=stderr, timeout=TIMEOUT)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 'timeout'
    row = score.score(run, need_stream=False)
    row['exit'] = code
    row['codex_validity'] = codex_validity(run)
    if row['codex_validity']:
        row['verdict'] = 'INVALID'
        row['invalid'] = row['codex_validity']
    with open(run / 'score.json', 'w', encoding='utf-8', newline='') as fh:
        json.dump(row, fh, ensure_ascii=False, indent=1)
    print('%s %s %s exit=%s %s' % (name, row['verdict'], row['outcome'], code,
                                  '；'.join(row['invalid'] or row['failed'])))
    return 4 if row['verdict'] == 'INVALID' else 0


def codex_validity(run):
    events = []
    for line in (run / 'codex-events.jsonl').read_text(encoding='utf-8').splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            return ['Codex JSONL 有無法解析的行']
    kinds = [event.get('type') for event in events]
    problems = []
    if 'thread.started' not in kinds:
        problems.append('沒有 thread.started')
    if 'turn.completed' not in kinds or 'turn.failed' in kinds:
        problems.append('Codex 沒有正常完成')
    if not any(event.get('type') == 'item.completed' and
               (event.get('item') or {}).get('type') == 'agent_message' for event in events):
        problems.append('沒有最後回覆')
    ids = [event.get('thread_id') for event in events if event.get('type') == 'thread.started']
    rollouts = list((run.parent.parent / 'codex-home' / 'sessions').rglob('*%s*.jsonl' % ids[0])) if ids else []
    if len(rollouts) != 1:
        problems.append('找不到唯一的 Codex rollout')
    else:
        records = [json.loads(line) for line in rollouts[0].read_text(encoding='utf-8').splitlines()]
        models = {item.get('payload', {}).get('model') for item in records
                  if item.get('type') == 'turn_context'}
        if models != {MODEL}:
            problems.append('模型不是 %s：%s' % (MODEL, sorted(str(m) for m in models)))
        facts = any(item.get('type') == 'response_item' and
                    item.get('payload', {}).get('role') == 'user' and
                    '[facts]' in json.dumps(item.get('payload', {}).get('content'), ensure_ascii=False)
                    for item in records)
        if not facts:
            problems.append('模型輸入沒有 SessionStart [facts]')
    prompt = run / 'prompt-input.json'
    if not prompt.exists() or not prompt_isolated(json.loads(prompt.read_text(encoding='utf-8')), run):
        problems.append('專案 AGENTS／skill 載入或隔離檢查失敗')
    return problems


def main(args):
    root = lab_root()
    if not args or args[0] == 'preflight':
        return 1 if preflight(root) else 0
    if args[0] == 'plan':
        for scenario in SCENARIOS:
            for n in range(1, REPEATS + 1):
                name = '%s-%s-%s' % (scenario, ARM, n)
                print(name, '已跑' if (root / 'runs' / name).exists() else '待跑')
        return 0
    if len(args) == 4 and args[0] == 'one' and args[3] == '--approved':
        return run_one(root, args[1], int(args[2]))
    raise SystemExit('用法：codex_run.py preflight|plan|one SCENARIO N --approved')


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
