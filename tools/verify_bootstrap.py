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
  README 跨工具表——README 那張表是部署包那一張的轉述，而保鮮期只守部署包那一份。同名列的
                  判定符號、README 的版本號、指回部署包的指標三者要對得上，否則人的入口會
                  無聲分岔（2026-11-01 加入，加的當下就抓到一處）
  ZIP 說明指標 ——工具差異只指向同包部署包的權威段落與驗收清單，不再維護另一份能力摘要。
                  原本的 ZIP_README 留著兩句「沒有 hook」，矩陣改對後它仍會被打包出去
                  （2026-11-01 加入，附六個負向測試）
  跨工具過期敘述——守住已修掉的「2.0 未測」「骨架還沒附接線」等已知舊斷言，涵蓋部署包正文、
                  重生的結構／協定範本與本 repo 結構說明。表頭的歷史變更記錄不算現況；
                  這不是通用語意檢查，不會重查外部工具（2026-11-01 加入，附負向與範圍測試）
  改名寫進回報——A5 與 B9 的回報模板各要有一行 `session：`，而且都要留著「不適用」這個選項。
                  改 session 名稱發生在 repo 外面，check_docs、git-freshness、pre-push 三層
                  都看不到它，所以漏掉完全無聲；那一行是它唯一的守門人，被誰順手刪掉也同樣
                  無聲（2026-11-01 加入，起因是六個收尾 session 裡兩個漏了改名）
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
    '.claude/hooks/codex-hook.cmd',
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

    # 開工改名提示（2026-11-01）。放進這張共用表，是因為它正是「期望值有兩份就會分岔」的
    # 下一個候選；而它消失的時候完全沒有徵兆——agent 只會回頭自己去 date 一次，或者更糟，
    # 拿系統提示裡的日期猜一個小時，寫出一個不存在的時刻。所以連格式一起釘：全形空格、
    # 八位數字、全形豎線，少一樣側欄上就排不整齊，而排不整齊就等於沒改名。
    cases.append(('印開工改名提示', '開工改名用' in out
                  and re.search('㊣　[0-9]{8}｜', out) is not None))
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


# A5／B9 回報模板裡那行 `session：`。改 session 名稱是整套程序裡唯一不留 repo 痕跡的動作，
# 所以它沒有辦法被真正地「驗」——能釘的只有「回報模板有沒有逼人講」。這一項守的就是那一行
# 別被後人順手刪掉：刪掉之後規則還在文件裡，但漏掉就再也看不出來，跟沒有這條規則一樣。
RENAME_LINE = 'session：'


def rename_block(text, heading):
    """取某個步驟標題底下第一個 ```text 區塊的內容；找不到回 None。"""
    i = text.find(heading)
    if i < 0:
        return None
    j = text.find('```text', i)
    if j < 0:
        return None
    k = text.find('```', j + len('```text'))
    if k < 0:
        return None
    return text[j + len('```text'):k]


def rename_line_problems(skill):
    """回傳問題清單；空清單＝兩個模板都把改名寫進去了。"""
    problems = []
    for heading in ('### A5 ', '### B9 '):
        block = rename_block(skill, heading)
        if block is None:
            problems.append('%s 底下找不到 ```text 回報模板' % heading.strip())
            continue
        hit = [l.strip() for l in block.splitlines() if l.strip().startswith(RENAME_LINE)]
        if not hit:
            problems.append('%s 的回報模板沒有「%s」那一行' % (heading.strip(), RENAME_LINE))
        elif '不適用' not in hit[0]:
            # 少了這個選項，沒有改名能力的工具（Codex CLI／Gemini CLI）就只剩「整行省掉」
            # 一條路可走，必填會退化成「有能力的工具才填」——正好放掉要守的那一半。
            problems.append('%s 的「%s」那一行沒有留「不適用」這個選項'
                            % (heading.strip(), RENAME_LINE))
    return problems


