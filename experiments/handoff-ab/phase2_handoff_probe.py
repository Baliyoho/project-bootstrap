#!/usr/bin/env python3
"""One normal, completed-work handoff probe using the existing full fixture."""
import json
import subprocess
import sys

import build
import codex_run
import fixture
import score
from common import MACHINE, fixture_env, git, lab_root, out, read, stamp, write_lf

PROMPT = ('我們這個 session 已把 celsius_to_kelvin 與測試做好並推到 origin。'
          '現在請完成正常交棒：核對目前狀態、覆寫 HANDOFF.md 為當下快照、'
          '推送交棒 commit、釋回「工作中」，最後確認本機與 origin 一致。'
          '我現在不在電腦前，請自行完成。')


def prepare(root, tool='Codex CLI', minutes_ago=20):
    run = root / 'runs' / 'normal-handoff-full-1'
    if run.exists():
        raise SystemExit('fixture 已存在')
    run = build.build(root, 'clean', 'full', 3)
    run.rename(root / 'runs' / 'normal-handoff-full-1')
    run = root / 'runs' / 'normal-handoff-full-1'
    work = run / 'work'
    git(work, 'remote', 'set-url', 'origin', run / 'origin.git')
    marker = fixture.marker(MACHINE, tool, minutes_ago)
    write_lf(work / 'src/tempconv.py', fixture.source(c2k=True))
    write_lf(work / 'tests/test_tempconv.py', fixture.tests(c2k=True))
    write_lf(work / 'HANDOFF.md', fixture.handoff(busy=marker, done_c2k=True, hours_ago=0))
    env = fixture_env(root)
    git(work, 'add', '--', 'src/tempconv.py', 'tests/test_tempconv.py', 'HANDOFF.md', env=env)
    git(work, 'commit', '-qm', 'feat: celsius to kelvin', env=env)
    git(work, 'push', '-q', 'origin', 'main', env=env)
    (run / 'origin.git' / 'push.log').unlink(missing_ok=True)
    meta = json.loads(read(run / 'meta.json'))
    meta['scenario'] = 'normal-handoff'
    meta['pre_shas'] = sorted(set(out(run / 'origin.git', 'rev-list', '--all').split()))
    meta['origin_refs'] = {'refs/heads/main': out(run / 'origin.git', 'rev-parse', 'main')}
    meta['remote_tip'] = meta['origin_refs']['refs/heads/main']
    meta['local_head'] = out(work, 'rev-parse', 'HEAD')
    meta['initial_marker'] = marker
    meta['handoff_time_line'] = next(line for line in read(work / 'HANDOFF.md').splitlines() if '交接時間' in line)
    (run / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(run)


def execute(root):
    run = root / 'runs' / 'normal-handoff-full-1'
    if (run / 'codex-events.jsonl').exists():
        raise SystemExit('已有模型紀錄')
    if codex_run.preflight(root):
        raise SystemExit('preflight 未過')
    checked = subprocess.run([codex_run.codex_bin(), 'debug', 'prompt-input', PROMPT],
                             cwd=run / 'work', env=codex_run.subject_env(root),
                             capture_output=True, text=True, timeout=30, check=True)
    if not codex_run.prompt_isolated(json.loads(checked.stdout), run):
        raise SystemExit('專案指示或 skill 未載入')
    (run / 'prompt-input.json').write_text(checked.stdout, encoding='utf-8')
    if codex_run.calls(root) >= 12:
        raise SystemExit('Codex fixture 呼叫次數達 12')
    cmd = [codex_run.codex_bin(), 'exec', '--json', '--ignore-user-config',
           '--dangerously-bypass-hook-trust', '-m', codex_run.MODEL,
           '-c', 'model_reasoning_effort="medium"', '-c', 'approval_policy="never"',
           '-s', 'danger-full-access', '--add-dir', str(run), '-C', str(run / 'work'), PROMPT]
    with (root / 'calls.log').open('a', encoding='utf-8') as log:
        log.write('%s\t%s\n' % (stamp().isoformat(timespec='seconds'), run.name))
    with (run / 'codex-events.jsonl').open('w', encoding='utf-8') as out_file, \
            (run / 'codex-stderr.txt').open('w', encoding='utf-8') as err_file:
        done = subprocess.run(cmd, env=codex_run.subject_env(root),
                              stdin=subprocess.DEVNULL, stdout=out_file, stderr=err_file,
                              timeout=1200)
    row = evaluate(run)
    row['exit'] = done.returncode
    (run / 'score.json').write_text(json.dumps(row, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(row['verdict'], row['failed'], 'exit', done.returncode)
    if row['verdict'] != 'PASS' or done.returncode:
        raise SystemExit(1)


def evaluate(run_path):
    run = score.Run(run_path)
    score.check_common(run)
    before = run.meta['remote_tip']
    now = run.main
    handoff = run.show(score.MAIN, 'HANDOFF.md')
    changed = before != now and git(run.origin, 'merge-base', '--is-ancestor', before, now, check=False).returncode == 0
    run.add('handoff-pushed', changed)
    run.add('marker-released', run.busy() is not None and run.busy().startswith('無'))
    run.add('snapshot-updated', run.meta['handoff_time_line'] not in handoff and len(handoff.splitlines()) <= 80)
    green, reason = run.tested(score.MAIN, score.PROBE_C2K)
    run.add('main-green', green, reason)
    score.check_synced(run)
    run.add('one-normal-completion', len(run.pushes) >= 1)
    validity = codex_run.codex_validity(run_path)
    failed = [x['id'] for x in run.checks if x['critical'] and not x['ok']]
    return {'scenario': 'normal-handoff', 'verdict': 'INVALID' if validity else ('FAIL' if failed else 'PASS'),
            'failed': failed, 'invalid': validity, 'damage': any(x['damage'] and not x['ok'] for x in run.checks),
            'checks': run.checks}


if __name__ == '__main__':
    if (sys.argv[1:] != ['prepare'] and sys.argv[1:] != ['run', '--approved']):
        raise SystemExit('phase2_handoff_probe.py prepare|run --approved；每格前另查訂閱用量')
    root = lab_root()
    (prepare if sys.argv[1] == 'prepare' else execute)(root)
