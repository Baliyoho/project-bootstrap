#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""驗證 PROJECT-BOOTSTRAP.md 這份部署包本身還能不能用（本 repo 唯一的驗證腳本）。

為什麼有這支：AGENTS.md 鐵律第 4 條要求「改完部署包要重生一次骨架驗證」，但在 2026-08-05
之前那是一段要人照著手刻的敘述——每一棒都得重刻一次，於是實務上常常跳過。把它固化成一個
指令，驗證才會真的發生。這支腳本本身不是「交接制度」（鐵律第 6 條講的是不要把 HANDOFF／
hooks 套到本 repo 身上），它是部署包的測試。

用法（在本 repo 根目錄執行）：
  python -X utf8 tools/verify_bootstrap.py
  python -X utf8 tools/verify_bootstrap.py --keep   # 保留產生的骨架供人工檢查
  python -X utf8 tools/verify_bootstrap.py --zip    # 全過才額外輸出解壓即用的 zip

zip 是建置產物，不進 Git（dist/ 已在 .gitignore）。要發佈就重跑一次，永遠不會有
一份會過期的壓縮檔躺在 repo 裡跟部署包唱反調。

檢查項（順序即執行順序；增減時同步 ARCHITECT.md「verify_bootstrap.py 守的東西」那張表。
這裡刻意不寫「做 N 件事」——數字會自己過期，2026-09-13 就漏算過一項）：
  重生骨架     ——把第 3 節每個範本抽成實體檔案，比對 EXPECTED 清單有沒有缺漏
  填佔位符     ——模擬一次真實部署，填完不該再有殘留
  check_docs   ——在填好的骨架跑，要 exit 0
  佔位符清單   ——check_docs 的 PLACEHOLDER_NAMES 要蓋住範本裡真正用到的佔位符，
                  漏一個名字就是那個洞永遠不會被檢查到，而且沒有任何跡象
  佔位符檢查   ——故意種一個佔位符回去，check_docs 必須 exit 2（否則 check_docs 的
                  佔位符檢查本身是壞的）
  日期標頭     ——拿掉 ARCHITECT.md 的「最後更新」，check_docs 必須 exit 2（2026-09-07 加
                  ARCHITECT.md 時補的）。守的是 check_docs 的 DATED_DIRS 有沒有真的涵蓋
                  ARCHITECT.md：漏掉不會有任何跡象，結構圖就會安靜地變成沒有日期、
                  沒人分得出是哪一天的事實
  真實部署形狀 ——把部署包與一個非 ASCII 檔名放回骨架裡再跑 check_docs，必須仍 exit 0
                  （2026-08-05 使用者回報實際部署踩到問題後補的）。這兩件事單獨看都不起眼，
                  合起來就是「照說明部署的人 100% 會踩到」
  跨平台防呆   ——掃絕對路徑，以及「用了 python 卻整份沒交代 python3 退路」的檔案。
                  這兩類問題在原機器上完全正常，換一台才壞，而且壞得無聲無息
  hook 五情境  ——pre-push：非 push／權威分支未更新 HANDOFF／已更新／feature／停用開關
  VERSION 檔   ——跟部署包開頭的版本行一致。各專案靠抓它判斷自己落後沒有，
                  不一致＝落後偵測說謊，而且沒有任何徵兆（2026-10-30 加入）
  版本落後偵測 ——種一個假的快取版本，git-freshness 要講；同版與開關 off 要閉嘴。
                  用快取餵假資料所以不打網路（2026-10-30 加入）
  跨工具表保鮮期——「跨工具與跨平台」那節的「查證日期」超過 90 天就 fail。對外部工具能力的
                  斷言會無聲過期，而上一次的對策是一句警告、警告沒擋住第二次（Antigravity
                  的 hooks、Codex 桌面 App 的 hooks）。`BOOTSTRAP_FRESHNESS=off` 可跳過
                  （2026-10-30 加入）
  工作中標記   ——HANDOFF.md 範本要有「工作中」欄位，且 git-freshness 讀 origin 那一份後
                  別台機器印 🔴、自己這台印 🟡、已交棒印 ✅、欄位不存在印 🟡。這條鏈斷掉
                  不會有徵兆，下一棒只會看到一切正常然後接棒（2026-10-30 加入）
  行末與雜項   ——本 repo 與重生骨架全 LF、兩份 JSON 設定合法、verify_state 與
                  git-freshness 可執行
  同步清單     ——sync_project.py 的清單要涵蓋骨架每一個檔，且 hook 接線合併要真的換掉
                  舊值又保住專案自己的設定。兩份 JSON 接線從來不在清單裡，於是 matcher
                  的修正一年半沒發下去，pre-push 防呆在那些專案等於沒裝（2026-10-30 加入）

結束碼：0＝全過；1＝有跳過項（缺 bash 之類）但無失敗；2＝有失敗。
本工具唯讀本 repo，只在系統暫存區寫檔。
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
KIT = ROOT / 'PROJECT-BOOTSTRAP.md'

# 第 3 節應該產出的檔案。少一份就是有人刪了範本卻沒發現；多一份就把它加進來。
EXPECTED = {
    'AGENTS.md', 'ARCHITECT.md', 'CLAUDE.md', 'GEMINI.md', 'HANDOFF.md', 'README.md',
    'docs/ai-notes/handover-protocol.md', 'docs/ai-notes/roadmap.md',
    '.claude/skills/handoff/SKILL.md', '.claude/settings.json',
    '.claude/hooks/git-freshness.sh', '.claude/hooks/pre-push-handoff.sh',
    '.codex/hooks.json', '.agents/skills/handoff/SKILL.md',
    '.claude/hooks/ag-wrap.sh', '.agents/ag-hook.cmd', '.agents/hooks.json',
    '.gitignore', '.gitattributes',
    'tools/check_docs.py', 'tools/verify_state.py',
}

# 模擬部署訪談的答案。值要「像真的」——URL 型佔位符填壞會誤觸 check_docs 的死連結檢查。
ANSWERS = {
    'PROJECT_NAME': '驗證用假專案',
    'ONELINER': '這是 verify_bootstrap.py 生成的測試骨架，不是真專案',
    'GH_OWNER': 'example-owner',
    'GH_REPO': 'example-repo',
    'GH_VISIBILITY': 'private',
    'LANG': '繁體中文',
    'TZ': 'Asia/Taipei',
    'TODAY': date.today().isoformat(),
    'SECRETS': '`.env`',
    'RUNTIME_DIRS': '`data/`',
    'STACK_DIRS': '`src/`',
    'VERIFY_TARGETS': '健康檢查 API',
}
# 與 check_docs.py 的第 5 項檢查同一套語法：雙大括號＋全大寫底線。放寬會誤判 verify_state.py
# 範本裡的 docker `--format '{{ .Names }}'`——那不是待填的洞。
PLACEHOLDER_RE = re.compile(r'\{\{([A-Z][A-Z0-9_]{1,40})\}\}')
HEAD_RE = re.compile(r'^### 3\.\d+ ')
FENCE_RE = re.compile(r'^(`{3,})(\w*)\s*$')

GIT_ENV = dict(
    os.environ,
    GIT_AUTHOR_NAME='verify', GIT_AUTHOR_EMAIL='verify@example.com',
    GIT_COMMITTER_NAME='verify', GIT_COMMITTER_EMAIL='verify@example.com',
    GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
)

# 工具身分的環境變數簽章（2026-10-31）。測 hook 的「同工具／不同工具」分支時必須先把
# 它們全部清掉再按情境放回去：verify 自己就跑在某個工具裡，os.environ 會把 CLAUDECODE
# 之類的變數帶進來，不清就變成「只有在某個工具上跑才會過」的測試——而「變數會被繼承、
# 會說謊」正是這段邏輯要擋的那件事，測試自己踩進去就什麼都證明不了。
TOOL_VARS = ('CLAUDECODE', 'AI_AGENT', 'CODEX_VERSION', 'CODEX_SESSION_ID',
             'CODEX_THREAD_ID', 'CODEX_CI', 'GEMINI_CLI')


