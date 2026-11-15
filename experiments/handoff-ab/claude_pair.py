#!/usr/bin/env python3
"""Claude Code adapter for comparable.py: launch, validity, observed actions, usage.

Only `launch` calls a model (one subscription-backed `claude -p` turn). Everything
else reads files that stay under HANDOFF_AB_ROOT, outside this public repository.
"""
import hashlib
import json
import subprocess
import time
import uuid

import run as claude_cli
import score
import usage
from common import MODEL, config_dir, read, run_env, stamp, write_lf

EFFORT = 'medium'          # 明確固定；跟 Codex 的 medium 不是同一個意思，不跨工具比較
MARKER_TOOL = 'Claude Code'
EVENTS = 'stream.jsonl'
READ_TOOLS = ('Read', 'Grep', 'Glob')
READ_TOKENS = ('cat ', 'sed ', 'rg ', 'grep ', 'git show ')
VERIFY_TOKENS = ('verify_state.py', 'unittest', 'pytest')
UNKNOWN = ('wait_returns', 'command_retries', 'verification_seconds', 'reading_seconds',
           'waiting_seconds')


def command(prompt, session_id):
    """同 run.py 的受測指令，但保留 session 紀錄並指定 session id，回合後才找得到唯一紀錄。"""
    return [claude_cli.claude_bin(), '-p', prompt, '--model', MODEL, '--effort', EFFORT,
            '--output-format', 'stream-json', '--verbose', '--include-hook-events',
            '--permission-mode', 'dontAsk', '--allowedTools', *claude_cli.TOOLS,
            '--disallowedTools', 'WebFetch', 'WebSearch', '--session-id', session_id]


def run_config(run):
    path = run / 'run-config.json'
    return json.loads(read(path)) if path.exists() else {}


def session_file(root, session_id):
    """受測設定目錄裡這個 session id 的唯一紀錄檔；沒有或不唯一回 None。"""
    base = config_dir(root) / 'projects'
    hits = list(base.rglob('%s.jsonl' % session_id)) if session_id and base.exists() else []
    return hits[0] if len(hits) == 1 else None


def user_uuid(path):
    """紀錄裡唯一一則人類訊息的 uuid。每格只送一句，不是剛好一則就回 None，不猜。"""
    try:
        ids = [row.get('uuid') for row in usage.records(path) if usage.human_user(row)]
    except (OSError, ValueError):
        return None
    return ids[0] if len(ids) == 1 and ids[0] else None


def tool_calls(run):
    """串流裡的工具呼叫 (名稱, 參數)，同一個 tool_use id 只算一次。沒有串流回 None。"""
    parsed = score.transcript(run)
    if parsed is None:
        return None
    seen, calls = set(), []
    for event in parsed[0]:
        if event.get('type') != 'assistant':
            continue
        for block in (event.get('message') or {}).get('content') or []:
            if not isinstance(block, dict) or block.get('type') != 'tool_use':
                continue
            ident = block.get('id')
            if ident and ident in seen:
                continue
            seen.add(ident)
            calls.append((block.get('name', ''), block.get('input') or {}))
    return calls


def observation(run):
    """只數串流看得到的工具呼叫；耗時、等待回合、重試沒有可靠事件，維持 null。"""
    calls = tool_calls(run)
    keys = ('read_commands', 'verify_commands', 'git_commands', 'skill_calls', 'tool_calls')
    if calls is None:
        return {key: None for key in keys + UNKNOWN}
    bash = [str(args.get('command', '')) for name, args in calls if name == 'Bash']
    seen = {'read_commands': sum(name in READ_TOOLS for name, _ in calls) +
                             sum(any(t in c for t in READ_TOKENS) for c in bash),
            'verify_commands': sum(any(t in c for t in VERIFY_TOKENS) for c in bash),
            'git_commands': sum('git ' in c for c in bash),
            'skill_calls': sum(name == 'Skill' for name, _ in calls),
            'tool_calls': len(calls)}
    seen.update({key: None for key in UNKNOWN})
    return seen


def validity(root, run):
    """這一格算不算數。沿用 score.validity 的串流檢查，再加 session 紀錄與回合邊界。"""
    problems = list(score.validity(run, 'full'))
    if problems == ['沒有串流紀錄'] or problems == ['串流裡沒有 init 事件']:
        return problems
    events = score.transcript(run)[0]
    wanted = run_config(run).get('session_id')
    inits = [e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init']
    if len(inits) != 1 or not wanted or inits[0].get('session_id') != wanted:
        problems.append('init 事件不是剛好一個，或 session id 跟啟動時指定的不同')
    results = [e for e in events if e.get('type') == 'result']
    if len(results) != 1 or results[0].get('subtype') != 'success':
        problems.append('result 事件不是剛好一個 success')
    path = session_file(root, wanted)
    if path is None:
        problems.append('找不到唯一的 Claude session 紀錄')
    elif user_uuid(path) is None:
        problems.append('session 紀錄裡的人類訊息不是剛好一則')
    return problems


def usage_for(root, run):
    """回合後一次解析；找不到唯一紀錄或唯一 user UUID 回 None（未知），不填零。"""
    path = session_file(root, run_config(run).get('session_id'))
    ident = user_uuid(path) if path else None
    return usage.claude(path, ident) if ident else None


def cli_reported(run):
    """CLI 自己在 result 事件回報的值，只當對照，不取代 usage.py。"""
    parsed = score.transcript(run)
    result = next((e for e in parsed[0] if e.get('type') == 'result'), None) if parsed else None
    if result is None:
        return None
    return {key: result.get(key) for key in ('duration_ms', 'duration_api_ms', 'num_turns')}


def launch(root, run, meta, name):
    """跑一格。先過用量守門與 preflight；寫 run-config、串流、stderr 與 wall。"""
    before = claude_cli.last_limit_problem(root)
    if before:
        raise RuntimeError('用量守門（呼叫前）：上一格%s，這一次不呼叫' % before)
    if claude_cli.preflight(root, quiet=True):
        raise RuntimeError('Claude preflight 未過；先跑 run.py preflight 看原因')
    env = run_env(root)
    prompt = meta['prompt']
    session_id = str(uuid.uuid4())
    version = subprocess.run([claude_cli.claude_bin(), '--version'], env=env,
                             capture_output=True, text=True, timeout=20, check=True)
    write_lf(run / 'run-config.json', json.dumps({
        'claude_version': version.stdout.strip(), 'model_argument': MODEL,
        'effort_argument': EFFORT, 'event_schema': 'claude -p --output-format stream-json',
        'usage_parser': 'usage.py claude (session jsonl, user uuid)',
        'session_id': session_id,
        'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
        'snapshot_sha256': meta['snapshot_sha256']}, ensure_ascii=False, indent=2) + '\n')
    with (root / 'calls.log').open('a', encoding='utf-8', newline='') as log:
        log.write('%s\t%s\n' % (stamp().isoformat(timespec='seconds'), name))
    start = time.monotonic()
    with (run / EVENTS).open('w', encoding='utf-8', newline='') as stdout, \
            (run / 'stderr.txt').open('w', encoding='utf-8', newline='') as stderr:
        try:
            done = subprocess.run(command(prompt, session_id), cwd=run / 'work', env=env,
                                  stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                  timeout=1200)
            code = done.returncode
        except subprocess.TimeoutExpired:
            code = 'timeout'
    write_lf(run / 'wall.json', json.dumps({'seconds': round(time.monotonic() - start, 3),
                                            'exit': code}) + '\n')
