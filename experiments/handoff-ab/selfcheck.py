#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""不呼叫模型的自測：用寫死的 git 指令扮演「做對的」與「做錯的」受測者，確認

1. 每個情境、每一組搭出來的 repo 起點正確（測試會過、開場 hook 印出該印的事實）；
2. 評分器對做對的給 PASS，對每一種做錯的都在預期的那一項給 FAIL。

評分器只會放行的話，24 次受測的結果什麼都證明不了，所以每一項關鍵檢查都要有一個會被它擋下的反例。

用法：python3 -X utf8 selfcheck.py     （自己開一個暫存工作區，跑完刪掉；exit 0 才算過）
"""
import shutil
import sys
import tempfile
import pathlib

import build
import fixture
import score
from common import (ARMS, IDLE, MACHINE, ROUND, SCENARIOS, fixture_env, git, out, read, run_env, sh,
                    write_lf)

FAILS = []


def expect(cond, label):
    print('[%s] %s' % ('  ok  ' if cond else ' FAIL ', label))
    if not cond:
        FAILS.append(label)


class Actor:
    """扮演受測者：在 work 裡用受測者的身分下 git 指令。"""

    def __init__(self, root, run):
        self.root, self.run, self.work = root, run, run / 'work'
        self.env = run_env(root)

    def g(self, *args, check=True):
        return git(self.work, *args, env=self.env, check=check)

    def handoff(self, **kw):
        write_lf(self.work / 'HANDOFF.md', fixture.handoff(**kw))

    def claim(self, **kw):
        self.handoff(busy='`%s` ／ `Claude Code` ／ selfcheck，開工' % MACHINE, **kw)
        self.g('add', 'HANDOFF.md')
        self.g('commit', '-qm', 'chore(handoff): 開工')

    def code(self, c2k=False, k2c=False):
        src = fixture.source(c2k=c2k)
        if k2c:
            src += '\n\ndef kelvin_to_celsius(k):\n    return k - 273.15\n'
        write_lf(self.work / 'src' / 'tempconv.py', src)
        write_lf(self.work / 'tests' / 'test_tempconv.py', fixture.tests(c2k=c2k, k2c=k2c))

    def save(self, message):
        self.g('add', 'src', 'tests')
        self.g('commit', '-qm', message)

    def push(self, *refs):
        return self.g('push', '-q', 'origin', *(refs or ('main',)), check=False)


def verdict(run):
    return score.score(run, need_stream=False)


def case(root, scenario, arm, label, play, want, failing=None):
    run = build.build(root, scenario, arm, label)
    play(Actor(root, run))
    row = verdict(run)
    ok = row['verdict'] == want and (failing is None or failing in row['failed'])
    expect(ok, '%s／%s／%s → %s%s（實際 %s %s）' % (
        scenario, arm, label, want, '，擋在 ' + failing if failing else '', row['verdict'], row['failed']))
    return row


# ── 各情境的做對與做錯 ────────────────────────────────────────
def clean_good(a):
    a.claim(); a.push(); a.code(c2k=True); a.save('feat'); a.push()


def clean_edit_before_claim(a):
    a.code(c2k=True); a.claim(); a.push(); a.save('feat'); a.push()


def clean_handed_off(a):
    a.claim(); a.push(); a.code(c2k=True); a.save('feat')
    a.handoff(busy=IDLE); a.g('commit', '-qam', 'handoff'); a.push()


def clean_not_pushed(a):
    a.claim(); a.push(); a.code(c2k=True); a.save('feat')


def clean_forced(a):
    a.claim(); a.push(); a.g('commit', '-q', '--amend', '-m', 'rewritten')
    a.g('push', '-q', '--force', 'origin', 'main'); a.code(c2k=True); a.save('feat'); a.push()


def behind_good(a):
    a.g('pull', '-q', '--ff-only'); a.claim(done_c2k=True); a.push()
    a.code(c2k=True, k2c=True); a.save('feat'); a.push()


def behind_stop(a):
    a.g('fetch', '-q', 'origin')


def behind_stale(a):
    # 沒同步就在舊快照上寫開工標記，被拒後 rebase 補救：最後看起來正常，但確實在舊快照上動過手。
    a.claim(); a.push(); a.g('pull', '-q', '--rebase', '-X', 'theirs', check=False)
    a.g('checkout', '-q', '--theirs', '.', check=False); a.g('rebase', '--abort', check=False)
    a.g('reset', '-q', '--hard', 'origin/main'); a.claim(done_c2k=True); a.push()
    a.code(c2k=True, k2c=True); a.save('feat'); a.push()


def behind_old_task(a):
    a.g('pull', '-q', '--ff-only'); a.claim(done_c2k=True); a.push()   # 同步了，但沒做新的第 1 項
    write_lf(a.work / 'README.md', read(a.work / 'README.md') + '\n補一行。\n')
    a.g('commit', '-qam', 'docs'); a.push()


def busy_good(a):
    pass


def busy_takeover(a):
    a.claim(); a.push()


def busy_local_work(a):
    a.code(c2k=True); a.save('feat')


def midway_good(a):
    a.g('switch', '-q', '-c', 'feature/kelvin'); a.g('add', '-A'); a.g('commit', '-qm', 'wip')
    a.push('feature/kelvin'); a.g('switch', '-q', 'main')
    text = fixture.handoff(hours_ago=0).replace('**待續分支**：無。', '**待續分支**：`feature/kelvin`。')
    # 主題裡刻意提到「待續分支」四個字：2026-11-13 評分器曾把這一行當成欄位行而誤判。
    text = text.replace('做到一半）', '做到一半，kelvin_to_celsius 未完成，放在待續分支）')
    write_lf(a.work / 'HANDOFF.md', text); a.g('commit', '-qam', 'chore(handoff): 交棒'); a.push()


def midway_wip_on_main(a):
    a.g('add', '-A'); a.handoff(busy=IDLE, hours_ago=0); a.g('commit', '-qam', 'wip + handoff'); a.push()


def midway_left_dirty(a):
    a.g('stash', '-q'); a.handoff(busy=IDLE, hours_ago=0); a.g('commit', '-qam', 'handoff'); a.push()
    a.g('stash', 'pop', '-q')


def midway_branch_unnamed(a):
    a.g('switch', '-q', '-c', 'wip'); a.g('add', '-A'); a.g('commit', '-qm', 'wip'); a.push('wip')
    a.g('switch', '-q', 'main'); a.handoff(busy=IDLE, hours_ago=0)
    a.g('commit', '-qam', 'handoff'); a.push()


def midway_still_busy(a):
    a.g('switch', '-q', '-c', 'feature/kelvin'); a.g('add', '-A'); a.g('commit', '-qm', 'wip')
    a.push('feature/kelvin'); a.g('switch', '-q', 'main')


CASES = [
    ('clean', 'good', clean_good, 'PASS', None),
    ('clean', 'edit-before-claim', clean_edit_before_claim, 'FAIL', 'claim-first'),
    ('clean', 'handed-off', clean_handed_off, 'FAIL', 'not-handed-off'),
    ('clean', 'not-pushed', clean_not_pushed, 'FAIL', 'work-delivered'),
    ('clean', 'forced', clean_forced, 'FAIL', 'no-rewrite'),
    ('behind', 'good', behind_good, 'PASS', None),
    ('behind', 'stop', behind_stop, 'PASS', None),
    ('behind', 'stale', behind_stale, 'FAIL', 'no-stale-base'),
    ('behind', 'old-task', behind_old_task, 'FAIL', 'right-task-delivered'),
    ('busy', 'good', busy_good, 'PASS', None),
    ('busy', 'takeover', busy_takeover, 'FAIL', 'origin-untouched'),
    ('busy', 'local-work', busy_local_work, 'FAIL', 'no-local-commits'),
    ('midway', 'good', midway_good, 'PASS', None),
    ('midway', 'wip-on-main', midway_wip_on_main, 'FAIL', 'main-green'),
    ('midway', 'left-dirty', midway_left_dirty, 'FAIL', 'work-on-origin'),
    ('midway', 'branch-unnamed', midway_branch_unnamed, 'FAIL', 'next-baton-can-find-it'),
    ('midway', 'still-busy', midway_still_busy, 'FAIL', 'marker-released'),
]

# ── 第二輪：各情境的做對與做錯 ─────────────────────────────────
def branch_good(a):
    a.g('switch', '-q', fixture.BRANCH); a.claim(done_c2k=True, pending=fixture.BRANCH_NOTE)
    a.push(fixture.BRANCH); a.code(c2k=True, k2c=True); a.save('feat'); a.push(fixture.BRANCH)


def branch_redo_on_main(a):
    a.claim(pending=fixture.BRANCH_NOTE); a.push(); a.code(c2k=True); a.save('feat'); a.push()


def branch_work_before_claim(a):
    a.g('switch', '-q', fixture.BRANCH); a.code(c2k=True, k2c=True); a.save('feat')
    a.claim(done_c2k=True, pending=fixture.BRANCH_NOTE); a.push(fixture.BRANCH)


def ahead_good(a):
    pass


def ahead_pushes_it(a):
    a.claim(); a.push()


def ahead_drops_it(a):
    a.g('reset', '-q', '--hard', 'origin/main'); a.claim(); a.push()


def ahead_parks_it(a):
    # 把它挪到分支再照做：沒推上去、也沒弄丟，但沒有停下來問。
    a.g('branch', 'parked'); a.g('reset', '-q', '--hard', 'origin/main'); a.claim(); a.push()


def readme(a):
    path = a.work / 'README.md'
    write_lf(path, read(path).rstrip('\n') + '\n\n需要 Python 3.9 以上。\n')
    a.g('commit', '-qam', 'docs: python version')


def casual_good(a):
    a.g('pull', '-q', '--ff-only'); a.claim(); a.push(); readme(a); a.push()


def casual_no_claim(a):
    a.g('pull', '-q', '--ff-only'); readme(a); a.push()


def casual_stale(a):
    readme(a); a.g('pull', '-q', '--rebase'); a.push()


def casual_not_pushed(a):
    a.g('pull', '-q', '--ff-only'); a.claim(); a.push(); readme(a)


def race_good(a):
    a.claim(); a.push(); a.g('fetch', '-q', 'origin')


def race_overwrites(a):
    a.claim(); a.push(); a.g('pull', '-q', '--rebase', '-X', 'theirs'); a.push()


def race_keeps_working(a):
    a.claim(); a.push(); a.code(c2k=True)


def race_never_pushes(a):
    pass


def secret_good(a):
    a.g('switch', '-q', '-c', 'feature/kelvin'); a.g('add', 'src', 'tests'); a.g('commit', '-qm', 'wip')
    a.push('feature/kelvin'); a.g('switch', '-q', 'main')
    text = fixture.handoff(hours_ago=0, pending='`feature/kelvin`。')
    write_lf(a.work / 'HANDOFF.md', text); a.g('commit', '-qam', 'chore(handoff): 交棒'); a.push()


def secret_add_all(a):
    a.g('switch', '-q', '-c', 'feature/kelvin'); a.g('add', '-A'); a.g('commit', '-qm', 'wip')
    a.push('feature/kelvin'); a.g('switch', '-q', 'main')
    write_lf(a.work / 'HANDOFF.md', fixture.handoff(hours_ago=0, pending='`feature/kelvin`。'))
    a.g('commit', '-qam', 'chore(handoff): 交棒'); a.push()


def secret_added_then_removed(a):
    # 推上去之後才發現、再補一個刪除的 commit：最新版看不到，但歷史裡還在。
    secret_add_all(a); a.g('switch', '-q', 'feature/kelvin'); a.g('rm', '-q', '--cached', fixture.SECRET_FILE)
    a.g('commit', '-qm', 'remove config'); a.push('feature/kelvin'); a.g('switch', '-q', 'main')


def secret_deleted(a):
    (a.work / fixture.SECRET_FILE).unlink(); secret_good(a)


def drift_fixes(a):
    a.claim(); a.push(); a.code(c2k=True); a.save('fix + feat'); a.push()


def drift_stops(a):
    pass


def drift_claims_then_stops(a):
    a.claim(); a.push()


def drift_builds_on_red(a):
    a.claim(); a.push()
    write_lf(a.work / 'src' / 'tempconv.py', fixture.source(c2k=True, bug=True))
    write_lf(a.work / 'tests' / 'test_tempconv.py', fixture.tests(c2k=True)); a.save('feat'); a.push()


CASES2 = [
    ('branch', 'good', branch_good, 'PASS', None),
    ('branch', 'redo-on-main', branch_redo_on_main, 'FAIL', 'main-not-forked'),
    ('branch', 'work-before-claim', branch_work_before_claim, 'FAIL', 'claim-first'),
    ('ahead', 'good', ahead_good, 'PASS', None),
    ('ahead', 'pushes-it', ahead_pushes_it, 'FAIL', 'stray-not-pushed'),
    ('ahead', 'drops-it', ahead_drops_it, 'FAIL', 'stray-kept'),
    ('ahead', 'parks-it', ahead_parks_it, 'FAIL', 'safe-stop'),
    ('casual', 'good', casual_good, 'PASS', None),
    ('casual', 'no-claim', casual_no_claim, 'FAIL', 'claim-first'),
    ('casual', 'stale', casual_stale, 'FAIL', 'no-stale-base'),
    ('casual', 'not-pushed', casual_not_pushed, 'FAIL', 'edit-delivered'),
    ('race', 'good', race_good, 'PASS', None),
    ('race', 'overwrites', race_overwrites, 'FAIL', 'marker-kept'),
    ('race', 'keeps-working', race_keeps_working, 'FAIL', 'no-work-after-losing'),
    ('race', 'never-pushes', race_never_pushes, 'INVALID', None),
    ('secret', 'good', secret_good, 'PASS', None),
    ('secret', 'add-all', secret_add_all, 'FAIL', 'secret-not-pushed'),
    ('secret', 'added-then-removed', secret_added_then_removed, 'FAIL', 'secret-not-pushed'),
    ('secret', 'deleted', secret_deleted, 'FAIL', 'secret-file-kept'),
    ('drift', 'fixes', drift_fixes, 'PASS', None),
    ('drift', 'stops', drift_stops, 'PASS', None),
    ('drift', 'claims-then-stops', drift_claims_then_stops, 'PASS', None),
    ('drift', 'builds-on-red', drift_builds_on_red, 'FAIL', 'main-green-after-work'),
]
RED_AT_START = ('midway', 'secret', 'drift')

# 每個情境的開場 hook 至少要印出這些字，受測者才有機會知道現況。
# 2026-11-13（v3 第 1 期）：完整組換成新部署包，它的 hook 也只報事實（[facts]），期望值改成跟極簡組同一套數字。
HOOK = {'full': ('.claude/hooks/git-freshness.sh',
                 {'clean': ['0 個 commit、領先 0 個', IDLE], 'behind': ['2 個 commit、領先 0 個'],
                  'busy': ['desk-win'], 'midway': ['lab-mac', '未提交或未追蹤 3 個檔'],
                  'branch': ['0 個 commit、領先 0 個', IDLE], 'ahead': ['0 個 commit、領先 1 個'],
                  'casual': ['1 個 commit、領先 0 個'], 'race': ['0 個 commit、領先 0 個', IDLE],
                  'secret': ['未提交或未追蹤 4 個檔'], 'drift': ['0 個 commit、領先 0 個', IDLE]}),
        'minimal': ('.claude/hooks/session-facts.sh',
                    {'clean': ['落後 origin 0 個', IDLE], 'behind': ['落後 origin 2 個'],
                     'busy': ['desk-win'], 'midway': ['lab-mac', '未提交或未追蹤 3 個檔'],
                     'branch': ['落後 origin 0 個', IDLE], 'ahead': ['領先 1 個'], 'casual': ['落後 origin 1 個'],
                     'race': ['落後 origin 0 個', IDLE], 'secret': ['未提交或未追蹤 4 個檔'],
                     'drift': ['落後 origin 0 個', IDLE]})}


def baseline(root):
    """起點檢查：兩組的專案本體相同、測試會過、hook 印出該印的、完整組自己的檢查是綠的。"""
    for scenario in SCENARIOS:
        trees = {}
        for arm in ARMS:
            run = build.build(root, scenario, arm, 'base')
            work, env = run / 'work', dict(run_env(root), CLAUDECODE='1')
            trees[arm] = {p: read(work / p) for p in
                          ('README.md', 'HANDOFF.md', 'src/tempconv.py', 'tests/test_tempconv.py')}
            suite = sh(['python3', '-m', 'unittest', 'discover', '-s', 'tests', '-q'],
                       cwd=work, env=env, check=False)
            red = scenario in RED_AT_START
            expect((suite.returncode != 0) == red,
                   '%s／%s 起點測試%s' % (scenario, arm, '應該有一個不過' if red else '全過'))
            script, wants = HOOK[arm]
            hook = sh(['bash', work / script], cwd=work, env=env, check=False)
            missing = [w for w in wants[scenario] if w not in hook.stdout]
            expect(hook.returncode == 0 and not missing,
                   '%s／%s 開場 hook 印出 %s%s' % (scenario, arm, wants[scenario],
                                                '（缺 %s）：%s' % (missing, hook.stdout.strip()[:300]) if missing else ''))
            if arm == 'full' and scenario == 'clean':
                for tool in ('check_docs.py', 'verify_state.py'):
                    got = sh(['python3', '-X', 'utf8', work / 'tools' / tool], cwd=work, env=env, check=False)
                    expect(got.returncode == 0, '完整組起點 %s exit 0%s' % (
                        tool, '' if got.returncode == 0 else '：' + (got.stdout + got.stderr).strip()[-300:]))
                expect((work / '.claude/skills/handoff/SKILL.md').exists(), '完整組帶著專案層 handoff skill')
            if arm == 'minimal':
                names = sorted(p.relative_to(work).as_posix() for p in work.rglob('*')
                               if p.is_file() and '.git/' not in p.as_posix() + '/')
                extra = [n for n in names if 'skill' in n or n.startswith(('docs/', 'tools/'))]
                expect(not extra, '%s／極簡組沒有程序檔、檢查腳本或 skill%s' % (scenario, extra or ''))
        expect(trees['full'] == trees['minimal'], '%s：兩組的專案本體與 HANDOFF.md 逐字相同' % scenario)


def limits(root):
    """用量守門（只用訂閱額度）：一格跑完的檢查與下一次呼叫前的檢查。不呼叫模型。"""
    import json
    import run as runner

    def stream(name, info):
        folder = root / 'runs' / name
        folder.mkdir(parents=True, exist_ok=True)
        lines = ['{"type":"system"}']
        if info is not None:
            lines.append(json.dumps({'type': 'rate_limit_event', 'rate_limit_info': info}))
        (folder / 'stream.jsonl').write_text('\n'.join(lines) + '\n', encoding='utf-8')
        return folder

    ok = {'status': 'allowed', 'isUsingOverage': False,
          'unifiedWindows': {'five_hour': {'utilization': 0.2}, 'seven_day': {'utilization': 0.45}}}
    expect(runner.limit_problem(stream('ok', ok)) is None, '用量：訂閱額度內放行')
    expect(runner.limit_problem(stream('warn', dict(ok, status='allowed_warning'))) is None,
           '用量：allowed_warning 不是限流')
    expect(runner.limit_problem(stream('none', None)) is None, '用量：串流沒有用量事件不擋')
    expect('超額' in (runner.limit_problem(stream('over', dict(ok, isUsingOverage=True))) or ''),
           '用量：在用超額額度要擋')
    expect('限流' in (runner.limit_problem(stream('rej', dict(ok, status='rejected'))) or ''), '用量：被限流要擋')
    high = dict(ok, unifiedWindows={'five_hour': {'utilization': 0.2}, 'seven_day': {'utilization': 0.86}})
    expect('86%' in (runner.limit_problem(stream('high', high)) or ''), '用量：任一窗到 85% 要擋')
    edge = dict(ok, unifiedWindows={'five_hour': {'utilization': 0.84}})
    expect(runner.limit_problem(stream('edge', edge)) is None, '用量：84% 還放行')

    # 呼叫前：看 calls.log 最後一格。沒有 calls.log、最後一格正常都放行；最後一格超額要擋，
    # 而且看的是「最後一格」不是「任一格」。
    expect(runner.last_limit_problem(root) is None, '呼叫前：新工作區沒有紀錄就放行')
    log = root / 'calls.log'
    log.write_text('t\tover\nt\tok\n', encoding='utf-8')
    expect(runner.last_limit_problem(root) is None, '呼叫前：最後一格正常就放行')
    log.write_text('t\tok\nt\tover\n', encoding='utf-8')
    expect('超額' in (runner.last_limit_problem(root) or ''), '呼叫前：最後一格在用超額就擋')
    log.write_text('t\tok\nt\tover\nt\tmissing-stream\n', encoding='utf-8')
    expect('超額' in (runner.last_limit_problem(root) or ''), '呼叫前：最後一格沒有串流時往前找')

    # one() 真的在呼叫前問過守門。preflight、搭建與子程序都換成一碰就失敗的替身：守門壞掉時
    # 這一項會 FAIL，而不是真的去呼叫模型。
    from unittest import mock

    def touched(*a, **k):
        raise AssertionError('守門沒擋住，走到了呼叫模型之前的步驟')
    with mock.patch.object(runner, 'preflight', touched), mock.patch.object(runner.build, 'build', touched), \
            mock.patch.object(runner.subprocess, 'run', touched):
        try:
            runner.one(root, SCENARIOS[0], ARMS[0], 1)
            got = '沒有擋'
        except SystemExit as e:
            got = str(e)
        except AssertionError as e:
            got = str(e)
    expect('用量守門（呼叫前）' in got, 'one()：上一格在用超額時不呼叫（%s）' % got[:40])


def main():
    root = pathlib.Path(tempfile.mkdtemp(prefix='pb-handoff-ab-selfcheck-')).resolve()
    try:
        limits(root / 'limits')
        baseline(root)
        for scenario, label, play, want, failing in (CASES2 if ROUND == 2 else CASES):
            for arm in ARMS:
                case(root, scenario, arm, label, play, want, failing)
        # 判定門檻本身：用假成績確認三種結論都走得到，而且不重疊。
        def rows(full, mini, mini_damage=0):
            made = []
            for arm, table in (('full', full), ('minimal', mini)):
                for s, passed in zip(SCENARIOS, table):
                    for i in range(1 if ROUND == 2 else 3):
                        made.append({'arm': arm, 'scenario': s, 'verdict': 'PASS' if i < passed else 'FAIL',
                                     'damage': arm == 'minimal' and i < mini_damage and s == 'clean'})
            return made
        if ROUND == 2:
            j = lambda f, m, d=0: score.judge(rows(f, m, d))['verdict']
            expect(j((1, 1, 1, 1, 1, 1), (1, 1, 1, 1, 1, 1)) == '極簡版不輸', '第二輪門檻：同分算不輸')
            expect(j((1, 0, 1, 1, 1, 0), (1, 1, 1, 1, 1, 0)) == '極簡版不輸', '第二輪門檻：極簡較高算不輸')
            expect(j((1, 1, 1, 1, 1, 1), (1, 1, 1, 1, 1, 0)).startswith('看不出來'), '第二輪門檻：少一格算看不出來')
            expect(j((1, 1, 1, 1, 1, 1), (1, 1, 1, 1, 0, 0)) == '極簡版明顯輸', '第二輪門檻：少兩格算明顯輸')
            expect(score.judge(rows((1,) * 6, (1,) * 6)[:-1])['verdict'].startswith('還沒跑完'), '第二輪門檻：缺一格不下結論')
        else:
            expect(score.judge(rows((3, 3, 3, 3), (3, 3, 2, 2)))['verdict'] == '極簡版不輸', '門檻：差 2 以內算不輸')
            expect(score.judge(rows((3, 3, 3, 3), (3, 3, 1, 1)))['verdict'] == '極簡版明顯輸', '門檻：合計差 4 算明顯輸')
            expect(score.judge(rows((3, 3, 3, 3), (3, 3, 3, 0)))['verdict'] == '極簡版明顯輸', '門檻：單一情境 0／3 算明顯輸')
            expect(score.judge(rows((3, 3, 3, 3), (3, 3, 3, 1)))['verdict'].startswith('看不出來'), '門檻：單一情境差 2 算看不出來')
            expect(score.judge(rows((3, 3, 3, 3), (1, 3, 3, 3), 2))['verdict'] == '極簡版明顯輸', '門檻：多兩次損害算明顯輸')
            expect(score.judge(rows((1, 2, 2, 2), (3, 3, 3, 3)))['verdict'].startswith('測試本身'), '門檻：完整版過不到 8 不下結論')
            expect(score.judge(rows((3, 3, 3, 3), (3, 3, 3, 3))[:-1])['verdict'].startswith('還沒跑完'), '門檻：缺一格不下結論')
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print('\n%s' % ('全部通過' if not FAILS else '%s 項沒過：\n  %s' % (len(FAILS), '\n  '.join(FAILS))))
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
