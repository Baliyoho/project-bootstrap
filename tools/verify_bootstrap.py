#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""驗證 PROJECT-BOOTSTRAP.md 這份部署包本身還能不能用（本 repo 唯一的驗證腳本）。

為什麼有這支：AGENTS.md 鐵律第 4 條要求「改完部署包要重生一次骨架驗證」，但在 2026-08-05
之前那是一段要人照著手刻的敘述——每一棒都得重刻一次，於是實務上常常跳過。把它固化成一個
指令，驗證才會真的發生。這支腳本是部署包的測試；本 repo 自己的交接快照與開場 hook
也由它檢查，不另部署一份 check_docs.py。

用法（在本 repo 根目錄執行）：
  python -X utf8 tools/verify_bootstrap.py
  python -X utf8 tools/verify_bootstrap.py --staged  # B7：驗提交候選與工作樹一致
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
  bash 3.2 多位元組變數——shell 腳本裡 `$變數` 後面不得緊接中文或全形字，要寫 `${變數}`。
                  macOS 的 /bin/bash 3.2 在 UTF-8 語系下會把那個字的第一個位元組吃進變數名，
                  訊息印成亂碼、「$tool」整個消失；Windows 的 Git Bash（bash 5）不重現，所以
                  只靠實跑永遠是綠的（2026-11-06 第一次在 Mac 上跑才發現，附負向測試）
  接線 cwd 定位 ——從子目錄實跑接線 JSON 裡原始的那一串命令（含空白與中文的 repo 路徑）。
                  舊接線假設 cwd 是 repo 根目錄，`cd tools` 開的 session 直接 exit 127，
                  而 SessionStart 失敗跟「檢查過了沒事」在畫面上一模一樣（2026-11-02／F05，
                  附舊形式與 Windows 混合斜線兩個負向測試）
  AI push 提醒 ——18 情境，含未提交修改、命令邊界與舊捷徑負向測試
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
  續聊狀態與計數——skill 與指標的 description 都要觸發已交棒後的新訊息；命名程序必須有
                  先恢復工作中、只讀不寫 Git、改檔重查 A 模式與成功交棒才累加的規則。
                  附負向測試；只驗程序文字沒有退化，不宣稱量到外部工具真的逐訊息改名
  工作中標記   ——HANDOFF.md 範本要有「工作中」欄位，且 git-freshness 讀 origin 那一份後
                  別台機器印 🔴、自己這台印 🟡、已交棒印 ✅、欄位不存在印 🟡。這條鏈斷掉
                  不會有徵兆，下一棒只會看到一切正常然後接棒（2026-10-30 加入）
  本 repo 交接 ——HANDOFF 必要欄位、80 行上限、版本與已知過期待辦；入口不得再教人只改標記。
                  只守可機械判定與已知回歸，不代替 B6 核對任意待辦是否真的完成
  來源例外可見性——逐項印出三項已宣告減項，核對來源缺而產物有；漏宣告、來源增項及
                  產物缺項均有負向變異。不代表 F46 全部同組情境已驗收（2026-11-08）
  交接快照同組情境——有效、整份缺失、占用欄缺失／重複、章節缺失、超行數，用同一份
                  合成輸入跑來源檢查與部署後 check_docs；仍非 F46 整項驗收
  文件同組情境——同一份合成文件跑來源檢查與部署後 check_docs；20 種連結／日期等正反例，
                  另有 9 種非 Markdown 佔位符、自訂過期字串與豁免情境；仍非 F46 整項驗收
  來源提交候選一致性——來源 --staged 拒絕部分 stage 與未追蹤檔；完整／部分 stage 同組
                  情境對照產物 check_docs.py --staged，仍非 F46 整項驗收
  verify_state ——失敗不得吞成 exit 0：命令非零退出、HTTP 500、連不上、200 但回應內容
                  不對都要讓結束碼非零；缺憑證是 SKIP（`--strict` 才非零），未填仍回 0，
                  祕密要遮罩。九個情境全部實跑（2026-11-02 加／F04）
  交接快照     ——check_docs 的第 7 項：HANDOFF.md 不見了、超過 80 行、缺必要章節或欄位
                  重複都要 exit 2，`--docs-only` 要真的關得掉；連結檢查不得把程式碼範例、
                  帶 title 與角括號連結誤報，但真的死連結仍要抓到（2026-11-02 加／F08）
  Python 下限 ——兩支維護工具檔頭都有 MIN_PY 守門且同號、README 範本寫出部署後工具的
                  下限、四支 .py 都沒有用到高於下限的 API。掃描前先把註解與字串塗白，
                  否則「解釋為什麼不要用」會被判成用法（2026-11-02 加／F14）
  主張沒復活   ——已修正的主張不得在範本、操作卡與入口文件裡復活：能力表 ✅ 的工具不得被
                  散文說成沒有 skill、交接 prompt 不得有自己的 A／B 編號、verify_state 不得
                  以憑證為前提、版本序號只有一種算法、可攜層不得寫成「到哪都成立」。綁的是
                  結構不是禁句，`舊版 …` 的引用刻意放行（2026-11-02 加／F15）
  行末與雜項   ——本 repo 與重生骨架全 LF、兩份 JSON 設定合法、verify_state 與
                  git-freshness 可執行
  同步安全     ——sync_project.py 只擁有指向骨架腳本的 handler（同組的自訂 hook 要留），
                  且任一項算不出來就零寫入、失敗要非零退出（2026-11-02／F02、F03）
  同步清單     ——sync_project.py 的清單要涵蓋骨架每一個檔，且 hook 接線合併要真的換掉
                  舊值又保住專案自己的設定。兩份 JSON 接線從來不在清單裡，於是 matcher
                  的修正一年半沒發下去，pre-push 防呆在那些專案等於沒裝（2026-10-30 加入）



Python 版本下限：這兩支維護工具（本檔與 `sync_project.py`）宣告的下限寫在下面的 MIN_PY，
而且在檔頭就檢查、清楚報錯。那是**靜態擔保**（「不使用更新的 API」），不是「在那個版本上
跑過」——實跑過的只有本機這一版。守門人是「Python 版本下限」那一項：它掃四支 .py（兩支
維護工具＋兩支部署後工具）有沒有用到高於下限的 API，所以下一棒順手用一個新 API 時會當場
FAIL，而不是在別人的舊 python 上才炸（查核報告 F14）。