def step_rename_line(dest):
    """改名有沒有被寫進回報模板（2026-11-01）。

    2026-11-01 量到：六個收尾 session（全 Sonnet）裡只有四個改了 session 名稱，六個的 git
    結果全部正確。**為什麼漏沒有量過**，所以加硬的方向不是猜原因，而是讓「有沒有做」露出來。
    """
    skill = (dest / '.claude/skills/handoff/SKILL.md').read_text(encoding='utf-8')
    problems = rename_line_problems(skill)
    if problems:
        record('FAIL', '改名寫進回報模板', '；'.join(problems))
        return False

    # 負向測試：一個永遠回 ok 的檢查跟沒有這一項在畫面上一模一樣。
    a5 = 'session：㊣　<YYMMDDHH｜主題>｜工作中（已改）／不適用：<本工具不能改名>'
    b9 = 'session：↗　<YYMMDDHH｜主題>｜已交棒（已改）／不適用：<本工具不能改名>'
    cases = (
        ('A5 那一行被刪掉', skill.replace(a5 + '\n', '')),
        ('B9 那一行被刪掉', skill.replace(b9 + '\n', '')),
        ('「不適用」選項被拿掉', skill.replace('（已改）／不適用：<本工具不能改名>', '（已改）')),
    )
    bad = []
    for name, mutated in cases:
        if mutated == skill:
            # 改壞的字串沒對上就等於沒測到，而它會安靜地「通過」。
            bad.append('%s：負向測試沒改到任何字，字串對不上了' % name)
        elif not rename_line_problems(mutated):
            bad.append('%s：沒被擋下' % name)
    if bad:
        record('FAIL', '改名寫進回報模板', '；'.join(bad))
        return False
    record('OK', '改名寫進回報模板',
           'A5／B9 模板各有一行 session：且留著「不適用」；三個負向測試都擋得住')
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

    # 兩份接線一起查（2026-11-01 加上 `.codex/hooks.json`）。這個 repo 的接線指的是它
    # 自己那支 `repo-git-check.sh`，所以它們跟部署包 3.9／3.17 只是長得像、不是副本；
    # 也因此沒有 `source:` 標記、落後偵測看不到它們，唯一的守門人就是這一項。
    # 連「有沒有被 sync_project.py 覆蓋過」一起釘：那會把它們改成指向這裡不存在的
    # `git-freshness.sh`，開場檢查於是靜默失效——看起來有防護、實際上沒有。
    hook_rel = '.claude/hooks/repo-git-check.sh'
    problems, present = [], []
    for rel in ('.claude/settings.json', '.codex/hooks.json'):
        cfg = ROOT / rel
        if not cfg.exists():
            problems.append('%s 不存在' % rel)
            continue
        raw = cfg.read_text(encoding='utf-8')
        try:
            data = json.loads(raw)
        except Exception as e:
            problems.append('%s 不是合法 JSON：%s' % (rel, e))
            continue
        present.append(rel)
        if hook_rel not in raw:
            problems.append('%s 沒指向 %s' % (rel, hook_rel))
        for bad in ('git-freshness.sh', 'pre-push-handoff.sh'):
            if bad in raw:
                problems.append('%s 指向 %s，而這個 repo 沒有那個檔'
                                '（被 sync_project.py 覆蓋過？）' % (rel, bad))
        for event in data.get('hooks', {}):
            if event != 'SessionStart':
                problems.append('%s 接了 %s，但這個 repo 只有 SessionStart 那一支'
                                % (rel, event))
    if not (ROOT / hook_rel).exists():
        problems.append('%s 不存在——兩份接線都指著一個不在的腳本' % hook_rel)

    if problems:
        record('FAIL', '本 repo 兩份接線', '；'.join(problems))
        ok = False
    elif not present:
        record('SKIP', '本 repo 兩份接線', '都不存在——開場沒有 git 檢查，接棒全靠人記得')
    else:
        record('OK', '本 repo 兩份接線',
               '%s 都是合法 JSON、只接 SessionStart、都指向 repo-git-check.sh'
               % '＋'.join(present))
    return ok


