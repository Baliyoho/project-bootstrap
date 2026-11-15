#!/usr/bin/env python3
"""Same-session relay for Claude Code: turn 1 takes over, turn 2 hands off.

The pure handoff fixture asks a fresh session to release a marker it never wrote.
Here the subject writes its own marker in turn 1 and releases it in turn 2 of the
same session (`--resume`), so the occupant is really the subject.

  relay.py run CELL --approved     two subscription-backed turns on a prepared takeover cell
  relay.py assess CELL             re-score turn 2 from files; calls no model

Cells come from `comparable.py prepare` in a fresh HANDOFF_AB_ROOT (HANDOFF_AB_TOOL=claude);
only the takeover cells are used. Raw records stay under HANDOFF_AB_ROOT.
"""
import json
import pathlib
import subprocess
import sys
import time

import claude_pair
import comparable
import run as claude_cli
import score
import usage
from common import IDLE, MODEL_MARK, REPO, busy_value, lab_root, out, read, real_home, run_env, stamp, write_lf

EVENTS2 = 'stream2.jsonl'
PROMPT2 = ('現在請交棒。這一輪沒有新增功能，HANDOFF.md 的下一項留給下一棒。'
           '依專案既有規則完成服務、文件與 staged 驗證，覆寫 HANDOFF.md 當下快照、推送並釋回「工作中」、'
           '確認本機乾淨且與 origin 一致，然後回覆。不要新增功能。')


def prompt2(arm):
    return PROMPT2 + (comparable.FOCUS if arm == 'B' else '')


def events2(run):
    path = run / EVENTS2
    if not path.exists():
        return None
    try:
        return [json.loads(line) for line in read(path).splitlines() if line.strip()]
    except ValueError:
        return None


def turn2_record(root, run):
    """第二回合的 (session 紀錄, user uuid)。resume 後的 session id 以第二回合 init 為準；
    取紀錄裡最後一則人類訊息，而且它的文字必須就是第二句提示，否則回 (None, None)。"""
    rows = events2(run) or []
    inits = [e for e in rows if e.get('type') == 'system' and e.get('subtype') == 'init']
    if len(inits) != 1:
        return None, None
    path = claude_pair.session_file(root, inits[0].get('session_id'))
    if path is None:
        return None, None
    meta = json.loads(read(run / 'meta.json'))
    humans = [row for row in usage.records(path) if usage.human_user(row)]
    if len(humans) < 2:
        return None, None
    content = (humans[-1].get('message') or {}).get('content')
    text = content if isinstance(content, str) else ''.join(
        part.get('text', '') for part in content if isinstance(part, dict))
    if text.strip() != prompt2(meta['arm']).strip():
        return None, None
    return path, humans[-1].get('uuid')


def validity2(root, run):
    rows = events2(run)
    if rows is None:
        return ['沒有第二回合的串流紀錄']
    problems = []
    inits = [e for e in rows if e.get('type') == 'system' and e.get('subtype') == 'init']
    if len(inits) != 1 or MODEL_MARK not in str(inits[0].get('model', '')):
        problems.append('第二回合 init 不是剛好一個，或模型不符')
    results = [e for e in rows if e.get('type') == 'result']
    if len(results) != 1 or results[0].get('subtype') != 'success' or results[0].get('is_error'):
        problems.append('第二回合 result 不是剛好一個 success')
    outside = (real_home() + '/.claude', real_home() + '/.codex', str(REPO), 'PROJECT-BOOTSTRAP')
    for event in rows:
        if event.get('type') != 'assistant':
            continue
        for block in (event.get('message') or {}).get('content') or []:
            if isinstance(block, dict) and block.get('type') == 'tool_use' and any(
                    o in json.dumps(block.get('input') or {}, ensure_ascii=False) for o in outside):
                problems.append('第二回合碰了測試 repo 以外的制度檔')
    if turn2_record(root, run)[1] is None:
        problems.append('找不到第二回合唯一的 session 紀錄與 user uuid')
    return problems