結束碼：0＝全過；1＝有跳過項（缺 bash 之類）但無失敗；2＝有失敗。
本工具唯讀本 repo，只在系統暫存區寫檔。
"""
import argparse
import atexit
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import http.server
import io
import tempfile
import threading
import tokenize
import zipfile
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch
from datetime import date

# Python 版本下限（2026-11-02／查核報告 F14）。在檔頭就擋，而且訊息要說「版本太舊」——
# 高於下限的 API 不會在啟動時失敗，而是執行到那一行才炸成 TypeError／AttributeError，
# 那種形狀沒人會聯想到版本。兩支維護工具的 MIN_PY 必須一致，由「Python 版本下限」那一
# 項檢查釘住。
MIN_PY = (3, 8)
if sys.version_info < MIN_PY:
    sys.exit('需要 Python %d.%d 以上，本機是 %d.%d——請改用較新的 python'
             % (MIN_PY + sys.version_info[:2]))

ROOT = pathlib.Path(__file__).resolve().parent.parent
KIT = ROOT / 'PROJECT-BOOTSTRAP.md'

# 第 3 節應該產出的檔案。少一份就是有人刪了範本卻沒發現；多一份就把它加進來。
EXPECTED = {
    'AGENTS.md', 'ARCHITECT.md', 'CLAUDE.md', 'GEMINI.md', 'HANDOFF.md', 'README.md',
    'docs/ai-notes/handover-protocol.md', 'docs/ai-notes/roadmap.md',
    '.claude/skills/handoff/SKILL.md', '.claude/skills/handoff/mode-a.md',
    '.claude/skills/handoff/mode-a-stop.md', '.claude/skills/handoff/mode-b.md',
    '.claude/skills/handoff/mode-0.md', '.claude/skills/handoff/reasons.md',
    '.claude/settings.json',
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

# 測試用的全域 git 設定：只關掉自動維護（2026-11-06）。
# Git 2.54（macOS 的 Apple Git-157）每次 commit／push 後都會 `git maintenance run --auto --detach`，
# 小 repo 也做 geometric repack 並寫 MIDX。背景打包跟緊接的本機 clone 撞在一起時，
# clone 會因為要硬連結的鬆散物件已經被打包刪掉而失敗（R03 owner 情境在 Mac 上約一半機率）。
# 不能用 GIT_CONFIG_COUNT：本機 push 啟動遠端 receive-pack 時 git 會清掉那組變數，
# origin 那一端看不到；GIT_CONFIG_GLOBAL 指向的檔案兩端都讀得到。
_GITCONFIG_DIR = tempfile.mkdtemp(prefix='verify-gitconfig-')
atexit.register(shutil.rmtree, _GITCONFIG_DIR, True)
_GITCONFIG = os.path.join(_GITCONFIG_DIR, 'gitconfig')
with open(_GITCONFIG, 'w', encoding='utf-8', newline='') as _f:
    _f.write('[maintenance]\n\tauto = false\n')

GIT_ENV = dict(
    os.environ,
    GIT_AUTHOR_NAME='verify', GIT_AUTHOR_EMAIL='verify@example.com',
    GIT_COMMITTER_NAME='verify', GIT_COMMITTER_EMAIL='verify@example.com',
    GIT_CONFIG_GLOBAL=_GITCONFIG, GIT_CONFIG_SYSTEM=os.devnull,
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


def read_lf(path, encoding='utf-8'):
    """讀檔，不做換行轉換（等同 Path.read_text(newline='')，但不需要 3.13）。

    **不要改回 `Path.read_text(..., newline='')`**：那個參數官方標「Changed in 3.13」，
    而這兩支維護工具宣告的下限是 MIN_PY。`open()` 的 newline 參數從一開始就有。
    2026-11-02 之前這裡就是 3.13-only 的寫法，而文件只說「`python` 不存在就用
    `python3`」——在 3.12 上它會在執行到那一行時才炸（查核報告 F14）。
    """
    with open(path, encoding=encoding, newline='') as fh:
        return fh.read()


def write_lf(path, text, encoding='utf-8'):
    """寫檔，不做換行轉換（`Path.write_text` 的 newline 參數要 3.10，見 read_lf）。"""
    with open(path, 'w', encoding=encoding, newline='') as fh:
        fh.write(text)


# ── 1. 重生骨架 ────────────────────────────────────────────────
SKILL_DIR = '.claude/skills/handoff/'
# 入口排最前、新寫的正常路徑摘要排最後：下面依標題找段落的檢查（「### A5 」之類）要先碰到
# 逐字搬來的原文，摘要另外由「skill 入口與常態必讀量」那一項守。
SKILL_FILES = ('SKILL.md', 'mode-a-stop.md', 'mode-b.md', 'mode-0.md', 'reasons.md', 'mode-a.md')
SKILL_ROUTINE = ('SKILL.md', 'mode-a.md')       # 正常接棒要讀的兩個檔
SKILL_ROUTINE_LIMIT = 6000                       # 設計稿第 3 節；F22 的 12,000 還要留給專案文件


def skill_text(dest):
    """整個 handoff skill 目錄的文字。2026-11-10 拆成六個檔之後，內容檢查看的是目錄而不是入口。"""
    return '\n'.join(read_lf(dest / (SKILL_DIR + name)) for name in SKILL_FILES)


def extract(dest, text=None):
    lines = (read_lf(KIT) if text is None else text).split('\n')
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
def ignore_rules(answer):
    """訪談的 Markdown 路徑清單 → .gitignore 的每行一個 pattern。"""
    rules = re.findall(r'`([^`]+)`', answer) or answer.splitlines()
    rules = [r.strip() for r in rules]
    if not rules or any(not r.strip() or r.startswith('!') or '\n' in r or '\r' in r for r in rules):
        raise ValueError('ignore 訪談須是非空且不含 ! 的路徑清單')
    return '\n'.join(r.strip() for r in rules)


def step_fill(dest, answers=None, report=True):
    answers = ANSWERS if answers is None else answers
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
            if key not in answers:
                unknown.add(key)
                return f'UNKNOWN_{key}'
            return ignore_rules(answers[key]) if f.name == '.gitignore' and key in ('SECRETS', 'RUNTIME_DIRS') else answers[key]

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
    if report:
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


# bash 3.2 在 UTF-8 語系下的變數名界線（2026-11-06）。
# `$name` 後面緊接多位元組字元時，bash 3.2 會把那個字的第一個位元組當成變數名的一部分：
# `（branch=$branch）` 印成 `（branch=��`。判斷邏輯不受影響，壞的是每一句結論訊息。
# 用靜態掃描而不是實跑：維護者多在 Windows 的 bash 5 上跑驗證，那裡不會重現。
MB_VAR_RE = re.compile(r'\$[A-Za-z_][A-Za-z0-9_]*(?=[^\x00-\x7f])')


def mb_var_hits(text):
    """回傳 (行號, 命中) 清單；整行註解不求值，略過。"""
    hits = []
    for n, line in enumerate(text.split('\n'), 1):
        if line.lstrip().startswith('#'):
            continue
        hits += [(n, m.group()) for m in MB_VAR_RE.finditer(line)]
    return hits


def step_bash32_multibyte(dest):
    # 負向測試：壞寫法一定要抓到，正確寫法與註解不能誤報
    probes = [
        ('echo "（b=$b）"', 1), ('echo "「$tool」"', 1), ('echo "$a、$b"', 1),
        ('echo "（b=${b}）"', 0), ('# 註解裡的 $b） 不求值', 0), ('echo "$b ok"', 0),
    ]
    wrong = [s for s, want in probes if len(mb_var_hits(s)) != want]
    if wrong:
        record('FAIL', 'bash 3.2 多位元組變數', '偵測器本身壞了：' + '；'.join(wrong))
        return False
    files = [f for f in sorted(dest.rglob('*.sh')) if '.git' not in f.parts]
    files += sorted((ROOT / '.claude' / 'hooks').glob('*.sh'))
    bad = []
    for f in files:
        rel = f.relative_to(dest).as_posix() if dest in f.parents else \
            '本 repo:' + f.relative_to(ROOT).as_posix()
        for n, hit in mb_var_hits(f.read_text(encoding='utf-8')):
            bad.append(f'{rel}:{n}  {hit}…（改成 ${{{hit[1:]}}}）')
    if bad:
        record('FAIL', 'bash 3.2 多位元組變數',
               f'{len(bad)} 處：\n           ' + '\n           '.join(bad[:8]))
        return False
    record('OK', 'bash 3.2 多位元組變數',
           f'骨架與本 repo 共 {len(files)} 支 .sh 無「$變數緊接全形字」；{len(probes)} 個正負向探針通過（靜態，未在 bash 3.2 實跑）')
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
            fh.write('\n- 這行是驗證用的：' + '{{' + 'PROJECT_NAME' + '}}' + '\n')
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
        record('FAIL', '工作中欄位格式（負向測試）', 'HANDOFF.md 範本找不到「工作中」欄位列')
        return False
    sess = '`㊣　26103009｜測試｜工作中`'
    # 四個都要被擋下。後三個是 2026-11-02 補的 F01 負向測試，在舊版（`'無' in value`
    # 就跳過驗證、而且只看第一列）上**全部會 exit 0**：
    #   ②「修無效連結」是完全正常的任務名稱，卻讓整個格式驗證被跳過；
    #   ③ 第一列寫「無（已交棒）」、第二列是真的占用標記——hook 只讀第一列，所以
    #      重複欄位等於讓人用一行字關掉防呆；
    #   ④ 機器欄空白，舊版照樣當成合法的三欄標記。
    bads = (
        ('舊格式沒有工具欄', '缺工具欄',
         '`desk-win` ／ ' + sess + '，2026-10-30 09:12 (+08) 開工'),
        ('主題含「無」仍要驗格式', '缺工具欄',
         '`other-box` ／ `㊣　26110209｜修無效連結｜工作中`'),
        ('欄位重複', '列「工作中」欄位',
         '無（已交棒）\n' + field + '`other-box` ／ `Codex CLI` ／ ' + sess),
        ('機器欄空白', '解析不出機器欄', '／ `Codex CLI` ／ ' + sess),
    )
    try:
        for name, want, value in bads:
            with open(target, 'w', encoding='utf-8', newline='') as fh:
                fh.write(original.replace(line, field + value))
            git(['add', '-A'], dest)
            r = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
            if r.returncode != 2 or want not in r.stdout:
                record('FAIL', '工作中欄位格式（負向測試）',
                       f'「{name}」沒被擋下：期望 exit 2 並指出「{want}」，'
                       f'實得 exit {r.returncode}——檢查 check_docs.py 的 check_busy_field')
                return False
        # 反向保險：修法不能嚴到連正常的已交棒值都認不出來（前後多幾個空白也要過）
        with open(target, 'w', encoding='utf-8', newline='') as fh:
            fh.write(original.replace(line, field + '　無（已交棒）　'))
        git(['add', '-A'], dest)
        r = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
        if r.returncode != 0:
            record('FAIL', '工作中欄位格式（負向測試）',
                   f'「已交棒前後有空白」被誤擋：期望 exit 0，實得 exit {r.returncode}')
            return False
        record('OK', '工作中欄位格式（負向測試）',
               '%d 種壞格式都擋下（exit 2），正常的已交棒值不誤擋' % len(bads))
        return True
    finally:
        with open(target, 'w', encoding='utf-8', newline='') as fh:
            fh.write(original)
        git(['add', '-A'], dest)


# ── 5. AI push 提醒情境 ────────────────────────────────────
def step_hook(dest, tmp):
    bash = find_bash()
    if not bash:
        record('SKIP', 'AI push 提醒情境', '找不到看得懂 Windows 路徑的 bash（裝 Git for Windows 即可）')
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

    def command(value):
        return fire(json.dumps({'tool_input': {'command': value}}))

    # F06：明列有限提醒的邊界，不把 substring 判讀冒充 shell／refspec 解析。
    cases.append(('選項 -c（刻意漏判）', 0, command('git -c color.ui=false push origin main')))
    cases.append(('其他 remote（仍看 origin，可能誤擋）', 2, command('git push backup main')))
    cases.append(('其他 refspec（仍看目前分支，可能誤擋）', 2, command('git push origin HEAD:feature/x')))
    cases.append(('僅提到 push（已知誤擋）', 2, command('echo git push')))
    cases.append(('script 間接 push（刻意漏判）', 0, command('./publish.sh')))
    cases.append(('GUI 無命令 payload（不覆蓋）', 0, fire('{}')))
    cases.append(('停用開關確實繞過阻擋', 0, fire(push, env=dict(GIT_ENV, HANDOFF_HOOK='off'))))

    (work / 'HANDOFF.md').open('a', encoding='utf-8', newline='').write('\n- 驗證用\n')
    cases.append(('HANDOFF 僅 unstaged', 2, fire(push)))
    git(['add', 'HANDOFF.md'], work)
    cases.append(('HANDOFF 僅 staged', 2, fire(push)))
    (work / 'HANDOFF.md').open('a', encoding='utf-8', newline='').write('\n- 尚未提交\n')
    cases.append(('HANDOFF staged 加 unstaged', 2, fire(push)))

    # 負向儀器：把 F06 修正前的放行捷徑插回去，必須重現錯誤的 exit 0。
    hook_path = pathlib.Path(hook)
    fixed = read_lf(hook_path)
    anchor = 'git diff --name-only "origin/$branch..HEAD"'
    at = fixed.index(anchor)
    try:
        write_lf(hook_path, fixed[:at] + 'git diff --quiet -- HANDOFF.md 2>/dev/null || exit 0\n' + fixed[at:])
        cases.append(('負向：舊捷徑重現錯誤放行', 0, fire(push)))
    finally:
        write_lf(hook_path, fixed)
    git(['commit', '-qam', 'chore: handoff'], work)
    cases.append(('交棒快照已提交', 0, fire(push)))
    git(['push', '-q', 'origin', 'main'], work)
    handoff = work / 'HANDOFF.md'
    write_lf(handoff, read_lf(handoff).replace('無（已交棒）', '`fixture` ／ `Codex CLI`'))
    git(['commit', '-qam', 'chore: claim'], work)
    cases.append(('開工標記已提交（不等於交棒）', 0, fire(push)))

    git(['checkout', '-q', '-b', 'feature/x'], work)
    (work / 'README.md').open('a', encoding='utf-8', newline='').write('\nwip\n')
    git(['commit', '-qam', 'wip'], work)
    cases.append(('feature 分支', 0, fire('{"tool_input":{"command":"git push origin feature/x"}}')))
    cases.append(('feature 推 main refspec（刻意漏判）', 0, command('git push origin HEAD:main')))

    git(['checkout', '-q', 'main'], work)
    cases.append(('HANDOFF_HOOK=off', 0, fire(push, env=dict(GIT_ENV, HANDOFF_HOOK='off'))))

    bad = [f'{n}：期望 {want}、實得 {got}' for n, want, got in cases if want != got]
    if bad:
        detail = '；'.join(bad)
        if noise:
            detail += '\n           hook stderr：' + ' | '.join(dict.fromkeys(noise))
        record('FAIL', 'AI push 提醒情境', detail)
        return False
    record('OK', 'AI push 提醒情境', '、'.join(f'{n}→{want}' for n, want, _ in cases))
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

    # ── F01 的負向測試（2026-11-02）。舊版 `case "$busy" in *無*)` 拿整列當子字串比，
    # 機器名比對也拿整列當乾草堆，所以下面前四個情境在舊版上全是錯的，而且錯的方向
    # 都是「放行」：前兩個直接印 ✅、第三個把別台機器讀成自己這台、第四個讓 head -1
    # 替你選一列。第五個是反向保險——修法不能嚴到連正常的已交棒值都認不出來。
    free = '✅ 「工作中」是'
    other = '🔴 另一台機器正在'

    out = push_busy('`other-box` ／ `Codex CLI` ／ `㊣　26110209｜修無效連結｜工作中｜交棒0次`',
                    claude)
    cases.append(('主題含「無」→🔴', other in out and free not in out))

    out = push_busy('`無人機-box` ／ `Codex CLI` ／ ' + sess, claude)
    cases.append(('機器名含「無」→🔴', other in out and free not in out))

    # 機器名互為子字串：舊版拿 $me 當針、整列當乾草堆，所以 `<me>-2` 會被讀成「同一台」。
    out = push_busy('`%s-2` ／ `Claude Code` ／ %s' % (me, sess), claude)
    cases.append(('機器名互為子字串→🔴', other in out and '🟡 這台機器' not in out))

    # 兩列欄位，第一列寫「無（已交棒）」、第二列是真的占用標記。舊版只讀第一列，
    # 於是一行字就能無聲關掉整個防呆。
    out = push_busy('無（已交棒）\n- **工作中**：`other-box` ／ `Codex CLI` ／ ' + sess, claude)
    cases.append(('欄位重複→🔴不猜', '列「工作中」欄位' in out and free not in out))

    # 機器欄空白：F01 新加的「解析不出來就當成有人在做」那條分支。順便釘住訊息的字面
    # 寫法——它原本用反引號包欄位名，而反引號在雙引號裡是**命令替換**，shell 會真的去
    # 執行「機器」，那三個欄位名就變成空白。改回反引號的話這串字會被吃掉，這一項就 FAIL。
    out = push_busy('／ `Codex CLI` ／ ' + sess, claude)
    cases.append(('機器欄空白→🔴且不猜',
                  '解析不出機器欄' in out and free not in out
                  and '「機器 ／ 工具 ／ session 名」' in out))

    out = push_busy('　無（已交棒）　', claude)
    cases.append(('已交棒前後有空白→✅', free in out and other not in out))
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
        write_lf(target, base.replace(line, '- %s：%s' % (field, value)))
        git(['commit', '-qam', 'chore: busy'], work)
        git(['push', '-q', 'origin', 'main'], work)
        return run([bash, hook], cwd=work, env=env or tool_env()).stdout

    cases, out = busy_cases(push_busy, me)
    # 欄位整列拿掉：舊骨架的樣子。要印 🟡 說「查不了」，不能安靜放過——
    # 安靜放過跟「查過了沒事」在畫面上一模一樣，那就回到了這個機制要解決的問題本身。
    write_lf(target, base.replace(line + '\n', ''))
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
        write_lf(target, body)
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
    （真正會壞的是比對，不是 curl）。五個情境：落後要講、**領先不能說成落後**、
    領先要勸退同步、同版要閉嘴、關掉開關要閉嘴。方向那兩項是 2026-11-02 補的（F09）。
    """
    bash = find_bash()
    if not bash or work is None:
        record('SKIP', '骨架版本落後偵測', '缺 bash 或 hook fixture')
        return None
    hook = '.claude/hooks/git-freshness.sh'
    cache = work / '.claude' / '.bootstrap-version'
    mark = '骨架落後'

    # 🔴 快取裡放的是「上游最新版」，所以落後的情境要餵一個**比本機新**的版本。
    # 2026-11-02 修（查核報告 F09）：舊版這裡餵 1999-01-01——那是上游比本機**舊**，
    # 也就是「本機領先」，卻被命名成「落後→講」並且通過。所以這個測試不但沒守住方向，
    # 還會把任何正確的修法判成 FAIL。方向弄反時沒有任何徵兆，因為舊實作只比 `!=`。
    write_lf(cache, '2099-01-01')
    lag = run([bash, hook], cwd=work).stdout
    off = run([bash, hook], cwd=work, env=dict(GIT_ENV, BOOTSTRAP_VERSION_CHECK='off')).stdout
    write_lf(cache, '1999-01-01')
    ahead = run([bash, hook], cwd=work).stdout
    write_lf(cache, (ROOT / 'VERSION').read_text(encoding='utf-8').strip())
    same = run([bash, hook], cwd=work).stdout
    cache.unlink(missing_ok=True)

    cases = [('落後→講', mark in lag),
             ('領先→不說落後', mark not in ahead),
             ('領先→說比上游新並勸退同步',
              '比上游新' in ahead and '不要跑 sync_project.py' in ahead),
             ('同版→閉嘴', mark not in same),
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
    skill = skill_text(dest)
    problems = rename_line_problems(skill)
    if problems:
        record('FAIL', '改名寫進回報模板', '；'.join(problems))
        return False

    # 負向測試：一個永遠回 ok 的檢查跟沒有這一項在畫面上一模一樣。
    a5 = 'session：㊣　<YYMMDDHH｜主題>｜工作中｜交棒<N>次（已改）／不適用：<本工具不能改名>；交棒<N>次'
    b9 = 'session：↗　<YYMMDDHH｜主題>｜已交棒｜交棒<N>次（已改）／不適用：<本工具不能改名>；交棒<N>次'
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


def session_resume_problems(skill, pointer):
    """守住 2026-11-02 的程序契約；不模擬模型或外部 session 改名工具。"""
    problems = []
    for name, text in (('skill', skill), ('指標', pointer)):
        description = re.search(r'^description: (.+)$', text, re.M)
        if not description or 'every new user message after a handoff' not in description[1]:
            problems.append(name + ' description 缺續聊觸發')
    # 2026-11-10：命名規則拆到入口（摘要）、mode-b.md（計數）與 reasons.md（細則原文），
    # 所以這裡看整個 skill 目錄；入口自己該有哪些句子由「skill 入口與常態必讀量」守。
    naming = skill
    required = (
        '每則使用者新訊息都先檢查 session 狀態',
        '包含只問問題、補充、更正與致謝',
        '先用改名工具恢復 `㊣ 工作中`，再回答或執行任務',
        '保留原本的 `YYMMDDHH`、主題與交棒次數',
        '只讀續聊不改 HANDOFF、不 commit、不 push，也不為了結束回答再交棒',
        '續聊要改檔前重新走 A1–A5，重查 origin 的工作中標記',
        '續聊回覆必須有 `session：` 一行',
        '交棒次數的家是該 session 標題尾端的 `｜交棒<N>次`，新 session 從 0 起算',
        '只有 B1–B8 完成且 B8 push 成功，才在 B9 把 N 加 1',
        '開工標記、中途安全點、失敗的 push 與重複回報同一次成功交棒都不增加',
        '交棒≥1次',
        '沒有改名能力的工具，以同一 session 最近一次 `session：` 回報保存 N',
        '舊 session 要明確重新讀取新版 skill',
    )
    problems.extend('命名程序缺規則：' + rule for rule in required if rule not in naming)
    for heading in ('### A5 ', '### B9 '):
        block = rename_block(skill, heading) or ''
        session_line = next((l for l in block.splitlines() if l.strip().startswith(RENAME_LINE)), '')
        # 可改名與不適用兩邊都要留計數，避免沒有工具時默默丟失 N。
        if session_line.count('交棒<N>次') != 2:
            problems.append(heading.strip() + ' 回報缺累計交棒次數')
    b9 = skill.partition('### B9 ')[2].partition('## C.')[0]
    if '依「同一 session 的交棒計數」將 N 加 1' not in b9:
        problems.append('B9 沒套用交棒計數')
    return problems


def step_session_resume(dest):
    skill = skill_text(dest)
    pointer = (dest / '.agents/skills/handoff/SKILL.md').read_text(encoding='utf-8')
    problems = session_resume_problems(skill, pointer)
    # 每個守門條件都故意拿掉一次；沒有改到字串也必須失敗，不能空測。
    rules = (
        'every new user message after a handoff',
        '每則使用者新訊息都先檢查 session 狀態',
        '包含只問問題、補充、更正與致謝',
        '先用改名工具恢復 `㊣ 工作中`，再回答或執行任務',
        '保留原本的 `YYMMDDHH`、主題與交棒次數',
        '只讀續聊不改 HANDOFF、不 commit、不 push，也不為了結束回答再交棒',
        '續聊要改檔前重新走 A1–A5，重查 origin 的工作中標記',
        '續聊回覆必須有 `session：` 一行',
        '交棒次數的家是該 session 標題尾端的 `｜交棒<N>次`，新 session 從 0 起算',
        '只有 B1–B8 完成且 B8 push 成功，才在 B9 把 N 加 1',
        '開工標記、中途安全點、失敗的 push 與重複回報同一次成功交棒都不增加',
        '交棒≥1次',
        '沒有改名能力的工具，以同一 session 最近一次 `session：` 回報保存 N',
        '舊 session 要明確重新讀取新版 skill',
        '依「同一 session 的交棒計數」將 N 加 1',
    )
    cases = [(rule, skill.replace(rule, ''), pointer) for rule in rules]
    cases.append(('指標續聊觸發', skill, pointer.replace('every new user message after a handoff', '')))
    for heading in ('### A5 ', '### B9 '):
        block = rename_block(skill, heading) or ''
        cases.append((heading + '計數', skill.replace(block, block.replace('交棒<N>次', '')), pointer))
    for name, changed_skill, changed_pointer in cases:
        if (changed_skill, changed_pointer) == (skill, pointer):
            problems.append('負向測試沒改到字串：' + name)
        elif not session_resume_problems(changed_skill, changed_pointer):
            problems.append('負向測試未擋住：' + name)
    if problems:
        record('FAIL', '續聊狀態與計數', '；'.join(problems))
        return False
    record('OK', '續聊狀態與計數',
           '程序與兩個 description 涵蓋逐訊息恢復、只讀續聊、重查占用、累計與舊版恢復；'
           '%d 個負向測試通過（未呼叫模型／改名工具）' % len(cases))
    return True


REPO_HANDOFF_HEADINGS = ('任務目標', 'Git 狀態', '已完成', '未完成／下一步',
                         '地雷與注意事項', '服務查證與期望快照', '懸置事項（AI 勿自行處理）')
REPO_HANDOFF_STALE = (
    r'Codex\s*接線從來沒真的跑過',
    r'Codex\s*這一面還沒有\s*bash\s*解析的解法',
    r'新發現、還沒處理.{0,80}ZIP_README',
)


def repo_handoff_rule_problems(text):
    flat = re.sub(r'\s+', ' ', text.replace('`', '').replace('**', ''))
    patterns = (r'每輪只維護.{0,45}兩欄', r'每輪一定要維護的只有.{0,45}兩欄',
                r'HANDOFF\.md.{0,12}只當.{0,15}標記的載體',
                r'本 repo 沒有\s*HANDOFF\.md',
                r'本 repo 刻意沒有\s*HANDOFF\.md', r'接線在、但還沒真的跑過')
    return ['交接入口仍有舊規則：' + pattern for pattern in patterns if re.search(pattern, flat)]


def repo_handoff_problems(text, version):
    """2026-11-01：舊快照凍結三輪但全數驗證通過；這裡只查已知回歸，不聲稱理解所有待辦。"""
    if text is None:
        return ['HANDOFF.md 不存在']
    problems = repo_handoff_rule_problems(text)
    if len(text.splitlines()) > 80:
        problems.append('HANDOFF 超過 80 行')
    for label in ('交接時間', '交棒者', '待續分支', '工作中', '骨架版本'):
        matches = re.findall(r'^- \*\*' + re.escape(label) + r'\*\*：(.+)$', text, re.M)
        if len(matches) != 1 or not matches[0].strip():
            problems.append(label + ' 必須有且只有一個非空欄位')
        elif label == '骨架版本' and matches[0].strip() != '`' + version + '`':
            problems.append('HANDOFF 骨架版本與 VERSION 不一致')
        elif label == '工作中':
            # 來源也須拒絕產物 check_docs 會拒絕的壞標記；僅有非空字串
            # 不能證明機器／工具身分可供 A2.5 判讀（F46、R08）。
            value = matches[0].split('，', 1)[0].strip(' \t\u3000`').strip()
            if value != '無（已交棒）':
                fields = [field.strip(' \t\u3000`').strip() for field in value.split('／')]
                if not fields[0]:
                    problems.append('工作中標記缺機器欄')
                elif len(fields) < 2 or not fields[1] or '｜' in fields[1]:
                    problems.append('工作中標記缺工具欄')
    for heading in REPO_HANDOFF_HEADINGS:
        matches = re.findall(r'^## ' + re.escape(heading) + r'\n(.*?)(?=^## |\Z)', text, re.M | re.S)
        if len(matches) != 1 or not matches[0].strip():
            problems.append('缺少或重複交接章節：' + heading)
    flat = re.sub(r'\s+', ' ', text.replace('`', '').replace('**', ''))
    problems.extend('已完成待辦復活：' + p for p in REPO_HANDOFF_STALE if re.search(p, flat))
    return problems


def step_repo_handoff():
    handoff = ROOT / 'HANDOFF.md'
    text = handoff.read_text(encoding='utf-8') if handoff.is_file() else None
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    problems = repo_handoff_problems(text, version)
    for name in ('AGENTS.md', 'ARCHITECT.md', 'README.md', '.claude/hooks/repo-git-check.sh'):
        problems.extend(name + '：' + p for p in
                        repo_handoff_rule_problems((ROOT / name).read_text(encoding='utf-8')))
    # 固定的有效基線讓負向測試不依賴實際快照的待辦內容或工作中／已交棒狀態。
    control = '\n'.join('- **%s**：%s' % (label, value) for label, value in (
        ('交接時間', '2026-11-01 23:18（+08）'), ('交棒者', 'Codex'),
        ('待續分支', '無。'), ('工作中', '無（已交棒）'), ('骨架版本', '`' + version + '`')))
    control += '\n' + '\n'.join('## ' + h + '\n無。\n' for h in REPO_HANDOFF_HEADINGS)
    cases = (
        ('整份缺失', None),
        ('版本落後', control.replace('`' + version + '`', '`2000-01-01`')),
        ('只剩標記', '- **工作中**：無（已交棒）\n'),
        ('缺待辦章節', control.replace('## 未完成／下一步\n無。\n', '')),
        ('空待辦章節', control.replace('## 未完成／下一步\n無。', '## 未完成／下一步\n')),
        ('工作中欄位重複', control + '\n- **工作中**：無（已交棒）'),
        ('超過行數', control + '\n' * 81),
        ('驗收舊待辦', control + '\nCodex 接線從來沒真的跑過。'),
        ('啟動器舊待辦', control + '\nCodex 這一面還沒有 `bash` 解析的解法。'),
        ('ZIP 舊待辦', control + '\n新發現、還沒處理：`ZIP_README` 有過期斷言。'),
    )
    if repo_handoff_problems(control, version):
        problems.append('有效快照被誤擋')
    busy = control.replace('無（已交棒）', '`desk` ／ `Codex CLI` ／ `session`，2026-11-01 開工')
    if repo_handoff_problems(busy, version):
        problems.append('工作中快照被誤擋')
    for name, mutated in cases:
        if mutated == control or not repo_handoff_problems(mutated, version):
            problems.append('負向測試未擋住：' + name)
    rules = ('每輪只維護「待續分支」與「工作中」兩欄。',
             '每輪一定要維護的只有「待續分支」與「工作中」兩欄。',
             'HANDOFF.md 只當「工作中」標記的載體。',
             '本 repo 沒有 HANDOFF.md。', '本 repo 刻意沒有 HANDOFF.md 與 hooks。',
             '接線在、但還沒真的跑過。')
    for old in rules:
        if not repo_handoff_rule_problems(old):
            problems.append('負向測試未擋住入口舊規則：' + old)
    if problems:
        record('FAIL', '本 repo 交接狀態', '；'.join(problems))
        return False
    record('OK', '本 repo 交接狀態',
           '快照必要欄位、≤80 行、版本一致、已知舊待辦與入口規則；%d 個負向測試通過'
           % (len(cases) + len(rules)))
    return True


# 2026-11-10／F22：AGENTS.md 的事故與理由搬到 AGENTS-reasons.md，入口只留規則。
# 搬走之後「保留每條規則的為什麼」（鐵律 3）不能只靠自律：規則沒有理由連結、
# 連結指不到段落、或段落是空的，都要被擋下來。
REASON_FILE = 'AGENTS-reasons.md'
REASON_LINK = re.compile(r'\]\(' + re.escape(REASON_FILE) + r'#([A-Za-z0-9-]+)\)')
REASON_ITEM_SECTIONS = ('鐵律', '副本規則', '改兩支 hook 的訊息時')
REASON_MIN_BODY = 40


def reason_link_problems(agents, reasons):
    """agents／reasons：兩份文件的全文 → 問題清單。"""
    problems = []
    bodies = {}
    chunks = re.split(r'(?m)^<a id="([A-Za-z0-9-]+)"></a>\s*$', reasons)
    for anchor, body in zip(chunks[1::2], chunks[2::2]):
        if anchor in bodies:
            problems.append('理由檔的錨點重複：' + anchor)
        text = '\n'.join(l for l in body.split('\n') if not l.startswith('## '))
        bodies[anchor] = text.strip()
    if not bodies:
        problems.append('理由檔沒有任何錨點')
    used = set()
    sections = re.split(r'(?m)^## ', agents)[1:]
    if not sections:
        problems.append('AGENTS.md 沒有任何章節')
    for section in sections:
        title, _, body = section.partition('\n')
        title = title.strip()
        found = REASON_LINK.findall(body)
        used.update(found)
        if not found:
            problems.append('章節沒有理由連結：' + title)
        if not any(title.startswith(name) for name in REASON_ITEM_SECTIONS):
            continue
        items, current = [], None
        for line in body.split('\n'):
            if re.match(r'(- |\d+\. )', line):
                current = [line]
                items.append(current)
            elif current is not None and line.startswith(' '):
                current.append(line)
            else:
                current = None
        if not items:
            problems.append('章節沒有任何規則項目：' + title)
        for item in items:
            if not REASON_LINK.search('\n'.join(item)):
                problems.append('規則沒有理由連結（%s）：%s' % (title, item[0][:30]))
    for anchor in sorted(used):
        if anchor not in bodies:
            problems.append('理由連結指不到段落：#' + anchor)
        elif len(bodies[anchor]) < REASON_MIN_BODY:
            problems.append('理由段落是空的或過短：#' + anchor)
    return problems


def step_reason_links():
    title = '規則理由連結'
    agents = read_lf(ROOT / 'AGENTS.md')
    path = ROOT / REASON_FILE
    reasons = read_lf(path) if path.is_file() else ''
    problems = reason_link_problems(agents, reasons)
    first = REASON_LINK.search(agents.split('\n## 鐵律', 1)[-1])
    rule = '](%s#%s)' % (REASON_FILE, first.group(1)) if first else None
    anchor = '<a id="%s"></a>' % first.group(1) if first else None
    cases = () if not first else (
        ('理由檔不存在', agents, ''),
        ('規則拿掉理由連結', agents.replace('[為什麼' + rule, '', 1), reasons),
        ('連結指向不存在的段落', agents.replace(rule, '](%s#no-such-reason)' % REASON_FILE, 1),
         reasons),
        ('理由段落被清空', agents,
         re.sub(re.escape(anchor) + r'.*?(?=\n<a id=|\Z)', anchor + '\n\n## 空\n', reasons,
                count=1, flags=re.S)),
        ('錨點重複', agents, reasons + '\n' + anchor + '\n\n## 重複\n' + '字' * REASON_MIN_BODY),
        ('整節沒有理由連結', agents + '\n## 新的一節\n\n只有規則，沒有理由。\n', reasons),
        ('新增規則沒有理由', agents.replace('\n## 副本規則\n', '\n7. **新規則。**\n\n## 副本規則\n', 1),
         reasons),
    )
    if not first:
        problems.append('鐵律一節找不到任何理由連結，負向測試無從建立')
    for name, mutated_agents, mutated_reasons in cases:
        if (mutated_agents, mutated_reasons) == (agents, reasons):
            problems.append('負向測試沒有改到內容：' + name)
        elif not reason_link_problems(mutated_agents, mutated_reasons):
            problems.append('負向測試未擋住：' + name)
    if problems:
        record('FAIL', title, '；'.join(problems))
        return False
    record('OK', title,
           'AGENTS.md 每節與鐵律／副本規則／hook 訊息每條都連到 %s 的非空段落；%d 個負向測試通過'
           '（只查連結與段落存在，不判斷理由寫得對不對）' % (REASON_FILE, len(cases)))
    return True


SOURCE_EXCEPTIONS = (
    ('handoff skill', '.claude/skills/handoff/SKILL.md'),
    ('pre-push-handoff.sh', '.claude/hooks/pre-push-handoff.sh'),
    ('check_docs.py', 'tools/check_docs.py'),
)


def source_exception_problems(architecture, source, generated):
    """F46 partial: report declared source reductions, without calling them parity."""
    marker = '> **宣告的內容**：'
    if architecture.count(marker) != 1:
        return ['正式例外宣告缺失或重複']
    declaration = architecture.split(marker, 1)[1].split('\n>\n', 1)[0]
    problems = []
    for label, relative in SOURCE_EXCEPTIONS:
        hits = declaration.count('**`' + label + '`**') + declaration.count('**' + label + '**')
        if hits != 1:
            problems.append('宣告未逐項列出：' + label)
        if (source / relative).exists():
            problems.append('來源已出現既定減項，須重新審查宣告：' + relative)
        if not (generated / relative).is_file():
            problems.append('產物缺少對照項：' + relative)
    return problems


def step_source_exceptions(dest, tmp):
    architecture = (ROOT / 'ARCHITECT.md').read_text(encoding='utf-8')
    problems = source_exception_problems(architecture, ROOT, dest)
    with tempfile.TemporaryDirectory(prefix='source-exception-', dir=str(tmp)) as name:
        source, generated = pathlib.Path(name) / 'source', pathlib.Path(name) / 'generated'
        source.mkdir()
        for label, relative in SOURCE_EXCEPTIONS:
            target = generated / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('fixture', encoding='utf-8')
        if source_exception_problems(architecture, source, generated):
            problems.append('有效例外 fixture 被誤擋')
        for label, relative in SOURCE_EXCEPTIONS:
            head, rest = architecture.split('> **宣告的內容**：', 1)
            declared, tail = rest.split('\n>\n', 1)
            altered_declaration = declared.replace('**`' + label + '`**', '已省略', 1)
            if altered_declaration == declared:
                altered_declaration = declared.replace('**' + label + '**', '已省略', 1)
            altered = head + '> **宣告的內容**：' + altered_declaration + '\n>\n' + tail
            if altered == architecture or not source_exception_problems(altered, source, generated):
                problems.append('宣告負向測試未擋住：' + label)
            (source / relative).parent.mkdir(parents=True, exist_ok=True)
            (source / relative).write_text('fixture', encoding='utf-8')
            if not source_exception_problems(architecture, source, generated):
                problems.append('來源增項負向測試未擋住：' + label)
            (source / relative).unlink()
            (generated / relative).unlink()
            if not source_exception_problems(architecture, source, generated):
                problems.append('產物缺項負向測試未擋住：' + label)
            (generated / relative).write_text('fixture', encoding='utf-8')
    if problems:
        record('FAIL', '來源例外可見性（F46 部分）', '；'.join(problems))
        return
    record('OK', '來源例外可見性（F46 部分）',
           '已宣告例外：' + '；'.join(label + '（來源缺、產物有）' for label, _ in SOURCE_EXCEPTIONS)
           + '；三類負向變異通過；未驗收來源／產物全部同組情境')


def step_handoff_parity(dest):
    """Run identical synthetic snapshot shapes through source and generated checks."""
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    control = '\n'.join('- **%s**：%s' % (label, value) for label, value in (
        ('交接時間', '2026-11-08 12:00（+08）'), ('交棒者', 'synthetic'),
        ('待續分支', '無'), ('工作中', '無（已交棒）'), ('骨架版本', '`' + version + '`')))
    control += '\n' + '\n'.join('## ' + h + '\n無。\n' for h in REPO_HANDOFF_HEADINGS)
    occupied = control.replace('- **工作中**：無（已交棒）',
                               '- **工作中**：`fixture` ／ `Codex CLI` ／ '
                               '`㊣　26110815｜測試｜工作中`')
    cases = (
        ('有效快照', control, True),
        ('整份缺失', None, False),
        ('缺占用欄', control.replace('- **工作中**：無（已交棒）\n', ''), False),
        ('重複占用欄', control + '\n- **工作中**：無（已交棒）\n', False),
        ('缺下一步章節', control.replace('## 未完成／下一步\n無。\n', ''), False),
        ('超過 80 行', control + ('\n內容' * 81), False),
        ('有效占用標記', occupied, True),
        ('機器欄空白', occupied.replace('`fixture`', '``'), False),
        ('工具欄空白', occupied.replace('`Codex CLI`', '``'), False),
        ('工具欄缺失', occupied.replace(' ／ `Codex CLI`', ''), False),
        ('舊格式把 session 誤作工具',
         occupied.replace('`Codex CLI` ／ ', ''), False),
    )
    target = dest / 'HANDOFF.md'
    original = target.read_text(encoding='utf-8')
    problems = []
    try:
        for name, body, expected in cases:
            source_ok = not repo_handoff_problems(body, version)
            if body is None:
                target.unlink()
                git(['rm', '-q', '--', 'HANDOFF.md'], dest)
            else:
                write_lf(target, body)
                git(['add', '--', 'HANDOFF.md'], dest)
            result = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
            product_ok = result.returncode == 0
            if source_ok != expected or product_ok != expected or \
                    result.returncode != (0 if expected else 2):
                problems.append('%s：來源=%s、產物=exit %s（預期 %s）' % (
                    name, source_ok, result.returncode, expected))
    finally:
        write_lf(target, original)
        git(['add', '--', 'HANDOFF.md'], dest)
    record('FAIL' if problems else 'OK', '來源／產物交接快照同組情境（F46 部分）',
           '；'.join(problems) if problems else
           '%d 種同組情境，含缺檔、結構與機器／工具欄正反例；兩端判定一致' % len(cases))


def step_document_parity(dest, tmp):
    """Apply identical link/date fixtures to source check and generated checker."""
    source = tmp / 'source-doc-fixture'
    source.mkdir()
    write_lf(source / 'README.md', '# fixture\n')
    control = '# ARCHITECT\n\n> 最後更新：2026-11-08\n\n[x](README.md)\n'
    cases = (
        ('有效連結與日期', control, True),
        ('整份文件缺失', None, False),
        ('死連結', control.replace('README.md', 'missing.md'), False),
        ('缺日期標頭', control.replace('> 最後更新：2026-11-08\n', ''), False),
        ('行內程式碼不算連結', control + '\n`[example](missing.md)`\n', True),
        ('程式碼圍欄不算連結', control + '\n```markdown\n[x](missing.md)\n```\n', True),
        ('圍欄後死連結仍攔截', control + '\n```markdown\n[x](missing.md)\n```\n[x](missing.md)\n', False),
        ('角括號路徑與 title', control.replace('[x](README.md)',
                                          '[x](<README.md> "title")'), True),
        ('角括號路徑與 title 的死連結', control.replace('[x](README.md)',
                                                 '[x](<missing.md> "title")'), False),
        ('片段連結', control.replace('[x](README.md)', '[x](README.md#section)'), True),
        ('日期標頭超出前八行',
         control.replace('> 最後更新：2026-11-08\n', '\n'.join(['前言'] * 9)
                         + '\n> 最後更新：2026-11-08\n'), False),
    )
    nested_rel = 'docs/ai-notes/roadmap.md'
    nested_control = '# fixture\n\n> 最後更新：2026-11-08\n\n[x](../../README.md)\n'
    nested_cases = (
        ('巢狀文件有效日期與連結', nested_control, True),
        ('巢狀文件缺失', None, False),
        ('巢狀文件缺日期', nested_control.replace('> 最後更新：2026-11-08\n', ''), False),
        ('巢狀文件日期超出前八行',
         nested_control.replace('> 最後更新：2026-11-08\n',
                                '\n'.join(['前言'] * 9) + '\n> 最後更新：2026-11-08\n'), False),
        ('巢狀文件死連結', nested_control.replace('../../README.md', 'missing.md'), False),
        ('巢狀文件程式碼圍欄豁免',
         nested_control + '\n~~~markdown\n[x](missing.md)\n~~~\n', True),
        ('巢狀文件圍欄後死連結',
         nested_control + '\n~~~markdown\n[x](missing.md)\n~~~\n[x](missing.md)\n', False),
        ('已知佔位符殘留', nested_control + '\n' + '{{' + 'GH_OWNER' + '}}' + '\n', False),
        ('非部署佔位符保留', nested_control + '\n{{PROJECT_LOCAL_VALUE}}\n', True),
    )
    target = dest / 'ARCHITECT.md'
    original = target.read_text(encoding='utf-8')
    nested_target = dest / nested_rel
    nested_original = nested_target.read_text(encoding='utf-8')
    source_nested = source / nested_rel
    source_nested.parent.mkdir(parents=True, exist_ok=True)
    problems = []
    try:
        for name, body, expected in cases:
            if body is None:
                (source / 'ARCHITECT.md').unlink()
                target.unlink()
                git(['rm', '-q', '--', 'ARCHITECT.md'], dest)
            else:
                write_lf(source / 'ARCHITECT.md', body)
                write_lf(target, body)
                git(['add', '--', 'ARCHITECT.md'], dest)
            dead, undated, missing, holes = source_document_problems(source, ['ARCHITECT.md'])
            source_ok = not dead and not undated and not missing and not holes
            result = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
            product_ok = result.returncode == 0
            if source_ok != expected or product_ok != expected or \
                    result.returncode != (0 if expected else 2):
                problems.append('%s：來源=%s、產物=exit %s（預期 %s）' % (
                    name, source_ok, result.returncode, expected))
        write_lf(target, original)
        git(['add', '--', 'ARCHITECT.md'], dest)
        for name, body, expected in nested_cases:
            if body is None:
                source_nested.unlink()
                nested_target.unlink()
                git(['rm', '-q', '--', nested_rel], dest)
            else:
                write_lf(source_nested, body)
                write_lf(nested_target, body)
                git(['add', '--', nested_rel], dest)
            dead, undated, missing, holes = source_document_problems(source, [nested_rel])
            source_ok = not dead and not undated and not missing and not holes
            result = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
            product_ok = result.returncode == 0
            if source_ok != expected or product_ok != expected or \
                    result.returncode != (0 if expected else 2):
                problems.append('%s：來源=%s、產物=exit %s（預期 %s）' % (
                    name, source_ok, result.returncode, expected))
    finally:
        write_lf(target, original)
        git(['add', '--', 'ARCHITECT.md'], dest)
        write_lf(nested_target, nested_original)
        git(['add', '--', nested_rel], dest)
    record('FAIL' if problems else 'OK', '來源／產物文件同組情境（F46 部分）',
           '；'.join(problems) if problems else
           '%d 種同組情境，含巢狀文件日期、佔位符、圍欄、角括號與 title、片段；兩端判定一致'
           % (len(cases) + len(nested_cases)))


def step_document_policy_parity(dest, tmp):
    """Compare configured stale strings and non-Markdown placeholders on both sides."""
    source = tmp / 'source-policy-fixture'
    source.mkdir()
    checker = dest / 'tools/check_docs.py'
    original_checker = checker.read_text(encoding='utf-8')
    readme = dest / 'README.md'
    original_readme = readme.read_text(encoding='utf-8')
    fixture_rel = 'tools/fixture.py'
    fixture = dest / fixture_rel
    source_fixture = source / fixture_rel
    source_fixture.parent.mkdir(parents=True)
    source_readme = source / 'README.md'
    token = '{{' + 'GH_OWNER' + '}}'
    patterns = (('retired.example', '合成舊網域'),)
    cases = (
        ('設定後的有效文件', 'value = "ok"\n', '# fixture\n', False, False, False, True, ''),
        ('非 Markdown 已知佔位符', 'value = "' + token + '"\n',
         '# fixture\n', False, False, False, False, '[holes]'),
        ('非 Markdown 未知樣板保留', 'value = "{{PROJECT_LOCAL_VALUE}}"\n',
         '# fixture\n', False, False, False, True, ''),
        ('佔位符豁免路徑', 'value = "' + token + '"\n',
         '# fixture\n', False, True, False, True, ''),
        ('自訂過期字串', 'value = "ok"\n',
         '# fixture\nretired.example\n', False, False, False, False, '[stale]'),
        ('同列歷史敘述豁免', 'value = "ok"\n',
         '# fixture\nretired.example 已退役\n', False, False, False, True, ''),
        ('過期字串路徑豁免', 'value = "ok"\n',
         '# fixture\nretired.example\n', True, False, False, True, ''),
        ('無豁免的死連結', 'value = "ok"\n',
         '# fixture\n[x](missing.md)\n', False, False, False, False, '[links]'),
        ('連結路徑豁免', 'value = "ok"\n',
         '# fixture\n[x](missing.md)\n', False, False, True, True, ''),
    )
    problems = []
    try:
        for name, py_body, md_body, stale_exempt, hole_exempt, link_exempt, expected, channel in cases:
            write_lf(fixture, py_body)
            write_lf(readme, md_body)
            write_lf(source_fixture, py_body)
            write_lf(source_readme, md_body)
            git(['add', '--', fixture_rel, 'README.md'], dest)
            configured = original_checker.replace(
                "STALE_PATTERNS = [\n    # ('localhost:8080', '已遷到正式網域，文件不該再出現本機位址'),\n]",
                "STALE_PATTERNS = [('retired.example', '合成舊網域')]")
            if configured == original_checker:
                problems.append('找不到產物過期字串設定區塊')
                break
            if stale_exempt:
                configured = configured.replace('STALE_OK_PATHS = ()',
                                                "STALE_OK_PATHS = ('README.md',)")
            if hole_exempt:
                configured = configured.replace(
                    "PLACEHOLDER_OK_PATHS = ('PROJECT-BOOTSTRAP.md',)",
                    "PLACEHOLDER_OK_PATHS = ('PROJECT-BOOTSTRAP.md', 'tools/fixture.py')")
            if link_exempt:
                configured = configured.replace(
                    "LINK_OK_PATHS = ('PROJECT-BOOTSTRAP.md',)",
                    "LINK_OK_PATHS = ('PROJECT-BOOTSTRAP.md', 'README.md')")
            write_lf(checker, configured)
            source_findings = source_repo_document_problems(
                source, ['README.md', fixture_rel], stale_patterns=patterns,
                stale_ok_paths=('README.md',) if stale_exempt else (),
                placeholder_ok_paths=(('PROJECT-BOOTSTRAP.md', fixture_rel)
                                      if hole_exempt else ('PROJECT-BOOTSTRAP.md',)),
                link_ok_paths=('README.md',) if link_exempt else ())
            source_ok = not any(source_findings)
            result = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=dest)
            product_ok = result.returncode == 0
            if (source_ok != expected or product_ok != expected or
                    result.returncode != (0 if expected else 2) or
                    (channel and channel not in result.stdout)):
                problems.append('%s：來源=%s、產物=exit %s（預期 %s／%s）' % (
                    name, source_ok, result.returncode, expected, channel))
    finally:
        write_lf(checker, original_checker)
        write_lf(readme, original_readme)
        git(['add', '--', 'README.md'], dest)
        if fixture.exists():
            git(['rm', '-qf', '--', fixture_rel], dest)
    record('FAIL' if problems else 'OK', '來源／產物文件設定同組情境（F46 部分）',
           '；'.join(problems) if problems else
           '%d 種同組情境，含非 Markdown 佔位符、自訂過期字串、死連結與豁免；兩端判定一致'
           % len(cases))


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


