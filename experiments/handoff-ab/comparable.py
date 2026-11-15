#!/usr/bin/env python3
"""Prepare, run, and assess paired pure takeover / handoff fixtures.

No model is called by prepare, plan, or assess. `run CELL --approved` calls one
subscription-backed turn of the selected tool: Codex by default, Claude Code with
HANDOFF_AB_TOOL=claude. Each tool needs its own HANDOFF_AB_ROOT; results are
compared within a tool, never across tools. Raw logs and repositories stay under
HANDOFF_AB_ROOT, outside this public repository.
"""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

import build
import claude_pair
import codex_run
import fixture
import phase2_handoff_probe
import run as claude_cli
import score
import usage
from common import (IDLE, MACHINE, ancestor_problems, busy_value, fixture_env,
                    git, lab_root, out, read, stamp, write_lf)

TOOL = os.environ.get('HANDOFF_AB_TOOL', 'codex')
if TOOL not in ('codex', 'claude'):
    raise SystemExit('HANDOFF_AB_TOOL 只能是 codex 或 claude')
REPEATS = 3
ARMS = ('A', 'B')
KINDS = ('takeover', 'handoff')
PROMPTS = {
    'takeover': ('請接棒這個專案。這一回合只完成接棒：核對本機與 origin、'
                 '依專案既有規則完成接棒驗證、'
                 '在 origin 推上你自己的「工作中」標記、從遠端確認標記已生效並回覆。'
                 'HANDOFF.md 的下一項等我下一個指令，現在不要實作下一項或交棒。'
                 '若已有別人占用或 Git 狀態異常，依現有規則停下來。'),
    # 2026-11-15：明講標記是自己的。受測者是新開的 session，名稱與開工時間對不上起點的標記，
    # 不講的話照規則會當成別人占用而停下（Claude 煙霧 handoff-A-1），量到的就不是交棒。
    'handoff': ('這個 session 的成果已完成並推到 origin。'
                'origin 上 HANDOFF.md 的「工作中」標記是我們這個 session 先前推上去的，'
                'session 中斷後由你接續，不是別人的占用。現在只完成交棒：'
                '依專案既有規則完成服務、文件與 staged 驗證，覆寫 HANDOFF.md 當下快照、推送並釋回「工作中」、'
                '確認本機乾淨且與 origin 一致，然後回覆。不要新增功能。'),
}
# 占用者核對探針（HANDOFF_AB_VARIANT=occupant）：交棒提示不講標記是誰的。起點的標記跟受測
# session 的名稱、開工時間對不上，照規則要當成別人占用而停下；看 B 的執行提示會不會壓掉這個核對。
VARIANT = os.environ.get('HANDOFF_AB_VARIANT', '')
# 長驗證探針（HANDOFF_AB_VARIANT=slow）：接棒起點的 verify_state.py 開頭多等 SLOW_SECONDS 秒，
# 超過 Bash 工具預設的 120 秒，看受測者怎麼等（設 timeout、丟背景、輪詢或放棄）。
SLOW_SECONDS = 150
if VARIANT not in ('', 'occupant', 'slow'):
    raise SystemExit('HANDOFF_AB_VARIANT 只能是 occupant 或 slow')
if VARIANT == 'occupant':
    PROMPTS['handoff'] = ('這個 session 的成果已完成並推到 origin。現在只完成交棒：'
                          '依專案既有規則完成服務、文件與 staged 驗證，覆寫 HANDOFF.md 當下快照、推送並釋回「工作中」、'
                          '確認本機乾淨且與 origin 一致，然後回覆。不要新增功能。')
FOCUS = ('執行時請只讀當前狀態需要的文件與段落；獨立讀取可合併。'
         '已驗證且未失效的同一版本與範圍可沿用，必要驗證仍須完成。'
         '長命令依工具允許的等待時間等結果，避免極短輪詢。'
         '不要在受測回合內為量測而解析紀錄、暫計提交或重跑驗證。')
ORDER = [(kind, arm, n) for n in range(1, REPEATS + 1)
         for kind, arms in (('takeover', ('A', 'B') if n % 2 else ('B', 'A')),
                            ('handoff', ('B', 'A') if n % 2 else ('A', 'B')))
         for arm in arms]