def step_sync_self_guard():
    """`sync_project.py <本 repo 路徑>` 必須拒絕（2026-11-01）。

    這個 repo 的 `.claude/settings.json` 與 `.codex/hooks.json` 跟 `WIRING` 清單同名，指的
    卻是它自己那支 `repo-git-check.sh`。沒有這道擋，一次 `sync_project.py .` 就把兩份接線
    改成指向這裡不存在的 `git-freshness.sh` 與 `pre-push-handoff.sh`——開場檢查從此靜默
    失效，而「看起來有防護、實際上沒有」是這套制度最貴的那一種壞法。`--all` 那條路本來就
    安全（`discover()` 靠 handoff skill 發現專案，這裡刻意沒有），會踩到的是手打路徑，而那
    在加擋之前實測真的印出兩個 `UPDATE`。

    釘兩件事而不是一件：拒絕的話有印出來，而且**預演輸出裡一個 `UPDATE` 都沒有**。只檢查
    前者的話，一個「印了話卻照樣改檔」的版本會通過，而那比沒有這項檢查更糟。
    """
    out = run([sys.executable, '-X', 'utf8', 'tools/sync_project.py', str(ROOT)],
              cwd=ROOT).stdout
    refused, untouched = '不是同步目標' in out, 'UPDATE' not in out
    if not (refused and untouched):
        record('FAIL', 'sync 拒絕本 repo',
               '%s%s' % ('' if refused else '沒印出拒絕；',
                         '' if untouched else '預演仍要改檔（UPDATE）')
               + chr(10) + '           輸出：' + out.strip()[:200])
        return False
    record('OK', 'sync 拒絕本 repo', '手打本 repo 路徑→拒絕，預演零 UPDATE')
    return True


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


def codex_wiring_problems(cfg, scripts):
    problems = []
    for event, script in scripts.items():
        hooks = [h for g in cfg.get('hooks', {}).get(event, []) for h in g.get('hooks', [])
                 if script in h.get('command', '')]
        if len(hooks) != 1:
            problems.append('%s 的 %s 接線不是一份' % (event, script))
            continue
        h = hooks[0]
        if h.get('command') != 'bash .claude/hooks/' + script:
            problems.append('%s 的 Unix 接線改變了' % event)
        if h.get('commandWindows') != 'cmd /d /c .claude\\hooks\\codex-hook.cmd ' + script:
            problems.append('%s 沒經 Windows 啟動器執行同一支腳本' % event)
    return problems