def source_document_problems(root, mds, link_ok_paths=()):
    """Same source document check used by the live repo and F46 fixtures.

    The deployment package intentionally retains interview placeholders. Other
    source documents must not accidentally carry one into a published commit.
    """
    missing = [rel for rel in mds if not (root / rel).is_file()]
    dead, holes = [], []
    for rel in mds:
        if rel in missing:
            continue
        base = (root / rel).parent
        if rel != 'PROJECT-BOOTSTRAP.md':
            for match in PLACEHOLDER_RE.finditer((root / rel).read_text(encoding='utf-8')):
                if match.group(1) in ANSWERS:
                    holes.append('%s → %s' % (rel, match.group(0)))
        # 來源部署包的範本位於圍欄內，仍須檢查；其他文件的圍欄是範例，
        # 與產物 check_docs 一樣略過。F46 同組反例同時驗圍欄後的真死連結。
        lines, fence = [], None
        for line in (root / rel).read_text(encoding='utf-8').split('\n'):
            marker = re.match(r'^\s*(```+|~~~+)', line)
            if rel != 'PROJECT-BOOTSTRAP.md':
                if fence is not None:
                    lines.append('')
                    if marker and line.strip().startswith(fence):
                        fence = None
                    continue
                if marker:
                    fence = marker.group(1)
                    lines.append('')
                    continue
            lines.append(re.sub(r'`[^`]*`', '', line))
        body = '\n'.join(lines)
        if any(rel == p or rel.startswith(p) for p in link_ok_paths):
            continue
        for raw in re.findall(r'\]\(([^)]+)\)', body):
            # title 先於角括號移除；反過來會把合法的 (<path> "title")
            # 當成不存在的字面檔名。這也是產物 R09 的修正邊界。
            link = re.sub(r'\s+["\'][^"\']*["\']\s*$', '', raw.strip()).strip()
            if link.startswith('<') and link.endswith('>'):
                link = link[1:-1].strip()
            if link.startswith(('http://', 'https://', 'mailto:', '#')):
                continue
            target = link.split('#')[0]
            if not target:
                continue
            if rel == 'PROJECT-BOOTSTRAP.md' and template_link(target):
                continue
            if not (base / target).exists():
                dead.append('%s → %s' % (rel, raw))
    undated = [rel for rel in mds
               if (rel in ('AGENTS.md', 'ARCHITECT.md') or rel.startswith('docs/ai-notes/'))
               and (root / rel).is_file() and '最後更新' not in
               '\n'.join((root / rel).read_text(encoding='utf-8').split('\n')[:8])]
    return dead, undated, missing, holes


SOURCE_PLACEHOLDER_SUFFIXES = ('.md', '.py', '.sh', '.json')
SOURCE_PLACEHOLDER_FILES = ('.gitignore', '.gitattributes')
SOURCE_STALE_OK = ('已停用', '已退役', '歷史', '勿再啟動', '~~')


def source_policy_problems(root, files, stale_patterns=(), stale_ok_paths=(),
                           placeholder_ok_paths=('PROJECT-BOOTSTRAP.md',)):
    """Check the source's publishable files with the product's document policy shape.

    The source has no project-specific stale patterns. Synthetic parity cases pass
    a configured pattern explicitly, just as a deployed project's checker does.
    """
    stale, holes = [], []
    for rel in files:
        path = root / rel
        if not path.is_file():
            continue
        body = path.read_text(encoding='utf-8')
        if rel.endswith('.md') and not any(
                rel == p or rel.startswith(p) for p in stale_ok_paths):
            for n, line in enumerate(body.split('\n'), 1):
                for pattern, why in stale_patterns:
                    if pattern in line and not any(ok in line for ok in SOURCE_STALE_OK):
                        stale.append('%s:%d → %s（%s）' % (rel, n, pattern, why))
        if (rel.endswith(SOURCE_PLACEHOLDER_SUFFIXES) or
                rel in SOURCE_PLACEHOLDER_FILES) and not any(
                rel == p or rel.startswith(p) for p in placeholder_ok_paths):
            for n, line in enumerate(body.split('\n'), 1):
                for match in PLACEHOLDER_RE.finditer(line):
                    if match.group(1) in ANSWERS:
                        holes.append('%s:%d → %s' % (rel, n, match.group(0)))
    return stale, holes


def source_repo_document_problems(root, tracked_files, stale_patterns=(),
                                  stale_ok_paths=(),
                                  placeholder_ok_paths=('PROJECT-BOOTSTRAP.md',),
                                  link_ok_paths=()):
    """One source entry point for the live repo and synthetic policy cases."""
    mds = [p for p in tracked_files if p.endswith('.md')]
    nonmds = [p for p in tracked_files if not p.endswith('.md')]
    dead, undated, missing, holes = source_document_problems(root, mds, link_ok_paths)
    stale, _ = source_policy_problems(root, mds, stale_patterns, stale_ok_paths,
                                      placeholder_ok_paths)
    _, extra_holes = source_policy_problems(root, nonmds, (), (), placeholder_ok_paths)
    return dead, undated, missing, stale, holes + extra_holes


def source_staged_problems(root):
    """B7：來源驗證器檢查工作樹，不能拿它證明另一份 staged 內容。

    來源沒有部署後的 check_docs.py；選用 --staged 時，整個提交候選須已 stage，
    且不能留下未暫存或未追蹤檔。未追蹤的連結目標若只在本機存在，
    也可能讓待提交 Markdown 的死連結檢查錯誤通過。
    """
    commands = (
        ('staged', ['diff', '--cached', '--name-only', '-z']),
        ('unstaged', ['diff', '--name-only', '-z']),
        ('untracked', ['ls-files', '--others', '--exclude-standard', '-z']),
    )
    names = {}
    for label, args in commands:
        result = git(args, root)
        if result.returncode:
            return ['讀取 %s 檔案集合失敗：%s' % (label, result.stderr.strip()[:160])]
        names[label] = [name for name in result.stdout.split('\0') if name]
    problems = []
    if not names['staged']:
        problems.append('沒有 staged 提交候選')
    for label in ('unstaged', 'untracked'):
        if names[label]:
            problems.append('%s 檔案尚未納入候選：%s' %
                            (label, '、'.join(names[label][:5])))
    return problems


def step_source_staged_parity(dest, tmp):
    """同一份 staged/unstaged 形狀對照來源檢查與產物 --staged。"""
    source = tmp / 'source-staged-fixture'
    shutil.copytree(dest, source, ignore=shutil.ignore_patterns('.git'))
    git(['init', '-q', '-b', 'main'], source)
    git(['add', '-A'], source)
    git(['commit', '-qm', 'fixture'], source)
    no_stage_rejected = bool(source_staged_problems(source))
    readme = source / 'README.md'
    with readme.open('a', encoding='utf-8', newline='') as handle:
        handle.write('\n驗證提交候選。\n')
    git(['add', '--', 'README.md'], source)
    cases = []
    source_ok = not source_staged_problems(source)
    product = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py', '--staged'], cwd=source)
    cases.append(('完整 stage', source_ok, product.returncode, True))
    with readme.open('a', encoding='utf-8', newline='') as handle:
        handle.write('未暫存內容。\n')
    source_ok = not source_staged_problems(source)
    product = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py', '--staged'], cwd=source)
    cases.append(('部分 stage', source_ok, product.returncode, False))
    restored = git(['checkout', '--', 'README.md'], source)
    untracked_baseline_clean = restored.returncode == 0 and not source_staged_problems(source)
    (source / 'untracked-target.md').write_text('未追蹤\n', encoding='utf-8')
    untracked_rejected = bool(source_staged_problems(source))
    problems = []
    for name, source_ok, product_exit, expected in cases:
        if source_ok != expected or product_exit != (0 if expected else 2):
            problems.append('%s：來源=%s、產物=exit %s（預期 %s）' %
                            (name, source_ok, product_exit, expected))
    if not no_stage_rejected:
        problems.append('空提交候選未被來源檢查攔截')
    if not untracked_baseline_clean:
        problems.append('未追蹤負向測試的起點不乾淨')
    if not untracked_rejected:
        problems.append('未追蹤檔未被來源檢查攔截')
    record('FAIL' if problems else 'OK', '來源提交候選一致性（F46 部分）',
           '；'.join(problems) if problems else
           '完整 stage 通過、部分 stage 兩端拒絕、來源另拒未追蹤檔；未驗實際接手流程')


def handoff_flow_case(kind, dest, tmp, bash):
    """以本機 bare origin 真正推送開工／交棒，再由另一個 checkout 接棒。"""
    home = tmp / ('flow-' + kind)
    origin, writer, reader = home / 'origin.git', home / 'writer', home / 'reader'
    home.mkdir()
    initial = dest if kind == 'product' else ROOT
    if kind == 'product':
        shutil.copytree(initial, writer, ignore=shutil.ignore_patterns('.git'))
        hook_rel = '.claude/hooks/git-freshness.sh'
    else:
        writer.mkdir()
        for rel in ('AGENTS.md', 'ARCHITECT.md', 'HANDOFF.md', 'README.md',
                    '.claude/hooks/repo-git-check.sh'):
            target = writer / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(initial / rel, target)
        hook_rel = '.claude/hooks/repo-git-check.sh'

    handoff = writer / 'HANDOFF.md'
    busy_line = next(line for line in read_lf(handoff).splitlines()
                     if line.startswith('- **工作中**：'))
    write_lf(handoff, read_lf(handoff).replace(busy_line,
             '- **工作中**：無（已交棒）'))
    def must(result, action):
        if result.returncode:
            raise AssertionError('%s exit %s：%s' % (
                action, result.returncode, result.stderr.strip()[:160]))
        return result
    must(run(['git', 'init', '-q', '--bare', str(origin)]), 'init bare')
    must(git(['init', '-q', '-b', 'main'], writer), 'init writer')
    must(git(['add', '-A'], writer), 'stage baseline')
    must(git(['commit', '-qm', 'baseline'], writer), 'commit baseline')
    must(git(['remote', 'add', 'origin', str(origin)], writer), 'remote')
    must(git(['push', '-q', '-u', 'origin', 'main'], writer), 'push baseline')
    must(run(['git', 'clone', '-q', '-b', 'main', str(origin), str(reader)]), 'clone reader')
    env = tool_env(CLAUDECODE='1', BOOTSTRAP_VERSION_CHECK='off')
    hook = reader / hook_rel
    def check_hook(expected):
        result = must(run([bash, str(hook)], cwd=reader, env=env), 'SessionStart hook')
        if expected not in result.stdout:
            raise AssertionError('hook 未印 %s：%s' % (expected, result.stdout.strip()[:200]))
    def set_busy(value, action):
        path = writer / 'HANDOFF.md'
        old = next(line for line in read_lf(path).splitlines()
                   if line.startswith('- **工作中**：'))
        write_lf(path, read_lf(path).replace(old, '- **工作中**：' + value))
        must(git(['add', '--', 'HANDOFF.md'], writer), 'stage ' + action)
        must(git(['commit', '-qm', action], writer), 'commit ' + action)
        must(git(['push', '-q', 'origin', 'main'], writer), 'push ' + action)

    check_hook('✅ 「工作中」是')
    set_busy('`other-box` ／ `Claude Code` ／ `㊣　26110816｜測試｜工作中｜交棒0次`',
             'foreign claim')
    # reader 的本機快照仍空閒；hook 必須 fetch 並讀 origin 那份。
    if '無（已交棒）' not in read_lf(reader / 'HANDOFF.md'):
        raise AssertionError('陳舊 checkout 起點不是空閒快照')
    check_hook('🔴 另一台機器正在')
    counts = must(git(['rev-list', '--left-right', '--count', 'HEAD...@{upstream}'], reader),
                  'A1 counts').stdout.strip()
    if counts != '0\t1':
        raise AssertionError('A1 未辨認落後一筆：' + counts)

    # 負向變異：改成讀 HEAD，陳舊 reader 會錯把遠端占用判成已交棒。
    original = read_lf(hook)
    needle = 'origin/$branch:HANDOFF.md'
    if original.count(needle) != 1:
        raise AssertionError('無法定位 hook 的遠端快照讀取')
    try:
        write_lf(hook, original.replace(needle, 'HEAD:HANDOFF.md'))
        mutant = must(run([bash, str(hook)], cwd=reader, env=env), 'local-only mutant')
        if '✅ 「工作中」是' not in mutant.stdout or '🔴 另一台機器正在' in mutant.stdout:
            raise AssertionError('本機快照負向變異沒有重現錯誤放行')
    finally:
        write_lf(hook, original)

    must(git(['pull', '-q', '--ff-only'], reader), 'A1 fast-forward')
    check_hook('🔴 另一台機器正在')
    set_busy('無（已交棒）', 'foreign release')
    must(git(['pull', '-q', '--ff-only'], reader), 'pull release')
    check_hook('✅ 「工作中」是')
    # A2.5 看到空閒到 A5 開工之間若遠端前進，舊 SHA 不能再授予寫入資格。
    observed = must(git(['rev-parse', 'origin/main'], reader), 'A2.5 SHA').stdout.strip()
    (writer / 'README.md').open('a', encoding='utf-8', newline='').write('\n另一棒先行。\n')
    must(git(['add', '--', 'README.md'], writer), 'stage intervening change')
    must(git(['commit', '-qm', 'intervening change'], writer), 'commit intervening change')
    must(git(['push', '-q', 'origin', 'main'], writer), 'push intervening change')
    must(git(['fetch', '-q', 'origin'], reader), 'A5 refetch')
    current = must(git(['rev-parse', 'origin/main'], reader), 'A5 SHA').stdout.strip()
    if observed == current:
        raise AssertionError('A5 未偵測遠端在觀測後前進')
    must(git(['pull', '-q', '--ff-only'], reader), 'catch up after changed SHA')
    me = must(run([bash, '-c', 'echo "${HOSTNAME:-$(hostname)}"'], cwd=reader),
              'hostname').stdout.strip()
    writer = reader
    set_busy('`%s` ／ `Claude Code` ／ `㊣　26110816｜測試｜工作中｜交棒0次`' % me,
             'own claim')
    check_hook('🟡 這台機器')
    (reader / 'README.md').open('a', encoding='utf-8', newline='').write('\n合成任務。\n')
    must(git(['add', '--', 'README.md'], reader), 'stage task')
    must(git(['commit', '-qm', 'synthetic task'], reader), 'commit task')
    must(git(['push', '-q', 'origin', 'main'], reader), 'push task')
    set_busy('無（已交棒）', 'own release')
    check_hook('✅ 「工作中」是')
    remote = must(git(['show', 'origin/main:HANDOFF.md'], reader), 'remote release').stdout
    if '- **工作中**：無（已交棒）' not in remote:
        raise AssertionError('交棒後 origin 標記未清')
    if git(['status', '--porcelain'], reader).stdout.strip() or \
            git(['rev-list', '--left-right', '--count', 'HEAD...@{upstream}'], reader).stdout.strip() != '0\t0':
        raise AssertionError('交棒後 reader 未乾淨對齊 origin')


def step_handoff_flow_parity(dest, tmp):
    """F46 部分：來源與產物共跑實際 Git 接力，不把 hook 提醒算作程序執行。"""
    bash = find_bash()
    if not bash:
        record('SKIP', '來源／產物接手流程同組情境（F46 部分）', '缺可用 bash')
        return
    problems = []
    for kind in ('source', 'product'):
        try:
            handoff_flow_case(kind, dest, tmp, bash)
        except (AssertionError, OSError, StopIteration) as exc:
            problems.append('%s：%s' % (kind, exc))
    record('FAIL' if problems else 'OK', '來源／產物接手流程同組情境（F46 部分）',
           '；'.join(problems) if problems else
           '兩端各走遠端占用→陳舊接手阻擋→釋出→A2.5/A5 SHA 變更→本機開工→任務推送→交棒；本機快照錯誤放行變異均重現。hook 只提醒，模型遵循未驗')


REPO_START_HOOK = '.claude/hooks/repo-git-check.sh'
REPO_ACTION_HOOK = '.claude/hooks/repo-action-rules.sh'
# 2026-11-10 決策書 Q6 (a)：動作當下送規則只在 Claude Code 那份試行，Codex 那份仍只准 SessionStart。
REPO_ACTION_EVENTS = {'.claude/settings.json': ('PreToolUse', 'PostToolUse'),
                      '.codex/hooks.json': ()}


def repo_wiring_problems(root):
    """本 repo 兩份接線的問題清單。

    兩份接線一起查（2026-11-01 加上 `.codex/hooks.json`）。這個 repo 的接線指的是它
    自己那支 `repo-git-check.sh`，所以它們跟部署包 3.9／3.17 只是長得像、不是副本；
    也因此沒有 `source:` 標記、落後偵測看不到它們，唯一的守門人就是這一項。
    連「有沒有被 sync_project.py 覆蓋過」一起釘：那會把它們改成指向這裡不存在的
    `git-freshness.sh`，開場檢查於是靜默失效——看起來有防護、實際上沒有。
    2026-11-10（Q6 (a)）：原本只准 SessionStart；現在 Claude Code 那份可以多接
    PreToolUse／PostToolUse，但每個 handler 都只能指向 repo-action-rules.sh，其他事件仍拒絕。
    抽成函式是為了讓負向測試能對暫存目錄跑。
    """
    problems, present = [], []
    for rel, extra in REPO_ACTION_EVENTS.items():
        cfg = root / rel
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
        for bad in ('git-freshness.sh', 'pre-push-handoff.sh'):
            if bad in raw:
                problems.append('%s 指向 %s，而這個 repo 沒有那個檔'
                                '（被 sync_project.py 覆蓋過？）' % (rel, bad))
        hooks = data.get('hooks', {})
        for event, groups in hooks.items():
            commands = [h.get('command', '') + ' ' + h.get('commandWindows', '')
                        for g in (groups or []) for h in (g.get('hooks') or [])]
            if event == 'SessionStart':
                if not commands or any(REPO_START_HOOK not in c for c in commands):
                    problems.append('%s 的 SessionStart 沒有都指向 %s' % (rel, REPO_START_HOOK))
            elif event in extra:
                if not commands or any(REPO_ACTION_HOOK not in c for c in commands):
                    problems.append('%s 的 %s 只能指向 %s' % (rel, event, REPO_ACTION_HOOK))
            else:
                problems.append('%s 接了 %s，但這個 repo 只允許 SessionStart%s'
                                % (rel, event, ('＋' + '／'.join(extra)) if extra else ''))
        if 'SessionStart' not in hooks:
            problems.append('%s 沒接 SessionStart' % rel)
    if not (root / REPO_START_HOOK).exists():
        problems.append('%s 不存在——兩份接線都指著一個不在的腳本' % REPO_START_HOOK)
    if REPO_ACTION_HOOK in ''.join(
            (root / r).read_text(encoding='utf-8') for r in REPO_ACTION_EVENTS
            if (root / r).exists()) and not (root / REPO_ACTION_HOOK).exists():
        problems.append('%s 不存在——接線指著一個不在的腳本' % REPO_ACTION_HOOK)
    return problems, present


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
    tracked_files = [p for p in run(['git', 'ls-files', '-z'], cwd=ROOT).stdout.split('\0') if p]
    # 2026-11-11：src/kit/ 是部署包的來源，內容逐位元組生成進 PROJECT-BOOTSTRAP.md
    # （「部署包由來源生成」守），在那裡照部署包的豁免規則查；這裡再查一次只會因為
    # kit.md 放在子目錄、範本保留佔位符而誤報。
    tracked_files = [p for p in tracked_files if not p.startswith('src/kit/')]
    mds = [p for p in tracked_files if p.endswith('.md')]
    dead, undated, missing, stale, holes = source_repo_document_problems(ROOT, tracked_files)
    if dead or undated or missing or stale or holes:
        detail = []
        if missing:
            detail.append('缺檔：%s' % '、'.join(missing[:5]))
        if dead:
            detail.append('死連結 %d 處：%s' % (len(dead), '、'.join(dead[:5])))
        if undated:
            detail.append('缺「最後更新」：%s' % '、'.join(undated))
        if stale:
            detail.append('過期字串：%s' % '、'.join(stale[:5]))
        if holes:
            detail.append('殘留部署佔位符：%s' % '、'.join(holes[:5]))
        record('FAIL', '本 repo 自己的文件', '；'.join(detail))
        ok = False
    else:
        record('OK', '本 repo 自己的文件',
               '%d 個 .md 無死連結、受管非 Markdown 無殘留部署佔位符，日期標頭齊備'
               % len(mds))

    problems, present = repo_wiring_problems(ROOT)
    if problems:
        record('FAIL', '本 repo 兩份接線', '；'.join(problems))
        ok = False
    elif not present:
        record('SKIP', '本 repo 兩份接線', '都不存在——開場沒有 git 檢查，接棒全靠人記得')
    else:
        record('OK', '本 repo 兩份接線',
               '%s 都是合法 JSON、SessionStart 指向 repo-git-check.sh；動作提醒只接在 Claude Code 那份'
               % '＋'.join(present))
    return ok


# 指令本身沒有 push，只有輸出裡換行後出現 git push（git 自己的 hint 就長這樣）。
OUTPUT_ONLY_PUSH = {'tool_name': 'Bash', 'tool_input': {'command': 'git status -sb'},
                    'tool_response': {'stdout': 'hint:\n    git push --set-upstream origin x\n'}}


def step_action_rules(tmp):
    """動作當下送規則（決策書 Q6 (a)，2026-11-10）：實跑 repo-action-rules.sh，並對接線守門做負向測試。

    只證明 hook 在該送的時候送出合法的 additionalContext、不該送的時候安靜、永遠不擋；
    不證明 Claude Code 真的把它放進 context，也不證明模型照它做。
    """
    issues = []
    bash = find_bash()
    script = ROOT / REPO_ACTION_HOOK
    cases = [
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'git add a && git push -q origin b'}}, '準備 push'),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'git -C /x push'}}, '準備 push'),
        ('pre', {'tool_name': 'Edit', 'tool_input': {'file_path': '/r/PROJECT-BOOTSTRAP.md'}}, '正在改部署包'),
        ('pre', {'tool_name': 'Edit', 'tool_input': {'file_path': '/r/src/kit/files/AGENTS.md.tmpl'}}, '正在改部署包'),
        ('pre', {'tool_name': 'Write', 'tool_input': {'file_path': '/r/src/kit/kit.md'}}, '正在改部署包'),
        ('pre', {'tool_name': 'Write', 'tool_input': {'file_path': '/r/.claude/hooks/x.sh'}}, '正在改 hook'),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'git status -sb'}}, None),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'git pushd'}}, None),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'echo 提到 git push 而已'}}, None),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'cat <<X\n說明 git push\nX'}}, None),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'git status\ngit push'}}, '準備 push'),
        ('pre', {'tool_name': 'Edit', 'tool_input': {'file_path': '/r/README.md'}}, None),
        ('pre', {'tool_name': 'Read', 'tool_input': {'file_path': '/r/PROJECT-BOOTSTRAP.md'}}, None),
        ('post', {'tool_name': 'Bash', 'tool_input': {'command': 'git push'}}, 'push 指令剛執行完'),
        ('post', {'tool_name': 'Bash', 'tool_input': {'command': 'git fetch origin'}}, None),
        # 2026-11-10 第二版：只看 tool_input、照 shell 切詞。下面每一條第一版都判錯或沒測。
        ('post', OUTPUT_ONLY_PUSH, None),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'echo "a && git push"'}}, None),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': "printf 'x\\ngit push\\n'"}}, None),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': "printf 'x\ngit push\n'"}}, None),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'git log --grep push'}}, None),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'git stash push'}}, None),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'cat <<X && git push\n內文\nX'}}, '準備 push'),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': '(cd x && git push)'}}, '準備 push'),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'if true; then git push; fi'}}, '準備 push'),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'FOO=1 git -c a.b=c push origin x'}}, '準備 push'),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'echo "沒關的引號 && git status'}}, None),
        ('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'echo "沒關的引號\ngit push'}}, '準備 push'),
    ]
    if not bash:
        issues.append('缺少可用 bash，腳本沒有實跑')
    elif not script.exists():
        issues.append('%s 不存在' % REPO_ACTION_HOOK)
    else:
        for compact in (True, False):
            for phase, payload, want in cases:
                event = 'PostToolUse' if phase == 'post' else 'PreToolUse'
                body = dict(payload, hook_event_name=event)
                text = json.dumps(body, ensure_ascii=False,
                                  separators=(',', ':') if compact else (', ', ': '))
                r = run([bash, str(script), phase], stdin=text)
                label = '%s %s' % (phase, json.dumps(payload['tool_input'], ensure_ascii=False))
                if r.returncode:
                    issues.append(label + ' 結束碼 %d' % r.returncode)
                    continue
                if want is None:
                    if r.stdout.strip():
                        issues.append(label + ' 不該送卻送了')
                    continue
                try:
                    out = json.loads(r.stdout)['hookSpecificOutput']
                except Exception:
                    issues.append(label + ' 輸出不是合法 JSON')
                    continue
                if out.get('hookEventName') != event or want not in out.get('additionalContext', ''):
                    issues.append(label + ' 沒送對應要點')
                if 'permissionDecision' in out or 'decision' in r.stdout:
                    issues.append(label + ' 不該做任何放行／阻擋決定')

        # 負向測試：關掉 JSON 解析、退回第一版的原始字串比對，「只有輸出提到 git push」那個情境
        # 必須誤報——證明上面那條情境真的分得出兩版；同時確認退路仍送得出提醒、仍 exit 0。
        text = script.read_text(encoding='utf-8')
        if text.count('parser=auto\n') != 1:
            issues.append('腳本沒有唯一的 parser=auto，退路負向測試做不了')
        else:
            legacy = tmp / 'action-rules-legacy.sh'
            legacy.write_text(text.replace('parser=auto\n', 'parser=off\n'), encoding='utf-8', newline='')
            for payload, want in ((OUTPUT_ONLY_PUSH, True),
                                  ({'tool_name': 'Bash', 'tool_input': {'command': 'git push'}}, True),
                                  ({'tool_name': 'Bash', 'tool_input': {'command': 'git push --dry-run'},
                                    'tool_response': {'stdout': 'x'}}, True),
                                  ({'tool_name': 'Bash', 'tool_input': {'command': 'echo push'}}, False)):
                r = run([bash, str(legacy), 'post'], stdin=json.dumps(payload, ensure_ascii=False))
                if r.returncode or bool(r.stdout.strip()) != want:
                    issues.append('退路（原始字串比對）對 %s 的結果不符預期'
                                  % json.dumps(payload['tool_input'], ensure_ascii=False))

    # 接線守門的負向測試：每一種錯接都要被 repo_wiring_problems 看出來。
    good = {rel: (ROOT / rel).read_text(encoding='utf-8') for rel in REPO_ACTION_EVENTS}

    def wiring(edit=None, drop=()):
        base = tmp / ('action-wiring-%d' % len(list(tmp.glob('action-wiring-*'))))
        for rel, text in good.items():
            data = json.loads(text)
            if edit and rel in edit:
                edit[rel](data)
            (base / rel).parent.mkdir(parents=True, exist_ok=True)
            (base / rel).write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        for rel in (REPO_START_HOOK, REPO_ACTION_HOOK):
            if rel not in drop:
                (base / rel).parent.mkdir(parents=True, exist_ok=True)
                (base / rel).write_text('#!/bin/sh\n', encoding='utf-8')
        return repo_wiring_problems(base)[0]

    def handler(cmd):
        return [{'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': cmd}]}]

    action_cmd = 'bash "%s" pre' % REPO_ACTION_HOOK
    if wiring():
        issues.append('現行接線複本被判有問題：' + '；'.join(wiring()))
    breakers = {
        'Codex 也接 PreToolUse': {'.codex/hooks.json': lambda d: d['hooks'].update(PreToolUse=handler(action_cmd))},
        'Claude Code 的 PreToolUse 指向別支': {'.claude/settings.json': lambda d: d['hooks'].update(PreToolUse=handler('bash other.sh'))},
        'Claude Code 多接 Stop': {'.claude/settings.json': lambda d: d['hooks'].update(Stop=handler(action_cmd))},
        'SessionStart 指向動作提醒': {'.claude/settings.json': lambda d: d['hooks'].update(SessionStart=handler(action_cmd))},
        '拿掉 SessionStart': {'.claude/settings.json': lambda d: d['hooks'].pop('SessionStart')},
    }
    for name, edit in breakers.items():
        if not wiring(edit):
            issues.append('負向測試沒擋住：' + name)
    if not wiring(drop=(REPO_ACTION_HOOK,)):
        issues.append('負向測試沒擋住：動作提醒腳本不存在')

    record('FAIL' if issues else 'OK', '動作當下送規則', '；'.join(issues) if issues else
           '實跑 %d 個情境（兩種 JSON 排版）：push 前後、改部署包、改 hook 送對應要點，其餘安靜、永遠 exit 0、'
           '不做放行／阻擋決定；只看 tool_input、不被指令輸出或引號內文字誤觸發，退回原始比對的負向測試確實誤報；接線守門 %d 個負向測試都擋住（不證明 Claude Code 放進 context 或模型照做）'
           % (len(cases) * 2, len(breakers) + 1))


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
    write_lf(probe, '#!/usr/bin/env bash\nprintf \'%s\\n\' \'' + payload + '\'\n')
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


