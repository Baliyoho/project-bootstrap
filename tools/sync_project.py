#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把部署包的最新內容推到已經部署過的專案（本 repo 唯一的「發佈」工具）。

為什麼有這支：`verify_bootstrap.py` 只驗**權威版對不對**，沒有任何東西負責把它**發下去**，
所以歷來每次同步都是手工的。2026-10-30 盤點這台機器時，9 個裝過骨架的專案得用 find 掃才
找得出來，而且其中 4 個留著上一輪覆蓋了卻沒 commit 的殘留——手工做 7 次，漏掉是遲早的。

搭配 `git-freshness.sh` 的版本偵測一起用：偵測負責「讓你知道哪個落後」（落後的專案開場
會自己講），這支負責「一行把它修好」。只有後者的話，你還是得先想起來有哪些專案。

用法（在本 repo 根目錄執行）：
  python -X utf8 tools/sync_project.py ../NAS_MAINT           # 預演，只印要改什麼
  python -X utf8 tools/sync_project.py ../NAS_MAINT --write   # 實際寫入
  python -X utf8 tools/sync_project.py --all                  # 掃 ROOTS 找出所有裝過的專案
  python -X utf8 tools/sync_project.py --all --write

**本工具只改檔案，不 commit、不 push。** 那是交接程序（skill B7／B8）的事：專案的工作樹
可能有別人未提交的變更，替它 commit 會把那些一起包進去——而「明確 stage 需要的檔案」正是
B7 存在的理由。跑完請到各專案照 B 模式收尾。

**本工具不做「補裝」**：專案缺哪個檔就跳過哪個；唯一例外是已裝 Codex 接線的專案升級時，
補齊它新增依賴的 Windows 啟動器。沒有 `.codex/hooks.json` 就不補。在既有專案上
補一套不完整的骨架是 skill 的模式 0 該做的事，而且動手前要先把清單給使用者看過。

兩份 hook 接線（`.claude/settings.json`、`.codex/hooks.json`）是 2026-10-30 才補進來的，
補的理由寫在 WIRING 那段註解——它們是 JSON，塞不進 `source:` 版本標記，所以落後偵測也
看不到它們，三個專案就這樣停在舊版 matcher 一年半。