def step_codex_windows(dest, tmp):
    """真部署發生過：已信任卻選到 WSL，exit 1；驗接線與實際 batch 的 stdin／結束碼。"""
    cfg = json.loads((dest / '.codex/hooks.json').read_text(encoding='utf-8'))
    scripts = {'SessionStart': 'git-freshness.sh', 'PreToolUse': 'pre-push-handoff.sh'}
    bad = codex_wiring_problems(cfg, scripts)
    for event in scripts:
        stale = json.loads(json.dumps(cfg))
        del stale['hooks'][event][0]['hooks'][0]['commandWindows']
        if not codex_wiring_problems(stale, scripts):
            bad.append('%s 拿掉 commandWindows 的負向測試沒擋住' % event)
    stale = json.loads(json.dumps(cfg))
    stale['hooks']['PreToolUse'][0]['hooks'][0]['commandWindows'] = 'bash .claude/hooks/pre-push-handoff.sh'
    if not codex_wiring_problems(stale, scripts):
        bad.append('Windows 改回 PATH bash 的負向測試沒擋住')
    own = json.loads((ROOT / '.codex/hooks.json').read_text(encoding='utf-8'))
    bad += codex_wiring_problems(own, {'SessionStart': 'repo-git-check.sh'})
    launcher = dest / '.claude/hooks/codex-hook.cmd'
    raw = launcher.read_bytes()
    body = raw.decode('ascii') if raw.isascii() else ''
    if not body or '\r' in body or re.search(r'^\s*(?::|\()|\(\s*$', body, re.M):
        bad.append('啟動器必須 ASCII、LF、無 label 與多行括號區塊')
    if (ROOT / '.claude/hooks/codex-hook.cmd').read_bytes() != raw:
        bad.append('本 repo 的 Windows 啟動器與權威範本不同')
    if bad:
        record('FAIL', 'Codex Windows 接線', '；'.join(bad))
        return False
    record('OK', 'Codex Windows 接線',
           '兩個事件與本 repo 均用 commandWindows；Unix 命令保留；三個負向測試通過，啟動器 ASCII／LF 且副本一致')

    import sync_project as sp
    project = tmp / 'codex-upgrade'
    (project / '.codex').mkdir(parents=True)
    old = json.loads(json.dumps(cfg))
    for groups in old['hooks'].values():
        for group in groups:
            for h in group['hooks']:
                h.pop('commandWindows', None)
    old['hooks']['SessionStart'].append({'hooks': [{'type': 'command', 'command': 'project-own'}]})
    wiring = project / '.codex/hooks.json'
    wiring.write_text(json.dumps(old), encoding='utf-8')
    skill = project / '.claude/skills/handoff/SKILL.md'
    skill.parent.mkdir(parents=True)
    skill.write_text('project skill must stay untouched', encoding='utf-8')
    preview, _ = sp.sync(project, dest, False, codex_only=True)
    if preview != 2 or (project / sp.CODEX_LAUNCHER).exists():
        bad.append('Codex 限定預演沒有列出兩項，或竟然寫檔')
    changed, _ = sp.sync(project, dest, True, codex_only=True)
    got = json.loads(wiring.read_text(encoding='utf-8'))
    if changed != 2 or codex_wiring_problems(got, scripts):
        bad.append('舊專案沒同時升級接線與新增啟動器')
    if skill.read_text(encoding='utf-8') != 'project skill must stay untouched':
        bad.append('Codex 限定同步竟改了 SKILL.md')
    if not any(h.get('command') == 'project-own' for g in got['hooks']['SessionStart'] for h in g['hooks']):
        bad.append('Codex 同步洗掉專案自己的 hook')
    if sp.sync(project, dest, True, codex_only=True)[0] != 0:
        bad.append('Codex 限定同步重跑仍改檔')
    absent = tmp / 'codex-absent'
    absent.mkdir()
    if sp.sync(absent, dest, True, codex_only=True)[0] or list(absent.iterdir()):
        bad.append('沒有 Codex 接線的專案被自動補裝')
    if bad:
        record('FAIL', 'Codex 接線升級', '；'.join(bad))
        return False
    record('OK', 'Codex 接線升級',
           '預演零寫入、舊接線補齊啟動器、自有 hook 與 SKILL 保留、重跑零變更、沒裝 Codex 的專案不補裝')

    if os.name != 'nt':
        return True  # batch 執行只適用 Windows；其他平台仍跑上面的接線與升級測試。
    fixture = tmp / 'Codex 空白路徑' / '.claude/hooks'
    fixture.mkdir(parents=True)
    shim = fixture / 'codex-hook.cmd'
    shim.write_bytes(raw)
    (fixture / 'probe.sh').write_text(
        '#!/usr/bin/env bash\nIFS= read -r payload\nprintf "[git-check] %s\\n" "$payload"\n'
        'printf "err:%s\\n" "$payload" >&2\nexit 2\n', encoding='utf-8', newline='')
    command = '"%s" /d /s /c ""%s" probe.sh"' % (os.environ['COMSPEC'], shim)
    r = run(command, cwd=tmp, stdin='stdin-survives\n')
    if (r.returncode != 2 or r.stdout.strip() != 'Git status check:\n[git-check] stdin-survives'
            or r.stderr.strip() != 'err:stdin-survives'):
        record('FAIL', 'Codex Windows 啟動器',
               '空白／中文路徑、不同 cwd、stdin 或 exit 2 沒保留：%r' % ((r.returncode, r.stdout, r.stderr),))
        return False
    # 原始回歸：只有方括號標記時，CLI 0.166.0 把它當 JSON。證明標頭真的不能被刪掉。
    stale = raw.replace(b'echo Git status check:\n', b'')
    if stale == raw:
        record('FAIL', 'Codex Windows 啟動器', '移除純文字標頭的負向測試沒有改到內容')
        return False
    try:
        shim.write_bytes(stale)
        negative = run(command, cwd=tmp, stdin='stdin-survives\n')
        if negative.stdout.startswith('Git status check:\n') or not negative.stdout.startswith('[git-check]'):
            record('FAIL', 'Codex Windows 啟動器', '移除標頭後沒有重現方括號開頭的舊輸出')
            return False
    finally:
        shim.write_bytes(raw)
    # Windows 啟動 cmd 時會重建 ProgramFiles；須在同一個 cmd 裡設定，負向情境才真的沒 Git。
    missing = fixture / 'missing-git.cmd'
    missing.write_text('@echo off\nset "ProgramFiles=%~dp0missing"\n'
                       'set "ProgramFiles(x86)=%~dp0missing"\n'
                       'set "LOCALAPPDATA=%~dp0missing"\n'
                       'call "%~dp0codex-hook.cmd" probe.sh\nexit /b %ERRORLEVEL%\n',
                       encoding='ascii', newline='')
    missing_command = '"%s" /d /s /c ""%s""' % (os.environ['COMSPEC'], missing)
    env = dict(os.environ, PATH=os.environ['SystemRoot'] + '\\System32')
    r = run(missing_command, cwd=tmp, env=env, stdin='no-git\n')
    if r.returncode != 1 or 'Git Bash not found' not in r.stderr:
        record('FAIL', 'Codex Windows 啟動器', '找不到 Git Bash 時沒明確失敗：%r' % ((r.returncode, r.stderr),))
        return False
    record('OK', 'Codex Windows 啟動器',
           '原生 cmd 實跑：中文／空白路徑、不同 cwd、純文字標頭、stdin／輸出內容／stderr／exit 2 保留；缺 Git Bash 明確 exit 1')
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
# 權威清單在部署包「這張表的保鮮期」那一段，這裡只是它的副本（用途只有放進 fail 訊息）。
# Codex 那兩頁 2026-10-31 搬家：舊網址回 308，skills 那頁連路徑名都換了，所以兩邊要一起改——
# 指著轉址等於每次重查都先撞一次牆。
FRESHNESS_PAGES = ('code.claude.com/docs/en/hooks', 'code.claude.com/docs/en/memory',
                   'learn.chatgpt.com/docs/hooks', 'learn.chatgpt.com/docs/build-skills',
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


TOOL_VERDICTS = '✅❌⬜🟡'
VER_TOKEN = r'`v?(\d+\.\d+(?:\.\d+)*)`'


def tool_section(text):
    """「## 跨工具與跨平台」那一節（到下一個 `## ` 為止）。"""
    i = text.find('## 跨工具與跨平台')
    if i < 0:
        return ''
    j = text.find('\n## ', i + 3)
    return text[i:j if j > 0 else len(text)]


def tool_matrix(section):
    """那一節裡的能力矩陣：表頭是空的第一欄＋四個工具名。

    回傳 (欄名, {列名: [判定符號]})。**只讀第一張這種形狀的表**：那一節裡還有別的表
    （Antigravity 四個 surface、hook 契約、實測版本），拿列名當 key 全掃會把它們也收
    進來，然後在兩邊都沒有的列名上比出一堆假問題。
    """
    lines = section.splitlines()
    for n, line in enumerate(lines):
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if cells[0] or len(cells) != 5:
            continue
        rows = {}
        for body in lines[n + 2:]:
            if not body.startswith('|'):
                break
            row = [c.strip() for c in body.strip('|').split('|')]
            if len(row) != 5:
                break
            rows[row[0]] = [c[:1] if c[:1] in TOOL_VERDICTS else '?' for c in row[1:]]
        return tuple(cells[1:]), rows
    return (), {}


def compare_tool_tables(readme, kit):
    """README 那張跨工具表不得跟部署包那一張分岔。回傳問題清單（空＝一致）。"""
    problems = []
    rsec, ksec = tool_section(readme), tool_section(kit)
    if not rsec or not ksec:
        problems.append('找不到「## 跨工具與跨平台」那一節（%s）'
                        % ('README' if not rsec else '部署包'))
        return problems
    rcols, rrows = tool_matrix(rsec)
    kcols, krows = tool_matrix(ksec)
    if not rrows or not krows:
        problems.append('抓不到能力矩陣，表頭要是空的第一欄＋四個工具名（%s）'
                        % ('README' if not rrows else '部署包'))
        return problems
    if rcols != kcols:
        problems.append('欄位不一樣：README %s ／ 部署包 %s' % (list(rcols), list(kcols)))
        return problems
    shared = [lab for lab in rrows if lab in krows]
    if not shared:
        problems.append('兩張表沒有同名的列，無從比對——列名改過就要兩邊一起改')
    for lab in shared:
        for col, rv, kv in zip(rcols, rrows[lab], krows[lab]):
            if rv != kv:
                problems.append('「%s」×「%s」：README %s ／ 部署包 %s' % (lab, col, rv, kv))
    orphan = sorted(set(re.findall(VER_TOKEN, rsec)) - set(re.findall(VER_TOKEN, ksec)))
    if orphan:
        problems.append('README 寫了部署包那節已經沒有的版本號：%s' % '、'.join(orphan))
    if '部署包' not in rsec:
        problems.append('README 那節沒有指回部署包——它是轉述，必須留指標')
    return problems


def step_readme_table():
    """README 的跨工具表是部署包那一張的**轉述**，而保鮮期檢查只讀部署包那一份。於是它可以
    無聲分岔：事實在部署包被重查、改對，README 留在舊事實上——而 README 正好是**人的入口**，
    第一個讀到它的人拿到的就是過期的那一份。

    2026-11-01 加。**加的當下就抓到一處已經發生的分岔**：「自動載入程序檔」×「Codex CLI」
    部署包 2026-10-30 實測後改成 ✅（`~/.codex/skills/` ＋ repo 的 `.agents/skills/`），
    README 還停在 ⬜「靠 `AGENTS.md` 指路」。沒有任何徵兆，也沒人發現。

    為什麼不是給 README 也加一個「查證日期」：那會讓同一個事實有**第二個時鐘**，而兩個時鐘
    一定會分岔（部署包那一節已經踩過——Antigravity 那段的 `實測日期：` 刻意避開 `查證日期：`
    這個字串，就是因為保鮮期只讀全檔第一個）。綁住一致性之後，**單一時鐘就同時罩得住兩張表**。

    天花板：只守矩陣的**判定符號**、README 的版本號與指回部署包的指標，守不了 cell 裡與表
    下面那幾段**散文**。README 的列比部署包少是刻意的（它是入口摘要，不是副本），所以只比對
    同名的列——代價是部署包新增一整列（新的能力類別）不會逼 README 跟上。
    """
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    problems = compare_tool_tables(readme, KIT.read_text(encoding='utf-8'))
    if problems:
        record('FAIL', 'README 跨工具表一致性', '；'.join(problems))
        return False

    # 負向測試：比對器自己要擋得住四種分岔。一個永遠回「一致」的比對器，跟沒有這項檢查
    # 在畫面上一模一樣——這整支腳本的存在理由就是不接受那種東西。
    base = ('## 跨工具與跨平台\n\n細節見部署包。\n\n'
            '| | Claude Code | Codex CLI | Codex 桌面 App | Antigravity |\n'
            '|---|---|---|---|---|\n'
            '| Hooks | ✅ a | ✅ b `1.2.3` | ✅ c | ✅ d |\n')
    cases = (
        ('判定符號翻掉', base.replace('| Hooks | ✅ a | ✅ b', '| Hooks | ✅ a | ⬜ b')),
        ('版本號成孤兒', base.replace('`1.2.3`', '`9.9.9`')),
        ('欄位長出一個', base.replace('| Antigravity |\n', '| Antigravity | 新工具 |\n')),
        ('指標被抽掉', base.replace('細節見部署包。', '細節見別處。')),
    )
    missed = [name for name, mutated in cases if not compare_tool_tables(mutated, base)]
    if missed or compare_tool_tables(base, base):
        record('FAIL', 'README 跨工具表一致性',
               '負向測試沒排到：%s' % ('、'.join(missed) or '兩份相同卻被判成分岔'))
        return False

    _, rrows = tool_matrix(tool_section(readme))
    record('OK', 'README 跨工具表一致性',
           '%d 個同名列的判定符號與部署包一致、沒有孤兒版本號、指標在；'
           '負向測試四種分岔都擋得住' % len(rrows))
    return True


def zip_readme_problems(text):
    """ZIP 的第一份說明只指路，工具能力留在部署包的一個家（2026-11-01）。"""
    heading = '## 各工具的差異'
    if heading not in text:
        return ['缺少「各工具的差異」入口']
    section = text.split(heading, 1)[1].split('\n## ', 1)[0]
    problems = []
    if not re.search(r'\[[^\]\n]+\]\(PROJECT-BOOTSTRAP\.md\)', section):
        problems.append('缺少同包 PROJECT-BOOTSTRAP.md 的相對連結')
    if '跨工具與跨平台' not in section:
        problems.append('未指向部署包的跨工具權威段落')
    if not re.search(r'第\s*5\s*節', section):
        problems.append('未指向第 5 節驗收清單')
    if re.search(r'^- \*\*(?:Claude Code|Codex CLI|Codex 桌面 App|Antigravity)\*\*',
                 section, re.M):
        problems.append('又長出逐工具摘要——能力說明只在部署包維護')
    return problems


def step_zip_readme():
    problems = zip_readme_problems(ZIP_README)
    cases = (
        ('入口刪掉', ZIP_README.replace('## 各工具的差異', '## 其他')),
        ('連結指錯', ZIP_README.replace('](PROJECT-BOOTSTRAP.md)', '](missing.md)')),
        ('權威段落抽掉', ZIP_README.replace('跨工具與跨平台', '工具說明')),
        ('驗收指標抽掉', ZIP_README.replace('第 5 節', '另一節')),
        ('App 舊說回來', ZIP_README + '\n- **Codex 桌面 App**：沒有 hook 機制。\n'),
        ('AG 舊說回來', ZIP_README + '\n- **Antigravity**：沒有 hook 機制。\n'),
    )
    for name, mutated in cases:
        if not zip_readme_problems(mutated):
            problems.append('負向測試未擋住：' + name)
    if problems:
        record('FAIL', 'ZIP 說明指標', '；'.join(problems))
        return False
    record('OK', 'ZIP 說明指標', '指向同包部署包的權威段落與第 5 節，無逐工具副本；六個負向測試通過')
    return True


# 只守已知回歸，不把所有「未解」「沒觸發」都擋掉，也不掃表頭的歷史變更記錄。
# 若未來有新證據改變結論，應連同本表一起更新；不是用保鮮期代替實際查證。
STALE_TOOL_PROSE = (
    ('2.0 仍列未測', r'2\.0\s*(?:未測|尚未測)'),
    ('CLI／2.0 仍列未測', r'(?:還沒|尚未)在\s*2\.0\s*與\s*CLI\s*上測過'),
    ('Antigravity 仍列未附接線', r'Antigravity\s*骨架(?:還沒|尚未)附接線'),
    ('skill 仍被稱作唯一入口', r'那是這個工具上唯一的入口'),
    ('IDE 追查又列下一步', r'要查就在\s*IDE\s*上重跑'),
)


def stale_tool_prose_problems(text):
    # 表頭的 dated changelog 保留事故史；第一個二級標題之後才是現行說明與範本。
    body = re.search(r'^## ', text, re.M)
    current = text[body.start():] if body else text
    current = re.sub(r'\s+', ' ', current.replace('`', '').replace('**', ''))
    return [label for label, pattern in STALE_TOOL_PROSE if re.search(pattern, current)]


def step_tool_prose(dest):
    documents = (
        ('部署包正文', KIT.read_text(encoding='utf-8')),
        ('本 repo ARCHITECT', (ROOT / 'ARCHITECT.md').read_text(encoding='utf-8')),
        ('重生 ARCHITECT', (dest / 'ARCHITECT.md').read_text(encoding='utf-8')),
        ('重生交接協定', (dest / 'docs/ai-notes/handover-protocol.md').read_text(encoding='utf-8')),
    )
    problems = [f'{name}：{problem}' for name, text in documents
                for problem in stale_tool_prose_problems(text)]
    regressions = (
        'IDE `1.107.0` 沒觸發、2.0 未測。',
        '而那正是還沒在 2.0 與 CLI 上測過的事。',
        'Antigravity 骨架還沒附接線。',
        '**那是這個工具上唯一的入口**。',
        '要查就在 IDE 上重跑這份接線。',
    )
    for name, text in documents:
        for old in regressions:
            if not stale_tool_prose_problems(text + '\n' + old):
                problems.append(f'負向測試未擋住（{name}）：{old}')
    control = ('> 2026-10-30 當時寫的是：2.0 未測、Antigravity 骨架還沒附接線。\n'
               '\n## 現況\nCLI／2.0 已實測；IDE 沒觸發，原因未解、不再追查。\n')
    if stale_tool_prose_problems(control):
        problems.append('範圍測試誤擋歷史紀錄或 IDE 未解事實')
    if problems:
        record('FAIL', '跨工具過期敘述', '；'.join(problems))
        return False
    record('OK', '跨工具過期敘述',
           '正文與重生範本無已知舊斷言；%d 個回歸負向測試通過，歷史紀錄與 IDE 未解事實保留'
           % (len(documents) * len(regressions)))
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
    step_readme_table()
    step_zip_readme()
    step_tool_prose(dest)

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

給 hook 腳本執行權限（Windows 不需要）：

```bash
chmod +x .claude/hooks/*.sh
```

## 各工具的差異

工具能力、信任審核與已實測版本，請讀同包的 [PROJECT-BOOTSTRAP.md](PROJECT-BOOTSTRAP.md)
「跨工具與跨平台」；實際驗收照該檔第 5 節，設定檔存在不代表 hook 已生效。
本說明只放指標，不另維護一份工具能力摘要：重查後若只修部署包，這裡的舊說法就會無聲留下。

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
            step_codex_windows(dest, tmp)
            step_portability(dest)
            hooked = step_hook(dest, tmp)
            work = hooked if isinstance(hooked, pathlib.Path) else None
            step_busy(dest, work)
            step_repo_busy(work)
            step_version_check(work)
            step_rename_line(dest)
        step_eol(dest)
        step_self()
        step_sync_coverage(dest)
        step_sync_self_guard()
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