def wiring_command(script):
    """接線裡那一串 Unix 命令的唯一來源。

    期望值有兩份就是下一個會悄悄分岔的地方——這裡同時被「Codex Windows 接線」與
    「接線 cwd 定位」兩項引用。
    """
    return 'bash "$(git rev-parse --show-cdup).claude/hooks/%s"' % script


def wiring_command_windows(script):
    r"""Windows 那一欄多一次斜線正規化：`--show-cdup` 回的是 `../`（正斜線），而
    `cmd /d /c "../.claude\hooks\codex-hook.cmd"` 會死在 `'..' is not recognized`
    （2026-11-02 實測）。`commandWindows` 由 Codex 外層的 PowerShell 執行，所以用
    得上 `-replace`。
    """
    return (r"""cmd /d /c "$((git rev-parse --show-cdup) -replace '/','\')"""
            + r""".claude\hooks\codex-hook.cmd" """ + script)


def codex_wiring_problems(cfg, scripts):
    problems = []
    for event, script in scripts.items():
        hooks = [h for g in cfg.get('hooks', {}).get(event, []) for h in g.get('hooks', [])
                 if script in h.get('command', '')]
        if len(hooks) != 1:
            problems.append('%s 的 %s 接線不是一份' % (event, script))
            continue
        h = hooks[0]
        if h.get('command') != wiring_command(script):
            problems.append('%s 的 Unix 接線改變了' % event)
        windows = wiring_command_windows(script)
        if event == 'PreToolUse':
            windows += '; exit $LASTEXITCODE'
        if h.get('commandWindows') != windows:
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
    preview = sp.sync(project, dest, codex_only=True)
    if preview.changed != 2 or preview.errors or (project / sp.CODEX_LAUNCHER).exists():
        bad.append('Codex 限定預演沒有列出兩項，或竟然寫檔')
    plan = sp.sync(project, dest, codex_only=True)
    changed = len(sp.apply_plan(plan)[0])
    got = json.loads(wiring.read_text(encoding='utf-8'))
    if changed != 2 or codex_wiring_problems(got, scripts):
        bad.append('舊專案沒同時升級接線與新增啟動器')
    if skill.read_text(encoding='utf-8') != 'project skill must stay untouched':
        bad.append('Codex 限定同步竟改了 SKILL.md')
    if not any(h.get('command') == 'project-own' for g in got['hooks']['SessionStart'] for h in g['hooks']):
        bad.append('Codex 同步洗掉專案自己的 hook')
    if sp.sync(project, dest, codex_only=True).changed != 0:
        bad.append('Codex 限定同步重跑仍改檔')
    absent = tmp / 'codex-absent'
    absent.mkdir()
    if sp.sync(absent, dest, codex_only=True).changed or list(absent.iterdir()):
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
    write_lf(fixture / 'probe.sh',
             '#!/usr/bin/env bash\nIFS= read -r payload\nprintf "[git-check] %s\\n" "$payload"\n'
             'printf "err:%s\\n" "$payload" >&2\nexit 2\n')
    command = '"%s" /d /s /c ""%s" probe.sh"' % (os.environ['COMSPEC'], shim)
    r = run(command, cwd=tmp, stdin='stdin-survives\n')
    if (r.returncode != 2 or r.stdout.strip() != 'Git status check:\n[git-check] stdin-survives'
            or r.stderr.strip() != 'err:stdin-survives'):
        record('FAIL', 'Codex Windows 啟動器',
               '空白／中文路徑、不同 cwd、stdin 或 exit 2 沒保留：%r' % ((r.returncode, r.stdout, r.stderr),))
        return False
    # Codex 的 Windows hook 外面還有 PowerShell -Command；只測 cmd 會漏掉 2 被折成 1。
    powershell = shutil.which('powershell') or shutil.which('pwsh')
    if not powershell:
        record('SKIP', 'Codex Windows 結束碼', '找不到 PowerShell，無法驗完整啟動鏈')
        return None
    ps_command = cfg['hooks']['PreToolUse'][0]['hooks'][0]['commandWindows'].replace(
        'pre-push-handoff.sh', 'probe.sh')
    ps = run([powershell, '-NoProfile', '-NonInteractive', '-Command', ps_command],
             cwd=fixture.parents[1], stdin='stdin-survives\n')
    old_ps = run([powershell, '-NoProfile', '-NonInteractive', '-Command',
                  ps_command.replace('; exit $LASTEXITCODE', '')],
                 cwd=fixture.parents[1], stdin='stdin-survives\n')
    if ps.returncode != 2 or old_ps.returncode != 1:
        record('FAIL', 'Codex Windows 結束碼',
               'PowerShell 完整啟動鏈應回 2、拿掉明確 exit 應回 1，實得 %s／%s'
               % (ps.returncode, old_ps.returncode))
        return False
    record('OK', 'Codex Windows 結束碼',
           'PowerShell → cmd → Git Bash 保留 exit 2；拿掉明確 exit 的負向測試重現 exit 1')
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
    write_lf(missing, '@echo off\nset "ProgramFiles=%~dp0missing"\n'
             'set "ProgramFiles(x86)=%~dp0missing"\n'
             'set "LOCALAPPDATA=%~dp0missing"\n'
             'call "%~dp0codex-hook.cmd" probe.sh\nexit /b %ERRORLEVEL%\n', encoding='ascii')
    missing_command = '"%s" /d /s /c ""%s""' % (os.environ['COMSPEC'], missing)
    env = dict(os.environ, PATH=os.environ['SystemRoot'] + '\\System32')
    r = run(missing_command, cwd=tmp, env=env, stdin='no-git\n')
    if r.returncode != 1 or 'Git Bash not found' not in r.stderr:
        record('FAIL', 'Codex Windows 啟動器', '找不到 Git Bash 時沒明確失敗：%r' % ((r.returncode, r.stderr),))
        return False
    record('OK', 'Codex Windows 啟動器',
           '原生 cmd 實跑：中文／空白路徑、不同 cwd、純文字標頭、stdin／輸出內容／stderr／exit 2 保留；缺 Git Bash 明確 exit 1')
    return True


def step_wiring_cwd(dest, tmp):
    """接線必須從子目錄也找得到腳本（2026-11-02，查核報告 F05）。

    hook 的 `command` 以 **session 的 cwd** 執行（Claude Code：handler「runs in the current
    directory」；Codex 官方文件同樣明寫，並直接建議改從 Git root 解析 repo hook），而人會
    從子目錄開 session——`cd tools && claude`。舊接線寫成 `bash .claude/hooks/git-freshness.sh`，
    那時候是 exit 127、No such file，而 **SessionStart 失敗跟「檢查過了沒事」在畫面上一模
    一樣**：落後的本機、別台機器的「工作中」標記、骨架落後提醒三件事同時無聲消失。

    所以這一項跑的是**接線 JSON 裡原始的那一串命令**，不是直接拿完整路徑跑腳本——後者在
    任何 cwd 都會過，測不到入口（那正是查核報告的驗收條件）。fixture 的路徑同時含空白與
    中文；版本偵測關掉，這一項不打網路。
    """
    files = {
        '骨架 .claude/settings.json': dest / '.claude/settings.json',
        '骨架 .codex/hooks.json': dest / '.codex/hooks.json',
        '本 repo .claude/settings.json': ROOT / '.claude/settings.json',
        '本 repo .codex/hooks.json': ROOT / '.codex/hooks.json',
    }
    bad = []
    for name, path in files.items():
        if not path.exists():
            bad.append('%s 不存在' % name)
            continue
        cfg = json.loads(path.read_text(encoding='utf-8'))
        for groups in cfg.get('hooks', {}).values():
            for group in groups:
                for h in group.get('hooks', []):
                    for key in ('command', 'commandWindows'):
                        cmd = h.get(key)
                        if cmd and 'rev-parse --show-cdup' not in cmd:
                            bad.append('%s 的 %s 沒從 Git root 定位：%s' % (name, key, cmd))
    if bad:
        record('FAIL', '接線 cwd 定位', '；'.join(bad))
        return False

    bash = find_bash()
    if not bash:
        record('SKIP', '接線 cwd 定位', '四份接線的文字檢查過了，但找不到看得懂 Windows 路徑的 bash，沒實跑')
        return None

    origin = tmp / 'cwd-origin.git'
    work = tmp / '我的 專案 cwd'
    run(['git', 'init', '-q', '--bare', str(origin)])
    shutil.copytree(dest, work, ignore=shutil.ignore_patterns('.git'))
    git(['init', '-q', '-b', 'main'], work)
    git(['add', '-A'], work)
    git(['commit', '-qm', 'init'], work)
    git(['remote', 'add', 'origin', str(origin)], work)
    git(['push', '-q', '-u', 'origin', 'main'], work)
    # 未推送、而且沒動 HANDOFF 的 commit：pre-push 防呆該回 2。拿 exit 2 當「腳本真的跑到了」
    # 的證據，比只看 exit 0 強——後者連「什麼都沒發生」都會過。
    with (work / 'README.md').open('a', encoding='utf-8', newline='') as fh:
        fh.write('\n驗證用改動\n')
    git(['commit', '-qam', 'docs: touch'], work)

    cfg = json.loads((work / '.codex/hooks.json').read_text(encoding='utf-8'))
    handler = {e: [h for g in groups for h in g['hooks']][0]
               for e, groups in cfg['hooks'].items()}
    env = dict(GIT_ENV, BOOTSTRAP_VERSION_CHECK='off')
    push = '{"tool_input":{"command":"git push origin main"}}'
    cases = []

    def check(name, ok, got):
        cases.append((name, ok, got))

    for sub in ('.', 'tools', 'docs/ai-notes'):
        cwd = work if sub == '.' else work / sub
        r = run([bash, '-c', handler['SessionStart']['command']], cwd=cwd, stdin='{}', env=env)
        check('%s 開場檢查' % sub, r.returncode == 0 and '[git-check]' in r.stdout,
              (r.returncode, r.stdout[:100], r.stderr[:100]))
        r = run([bash, '-c', handler['PreToolUse']['command']], cwd=cwd, stdin=push, env=env)
        check('%s push 防呆' % sub, r.returncode == 2, (r.returncode, r.stderr[:100]))

    # 負向①：舊形式從子目錄必須失敗，否則這一項根本沒在量東西。
    r = run([bash, '-c', 'bash .claude/hooks/git-freshness.sh'],
            cwd=work / 'tools', stdin='{}', env=env)
    check('舊形式從子目錄→失敗（負向）', r.returncode != 0 and '[git-check]' not in r.stdout,
          (r.returncode, r.stdout[:80]))

    if os.name == 'nt':
        powershell = shutil.which('powershell') or shutil.which('pwsh')
        if powershell:
            win = handler['SessionStart']['commandWindows']
            r = run([powershell, '-NoProfile', '-NonInteractive', '-Command', win],
                    cwd=work / 'tools', stdin='{}', env=env)
            check('Windows 啟動鏈從子目錄', r.returncode == 0 and '[git-check]' in r.stdout,
                  (r.returncode, r.stdout[:100], r.stderr[:100]))
            # 負向②：拿掉斜線正規化就會變成 `../.claude\...`，cmd 吃不下混合斜線。
            naive = win.replace("$((git rev-parse --show-cdup) -replace '/','\\')",
                                '$(git rev-parse --show-cdup)')
            if naive == win:
                check('混合斜線負向測試改到了命令', False, naive)
            else:
                r = run([powershell, '-NoProfile', '-NonInteractive', '-Command', naive],
                        cwd=work / 'tools', stdin='{}', env=env)
                check('混合斜線從子目錄→失敗（負向）',
                      r.returncode != 0 and '[git-check]' not in r.stdout,
                      (r.returncode, r.stdout[:80]))
        else:
            cases.append(('Windows 啟動鏈', None, '找不到 PowerShell'))

    failed = ['%s：實得 %r' % (n, got) for n, ok, got in cases if ok is False]
    if failed:
        record('FAIL', '接線 cwd 定位', '；'.join(failed))
        return False
    skipped = [n for n, ok, _ in cases if ok is None]
    done = '、'.join(n for n, ok, _ in cases if ok)
    if skipped:
        record('SKIP', '接線 cwd 定位', '%s；跳過：%s' % (done, '、'.join(skipped)))
        return None
    record('OK', '接線 cwd 定位', done)
    return True


def fixture_origin(project, claim=False):
    """本機 bare remote，讓同步測試遵守真實 A1／A5 前提。"""
    def must(args):
        r = git(args, project)
        if r.returncode:
            raise RuntimeError('fixture origin: ' + r.stderr)
    remote = project.parent / (project.name + '-origin.git')
    must(['init', '--bare', '-q', str(remote)])
    must(['remote', 'add', 'origin', str(remote)])
    must(['push', '-qu', 'origin', 'HEAD'])
    owner = '`fixture-machine` ／ `Codex CLI` ／ `fixture-session`，2026-11-03 開工'
    if claim:
        write_lf(project / 'HANDOFF.md', '- **工作中**：' + owner + '\n')
        must(['add', 'HANDOFF.md'])
        must(['commit', '-qm', 'A5 claim'])
        must(['push', '-q', 'origin', 'HEAD'])
    return owner


def wiring_preservation_problems(sp):
    """R01／R02：保存內容與觸發條件，不能只靠成功退出推定。"""
    own = {'type': 'command', 'command': 'bash .claude/hooks/pre-push-handoff.sh'}
    auth_group = {'matcher': 'Bash|PowerShell', 'hooks': [dict(own, timeout=30)]}
    auth = json.dumps({'hooks': {'PreToolUse': [auth_group]}})
    bad = []
    commands = [
        'python audit_hook.py --watch git-freshness.sh',
        'echo pre-push-handoff.sh',
        'bash project/pre-push-handoff.sh',
        own['command'] + ' && echo project-audit',
    ]
    for field in ('command', 'commandWindows'):
        for command in commands:
            custom = {'type': 'command', field: command}
            group = dict(auth_group, hooks=[own, custom])
            cur = json.dumps({'hooks': {'PreToolUse': [group]}})
            new, _, err = sp.merge_wiring(auth, cur)
            if not err or new is not None or sp.handler_scripts(custom):
                bad.append('R01 未拒絕不明命令：' + field + ' ' + command)
    # 任一命令欄不明，就不能認領整個雙平台 handler。
    mixed = dict(own, commandWindows='echo pre-push-handoff.sh')
    if sp.handler_scripts(mixed):
        bad.append('R01 雙平台命令只認得一欄仍被認領')
    for matcher in (None, '', '*', 'Bash', 'Bash|PowerShell'):
        group = {'hooks': [own, {'type': 'command', 'command': 'echo all-tools-audit'}]}
        if matcher is not None:
            group['matcher'] = matcher
        cur = json.dumps({'hooks': {'PreToolUse': [group]}})
        new, _, err = sp.merge_wiring(auth, cur)
        if matcher != 'Bash|PowerShell':
            if not err or new is not None:
                bad.append('R02 matcher 語意被改：' + repr(matcher))
        elif err or not new or json.loads(new)['hooks']['PreToolUse'][0]['hooks'][-1] != group['hooks'][-1]:
            bad.append('R02 一致 matcher 的自訂 handler 沒保留')
    for side in ('current', 'authority'):
        cur_group = dict(auth_group, hooks=[own, {'type': 'command', 'command': 'echo custom'}])
        ag = dict(auth_group)
        (cur_group if side == 'current' else ag)['extra-setting'] = True
        if not sp.merge_wiring(json.dumps({'hooks': {'PreToolUse': [ag]}}),
                               json.dumps({'hooks': {'PreToolUse': [cur_group]}}))[2]:
            bad.append('R02 組層欄位變動未拒絕：' + side)
    return bad


def step_sync_safety(tmp):
    """同步器的資料保全與失敗訊號（2026-11-02，查核報告 F02／F03）。

    F02：骨架擁有的是**指向骨架腳本的 handler**，不是含它的整組。舊版 `cur[at] =
    deepcopy(g)` 把整組當成骨架的，所以專案把自己的 hook 加在同一組裡（`hooks` 陣列
    本來就放得下多個，完全合法）就會被靜默刪掉——而輸出還寫著「專案其他設定原樣保留」。
    既有的「接線合併」把專案 hook 放在**另一組**，所以一直沒碰到這個形狀；這裡補的就是
    同一組的那幾種。

    F03：先算完整個計畫、驗完才寫。舊版邊算邊寫且 `WHOLE` 那圈在 JSON 驗證之前，於是
    一份壞掉的接線會在覆蓋掉好幾個檔之後才被發現；而 FAIL 只進訊息列、不影響結束碼，
    所以同步失敗一半照樣 exit 0，最後還印「全部都已經是 v…」。這裡釘的是
    「任一檔算不出來→零寫入」與「任何目標沒完成→非零退出」。
    """
    import sync_project as sp
    bad = wiring_preservation_problems(sp)
    # 負向測試恢復兩種舊判準；同一套行為斷言必須能抓到缺口。
    import types
    source = read_lf(ROOT / 'tools/sync_project.py')
    start = source.index('def handler_scripts(')
    end = source.index('\n\ndef scripts_in(', start)
    old_handler = '''def handler_scripts(handler):
    cmd = '%s %s' % (handler.get('command', ''), handler.get('commandWindows', ''))
    return frozenset(s for s in OWNED_SCRIPTS if s in cmd)
'''
    mutants = [source[:start] + old_handler + source[end:],
               source.replace('if meta_now.get(k) != meta_auth.get(k)',
                              'if k in meta_now and k in meta_auth and meta_now[k] != meta_auth[k]')]
    for i, text in enumerate(mutants):
        mutant = types.ModuleType('sync_mutant')
        mutant.__file__ = str(ROOT / 'tools/sync_project.py')
        exec(compile(text, mutant.__file__, 'exec'), mutant.__dict__)
        if not wiring_preservation_problems(mutant):
            bad.append('R01／R02 負向測試沒抓到舊判準 ' + str(i))

    def J(o):
        return json.dumps(o, ensure_ascii=False, indent=2)

    own = {'type': 'command', 'command': 'bash .claude/hooks/pre-push-handoff.sh'}
    mine = {'type': 'command', 'command': 'echo project-own'}
    auth = J({'hooks': {'PreToolUse': [{'matcher': 'Bash|PowerShell',
                                        'hooks': [dict(own, timeout=30)]}]}})

    # ① 同一組裡有專案自己的 handler，而骨架 handler 要更新 → 兩者都要在
    cur = J({'hooks': {'PreToolUse': [{'matcher': 'Bash|PowerShell',
                                       'hooks': [dict(own, timeout=10), mine]}]}})
    new, _, err = sp.merge_wiring(auth, cur)
    if err or new is None:
        bad.append('同組自訂 hook：%s' % (err or '沒認出骨架 handler 要更新'))
    else:
        hs = json.loads(new)['hooks']['PreToolUse'][0]['hooks']
        if not any(h.get('command') == 'echo project-own' for h in hs):
            bad.append('同組自訂 hook 被刪掉了（F02 的原始缺陷）')
        if not any(h.get('timeout') == 30 for h in hs):
            bad.append('同組的骨架 handler 沒更新成權威版')

    # ② 同一組裡有專案 handler，而權威版要改這一組的 matcher → 拒絕並說出新舊值，
    #    不要靜默把專案那個 handler 的觸發條件一起換掉
    stale = J({'hooks': {'PreToolUse': [{'matcher': 'Bash',
                                         'hooks': [dict(own, timeout=30), mine]}]}})
    new, _, err = sp.merge_wiring(auth, stale)
    if not err or new is not None:
        bad.append('matcher 衝突沒被拒絕——專案 handler 的觸發條件會被悄悄換掉')
    elif 'Bash|PowerShell' not in err or 'matcher' not in err:
        bad.append('matcher 衝突的訊息沒說出要改什麼（看不出該怎麼手動處理）')

    # ③ 專案有兩組都指向同一支骨架腳本 → 不敢猜要更新哪一組
    dup = J({'hooks': {'PreToolUse': [{'matcher': 'Bash', 'hooks': [own]},
                                      {'matcher': 'Bash', 'hooks': [own]}]}})
    if sp.merge_wiring(auth, dup)[2] is None:
        bad.append('重複的骨架組沒被拒絕')

    # ④ 分組方式跟權威版不同（兩支腳本擠在一組）→ 拒絕，不要在後面另外補一組，
    #    否則同一支腳本掛兩次：開場印兩遍、防呆跑兩次
    other = {'type': 'command', 'command': 'bash .claude/hooks/git-freshness.sh'}
    lumped = J({'hooks': {'PreToolUse': [{'matcher': 'Bash', 'hooks': [own, other]}]}})
    merged, _, err = sp.merge_wiring(auth, lumped)
    if err is None:
        hs = json.loads(merged)['hooks']['PreToolUse'] if merged else []
        n = sum('pre-push-handoff.sh' in h.get('command', '')
                for g in hs for h in g.get('hooks', []))
        bad.append('分組方式不同卻照樣合併了（骨架腳本出現 %d 次）' % n)

    # ⑤ 只有 commandWindows 的 handler 也要算成骨架的（Codex 的 Windows 接線就是這形狀）
    if 'pre-push-handoff.sh' not in sp.handler_scripts(
            {'type': 'command', 'commandWindows':
             'cmd /d /c "$((git rev-parse --show-cdup) -replace \'/\',\'\\\').claude\\hooks\\codex-hook.cmd" pre-push-handoff.sh; exit $LASTEXITCODE'}):
        bad.append('只有 commandWindows 的 handler 沒被認成骨架的')

    # ── F03：拿一個最小假專案跑真的 CLI
    proj = tmp / 'sync-safety' / 'proj'
    (proj / '.claude' / 'skills' / 'handoff').mkdir(parents=True)
    skill = proj / '.claude' / 'skills' / 'handoff' / 'SKILL.md'
    write_lf(skill, 'stale skill')
    wiring = proj / '.claude' / 'settings.json'
    write_lf(wiring, '{ not json')
    write_lf(proj / 'HANDOFF.md', sp.BUSY_FIELD + '\n')
    for args in (['init', '-q', '-b', 'main'], ['add', '.'], ['commit', '-qm', 'fixture']):
        if git(args, proj).returncode:
            raise RuntimeError('同步安全 Git fixture 建立失敗')
    owner = fixture_origin(proj, claim=True)

    def cli(*args):
        extra = ['--owner', owner] if str(proj) in args else []
        return run([sys.executable, '-X', 'utf8', 'tools/sync_project.py'] + list(args) + extra,
                   cwd=ROOT)

    for group in (
        {'matcher': 'Bash|PowerShell', 'hooks': [own, {'type': 'command',
          'command': 'python audit_hook.py --watch git-freshness.sh'}]},
        {'hooks': [own, mine]},
    ):
        text = J({'hooks': {'PreToolUse': [group]}})
        write_lf(wiring, text)
        r = cli(str(proj), '--write', '--allow-dirty', '--accept-drift', '.claude/skills/handoff/SKILL.md')
        if r.returncode == 0 or read_lf(wiring) != text or read_lf(skill) != 'stale skill':
            bad.append('R01／R02 CLI 未拒絕或未維持零寫入')
    write_lf(wiring, '{ not json')

    r = cli(str(proj), '--write', '--allow-dirty', '--accept-drift', '.claude/skills/handoff/SKILL.md')
    if r.returncode == 0:
        bad.append('壞 JSON 的目標竟然 exit 0（F03 的原始缺陷）')
    if skill.read_text(encoding='utf-8') != 'stale skill':
        bad.append('算不出來卻已經寫了別的檔——preflight 沒有擋住部分寫入')
    if '全部都已經是' in r.stdout:
        bad.append('失敗卻宣稱「全部都已經是最新版」')

    r = cli(str(tmp / 'sync-safety' / 'absent'))
    if r.returncode == 0 or '全部都已經是' in r.stdout:
        bad.append('不存在的目標竟然 exit 0 或宣稱最新版')

    # 修好之後要真的寫得進去、而且 exit 0——修法不能嚴到什麼都不敢改
    write_lf(wiring, '{"hooks":{}}')
    r = cli(str(proj), '--write', '--allow-dirty', '--accept-drift', '.claude/skills/handoff/SKILL.md')
    if r.returncode != 0 or skill.read_text(encoding='utf-8') == 'stale skill':
        bad.append('正常的目標沒同步成功（exit %d）' % r.returncode)
    r = cli(str(proj), '--allow-dirty')
    if r.returncode != 0 or '全部都已經是' not in r.stdout:
        bad.append('重跑沒有回到「全部都已經是」且 exit 0')

    if bad:
        record('FAIL', '同步安全', '；'.join(bad))
        return False
    record('OK', '同步安全',
           'handler 層所有權：同組自訂 hook 保留、matcher 衝突與重複／異常分組拒絕、'
           'commandWindows 認得出來；R01／R02 命令所有權與缺省 matcher 組合、兩個負向變異通過；preflight：壞 JSON 零寫入、失敗非零退出、'
           '修好後照樣同步得動')
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

# ── Python 版本下限（F14）────────────────────────────────────────────────
# 這張表只收「寫得出來、但舊版 python 沒有」的 API。每一條都要註明需要的版本，因為
# 這一項報錯時要能直接回答「那我最低要幾」——只說「不要用」會逼下一棒去翻官方文件。
PY_FEATURES = (
    (re.compile(r'read_text\([^)]*newline'), (3, 13), "Path.read_text 的 newline 參數"),
    (re.compile(r'write_text\([^)]*newline'), (3, 10), "Path.write_text 的 newline 參數"),
    (re.compile(r'\.(?:removeprefix|removesuffix)\('), (3, 9), 'str.removeprefix／removesuffix'),
    (re.compile(r'\.is_relative_to\('), (3, 9), 'Path.is_relative_to'),
    (re.compile(r'functools\.cache\b'), (3, 9), 'functools.cache'),
    (re.compile(r'^\s*match\s+[^\n]+:\s*$', re.M), (3, 10), 'match 語句'),
    (re.compile(r'zip\([^)]*strict='), (3, 10), 'zip(strict=)'),
    (re.compile(r'\btomllib\b'), (3, 11), 'tomllib'),
    (re.compile(r'datetime\.UTC\b'), (3, 11), 'datetime.UTC'),
    (re.compile(r'\bdirs_exist_ok='), (3, 8), 'shutil.copytree(dirs_exist_ok=)'),
)


def code_only(text):
    """把註解與字串塗成空白後的原始碼（位置保留，所以正規表示式還是對得上行）。

    為什麼非去不可：這一項掃的是「有沒有用到比下限新的 API」，而那些 API 的名字在
    **解釋為什麼不要用它**的註解與 docstring 裡一定會出現——`read_lf` 的 docstring 就
    寫著 `Path.read_text(..., newline='')`。掃全檔會把說明判成用法，於是正確的修法反而
    FAIL，而那種假陽性會逼下一棒把理由刪掉，正好砍掉鐵律 3 要保的東西。
    """
    lines = text.split('\n')
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text  # 壞檔讓語法本身去報；這裡寧可多掃，不要少掃
    for tok in toks:
        if tok.type not in (tokenize.COMMENT, tokenize.STRING):
            continue
        (sr, sc), (er, ec) = tok.start, tok.end
        for r in range(sr - 1, min(er, len(lines))):
            line = lines[r]
            a = sc if r == sr - 1 else 0
            b = ec if r == er - 1 else len(line)
            lines[r] = line[:a] + ' ' * max(0, b - a) + line[b:]
    return '\n'.join(lines)