def tool_env(**extra):
    env = {k: v for k, v in GIT_ENV.items() if k not in TOOL_VARS}
    env.update(extra)
    return env


results = []  # (status, 標題, 說明)  status: OK / FAIL / SKIP


def record(status, title, detail=''):
    results.append((status, title, detail))
    icon = {'OK': '  ok  ', ' FAIL ': ' FAIL ', 'FAIL': ' FAIL ', 'SKIP': ' skip '}[status]
    print(f'[{icon}] {title}{("  — " + detail) if detail else ""}')


def run(cmd, cwd=None, stdin=None, env=None):
    return subprocess.run(
        cmd, cwd=cwd, input=stdin, capture_output=True, text=True,
        encoding='utf-8', errors='replace', env=env or GIT_ENV,
    )


def git(args, cwd):
    return run(['git', *args], cwd=cwd)


def crlf_count(path):
    data = path.read_bytes()
    return data.count(b'\r\n')


_bash = False


def find_bash():
    """找一個看得懂 Windows 路徑的 bash。

    不能只用 shutil.which('bash')：Windows 上那常常是 WSL 的 bash，它讀不到 C:\\ 路徑，
    於是每個 hook 情境都回 1，看起來像 hook 壞了。用實際探測一個已知存在的檔案來篩掉它。
    """
    global _bash
    if _bash is not False:
        return _bash
    cands = []
    git_exe = shutil.which('git')
    if git_exe:                                   # Git for Windows：cmd/git.exe → bin/bash.exe
        base = pathlib.Path(git_exe).resolve().parent.parent
        cands += [base / 'bin' / 'bash.exe', base / 'usr' / 'bin' / 'bash.exe']
    found = shutil.which('bash')
    if found:
        cands.append(pathlib.Path(found))
    cands.append(pathlib.Path(r'C:\Program Files\Git\bin\bash.exe'))
    for c in cands:
        if not c.exists():
            continue
        probe = subprocess.run(
            [str(c), '-c', f'test -f "{KIT.as_posix()}"'], capture_output=True)
        if probe.returncode == 0:
            _bash = str(c)
            return _bash
    _bash = None
    return None


# ── 1. 重生骨架 ────────────────────────────────────────────────
def extract(dest):
    lines = KIT.read_text(encoding='utf-8', newline='').split('\n')
    heads = [i for i, ln in enumerate(lines) if HEAD_RE.match(ln)]
    written = set()
    for n, i in enumerate(heads):
        end = heads[n + 1] if n + 1 < len(heads) else len(lines)
        paths = [p for p in re.findall(r'`([^`]+)`', lines[i]) if '.' in p or '/' in p]
        if not paths:
            continue                       # 例：3.20 是慣例說明，不是檔案
        # 一節裡的圍籬區塊依序對應標題上的檔名；區塊比檔名少就全部沿用第一個
        # （多數節是一個檔、一個區塊）。2026-10-30 從「只取第一個區塊、事後改標題」
        # 改成這樣：3.2 的 CLAUDE.md 與 GEMINI.md 從此內容不同，而把其中一份合成在
        # 這支腳本裡，就等於讓範本內容有第二個家——部署包才是權威版。
        blocks, j = [], i
        while j < end:
            m = FENCE_RE.match(lines[j])
            if not m:
                j += 1
                continue
            fence = m.group(1)
            k, body = j + 1, []
            while k < end and lines[k].rstrip() != fence:
                body.append(lines[k])
                k += 1
            blocks.append('\n'.join(body) + '\n')
            j = k + 1
        if not blocks:
            continue
        for n_p, p in enumerate(paths):
            f = dest / p
            f.parent.mkdir(parents=True, exist_ok=True)
            with open(f, 'w', encoding='utf-8', newline='') as fh:
                fh.write(blocks[n_p] if n_p < len(blocks) else blocks[0])
            written.add(p)
    return written


def step_regenerate(dest):
    written = extract(dest)
    missing, extra = EXPECTED - written, written - EXPECTED
    if missing or extra:
        detail = ''
        if missing:
            detail += f'缺少 {sorted(missing)}'
        if extra:
            detail += f' 多出 {sorted(extra)}（新範本記得加進 EXPECTED）'
        record('FAIL', '重生骨架', detail.strip())
        return False
    record('OK', '重生骨架', f'{len(written)} 檔與 EXPECTED 一致')
    return True


# ── 2. 填佔位符 ────────────────────────────────────────────────
def step_fill(dest):
    unknown, seen, filled = set(), set(), 0
    for f in sorted(dest.rglob('*')):
        if not f.is_file():
            continue
        text = f.read_text(encoding='utf-8')
        if '{' not in text:
            continue

        def sub(m):
            key = m.group(1)
            seen.add(key)
            if key not in ANSWERS:
                unknown.add(key)
                return f'UNKNOWN_{key}'
            return ANSWERS[key]

        new, n = PLACEHOLDER_RE.subn(sub, text)
        if n:
            filled += n
            with open(f, 'w', encoding='utf-8', newline='') as fh:
                fh.write(new)
    left = [
        f.relative_to(dest).as_posix()
        for f in dest.rglob('*')
        if f.is_file() and PLACEHOLDER_RE.search(f.read_text(encoding='utf-8'))
    ]
    if unknown:
        record('FAIL', '填佔位符', f'第 1 節訪談表沒有這些佔位符：{sorted(unknown)}（新增佔位符要同步 ANSWERS）')
        return False
    if left:
        record('FAIL', '填佔位符', f'仍有殘留：{left}')
        return False
    record('OK', '填佔位符', f'替換 {filled} 處、{len(seen)} 種，無殘留')
    return seen


def step_placeholder_list(dest, seen):
    """check_docs.py 的 PLACEHOLDER_NAMES 必須蓋住範本裡真正出現的佔位符。

    那份清單是封閉列舉（不是語法比對），漏掉一個名字就是那個洞永遠不會被檢查到，
    而且沒有任何跡象——所以在這裡對一次。
    """
    src = (dest / 'tools' / 'check_docs.py').read_text(encoding='utf-8')
    m = re.search(r'PLACEHOLDER_NAMES\s*=\s*\(([^)]*)\)', src, re.S)
    if not m:
        record('FAIL', '佔位符清單涵蓋範本', 'check_docs.py 裡找不到 PLACEHOLDER_NAMES')
        return False
    declared = set(re.findall(r"'([A-Z0-9_]+)'", m.group(1)))
    missing = seen - declared
    if missing:
        record('FAIL', '佔位符清單涵蓋範本',
               f'範本用了但清單沒列：{sorted(missing)}——這些洞不會被檢查到')
        return False
    unused = declared - seen
    detail = f'{len(declared)} 個名字涵蓋範本用到的 {len(seen)} 種'
    if unused:
        detail += f'（{sorted(unused)} 只在訪談表出現，不進範本）'
    record('OK', '佔位符清單涵蓋範本', detail)
    return True


# ── 3./4. check_docs ───────────────────────────────────────────
def step_check_docs(dest):
    git(['init', '-q', '-b', 'main'], dest)
    git(['add', '-A'], dest)
    r = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
    if r.returncode != 0:
        record('FAIL', 'check_docs.py', f'exit {r.returncode}\n{r.stdout.strip()}\n{r.stderr.strip()}')
        return False
    record('OK', 'check_docs.py', 'exit 0')
    return True


