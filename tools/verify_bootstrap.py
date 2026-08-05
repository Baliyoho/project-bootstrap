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

做八件事（第 6 項是 2026-08-05 使用者回報實際部署踩到問題後補的）：
  1. 重生骨架     ——把第 3 節每個範本抽成實體檔案，比對 EXPECTED 清單有沒有缺漏
  2. 填佔位符     ——模擬一次真實部署，填完不該再有殘留
  3. check_docs   ——在填好的骨架跑，要 exit 0
  4. 佔位符清單   ——check_docs 的 PLACEHOLDER_NAMES 要蓋住範本裡真正用到的佔位符，
                    漏一個名字就是那個洞永遠不會被檢查到，而且沒有任何跡象
  5. 佔位符檢查   ——故意種一個佔位符回去，check_docs 必須 exit 2（否則第 5 項檢查是壞的）
  6. 真實部署形狀 ——把部署包與一個非 ASCII 檔名放回骨架裡再跑 check_docs，必須仍 exit 0。
                    這兩件事單獨看都不起眼，合起來就是「照說明部署的人 100% 會踩到」
  7. hook 五情境  ——pre-push：非 push／權威分支未更新 HANDOFF／已更新／feature／停用開關
  8. 行末與雜項   ——本 repo 與重生骨架全 LF、兩份 JSON 設定合法、verify_state 與
                    git-freshness 可執行

結束碼：0＝全過；1＝有跳過項（缺 bash 之類）但無失敗；2＝有失敗。
本工具唯讀本 repo，只在系統暫存區寫檔。
"""
import argparse
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
    'AGENTS.md', 'CLAUDE.md', 'GEMINI.md', 'HANDOFF.md', 'README.md',
    'docs/ai-notes/handover-protocol.md', 'docs/ai-notes/roadmap.md',
    '.claude/skills/handoff/SKILL.md', '.claude/settings.json',
    '.claude/hooks/git-freshness.sh', '.claude/hooks/pre-push-handoff.sh',
    '.codex/hooks.json', '.agents/skills/handoff/SKILL.md',
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
            continue                       # 例：3.15 是慣例說明，不是檔案
        j, fence = i, None
        while j < end:
            m = FENCE_RE.match(lines[j])
            if m:
                fence = m.group(1)
                break
            j += 1
        if fence is None:
            continue
        k, body = j + 1, []
        while k < end and not re.match('^' + fence + r'\s*$', lines[k]):
            body.append(lines[k])
            k += 1
        content = '\n'.join(body) + '\n'
        for p in paths:
            f = dest / p
            f.parent.mkdir(parents=True, exist_ok=True)
            with open(f, 'w', encoding='utf-8', newline='') as fh:
                fh.write(content)
            written.add(p)
    # 3.2 一個範本產兩檔，差別只有標題（部署包在該節有註明），這裡照著補上。
    gem = dest / 'GEMINI.md'
    if gem.exists():
        text = gem.read_text(encoding='utf-8').replace('# CLAUDE.md', '# GEMINI.md', 1)
        with open(gem, 'w', encoding='utf-8', newline='') as fh:
            fh.write(text)
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
- **Codex**：同上，但第一次要在 CLI 打 `/hooks` 信任 `.codex/hooks.json`。
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
            step_deploy_shape(dest)
            step_portability(dest)
            hooked = step_hook(dest, tmp)
            work = hooked if isinstance(hooked, pathlib.Path) else None
        step_eol(dest)
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