def py_floor_problems(sources, floor):
    """sources：{標籤: 原始碼}。回傳問題清單（空＝沒有用到高於 floor 的 API）。"""
    problems = []
    for label in sorted(sources):
        code = code_only(sources[label])
        for pat, need, what in PY_FEATURES:
            if need > floor and pat.search(code):
                problems.append('%s 用了 %s：要 Python %d.%d，宣告的下限是 %d.%d'
                                % ((label, what) + need + floor))
    return problems


def step_python_floor(dest):
    """宣告 Python 版本下限，並守住「沒有人順手用了更新的 API」。

    2026-11-02 加（查核報告 F14）。起因：`verify_bootstrap.py` 用 `Path.read_text(
    ..., newline='')`，而那個參數官方標「Changed in 3.13」——文件卻只說「`python` 不存在
    就用 `python3`」。**失敗的形狀是最壞的那一種**：舊版不會在啟動時說「版本太舊」，而是
    執行到那一行才炸成 TypeError，沒人會把它聯想到版本。

    守三件事：①兩支維護工具檔頭都有 `MIN_PY` 守門、而且兩邊同號（同一個事實兩個家，所以
    要釘住）；②部署後兩支腳本的下限有寫在 `README.md` 範本——那是**人的入口**，而部署出去
    的專案看不到這個 repo 的驗證器；③四支 .py 都沒有用到高於下限的 API。

    天花板要講明白：**下限是「不使用更新的 API」的靜態擔保，不是「在那個版本上跑過」。**
    這台機器只有 3.13，沒有舊版可測；要把它變成實測，得先有 CI（查核報告第 6 節）。
    部署後那兩支**刻意不加 `MIN_PY` 守門**：`tools/check_docs.py` 是 `sync_project.py` 的
    同步對象，動它就得跳 `source:` 標記、再把六個專案同步一輪，而 `VERSION` 不跟著動
    （鐵律 1），於是落後偵測不會替你講——為了一個「本來就跑得動」的版本宣告製造一筆無聲的
    同步債並不划算。它們的保障是這一項的靜態掃描。
    """
    maint = {}
    for rel in ('tools/verify_bootstrap.py', 'tools/sync_project.py'):
        maint[rel] = read_lf(ROOT / rel)
    problems, floors = [], {}
    for rel, text in maint.items():
        m = re.search(r'^MIN_PY = \((\d+), (\d+)\)$', text, re.M)
        if not m:
            problems.append('%s 檔頭沒有 `MIN_PY = (x, y)`——沒有宣告就沒有下限' % rel)
            continue
        floors[rel] = (int(m.group(1)), int(m.group(2)))
        if 'if sys.version_info < MIN_PY' not in text or '需要 Python' not in text:
            problems.append('%s 宣告了 MIN_PY 卻沒有在檔頭擋下舊版並清楚報錯' % rel)
    if len(set(floors.values())) > 1:
        problems.append('兩支維護工具的 MIN_PY 不一致：%s' % floors)
    if problems:
        record('FAIL', 'Python 版本下限', '；'.join(problems))
        return False

    floor = sorted(floors.values())[0]
    want = '需要 Python %d.%d 以上' % floor
    if want not in read_lf(dest / 'README.md'):
        record('FAIL', 'Python 版本下限',
               'README.md 範本沒有寫「%s」——部署出去的專案看不到這個 repo 的驗證器' % want)
        return False

    sources = dict(maint)
    for rel in ('tools/check_docs.py', 'tools/verify_state.py'):
        sources['骨架 ' + rel] = read_lf(dest / rel)
    problems = py_floor_problems(sources, floor)
    if problems:
        record('FAIL', 'Python 版本下限', '；'.join(problems))
        return False

    # 負向測試：掃描器要真的掃得到，而且不能把「解釋為什麼不要用」判成用法。
    cases = (
        ('3.13 的 read_text(newline=)', "s = p.read_text(encoding='utf-8', newline='')\n"),
        ('3.10 的 write_text(newline=)', "p.write_text(s, encoding='utf-8', newline='')\n"),
        ('3.9 的 removeprefix', "s = s.removeprefix('a')\n"),
        ('3.11 的 tomllib', 'import tomllib\n'),
    )
    missed = [name for name, src in cases if not py_floor_problems({'x.py': src}, floor)]
    excuse = ('"""不要改回 Path.read_text(..., newline=\'\') ——那要 3.13。"""\n'
              '# 也不要 p.write_text(s, newline="")\n')
    if py_floor_problems({'x.py': excuse}, floor):
        missed.append('把註解／docstring 裡的說明判成用法')
    if missed:
        record('FAIL', 'Python 版本下限', '負向測試沒排到：%s' % '、'.join(missed))
        return False

    record('OK', 'Python 版本下限',
           '兩支維護工具都有 MIN_PY=%d.%d 守門且同號、README 範本寫出下限、四支 .py 沒有'
           '用到更新的 API；%d 個負向測試＋1 個反向保險通過（下限是靜態擔保，不是實跑過）'
           % (floor + (len(cases),)))
    return True


# ── 已修正的主張不得在別處復活（F15）──────────────────────────────────────
# 這裡刻意**不是**一張「禁句表」：查核報告 F15 的改善建議明寫「不要只增加特定舊句的禁止
# regex，因為新的措辭會再次繞過」。所以每一項都綁在一個**結構**上——能力表的那一格、
# skill 的字母對應、同一條規則的單一定義——句子怎麼改寫都還是得跟那個結構對得起來。
CLAIM_SERIAL = '當天第幾個帶 `source:` 標記的改動'
CLAIM_STALE_SERIAL = '部署包當天的第幾次修改'
# 否認句要**跟工具名相鄰**才算在講那個工具：`AGENTS.md` 有一行同時提到 Codex 與「沒有全域
# 副本、或工具不會自動載入 skill」，那是在講這個 repo 少一個檔，不是在講 Codex 少一層機制。
# 兩件事同形，只靠「同一行」分不開（加這一項的當下就誤判到）。
CLAIM_DENY = r'%s[^。\n]{0,20}(?:沒有|不支援)[^。\n]{0,16}skill'
CLAIM_QUOTE = re.compile(r'「[^」]*」')


def claim_text(line):
    """把「」裡的內容拿掉之後的那一行——引用不算主張。

    鐵律 3 要求保留每條規則的「為什麼」，而「為什麼」幾乎一定要引用被改掉的舊說法
    （「舊版寫『有憑證就跑』」）。不區分引用與主張的話，守門人就會逼下一棒把理由刪掉，
    正好砍掉這份骨架最值錢的那一半。2026-11-02 加這一項的當下就被自己的修正文字誤判。
    """
    return CLAIM_QUOTE.sub('', line)


def claim_problems(docs):
    """docs：{'kit', 'readme', 'dep_readme', 'dep_protocol', 'agents'} → 問題清單。"""
    problems = []

    # ① 散文不得否認能力表裡已經 ✅ 的工具（2026-11-02 之前 README 範本還寫著
    #    「其他工具（Gemini／Codex）沒有 skill 機制」，而那一格 2026-10-30 就實測成 ✅）。
    cols, rows = tool_matrix(tool_section(docs['kit']))
    if not rows.get('自動載入程序檔'):
        problems.append('部署包能力表找不到「自動載入程序檔」那一列，這一項無從判斷')
    else:
        yes = set()
        for col, verdict in zip(cols, rows['自動載入程序檔']):
            if verdict == '✅':
                yes.add(col.replace(' CLI', '').replace(' 桌面 App', '').strip())
        for name in sorted(docs):
            for line in docs[name].split('\n'):
                bare = claim_text(line)
                for tool in sorted(yes):
                    for hit in re.finditer(CLAIM_DENY % re.escape(tool), bare):
                        # 「…沒有 handoff skill」講的是少一個檔，不是少一層機制。例外只能
                        # 看**命中的那一段**：2026-11-02 第一版寫成「整行含 handoff skill
                        # 就放行」，而要擋的那一句所在的那一行開頭正好是「程序已經寫成
                        # **[handoff skill](…)**」——例外把唯一的目標吃掉了，而畫面上是 ok。
                        if 'handoff skill' in hit.group(0):
                            continue
                        problems.append('%s 有一句說「%s 沒有 skill」，但能力表那一格是 ✅：%s'
                                        % (name, tool, hit.group(0)[:40]))

    # ② 交接 prompt 不得有自己的字母編號（舊版 A＝交棒、B＝接棒，跟 skill 正好相反），
    #    而且每一段都要寫出它要跑的模式。
    if '**A 接棒**' not in docs['kit'] or '**B 交棒**' not in docs['kit']:
        problems.append('部署包的 skill 模式表沒有「**A 接棒**／**B 交棒**」，字母對應無從比對')
    sec = docs['dep_readme']
    i = sec.find('## 換一個 AI 接手工作')
    sec = sec[i:sec.find('\n## ', i + 3)] if i >= 0 else ''
    if not sec:
        problems.append('README 範本找不到「## 換一個 AI 接手工作」那一節')
    else:
        if re.search(r'^### *[AB] *[.．、]', sec, re.M):
            problems.append('交接 prompt 又長出自己的 A／B 編號——字母只留 skill 那一套')
        for word, mode in (('交棒', 'B 模式'), ('接棒', 'A 模式')):
            heads = [l for l in sec.split('\n') if l.startswith('### ') and word in l]
            if not heads:
                problems.append('README 範本沒有「%s」那一段 prompt' % word)
            elif not any(mode in h for h in heads):
                problems.append('「%s」那段 prompt 的標題沒寫出它跑 skill 的 %s' % (word, mode))

    # ③ verify_state 不得被「有憑證」這個不相干的前提擋掉。
    for name in sorted(docs):
        for line in docs[name].split('\n'):
            if 'verify_state' in line and re.search(r'有憑證(?:才|就)', claim_text(line)):
                problems.append('%s 把 verify_state 寫成有憑證才跑：%s'
                                % (name, line.strip()[:50]))
    if '一律跑' not in docs['dep_protocol']:
        problems.append('協定範本的一鍵驗證沒有寫「一律跑」')

    # ④ 版本序號只有一種算法，而且要講明它跟版本行不保證同號。
    for name in ('kit', 'agents'):
        if CLAIM_SERIAL not in docs[name]:
            problems.append('%s 沒有把序號規則寫成「%s」' % (name, CLAIM_SERIAL))
        if '不保證同號' not in docs[name]:
            problems.append('%s 沒有講明序號跟版本行不保證同號' % name)
    for name in sorted(docs):
        for line in docs[name].split('\n'):
            if CLAIM_STALE_SERIAL in claim_text(line):
                problems.append('%s 還在用舊的序號算法（只有引用舊版時才能出現）：%s'
                                % (name, line.strip()[:50]))

    # ⑤ 可攜層不得被寫成「到哪都成立」——載入、遵循、執行是三種不同的證據。
    if '載入、遵循、執行是三種不同的證據' not in docs['kit']:
        problems.append('部署包沒有把「載入／遵循／執行是三種證據」寫出來')
    for name in sorted(docs):
        for line in docs[name].split('\n'):
            if '到哪都成立' in claim_text(line):
                problems.append('%s 還在寫「可攜層到哪都成立」：%s' % (name, line.strip()[:50]))
    if '三層自動發生' in docs['readme']:
        problems.append('README 還在寫「三層自動發生」——三層壓低漏做的機會，不保證發生')
    return problems


def step_claims(dest):
    """已修正的主張不得在範本、操作卡與入口文件裡復活。

    2026-11-02 加（查核報告 F15）。那份報告點名五處：README 範本說「其他工具沒有 skill
    機制」（能力表 2026-10-30 就改成 ✅）、第 6 節的版本序號算法跟 `AGENTS.md` 鐵律 2 不同、
    協定與接棒 prompt 把 `verify_state` 寫成「有憑證才跑」（漏掉不需要憑證的本機／公開
    檢查）、README 的 prompt A／B 跟 skill 的 A／B 正好相反、以及「可攜層到哪都成立」
    「三層自動發生」這兩句過度保證。

    **為什麼不是一張禁句表**：報告的改善建議明寫「不要只增加特定舊句的禁止 regex，因為新的
    措辭會再次繞過」。所以每一項都綁在一個結構上——能力表的那一格、skill 的字母對應、
    同一條規則的單一定義、`舊版` 引用之外不得出現的舊算法。

    天花板：它守的是**可機械判定的那一面**（表格的格子、字母對應、關鍵定義是否單一），
    守不了一段敘述整體的準確度；而「舊版 …」這個例外是故意的——鐵律 3 要求保留為什麼，
    所以引用舊說法的那些行必須放行。
    """
    docs = {
        'kit': read_lf(KIT),
        'readme': read_lf(ROOT / 'README.md'),
        'agents': read_lf(ROOT / 'AGENTS.md'),
        'dep_readme': read_lf(dest / 'README.md'),
        'dep_protocol': read_lf(dest / 'docs' / 'ai-notes' / 'handover-protocol.md'),
    }
    problems = claim_problems(docs)
    if problems:
        record('FAIL', '已修正的主張沒復活', '；'.join(problems[:6]))
        return False

    # 負向測試：五項各自要擋得住一次真的退化。
    cases = (
        ('能力表 ✅ 卻說沒有 skill', 'dep_readme',
         lambda t: t.replace('## 換一個 AI 接手工作',
                             '## 換一個 AI 接手工作\n\nCodex 沒有 skill 機制。')),
        ('prompt 又長出 A／B 編號', 'dep_readme',
         lambda t: t.replace('### 收工時：', '### A. 收工時：')),
        ('prompt 標題不寫模式', 'dep_readme',
         lambda t: t.replace('（skill 的 **B 模式**）', '')),
        ('verify_state 又變成有憑證才跑', 'dep_protocol',
         lambda t: t.replace('**一律跑** `tools/verify_state.py`',
                             '有憑證才跑 `tools/verify_state.py`')),
        ('協定不寫一律跑', 'dep_protocol', lambda t: t.replace('一律跑', '跑')),
        ('序號算法退回舊版', 'agents',
         lambda t: t.replace(CLAIM_SERIAL, CLAIM_STALE_SERIAL)),
        ('不再講明跟版本行同不同號', 'kit', lambda t: t.replace('不保證同號', '一樣')),
        ('可攜層又寫成到哪都成立', 'kit',
         lambda t: t.replace('- **可攜層——不需要任何設定就讀得到**',
                             '- **可攜層——到哪都成立**')),
        ('README 又寫三層自動發生', 'readme',
         lambda t: t.replace('## 核心：交接不靠人記，靠三層把漏做的機會壓低',
                             '## 核心：交接不靠人記，靠三層自動發生')),
    )
    missed = []
    for name, key, mutate in cases:
        bad = dict(docs)
        bad[key] = mutate(docs[key])
        if bad[key] == docs[key]:
            missed.append('%s（改寫沒命中，測試本身壞了）' % name)
        elif not claim_problems(bad):
            missed.append(name)
    if missed:
        record('FAIL', '已修正的主張沒復活', '負向測試沒排到：%s' % '、'.join(missed))
        return False

    record('OK', '已修正的主張沒復活',
           '能力表與散文一致、字母只剩 skill 那一套、verify_state 不以憑證為前提、'
           '序號規則單一定義、可攜層不過度保證；%d 個負向測試通過' % len(cases))
    return True


# ── verify_state 的失敗訊號（F04）────────────────────────────────────────
# 驅動程式：把 CHECKS 從外面灌進去，不碰範本的「專案設定」區塊。用 import 而不是
# 文字替換，是因為要驗的是 main() 的**行為**（狀態分類與結束碼），不是它長什麼樣。
STATE_DRIVER = """import json
import sys
sys.path.insert(0, '.')
import verify_state as vs
cfg = json.loads(sys.argv[1])
vs.BASE = cfg.get('base', '')
vs.SECRET_FILE = cfg.get('secret_file', '.env')
vs.HTTP_CHECKS = [tuple(x) for x in cfg.get('http', [])]
vs.CMD_CHECKS = [tuple(x) for x in cfg.get('cmd', [])]
vs.OPTIONAL = tuple(cfg.get('optional', []))
sys.exit(vs.main(cfg.get('argv', [])))
"""


class _StateHandler(http.server.BaseHTTPRequestHandler):
    """/good → 200 ＋ JSON；其餘 → 500。只聽 127.0.0.1，不碰網路。"""

    def do_GET(self):
        body = b'{"status": "ok"}' if self.path == '/good' else b'boom'
        self.send_response(200 if self.path == '/good' else 500)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def step_state_exit(dest):
    """verify_state 不得把失敗吞成 exit 0（2026-11-02／查核報告 F04）。

    原始缺陷：在生成的檢查裡放一個 exit 7 的命令，畫面上印著 `=rc7`，而 `main()` 仍然
    `return 0`；HTTP 的 FAIL／ERROR 也只是印字。於是任何「跑 verify_state，exit 0 就算
    服務驗過」的下游流程都會誤過關——而這支腳本存在的理由正是「把接手查證壓成一個回合」，
    也就是說它的結束碼本來就會被當成結論用。

    九個情境全部實跑（不是讀原始碼）：rc7、HTTP 500、連不上、200 但回應內容不對、
    全綠、缺憑證（預設／`--strict`／列進 OPTIONAL）、未填 CHECKS，再加一個祕密遮罩。
    `NOT_CONFIGURED` 仍然回 0 是刻意的，所以它也在表裡——免得下一棒「順手把它也改成非零」。
    """
    work = pathlib.Path(tempfile.mkdtemp(prefix='state-exit-'))
    shutil.copyfile(dest / 'tools' / 'verify_state.py', work / 'verify_state.py')
    write_lf(work / 'driver.py', STATE_DRIVER)
    write_lf(work / 'empty.env', 'OTHER=1\n')
    write_lf(work / 'real.env', 'API_KEY=supersecretvalue\n')

    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), _StateHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:%d' % srv.server_address[1]
    leak = [sys.executable, '-c', 'print("leak " + "supersecretvalue")']
    cases = (
        ('命令非零退出', {'cmd': [['boom', [sys.executable, '-c', 'import sys; sys.exit(7)']]]},
         2, 'FAIL', None),
        ('HTTP 500', {'base': base, 'http': [['bad', '/bad', False]]}, 2, 'FAIL', None),
        ('連不上', {'http': [['down', 'http://127.0.0.1:1/', False]]}, 2, 'ERROR', None),
        ('200 但內容不對', {'base': base, 'http': [['good', '/good', False, 'absent']]},
         2, 'FAIL', None),
        ('全綠', {'base': base, 'http': [['good', '/good', False, 'ok']],
                  'cmd': [['fine', [sys.executable, '-c', 'pass']]]}, 0, 'PASS', None),
        ('缺憑證（預設）', {'base': base, 'secret_file': 'empty.env',
                            'http': [['needs', '/good', True]]}, 0, 'SKIP', None),
        ('缺憑證（--strict）', {'base': base, 'secret_file': 'empty.env', 'argv': ['--strict'],
                                'http': [['needs', '/good', True]]}, 3, 'SKIP', None),
        ('缺憑證但列進 OPTIONAL', {'base': base, 'secret_file': 'empty.env',
                                   'argv': ['--strict'], 'optional': ['needs'],
                                   'http': [['needs', '/good', True]]}, 0, 'SKIP', None),
        ('未填 CHECKS', {}, 0, 'NOT_CONFIGURED', None),
        ('祕密遮罩', {'secret_file': 'real.env', 'cmd': [['leak', leak]]},
         0, '***', 'supersecretvalue'),
    )
    # R04：跨 stdout 300／stderr 200 摘要邊界，以及換行先於遮罩的組合。
    for stream, size in (('stdout', 290), ('stderr', 190)):
        argv = [sys.executable, '-c', 'import sys; sys.%s.write("x"*%d+"supersecretvalue")' % (stream, size)]
        cases += ((stream + ' 邊界遮罩', {'secret_file': 'real.env', 'cmd': [['boundary', argv]]},
                   0, '***', 'supersecr'),)
    bad = []
    try:
        for name, cfg, want_rc, want_in, forbid in cases:
            r = run([sys.executable, '-X', 'utf8', 'driver.py', json.dumps(cfg)], cwd=work)
            if r.returncode != want_rc:
                bad.append('%s：期望 exit %d，實得 %d（%s）'
                           % (name, want_rc, r.returncode,
                              r.stdout.strip().replace('\n', ' / ')[:70] or r.stderr[:70]))
            elif want_in not in r.stdout:
                bad.append('%s：輸出裡沒有「%s」（%s）'
                           % (name, want_in, r.stdout.strip()[:70]))
            elif forbid and forbid in r.stdout:
                bad.append('%s：祕密原文出現在輸出裡' % name)
        original_script = read_lf(work / 'verify_state.py')
        old_script = original_script.replace('mask(p.stdout)', 'p.stdout').replace('mask(p.stderr)', 'p.stderr')
        write_lf(work / 'verify_state.py', old_script)
        cfg = cases[-2][1]
        r = run([sys.executable, '-X', 'utf8', 'driver.py', json.dumps(cfg)], cwd=work)
        if 'supersecr' not in r.stdout:
            bad.append('R04 負向測試沒有重現摘要邊界洩出前綴')
    finally:
        srv.shutdown()
        srv.server_close()
        shutil.rmtree(work, ignore_errors=True)
    if bad:
        record('FAIL', 'verify_state 失敗訊號', '；'.join(bad[:4]))
        return False
    record('OK', 'verify_state 失敗訊號',
           '%d 個情境實跑：非零退出與 HTTP 失敗讓結束碼非零、連不上算 ERROR、'
           '200 但內容不對也算 FAIL、缺憑證是 SKIP（--strict 才非零，OPTIONAL 放行）、'
           '未填仍回 0、祕密有遮罩' % len(cases))
    return True


# ── 交接快照檢查（F08）──────────────────────────────────────────────────
# 連結誤報的 fixture：三種「看起來像連結但不是」的寫法都不該被報成死連結。
LINK_FIXTURE = """\
# 連結誤報測試

> 最後更新：2026-11-02

圍欄裡的程式碼範例不是連結：

```python
print('[x](does-not-exist.md)')
```

行內的 `[y](also-missing.md)` 也不是。

真的連結要解析得對：[說明](README.md)、[帶 title](README.md "說明")、
[角括號](<README.md>)。
"""


def step_snapshot_guard(dest):
    """check_docs 的第 7 項：交接快照不見了必須擋下（2026-11-02／查核報告 F08）。

    原始缺陷：第 6 項（「工作中」欄位）是「HANDOFF.md 有出現在輸入清單裡才驗」，所以
    **部署後整份刪掉或改名時，它回報乾淨**——而那一刀正好把跨機器誤接棒防呆連根拔掉。
    80 行、必要欄位與必要章節是 skill B6 的規則，在此之前只有骨架自己這個 repo 在驗，
    使用者的專案拿不到（報告原話：「本 repo 有較強版本，但沒有部署給使用者」）。

    七個情境都實跑 `check_docs.py`：刪檔、超行、缺章節、欄位重複各要 exit 2；
    `--docs-only` 下刪檔要 exit 0（那個開關要真的是開關）；連結誤報的 fixture 要 exit 0；
    最後放一個真的死連結進去，確認「不誤報」不是靠「什麼都不報」換來的。
    """
    handoff = dest / 'HANDOFF.md'
    original = handoff.read_text(encoding='utf-8')
    # 放在根目錄：fixture 裡那三個「真的連結」指向 README.md，放到 docs/ai-notes/
    # 底下會解析不到，那會變成 fixture 自己製造的死連結（第一版就是這樣誤判）。
    probe = dest / 'link-probe.md'

    def check(args=()):
        git(['add', '-A'], dest)
        return run([sys.executable, '-X', 'utf8', 'tools/check_docs.py', *args], cwd=dest)

    bad = []
    try:
        # R07：未追蹤新文件先 stage 後才能進提交驗證集合。
        write_lf(probe, '[dead](missing-r07.md)\n')
        git(['add', '--', probe.name], dest)
        r = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py', '--staged'], cwd=dest)
        if r.returncode != 2 or 'missing-r07.md' not in r.stdout:
            bad.append('R07 新增文件 stage 後沒抓到死連結')
        write_lf(probe, '[good](README.md)\n')
        r = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py', '--staged'], cwd=dest)
        if r.returncode != 2 or '[index]' not in r.stdout:
            bad.append('R07 工作樹好內容遮住 index 壞內容')
        # 移除 index 門檻會錯誤通過；驗證新守門確實改變行為。
        checker = dest / 'tools/check_docs.py'
        checker_original = read_lf(checker)
        write_lf(checker, checker_original.replace('if args.staged:', 'if False:'))
        r = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py', '--staged'], cwd=dest)
        if r.returncode != 0:
            bad.append('R07 負向測試沒重現部分 stage 被錯放')
        write_lf(checker, checker_original)
        probe.unlink()
        git(['add', '-A'], dest)

        for value in ('`machine` ／ ``', '`machine` ／ `   `', '`` ／ `Codex CLI`'):
            write_lf(handoff, original.replace('無（已交棒）', value))
            r = check()
            if r.returncode != 2:
                bad.append('R08 空機器／工具欄沒擋下：' + value)
        write_lf(handoff, original.replace('無（已交棒）', '`machine` ／ ``'))
        write_lf(checker, checker_original.replace('or not fields[1] ', ''))
        if check().returncode != 0:
            bad.append('R08 負向測試沒重現空工具欄被放行')
        write_lf(checker, checker_original)
        write_lf(handoff, original)

        spaced = dest / 'existing file.md'
        write_lf(spaced, '# Existing\n')
        write_lf(probe, '[valid](<existing file.md> "title")\n')
        r = check()
        if r.returncode:
            bad.append('R09 角括號／空白／title 合用誤報')
        old_order = checker_original.replace(
            "    link = TITLE_RE.sub('', link).strip()\n    if link.startswith('<') and link.endswith('>'):\n        link = link[1:-1].strip()",
            "    if link.startswith('<') and link.endswith('>'):\n        link = link[1:-1].strip()\n    else:\n        link = TITLE_RE.sub('', link).strip()")
        write_lf(checker, old_order)
        if check().returncode != 2:
            bad.append('R09 負向測試沒重現角括號 title 誤報')
        write_lf(checker, checker_original)
        spaced.unlink()
        probe.unlink()

        handoff.unlink()
        r = check()
        if r.returncode != 2 or 'HANDOFF.md' not in r.stdout:
            bad.append('刪掉 HANDOFF.md 沒被擋下（exit %d）' % r.returncode)
        write_lf(handoff, original)

        # --docs-only 用「超行」驗，不用「刪檔」：刪掉 HANDOFF.md 會讓 README／AGENTS
        # 指向它的連結變成**真的**死連結，於是 --docs-only 照樣 exit 2——那不是開關沒用。
        write_lf(handoff, original.rstrip('\n') + '\n' + '- 填行\n' * 90)
        r = check()
        if r.returncode != 2 or '80 行' not in r.stdout:
            bad.append('超過 80 行沒被擋下（exit %d）' % r.returncode)
        r = check(['--docs-only'])
        if r.returncode != 0:
            bad.append('--docs-only 下仍然 exit %d（這個開關要真的關掉第 7 項）'
                       % r.returncode)

        write_lf(handoff, original.replace('## 已完成', '## 做完的'))
        r = check()
        if r.returncode != 2 or '已完成' not in r.stdout:
            bad.append('缺必要章節沒被擋下（exit %d）' % r.returncode)

        # 章節重複＝往下疊成日誌（B6 禁止）。2026-11-02 在真專案上量到一份有兩個
        # 「## 已完成（日期）」——所以比對開頭、罰重複，而不是罰標題的措辭。
        write_lf(handoff, original + '\n## 已完成（更早）\n\n- 舊的\n')
        r = check()
        if r.returncode != 2 or '不要往下疊' not in r.stdout:
            bad.append('章節重複沒被擋下（exit %d）' % r.returncode)

        write_lf(handoff, original.replace('- **交棒者**', '- **交接時間**', 1))
        r = check()
        if r.returncode != 2 or '交棒者' not in r.stdout:
            bad.append('欄位重複／缺漏沒被擋下（exit %d）' % r.returncode)
        write_lf(handoff, original)

        write_lf(probe, LINK_FIXTURE)
        r = check()
        if r.returncode != 0:
            bad.append('連結誤報：程式碼範例／帶 title／角括號被當成死連結（exit %d：%s）'
                       % (r.returncode, r.stdout.strip()[:90]))
        write_lf(probe, LINK_FIXTURE + '\n[真的死連結](no-such-file.md)\n')
        r = check()
        if r.returncode != 2 or 'no-such-file.md' not in r.stdout:
            bad.append('真的死連結沒被抓到（exit %d）——不誤報不能靠什麼都不報換'
                       % r.returncode)
    finally:
        write_lf(handoff, original)
        probe.unlink(missing_ok=True)
        git(['add', '-A'], dest)

    if bad:
        record('FAIL', '交接快照檢查', '；'.join(bad[:4]))
        return False
    record('OK', '交接快照檢查',
           '刪檔／超 80 行／缺章節／章節重複／欄位重複都 exit 2，--docs-only 真的關得掉'
           '（用超行情境驗，刪檔會連帶產生真的死連結）；'
           '程式碼範例、帶 title 與角括號連結不誤報，真的死連結仍 exit 2；R07 stage 集合／部分 stage、R08 空欄、R09 空白角括號 title 組合與負向變異')
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
    step_python_floor(dest)
    step_claims(dest)
    step_state_exit(dest)
    step_snapshot_guard(dest)

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
2. 依第 4 節先本機驗收（含 ignore、文件與執行位元），通過才提交及首次發布。
3. 跑第 5 節遠端與工具驗收清單，逐項回報通過／不適用／有問題。
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