def step_portability(dest):
    """跨平台／跨工具的靜默失效防呆。

    這兩類問題的共通點是「在原機器上完全正常，換一台才壞，而且壞得無聲無息」：
      - 絕對路徑：曾經真的發生——某專案的 .codex/hooks.json 寫死了
        C:\\Users\\<某人>\\Desktop\\<專案>\\...，那台機器一切正常，Mac 上 hook 直接不執行。
      - 硬寫 `python`：macOS／Linux 常常只有 python3，`python` 不存在。文件裡寫死
        `python xxx.py` 的那一行，換平台就是一句跑不動的指令。
    """
    abs_re = re.compile(r'[A-Za-z]:[\\/]Users[\\/]|/Users/[A-Za-z0-9._-]+/|/home/[A-Za-z0-9._-]+/')
    py_re = re.compile(r'(?<![a-zA-Z0-9_./-])python(?!3)(?![a-zA-Z0-9_])')
    bad = []
    for f in sorted(dest.rglob('*')):
        if not f.is_file() or '.git' in f.parts:
            continue
        rel = f.relative_to(dest).as_posix()
        text = f.read_text(encoding='utf-8')
        # 判準是「整份檔案有沒有交代退路」，不是每一行都得重述——逐行要求會逼出
        # 一堆複述噪音，而讀者是整份讀的。檔內任何一處提到 python3 就算交代過了。
        told = 'python3' in text
        for n, line in enumerate(text.split('\n'), 1):
            if abs_re.search(line):
                bad.append(f'{rel}:{n}  絕對路徑  {line.strip()[:60]}')
            if not told and py_re.search(line):
                bad.append(f'{rel}:{n}  用了 python 但整份沒交代 python3 退路  {line.strip()[:60]}')
    if bad:
        record('FAIL', '跨平台防呆', f'{len(bad)} 處：\n           ' + '\n           '.join(bad[:8]))
        return False
    record('OK', '跨平台防呆', '無絕對路徑、無缺 python3 退路的 python 呼叫')
    return True


def step_deploy_shape(dest):
    """模擬「剛解壓、還沒刪部署包」的真實部署形狀。

    2026-08-05 使用者實際部署時回報的兩個問題都只在這個形狀下出現，而原本的驗證流程
    剛好兩個都避開了——骨架裡沒有部署包、檔名又全是 ASCII：
      - 部署包還在專案裡時，它內嵌範本的相對路徑會被當成死連結（假警報），
        於是自檢清單第 1 項在刪檔之前永遠不可能通過。
      - 壓縮檔附的「讀我-先看這個.md」是非 ASCII 檔名，git ls-files 預設會輸出八進位
        跳脫字串，check_docs 直接 traceback 而不是 FAIL。比 FAIL 更糟：看起來像環境
        問題，接手的人會跳過驗證，正好繞開這套骨架唯一的文檔關卡。
    """
    kit_copy = dest / KIT.name
    noise = dest / '讀我-先看這個.md'
    shutil.copyfile(KIT, kit_copy)
    with open(noise, 'w', encoding='utf-8', newline='') as fh:
        fh.write('# 說明\n\n> 最後更新：2026-08-05\n')
    try:
        git(['add', '-A'], dest)
        r = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
        if 'Traceback' in r.stderr:
            tail = r.stderr.strip().splitlines()[-1][:120]
            record('FAIL', '真實部署形狀', f'check_docs 崩潰而非回報問題：{tail}')
            return False
        if r.returncode != 0:
            head = '\n           '.join(r.stdout.strip().splitlines()[:6])
            record('FAIL', '真實部署形狀', f'exit {r.returncode}\n           {head}')
            return False
        record('OK', '真實部署形狀', '部署包在場＋非 ASCII 檔名，check_docs 仍 exit 0')
        return True
    finally:
        kit_copy.unlink(missing_ok=True)
        noise.unlink(missing_ok=True)
        git(['add', '-A'], dest)


def step_placeholder_guard(dest):
    """故意種一個佔位符回去。抓不到就代表第 5 項檢查形同虛設。

    種的名字必須是 PLACEHOLDER_NAMES 裡真的有的（檢查是封閉清單比對，隨便編一個名字
    本來就不會被抓到，那樣這個測試會恆真、什麼都沒驗到）。
    """
    target = dest / 'docs' / 'ai-notes' / 'roadmap.md'
    original = target.read_text(encoding='utf-8')
    try:
        with open(target, 'a', encoding='utf-8', newline='') as fh:
            fh.write('\n- 這行是驗證用的：{{PROJECT_NAME}}\n')
        git(['add', '-A'], dest)
        r = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
        if r.returncode != 2 or 'PROJECT_NAME' not in r.stdout:
            record('FAIL', '佔位符檢查（負向測試）', f'期望 exit 2 並指出該行，實得 exit {r.returncode}')
            return False
        record('OK', '佔位符檢查（負向測試）', '殘留佔位符確實被擋下（exit 2）')
        return True
    finally:
        with open(target, 'w', encoding='utf-8', newline='') as fh:
            fh.write(original)
        git(['add', '-A'], dest)


def step_date_guard(dest):
    """拿掉 ARCHITECT.md 的日期標頭，check_docs 必須擋下。

    ARCHITECT.md 是被拿來「找檔案」的文件，沒有日期就無法判斷這份結構圖是哪一天的事實，
    而過期的結構圖比沒有更糟。它靠 check_docs 的 DATED_DIRS 把關——但那份清單漏掉一個
    名字不會有任何跡象（少一項檢查而已，照樣 exit 0），所以在這裡對一次。
    """
    target = dest / 'ARCHITECT.md'
    original = target.read_text(encoding='utf-8')
    stripped = '\n'.join(
        ln for ln in original.split('\n') if '最後更新' not in ln)
    try:
        with open(target, 'w', encoding='utf-8', newline='') as fh:
            fh.write(stripped)
        git(['add', '-A'], dest)
        r = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
        if r.returncode != 2 or 'ARCHITECT.md' not in r.stdout:
            record('FAIL', '日期標頭（負向測試）',
                   f'期望 exit 2 並指出 ARCHITECT.md，實得 exit {r.returncode}'
                   '——檢查 check_docs.py 的 DATED_DIRS 有沒有含 ARCHITECT.md')
            return False
        record('OK', '日期標頭（負向測試）', 'ARCHITECT.md 缺「最後更新」確實被擋下（exit 2）')
        return True
    finally:
        with open(target, 'w', encoding='utf-8', newline='') as fh:
            fh.write(original)
        git(['add', '-A'], dest)


def step_busy_tool_guard(dest):
    """「工作中」標記少了工具欄，check_docs 必須擋下（2026-10-31）。

    2026-10-31 把標記格式從 `機器` ／ `session 名` 改成 `機器` ／ `工具` ／ `session 名`。
    這種「加一欄」的格式變更有一個特性：少填那一欄不會壞掉，只會**靜默退化回舊行為**——
    hook 的同機器分支退回「大概是你自己另一個視窗」的 🟡，而退化後的畫面跟「從來沒有這個
    機制」一模一樣。所以 check_docs 第 6 項要擋，而這裡要證明它真的擋得住。
    """
    target = dest / 'HANDOFF.md'
    original = target.read_text(encoding='utf-8')
    field = '- **工作中**：'
    line = next((ln for ln in original.split('\n') if ln.startswith(field)), None)
    if line is None:
        record('FAIL', '工具欄（負向測試）', 'HANDOFF.md 範本找不到「工作中」欄位列')
        return False
    stale = field + '`desk-win` ／ `㊣　26103009｜測試｜工作中`，2026-10-30 09:12 (+08) 開工'
    try:
        with open(target, 'w', encoding='utf-8', newline='') as fh:
            fh.write(original.replace(line, stale))
        git(['add', '-A'], dest)
        r = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
        if r.returncode != 2 or '缺工具欄' not in r.stdout:
            record('FAIL', '工具欄（負向測試）',
                   f'期望 exit 2 並指出「缺工具欄」，實得 exit {r.returncode}'
                   '——檢查 check_docs.py 的 check_busy_field')
            return False
        record('OK', '工具欄（負向測試）',
               '舊格式標記（沒有工具欄）確實被擋下（exit 2）')
        return True
    finally:
        with open(target, 'w', encoding='utf-8', newline='') as fh:
            fh.write(original)
        git(['add', '-A'], dest)