def assess2(run):
    """第二回合（交棒）的評分。第一回合的評分在 score-turn1.json，這裡不重算。"""
    root = run.parent.parent
    meta = json.loads(read(run / 'meta.json'))
    turn1 = json.loads(read(run / 'score-turn1.json'))
    r = score.Run(run)
    score.check_common(r)
    before = meta['remote_tip']
    handoff = r.show(score.MAIN, 'HANDOFF.md')
    old_time = next((line for line in out(r.origin, 'show', before + ':HANDOFF.md').splitlines()
                     if '交接時間' in line), None)
    r.add('feature-unchanged',
          set(out(r.origin, 'diff', '--name-only', before, r.main).splitlines()) <= {'HANDOFF.md'})
    r.add('handoff-pushed', len(r.pushes) >= 2 and r.main != turn1.get('main_after_turn1'))
    r.add('marker-released', busy_value(handoff) == IDLE)
    r.add('snapshot-updated', bool(old_time) and old_time not in handoff
          and len(handoff.splitlines()) <= 80)
    green, reason = r.tested(score.MAIN)
    r.add('main-green', green, reason)
    score.check_synced(r)
    invalid = validity2(root, run)
    wall = json.loads(read(run / 'wall2.json')) if (run / 'wall2.json').exists() else {}
    if wall.get('exit') != 0:
        invalid.append('第二回合程序未正常 exit 0（含 timeout 或缺 wall 紀錄）')
    failed = [c['id'] for c in r.checks if c['critical'] and not c['ok']]
    review_path = run / 'review2.json'
    review = comparable.review_values(json.loads(read(review_path)) if review_path.exists() else {},
                                      'handoff')
    path, ident = turn2_record(root, run)
    rows = events2(run) or []
    calls = [b for e in rows if e.get('type') == 'assistant'
             for b in (e.get('message') or {}).get('content') or []
             if isinstance(b, dict) and b.get('type') == 'tool_use']
    result = {'cell': run.name, 'turn': 2,
              'verdict': comparable.classify(invalid, failed, wall.get('exit'), review),
              'invalid': invalid, 'failed': failed,
              'damage': any(c['damage'] and not c['ok'] for c in r.checks), 'checks': r.checks,
              'wall_seconds': wall.get('seconds'), 'manual_review': review,
              'tool_calls': len({b.get('id') for b in calls}) if rows else None,
              'skill_calls': len({b.get('id') for b in calls if b.get('name') == 'Skill'}) if rows else None,
              'usage': usage.claude(path, ident) if ident else None,
              'limit': claude_cli.limit_problem(run, EVENTS2) if rows else None}
    write_lf(run / 'score-turn2.json', json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def execute(root, name):
    run = root / 'runs' / name
    if not name.startswith('takeover-') or not (run / 'meta.json').exists():
        raise RuntimeError('relay 只用 prepare 出來的 takeover 格')
    if (run / EVENTS2).exists():
        raise RuntimeError('這一格的第二回合已跑')
    if not (run / 'score-turn1.json').exists():
        first = comparable.execute(root, name)          # 第一回合：純接棒，沿用同一套守門與評分
        first['main_after_turn1'] = out(run / 'origin.git', 'rev-parse', 'main')
        write_lf(run / 'score-turn1.json', json.dumps(first, ensure_ascii=False, indent=2) + '\n')
    first = json.loads(read(run / 'score-turn1.json'))
    if first['invalid'] or first['failed'] or first['damage'] or first.get('limit'):
        raise RuntimeError('第一回合無效、失敗或碰到用量守門，不跑第二回合')
    if claude_cli.preflight(root, quiet=True):
        raise RuntimeError('Claude preflight 未過')
    meta = json.loads(read(run / 'meta.json'))
    session_id = claude_pair.run_config(run)['session_id']
    cmd = claude_pair.command(prompt2(meta['arm']), session_id)
    at = cmd.index('--session-id')
    cmd[at] = '--resume'
    with (root / 'calls.log').open('a', encoding='utf-8', newline='') as log:
        log.write('%s\t%s\n' % (stamp().isoformat(timespec='seconds'), name))
    start = time.monotonic()
    with (run / EVENTS2).open('w', encoding='utf-8', newline='') as stdout, \
            (run / 'stderr2.txt').open('w', encoding='utf-8', newline='') as stderr:
        try:
            done = subprocess.run(cmd, cwd=run / 'work', env=run_env(root),
                                  stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                  timeout=1200)
            code = done.returncode
        except subprocess.TimeoutExpired:
            code = 'timeout'
    write_lf(run / 'wall2.json', json.dumps({'seconds': round(time.monotonic() - start, 3),
                                             'exit': code}) + '\n')
    return assess2(run)


def main(argv):
    if comparable.TOOL != 'claude':
        raise SystemExit('relay.py 只支援 HANDOFF_AB_TOOL=claude')
    root = lab_root()
    if len(argv) == 3 and argv[0] == 'run' and argv[2] == '--approved':
        print(json.dumps(execute(root, argv[1]), ensure_ascii=False, indent=2))
    elif len(argv) == 2 and argv[0] == 'assess':
        print(json.dumps(assess2(root / 'runs' / argv[1]), ensure_ascii=False, indent=2))
    else:
        raise SystemExit('relay.py run CELL --approved | assess CELL')


if __name__ == '__main__':
    main(sys.argv[1:])