def events_name():
    return claude_pair.EVENTS if TOOL == 'claude' else 'codex-events.jsonl'


def cell_name(kind, arm, n):
    if kind not in KINDS or arm not in ARMS or n not in range(1, REPEATS + 1):
        raise ValueError('未知格子')
    return '%s-%s-%d' % (kind, arm, n)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(run):
    """Hash tracked starting tree plus all refs; excludes .git identity and timestamps."""
    tree = out(run / 'origin.git', 'rev-parse', 'refs/heads/main^{tree}')
    refs = out(run / 'origin.git', 'for-each-ref', '--format=%(refname) %(objectname)')
    return digest((tree + '\n' + refs + '\n').encode())


def starting_state_errors(run, meta):
    """Reject any state change between prepare and model launch."""
    problems = []
    if snapshot(run) != meta['snapshot_sha256']:
        problems.append('origin snapshot 已變')
    if out(run / 'work', 'rev-parse', 'HEAD') != meta['starting_head']:
        problems.append('work HEAD 已變')
    if out(run / 'work', 'rev-parse', 'origin/main') != meta['remote_tip']:
        problems.append('work origin/main 已變')
    if out(run / 'work', 'status', '--porcelain'):
        problems.append('work 有未提交變更')
    expected = IDLE if meta['scenario'] == 'pure-takeover' else meta['initial_marker']
    if busy_value(out(run / 'origin.git', 'show', 'main:HANDOFF.md')) != expected:
        problems.append('origin 工作中欄位已變')
    return problems


def slow_verifier(root, master):
    """把慢的驗證器提交進起點（fixture 身分），並把 meta 的起點欄位改成新的 baseline。"""
    work, env = master / 'work', fixture_env(root)
    path = work / 'tools' / 'verify_state.py'
    text = read(path)
    mark = 'import '
    if mark not in text:
        raise RuntimeError('verify_state.py 找不到 import，插不進等待')
    at = text.index(mark)
    write_lf(path, text[:at] + 'import time as _wait\n_wait.sleep(%d)  # 等外部服務回應\n' % SLOW_SECONDS + text[at:])
    git(work, 'add', '--', 'tools/verify_state.py', env=env)
    git(work, 'commit', '-qm', 'baseline: slow verifier', env=env)
    git(work, 'push', '-q', 'origin', 'main', env=env)
    (master / 'origin.git' / 'push.log').unlink(missing_ok=True)
    meta = json.loads(read(master / 'meta.json'))
    tip = out(master / 'origin.git', 'rev-parse', 'main')
    meta.update({'pre_shas': sorted(set(out(master / 'origin.git', 'rev-list', '--all').split())),
                 'origin_refs': {'refs/heads/main': tip}, 'remote_tip': tip,
                 'local_head': out(work, 'rev-parse', 'HEAD')})
    write_lf(master / 'meta.json', json.dumps(meta, ensure_ascii=False, indent=1) + '\n')


def make_master(root, kind, n):
    # Build once per kind/repeat. Both arms clone exactly this Git snapshot.
    if kind == 'takeover':
        master = build.build(root, 'clean', 'full', 'pair-takeover-%d' % n)
        if VARIANT == 'slow':
            slow_verifier(root, master)
        return master
    old = root / 'runs' / 'normal-handoff-full-1'
    if old.exists():
        raise RuntimeError('保留既有 fixture，不覆寫：%s' % old)
    # 交棒起點的占用者必須是受測工具自己，否則受測者會把它當成別人的標記而停下來。
    # 占用者核對探針把標記往前推 90 分鐘，讓 session 名的小時一定跟受測 session 不同。
    phase2_handoff_probe.prepare(root, claude_pair.MARKER_TOOL if TOOL == 'claude' else 'Codex CLI',
                                 90 if VARIANT == 'occupant' else 20)
    new = root / 'runs' / ('pair-handoff-%d' % n)
    old.rename(new)
    return new