# ── 5. pre-push hook 五情境 ────────────────────────────────────
def step_hook(dest, tmp):
    bash = find_bash()
    if not bash:
        record('SKIP', 'pre-push hook 五情境', '找不到看得懂 Windows 路徑的 bash（裝 Git for Windows 即可）')
        return None
    origin = tmp / 'origin.git'
    work = tmp / 'hookwork'
    run(['git', 'init', '-q', '--bare', str(origin)])
    shutil.copytree(dest, work, ignore=shutil.ignore_patterns('.git'))
    git(['init', '-q', '-b', 'main'], work)
    git(['add', '-A'], work)
    git(['commit', '-qm', 'init'], work)
    git(['remote', 'add', 'origin', str(origin)], work)
    git(['push', '-q', '-u', 'origin', 'main'], work)
    git(['remote', 'set-head', 'origin', 'main'], work)
    hook = str(work / '.claude' / 'hooks' / 'pre-push-handoff.sh')
    push = '{"tool_input":{"command":"git push origin main"}}'

    noise = []

    def fire(payload, env=None):
        r = run([bash, hook], cwd=work, stdin=payload, env=env or GIT_ENV)
        if r.stderr.strip():
            noise.append(r.stderr.strip()[:200])
        return r.returncode

    cases = []
    cases.append(('非 push 指令', 0, fire('{"tool_input":{"command":"git status -sb"}}')))

    (work / 'README.md').open('a', encoding='utf-8', newline='').write('\n驗證用改動\n')
    git(['commit', '-qam', 'docs: touch'], work)
    cases.append(('權威分支未更新 HANDOFF', 2, fire(push)))

    (work / 'HANDOFF.md').open('a', encoding='utf-8', newline='').write('\n- 驗證用\n')
    git(['commit', '-qam', 'chore: handoff'], work)
    cases.append(('HANDOFF 已更新', 0, fire(push)))

    git(['checkout', '-q', '-b', 'feature/x'], work)
    (work / 'README.md').open('a', encoding='utf-8', newline='').write('\nwip\n')
    git(['commit', '-qam', 'wip'], work)
    cases.append(('feature 分支', 0, fire('{"tool_input":{"command":"git push origin feature/x"}}')))

    git(['checkout', '-q', 'main'], work)
    cases.append(('HANDOFF_HOOK=off', 0, fire(push, env=dict(GIT_ENV, HANDOFF_HOOK='off'))))

    bad = [f'{n}：期望 {want}、實得 {got}' for n, want, got in cases if want != got]
    if bad:
        detail = '；'.join(bad)
        if noise:
            detail += '\n           hook stderr：' + ' | '.join(dict.fromkeys(noise))
        record('FAIL', 'pre-push hook 五情境', detail)
        return False
    record('OK', 'pre-push hook 五情境', '、'.join(f'{n}→{want}' for n, want, _ in cases))
    return work        # 有 origin、有 commit，git-freshness 才走得到比對邏輯


# ── 6. 行末與雜項 ──────────────────────────────────────────────
def busy_cases(push_busy, me):
    """兩支 hook 共用的「工作中」情境表（2026-10-31 起含工具欄）。

    刻意只有一份：3.10 的 `git-freshness.sh` 與本 repo 的 `repo-git-check.sh` 是分開維護的
    兩支腳本（檔頭寫了為什麼不抄），但它們該印的結論必須一樣——而「期望值有兩份」就是
    下一個會悄悄分岔的地方。

    回傳 (情境清單, 最後一次輸出)；最後一次輸出只給失敗時貼現場用。
    """
    sess = '`㊣　26103009｜測試｜工作中`'
    claude = tool_env(CLAUDECODE='1')
    cases = []

    out = push_busy('`other-box` ／ `Claude Code` ／ ' + sess, claude)
    cases.append(('別台機器→🔴', '🔴 另一台機器正在' in out and 'other-box' in out))

    out = push_busy('`%s` ／ `Claude Code` ／ %s' % (me, sess), claude)
    cases.append(('同機器同工具→🟡', '🟡 這台機器' in out and '「Claude Code」' in out
                  and '另一個工具正在' not in out))

    out = push_busy('`%s` ／ `Codex CLI` ／ %s' % (me, sess), claude)
    cases.append(('同機器不同工具→🔴', '🔴 同一台機器' in out and 'Codex CLI' in out))

    # 認不出自己是哪個工具 → 不准放行，但也不准假裝知道：印 🟡 並把「你自己是不是 X」
    # 明文丟給模型答。模型知道答案，hook 不知道——這是整段設計的支點。
    out = push_busy('`%s` ／ `Codex CLI` ／ %s' % (me, sess), tool_env())
    cases.append(('認不出自己→🟡且把問題丟回', '🟡 這台機器' in out
                  and '你自己是不是' in out and '另一個工具正在' not in out))

    # 兩家簽章同時在場＝在別的工具殼層裡被啟動、變數被繼承，這時不猜（實測見部署包
    # 「工具身分」一節：從 Claude Code 的殼層跑 codex，CLAUDECODE 整批都還在）。
    out = push_busy('`%s` ／ `Codex CLI` ／ %s' % (me, sess),
                    tool_env(CLAUDECODE='1', CODEX_VERSION='0.164.0'))
    cases.append(('兩家簽章同時在場→不猜', '🟡 這台機器' in out
                  and '另一個工具正在' not in out))

    out = push_busy('`%s` ／ %s' % (me, sess), claude)
    cases.append(('同機器舊格式→🟡', '🟡 這台機器' in out and '舊格式' in out
                  and '另一個工具正在' not in out))

    out = push_busy('無（已交棒）', claude)
    cases.append(('已交棒→✅', '✅ 「工作中」是' in out and '另一台機器正在' not in out
                  and '還有一個 session' not in out))
    return cases, out


def step_busy(dest, work):
    """「工作中」標記防呆（2026-10-30，2026-10-31 加工具欄）。

    守的是整條鏈：範本有欄位 → hook 讀得到 origin 那一份 → 別台機器印 🔴、同機器不同工具
    也印 🔴、同機器同工具印 🟡、認不出自己是哪個工具印 🟡 但把問題丟回給模型、交棒後不印。
    鏈上任何一環斷掉都不會有徵兆——下一棒只會看到一切正常然後接棒，而那正是這個機制要擋
    的那件事，所以它必須有自動測試。
    """
    field = '**工作中**'
    if field not in (dest / 'HANDOFF.md').read_text(encoding='utf-8'):
        record('FAIL', '工作中欄位在範本裡', 'HANDOFF.md 範本沒有「工作中」欄位，防呆沒有依據')
        return False
    record('OK', '工作中欄位在範本裡', 'HANDOFF.md 有「- **工作中**：無（已交棒）」')

    bash = find_bash()
    if not bash:
        record('SKIP', 'git-freshness 工作中標記', '找不到看得懂 Windows 路徑的 bash')
        return None
    if work is None:
        record('SKIP', 'git-freshness 工作中標記', 'hook fixture 沒建起來，缺少有 origin 的 repo 可測')
        return None

    # hook 用 ${HOSTNAME:-$(hostname)} 判斷「是不是這台機器」，這裡走同一條路徑取名字——
    # 自己另外用 socket.gethostname() 會在大小寫或 FQDN 上跟 hook 的實際行為對不上。
    me = run([bash, '-c', 'echo "${HOSTNAME:-$(hostname 2>/dev/null || uname -n 2>/dev/null)}"'],
             cwd=work).stdout.strip()
    hook = '.claude/hooks/git-freshness.sh'
    target = work / 'HANDOFF.md'
    base = target.read_text(encoding='utf-8')
    line = next((l for l in base.split('\n') if l.startswith('- ' + field)), None)
    if line is None:
        record('FAIL', 'git-freshness 工作中標記', 'fixture 的 HANDOFF.md 找不到「工作中」欄位列')
        return False

    def push_busy(value, env=None):
        target.write_text(base.replace(line, '- %s：%s' % (field, value)),
                          encoding='utf-8', newline='')
        git(['commit', '-qam', 'chore: busy'], work)
        git(['push', '-q', 'origin', 'main'], work)
        return run([bash, hook], cwd=work, env=env or tool_env()).stdout

    cases, out = busy_cases(push_busy, me)
    # 欄位整列拿掉：舊骨架的樣子。要印 🟡 說「查不了」，不能安靜放過——
    # 安靜放過跟「查過了沒事」在畫面上一模一樣，那就回到了這個機制要解決的問題本身。
    target.write_text(base.replace(line + '\n', ''), encoding='utf-8', newline='')
    git(['commit', '-qam', 'chore: drop busy field'], work)
    git(['push', '-q', 'origin', 'main'], work)
    out = run([bash, hook], cwd=work, env=tool_env()).stdout
    cases.append(('欄位不存在→🟡', '沒有「工作中」欄位' in out))

    bad = [n for n, good in cases if not good]
    if bad:
        record('FAIL', 'git-freshness 工作中標記',
               '、'.join(bad) + '\n           最後一次輸出：' + out.strip()[:200])
        return False
    record('OK', 'git-freshness 工作中標記', '、'.join(n for n, _ in cases))
    return True


