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

**本工具不做「補裝」**：專案缺哪個檔就跳過哪個，不會把沒裝過的檔案長出來。在既有專案上
補一套不完整的骨架是 skill 的模式 0 該做的事，而且動手前要先把清單給使用者看過。

兩份 hook 接線（`.claude/settings.json`、`.codex/hooks.json`）是 2026-10-30 才補進來的，
補的理由寫在 WIRING 那段註解——它們是 JSON，塞不進 `source:` 版本標記，所以落後偵測也
看不到它們，三個專案就這樣停在舊版 matcher 一年半。
"""
import argparse
import copy
import json
import pathlib
import shutil
import sys
import tempfile

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
# `.agents/hooks.json` 2026-10-31 加入，同日移除：實測 Antigravity 根本不讀專案層的那個檔
# （詳見部署包「跨工具與跨平台」的 Antigravity 一節）。這裡留一句是為了擋住「補回來」的衝動——
# 那個檔**部署出去也不會被觸發**，而一個不會觸發的 hook 比沒有更糟：它看起來像有防護。

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
    p.write_text(text, encoding='utf-8', newline='')


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


def scripts_in(group):
    """這一組 hook 指向哪些骨架腳本。用檔名比對，不挑路徑寫法。"""
    if not isinstance(group, dict):
        return frozenset()
    found = set()
    for h in group.get('hooks', []):
        cmd = h.get('command', '') if isinstance(h, dict) else ''
        found.update(s for s in OWNED_SCRIPTS if s in cmd)
    return frozenset(found)


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
        for g in groups:
            key = scripts_in(g)
            if not key:
                continue                      # 不指向骨架腳本的組，骨架不插手
            at = next((i for i, x in enumerate(cur) if scripts_in(x) == key), None)
            if at is None:
                cur.append(copy.deepcopy(g))
                repaired.append('補回 %s 的接線' % '、'.join(sorted(key)))
            else:
                cur[at] = copy.deepcopy(g)
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


def sync(project, gen, write_mode):
    """回傳 (改了幾項, [訊息])。"""
    msgs, changed = [], 0

    for rel in WHOLE:
        dst, src = project / rel, gen / rel
        cur = read(dst)
        if cur is None:
            msgs.append('  skip   %s（這個專案沒有這個檔）' % rel)
            continue
        new = read(src)
        if cur == new:
            msgs.append('  ok     %s' % rel)
            continue
        changed += 1
        msgs.append('  UPDATE %s' % rel)
        if write_mode:
            write(dst, new)

    dst, src = project / SURGICAL, gen / SURGICAL
    cur = read(dst)
    if cur is None:
        msgs.append('  skip   %s（這個專案沒有這個檔）' % SURGICAL)
    else:
        merged, err = merge_check_docs(read(src), cur)
        if err:
            msgs.append('  FAIL   %s：%s' % (SURGICAL, err))
        elif merged == cur:
            msgs.append('  ok     %s' % SURGICAL)
        else:
            changed += 1
            msgs.append('  UPDATE %s（保留專案設定區塊）' % SURGICAL)
            if write_mode:
                write(dst, merged)

    for rel in WIRING:
        dst, src = project / rel, gen / rel
        cur = read(dst)
        if cur is None:
            msgs.append('  skip   %s（這個專案沒有這個檔）' % rel)
            continue
        new, note, err = merge_wiring(read(src), cur)
        if err:
            msgs.append('  FAIL   %s：%s' % (rel, err))
        elif new is None:
            msgs.append('  ok     %s' % rel)
        else:
            changed += 1
            msgs.append('  UPDATE %s（%s）' % (rel, note))
            if write_mode:
                write(dst, new)

    h = project / 'HANDOFF.md'
    cur = read(h)
    if cur is None:
        msgs.append('  skip   HANDOFF.md（不存在）')
    else:
        new = ensure_busy_field(cur)
        if new is None:
            msgs.append('  ok     HANDOFF.md（「工作中」欄位已在，或找不到 Git 狀態那節）'
                        if '**工作中**' in cur else
                        '  FAIL   HANDOFF.md：找不到「待續分支」或「## Git 狀態」，無法插入欄位')
        else:
            changed += 1
            msgs.append('  UPDATE HANDOFF.md（補上「工作中」欄位）')
            if write_mode:
                write(h, new)

    gi = project / '.gitignore'
    cur = read(gi)
    if cur is None:
        msgs.append('  skip   .gitignore（不存在）')
    else:
        new = ensure_gitignore(cur)
        if new is None:
            msgs.append('  ok     .gitignore')
        else:
            changed += 1
            msgs.append('  UPDATE .gitignore（補 %s）' % '、'.join(
                l for l in GITIGNORE_LINES if l not in cur.split('\n')))
            if write_mode:
                write(gi, new)

    cm = project / 'CLAUDE.md'
    cur = read(cm)
    if cur is None:
        msgs.append('  skip   CLAUDE.md（不存在）')
    else:
        new = ensure_claude_import(cur)
        if new is None:
            msgs.append('  ok     CLAUDE.md（已有 @AGENTS.md import）')
        else:
            changed += 1
            msgs.append('  UPDATE CLAUDE.md（補上 @AGENTS.md import）')
            if write_mode:
                write(cm, new)

    return changed, msgs


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
    total = 0
    try:
        extract(tmp)
        print('權威版 v%s（%d 個目標）\n' % (version, len(targets)))
        for project in targets:
            if not project.exists():
                print('%s\n  找不到這個資料夾\n' % project)
                continue
            changed, msgs = sync(project, tmp, args.write)
            total += changed
            print('%s' % project)
            print('\n'.join(msgs))
            print()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if not total:
        print('全部都已經是 v%s，沒有東西要改。' % version)
        return 0
    if args.write:
        print('共改了 %d 項。**還沒 commit**——到各專案照 skill 的 B 模式收尾：'
              '跑 check_docs.py、明確 stage 這幾個檔、看過 staged 清單再 commit。' % total)
    else:
        print('預演：共 %d 項要改。加 --write 才寫入。' % total)
    return 0


if __name__ == '__main__':
    sys.exit(main())
