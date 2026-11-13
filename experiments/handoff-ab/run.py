#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""執行受測。每一次受測是一個獨立的 `claude -p` 新 session，對著剛搭好的拋棄式 repo。

用法：
  python3 -X utf8 run.py preflight                     只檢查環境，不呼叫模型
  python3 -X utf8 run.py plan                          印出 24 格的固定順序
  python3 -X utf8 run.py one <情境> <組別> <次> --approved
  python3 -X utf8 run.py all --approved                依固定順序跑還沒跑的格子

沒有 --approved 一律不呼叫模型。呼叫次數記在 <工作區>/calls.log，超過 24 次就拒絕，
要加跑得明確給 --extra N（每次加跑都要使用者另外批准）。

環境變數：
  HANDOFF_AB_ROOT   工作區（預設系統暫存目錄下的 pb-handoff-ab；必須在任何 repo 之外）
  HANDOFF_AB_HOME   real＝沿用真的家目錄（預設用工作區裡的空家目錄）
  CLAUDE_BIN        claude 執行檔（預設 CLAUDE_CODE_EXECPATH，再來是 PATH 上的 claude）
"""
import json
import os
import pathlib
import random
import shutil
import subprocess
import sys

import build
import score
from common import (ARMS, BUDGET, MODEL, PROMPTS, REPEATS, SCENARIOS, TIMEOUT,
                    ancestor_problems, home_mode, lab_root, prepare_root, real_home,
                    run_env, sh, stamp)

TOOLS = ['Bash', 'Read', 'Edit', 'Write', 'Glob', 'Grep', 'Skill']
SKILL_FILES = ('SKILL.md', 'mode-a.md', 'mode-a-stop.md', 'mode-b.md', 'mode-0.md', 'reasons.md')


def claude_bin():
    found = (os.environ.get('CLAUDE_BIN') or os.environ.get('CLAUDE_CODE_EXECPATH')
             or shutil.which('claude'))
    if not found or not os.path.exists(found):
        raise SystemExit('找不到 claude 執行檔；用 CLAUDE_BIN 指定')
    return found


def order():
    """24 格的固定順序：種子寫死，兩組交錯，避免某一組集中在額度或服務狀態不同的時段。"""
    cells = [(s, a, n) for n in range(1, REPEATS + 1) for s in SCENARIOS for a in ARMS]
    random.Random(20261112).shuffle(cells)
    # 第一格固定是極簡組的乾淨接棒：它同時當煙霧測試，隔離失效在這裡就會現形。
    first = ('clean', 'minimal', 1)
    if first not in cells:      # 第二輪沒有煙霧格：串流欄位第一輪已經對過
        return cells
    cells.remove(first)
    return [first] + cells


def login_command(root):
    env = run_env(root)
    return 'HOME="%s" CLAUDE_CONFIG_DIR="%s" "%s" auth login' % (
        env['HOME'], env['CLAUDE_CONFIG_DIR'], claude_bin())


def preflight(root, quiet=False):
    """不呼叫模型的檢查。回傳問題清單；空的才可以跑。"""
    problems = list(ancestor_problems(root) and
                    ['工作區上層有指示檔或 repo：%s' % ancestor_problems(root)] or [])
    prepare_root(root)
    env = run_env(root)
    config = pathlib.Path(env['CLAUDE_CONFIG_DIR'])
    # 坑 1：家目錄的 handoff skill 會蓋掉專案那份。這裡查「受測 session 看得到的兩個位置」。
    # 2026-11-13：第一次受測後，Claude Code 會自己把帳號同步的通用 skill 與內建 plugin 寫進
    # skills/synced、plugins/（兩組都拿到同一批，沒有 handoff）。所以查的是「有沒有交接程序」，不是「空不空」。
    if (config / 'CLAUDE.md').exists():
        problems.append('受測用的設定目錄出現了使用者層 CLAUDE.md')
    for sub in ('skills', 'commands', 'plugins', 'rules'):
        hits = [str(p) for p in (config / sub).rglob('*') if 'handoff' in p.name.lower()] if (config / sub).exists() else []
        if hits or ((config / sub).exists() and sub in ('commands', 'rules') and any((config / sub).iterdir())):
            problems.append('受測用的設定目錄的 %s 有交接程序或自訂內容：%s' % (sub, hits[:3]))
    home_skill = os.path.join(env['HOME'], '.claude', 'skills', 'handoff')
    if home_mode() == 'fake':
        if os.path.exists(os.path.join(env['HOME'], '.claude')):
            problems.append('空家目錄裡出現了 .claude：%s' % env['HOME'])
    elif os.path.isdir(home_skill):
        # 真家目錄模式：完整組的開場 hook 會拿它跟專案那份比，不同就多印一段警告。
        kit = build.REPO / 'src' / 'kit' / 'files' / '.claude' / 'skills' / 'handoff'
        for name in SKILL_FILES:
            mine, theirs = os.path.join(home_skill, name), kit / (name + '.tmpl')
            if not os.path.exists(mine) or open(mine, encoding='utf-8').read() != theirs.read_text(encoding='utf-8'):
                problems.append('真家目錄的 handoff skill 跟部署包不同（%s）；改用空家目錄或先同步' % name)
                break
    # 坑 3：環境是白名單，宿主 session 的變數一個都不會進去；這裡再確認一次。
    leaked = [k for k in env if k.startswith(('CLAUDE_CODE', 'CLAUDECODE', 'ANTHROPIC', 'AI_AGENT', 'CODEX'))]
    if leaked:
        problems.append('受測環境帶了宿主變數：%s' % leaked)
    status = sh([claude_bin(), 'auth', 'status'], env=env, check=False)
    try:
        auth = json.loads(status.stdout)
    except ValueError:
        auth = {}
    if not auth.get('loggedIn'):
        problems.append('受測用的設定目錄還沒登入。請你自己在終端機跑一次（我不搬憑證）：\n    ' + login_command(root))
    elif auth.get('authMethod') != 'claude.ai' or not auth.get('subscriptionType'):
        problems.append('登入方式不是訂閱（authMethod=%s）；這個實測只用訂閱額度' % auth.get('authMethod'))
    version = sh([claude_bin(), '--version'], env=env, check=False).stdout.strip()
    if not quiet:
        print('工作區：%s' % root)
        print('家目錄模式：%s（HOME=%s）' % (home_mode(), env['HOME']))
        print('claude：%s　%s' % (version, claude_bin()))
        print('登入：%s／%s' % (auth.get('authMethod'), auth.get('subscriptionType')))
        print('已用呼叫次數：%s／%s' % (calls(root), BUDGET))
        for p in problems:
            print('✗ ' + p)
        print('可以跑' if not problems else '還不能跑')
    return problems


def calls(root):
    log = root / 'calls.log'
    return len(log.read_text(encoding='utf-8').splitlines()) if log.exists() else 0


def command(prompt):
    return [claude_bin(), '-p', prompt, '--model', MODEL,
            '--output-format', 'stream-json', '--verbose', '--include-hook-events',
            '--permission-mode', 'dontAsk', '--allowedTools', *TOOLS,
            '--disallowedTools', 'WebFetch', 'WebSearch',
            '--no-session-persistence']


def limit_problem(run):
    """只用訂閱額度（2026-11-13 第一格跑完後加）：帳號允許超額時，撞到上限會直接轉成超額計費，
    串流不會報錯。所以每格跑完讀最後一筆 rate_limit_event，有超額、被限流或五小時窗用到九成就停。"""
    last = None
    for line in open(run / 'stream.jsonl', encoding='utf-8'):
        if '"rate_limit_event"' in line:
            try:
                last = json.loads(line).get('rate_limit_info') or {}
            except ValueError:
                pass
    if last is None:
        return None
    used = max((w.get('utilization') or 0) for w in (last.get('unifiedWindows') or {'x': {}}).values())
    if last.get('isUsingOverage'):
        return '已經在用超額額度'
    # allowed_warning 是「接近上限」的預告，不是限流（2026-11-13 第 8 格在七天窗 25% 時出現）；
    # 真正的界線是下面的用量門檻，留 15% 給同一個帳號上其他 session 的用量。
    if last.get('status') not in ('allowed', 'allowed_warning'):
        return '被限流（status=%s）' % last.get('status')
    if used >= 0.85:
        return '用量已到 %d%%' % round(used * 100)
    return None


def one(root, scenario, arm, n, extra=0):
    if calls(root) >= BUDGET + extra:
        raise SystemExit('呼叫次數已到 %s；加跑要 --extra N 並取得批准' % (BUDGET + extra))
    problems = preflight(root, quiet=True)
    if problems:
        raise SystemExit('preflight 沒過：\n' + '\n'.join(problems))
    run = build.build(root, scenario, arm, n)
    with open(root / 'calls.log', 'a', encoding='utf-8', newline='') as fh:
        fh.write('%s\t%s\n' % (stamp().isoformat(timespec='seconds'), run.name))
    with open(run / 'stream.jsonl', 'w', encoding='utf-8', newline='') as so, \
            open(run / 'stderr.txt', 'w', encoding='utf-8', newline='') as se:
        try:
            done = subprocess.run(command(PROMPTS[scenario]), cwd=run / 'work', env=run_env(root),
                                  stdin=subprocess.DEVNULL, stdout=so, stderr=se, timeout=TIMEOUT)
            code = done.returncode
        except subprocess.TimeoutExpired:
            code = 'timeout'
    row = score.score(run)
    row['exit'] = code
    row['limit'] = limit_problem(run)
    with open(run / 'score.json', 'w', encoding='utf-8', newline='') as fh:
        json.dump(row, fh, ensure_ascii=False, indent=1)
    print('%-20s %-8s %-10s exit=%s %s' % (run.name, row['verdict'], row['outcome'], code,
                                           '；'.join(row['invalid'] or row['failed'])))
    return row


def main(argv):
    root = lab_root()
    approved = '--approved' in argv
    extra = int(argv[argv.index('--extra') + 1]) if '--extra' in argv else 0
    args = [a for i, a in enumerate(argv)
            if not a.startswith('--') and (i == 0 or argv[i - 1] != '--extra')]
    if not args:
        print(__doc__)
        return 2
    if args[0] == 'preflight':
        return 1 if preflight(root) else 0
    if args[0] == 'plan':
        for i, cell in enumerate(order(), 1):
            done = (root / 'runs' / ('%s-%s-%s' % cell)).exists()
            print('%2d  %-8s %-8s %s%s' % (i, *cell, '　已跑' if done else ''))
        return 0
    if args[0] in ('one', 'all') and not approved:
        print('沒有 --approved：不呼叫模型。先跑 preflight 與 selfcheck.py，等使用者批准整批。')
        return 3
    if args[0] == 'one' and len(args) == 4:
        one(root, args[1], args[2], args[3], extra)
        return 0
    if args[0] == 'all':
        for i, cell in enumerate(order()):
            if (root / 'runs' / ('%s-%s-%s' % cell)).exists():
                continue
            row = one(root, *cell, extra=extra)
            if row.get('limit'):
                print('用量守門：%s。停在第 %s 格（%s），不重試。' % (row['limit'], i + 1, '-'.join(map(str, cell))))
                return 5
            if row['verdict'] == 'INVALID':
                # 不算數的那一次仍然花了一次呼叫。停下來讓人看原因，不自動重跑。
                print('這一次不算數，先停：%s' % row['invalid'])
                return 4
        return score.main(['--all'])
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