def step_repo_busy(work):
    """本 repo 自己那支 hook 的「工作中」判讀（2026-10-30）。

    這個 repo 從多機維護開始就靠 `.claude/hooks/repo-git-check.sh` 擋誤接棒，而它刻意**不是**
    3.10 的副本（檔頭寫了為什麼：sync_project.py 的 discover() 掃不到這個 repo，抄整份就會
    變成唯一落後又沒有徵兆的那一份）。代價是 step_busy 測不到它——兩支各自演化的話，這裡
    就會變成「看起來有防護、實際上沒有」，而那正是這個機制要擋的那件事。

    順便釘住欄位字串：兩支讀的必須是同一個欄位。哪天 3.10 改了格式而這支沒跟上，它會對著
    一個永遠配不到的字串安靜放過每一次檢查。
    """
    field = '**工作中**'
    hook = ROOT / '.claude' / 'hooks' / 'repo-git-check.sh'
    if not hook.exists():
        record('FAIL', '本 repo 工作中判讀', 'repo-git-check.sh 不存在')
        return False
    if field not in hook.read_text(encoding='utf-8'):
        record('FAIL', '本 repo 工作中判讀',
               'repo-git-check.sh 沒讀「工作中」欄位——這個 repo 的跨機器防呆沒有依據')
        return False

    bash = find_bash()
    if not bash:
        record('SKIP', '本 repo 工作中判讀', '找不到看得懂 Windows 路徑的 bash')
        return None
    if work is None:
        record('SKIP', '本 repo 工作中判讀', 'hook fixture 沒建起來，缺少有 origin 的 repo 可測')
        return None

    me = run([bash, '-c', 'echo "${HOSTNAME:-$(hostname 2>/dev/null || uname -n 2>/dev/null)}"'],
             cwd=work).stdout.strip()
    target = work / 'HANDOFF.md'
    # step_busy 收尾時把欄位整列拿掉了，所以這裡自己重建一列，不依賴前一步留下的狀態。
    base = [l for l in target.read_text(encoding='utf-8').split('\n') if field not in l]

    def push_busy(value, env=None):
        body = '\n'.join(base)
        if value is not None:
            body = body.rstrip('\n') + '\n- %s：%s\n' % (field, value)
        target.write_text(body, encoding='utf-8', newline='')
        git(['commit', '-qam', 'chore: repo busy'], work)
        git(['push', '-q', 'origin', 'main'], work)
        return run([bash, hook.as_posix()], cwd=work, env=env or tool_env()).stdout

    cases, out = busy_cases(push_busy, me)
    out = push_busy(None, tool_env())
    cases.append(('欄位不存在→🟡', '沒有「工作中」欄位' in out))

    bad = [n for n, good in cases if not good]
    if bad:
        record('FAIL', '本 repo 工作中判讀',
               '、'.join(bad) + '\n           最後一次輸出：' + out.strip()[:200])
        return False
    record('OK', '本 repo 工作中判讀', '、'.join(n for n, _ in cases) + '，欄位字串與 3.10 一致')
    return True


def step_version_check(work):
    """骨架版本落後偵測（2026-10-30）。

    用快取檔餵假版本，所以**不打網路**：離線也驗得到，而且驗的正是比對邏輯本身
    （真正會壞的是比對，不是 curl）。三個情境：落後要講、同版要閉嘴、關掉開關要閉嘴。
    """
    bash = find_bash()
    if not bash or work is None:
        record('SKIP', '骨架版本落後偵測', '缺 bash 或 hook fixture')
        return None
    hook = '.claude/hooks/git-freshness.sh'
    cache = work / '.claude' / '.bootstrap-version'
    mark = '骨架落後'

    cache.write_text('1999-01-01', encoding='utf-8', newline='')
    lag = run([bash, hook], cwd=work).stdout
    off = run([bash, hook], cwd=work, env=dict(GIT_ENV, BOOTSTRAP_VERSION_CHECK='off')).stdout
    cache.write_text((ROOT / 'VERSION').read_text(encoding='utf-8').strip(),
                     encoding='utf-8', newline='')
    same = run([bash, hook], cwd=work).stdout
    cache.unlink(missing_ok=True)

    cases = [('落後→講', mark in lag), ('同版→閉嘴', mark not in same),
             ('開關 off→閉嘴', mark not in off)]
    bad = [n for n, good in cases if not good]
    if bad:
        record('FAIL', '骨架版本落後偵測',
               '、'.join(bad) + '\n           落後情境輸出：' + lag.strip()[:200])
        return False
    record('OK', '骨架版本落後偵測', '、'.join(n for n, _ in cases))
    return True


def template_link(target):
    """部署包裡指向「部署後才存在的檔」的連結不是死連結——那是範本內容，真正該檢查它的
    地方是重生出來的骨架（step_check_docs 就在那裡跑 check_docs.py）。判準用 EXPECTED
    本身而不是「整個 PROJECT-BOOTSTRAP.md 跳過」：這樣它指向本 repo 檔案的連結
    （README.md、ARCHITECT.md…）改檔名時照樣會被抓到。`<slug>` 那種示意路徑也跳過。"""
    if '<' in target:
        return True
    while target.startswith('../'):
        target = target[3:]
    return target in EXPECTED


def step_self():
    """本 repo 自己的 .md 與設定檔沒有任何自動檢查——`check_docs.py` 是骨架的檔，部署進來
    就成了副本，要跳版、要同步，而 sync_project.py 的 --all 又掃不到這個 repo（它靠
    handoff skill 發現專案，這裡刻意沒有）。所以改成在這支腳本多一項：同一個指令、同一份
    報告，沒有第二個會腐化的家。

    2026-10-30 加。在此之前 AGENTS／ARCHITECT／README 之間的相對連結從來沒有被檢查過；
    當天手掃是乾淨的，但那是一次快照，不是防護——死連結會在改檔名的那一次無聲出現。
    settings.json 一起查，是因為它壞掉的後果是 SessionStart hook 靜默不執行：那正是
    「看起來有防護、實際上沒有」的那一類失效，而且沒有任何徵兆。
    """
    ok = True
    mds = [m for m in run(['git', 'ls-files', '*.md'], cwd=ROOT).stdout.splitlines() if m]
    dead = []
    for rel in mds:
        base = (ROOT / rel).parent
        for link in re.findall(r'\]\(([^)]+)\)', (ROOT / rel).read_text(encoding='utf-8')):
            if link.startswith(('http://', 'https://', 'mailto:', '#')):
                continue
            target = link.split('#')[0]
            if not target:
                continue
            if rel == 'PROJECT-BOOTSTRAP.md' and template_link(target):
                continue
            if not (base / target).exists():
                dead.append('%s → %s' % (rel, link))
    undated = [rel for rel in ('AGENTS.md', 'ARCHITECT.md')
               if '最後更新' not in (ROOT / rel).read_text(encoding='utf-8')]
    if dead or undated:
        detail = []
        if dead:
            detail.append('死連結 %d 處：%s' % (len(dead), '、'.join(dead[:5])))
        if undated:
            detail.append('缺「最後更新」：%s' % '、'.join(undated))
        record('FAIL', '本 repo 自己的文件', '；'.join(detail))
        ok = False
    else:
        record('OK', '本 repo 自己的文件', '%d 個 .md 無死連結，日期標頭齊備' % len(mds))

    cfg = ROOT / '.claude' / 'settings.json'
    if not cfg.exists():
        record('SKIP', '本 repo settings.json', '不存在——開場沒有 git 檢查，接棒全靠人記得')
    else:
        try:
            json.loads(cfg.read_text(encoding='utf-8'))
            hook = ROOT / '.claude' / 'hooks' / 'repo-git-check.sh'
            if hook.exists():
                record('OK', '本 repo settings.json', '合法 JSON，且 repo-git-check.sh 在')
            else:
                record('FAIL', '本 repo settings.json', '指向的 repo-git-check.sh 不存在')
                ok = False
        except Exception as e:
            record('FAIL', '本 repo settings.json', str(e))
            ok = False
    return ok