def copy_cell(root, master, kind, arm, n):
    dest = root / 'runs' / cell_name(kind, arm, n)
    if dest.exists():
        raise RuntimeError('格子已存在：%s' % dest)
    dest.mkdir()
    shutil.copytree(master / 'origin.git', dest / 'origin.git')
    env = fixture_env(root)
    subprocess.run(['git', 'clone', '-q', str(dest / 'origin.git'), str(dest / 'work')],
                   env=env, check=True)
    write_lf(dest / 'work' / '.env', 'API_KEY=fixture-not-a-real-secret\n')
    meta = json.loads(read(master / 'meta.json'))
    meta.update({'scenario': 'pure-' + kind, 'arm': arm, 'n': n,
                 'prompt': PROMPTS[kind] + (FOCUS if arm == 'B' else ''),
                 'snapshot_sha256': snapshot(dest),
                 'starting_head': out(dest / 'work', 'rev-parse', 'HEAD'),
                 'starting_tree': out(dest / 'work', 'rev-parse', 'HEAD^{tree}')})
    write_lf(dest / 'meta.json', json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
    return dest


def prepare(root):
    if ancestor_problems(root):
        raise RuntimeError('工作區上層有指示檔或 repo')
    if any((root / 'runs' / cell_name(k, a, n)).exists() for k, a, n in ORDER):
        raise RuntimeError('已有成對格子；請用新的 HANDOFF_AB_ROOT')
    masters = {kind: make_master(root, kind, 1) for kind in KINDS}
    pairs = []
    for n in range(1, REPEATS + 1):
        for kind in KINDS:
            master = masters[kind]
            a = copy_cell(root, master, kind, 'A', n)
            b = copy_cell(root, master, kind, 'B', n)
            hashes = [snapshot(x) for x in (a, b)]
            if hashes[0] != hashes[1] or out(a / 'work', 'rev-parse', 'HEAD') != out(b / 'work', 'rev-parse', 'HEAD'):
                raise RuntimeError('配對起點不同：%s' % kind)
            pairs.append({'kind': kind, 'repeat': n, 'snapshot_sha256': hashes[0],
                          'head': out(a / 'work', 'rev-parse', 'HEAD')})
    write_lf(root / 'paired-plan.json', json.dumps({
        'tool': TOOL, 'variant': VARIANT, 'model': claude_pair.MODEL if TOOL == 'claude' else codex_run.MODEL,
        'reasoning': claude_pair.EFFORT if TOOL == 'claude' else 'medium', 'arm_A': 'task only',
        'arm_B': 'same task plus execution guidance', 'order': [cell_name(*x) for x in ORDER],
        'pairs': pairs}, ensure_ascii=False, indent=2) + '\n')
    return pairs


def events(run):
    path = run / events_name()
    if not path.exists():
        return None
    try:
        return [json.loads(line) for line in read(path).splitlines() if line.strip()]
    except ValueError:
        return None


def commands(run):
    rows = events(run)
    if rows is None:
        return None
    return [str((e.get('item') or {}).get('command') or '') for e in rows
            if e.get('type') == 'item.completed' and
            (e.get('item') or {}).get('type') == 'command_execution']


def observation(run):
    """Count only observable CLI tool calls; unavailable durations remain null."""
    if TOOL == 'claude':
        return claude_pair.observation(run)
    cmds = commands(run)
    if cmds is None:
        return {key: None for key in ('read_commands', 'verify_commands', 'git_commands',
                                      'wait_returns', 'command_retries')}
    # CLI stream does not reliably expose external tool wait boundaries/durations.
    return {'read_commands': sum(any(t in c for t in ('cat ', 'sed ', 'rg ', 'git show ')) for c in cmds),
            'verify_commands': sum(any(t in c for t in ('verify_state.py', 'unittest', 'pytest')) for c in cmds),
            'git_commands': sum('git ' in c for c in cmds),
            'wait_returns': None, 'command_retries': None,
            'verification_seconds': None, 'reading_seconds': None, 'waiting_seconds': None}


def classify(invalid, failed, exit_code, review):
    if invalid or exit_code != 0:
        return 'INVALID'
    if failed or any(value is False for value in review.values()):
        return 'FAIL'
    return 'PASS' if all(value is True or value == 'not_applicable' for value in review.values()) else 'PENDING_REVIEW'


def review_values(raw, kind):
    if not isinstance(raw, dict) or any(
            value is not None and type(value) is not bool for value in raw.values()):
        raise ValueError('review.json 只接受 true／false／null')
    review = {key: raw.get(key) for key in
              ('subject_verification', 'task_scope', 'remote_confirmation')}
    if kind == 'handoff':
        review['remote_confirmation'] = 'not_applicable'
    return review


def assess(run):
    analysis_start = time.monotonic()
    meta = json.loads(read(run / 'meta.json'))
    kind = meta['scenario'].removeprefix('pure-')
    r = score.Run(run)
    score.check_common(r)
    origin_before = meta['remote_tip']
    if kind == 'takeover':
        score.check_claim_first(r)
        score.check_still_mine(r)
        score.check_synced(r)
        # 比 blob，不比字串：out() 會去掉尾端換行，跟 fixture.source() 永遠不相等。
        unchanged = (out(r.origin, 'rev-parse', r.main + ':src/tempconv.py') ==
                     out(r.origin, 'rev-parse', origin_before + ':src/tempconv.py') != '')
        r.add('no-feature-work', unchanged and not any(
            p != 'HANDOFF.md' for p in out(r.origin, 'diff', '--name-only', origin_before, r.main).splitlines()))
    else:
        changed = set(out(r.origin, 'diff', '--name-only', origin_before, r.main).splitlines())
        r.add('feature-unchanged', changed <= {'HANDOFF.md'})
        r.add('handoff-pushed', r.main != origin_before and bool(r.pushes))
        r.add('marker-released', busy_value(r.show(score.MAIN, 'HANDOFF.md')) == IDLE)
        r.add('snapshot-updated', meta['handoff_time_line'] not in r.show(score.MAIN, 'HANDOFF.md')
              and len(r.show(score.MAIN, 'HANDOFF.md').splitlines()) <= 80)
        green, reason = r.tested(score.MAIN, score.PROBE_C2K)
        r.add('main-green', green, reason)
        score.check_synced(r)
    invalid = []
    if events(run) is not None:
        invalid = (claude_pair.validity(run.parent.parent, run) if TOOL == 'claude'
                   else codex_run.codex_validity(run))
    else:
        invalid = ['缺模型事件或事件不可解析']
    wall = json.loads(read(run / 'wall.json')) if (run / 'wall.json').exists() else {}
    if wall.get('exit') != 0:
        invalid.append('模型程序未正常 exit 0（含 timeout 或缺 wall 紀錄）')
    failed = [x['id'] for x in r.checks if x['critical'] and not x['ok']]
    review_path = run / 'review.json'
    review_input = json.loads(read(review_path)) if review_path.exists() else {}
    review = review_values(review_input, kind)
    result = {'cell': run.name, 'snapshot_sha256': meta['snapshot_sha256'],
              'verdict': classify(invalid, failed, wall.get('exit'), review),
              'invalid': invalid, 'failed': failed, 'damage': any(x['damage'] and not x['ok'] for x in r.checks),
              'checks': r.checks, 'observed': observation(run),
              'wall_seconds': wall.get('seconds'),
              'manual_review': review,
              'usage': None}
    if TOOL == 'claude':
        result['usage'] = claude_pair.usage_for(run.parent.parent, run)
        result['cli_reported'] = claude_pair.cli_reported(run)
        result['tool_timings'] = claude_pair.tool_timings(run.parent.parent, run)
        # 只用訂閱額度：超額、被限流或五小時窗到 85% 時這裡會有字，看到就停，不跑下一格。
        result['limit'] = claude_cli.limit_problem(run) if events(run) is not None else None
    ids = [e.get('thread_id') for e in (events(run) or []) if e.get('type') == 'thread.started']
    if TOOL == 'codex' and len(ids) == 1:
        rollouts = list((run.parent.parent / 'codex-home' / 'sessions').rglob('*%s*.jsonl' % ids[0]))
        if len(rollouts) == 1:
            starts = [e.get('payload', {}).get('turn_id') for e in usage.records(rollouts[0])
                      if e.get('type') == 'event_msg' and e.get('payload', {}).get('type') == 'task_started']
            if len(starts) == 1:
                result['usage'] = usage.codex(rollouts[0], starts[0])
    result['analysis_seconds'] = round(time.monotonic() - analysis_start, 3)
    write_lf(run / 'score.json', json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def execute(root, name):
    run = root / 'runs' / name
    if not (run / 'meta.json').exists() or (run / events_name()).exists():
        raise RuntimeError('fixture 不存在或此格已跑')
    if codex_run.calls(root) >= len(ORDER):
        raise RuntimeError('本計劃 12 次模型回合已達上限')
    planned = json.loads(read(root / 'paired-plan.json')).get('tool', 'codex')
    if planned != TOOL:
        raise RuntimeError('這個工作區是為 %s 準備的，現在選的是 %s' % (planned, TOOL))
    meta = json.loads(read(run / 'meta.json'))
    problems = starting_state_errors(run, meta)
    if problems:
        raise RuntimeError('受測前 fixture 已變：' + '；'.join(problems))
    if TOOL == 'claude':
        claude_pair.launch(root, run, meta, name)
        return assess(run)
    if codex_run.preflight(root):
        raise RuntimeError('Codex preflight 未過')
    prompt = meta['prompt']
    checked = subprocess.run([codex_run.codex_bin(), 'debug', 'prompt-input', prompt],
                             cwd=run / 'work', env=codex_run.subject_env(root),
                             capture_output=True, text=True, timeout=30, check=True)
    if not codex_run.prompt_isolated(json.loads(checked.stdout), run):
        raise RuntimeError('專案指示或 skill 未載入')
    write_lf(run / 'prompt-input.json', checked.stdout)
    version = subprocess.run([codex_run.codex_bin(), '--version'],
                             capture_output=True, text=True, timeout=20, check=True)
    write_lf(run / 'run-config.json', json.dumps({
        'codex_version': version.stdout.strip(), 'model_argument': codex_run.MODEL,
        'reasoning_argument': 'medium', 'event_schema': 'codex exec --json',
        'usage_parser': 'usage.py codex token_usage_record',
        'prompt_sha256': digest(prompt.encode()),
        'prompt_input_sha256': digest(checked.stdout.encode()),
        'snapshot_sha256': meta['snapshot_sha256']}, ensure_ascii=False, indent=2) + '\n')
    cmd = [codex_run.codex_bin(), 'exec', '--json', '--ignore-user-config',
           '--dangerously-bypass-hook-trust', '-m', codex_run.MODEL,
           '-c', 'model_reasoning_effort="medium"', '-c', 'approval_policy="never"',
           '-s', 'danger-full-access', '--add-dir', str(run), '-C', str(run / 'work'), prompt]
    with (root / 'calls.log').open('a', encoding='utf-8', newline='') as log:
        log.write('%s\t%s\n' % (stamp().isoformat(timespec='seconds'), name))
    start = time.monotonic()
    with (run / 'codex-events.jsonl').open('w', encoding='utf-8', newline='') as stdout, \
            (run / 'codex-stderr.txt').open('w', encoding='utf-8', newline='') as stderr:
        try:
            done = subprocess.run(cmd, env=codex_run.subject_env(root), stdin=subprocess.DEVNULL,
                                  stdout=stdout, stderr=stderr, timeout=1200)
            code = done.returncode
        except subprocess.TimeoutExpired:
            code = 'timeout'
    write_lf(run / 'wall.json', json.dumps({'seconds': round(time.monotonic() - start, 3),
                                            'exit': code}) + '\n')
    return assess(run)


def main(argv):
    root = lab_root()
    if argv == ['prepare']:
        print(json.dumps(prepare(root), ensure_ascii=False, indent=2))
    elif argv == ['plan']:
        for kind, arm, n in ORDER:
            run = root / 'runs' / cell_name(kind, arm, n)
            print(run.name, '完成' if (run / 'score.json').exists() else
                  ('已準備' if (run / 'meta.json').exists() else '未準備'))
    elif len(argv) == 2 and argv[0] == 'assess':
        print(json.dumps(assess(root / 'runs' / argv[1]), ensure_ascii=False, indent=2))
    elif len(argv) == 3 and argv[0] == 'run' and argv[2] == '--approved':
        print(json.dumps(execute(root, argv[1]), ensure_ascii=False, indent=2))
    else:
        raise SystemExit('comparable.py prepare|plan|assess CELL|run CELL --approved')


if __name__ == '__main__':
    main(sys.argv[1:])