def build_zip(out_path, skipped=()):
    """打包未填的骨架；呼叫端先檢查門檻，有 skipped 時明確標示未驗證。

    刻意從部署包重新抽一次未填的範本，不用驗證流程裡那份——那一份的佔位符已經
    被測試用假值填掉了，打包出去會讓人拿到「驗證用假專案」當專案名。
    """
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='pack-'))
    try:
        src = tmp / 'gen'
        src.mkdir()
        extract(src)
        warning = ''
        if skipped:
            # F07：顯式調試產物不能看起來像完整通過的發行包。
            warning = '# 未驗證產物（UNVERIFIED）\n\n部分檢查被跳過；不可視為正式驗證通過。詳見 UNVERIFIED.json。\n\n'
            manifest = {'status': 'UNVERIFIED', 'skipped': [
                {'name': title, 'reason': detail} for _, title, detail in skipped]}
            write_lf(src / 'UNVERIFIED.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        write_lf(src / '讀我-先看這個.md', warning + ZIP_README)
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
        with zipfile.ZipFile(out_path) as z:
            n = len(z.namelist())
        label = '未驗證產物（UNVERIFIED）' if skipped else '已驗證產物'
        print(f'\n已打包 {label} {n} 檔 → {out_path}')
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def zip_gate_problems(entry, tmp):
    """注入檢查結果走真正的 CLI main 與 ZIP 寫入，不啟動模型或外部發布。"""
    problems = []
    scenarios = (
        ('全過', ('OK',), True, False, False, 0, True),
        ('全過加例外', ('OK',), True, True, False, 0, True),
        ('SKIP 不打包', ('SKIP',), False, False, False, 1, False),
        ('SKIP 預設拒絕', ('SKIP',), True, False, False, 1, False),
        ('SKIP 顯式調試', ('SKIP',), True, True, False, 1, True),
        ('FAIL 拒絕', ('FAIL',), True, False, False, 2, False),
        ('FAIL 不能覆寫', ('FAIL',), True, True, False, 2, False),
        ('FAIL 優先於 SKIP', ('FAIL', 'SKIP'), True, True, False, 2, False),
        ('SKIP 保留既有檔', ('SKIP',), True, False, True, 1, False),
        ('FAIL 保留既有檔', ('FAIL',), True, True, True, 2, False),
    )
    for i, (name, statuses, zip_requested, allow, existing, want_rc, want_zip) in enumerate(scenarios):
        out = tmp / ('gate-%d.zip' % i)
        sentinel = b'existing artifact'
        if existing:
            out.write_bytes(sentinel)
        rows = [(s, 'fixture-' + s, 'injected reason') for s in statuses]
        argv = ['verify_bootstrap.py'] + (['--zip', str(out)] if zip_requested else [])
        if allow:
            argv.append('--allow-unverified-zip')
        capture = io.StringIO()
        # 使用獨立 results，巢狀 main 清空結果時不會吃掉外層驗證。
        with patch.dict(entry.__globals__, {'results': [], 'run_checks': lambda d, t: results.extend(rows)}), \
                patch.object(sys, 'argv', argv), redirect_stdout(capture), redirect_stderr(capture):
            rc = entry()
        if rc != want_rc:
            problems.append('%s exit %s，期望 %s' % (name, rc, want_rc))
        if want_zip:
            if not out.exists() or not zipfile.is_zipfile(out):
                problems.append(name + ' 缺 ZIP')
                continue
            with zipfile.ZipFile(out) as z:
                unverified = 'SKIP' in statuses
                has_manifest = 'UNVERIFIED.json' in z.namelist()
                if has_manifest != unverified:
                    problems.append(name + ' 未驗證 manifest 判定錯誤')
                if unverified and has_manifest:
                    manifest = json.loads(z.read('UNVERIFIED.json'))
                    if manifest != {'status': 'UNVERIFIED', 'skipped': [
                            {'name': 'fixture-SKIP', 'reason': 'injected reason'}]}:
                        problems.append(name + ' manifest 沒有保留跳過項目與原因')
                readme = z.read('讀我-先看這個.md').decode('utf-8')
                if ('UNVERIFIED' in readme) != unverified:
                    problems.append(name + ' 說明檔標示錯誤')
        elif existing:
            if out.read_bytes() != sentinel:
                problems.append(name + ' 覆寫了既有產物')
        elif out.exists():
            problems.append(name + ' 不該產出 ZIP')
        if 'SKIP' in statuses and 'FAIL' not in statuses and 'fixture-SKIP' not in capture.getvalue():
            problems.append(name + ' 沒說明哪項 SKIP')
    return problems


def step_zip_gate(tmp):
    problems = zip_gate_problems(main, tmp)
    # 負向測試：移除 SKIP 提前返回的門檻，必須抓到錯誤產物與舊檔被覆寫。
    import inspect
    source = inspect.getsource(main)
    guard = 'if not args.allow_unverified_zip:'
    if guard not in source:
        problems.append('負向測試找不到 SKIP 門檻')
    else:
        mutant = {}
        exec(compile(source.replace(guard, 'if False:', 1), '<zip-gate-mutant>', 'exec'), globals(), mutant)
        negative_dir = tmp / 'negative-zip'
        negative_dir.mkdir()
        caught = zip_gate_problems(mutant['main'], negative_dir)
        if not any('不該產出 ZIP' in p for p in caught) or not any('覆寫了既有產物' in p for p in caught):
            problems.append('負向測試沒有抓到移除門檻後的錯誤打包')
    record('FAIL' if problems else 'OK', 'ZIP 發布門檻',
           '；'.join(problems) if problems else '10 情境：SKIP 預設不打包、例外附未驗證清單且 exit 1、FAIL 不可覆寫、既有產物保留；移除門檻的負向測試確實失敗')


def flow_contract_problems(skill):
    """F11：檢查結構與關鍵操作契約，不宣稱測到模型遵循。"""
    bad = []
    table = re.search(r'### A／B／C 狀態轉移.*?(?=\n\*\*證據的範圍)', skill, re.S)
    expected = {
        '待接棒': ('A1', 'fetch exit 0', 'ahead=0、behind=0', '停下'),
        '已定位': ('A4', '結束碼', 'A5 開工成功後'),
        '開工中': ('HANDOFF', 'push exit 0', 'origin', '停止修改'),
        '工作中': ('B7 → B8', 'exit 0', 'upstream', '工作中'),
        '待交棒': ('B7', 'exit 0', '無（已交棒）', '不可發布'),
        '已交棒': ('B9', 'origin', '重走 A'),
    }
    rows = {}
    if table:
        for line in table.group().splitlines():
            if line.startswith('|'):
                cells = [c.strip() for c in line.strip('|').split('|')]
                if cells[0] in expected:
                    if cells[0] in rows:
                        bad.append('重複狀態：' + cells[0])
                    rows[cells[0]] = cells
    for state, tokens in expected.items():
        cells = rows.get(state, [])
        if len(cells) != 5 or not all(cells) or any(t not in ' '.join(cells) for t in tokens):
            bad.append('狀態缺前提／操作／證據／失敗處理：' + state)

    contracts = (
        ('### A1 ', 'ahead-only（ahead > 0、behind = 0） | **停**'),
        ('### A1 ', 'fetch 失敗（非零退出） | **停**'),
        ('### A1 ', 'HEAD...@{upstream}'),
        ('### A2 ', '切換到待續分支後重跑 A1'),
        ('### A4 ', '此步只記錄差異與結束碼、不修改專案檔案'),
        ('### A4 ', '開工標記 push 成功後'),
        ('### A5 ', '這是開工 push 例外'),
        ('### A5 ', 'push 成功後重讀 origin'),
        ('### B7 ', 'B6 覆寫完成後'),
        ('### B7 ', 'tools/check_docs.py'),
        ('### B7 ', 'exit 0 才提交發布'),
        ('### B7 ', 'B3 後改過，連 B3 也重跑'),
        ('### B8 ', 'fetch 失敗 → **停下**'),
        ('## C.', '保留本 session 的「工作中」標記'),
        ('## C.', '不走 B6 的釋出標記與 B9 的交棒計數'),
    )
    for heading, token in contracts:
        part = skill.split(heading, 1)[-1].split('\n### ', 1)[0].split('\n## ', 1)[0]
        if heading not in skill or token not in part:
            bad.append(heading + '缺契約：' + token)
    mode = skill.split('## 判斷模式', 1)[-1].split('### A／B／C', 1)[0]
    if '只有 **A5 開工標記**與 **C 中途安全點**例外' not in mode:
        bad.append('push 模式缺 A5／C 例外')
    b7 = skill.split('### B7 ', 1)[-1].split('### B8 ', 1)[0]
    stage_pos = b7.find('git diff --cached --name-only')
    verify_pos = b7.find('tools/check_docs.py --staged')
    if stage_pos < 0 or verify_pos < stage_pos:
        bad.append('R07 必須先檢視 stage 集合再執行 --staged 驗證')
    return bad


def step_flow_contract(dest, tmp):
    skill = skill_text(dest)
    bad = flow_contract_problems(skill)
    # 每種契約都故意拿掉一次，避免檢查器永遠回成功。
    mutations = ('| 待接棒 |', '| 已定位 |', '| 開工中 |', '| 工作中 |', '| 待交棒 |', '| 已交棒 |',
                 'ahead-only（ahead > 0、behind = 0）', 'fetch 失敗（非零退出）',
                 '切換到待續分支後重跑 A1', '此步只記錄差異與結束碼、不修改專案檔案',
                 '這是開工 push 例外', 'push 成功後重讀 origin', 'B6 覆寫完成後',
                 'B3 後改過，連 B3 也重跑', 'fetch 失敗 → **停下**',
                 '保留本 session 的「工作中」標記', '不走 B6 的釋出標記與 B9 的交棒計數',
                 '只有 **A5 開工標記**與 **C 中途安全點**例外')
    mutations += ('tools/check_docs.py --staged', 'git diff --cached --name-only')
    for token in mutations:
        mutated = skill.replace(token, '移除契約')
        if mutated == skill or not flow_contract_problems(mutated):
            bad.append('負向測試未擋：' + token)
    record('FAIL' if bad else 'OK', '協作狀態契約', '；'.join(bad) if bad else
           '六狀態與 A1／A2／A4／A5／B7／B8／C 契約齊備；20 個負向測試通過，含 R07 stage 順序（不代表模型遵循）')

    bash = find_bash()
    if not bash:
        record('SKIP', 'Git 異常提示', '缺少可用 bash')
        return
    origin, work, peer = (tmp / n for n in ('flow-origin.git', 'flow-work', 'flow-peer'))
    def must(args, cwd=None):
        r = run(['git', *args], cwd=cwd)
        if r.returncode:
            raise RuntimeError('Git fixture 失敗：' + r.stderr)
        return r
    must(['init', '-q', '--bare', str(origin)])
    must(['init', '-q', '-b', 'main', str(work)])
    write_lf(work / 'file', 'init\n')
    must(['add', 'file'], work)
    must(['commit', '-qm', 'init'], work)
    must(['remote', 'add', 'origin', str(origin)], work)
    must(['push', '-qu', 'origin', 'main'], work)
    must(['clone', '-q', '-b', 'main', str(origin), str(peer)])
    write_lf(work / 'file', 'local\n')
    must(['commit', '-qam', 'local'], work)
    scripts = [('部署 hook', read_lf(dest / '.claude/hooks/git-freshness.sh')),
               ('本 repo hook', read_lf(ROOT / '.claude/hooks/repo-git-check.sh'))]
    issues = []
    def check_scripts(state, marker):
        for name, source in scripts:
            path = tmp / 'flow-probe.sh'
            write_lf(path, source)
            r = run([bash, str(path)], cwd=work, env=tool_env(BOOTSTRAP_FRESHNESS='off'))
            if r.returncode or marker not in r.stdout or '停下' not in r.stdout or '等待使用者指示' not in r.stdout or 'git pull --rebase' in r.stdout:
                issues.append(name + ' ' + state + ' 未要求停止或仍建議 rebase')
    check_scripts('ahead-only', 'ahead-only')
    write_lf(peer / 'file', 'remote\n')
    must(['commit', '-qam', 'remote'], peer)
    must(['push', '-q', 'origin', 'main'], peer)
    check_scripts('diverged', '已分岔')
    # 在真分岔 fixture 上恢復舊建議，儀器必須辨識這是錯誤提示。
    old = scripts[0][1].replace('停下回報並等待使用者指示；不得自行 rebase 或 merge', '開工前必須先整合（git pull --rebase）')
    path = tmp / 'flow-old.sh'
    write_lf(path, old)
    r = run([bash, str(path)], cwd=work, env=tool_env(BOOTSTRAP_FRESHNESS='off'))
    if '已分岔' not in r.stdout or 'git pull --rebase' not in r.stdout:
        issues.append('負向測試未重現舊分岔建議')
    must(['remote', 'set-url', 'origin', str(tmp / 'missing-origin.git')], work)
    check_scripts('fetch failure', '無法 fetch')
    record('FAIL' if issues else 'OK', 'Git 異常提示', '；'.join(issues) if issues else
           '兩支 hook 實跑 ahead-only／分岔／fetch 失敗均要求停止；舊 rebase 建議負向重現')


def core_priority_problems(skill, protocol, readme=None):
    bad = []
    for name, text in (('skill', skill), ('protocol', protocol)):
        if text.count('**核心優先序：SKILL.md**') != 1:
            bad.append(name + ' 核心優先序不唯一或不一致')
        for token in ('不同步的專案實例', '升級時須人工遷移', '不得在單一專案就地修改共用 skill',
                      'override', '使用者明確指示仍優先'):
            if token not in text:
                bad.append(name + ' 缺 ' + token)
        if re.search(r'兩者衝突時.*(?:以協定為準|以本檔為準)', text):
            bad.append(name + ' 恢復舊優先序')
    if readme is not None:
        plain = readme.replace('**', '')
        if '核心優先序：SKILL.md' not in plain or '使用者明確指示仍優先' not in plain:
            bad.append('README 缺核心優先序或使用者優先宣告')
        if re.search(r'兩者衝突(?:時)?.*以協定為準', plain):
            bad.append('README 恢復舊優先序')
    return bad


def step_core_priority(dest, tmp):
    import sync_project as syncer
    skill = skill_text(dest)
    protocol = read_lf(dest / 'docs/ai-notes/handover-protocol.md')
    bad = core_priority_problems(skill, protocol)
    readme = read_lf(ROOT / 'README.md')
    bad.extend(core_priority_problems(skill, protocol, readme))
    for mutant in (readme.replace('核心優先序：SKILL.md', '舊優先序'),
                   readme + '\n兩者衝突以協定為準。\n',
                   readme + '\n兩者衝突時**以協定為準**。\n'):
        if not core_priority_problems(skill, protocol, mutant):
            bad.append('R06 README 負向測試沒擋住反向或缺失宣告')
    for index in (0, 1):
        for token in ('**核心優先序：SKILL.md**', '升級時須人工遷移', '不得在單一專案就地修改共用 skill'):
            pair = [skill, protocol]
            pair[index] = pair[index].replace(token, '舊規則')
            if not core_priority_problems(*pair):
                bad.append('負向測試未擋 ' + token)
    # 不依賴 Git 歷史也可驗：把兩份文件頂端的舊宣告還原。
    for index, line in enumerate(('兩者衝突時**以協定為準**，並就地修正本檔。',
                                  '兩者衝突時**以本檔為準**，並就地修正 skill。')):
        pair = [skill, protocol]
        pair[index] = line + '\n' + pair[index]
        if not core_priority_problems(*pair):
            bad.append('反向優先序未擋')
    project = tmp / 'priority-project'
    shutil.copytree(dest, project)
    write_lf(project / 'docs/ai-notes/handover-protocol.md', '舊協定，專案自訂規則保留\n')
    plan = syncer.sync(project, dest)
    if not any('MIGRATE' in m for m in plan.msgs) or not any('核心版本' in m for m in plan.msgs):
        bad.append('同步未列核心版本與人工遷移需求')
    if any(rel == 'docs/ai-notes/handover-protocol.md' for _, _, rel in plan.writes):
        bad.append('同步覆蓋專案協定')
    record('FAIL' if bad else 'OK', '核心與實例優先序', '；'.join(bad) if bad else
           '核心兩份與 README 宣告一致、override 範圍明確、11 個負向測試；同步列核心版本與 MIGRATE，不覆蓋舊實例')


def coordination_problems(skill, protocol):
    bad = []
    a25 = skill.split('### A2.5 ', 1)[-1].split('### A3 ', 1)[0]
    a5 = skill.split('### A5 ', 1)[-1].split('### A6 ', 1)[0]
    for label, text, tokens in (
        ('A2.5', a25, ('接力式 single-writer', '協調訊號，不是互斥鎖', '同一工作樹不得同時有兩個 writer',
                       '不得自動奪取 writer', '不是穩定 owner token', '同時記錄觀測到的', '原子 claim 尚未實作', '未做並行實驗')),
        ('A5', a5, ('協調訊號，不是互斥鎖', 'SHA 與 A2.5 觀測值不同就停止', '不能當一般 merge 衝突合併', '不等於取得原子 claim')),
        ('協定', protocol, ('接力式 single-writer', '協調訊號，不是互斥鎖', '不得自動奪取 writer', '原子 claim 尚未實作', '未做並行實驗'))):
        for token in tokens:
            if token not in text:
                bad.append(label + ' 缺 ' + token)
    return bad


def step_coordination(dest):
    skill = skill_text(dest)
    protocol = read_lf(dest / 'docs/ai-notes/handover-protocol.md')
    bad = coordination_problems(skill, protocol)
    probes = ('協調訊號，不是互斥鎖', '不得自動奪取 writer', '原子 claim 尚未實作', '未做並行實驗')
    for i in (0, 1):
        for token in probes:
            pair = [skill, protocol]
            pair[i] = pair[i].replace(token, '移除邊界')
            if not coordination_problems(*pair):
                bad.append('負向測試未擋 ' + token)
    record('FAIL' if bad else 'OK', '接力協調邊界', '；'.join(bad) if bad else
           'A2.5／A5／協定明列協調範圍、SHA 比對與禁止自動奪取；8 個負向測試，不代表並行互斥實測')


def sync_owner_cli_problems(cli, folder, gen, scenarios=None):
    """R03：真 local bare origin；成功流程與拒絕情境都檢查檔案內容。"""
    bad = []
    for scenario in (scenarios or ('own', 'other', 'ahead', 'behind', 'diverged', 'offline', 'no-upstream', 'local-marker')):
        work = folder / ('owner-' + scenario)
        shutil.copytree(gen, work, ignore=shutil.ignore_patterns('.git'))
        step_fill(work, report=False)
        wiring = work / '.codex/hooks.json'
        write_lf(wiring, '{"hooks":{}}\n')
        def must(args, cwd=work):
            r = git(args, cwd)
            if r.returncode:
                raise RuntimeError('owner fixture: ' + r.stderr)
            return r
        must(['init', '-q', '-b', 'main'])
        must(['add', '.'])
        must(['commit', '-qm', 'fixture'])
        owner = fixture_origin(work)
        handoff = work / 'HANDOFF.md'
        text = read_lf(handoff).replace('無（已交棒）', owner)
        write_lf(handoff, text)
        must(['commit', '-qam', 'A5 own claim'])
        must(['push', '-q', 'origin', 'HEAD'])
        if scenario in ('behind', 'diverged'):
            peer = folder / ('peer-' + scenario)
            must(['clone', '-q', str(work.parent / (work.name + '-origin.git')), str(peer)])
            # bare HEAD 的預設分支可能不是 main，明確切換。
            must(['checkout', '-q', 'main'], peer)
            write_lf(peer / 'HANDOFF.md', read_lf(peer / 'HANDOFF.md').replace(owner, '`peer` ／ `Codex CLI`'))
            must(['commit', '-qam', 'peer busy'], peer)
            must(['push', '-q', 'origin', 'HEAD'], peer)
        if scenario in ('ahead', 'diverged'):
            write_lf(work / 'local-note', 'local commit\n')
            must(['add', 'local-note'])
            must(['commit', '-qm', 'local ahead'])
        if scenario == 'offline':
            must(['remote', 'set-url', 'origin', str(folder / 'absent-origin.git')])
        if scenario == 'no-upstream':
            must(['branch', '--unset-upstream'])
        if scenario == 'local-marker':
            write_lf(handoff, text.replace(owner, '`peer` ／ `Codex CLI`'))
        before = {str(p.relative_to(work)): p.read_bytes() for p in work.rglob('*')
                  if p.is_file() and '.git' not in p.relative_to(work).parts}
        if scenario == 'own':
            for invalid in ([str(work), '--write'], ['--all', '--root', str(folder), '--write'],
                            [str(work), '--write', '--owner', '無（已交棒）']):
                if run(cli + invalid).returncode == 0 or wiring.read_bytes() != before[str(wiring.relative_to(work))]:
                    bad.append('R03 無 owner／批次／空閒 writer 未拒絕')
        args = [str(work), '--codex-only', '--write', '--owner',
                '`someone-else` ／ `Codex CLI`' if scenario == 'other' else owner, '--allow-dirty']
        r = run(cli + args)
        if scenario != 'own':
            after = {str(p.relative_to(work)): p.read_bytes() for p in work.rglob('*')
                     if p.is_file() and '.git' not in p.relative_to(work).parts}
            if r.returncode == 0 or after != before:
                bad.append('R03 未拒絕或非零寫入：' + scenario)
            continue
        if r.returncode or read_lf(wiring) != read_lf(gen / '.codex/hooks.json'):
            bad.append('R03 自身 A5 claim 無法同步')
            continue
        # B7／B8：驗最終文件，明確 stage，發布清標記快照。
        write_lf(handoff, read_lf(handoff).replace(owner, '無（已交棒）'))
        must(['add', 'HANDOFF.md', '.codex/hooks.json'])
        checked = run([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], cwd=work)
        if checked.returncode:
            bad.append('R03 同步後 B7 文件檢查失敗：' + checked.stdout)
        must(['commit', '-qm', 'B7 final snapshot'])
        must(['fetch', '-q', 'origin'])
        must(['push', '-q', 'origin', 'HEAD'])
        if '無（已交棒）' not in must(['show', 'origin/main:HANDOFF.md']).stdout or must(['status', '--porcelain']).stdout:
            bad.append('R03 B8 未清標記或工作樹不乾淨')
    return bad


def inventory_cli_problems(cli, folder, normal):
    """R05：active 失效不能冒充成功；archived 與重複路徑另驗。"""
    bad = []
    inv = folder / 'active-cases.json'
    active = {'path': str(normal), 'status': 'active'}
    missing = {'path': 'missing-active', 'status': 'active'}
    cases = [([active, missing], False),
             ([active, dict(missing, status='archived')], True),
             ([missing], False), ([active, active], False)]
    for i, (items, success) in enumerate(cases):
        write_lf(inv, json.dumps(items))
        r = run(cli + ['--inventory', str(inv)])
        if (r.returncode == 0) != success or (not success and '全部都已經是' in r.stdout):
            bad.append('R05 inventory CLI 結果錯誤 ' + str(i))
        if i == 0 and ('FAIL' not in r.stdout or '沒有完成' not in r.stdout):
            bad.append('R05 混合 active 失敗未列入彙總')
    return bad


def step_sync_scope(dest, tmp):
    import sync_project as sp
    folder = tmp / 'scope'
    folder.mkdir()
    folder = folder.resolve()  # Windows TEMP 可能是 8.3 短路徑；決策輸出已正規化。
    bad = []
    def must(args, cwd=None):
        r = run(['git', *args], cwd=cwd)
        if r.returncode:
            raise RuntimeError('scope fixture: ' + r.stderr)
        return r
    def project(name):
        p = folder / name
        shutil.copytree(dest, p, ignore=shutil.ignore_patterns('.git'))
        must(['init', '-q', '-b', 'main'], p)
        must(['add', '.'], p)
        must(['commit', '-qm', 'fixture'], p)
        return p
    normal = project('normal-worktrees-name')
    archived = project('archived')
    owner = fixture_origin(normal)
    fixture_origin(archived)
    linked = folder / 'arbitrary-checkout'
    must(['worktree', 'add', '-q', '-b', 'peer', str(linked)], normal)
    decisions = dict(sp.discover_decisions([folder], ['archived']))
    if decisions.get(normal, 'missing') is not None:
        bad.append('名字含 worktrees 的普通目錄被排除')
    if 'worktree' not in (decisions.get(linked) or ''):
        bad.append('任意名稱的真 worktree 未排除')
    if decisions.get(archived) != '明確排除':
        bad.append('明確排除未列原因')
    inv = folder / 'inventory.json'
    write_lf(inv, json.dumps([{'path': normal.name, 'status': 'active'},
                             {'path': archived.name, 'status': 'archived'}]))
    if dict(sp.inventory_decisions(inv)).get(archived) != 'inventory 已完結':
        bad.append('已完結專案未排除')
    cli = [sys.executable, '-X', 'utf8', str(ROOT / 'tools/sync_project.py')]
    r = run(cli + ['--inventory', str(inv)])
    if r.returncode or 'INCLUDE' not in r.stdout or 'EXCLUDE' not in r.stdout or '全域' not in r.stdout:
        bad.append('inventory CLI 範圍／排除原因未列出')
    bad.extend(inventory_cli_problems(cli, folder, normal))
    # 負向測試恢復「active 失效當正常排除」，走相同真 CLI 案例。
    mutant = folder / 'sync-mutant.py'
    source = read_lf(ROOT / 'tools/sync_project.py')
    write_lf(mutant, source.replace("reason = 'inventory active 無法處理：' + reason", 'reason = reason'))
    wrapper = ('import sys; sys.path.insert(0, %r); __file__=%r; '
               'exec(compile(open(%r, encoding="utf-8").read(), __file__, "exec"))'
               % (str(ROOT / 'tools'), str(ROOT / 'tools/sync_project.py'), str(mutant)))
    if not inventory_cli_problems([sys.executable, '-X', 'utf8', '-c', wrapper], folder, normal):
        bad.append('R05 負向測試沒抓到 active 失效被排除')
    bad.extend(sync_owner_cli_problems(cli, folder, dest))
    owner_mutant = folder / 'owner-mutant.py'
    first = source.index('def sync_owner_check(')
    last = source.index('\n\ndef preflight(', first)
    write_lf(owner_mutant, source[:first] +
             "def sync_owner_check(project, owner=None, writing=False):\n    return git_output(project, 'rev-parse', 'HEAD')\n" + source[last:])
    owner_wrapper = ('import sys; sys.path.insert(0, %r); __file__=%r; '
                     'exec(compile(open(%r, encoding="utf-8").read(), __file__, "exec"))'
                     % (str(ROOT / 'tools'), str(ROOT / 'tools/sync_project.py'), str(owner_mutant)))
    negative_folder = folder / 'owner-negative'
    negative_folder.mkdir()
    if not sync_owner_cli_problems([sys.executable, '-X', 'utf8', '-c', owner_wrapper], negative_folder, dest, ('other',)):
        bad.append('R03 移除資格檢查的 CLI 負向測試沒抓到錯誤寫入')
    write_lf(normal / 'HANDOFF.md', '- **工作中**：' + owner + '\n')
    must(['commit', '-qam', 'A5 claim'], normal)
    must(['push', '-q', 'origin', 'HEAD'], normal)
    # 真的寫入入口：dirty、占用、客製漂移都必須零寫入、非零退出。
    skill = normal / '.claude/skills/handoff/SKILL.md'
    original = read_lf(skill)
    def rejected(label, extra=()):
        before = skill.read_bytes()
        common = (normal / sp.SURGICAL).read_bytes()
        r = run(cli + [str(normal), '--write', '--owner', owner, *extra])
        if r.returncode == 0 or skill.read_bytes() != before or (normal / sp.SURGICAL).read_bytes() != common or label not in r.stdout:
            bad.append(label + ' preflight 沒擋／已有寫入')
    write_lf(normal / 'note', 'unfinished\n')
    rejected('dirty')
    (normal / 'note').unlink()
    write_lf(normal / 'HANDOFF.md', '- **工作中**：`peer` ／ `Codex CLI`\n')
    must(['commit', '-qam', 'busy'], normal)
    must(['push', '-q', 'origin', 'HEAD'], normal)
    rejected('占用')
    write_lf(normal / 'HANDOFF.md', '- **工作中**：' + owner + '\n')
    write_lf(skill, original + '\nproject custom rule\n')
    must(['commit', '-qam', 'custom'], normal)
    must(['push', '-q', 'origin', 'HEAD'], normal)
    rejected('客製漂移')
    r = run(cli + [str(normal), '--write', '--owner', owner, '--accept-drift', '.claude/skills/handoff/SKILL.md'])
    if r.returncode or 'project custom rule' in read_lf(skill):
        bad.append('明確接受單檔漂移後仍無法同步')
    must(['add', '.'], normal)
    must(['commit', '-qm', 'synced'], normal)
    must(['push', '-q', 'origin', 'HEAD'], normal)
    checker = normal / sp.SURGICAL
    original_checker = read_lf(checker)
    write_lf(checker, original_checker + '\n# project custom implementation\n')
    must(['commit', '-qam', 'custom checker'], normal)
    must(['push', '-q', 'origin', 'HEAD'], normal)
    rejected('客製漂移')
    write_lf(checker, original_checker)
    # 反向測試：把新 preflight 拿掉，客製漂移會真的被覆蓋。
    write_lf(skill, original + '\nproject custom rule\n')
    plan = sp.sync(normal, dest)
    done, error = sp.apply_plan(plan)
    if error or '.claude/skills/handoff/SKILL.md' not in done or 'project custom rule' in read_lf(skill):
        bad.append('移除 preflight 的負向測試未重現覆蓋')
    record('FAIL' if bad else 'OK', '同步範圍與前置檢查', '；'.join(bad) if bad else
           '真 worktree／含 worktrees 普通目錄／已完結 inventory；R03 自身 writer→同步→B7→B8、七種資格拒絕與負向變異；R05 active 失效、archived、重複路徑與 CLI 負向變異；dirty／占用／整份檔與共用程式漂移拒絕且零寫入')


def deployment_order_problems(kit, skill, zip_readme, readme):
    bad = []
    section = kit.split('## 4. ', 1)[-1].split('## 5. ', 1)[0]
    sequence = ('### 4.1 本機驗收', 'git add .', 'git check-ignore',
                'git update-index --chmod=+x .claude/hooks/ag-wrap.sh',
                'python -X utf8 tools/check_docs.py', '### 4.2 首次發布',
                'git commit -m', 'gh repo create')
    positions = [section.find(token) for token in sequence]
    if any(i < 0 for i in positions) or positions != sorted(positions):
        bad.append('本機驗收／首次提交／發布順序缺失或反轉')
    for name, text in (('skill', skill), ('ZIP', zip_readme), ('README', readme)):
        if '先本機驗收' not in text and '先完成第 4 節的本機驗收' not in text:
            bad.append(name + ' 入口未要求先本機驗收')
    return bad


def deployment_index_problems(work, paths):
    bad = []
    for path in paths:
        if git(['check-ignore', '--no-index', '-q', '--', path], work).returncode:
            bad.append('未忽略 ' + path)
        if git(['ls-files', '--', path], work).stdout.strip():
            bad.append('已進索引 ' + path)
    mode = git(['ls-files', '--stage', '--', '.claude/hooks/ag-wrap.sh'], work)
    if mode.returncode or not mode.stdout.startswith('100755 '):
        bad.append('wrapper 索引 mode 不是 100755')
    return bad


def step_deployment_lifecycle(tmp):
    work, remote, clone = (tmp / n for n in ('deploy-life', 'deploy-origin.git', 'deploy-clone'))
    extract(work)
    # manifest 是訪談輸入與預期的單一 fixture，全部是假資料，不需要外部帳戶。
    manifest = dict(ANSWERS, SECRETS='`credentials/odd-session.fixture`、`keys/測試 key.fixture`',
                    RUNTIME_DIRS='`run outputs/`')
    if not step_fill(work, manifest, report=False):
        record('FAIL', '部署生命週期', '訪談替換失敗')
        return
    paths = ['credentials/odd-session.fixture', 'keys/測試 key.fixture', 'run outputs/state.fixture']
    for name in paths:
        path = work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        write_lf(path, 'synthetic deployment fixture only\n')
    def must(args, cwd=None):
        r = run(args, cwd=cwd)
        if r.returncode:
            raise RuntimeError('deployment fixture: ' + r.stderr + r.stdout)
        return r
    must(['git', 'init', '-q', '-b', 'main', str(work)])
    must(['git', 'add', '.'], work)
    kit = read_lf(KIT)
    skill = skill_text(work)
    bad = deployment_order_problems(kit, skill, ZIP_README, read_lf(ROOT / 'README.md'))
    for invalid in (' !fixture', '` !fixture`'):
        try:
            ignore_rules(invalid)
        except ValueError:
            pass
        else:
            bad.append('反向納入祕密的 ignore 輸入未拒絕')
    # 從操作卡取出原始命令執行，避免只驗測試自己的固定命令。
    command = re.search(r'^git update-index --chmod=\+x \.claude/hooks/ag-wrap\.sh$', kit, re.M)
    if command:
        must(command.group(0).split(), work)
    else:
        bad.append('部署包缺執行位元命令')
    must([sys.executable, '-X', 'utf8', 'tools/check_docs.py'], work)
    state = must([sys.executable, '-X', 'utf8', 'tools/verify_state.py'], work)
    if 'NOT_CONFIGURED' not in state.stdout:
        bad.append('未填服務狀態未明列')
    bad.extend(deployment_index_problems(work, paths))
    # 移除自訂 ignore 規則和執行位元，儀器都必須真的擋得住。
    ignore = read_lf(work / '.gitignore')
    write_lf(work / '.gitignore', ignore.replace(ignore_rules(manifest['SECRETS']), '').replace(ignore_rules(manifest['RUNTIME_DIRS']), ''))
    if not any('未忽略' in s for s in deployment_index_problems(work, paths)):
        bad.append('負向測試未抓到自訂 ignore 缺失')
    write_lf(work / '.gitignore', ignore)
    must(['git', 'update-index', '--chmod=-x', '.claude/hooks/ag-wrap.sh'], work)
    if not any('mode' in s for s in deployment_index_problems(work, paths)):
        bad.append('負向測試未抓到 100644')
    must(['git', 'update-index', '--chmod=+x', '.claude/hooks/ag-wrap.sh'], work)
    for token in ('git check-ignore', 'git update-index --chmod=+x .claude/hooks/ag-wrap.sh', '### 4.1 本機驗收'):
        if not deployment_order_problems(kit.replace(token, '移除門檻'), skill, ZIP_README, read_lf(ROOT / 'README.md')):
            bad.append('順序負向測試未擋 ' + token)
    if bad:
        record('FAIL', '部署生命週期', '；'.join(bad))
        return
    must(['git', 'commit', '-qm', 'bootstrap verified locally'], work)
    must(['git', 'init', '-q', '--bare', str(remote)])
    must(['git', 'remote', 'add', 'origin', str(remote)], work)
    must(['git', 'push', '-qu', 'origin', 'main'], work)
    must(['git', 'clone', '-q', '-b', 'main', str(remote), str(clone)])
    if git(['ls-tree', '-r', '--name-only', 'HEAD', '--', *paths], clone).stdout.strip():
        bad.append('初次 commit 含假憑證或運行資料')
    # clone 後仍驗索引與原始 wrapper；不呼叫模型、不測外部工具注入。
    bad.extend(deployment_index_problems(clone, paths))
    bash = find_bash()
    if not bash:
        record('SKIP', '部署生命週期', '缺少 Git Bash，無法驗 clone 後直接執行 wrapper')
        return
    r = run([bash, '-c', './.claude/hooks/ag-wrap.sh git-freshness.sh'], cwd=clone,
            env=tool_env(BOOTSTRAP_FRESHNESS='off'))
    if r.returncode or '[git-check]' not in r.stdout:
        bad.append('clone 後 wrapper 直接執行失敗')
    record('FAIL' if bad else 'OK', '部署生命週期', '；'.join(bad) if bad else
           '自訂憑證／空白中文路徑 ignore；本機驗收→首 commit→local bare push→clone，100755 與 wrapper 直接執行；7 個負向測試，未呼叫模型或 GitHub')


def sync_mode_problems(sp, dest, tmp):
    """同一套斷言用於現行實作及移除 copymode 的負向變異。"""
    from unittest import mock
    import stat
    def must(args, cwd=None):
        result = run(args, cwd=cwd)
        if result.returncode:
            raise RuntimeError('%r: %s' % (args, result.stderr))
        return result
    work = tmp / 'mode-upgrade'
    work.mkdir(parents=True, exist_ok=True)
    wrapper = work / '.claude/hooks/ag-wrap.sh'
    wrapper.parent.mkdir(parents=True, exist_ok=True)
    original = read_lf(dest / '.claude/hooks/ag-wrap.sh')
    write_lf(wrapper, original + '\n# before upgrade\n')
    write_lf(wrapper.parent / 'git-freshness.sh', '#!/bin/sh\necho mode-upgrade-ok\n')
    wrapper.chmod(0o755)
    must(['git', 'init', '-q', work.as_posix()])
    must(['git', 'config', 'core.filemode', 'true'], work)
    must(['git', 'add', '.'], work)
    must(['git', 'update-index', '--chmod=+x', '.claude/hooks/ag-wrap.sh'], work)
    must(['git', 'commit', '-qm', 'before mode upgrade'], work)
    plan = sp.Plan()
    plan.update(wrapper, '.claude/hooks/ag-wrap.sh', original + '\n# after upgrade\n')
    bad = []
    copier = sp.shutil.copymode
    with mock.patch.object(sp.shutil, 'copymode', wraps=copier) as copied:
        done, error = sp.apply_plan(plan)
        if copied.call_args_list != [mock.call(wrapper, wrapper.with_name('ag-wrap.sh.sync-tmp'))]:
            bad.append('替換前未複製既存 mode')
    if error or done != ['.claude/hooks/ag-wrap.sh'] or '# after upgrade' not in read_lf(wrapper):
        bad.append('升級內容未完成')
    if os.name == 'posix':
        if stat.S_IMODE(wrapper.stat().st_mode) != 0o755:
            bad.append('0755 升級後 mode 改變')
        diff = must(['git', 'diff', '--summary'], work).stdout
        if 'mode change' in diff:
            bad.append('Git 出現 mode change')
        try:
            result = run([str(wrapper), 'git-freshness.sh'], cwd=work)
            if result.returncode or 'mode-upgrade-ok' not in result.stdout:
                bad.append('升級後原始 wrapper 無法直接執行')
        except OSError:
            bad.append('升級後原始 wrapper 拒絕執行')
        ordinary = work / 'config.txt'
        write_lf(ordinary, 'before')
        ordinary.chmod(0o640)
        config_plan = sp.Plan()
        config_plan.update(ordinary, 'config.txt', 'after')
        if sp.apply_plan(config_plan)[1] or stat.S_IMODE(ordinary.stat().st_mode) != 0o640:
            bad.append('一般檔案 0640 未保留')
    before = wrapper.read_bytes()
    with mock.patch.object(sp.shutil, 'copymode', side_effect=OSError('fixture denied')):
        done, error = sp.apply_plan(plan)
    if done or not error or wrapper.read_bytes() != before:
        bad.append('權限複製失敗仍替換原檔或回報成功')
    # 新依賴沒有原檔，應照原本的建立流程，不向不存在的路徑複製權限。
    missing = work / 'new.cmd'
    new_plan = sp.Plan()
    new_plan.update(missing, 'new.cmd', 'new')
    with mock.patch.object(sp.shutil, 'copymode', side_effect=OSError('must not copy')):
        if sp.apply_plan(new_plan)[1] or read_lf(missing) != 'new':
            bad.append('新增依賴被既存 mode 流程擋住')
    return bad


def step_sync_mode(dest, tmp):
    """2026-11-03：同步升級要保留 mode；Windows 只驗呼叫與失敗契約。"""
    import sync_project as sp
    import types
    bad = sync_mode_problems(sp, dest, tmp / 'current-mode')
    source = read_lf(ROOT / 'tools/sync_project.py')
    mutant = types.ModuleType('sync_mode_mutant')
    mutant.__file__ = str(ROOT / 'tools/sync_project.py')
    exec(compile(source.replace('shutil.copymode(path, tmp)', 'pass'), mutant.__file__, 'exec'), mutant.__dict__)
    if not sync_mode_problems(mutant, dest, tmp / 'mutant-mode'):
        bad.append('移除 mode 保留的負向變異未失敗')
    record('FAIL' if bad else 'OK', '同步升級 mode', '；'.join(bad) if bad else
           ('POSIX 0755／0640、原始 wrapper 直接執行、Git 無 mode diff；' if os.name == 'posix' else
            'Windows 僅驗 copymode 呼叫契約（非 POSIX 實測）；') +
           '複製失敗保留原檔、新增依賴、移除保留的負向變異')


def step_architecture_summary(dest):
    def problems(docs):
        bad = []
        for name, text in docs.items():
            rows = [line for line in text.splitlines() if line.startswith('|')]
            pointers = [line for line in rows if 'CLAUDE.md' in line and 'GEMINI.md' in line]
            if not pointers or any('import' not in line or '文字指標' not in line for line in pointers):
                bad.append(name + ' 未區分 Claude import 與 Gemini 文字指標')
            if name == 'repo':
                prompts = [line for line in rows if line.startswith('| 3.4 |')]
                if not prompts or any('收工交棒／開工接棒' not in line for line in prompts):
                    bad.append('README prompt 摘要與現行命名分岔')
        return bad
    docs = {'repo': read_lf(ROOT / 'ARCHITECT.md'), 'generated': read_lf(dest / 'ARCHITECT.md')}
    bad = problems(docs)
    for name in docs:
        mutant = dict(docs)
        mutant[name] = docs[name].replace('import', '只有標題不同')
        if not problems(mutant):
            bad.append('負向測試未抓到指標摘要退化：' + name)
    mutant = dict(docs)
    mutant['repo'] = docs['repo'].replace('收工交棒／開工接棒', 'A／B')
    if not problems(mutant):
        bad.append('負向測試未抓到 prompt 字母退化')
    # 反向保險：表格裡的版本號（v3.4）不是範本 3.4，不得被當成 prompt 那一列。
    mutant = dict(docs)
    mutant['repo'] = docs['repo'].replace('| 3.4 | `README.md`', '| 3.4x | `README.md`')
    if '| 3.4x |' not in mutant['repo']:
        bad.append('反向保險失效：ARCHITECT 沒有「| 3.4 | `README.md`」那一列')
    elif [p for p in problems(mutant) if 'prompt' in p] != ['README prompt 摘要與現行命名分岔']:
        bad.append('反向保險失效：缺了範本 3.4 那一列時沒有被判出來')
    record('FAIL' if bad else 'OK', '結構摘要一致性', '；'.join(bad) if bad else
           '本 repo 與生成 ARCHITECT 區分 import／文字指標、prompt 用收工／開工（認的是範本編號欄，不是全行出現 3.4）；三個負向測試＋一個反向保險')


def v2_report_problem(report):
    """Reject an empty/partial/optimistic report, including a false ready claim."""
    try:
        tests, findings = report['tests'], report['findings']
        if report['harness_passed'] is not True or report['strict_ready'] is not False:
            return 'P0 回歸失敗或不當宣稱 strict ready'
        if tests['run'] < 1 or any(tests[key] != 0 for key in ('failed', 'errors', 'skipped')):
            return '測試為空、失敗或有未驗證項'
        if not isinstance(tests.get('needs_uv'), list):
            return '報告沒列出 A4 不跑的測試檔'
        expected = {'same-uid-journal-bypass', 'direct-git-object-bypass',
                    'running-context-still-uses-old-premise'}
        if len(findings) != len(expected) or {row['id'] for row in findings} != expected:
            return '缺少架構反例'
        if any(row['counterexample_observed'] is not True or row['requirement_result'] != '不通過'
               for row in findings):
            return '反例未重現或把需求誤報通過'
        if report['isolation_probe']['result'] not in ('通過', '不通過', '未驗證'):
            return 'OS 探針未揭露結果'
        if report['supervisor_probe']['result'] != '通過':
            return '合成上下文替換探針未通過'
        if report['broker_probe']['result'] not in ('通過', '未驗證'):
            return '管道身分／管理分權探針失敗'
        if report['managed_probe']['result'] not in ('通過', '未驗證'):
            return '受管前提切換／outbox 探針失敗'
    except (KeyError, TypeError):
        return 'v2 報告缺失或無效'
    return ''


def step_v2():
    """P0 regression success is NOT strict-mode or requirement acceptance."""
    result = run([sys.executable, '-X', 'utf8', str(ROOT / 'tools/verify_v2.py'), '--json'], cwd=ROOT)
    try:
        report = json.loads(result.stdout)
        problem = v2_report_problem(report)
        valid = result.returncode == 0 and not problem
        needs_uv = report['tests'].get('needs_uv', [])
        detail = problem or ('%s 個契約／索引測試%s；三個預期反例重現；strict_ready=%s；'
                  'OS 子程序探針=%s、管道分權=%s、受管前提切換／outbox=%s（非桌面工具驗收）' % (
                      report['tests']['run'],
                      '（另有 %d 個測試檔要外部套件，A4 不跑、要 uv run pytest：%s）' % (
                          len(needs_uv), '、'.join(needs_uv)) if needs_uv else '',
                      report['strict_ready'], report['isolation_probe']['result'],
                      report['broker_probe']['result'], report['managed_probe']['result']))
    except (ValueError, KeyError, TypeError):
        valid, detail = False, 'v2 報告缺失或無效'
    record('OK' if valid else 'FAIL', 'v2 P0 原型回歸（非需求達標）', detail)


SPLIT_BASELINE = ROOT / 'tools/skill_split_baseline.json'
# 入口必須自己帶著的句子：停止條件、禁令與每則訊息都適用的命名規則。這些不能只留在
# 模式檔或理由檔——模型沒去讀模式檔時，入口是最後一道。
ENTRY_MUST = (
    '不要憑空建立交接檔案', '`reset --hard`', '`push --force`', '自行 `stash`',
    '接棒時 ahead-only', 'fetch 失敗', 'A2.5 偵測到別台機器的「工作中」標記',
    '功能分支要併進 `main`', '憑證缺失', 'HANDOFF 沒授權的破壞性操作', '建 GitHub repo 與第一次 push',
    'A1–A4 不修改專案檔案', '~/.claude/skills/handoff/', '找不到模式檔就停下回報',
    '每則使用者新訊息都先看 session 狀態', '續聊要改檔前重新走 A1–A5', '必須有 `session：` 一行',
)
MODE_A_MUST = (
    '] 全綠 ', 'bash .claude/hooks/git-freshness.sh', '不要自己判斷「大概沒事」', '`mode-a-stop.md`',
    '切換後重做 A1', '都不能寫成通過',
    'session：㊣　<YYMMDDHH｜主題>｜工作中｜交棒<N>次（已改）／不適用：<本工具不能改名>；交棒<N>次',
    '只讀、只問問題的 session 不寫開工標記', '**工具欄不能省**', '遠端 SHA 跟 A1 記下的不同就停',
    'push 失敗就不是「已標記」', '不是互斥鎖',
)


def line_key(line):
    return hashlib.sha256(line.strip().encode('utf-8')).hexdigest()[:16]


def skill_split_problems(files, version, whole, baseline):
    """2026-11-10（決策書 F22／Q9）：handoff skill 拆成六個檔之後要守的東西。

    files 是 {檔名: 內容}。拆檔最怕三件事，而且都沒有徵兆：入口指向不存在的檔、六個檔
    版本不一（同步只寫了一半）、濃縮時把停止條件或理由弄丟。
    """
    missing = [name for name in SKILL_FILES if name not in files]
    if missing:
        return ['缺 skill 檔：' + '、'.join(missing)]
    bad = []
    entry = files['SKILL.md']
    for name in SKILL_FILES[1:]:
        if '`%s`' % name not in entry:
            bad.append('入口沒有指到 ' + name)
    for name in SKILL_FILES:
        if SKILL_DIR + name not in whole:
            bad.append(name + ' 不在 sync_project 的 WHOLE')
        mark = re.search(r'source: PROJECT-BOOTSTRAP\.md v([0-9][0-9.-]*)', files[name])
        if not mark:
            bad.append(name + ' 缺 source 版本標記')
        elif mark[1] != version:
            bad.append('%s 的版本標記 v%s 與 VERSION %s 不同' % (name, mark[1], version))
    size = sum(len(files[name]) for name in SKILL_ROUTINE)
    if size > SKILL_ROUTINE_LIMIT:
        bad.append('常態必讀（入口＋mode-a.md）%d 字元，超過 %d' % (size, SKILL_ROUTINE_LIMIT))
    bad.extend('入口缺：' + token for token in ENTRY_MUST if token not in entry)
    bad.extend('mode-a.md 缺：' + token for token in MODE_A_MUST if token not in files['mode-a.md'])
    have = {line_key(line) for text in files.values() for line in text.split('\n') if line.strip()}
    rewritten = baseline['rewritten']
    lost = [key for key in baseline['lines'] if key not in have and key not in rewritten]
    if lost:
        bad.append('拆分前的 SKILL.md 有 %d 行不在任何一個檔、也不在已改寫清單（%s…）' % (len(lost), lost[0]))
    if any(key not in baseline['lines'] or not str(note).strip() for key, note in rewritten.items()):
        bad.append('已改寫清單有不屬於舊文本的行，或沒寫去處')
    return bad


def step_skill_split(dest):
    import sync_project as syncer
    files = {name: read_lf(dest / (SKILL_DIR + name)) for name in SKILL_FILES
             if (dest / (SKILL_DIR + name)).is_file()}
    version = read_lf(ROOT / 'VERSION').strip()
    baseline = json.loads(read_lf(SPLIT_BASELINE))
    bad = skill_split_problems(files, version, syncer.WHOLE, baseline)
    size = sum(len(files.get(name, '')) for name in SKILL_ROUTINE)

    def mutated(name, text):
        copy = dict(files)
        copy[name] = text
        return copy
    cases = []
    if not bad:
        cases.append(('少一個模式檔', {k: v for k, v in files.items() if k != 'mode-b.md'}, version, syncer.WHOLE, baseline))
        cases.append(('入口不再指到 reasons.md', mutated('SKILL.md', files['SKILL.md'].replace('`reasons.md`', '理由檔')),
                      version, syncer.WHOLE, baseline))
        cases.append(('模式檔不在 WHOLE', files, version,
                      tuple(rel for rel in syncer.WHOLE if not rel.endswith('mode-a-stop.md')), baseline))
        cases.append(('只有一個檔的版本標記不同',
                      mutated('mode-0.md', files['mode-0.md'].replace('md v' + version, 'md v2000-01-01', 1)),
                      version, syncer.WHOLE, baseline))
        cases.append(('模式檔沒有版本標記',
                      mutated('reasons.md', files['reasons.md'].replace('source: PROJECT-BOOTSTRAP.md v', 'from v', 1)),
                      version, syncer.WHOLE, baseline))
        cases.append(('入口灌到超過上限', mutated('SKILL.md', files['SKILL.md'] + '字' * (SKILL_ROUTINE_LIMIT - size + 1)),
                      version, syncer.WHOLE, baseline))
        for token in ENTRY_MUST:
            cases.append(('入口拿掉 ' + token, mutated('SKILL.md', files['SKILL.md'].replace(token, '')),
                          version, syncer.WHOLE, baseline))
        for token in MODE_A_MUST:
            cases.append(('mode-a.md 拿掉 ' + token, mutated('mode-a.md', files['mode-a.md'].replace(token, '')),
                          version, syncer.WHOLE, baseline))
        # 理由檔少一行（任挑「反例」裡的一條）：覆蓋率必須擋下，理由可以搬不能消失。
        victim = next((line for line in files['reasons.md'].split('\n') if line.startswith('- ❌ 開工沒 fetch')), '')
        cases.append(('理由檔刪掉一條反例', mutated('reasons.md', files['reasons.md'].replace(victim + '\n', '', 1) if victim else files['reasons.md']),
                      version, syncer.WHOLE, baseline))
        ghost = dict(baseline, rewritten=dict(baseline['rewritten'], **{'0' * 16: '憑空多一筆'}))
        cases.append(('已改寫清單混進不存在的行', files, version, syncer.WHOLE, ghost))
        unexplained = dict(baseline, rewritten={key: '' for key in baseline['rewritten']})
        cases.append(('已改寫清單沒寫去處', files, version, syncer.WHOLE, unexplained))
    for name, *args in cases:
        if not skill_split_problems(*args):
            bad.append('負向測試未擋：' + name)
    record('FAIL' if bad else 'OK', 'skill 拆分', '；'.join(bad) if bad else
           '六個檔齊全、同版本、都在同步清單；常態必讀（入口＋mode-a.md）%d／%d 字元；入口 %d 條、mode-a %d 條必備句；'
           '拆分前 %d 行逐字留存、%d 行列為已改寫；%d 個負向測試（不代表模型會去讀模式檔）'
           % (size, SKILL_ROUTINE_LIMIT, len(ENTRY_MUST), len(MODE_A_MUST),
              len(baseline['lines']) - len(baseline['rewritten']), len(baseline['rewritten']), len(cases)))


RULE_MAP_HEAD = '## 規則 → 理由在哪（對照表）'
RULE_MAP_SOURCES = ('SKILL.md', 'mode-a.md', 'mode-a-stop.md', 'mode-b.md', 'mode-0.md')
RULE_MAP_WORDS = ('本段內文', '沒有寫下理由', '分節標題')


def skill_headings(text):
    """## 與 ### 段落標題，略過圍欄裡的（mode-b.md 的 HANDOFF 範本也有 ## 標題）。"""
    heads, fence = [], None
    for line in text.split('\n'):
        run = re.match(r'(`{3,})', line)
        if run:
            if fence is None:
                fence = run[1]
            elif line.strip() == fence:
                fence = None
            continue
        if fence is None and re.match(r'#{2,3} ', line):
            heads.append(line.split(' ', 1)[1].strip())
    return heads


def rule_map_problems(files):
    """2026-11-10（決策書 Q17 (b)）：reasons.md 的對照表要涵蓋入口與四個模式檔的每個段落。

    只查涵蓋與指向：左欄每個段落都在、沒有多出不存在的段落；右欄指到的段落真的存在，
    或是三個固定字樣之一。理由寫得對不對、「本段內文」是不是真的有理由，這裡看不出來。
    """
    reasons = files.get('reasons.md', '')
    if RULE_MAP_HEAD not in reasons:
        return ['reasons.md 沒有「規則 → 理由在哪」對照表']
    section = reasons.split(RULE_MAP_HEAD, 1)[1].split('\n## ', 1)[0]
    heads = {name: skill_headings(files.get(name, '')) for name in RULE_MAP_SOURCES + ('reasons.md',)}
    rows, bad = {}, []
    for line in section.split('\n'):
        if not line.startswith('| ') or line.startswith('| 規則（'):
            continue
        cells = [cell.strip() for cell in line.strip().strip('|').split(' | ')]
        if len(cells) != 2:
            bad.append('對照表格式不對：' + line[:40])
            continue
        if cells[0] in rows:
            bad.append('對照表重複列：' + cells[0])
        rows[cells[0]] = [item.strip() for item in cells[1].split('<br>') if item.strip()]
    for name in RULE_MAP_SOURCES:
        for head in heads[name]:
            if '%s § %s' % (name, head) not in rows:
                bad.append('對照表缺：%s § %s' % (name, head))
    for left, targets in rows.items():
        name, _, head = left.partition(' § ')
        if name not in RULE_MAP_SOURCES or head not in heads[name]:
            bad.append('對照表左欄指到不存在的段落：' + left)
        if not targets:
            bad.append('對照表沒寫理由在哪：' + left)
        for target in targets:
            if target in RULE_MAP_WORDS:
                continue
            name, sep, head = target.partition(' § ')
            if (not sep or name not in heads or head not in heads[name]
                    or '## ' + head == RULE_MAP_HEAD):
                bad.append('對照表右欄指到不存在的段落：' + target)
    return bad


def step_skill_rule_map(dest):
    files = {name: read_lf(dest / (SKILL_DIR + name)) for name in SKILL_FILES
             if (dest / (SKILL_DIR + name)).is_file()}
    bad = rule_map_problems(files)
    rows = sum(len(skill_headings(files.get(name, ''))) for name in RULE_MAP_SOURCES)

    def mutated(name, old, new):
        copy = dict(files)
        if old not in copy[name]:
            return None
        copy[name] = copy[name].replace(old, new, 1)
        return copy
    cases = []
    if not bad:
        a2_row = '| mode-a.md § A2 站對分支 | mode-a-stop.md § A2 站對分支 |\n'
        cases = [
            ('少一列', mutated('reasons.md', a2_row, '')),
            ('模式檔段落改名', mutated('mode-b.md', '### B8 發布', '### B8 發佈')),
            ('入口多一段沒列', mutated('SKILL.md', '## 全程禁令', '## 新規則\n\n## 全程禁令')),
            ('右欄指錯段落', mutated('reasons.md', a2_row, a2_row.replace('§ A2 站對分支 |\n', '§ A2 換分支 |\n'))),
            ('右欄空白', mutated('reasons.md', a2_row, '| mode-a.md § A2 站對分支 |  |\n')),
            ('重複列', mutated('reasons.md', a2_row, a2_row * 2)),
            ('右欄指到對照表自己', mutated('reasons.md', a2_row, a2_row.replace(
                'mode-a-stop.md § A2 站對分支 |', 'reasons.md § 規則 → 理由在哪（對照表） |'))),
            ('沒有對照表', mutated('reasons.md', RULE_MAP_HEAD, '## 別的標題')),
        ]
        for name, copy in cases:
            if copy is None or not rule_map_problems(copy):
                bad.append('負向測試未擋：' + name)
    record('FAIL' if bad else 'OK', 'skill 規則對照表', '；'.join(bad) if bad else
           'reasons.md 對照表涵蓋入口與四個模式檔共 %d 個段落，右欄都指到存在的段落；%d 個負向測試'
           '（只查涵蓋與指向，不判斷理由寫得對不對）' % (rows, len(cases)))


def step_sync_skill_parts(dest, tmp):
    """舊專案只有單檔 SKILL.md：同步要補上五個新檔，而且入口最後才寫（2026-11-10）。

    只看 sync() 算出來的計畫，不寫入、不碰同步資格檢查（那由「同步資格」等項目守）。
    """
    import sync_project as syncer
    parts = [SKILL_DIR + name for name in SKILL_FILES if name != 'SKILL.md']
    entry = SKILL_DIR + 'SKILL.md'

    def planned(project, **kw):
        plan = syncer.sync(project, dest, **kw)
        return [rel for _, _, rel in plan.writes], '\n'.join(plan.msgs)
    old = tmp / 'parts-old'
    (old / SKILL_DIR).mkdir(parents=True)
    write_lf(old / entry, '---\nname: handoff\ndescription: old\n---\n\n單檔舊版\n')
    write_lf(old / (SKILL_DIR + 'notes-local.md'), '專案就地加的檔\n')
    writes, msgs = planned(old)
    bad = []
    if any(rel not in writes for rel in parts):
        bad.append('有入口的舊專案沒有補齊五個新檔')
    if entry not in writes or any(writes.index(rel) > writes.index(entry) for rel in parts if rel in writes):
        bad.append('入口不是 skill 檔裡最後寫的')
    if 'EXTRA' not in msgs or 'notes-local.md' not in msgs:
        bad.append('skill 目錄裡不認得的檔沒有被列出來')
    # 沒有這套 skill 的專案不能被補裝；Codex 限定同步也不能動 skill。
    bare = tmp / 'parts-bare'
    bare.mkdir()
    write_lf(bare / 'README.md', 'x\n')
    writes, _ = planned(bare)
    if any(rel.startswith(SKILL_DIR) for rel in writes):
        bad.append('沒有 handoff skill 的專案被補裝了模式檔')
    writes, _ = planned(old, codex_only=True)
    if any(rel.startswith(SKILL_DIR) for rel in writes):
        bad.append('Codex 限定同步動了 skill 目錄')
    # 負向：WHOLE 裡沒有模式檔時，這項檢查必須看得出「沒補齊」。
    with patch.object(syncer, 'WHOLE', tuple(rel for rel in syncer.WHOLE if rel not in syncer.SKILL_PARTS)):
        writes, _ = planned(old)
    if all(rel in writes for rel in parts):
        bad.append('負向測試未重現：WHOLE 拿掉模式檔後仍顯示補齊')
    record('FAIL' if bad else 'OK', '同步補齊模式檔', '；'.join(bad) if bad else
           '只有單檔的舊專案會補上五個新檔、入口最後寫、不認得的檔列為 EXTRA；沒有 skill 的專案與 Codex 限定同步不動；1 個負向測試')


def step_all_green(dest, tmp):
    """開場 hook 的「全綠」行（2026-11-10，F22）：全部條件成立才印，少一項就不能印。

    這一行讓正常接棒可以不讀完整判讀表，所以它印錯的方向只有一個是危險的——不該綠的時候綠了。
    每個條件各用一個真 Git fixture 打破一次；兩支 hook（部署範本與本 repo 自己的）都跑。
    """
    bash = find_bash()
    if not bash:
        record('SKIP', '全綠行', '缺少可用 bash')
        return
    scripts = [('部署 hook', read_lf(dest / '.claude/hooks/git-freshness.sh')),
               ('本 repo hook', read_lf(ROOT / '.claude/hooks/repo-git-check.sh'))]
    free = '# HANDOFF\n\n- **工作中**：無（已交棒）\n'
    counter = [0]

    def git(args, cwd=None):
        r = run(['git', *args], cwd=cwd)
        if r.returncode:
            raise RuntimeError('Git fixture 失敗：' + ' '.join(args) + ' ' + r.stderr)
        return r.stdout.strip()

    def fixture(handoff=free):
        counter[0] += 1
        base = tmp / ('green-%d' % counter[0])
        origin, work = base / 'origin.git', base / 'work'
        base.mkdir()
        git(['init', '-q', '--bare', str(origin)])
        git(['init', '-q', '-b', 'main', str(work)])
        write_lf(work / 'HANDOFF.md', handoff)
        git(['add', 'HANDOFF.md'], work)
        git(['commit', '-qm', 'init'], work)
        git(['remote', 'add', 'origin', str(origin)], work)
        git(['push', '-qu', 'origin', 'main'], work)
        return origin, work

    def green_line(source, work):
        path = tmp / 'green-probe.sh'
        write_lf(path, source)
        out = run([bash, str(path)], cwd=work, env=tool_env(BOOTSTRAP_VERSION_CHECK='off')).stdout
        return next((line for line in out.splitlines() if '] 全綠 ' in line), '')

    def dirty(origin, work):
        write_lf(work / 'untracked.txt', 'x\n')

    def ahead(origin, work):
        write_lf(work / 'HANDOFF.md', free + '\n本機多一個 commit\n')
        git(['commit', '-qam', 'local'], work)

    def behind(origin, work):
        peer = work.parent / 'peer'
        git(['clone', '-q', '-b', 'main', str(origin), str(peer)])
        write_lf(peer / 'other.txt', 'x\n')
        git(['add', 'other.txt'], peer)
        git(['commit', '-qm', 'remote'], peer)
        git(['push', '-q', 'origin', 'main'], peer)

    def wrong_upstream(origin, work):
        git(['push', '-q', 'origin', 'main:other'], work)
        git(['fetch', '-q', 'origin'], work)
        git(['branch', '-q', '-u', 'origin/other'], work)

    def detached(origin, work):
        git(['checkout', '-q', '--detach'], work)

    def fetch_fails(origin, work):
        git(['remote', 'set-url', 'origin', str(work.parent / 'missing.git')], work)

    def remote_handoff(text):
        def change(origin, work):
            write_lf(work / 'HANDOFF.md', text)
            git(['commit', '-qam', 'handoff'], work)
            git(['push', '-q', 'origin', 'main'], work)
        return change

    breakers = (
        ('未提交變更', dirty), ('ahead', ahead), ('behind', behind),
        ('upstream 不是 origin/<分支>', wrong_upstream), ('detached HEAD', detached), ('fetch 失敗', fetch_fails),
        ('有人佔用', remote_handoff('# HANDOFF\n\n- **工作中**：`other-box` ／ `Codex CLI`，2026-11-10 09:00 (+08) 開工\n')),
        ('兩列工作中', remote_handoff(free + '- **工作中**：無（已交棒）\n')),
        ('沒有工作中欄位', remote_handoff('# HANDOFF\n\n沒有欄位\n')),
        ('任務名含「無」但有人佔用', remote_handoff('# HANDOFF\n\n- **工作中**：`box` ／ `Claude Code` ／ `㊣　26111009｜修無效連結｜工作中｜交棒0次`\n')),
    )
    issues = []
    try:
        for name, source in scripts:
            origin, work = fixture()
            line = green_line(source, work)
            sha = git(['rev-parse', 'origin/main'], work)
            if not line or 'branch=main' not in line or 'origin=' + sha not in line:
                issues.append(name + ' 正常狀態沒有印全綠行或缺分支／SHA')
            for label, breaker in breakers:
                origin, work = fixture()
                breaker(origin, work)
                if green_line(source, work):
                    issues.append('%s 在「%s」時仍印全綠' % (name, label))
            # 儀器自檢：把 dirty 條件從腳本拿掉，dirty fixture 就必須看得到全綠行。
            weakened = source.replace(' || [ "$dirty" -gt 0 ]; then green=0; fi', '; then green=0; fi')
            origin, work = fixture()
            dirty(origin, work)
            if weakened == source or not green_line(weakened, work):
                issues.append(name + ' 負向測試未重現：拿掉 dirty 條件後應該印出全綠')
            unfree = source.replace('free=0\n', 'free=1\n', 1)
            origin, work = fixture()
            remote_handoff('# HANDOFF\n\n- **工作中**：`other-box` ／ `Codex CLI`\n')(origin, work)
            if unfree == source or not green_line(unfree, work):
                issues.append(name + ' 負向測試未重現：占用判定失效後應該印出全綠')
    except RuntimeError as e:
        issues.append(str(e))
    record('FAIL' if issues else 'OK', '全綠行', '；'.join(issues) if issues else
           '兩支 hook 實跑：正常狀態印出含分支與 origin SHA 的全綠行；%d 種不正常狀態都不印；'
           '拿掉 dirty 或占用條件的腳本會被看出來（只證明 hook 的判定，不證明模型照它走）' % len(breakers))


def run_checks(dest, tmp):
    work = None
    seen = step_regenerate(dest) and step_fill(dest)
    if seen and step_check_docs(dest):
        step_placeholder_list(dest, seen)
        step_placeholder_guard(dest)
        step_date_guard(dest)
        step_busy_tool_guard(dest)
        step_deploy_shape(dest)
        step_antigravity(dest)
        step_codex_windows(dest, tmp)
        step_wiring_cwd(dest, tmp)
        step_portability(dest)
        step_bash32_multibyte(dest)
        hooked = step_hook(dest, tmp)
        work = hooked if isinstance(hooked, pathlib.Path) else None
        step_busy(dest, work)
        step_repo_busy(work)
        step_version_check(work)
        step_rename_line(dest)
        step_session_resume(dest)
    step_eol(dest)
    step_self()
    step_action_rules(tmp)
    step_repo_handoff()
    step_reason_links()
    if seen:
        step_source_exceptions(dest, tmp)
        step_handoff_parity(dest)
        step_document_parity(dest, tmp)
        step_document_policy_parity(dest, tmp)
        step_source_staged_parity(dest, tmp)
        step_handoff_flow_parity(dest, tmp)
    step_sync_coverage(dest)
    step_sync_self_guard()
    step_sync_safety(tmp)
    step_misc(dest, work)
    step_zip_gate(tmp)
    step_flow_contract(dest, tmp)
    step_core_priority(dest, tmp)
    step_coordination(dest)
    step_skill_split(dest)
    step_skill_rule_map(dest)
    step_sync_skill_parts(dest, tmp)
    step_all_green(dest, tmp)
    step_sync_scope(dest, tmp)
    step_sync_mode(dest, tmp)
    step_architecture_summary(dest)
    step_deployment_lifecycle(tmp)
    step_v2()
    step_p1_layout()
    step_kit_source()


# 鎖檔裡的套件名 → import 名，名字不一樣的才列
P1_IMPORT_NAMES = {'attrs': ('attr', 'attrs'), 'markdown-it-py': ('markdown_it',),
                   'pytest': ('pytest', '_pytest'), 'rpds-py': ('rpds',)}
# A4 會跑到的程式：只能用標準函式庫，沒裝 uv 的機器也要能驗
P1_STDLIB_ONLY = ('tools', 'src/project_bootstrap')
# 2026-11-11 P1 第四片：只有這幾支可以用鎖檔裡的套件。其他程式不能 import 它們（A4 才碰不到），
# import 它們的測試要以 raise unittest.SkipTest('needs …') 開頭：verify_v2 憑這個標記不跑它們並在報告列出。
# 要多一支就加在這裡，這是刻意留的關卡。
P1_EXTRAS = ('src/project_bootstrap/mdlinks.py', 'src/project_bootstrap/schema_check.py')


def p1_section(text, header):
    """回傳 TOML 某個 [header] 底下的 key = value 行（只認本 repo 自己寫的簡單格式）。"""
    body = text.split('\n[' + header + ']\n', 1)
    if len(body) != 2:
        return None
    rows = {}
    for line in body[1].split('\n'):
        if line.startswith('['):
            break
        match = re.match(r'([A-Za-z0-9_.-]+)\s*=\s*(.+)$', line)
        if match:
            rows[match[1]] = match[2].strip()
    return rows


def p1_imports(text):
    """頂層 import 的完整模組名；相對 import 不算。"""
    ast = __import__('ast')
    names = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            module = node.module or ''
            names.append(module)
            names += ['%s.%s' % (module, alias.name) for alias in node.names]
    return names


def p1_layout_problems(pyproject, lock, sources, tests=None, extras=P1_EXTRAS):
    """2026-11-11 P1 第一片：開發骨架的鎖定與 A4 免安裝。

    只查：最低版本是 3.12、還不是可安裝的包；pyproject 宣告的每個依賴都在 uv.lock；
    鎖檔每個外部套件都有 sha256；每個鎖住的套件都登記了授權；A4 會跑到的程式不 import
    鎖檔裡的套件。授權字串對不對、鎖檔是不是 uv 最新解出來的，這裡看不出來（後者用 uv lock --check）。
    第四片起：`extras` 列的模組可以用鎖檔套件，但別的程式不能 import 它們，import 它們的測試
    要在缺套件時 SkipTest。只看靜態 import，`importlib` 動態載入看不到。
    """
    bad = []
    project = p1_section(pyproject, 'project') or {}
    if project.get('requires-python') != '">=3.12"':
        bad.append('pyproject 的 requires-python 不是 >=3.12')
    if (p1_section(pyproject, 'tool.uv') or {}).get('package') != 'false':
        bad.append('pyproject 沒寫 [tool.uv] package = false（打包屬 P2）')
    declared = set(re.findall(r'^\s+"([A-Za-z0-9_.-]+)[^"]*",$', pyproject, re.M))
    packages = {}
    for block in lock.split('\n[[package]]\n')[1:]:
        name = re.search(r'^name = "([^"]+)"', block, re.M)
        if name:
            packages[name[1]] = block
    if not declared:
        bad.append('pyproject 沒有宣告任何依賴')
    for name in sorted(declared - set(packages)):
        bad.append('依賴沒進 uv.lock：' + name)
    licenses = p1_section(pyproject, 'tool.project-bootstrap.licenses') or {}
    external = {name: block for name, block in packages.items()
                if 'source = { registry = ' in block}
    if 'project-bootstrap' not in packages:
        bad.append('uv.lock 沒有本專案自己')
    for name, block in sorted(external.items()):
        if 'hash = "sha256:' not in block:
            bad.append('鎖檔套件沒有 sha256：' + name)
        if name not in licenses:
            bad.append('鎖檔套件沒登記授權：' + name)
    for name in sorted(set(licenses) - set(external)):
        bad.append('授權表有鎖檔沒有的套件：' + name)
    forbidden = set()
    for name in packages:
        forbidden.update(P1_IMPORT_NAMES.get(name, (name.replace('-', '_'),)))
    forbidden.discard('project_bootstrap')
    extra_modules = {path[len('src/'):-len('.py')].replace('/', '.') for path in extras}
    for path in extras:
        if path not in sources:
            bad.append('P1_EXTRAS 列的模組不存在：' + path)
    for kind, files in (('程式', sources), ('測試', tests or {})):
        for path, text in sorted(files.items()):
            try:
                names = p1_imports(text)
            except SyntaxError:
                bad.append('解析失敗：' + path)
                continue
            reaches = sorted({n for n in names if n in extra_modules or n.rsplit('.', 1)[0] in extra_modules})
            if kind == '程式' and path not in extras:
                for name in names:
                    if name.split('.')[0] in forbidden:
                        bad.append('A4 會跑到的程式 import 了外部套件：%s（%s）' % (path, name))
                if reaches:
                    bad.append('A4 會跑到的程式 import 了用外部套件的模組：%s（%s）' % (path, '、'.join(reaches)))
            if kind == '測試' and reaches and "raise unittest.SkipTest('needs " not in text:
                bad.append('測試 import 用外部套件的模組卻沒有缺套件時 SkipTest：' + path)
    return bad


def step_p1_layout():
    try:
        pyproject = read_lf(ROOT / 'pyproject.toml')
        lock = read_lf(ROOT / 'uv.lock')
    except OSError as exc:
        record('FAIL', 'P1 開發骨架', '讀不到 pyproject.toml 或 uv.lock：%s' % exc)
        return
    sources = {}
    for folder in P1_STDLIB_ONLY:
        for path in sorted((ROOT / folder).glob('*.py')):
            if not path.name.startswith('test_'):
                sources[path.relative_to(ROOT).as_posix()] = read_lf(path)
    tests = {path.relative_to(ROOT).as_posix(): read_lf(path) for path in sorted((ROOT / 'tests').glob('test_*.py'))}
    bad = p1_layout_problems(pyproject, lock, sources, tests)
    cases = []
    if not bad:
        first = sorted(path for path in sources if path not in P1_EXTRAS)[0]
        skip_test = next(path for path, text in tests.items() if 'project_bootstrap.mdlinks' in text)

        def lock_block(name, change):
            start = lock.index('\n[[package]]\nname = "%s"\n' % name)
            end = lock.find('\n[[package]]\n', start + 1)
            end = len(lock) if end == -1 else end
            return lock[:start] + change(lock[start:end]) + lock[end:]
        cases = [
            ('依賴沒進鎖檔', p1_layout_problems(pyproject, lock_block('jsonschema', lambda b: ''), sources)),
            ('鎖檔少 sha256', p1_layout_problems(pyproject, lock_block(
                'attrs', lambda b: b.replace('sha256:', 'md5:')), sources)),
            ('授權表少一個', p1_layout_problems(pyproject.replace('\npytest = "MIT"\n', '\n', 1), lock, sources)),
            ('最低版本改 3.11', p1_layout_problems(pyproject.replace('">=3.12"', '">=3.11"', 1), lock, sources)),
            ('拿掉 package = false', p1_layout_problems(pyproject.replace('package = false', '', 1), lock, sources)),
            ('驗證器 import jsonschema', p1_layout_problems(pyproject, lock, dict(
                sources, **{first: sources[first] + '\nimport jsonschema\n'}))),
            ('驗證器 from markdown_it import', p1_layout_problems(pyproject, lock, dict(
                sources, **{first: sources[first] + '\nfrom markdown_it.token import Token\n'}))),
            ('一般模組 import 用外部套件的模組', p1_layout_problems(pyproject, lock, dict(
                sources, **{first: sources[first] + '\nfrom project_bootstrap import mdlinks\n'}), tests)),
            ('測試沒有缺套件時 SkipTest', p1_layout_problems(pyproject, lock, sources, dict(
                tests, **{skip_test: tests[skip_test].replace("raise unittest.SkipTest('needs ", "raise unittest.SkipTest('x ")}))),
            ('P1_EXTRAS 列了不存在的模組', p1_layout_problems(pyproject, lock, sources, tests,
                                                         P1_EXTRAS + ('src/project_bootstrap/gone.py',))),
        ]
        for name, problems in cases:
            if not problems:
                bad.append('負向測試未擋：' + name)
    record('FAIL' if bad else 'OK', 'P1 開發骨架', '；'.join(bad) if bad else
           'pyproject 依賴都在 uv.lock、%d 個外部套件都有 sha256 與授權、最低 Python 3.12；'
           '%d 支程式除 %d 支指定模組外只用標準函式庫，且不 import 那幾支；import 它們的測試缺套件時 SkipTest；'
           '%d 個負向測試（鎖檔是否最新要另跑 uv lock --check，本項不需要 uv）' % (
               len(re.findall(r'source = \{ registry = ', lock)), len(sources), len(P1_EXTRAS), len(cases)))


def kit_source_problems(build_kit, prose, files, kit):
    """2026-11-11 P1 第三片：PROJECT-BOOTSTRAP.md 必須等於 src/kit 生成的結果。

    只查生成結果逐位元組相同、每個範本剛好被用一次、範本集合等於 EXPECTED。
    範本內容對不對由本檔其他各項（重生骨架起）照舊在生成出來的部署包上驗。
    """
    try:
        built = build_kit.build(prose, files)
    except build_kit.KitError as exc:
        return ['src/kit 生不出部署包：%s' % exc]
    bad = []
    if built != kit:
        lines = (built.split('\n'), kit.split('\n'))
        first = next((i for i, pair in enumerate(zip(*lines)) if pair[0] != pair[1]),
                     min(len(lines[0]), len(lines[1])))
        bad.append('PROJECT-BOOTSTRAP.md 與 src/kit 生成結果不同（第 %d 行起）；'
                   '改來源後跑 python3 -X utf8 tools/build_kit.py，不要手改部署包' % (first + 1))
    if set(files) != EXPECTED:
        bad.append('src/kit/files 的範本與 EXPECTED 不同：缺 %s 多 %s'
                   % (sorted(EXPECTED - set(files)), sorted(set(files) - EXPECTED)))
    return bad


def step_kit_source():
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import build_kit
        prose, files = build_kit.load_source()
    except (ImportError, OSError) as exc:
        record('FAIL', '部署包由來源生成', '讀不到 tools/build_kit.py 或 src/kit：%s' % exc)
        return
    except Exception as exc:  # build_kit.KitError（例如範本少了 .tmpl）
        record('FAIL', '部署包由來源生成', str(exc))
        return
    finally:
        sys.path.remove(str(ROOT / 'tools'))
    kit = read_lf(KIT)
    bad = kit_source_problems(build_kit, prose, files, kit)
    cases = []
    if not bad:
        name = 'AGENTS.md'
        directive = '<!-- kit-file: %s -->' % name
        cases = [
            ('手改部署包', kit_source_problems(build_kit, prose, files, kit.replace('鐵律', '鐵則', 1))),
            ('改範本沒重生', kit_source_problems(build_kit, prose, dict(files, **{name: files[name] + 'x\n'}), kit)),
            ('改 kit.md 沒重生', kit_source_problems(build_kit, prose.replace('## 0.', '## 0 .', 1), files, kit)),
            ('多一個沒用到的範本', kit_source_problems(build_kit, prose, dict(files, **{'extra.md': 'x\n'}), kit)),
            ('kit.md 指到不存在的範本', kit_source_problems(build_kit, prose.replace(
                directive, '<!-- kit-file: missing.md -->', 1), files, kit)),
            ('同一個範本用兩次', kit_source_problems(build_kit, prose.replace(
                '<!-- kit-file: GEMINI.md -->', directive, 1), files, kit)),
            ('範本少了結尾換行', kit_source_problems(build_kit, prose, dict(files, **{name: files[name][:-1]}), kit)),
            ('範本含收尾圍籬', kit_source_problems(build_kit, prose, dict(
                files, **{'.gitattributes': files['.gitattributes'] + '````\n'}), kit)),  # 3.13 用四個反引號圍
            ('範本集合少一個', kit_source_problems(build_kit, prose.replace(
                '<!-- kit-file: .gitattributes -->\n', '', 1),
                {k: v for k, v in files.items() if k != '.gitattributes'}, kit)),
        ]
        for label, problems in cases:
            if not problems:
                bad.append('負向測試未擋：' + label)
    record('FAIL' if bad else 'OK', '部署包由來源生成', '；'.join(bad) if bad else
           'PROJECT-BOOTSTRAP.md 與 src/kit（kit.md＋%d 個 .tmpl 範本）生成結果逐位元組相同；'
           '%d 個負向測試（只證明部署包是生成的，範本內容由其他各項驗）' % (len(files), len(cases)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--staged', action='store_true',
                    help='B7 提交前拒絕未暫存或未追蹤檔，驗證實際 staged 候選')
    ap.add_argument('--keep', action='store_true', help='保留產生的骨架，印出路徑')
    ap.add_argument('--zip', nargs='?', const='', metavar='PATH',
                    help='驗證全過時，額外輸出解壓即用的 zip（預設 dist/project-skeleton-<日期>.zip）')
    ap.add_argument('--allow-unverified-zip', action='store_true',
                    help='搭配 --zip：容許 SKIP 的調試產物，附未驗證清單且仍 exit 1；FAIL 不可覆寫')
    args = ap.parse_args()
    if args.allow_unverified_zip and args.zip is None:
        ap.error('--allow-unverified-zip 必須搭配 --zip')
    results.clear()

    if not KIT.exists():
        print(f'找不到 {KIT}——請在本 repo 根目錄執行')
        return 2

    if args.staged:
        problems = source_staged_problems(ROOT)
        if problems:
            print('[index] 🔴 ' + '；'.join(problems))
            return 2
        print('[index] staged 提交候選與工作樹一致，無未追蹤檔')

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='verify-bootstrap-'))
    dest = tmp / 'gen'
    dest.mkdir()
    print(f'重生骨架於 {dest}\n')
    try:
        run_checks(dest, tmp)
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
    if skipped:
        print(f'SKIP：{len(skipped)} 項未驗證 —— {"、".join(skipped)}')
        if not args.allow_unverified_zip:
            if args.zip is not None:
                print('（有 SKIP，不產出 zip；既有檔案不覆寫。調試時可明確加 --allow-unverified-zip）')
            return 1
    if args.zip is not None:
        out = pathlib.Path(args.zip) if args.zip else \
            ROOT / 'dist' / f'project-skeleton-{date.today().isoformat()}.zip'
        build_zip(out, [r for r in results if r[0] == 'SKIP'])
    if skipped:
        print('UNVERIFIED：僅供調試，跳過的項目沒有被驗證，結束碼仍為 1')
        return 1
    print('OK：部署包驗證全數通過')
    return 0


if __name__ == '__main__':
    sys.exit(main())