def step_antigravity(dest):
    """Antigravity 接線的三個檔：轉接層的 JSON 與 escaping、shim 的兩個硬約束、接線的形狀。

    2026-10-31 端到端實測過（`agy -p` 讓 agent 把注入的開場訊息原文背出來），但那個測試
    需要裝著 Antigravity CLI 的機器，所以這裡釘的是**自動驗得出來的那部分**：管線會不會動、
    以及兩個踩過才知道的約束有沒有被「順手整理」掉——
      ① shim 必須全 ASCII：中文 `rem` 註解被 OEM code page 誤讀後會**整段被當成指令執行**，
         stderr 噴出 `is not recognized`，而 stdout 的 JSON 看起來還是對的，所以不會有徵兆。
      ② shim 不能有多行括號區塊或 label：檔案是 LF 行末（.gitattributes 強制全檔 LF），
         而 cmd.exe 讀 LF-only 檔案時這兩種結構會出錯。
    這兩項都是「看起來沒問題、實際壞掉」的類型，所以做成 fail 而不是註解裡的叮嚀。
    """
    wrap = dest / '.claude' / 'hooks' / 'ag-wrap.sh'
    shim = dest / '.agents' / 'ag-hook.cmd'
    wiring = dest / '.agents' / 'hooks.json'

    raw = shim.read_bytes()
    bad = []
    if any(b > 127 for b in raw):
        bad.append('shim 有非 ASCII 位元組（batch 的 echo 會依 OEM code page 變亂碼，'
                   '而被誤讀的註解會被當成指令執行）')
    text = raw.decode('ascii', 'replace')
    for n, ln in enumerate(text.split('\n'), 1):
        s = ln.strip()
        if s.startswith(':') and not s.startswith('::'):
            bad.append('shim 第 %d 行是 label（LF-only 檔案上 goto／label 會出錯）' % n)
        if s.endswith('(') and not s.lower().startswith('rem'):
            bad.append('shim 第 %d 行開了多行括號區塊（LF-only 檔案上會出錯）' % n)
    try:
        conf = json.loads(wiring.read_text(encoding='utf-8'))
    except Exception as e:
        record('FAIL', 'Antigravity 接線', '.agents/hooks.json 不是合法 JSON：%s' % e)
        return False
    hook = conf.get('handoff-git-check')
    if not isinstance(hook, dict):
        bad.append('hooks.json 少了 handoff-git-check 這個頂層 key（sync 靠它認骨架的接線）')
    else:
        if list(hook) != ['enabled', 'SessionStart']:
            bad.append('hooks.json 的 handoff-git-check 多了或少了欄位：%s'
                       '（PreToolUse 刻意不接——不明確回 allow_tool 就等於拒絕）' % list(hook))
        cmds = [h.get('command', '') for h in hook.get('SessionStart', [])]
        if not any(c.startswith('../') for c in cmds):
            bad.append('hooks.json 少了 Unix 那條 handler')
        if not any(c.startswith('.\\\\') or c.startswith('.\\') for c in cmds):
            bad.append('hooks.json 少了 Windows 那條（.\\ag-hook.cmd）handler')
        for c in cmds:
            if ':' in c or c.startswith('/'):
                bad.append('hooks.json 的 command 看起來是絕對路徑：%s'
                           '（換機器就靜默失效，而且 agy 的 command 不吃空白）' % c)

    bash = find_bash()
    if not bash:
        record('SKIP', 'Antigravity 接線', '這台機器上沒有 bash，轉接層的管線沒測到')
        return True

    # 轉接層的管線：拿一支會吐引號、反斜線與換行的腳本餵它，JSON 要合法且原樣還原。
    probe = dest / '.claude' / 'hooks' / '_probe.sh'
    payload = 'he said "hi"\\path\tand\nsecond line'
    probe.write_text('#!/usr/bin/env bash\nprintf \'%s\\n\' \'' + payload + '\'\n',
                     encoding='utf-8', newline='')
    for name, args, want in (
            ('正常注入', ['_probe.sh'], payload),
            ('少參數', [], '少了參數'),
            ('腳本不存在', ['_nope.sh'], '找不到'),
    ):
        r = run([bash, str(wrap)] + args, cwd=str(dest / '.agents'))
        try:
            got = json.loads(r.stdout)
        except Exception as e:
            bad.append('轉接層「%s」的 stdout 不是合法 JSON（%s）：%r'
                       % (name, e, r.stdout[:120]))
            continue
        msg = got.get('injectSteps', [{}])[0].get('ephemeralMessage', '')
        if want not in msg:
            bad.append('轉接層「%s」的訊息不對：%r' % (name, msg[:120]))
    probe.unlink()

    # 接線合併：骨架只擁有 handoff-git-check 這一個頂層 key，要換得掉又不能動到專案自己的。
    sys.path.insert(0, str(ROOT / 'tools'))
    import sync_project as sp
    auth = wiring.read_text(encoding='utf-8')
    stale = json.loads(auth)
    stale[sp.AG_KEY]['SessionStart'] = [{'type': 'command', 'command': 'OLD'}]
    stale['project-own-hook'] = {'enabled': True, 'Stop': [{'command': 'mine'}]}
    new, _, err = sp.merge_ag_wiring(auth, json.dumps(stale, ensure_ascii=False, indent=2))
    if err or new is None:
        bad.append('AG 接線合併沒認出落後的 %s（落後的專案不會被修好）：%s'
                   % (sp.AG_KEY, err or '說已經一致'))
    else:
        got = json.loads(new)
        if got.get(sp.AG_KEY) != json.loads(auth)[sp.AG_KEY]:
            bad.append('AG 接線合併沒把 %s 換成權威版' % sp.AG_KEY)
        if got.get('project-own-hook', {}).get('Stop', [{}])[0].get('command') != 'mine':
            bad.append('AG 接線合併把專案自己的 hook 洗掉了')
    same, _, err2 = sp.merge_ag_wiring(auth, auth)
    if err2 or same is not None:
        bad.append('AG 接線已一致卻說要改（每次同步都製造假變更，雜訊會讓人不再看輸出）')
    if sp.merge_ag_wiring(auth, '{壞掉')[2] is None:
        bad.append('AG 接線合併吃到壞 JSON 卻沒回報錯誤')

    if bad:
        record('FAIL', 'Antigravity 接線', '；'.join(bad))
        return False
    record('OK', 'Antigravity 接線',
           '轉接層三情境的 JSON 與 escaping 正確、shim 全 ASCII 且無括號區塊／label、'
           'hooks.json 兩個 handler 都在且只接 SessionStart、接線合併換得掉又保住專案自己的')
    return True