Python 版本下限見下面的 MIN_PY 與 `verify_bootstrap.py` 檔頭那一段（查核報告 F14）。
"""
import argparse
import copy
import json
import os
import pathlib
import shutil
import sys
import tempfile

# Python 版本下限（2026-11-02／查核報告 F14）。在檔頭就擋，而且訊息要說「版本太舊」——
# 高於下限的 API 不會在啟動時失敗，而是執行到那一行才炸成 TypeError／AttributeError，
# 那種形狀沒人會聯想到版本。兩支維護工具的 MIN_PY 必須一致，由「Python 版本下限」那一
# 項檢查釘住。
MIN_PY = (3, 8)
if sys.version_info < MIN_PY:
    sys.exit('需要 Python %d.%d 以上，本機是 %d.%d——請改用較新的 python'
             % (MIN_PY + sys.version_info[:2]))

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from verify_bootstrap import extract  # noqa: E402  重用範本抽取，不另寫一份

ROOT = pathlib.Path(__file__).resolve().parent.parent

# --all 要掃的根目錄。換一台機器、專案放別的地方就改這裡。
ROOTS = (pathlib.Path.home() / 'Desktop',)

# 整份覆蓋就對的檔：純制度內容，沒有任何專案專屬的值。
WHOLE = (
    '.claude/skills/handoff/SKILL.md',
    '.claude/hooks/git-freshness.sh',
    '.claude/hooks/pre-push-handoff.sh',
    '.claude/hooks/ag-wrap.sh',
    '.claude/hooks/codex-hook.cmd',
    '.agents/ag-hook.cmd',
    '.agents/skills/handoff/SKILL.md',
)
# 手術式更新：這一份混了「共用程式」與「專案自己的設定」，整份蓋過去會把設定洗掉。
SURGICAL = 'tools/check_docs.py'
SETTINGS_START = '# ── 專案設定（部署後依實際情況調整）'
SETTINGS_END = '# ── 專案設定結束'

# hook 接線（JSON）：只換「指向骨架那兩個 .sh」的那幾組，專案自己加的 permissions、env
# 與額外 hook 原樣保留。整份覆蓋會把那些洗掉，而不同步的代價 2026-10-30 現形：
# 2026-09-13 把 3.9 的 PreToolUse matcher 補成 `Bash|PowerShell` 之後，三個專案一直停在
# 舊的 `Bash`，而那台機器的主 shell 正是 PowerShell——pre-push 防呆整個不會觸發，而且
# 完全沒有徵兆。JSON 塞不進 `source:` 版本標記，落後偵測同樣看不到它們，所以這份清單
# 是這兩個檔唯一的守門人。
WIRING = ('.claude/settings.json', '.codex/hooks.json')
OWNED_SCRIPTS = ('git-freshness.sh', 'pre-push-handoff.sh')
CODEX_WIRING = '.codex/hooks.json'
CODEX_LAUNCHER = '.claude/hooks/codex-hook.cmd'

# Antigravity 的接線（2026-10-31 重新加入，這次端到端實測過：CLI 1.4.7 會讀、會觸發）。
# 它跟 WIRING 那兩個檔分開處理，因為形狀不同——Antigravity 的頂層 key 就是 hook 名稱，
# 所以骨架只擁有 AG_KEY 這一個 key，換掉它、其餘原樣保留就夠了，不必像 3.9／3.17 那樣
# 在同一個 hooks 物件裡逐組比對。這個「key 即命名空間」的形狀是它比另外兩家好處理的地方。
AG_WIRING = '.agents/hooks.json'
AG_KEY = 'handoff-git-check'

# 只補單一欄位／單一行，其餘歸專案自己。
PARTIAL = ('HANDOFF.md', '.gitignore', 'CLAUDE.md')
# 刻意不同步：部署後就歸專案自己，內容會長成專案的樣子（副本拓撲見 ARCHITECT.md）。
# 這份清單唯一的用途是讓 verify_bootstrap 的「同步清單涵蓋骨架」對得起來——新增一份範本
# 卻忘了歸類，會在那裡 FAIL，而不是安靜地沒人同步（那正是 WIRING 兩個檔踩過的坑）。
INSTANCE = (
    'AGENTS.md', 'ARCHITECT.md', 'GEMINI.md', 'README.md',
    'docs/ai-notes/handover-protocol.md', 'docs/ai-notes/roadmap.md',
    'tools/verify_state.py', '.gitattributes',
)

BUSY_FIELD = '- **工作中**：無（已交棒）'
GITIGNORE_LINES = ('.claude/.bootstrap-version', '.obsidian/')
# CLAUDE.md 2026-10-30 從 INSTANCE 搬到 PARTIAL：Claude Code 有 CLAUDE.md 就不原生讀
# AGENTS.md，所以舊版那句「去讀 AGENTS.md」的指標反而壓掉了保證載入的機制。補一行
# import 是純加法（官方說留著 import 不會讓它讀兩次），專案自己加的內容原樣保留。
# 不這樣做的話，這個修正只有新部署的專案拿得到，既有專案會無聲地停在舊行為。
CLAUDE_IMPORT = '@AGENTS.md'


def read(p):
    return p.read_text(encoding='utf-8') if p.exists() else None


def write(p, text):
    # 不用 Path.write_text(newline='')：那個參數要 3.10，見 verify_bootstrap.write_lf。
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def split_settings(text, require_end):
    """切成（含起始標記的前段、專案設定、從結束標記起的後段）。切不開就回 None。"""
    lines = text.split('\n')
    i = next((k for k, l in enumerate(lines) if l.startswith(SETTINGS_START)), None)
    if i is None:
        return None
    j = next((k for k, l in enumerate(lines) if k > i and l.startswith(SETTINGS_END)), None)
    if j is None:
        if require_end:
            return None
        # 舊副本還沒有結束標記：退回用「設定區塊後的第一個非設定常數」當邊界。
        j = next((k for k, l in enumerate(lines) if k > i and l.startswith('COUNT_RE')), None)
        if j is None:
            return None
    return lines[:i + 1], lines[i + 1:j], lines[j:]


def merge_check_docs(authority, current):
    """權威版的程式 ＋ 專案自己的設定。任一邊切不開就不動它（寧可不改，不要默默洗掉設定）。"""
    a = split_settings(authority, require_end=True)
    c = split_settings(current, require_end=False)
    if a is None:
        return None, '權威版切不出設定區塊（部署包的標記被改壞了？）'
    if c is None:
        return None, '專案這份切不出設定區塊，不敢動——請人工比對'
    return '\n'.join(a[0] + c[1] + a[2]), None


def handler_scripts(handler):
    """這一個 handler 指向哪些骨架腳本。

    `commandWindows` 也要看（2026-11-02）：Codex 的 Windows 接線把腳本名寫在那一欄，
    只看 `command` 的話「只有 Windows 命令」的 handler 會被當成專案自己的，於是骨架
    永遠不更新它，而落後的接線沒有任何徵兆。
    """
    if not isinstance(handler, dict):
        return frozenset()
    cmd = '%s %s' % (handler.get('command', ''), handler.get('commandWindows', ''))
    return frozenset(s for s in OWNED_SCRIPTS if s in cmd)


def scripts_in(group):
    """這一組 hook 指向哪些骨架腳本。用檔名比對，不挑路徑寫法。"""
    if not isinstance(group, dict):
        return frozenset()
    found = set()
    for h in group.get('hooks', []):
        found.update(handler_scripts(h))
    return frozenset(found)


def merge_group(auth_group, cur_group, event, key):
    """合併一組：骨架擁有的是**指向骨架腳本的那幾個 handler**，不是整組。

    2026-11-02 修（查核報告 F02）。舊版是 `cur[at] = deepcopy(g)`——只要一組裡有骨架
    handler，整組就被當成骨架的。於是專案把自己的 hook 加在同一組裡（`hooks` 陣列本來
    就能放多個，這是完全合法的形狀）就會被**靜默刪掉**，而輸出還寫著「專案其他設定原樣
    保留」。既有測試把專案的 hook 放在另一組，所以一直沒碰到這個形狀。

    組層設定（`matcher` 等）仍歸骨架：2026-09-13 那次事故要修的正是 matcher。但如果這
    一組裡有專案自己的 handler，而權威版又要改這一組的 matcher，那就會連專案那個
    handler 的觸發條件一起換掉——這種情況**拒絕並說清楚**，不要猜。
    """
    foreign = [h for h in cur_group.get('hooks', []) if not handler_scripts(h)]
    auth_own = [h for h in auth_group.get('hooks', []) if handler_scripts(h)]
    meta_now = {k: v for k, v in cur_group.items() if k != 'hooks'}
    meta_auth = {k: v for k, v in auth_group.items() if k != 'hooks'}
    clash = sorted(k for k, v in meta_auth.items() if k in meta_now and meta_now[k] != v)
    if foreign and clash:
        return None, (
            '%s 的「%s」那一組裡有專案自己的 handler（%s），而權威版要改這一組的 %s'
            '（%s → %s）——改下去會連專案那個 handler 的觸發條件一起換掉，不敢猜。'
            '請把專案自己的 handler 搬到另一組，或人工比對'
            % (event, '、'.join(sorted(key)),
               '、'.join(str(h.get('command', h))[:40] for h in foreign),
               '、'.join(clash),
               '、'.join(str(meta_now[k]) for k in clash),
               '、'.join(str(meta_auth[k]) for k in clash)))
    merged = dict(meta_now)
    merged.update(meta_auth)
    merged['hooks'] = ([copy.deepcopy(h) for h in auth_own]
                       + [copy.deepcopy(h) for h in foreign])
    return merged, None


def merge_ag_wiring(authority, current):
    """Antigravity 的接線：只換骨架擁有的那一個頂層 key，其餘原樣保留。

    形狀跟 3.9／3.17 不同——Antigravity 的頂層 key 就是 hook 名稱，所以骨架擁有的東西
    天生被 AG_KEY 圈起來，不必逐組比對。回傳 (新內容, 說明, 錯誤)；新內容為 None 且無
    錯誤＝已經一致，不要動它（照寫會把格式差異變成假變更，那種雜訊會讓人不再看輸出）。
    """
    try:
        a = json.loads(authority)
    except Exception as e:
        return None, None, '權威版不是合法 JSON（部署包被改壞了？）：%s' % e
    try:
        c = json.loads(current)
    except Exception as e:
        return None, None, '專案這份不是合法 JSON，不敢動——請人工比對：%s' % e
    if not isinstance(c, dict):
        return None, None, '專案這份的頂層不是物件，不敢動——請人工比對'
    if AG_KEY not in a:
        return None, None, '權威版裡找不到 %s——部署包被改壞了？' % AG_KEY

    want = copy.deepcopy(c)
    if want.get(AG_KEY) == a[AG_KEY]:
        return None, None, None
    had = AG_KEY in want
    want[AG_KEY] = copy.deepcopy(a[AG_KEY])
    note = '換掉 %s 的接線' % AG_KEY if had else '補回 %s 的接線' % AG_KEY
    return json.dumps(want, ensure_ascii=False, indent=2) + '\n', note, None


def merge_wiring(authority, current):
    """權威版的骨架 hook 接線 ＋ 專案自己的其他設定。

    回傳 (新內容, 說明, 錯誤)。新內容為 None 且無錯誤＝結構上已經一致，不要動它
    （照寫會把格式差異變成假變更，那種雜訊會讓人不再看同步輸出）。
    """
    try:
        a = json.loads(authority)
    except Exception as e:
        return None, None, '權威版不是合法 JSON（部署包被改壞了？）：%s' % e
    try:
        c = json.loads(current)
    except Exception as e:
        return None, None, '專案這份不是合法 JSON，不敢動——請人工比對：%s' % e
    if not isinstance(c, dict) or not isinstance(c.get('hooks', {}), dict):
        return None, None, '專案這份的結構不是預期的 {"hooks": {...}}，不敢動——請人工比對'

    want = copy.deepcopy(c)
    hooks = want.setdefault('hooks', {})
    repaired = []
    for event, groups in a.get('hooks', {}).items():
        cur = hooks.get(event)
        cur = list(cur) if isinstance(cur, list) else []
        used = set()
        for g in groups:
            key = scripts_in(g)
            if not key:
                continue                      # 不指向骨架腳本的組，骨架不插手
            at = [i for i, x in enumerate(cur)
                  if i not in used and scripts_in(x) == key]
            if len(at) > 1:
                return None, None, (
                    '專案的 %s 有 %d 組都指向「%s」，不敢猜要更新哪一組——'
                    '請人工比對後只留一組' % (event, len(at), '、'.join(sorted(key))))
            if not at:
                cur.append(copy.deepcopy(g))
                used.add(len(cur) - 1)
                repaired.append('補回 %s 的接線' % '、'.join(sorted(key)))
                continue
            merged, err = merge_group(g, cur[at[0]], event, key)
            if err:
                return None, None, err
            cur[at[0]] = merged
            used.add(at[0])
        # 還指向骨架腳本、卻沒有任何權威組認領的組：分組方式跟權威版不一樣。
        # 舊版會在後面另外 append 一組，於是同一支腳本掛兩次（開場印兩遍、防呆跑兩次）。
        orphan = [x for i, x in enumerate(cur) if i not in used and scripts_in(x)]
        if orphan:
            return None, None, (
                '專案的 %s 有 %d 組指向骨架腳本、但分組方式跟權威版不同（%s）——'
                '直接補一組會讓同一支腳本掛兩次，整組換掉又會動到不屬於骨架的東西。'
                '請人工比對' % (event, len(orphan),
                             '；'.join('、'.join(sorted(scripts_in(x))) for x in orphan)))
        hooks[event] = cur

    if want == c:
        return None, None, None
    note = '；'.join(repaired) if repaired else '換成權威版接線，專案其他設定原樣保留'
    return json.dumps(want, ensure_ascii=False, indent=2) + '\n', note, None


def ensure_busy_field(text):
    """在「Git 狀態」那節補上「工作中」欄位。已經有就不動。"""
    if '**工作中**' in text:
        return None
    lines = text.split('\n')
    at = next((k for k, l in enumerate(lines) if l.startswith('- **待續分支**')), None)
    if at is None:
        at = next((k for k, l in enumerate(lines) if l.strip() == '## Git 狀態'), None)
    if at is None:
        return None
    lines.insert(at + 1, BUSY_FIELD)
    return '\n'.join(lines)


def ensure_gitignore(text):
    missing = [l for l in GITIGNORE_LINES if l not in text.split('\n')]
    if not missing:
        return None
    tail = '' if text.endswith('\n') else '\n'
    return text + tail + '\n# Added by sync_project.py\n' + '\n'.join(missing) + '\n'


def ensure_claude_import(text):
    """CLAUDE.md 補上 `@AGENTS.md` import。已經有就不動，其餘內容原樣保留。"""
    lines = text.split('\n')
    if any(l.strip() == CLAUDE_IMPORT for l in lines):
        return None
    at = 1 if lines and lines[0].startswith('# ') else 0
    lines[at:at] = ['', CLAUDE_IMPORT] if at else [CLAUDE_IMPORT, '']
    return '\n'.join(lines)


class Plan:
    """一個同步目標的計畫：要改哪些檔、算不出來的有哪些。

    2026-11-02 加（查核報告 F03）。舊版邊算邊寫：`WHOLE` 那一圈在任何 JSON 驗證之前，
    所以一份壞掉的接線會在「已經覆蓋掉好幾個檔之後」才被發現；而 `FAIL` 只進訊息列、
    不影響 `changed` 也不影響結束碼，於是同步失敗一半照樣回 exit 0，最後還印
    「全部都已經是 v… 」。先算完、驗完、再寫，是這兩件事唯一的共同修法。
    """

    def __init__(self):
        self.msgs = []
        self.errors = []
        self.writes = []                      # [(path, text, rel)]

    def ok(self, rel):
        self.msgs.append('  ok     %s' % rel)

    def skip(self, rel, why):
        self.msgs.append('  skip   %s（%s）' % (rel, why))

    def fail(self, rel, why):
        self.msgs.append('  FAIL   %s：%s' % (rel, why))
        self.errors.append('%s：%s' % (rel, why))

    def update(self, path, rel, text, note=None):
        self.msgs.append('  UPDATE %s%s' % (rel, ('（%s）' % note) if note else ''))
        self.writes.append((path, text, rel))

    @property
    def changed(self):
        return len(self.writes)


def apply_plan(plan):
    """逐檔原子替換，回傳 (已套用的 rel, 失敗的 (rel, 原因) 或 None)。

    先寫同目錄的暫存檔再 `os.replace`：中途斷掉也不會留下半個檔（半個 JSON 接線
    比舊的接線更糟——它會讓整份設定失效，而那是靜默的）。一旦失敗就停，已經套用的
    必須講出來，否則人不知道這個專案現在是什麼狀態。
    """
    done = []
    for path, text, rel in plan.writes:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + '.sync-tmp')
            write(tmp, text)
            os.replace(tmp, path)
            done.append(rel)
        except OSError as e:
            return done, (rel, str(e))
    return done, None


def sync_wiring(project, gen, rels, plan):
    for rel in rels:
        dst, src = project / rel, gen / rel
        cur = read(dst)
        if cur is None:
            plan.skip(rel, '這個專案沒有這個檔')
            continue
        new, note, err = merge_wiring(read(src), cur)
        if err:
            plan.fail(rel, err)
        elif new is None:
            plan.ok(rel)
        else:
            plan.update(dst, rel, new, note)


def sync(project, gen, codex_only=False):
    """算出這個目標要改什麼，**不寫任何檔**。回傳 Plan；寫入是 apply_plan 的事。"""
    plan = Plan()
    if not codex_only:
        core = read(project / '.claude/skills/handoff/SKILL.md') or ''
        target = read(gen / '.claude/skills/handoff/SKILL.md') or ''
        def source(text):
            return next((s.strip() for s in text.splitlines() if '<!-- source:' in s), '無版本標記')
        plan.msgs.append('  核心版本：%s → %s' % (source(core), source(target)))
        protocol = read(project / 'docs/ai-notes/handover-protocol.md')
        if protocol is not None and '**核心優先序：SKILL.md**' not in protocol:
            plan.msgs.append('  MIGRATE docs/ai-notes/handover-protocol.md：舊實例須人工遷移優先序與 override；不覆蓋專案規則，新 skill 核心優先')

    for rel in WHOLE:
        if codex_only and rel != CODEX_LAUNCHER:
            continue
        dst, src = project / rel, gen / rel
        cur = read(dst)
        if cur is None:
            if rel != CODEX_LAUNCHER or not (project / CODEX_WIRING).exists():
                plan.skip(rel, '這個專案沒有這個檔')
                continue
        new = read(src)
        if cur == new:
            plan.ok(rel)
        else:
            plan.update(dst, rel, new)

    if codex_only:
        sync_wiring(project, gen, (CODEX_WIRING,), plan)
        return plan

    dst, src = project / SURGICAL, gen / SURGICAL
    cur = read(dst)
    if cur is None:
        plan.skip(SURGICAL, '這個專案沒有這個檔')
    else:
        merged, err = merge_check_docs(read(src), cur)
        if err:
            plan.fail(SURGICAL, err)
        elif merged == cur:
            plan.ok(SURGICAL)
        else:
            plan.update(dst, SURGICAL, merged, '保留專案設定區塊')

    sync_wiring(project, gen, WIRING, plan)

    dst, src = project / AG_WIRING, gen / AG_WIRING
    cur = read(dst)
    if cur is None:
        plan.skip(AG_WIRING, '這個專案沒有這個檔')
    else:
        new, note, err = merge_ag_wiring(read(src), cur)
        if err:
            plan.fail(AG_WIRING, err)
        elif new is None:
            plan.ok(AG_WIRING)
        else:
            plan.update(dst, AG_WIRING, new, note)

    h = project / 'HANDOFF.md'
    cur = read(h)
    if cur is None:
        plan.skip('HANDOFF.md', '不存在')
    else:
        new = ensure_busy_field(cur)
        if new is not None:
            plan.update(h, 'HANDOFF.md', new, '補上「工作中」欄位')
        elif '**工作中**' in cur:
            plan.ok('HANDOFF.md（「工作中」欄位已在）')
        else:
            plan.fail('HANDOFF.md', '找不到「待續分支」或「## Git 狀態」，無法插入欄位')

    gi = project / '.gitignore'
    cur = read(gi)
    if cur is None:
        plan.skip('.gitignore', '不存在')
    else:
        new = ensure_gitignore(cur)
        if new is None:
            plan.ok('.gitignore')
        else:
            plan.update(gi, '.gitignore', new, '補 %s' % '、'.join(
                l for l in GITIGNORE_LINES if l not in cur.split('\n')))

    cm = project / 'CLAUDE.md'
    cur = read(cm)
    if cur is None:
        plan.skip('CLAUDE.md', '不存在')
    else:
        new = ensure_claude_import(cur)
        if new is None:
            plan.ok('CLAUDE.md（已有 @AGENTS.md import）')
        else:
            plan.update(cm, 'CLAUDE.md', new, '補上 @AGENTS.md import')

    return plan


def discover():
    """裝過骨架的專案＝有 handoff skill 的目錄。worktree 是同一個 repo 其他分支的
    checkout，個別覆蓋只會製造互相打架的副本，所以排除——它們等分支合併才拿到。"""
    found = []
    for root in ROOTS:
        if not root.exists():
            continue
        for p in sorted(root.glob('*/.claude/skills/handoff/SKILL.md')):
            found.append(p.parents[3])
    return [p for p in found if 'worktrees' not in p.as_posix()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('project', nargs='?', help='要同步的專案路徑')
    ap.add_argument('--all', action='store_true', help='掃 ROOTS 底下所有裝過骨架的專案')
    ap.add_argument('--write', action='store_true', help='實際寫入（預設只預演）')
    ap.add_argument('--codex-only', action='store_true',
                    help='只更新 Codex 接線與其 Windows 啟動器，不更新 SKILL.md 或其他檔案')
    args = ap.parse_args()

    if not (ROOT / 'PROJECT-BOOTSTRAP.md').exists():
        print('找不到 PROJECT-BOOTSTRAP.md——請在本 repo 根目錄執行')
        return 2
    targets = discover() if args.all else ([pathlib.Path(args.project).resolve()]
                                           if args.project else [])
    if not targets:
        print('沒有目標。給一個專案路徑，或用 --all')
        return 2

    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='sync-project-'))
    planned = applied = 0
    failures = []
    try:
        extract(tmp)
        print('權威版 v%s（%d 個目標）\n' % (version, len(targets)))
        for project in targets:
            # 本 repo 自己不是同步目標（2026-11-01）。`--all` 掃不到它（discover() 靠
            # handoff skill 發現專案，這裡刻意沒有），但手打一個路徑進來本來會過——而這個
            # repo 的 `.claude/settings.json` 與 `.codex/hooks.json` 跟 WIRING 同名，指的
            # 卻是它自己那支 `repo-git-check.sh`；覆蓋下去就變成指向這裡不存在的
            # `git-freshness.sh`，開場檢查從此靜默失效（實測預演真的會印出兩個 UPDATE）。
            # 擋在這裡，而不是在文件裡寫一句「不要這樣做」——那種規則只在有人記得時有效。
            if project == ROOT:
                print('%s\n  這是權威版 repo 自己，不是同步目標：它的兩份接線指向自己那支'
                      ' repo-git-check.sh，覆蓋下去會指到這裡不存在的 git-freshness.sh\n'
                      % project)
                failures.append('%s：是權威版 repo 自己，拒絕同步' % project)
                continue
            if not project.exists():
                print('%s\n  找不到這個資料夾\n' % project)
                failures.append('%s：找不到這個資料夾' % project)
                continue
            plan = sync(project, tmp, codex_only=args.codex_only)
            print('%s' % project)
            print('\n'.join(plan.msgs))
            # 算不出來就整個目標跳過，一個檔都不寫（F03）：半套同步比沒同步更難查，
            # 因為看起來像是「同步過了」。
            if plan.errors:
                print('  → 這個目標有 %d 項算不出來，整個跳過，一個檔都沒改' % len(plan.errors))
                failures.append('%s：%s' % (project, '；'.join(plan.errors)))
                print()
                continue
            planned += plan.changed
            if args.write and plan.writes:
                done, failed = apply_plan(plan)
                applied += len(done)
                if failed:
                    rest = [r for _, _, r in plan.writes[len(done):]]
                    print('  🔴 寫入失敗：%s（%s）' % failed)
                    print('  已經套用：%s' % ('、'.join(done) or '無'))
                    print('  還沒套用：%s' % '、'.join(rest))
                    failures.append('%s：寫到 %s 失敗（%s），已套用 %d 項'
                                    % (project, failed[0], failed[1], len(done)))
            print()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print('🔴 %d 個目標沒有完成：' % len(failures))
        for f in failures:
            print('   ' + f)
    if not planned and not failures:
        print('全部都已經是 v%s，沒有東西要改。' % version)
        return 0
    if planned:
        if args.write:
            print('共套用 %d／%d 項。**還沒 commit**——到各專案照 skill 的 B 模式收尾：'
                  '跑 check_docs.py、明確 stage 這幾個檔、看過 staged 清單再 commit。'
                  % (applied, planned))
        else:
            print('預演：共 %d 項要改。加 --write 才寫入。' % planned)
    # 任何目標沒完成就非零退出：呼叫方（人或 CI）唯一看得到的訊號就是結束碼。
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