def step_sync_coverage(dest):
    """同步清單要涵蓋骨架每一個檔，而且 hook 接線真的會被修好。

    2026-10-30 查出來的洞：`.claude/settings.json` 與 `.codex/hooks.json` 兩份 hook 接線
    從來不在 sync_project.py 的清單裡。所以 2026-09-13 把 3.9 的 PreToolUse matcher 補成
    `Bash|PowerShell` 之後，三個專案一直停在舊的 `Bash`——而那台機器的主 shell 正是
    PowerShell，於是 pre-push 防呆整個不會觸發，且完全沒有徵兆。這兩個檔是 JSON，塞不進
    `source:` 版本標記，落後偵測也看不到它們，等於沒人在看。所以這裡釘兩件事：清單有沒有
    涵蓋全部範本（新增範本忘了歸類就 FAIL，而不是安靜地沒人同步），以及接線合併有沒有
    真的換掉舊值、又保住專案自己加的設定。
    """
    sys.path.insert(0, str(ROOT / 'tools'))
    import sync_project as sp

    declared = (set(sp.WHOLE) | {sp.SURGICAL} | set(sp.WIRING) | {sp.AG_WIRING}
                | set(sp.PARTIAL) | set(sp.INSTANCE))
    missing, extra = EXPECTED - declared, declared - EXPECTED
    if missing or extra:
        bits = []
        if missing:
            bits.append('範本有、清單沒歸類：%s（這些檔沒人同步，而且不會有徵兆）'
                        % sorted(missing))
        if extra:
            bits.append('清單有、範本沒有：%s' % sorted(extra))
        record('FAIL', '同步清單涵蓋骨架', '；'.join(bits))
        return False
    record('OK', '同步清單涵蓋骨架',
           '%d 個範本全部歸類（整份覆蓋 %d／手術 1／接線 %d＋AG 1／補欄位 %d／專案實例 %d）'
           % (len(EXPECTED), len(sp.WHOLE), len(sp.WIRING), len(sp.PARTIAL),
              len(sp.INSTANCE)))

    # 接線合併：拿真的範本當權威，餵一份「舊 matcher ＋ 專案自己加的東西」進去。
    auth = (dest / '.claude' / 'settings.json').read_text(encoding='utf-8')
    stale = json.loads(auth)
    stale['hooks']['PreToolUse'][0]['matcher'] = 'Bash'          # 2026-09-13 之前的舊值
    stale['permissions'] = {'allow': ['Bash(git status)']}       # 專案自己加的
    stale['hooks']['SessionStart'].append(                       # 專案自己加的 hook
        {'hooks': [{'type': 'command', 'command': 'bash .claude/hooks/project-own.sh'}]})
    new, _, err = sp.merge_wiring(auth, json.dumps(stale, ensure_ascii=False, indent=2))
    if err or new is None:
        record('FAIL', '接線合併', err or '舊 matcher 沒被認出來——落後的專案不會被修好')
        return False
    got = json.loads(new)
    start = [h for g in got['hooks']['SessionStart'] for h in g.get('hooks', [])]
    checks = {
        '換掉舊 matcher': got['hooks']['PreToolUse'][0].get('matcher') == 'Bash|PowerShell',
        '保留專案 permissions': got.get('permissions') == stale['permissions'],
        '保留專案自己的 hook': any('project-own.sh' in h.get('command', '') for h in start),
        '骨架 hook 不重複': sum('git-freshness.sh' in h.get('command', '')
                             for h in start) == 1,
    }
    bad = [k for k, v in checks.items() if not v]
    if bad:
        record('FAIL', '接線合併', '沒做到：%s' % '、'.join(bad))
        return False
    # 已經一致就不該回報要改，否則每次同步都製造假變更，雜訊會讓人不再看輸出。
    same, _, err2 = sp.merge_wiring(auth, auth)
    if err2 or same is not None:
        record('FAIL', '接線合併', '內容已一致卻說要改（%s）' % (err2 or '會製造假變更'))
        return False
    record('OK', '接線合併', '舊 matcher 換新、專案 permissions 與自有 hook 保留、已一致不動')
    return True


def step_eol(dest):
    tracked = [
        ROOT / p for p in
        run(['git', 'ls-files'], cwd=ROOT).stdout.split('\n') if p
    ]
    generated = [f for f in dest.rglob('*') if f.is_file() and '.git' not in f.parts]
    bad = [f for f in tracked + generated if f.is_file() and crlf_count(f)]
    if bad:
        record('FAIL', '行末全 LF', f'{len(bad)} 檔含 CRLF：{[str(b) for b in bad[:5]]}')
        return False
    record('OK', '行末全 LF', f'本 repo {len(tracked)} 檔＋骨架 {len(generated)} 檔')
    return True


FRESHNESS_DAYS = 90
FRESHNESS_PAGES = ('code.claude.com/docs/en/hooks', 'code.claude.com/docs/en/memory',
                   'developers.openai.com/codex/hooks', 'developers.openai.com/codex/skills',
                   'antigravity.google/docs/hooks', 'antigravity.google/docs/rules')


def step_table_freshness():
    """「跨工具與跨平台」那張表的查證日期不得超過 FRESHNESS_DAYS 天。

    為什麼要用工具擋：同一種錯踩過兩次——Antigravity 的 hooks（2026-08-05 的事實，
    2026-10-30 才發現過時）、Codex 桌面 App 的 hooks（2026-08-06 的實測，同樣到
    2026-10-30 才發現）。第一次之後的對策是在那一節寫一句警告，而**警告沒有擋住
    第二次**：表上一直都有查證日期，但沒有人會因為日期舊就主動重查。

    天花板要講明白：這一項只能保證有人看過日期，不能保證有人真的重查。它買到的是
    「必須有意識地決定」，不是正確性。不怕退化成「bump 一個欄位就能過」（那是
    pre-push-handoff.sh 被否決的理由之一）的原因是頻率——90 天一次，一年四次，
    反射形不成；pre-push 是每次推進度都誤報。
    """
    if os.environ.get('BOOTSTRAP_FRESHNESS') == 'off':
        record('SKIP', '跨工具表保鮮期', 'BOOTSTRAP_FRESHNESS=off')
        return True
    m = re.search(r'查證日期：(\d{4})-(\d{2})-(\d{2})', KIT.read_text(encoding='utf-8'))
    if not m:
        record('FAIL', '跨工具表保鮮期',
               '「跨工具與跨平台」那節找不到「查證日期：YYYY-MM-DD」——這一項是靠它判斷的')
        return False
    checked = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    age = (datetime.date.today() - checked).days
    if age > FRESHNESS_DAYS:
        record('FAIL', '跨工具表保鮮期',
               '查證日期 %s 已經 %d 天（上限 %d）。先真的重讀這幾頁再改日期：%s。'
               '只是要跑別的驗證就 BOOTSTRAP_FRESHNESS=off'
               % (checked, age, FRESHNESS_DAYS, '、'.join(FRESHNESS_PAGES)))
        return False
    record('OK', '跨工具表保鮮期', '查證日期 %s，%d 天內（上限 %d）' % (checked, age, FRESHNESS_DAYS))
    return True


def step_misc(dest, work=None):
    ok = True
    for label, rel in (('settings.json', '.claude/settings.json'),
                       ('.codex/hooks.json', '.codex/hooks.json')):
        try:
            json.loads((dest / rel).read_text(encoding='utf-8'))
            record('OK', f'{label} 合法 JSON')
        except Exception as e:
            record('FAIL', f'{label} 合法 JSON', str(e))
            ok = False

    # VERSION 檔是落後偵測的依據：各專案抓它跟自己的 source 標記比。它跟部署包開頭
    # 「版本：**…**」那一行必須一致——不一致的話偵測就會說謊，而那種謊沒有任何徵兆：
    # 落後的專案會以為自己是最新的，正好是這個機制要解決的問題本身。
    kit_ver = re.search(r'^> 版本：\*\*([^*]+)\*\*', KIT.read_text(encoding='utf-8'), re.M)
    vfile = ROOT / 'VERSION'
    if not vfile.exists():
        record('FAIL', 'VERSION 檔', '不存在——落後偵測沒有依據')
        ok = False
    elif not kit_ver:
        record('FAIL', 'VERSION 檔', '部署包找不到「> 版本：**…**」那一行')
        ok = False
    elif vfile.read_text(encoding='utf-8').strip() != kit_ver.group(1).strip():
        record('FAIL', 'VERSION 檔', 'VERSION=%s 但部署包版本行=%s'
               % (vfile.read_text(encoding='utf-8').strip(), kit_ver.group(1).strip()))
        ok = False
    else:
        record('OK', 'VERSION 檔', '與部署包版本行一致（%s）' % kit_ver.group(1).strip())

    step_table_freshness()

    r = run([sys.executable, '-X', 'utf8', 'tools/verify_state.py'], cwd=dest)
    if r.returncode == 0 and 'NOT_CONFIGURED' in r.stdout:
        record('OK', 'verify_state.py', '未填檢查項時印 NOT_CONFIGURED')
    else:
        record('FAIL', 'verify_state.py', f'exit {r.returncode}：{r.stdout.strip()[:120]}')
        ok = False

    bash = find_bash()
    if not bash:
        record('SKIP', 'git-freshness.sh', '找不到看得懂 Windows 路徑的 bash')
    elif work is None:
        # 只有 git init／add、還沒有任何 commit 的骨架，這支 hook 判斷不了就靜默放行（設計如此），
        # 拿它來測等於什麼都沒測。所以只在 hook fixture（有 origin、有 commit）上驗。
        record('SKIP', 'git-freshness.sh', 'hook fixture 沒建起來，缺少有 origin 與 commit 的 repo 可測')
    else:
        r = run([bash, '.claude/hooks/git-freshness.sh'], cwd=work)
        if r.returncode == 0 and '[git-check]' in r.stdout and '[handoff]' in r.stdout:
            record('OK', 'git-freshness.sh', 'exit 0，印出 [git-check] 比對結果與 [handoff] 提醒行')
        else:
            record('FAIL', 'git-freshness.sh',
                   f'exit {r.returncode}：{(r.stdout + r.stderr).strip()[:160]}')
            ok = False
    return ok


# 解壓即用的說明檔。刻意只存在於壓縮檔裡、不進部署包第 3 節——它講的是「怎麼用這個 zip」，
# 屬於發佈方式，不是專案要長期保留的制度。部署完成就跟部署包一起刪掉。
ZIP_README = """# 先看這個——三步驟

本資料夾是「AI 協作專案管理骨架」解壓後的樣子。檔案都已就位，但裡面還有 `{{佔位符}}` 沒填。

## 1. 確認位置

這些檔案應該直接躺在**你的專案資料夾根目錄**（跟你的程式碼同一層）。
如果解壓後多包了一層資料夾，把裡面的東西搬上來。

## 2. 開一個 AI session，貼這段

```text
本資料夾已經解壓好一套 AI 協作管理骨架，檔案都在，但裡面還有 {{佔位符}} 沒填。
請照 PROJECT-BOOTSTRAP.md 第 1 節的表格問我問題（一次問完），拿到答案後：
1. 把所有檔案裡的 {{佔位符}} 換成我的答案，其他內容一個字都不要改、不要自行增刪制度。
2. 依第 4 節把專案推上 GitHub（已經是 git repo 就只確認 upstream 有設好）。
3. 跑第 5 節自檢清單，逐項回報通過／不適用／有問題。
4. 最後刪掉 PROJECT-BOOTSTRAP.md 與本說明檔。
```

**如果這是一個已經在進行中的專案**（已有 README.md／AGENTS.md），再加一句：
「已存在的檔案不要覆蓋，只補上缺的段落，動手前先把你打算加什麼列給我看。」

## 3. macOS／Linux 要多做一步

給兩個 hook 腳本執行權限（Windows 不需要）：

```bash
chmod +x .claude/hooks/*.sh
```

## 各工具的差異

- **Claude Code**：全自動。開場檢查 git、可打 `/handoff`、忘了寫交接會擋下上傳。
- **Codex CLI**：同上，但第一次要打 `/hooks` 信任 `.codex/hooks.json`。
- **Codex 桌面 App**：沒有 hook 機制（2026-08-06 在 App `26.721.41059` 實測），所以沒有自動
  提醒。把 `.claude/skills/handoff/SKILL.md` 複製到 `~/.codex/skills/handoff/SKILL.md` 就能
  用 skill；開工時自己講一句「請先讀 .claude/skills/handoff/SKILL.md，照 A 模式接棒」。
- **Antigravity**：沒有 hook 機制，所以沒有自動提醒。它會讀 `AGENTS.md` 與 `.agents/skills/`；
  開工時自己講一句「請先讀 .claude/skills/handoff/SKILL.md，照 A 模式接棒」即可。

`python` 指令不存在的機器（macOS 常見）一律改用 `python3`。
"""


def build_zip(out_path):
    """把「剛剛通過驗證的那份骨架」打包成解壓即用的 zip。

    刻意從部署包重新抽一次未填的範本，不用驗證流程裡那份——那一份的佔位符已經
    被測試用假值填掉了，打包出去會讓人拿到「驗證用假專案」當專案名。
    """
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='pack-'))
    try:
        src = tmp / 'gen'
        src.mkdir()
        extract(src)
        (src / '讀我-先看這個.md').write_text(ZIP_README, encoding='utf-8', newline='')
        shutil.copyfile(KIT, src / KIT.name)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for f in sorted(src.rglob('*')):
                if not f.is_file():
                    continue
                arc = f.relative_to(src).as_posix()
                # 固定時間戳，同一份部署包每次打包都得到相同的 zip（可比對）
                info = zipfile.ZipInfo(arc, date_time=(2026, 1, 1, 0, 0, 0))
                # 讓 macOS／Linux 解壓後 .sh 直接可執行，省掉一步 chmod
                info.external_attr = (0o755 if arc.endswith('.sh') else 0o644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, f.read_bytes())
        n = len(zipfile.ZipFile(out_path).namelist())
        print(f'\n已打包 {n} 檔 → {out_path}')
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep', action='store_true', help='保留產生的骨架，印出路徑')
    ap.add_argument('--zip', nargs='?', const='', metavar='PATH',
                    help='驗證全過時，額外輸出解壓即用的 zip（預設 dist/project-skeleton-<日期>.zip）')
    args = ap.parse_args()

    if not KIT.exists():
        print(f'找不到 {KIT}——請在本 repo 根目錄執行')
        return 2

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='verify-bootstrap-'))
    dest = tmp / 'gen'
    dest.mkdir()
    print(f'重生骨架於 {dest}\n')
    work = None
    try:
        seen = step_regenerate(dest) and step_fill(dest)
        if seen and step_check_docs(dest):
            step_placeholder_list(dest, seen)
            step_placeholder_guard(dest)
            step_date_guard(dest)
            step_busy_tool_guard(dest)
            step_deploy_shape(dest)
            step_antigravity(dest)
            step_portability(dest)
            hooked = step_hook(dest, tmp)
            work = hooked if isinstance(hooked, pathlib.Path) else None
            step_busy(dest, work)
            step_repo_busy(work)
            step_version_check(work)
        step_eol(dest)
        step_self()
        step_sync_coverage(dest)
        step_misc(dest, work)
    finally:
        if args.keep:
            print(f'\n（--keep）骨架保留在 {dest}')
        else:
            shutil.rmtree(tmp, ignore_errors=True)

    failed = [t for s, t, _ in results if s == 'FAIL']
    skipped = [t for s, t, _ in results if s == 'SKIP']
    print()
    if failed:
        print(f'FAIL：{len(failed)} 項未通過 —— {"、".join(failed)}')
        if args.zip is not None:
            print('（有項目未通過，不產出 zip——沒驗過的東西不該發出去）')
        return 2
    if args.zip is not None:
        out = pathlib.Path(args.zip) if args.zip else \
            ROOT / 'dist' / f'project-skeleton-{date.today().isoformat()}.zip'
        build_zip(out)
    if skipped:
        print(f'PASS（有 {len(skipped)} 項跳過：{"、".join(skipped)}）——跳過的項目沒有被驗證，回報時要寫明')
        return 1
    print('OK：部署包驗證全數通過')
    return 0


if __name__ == '__main__':
    sys.exit(main())
