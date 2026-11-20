#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 協作專案管理骨架的安裝程式（v2026-11-20.2）。

用法：
  python3 bootstrap.py --target <專案資料夾>            # 安裝：程式會問訪談題目
  python3 bootstrap.py --target <專案資料夾> --answers answers.json --non-interactive
  python3 bootstrap.py update --target <專案資料夾>     # 更新預演；加 --write 才寫入

只用 Python 標準函式庫，需要 Python 3.12 以上；只寫本機檔案，不碰網路、不推送。
已存在的同名檔一律不覆寫，新內容寫到旁邊的 <路徑>.bootstrap-new。
"""
# 產物，不要手改：由 project-bootstrap 的 tools/build_kit.py 從 src/kit/、
# src/project_bootstrap/installer.py 與 tools/sync_project.py 產生（需求決策書 v3 Q49）。
import copy
import argparse
import datetime
import fnmatch
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

# Python 版本下限看 pyproject.toml 的 requires-python（決策書 v3 Q49）。在 main() 裡擋，
# 不在 import 時擋：sync_project.py 與測試在較舊的 Python 上也要能 import 本模組。
MIN_PY = (3, 12)

ANSWERS_FILE = '.bootstrap/answers.json'
SIDECAR = '.bootstrap-new'
PENDING = '<部署後填>'
PLACEHOLDER_RE = re.compile(r'\{\{([A-Z][A-Z0-9_]{1,40})\}\}')
# 清單型的答案：Markdown 裡寫成反引號清單，`.gitignore` 裡每行一個 pattern。
LIST_KEYS = ('SECRETS', 'RUNTIME_DIRS', 'STACK_DIRS')
IGNORE_KEYS = ('SECRETS', 'RUNTIME_DIRS')
# 答案檔會進 Git，所以答案裡不得有祕密。只擋常見的金鑰樣式；擋不到的格式仍靠人。
SECRET_PATTERNS = (
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    re.compile(r'\b(?:sk|rk|pk)-[A-Za-z0-9_-]{20,}'),
    re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}'),
    re.compile(r'\bgithub_pat_[A-Za-z0-9_]{20,}'),
    re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    re.compile(r'\bxox[abposr]-[A-Za-z0-9-]{10,}'),
    re.compile(r'\bAIza[0-9A-Za-z_-]{35}\b'),
    re.compile(r'[A-Za-z0-9+/_=-]{40,}'),
)

# 訪談題目（部署包第 1 節的表）。judgment=True 的題目有判斷空間，程式只記下使用者的
# 原話；留空或怎麼落實，列進安裝後 agent 的第一批工作。
QUESTIONS = (
    {'key': 'PROJECT_NAME', 'prompt': '專案名稱', 'default': 'folder', 'required': True},
    {'key': 'ONELINER', 'prompt': '一句話說明它是什麼、給誰用（可留空，之後由 agent 補）'},
    {'key': 'GH_OWNER', 'prompt': 'GitHub 帳號或組織（可留空，建 repo 前由 agent 問你）'},
    {'key': 'GH_REPO', 'prompt': 'GitHub repo 名', 'default': 'folder', 'required': True},
    {'key': 'GH_VISIBILITY', 'prompt': 'repo 公開或私有（private／public）', 'default': 'private',
     'required': True, 'choices': ('private', 'public')},
    {'key': 'LANG', 'prompt': '跟 AI 溝通的語言', 'default': '繁體中文', 'required': True},
    {'key': 'TZ', 'prompt': '時區（IANA 名稱，例如 Asia/Taipei）', 'default': 'tz', 'required': True},
    {'key': 'SECRETS', 'prompt': '絕不進 Git 的憑證檔，用逗號分隔', 'default': '.env', 'required': True,
     'list': True},
    {'key': 'RUNTIME_DIRS', 'prompt': '絕不進 Git 的運行／資料目錄，用逗號分隔（可留空）', 'list': True},
    {'key': 'STACK_DIRS', 'prompt': '專案主要程式目錄，用逗號分隔（可留空）', 'list': True},
    {'key': 'VERIFY_TARGETS', 'prompt': '「一鍵驗證」該查什麼（可留空；由 agent 寫進 verify_state.py）',
     'judgment': True},
    {'key': 'FORBIDDEN_OPS', 'prompt': '有沒有已知「絕對不能做」的操作（可留空；由 agent 寫成 AGENTS.md 鐵律）',
     'judgment': True},
)
KEYS = tuple(q['key'] for q in QUESTIONS) + ('TODAY',)


class InstallError(Exception):
    pass


# ── 範本與答案 ──────────────────────────────────────────────────

def load_kit(source):
    """開發用：從 src/kit/ 讀出跟 bootstrap.py 內嵌的同一份資料。"""
    source = pathlib.Path(source)
    templates = {}
    for path in sorted((source / 'files').rglob('*')):
        if path.is_file():
            rel = path.relative_to(source / 'files').as_posix()
            if not rel.endswith('.tmpl'):
                raise InstallError('範本少了 .tmpl：' + rel)
            with open(path, encoding='utf-8', newline='') as fh:
                templates[rel[:-len('.tmpl')]] = fh.read().replace('\r\n', '\n')
    owners = json.loads((source / 'owners.json').read_text(encoding='utf-8'))['files']
    return {'version': kit_version(templates), 'owners': owners, 'templates': templates}


def kit_version(templates):
    """骨架版本取自 AGENTS.md 共用制度開始標記；驗證器另外釘住它跟 VERSION 相同。"""
    match = re.search(r'共用制度開始 source: PROJECT-BOOTSTRAP\.md v([0-9][0-9.-]*)', templates.get('AGENTS.md', ''))
    if not match:
        raise InstallError('AGENTS.md 範本沒有共用制度的版本標記')
    return match.group(1)


def split_list(value):
    """答案裡的路徑清單。有反引號就取反引號內，否則以逗號、頓號或換行分隔。"""
    value = value or ''
    items = re.findall(r'`([^`]+)`', value) or re.split(r'[,，、\n]', value)
    return [i.strip() for i in items if i.strip()]


def secret_problems(answers):
    bad = []
    for key, value in sorted(answers.items()):
        for pattern in SECRET_PATTERNS:
            if isinstance(value, str) and pattern.search(value):
                bad.append('%s 看起來含金鑰或權杖，答案檔會進 Git，不收' % key)
                break
    return bad


def check_answers(answers):
    """缺題、多題、清單格式與祕密。回傳問題清單；空的才可以寫檔。"""
    bad = ['不認得的題目 %s' % k for k in sorted(set(answers) - set(KEYS))]
    for q in QUESTIONS:
        value = answers.get(q['key'], '')
        if not isinstance(value, str):
            bad.append('%s 必須是字串' % q['key'])
            continue
        if q.get('required') and not value.strip():
            bad.append('%s 必填' % q['key'])
        if q.get('choices') and value and value not in q['choices']:
            bad.append('%s 只能是 %s' % (q['key'], '／'.join(q['choices'])))
        if q.get('list'):
            for item in split_list(value):
                if item.startswith('!') or '`' in item:
                    bad.append('%s 的「%s」不能用 ! 反向納入或含反引號' % (q['key'], item))
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', answers.get('TODAY', '')):
        bad.append('TODAY 要是 YYYY-MM-DD')
    return bad + secret_problems(answers)


def blank_keys(answers):
    """留空、要由 agent 補的題目（必填題不會留空）。"""
    return [q['key'] for q in QUESTIONS if not q.get('required') and not answers.get(q['key'], '').strip()]


def render(rel, text, answers):
    """換掉一個範本的佔位符。範本用到訪談沒有的題目就停，不猜。"""
    def sub(match):
        key = match.group(1)
        if key not in answers:
            raise InstallError('%s 用到訪談沒有的佔位符 %s' % (rel, key))
        value = answers[key]
        if key in LIST_KEYS:
            items = split_list(value)
            if rel == '.gitignore' and key in IGNORE_KEYS:
                return '\n'.join(items) if items else '# （%s 尚未指定，見 HANDOFF.md）' % key
            return '、'.join('`%s`' % i for i in items) if items else PENDING
        return value.strip() or PENDING
    return PLACEHOLDER_RE.sub(sub, text)


# ── 換行與雜湊 ──────────────────────────────────────────────────

def eol_rules(gitattributes):
    rules = []
    for line in gitattributes.split('\n'):
        parts = line.split()
        if not parts or parts[0].startswith('#'):
            continue
        for attr in parts[1:]:
            if attr.startswith('eol='):
                rules.append((parts[0], attr[4:]))
    return rules


def eol_for(rel, rules):
    """依 .gitattributes 決定寫檔的換行；最後一條符合的規則勝出，跟 Git 一樣。"""
    eol = 'lf'
    for pattern, value in rules:
        subject = rel if '/' in pattern else rel.rsplit('/', 1)[-1]
        if fnmatch.fnmatchcase(subject, pattern):
            eol = value
    return eol


def encode(text, eol):
    text = text.replace('\r\n', '\n')
    if eol == 'crlf':
        text = text.replace('\n', '\r\n')
    return text.encode('utf-8')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_bytes(path, data, executable=False):
    """先寫同目錄暫存檔再換名：中斷時不會留下半個檔。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as fh:
            fh.write(data)
        if os.name == 'posix':
            # mkstemp 開出來是 0600；照一般建檔的 umask 給權限，hook 另加執行位元。
            mask = os.umask(0)
            os.umask(mask)
            os.chmod(tmp, (0o777 if executable else 0o666) & ~mask)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def hash_problems(target, expected):
    """寫完逐檔讀回來比對。expected 是 {相對路徑: 位元組}。"""
    bad = []
    for rel, data in expected.items():
        try:
            got = (target / rel).read_bytes()
        except OSError as e:
            bad.append('%s 讀不回來：%s' % (rel, e))
            continue
        if digest(got) != digest(data):
            bad.append('%s 雜湊不符（寫入 %s，讀回 %s）' % (rel, digest(data)[:12], digest(got)[:12]))
    return bad


# ── 安裝 ────────────────────────────────────────────────────────

def install_order(kit):
    """`.gitignore` 先寫：之後任何人 git add，祕密規則都已就位。HANDOFF 最後寫。"""
    rels = sorted(kit['templates'])
    first = [r for r in ('.gitignore', '.gitattributes') if r in rels]
    last = [r for r in ('HANDOFF.md',) if r in rels]
    return first + [r for r in rels if r not in first and r not in last] + last


def target_problems(target):
    """不能裝的位置與已經裝過的資料夾。"""
    home = pathlib.Path.home().resolve()
    resolved = target.resolve()
    if resolved == home or resolved == pathlib.Path(resolved.anchor) or resolved.parent == home and resolved.name in ('Desktop', 'Documents', 'Downloads'):
        return ['%s 是家目錄、磁碟根目錄或大目錄，請先建一個專案資料夾' % target]
    if target.exists() and not target.is_dir():
        return ['%s 不是資料夾' % target]
    if (target / ANSWERS_FILE).exists() or (target / '.claude/skills/handoff/SKILL.md').exists():
        return ['%s 已經裝過骨架；要更新跑 `bootstrap.py update`，要接手走 handoff 的模式 A' % target]
    leftovers = sorted(p.relative_to(target).as_posix() for p in target.rglob('*' + SIDECAR)) if target.exists() else []
    if leftovers:
        return ['上一次安裝留下的 %s 還在：%s；先處理掉再裝' % (SIDECAR, '、'.join(leftovers))]
    return []


def first_tasks(conflicts, blanks, answers):
    """安裝後 agent 的第一批工作，照決策書 v3 Q49 的順序。"""
    tasks = ['補寫 `ARCHITECTURE.md` 的「專案本體」、`README.md` 與 `docs/ai-notes/roadmap.md`，照實寫；'
             '還沒有程式碼就寫「尚未有程式碼」。']
    hint = answers.get('VERIFY_TARGETS', '').strip()
    tasks.append('填 `tools/verify_state.py` 要查證的項目（%s）。'
                 % ('訪談的答案：「%s」' % hint if hint else '訪談沒有答案，先問使用者'))
    if conflicts:
        tasks.append('合併 %s 衝突檔：%s。安裝程式沒有覆寫原檔，新內容在旁邊；照 mode-0 的 0-4 合進原檔後刪掉 `%s`。'
                     % (SIDECAR, '、'.join('`%s`' % r for r in conflicts), SIDECAR))
    asks = [k for k in blanks if k not in ('VERIFY_TARGETS', 'FORBIDDEN_OPS')]
    forbidden = answers.get('FORBIDDEN_OPS', '').strip()
    if asks or not forbidden:
        tasks.append('回答訪談中留空的題目：%s。答案寫回 `%s`，檔案裡的 `%s` 換成實際值。'
                     % ('、'.join(asks + ([] if forbidden else ['FORBIDDEN_OPS（絕對不能做的操作）'])) ,
                        ANSWERS_FILE, PENDING))
    if forbidden:
        tasks.append('把訪談說的「絕對不能做」寫成 `AGENTS.md` 共用制度標記外的鐵律，附理由與日期：「%s」。' % forbidden)
    tasks.append('建 GitHub repo（owner／repo 名與 public／private 先問使用者確認）、照 mode-0 的 0-5 '
                 '本機驗收後首次推送，再跑 0-6 的遠端與工具驗收並回報。')
    return tasks


def handoff_text(template, written, conflicts, blanks, answers, now):
    """HANDOFF.md：「工作中」是「無（已交棒）」，下一步列第一批工作，讓 agent 照平常接棒接手。"""
    text = template.replace('HH:MM', now.strftime('%H:%M'), 1)
    lines = text.split('\n')
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith('## 未完成'))
    except StopIteration:
        raise InstallError('HANDOFF.md 範本沒有「## 未完成」一節')
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('## ')), len(lines))
    body = ['', '安裝後的第一批工作，做法在 `.claude/skills/handoff/mode-0.md`：', '']
    body += ['%d. %s' % (n, t) for n, t in enumerate(first_tasks(conflicts, blanks, answers), 1)]
    if '**工作中**：無（已交棒）' not in text:
        raise InstallError('HANDOFF.md 範本的「工作中」不是「無（已交棒）」')
    return '\n'.join(lines[:start + 1] + body + [''] + lines[end:])


def plan_install(target, kit, answers, now):
    """算出要寫的檔：{寫到哪: (位元組, 範本路徑)}，與衝突清單。不寫任何東西。"""
    rules = eol_rules(kit['templates'].get('.gitattributes', ''))
    rendered = {rel: render(rel, kit['templates'][rel], answers) for rel in install_order(kit)}
    conflicts = [rel for rel in rendered if (target / rel).exists() or (target / rel).is_symlink()]
    if (target / ANSWERS_FILE).exists():
        conflicts.append(ANSWERS_FILE)
    blanks = blank_keys(answers)
    rendered['HANDOFF.md'] = handoff_text(rendered['HANDOFF.md'], rendered, conflicts, blanks, answers, now)
    rendered[ANSWERS_FILE] = answers_text(kit, answers)
    writes = {}
    for rel, text in rendered.items():
        dest = rel + SIDECAR if rel in conflicts else rel
        writes[dest] = (encode(text, eol_for(rel, rules)), rel)
    return writes, conflicts, blanks


def answers_text(kit, answers):
    data = {'schema': 1, 'kit_version': kit['version'],
            'answers': {k: answers.get(k, '') for k in KEYS}}
    return json.dumps(data, ensure_ascii=False, indent=2) + '\n'


def git_init(target, enabled=True):
    """只在不屬於任何 Git 工作樹時 `git init -b main`；不 add、不 commit、不碰網路。"""
    if not enabled:
        return 'skip   git init（--no-git-init）'
    git = shutil.which('git')
    if not git:
        return 'skip   git init（找不到 git；agent 首次發布前再做）'
    inside = subprocess.run([git, '-C', str(target), 'rev-parse', '--is-inside-work-tree'],
                            capture_output=True, text=True)
    if inside.returncode == 0 and inside.stdout.strip() == 'true':
        return 'skip   git init（已經在 Git 工作樹裡）'
    done = subprocess.run([git, 'init', '-q', '-b', 'main', str(target)], capture_output=True, text=True)
    if done.returncode:
        done = subprocess.run([git, 'init', '-q', str(target)], capture_output=True, text=True)
        if done.returncode == 0:
            subprocess.run([git, '-C', str(target), 'symbolic-ref', 'HEAD', 'refs/heads/main'],
                           capture_output=True, text=True)
    if done.returncode:
        return 'FAIL   git init：%s' % (done.stderr.strip() or done.stdout.strip())
    return 'ok     git init（main，沒有 add、沒有 commit）'


def install(target, kit, answers, now=None, init_git=True, out=print):
    """寫檔、逐檔比對雜湊、必要時 git init。回傳 exit code。"""
    target = pathlib.Path(target)
    now = now or datetime.datetime.now()
    problems = target_problems(target) + check_answers(answers)
    if problems:
        for p in problems:
            out('FAIL   ' + p)
        return 2
    try:
        writes, conflicts, blanks = plan_install(target, kit, answers, now)
    except InstallError as e:
        out('FAIL   ' + str(e))
        return 2
    executable = {rel for rel in kit['templates'] if rel.endswith('.sh')}
    for dest, (data, rel) in writes.items():
        write_bytes(target / dest, data, executable=rel in executable)
        out(('SIDE   %s（%s 已存在，沒覆寫）' % (dest, rel)) if dest != rel else 'write  ' + dest)
    bad = hash_problems(target, {dest: data for dest, (data, rel) in writes.items()})
    for p in bad:
        out('FAIL   ' + p)
    note = git_init(target, init_git)
    out(note)
    out('')
    out('骨架 v%s 已寫入 %d 個檔%s；逐檔雜湊%s。' % (
        kit['version'], len(writes), '，%d 個衝突寫成 %s' % (len(conflicts), SIDECAR) if conflicts else '',
        '有 %d 個不符' % len(bad) if bad else '全部相符'))
    out('下一步：在這個資料夾開 Claude Code 或 Codex，說「接棒」；第一批工作寫在 HANDOFF.md。')
    return 1 if bad or note.startswith('FAIL') else 0


# ── 訪談 ────────────────────────────────────────────────────────

def detect_tz():
    zone = os.environ.get('TZ', '')
    if '/' in zone:
        return zone.lstrip(':')
    try:
        real = os.path.realpath('/etc/localtime')
    except OSError:
        return ''
    return real.split('zoneinfo/', 1)[1] if 'zoneinfo/' in real else ''


def defaults(target):
    folder = pathlib.Path(target).resolve().name
    return {'folder': folder, 'tz': detect_tz()}


def interview(target, preset, interactive=True, ask=input, out=print):
    """題目一次問完。preset（答案檔與 --set）有值的題目不再問。"""
    base = defaults(target)
    answers = {'TODAY': preset.get('TODAY') or datetime.date.today().isoformat()}
    for q in QUESTIONS:
        key = q['key']
        default = q.get('default', '')
        default = base.get(default, default) if default in base else default
        if key in preset:
            answers[key] = preset[key]
            continue
        if not interactive:
            answers[key] = default
            continue
        while True:
            shown = ' [%s]' % default if default else ''
            value = ask('%s%s：' % (q['prompt'], shown)).strip() or default
            probe = dict(answers, **{key: value})
            errors = [e for e in check_answers(probe) if e.startswith(key)]
            if not errors:
                answers[key] = value
                break
            out('  ' + '；'.join(errors))
    return answers


def read_preset(path, pairs):
    preset = {}
    if path:
        data = json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
        preset.update(data.get('answers', data) if isinstance(data, dict) else {})
    for pair in pairs or ():
        if '=' not in pair:
            raise InstallError('--set 要寫成 KEY=VALUE：' + pair)
        key, value = pair.split('=', 1)
        preset[key.strip()] = value
    unknown = sorted(set(preset) - set(KEYS))
    if unknown:
        raise InstallError('不認得的題目：' + '、'.join(unknown))
    return {k: str(v) for k, v in preset.items()}


# ── 更新 ────────────────────────────────────────────────────────

def update(target, kit, lib, write=False, out=print):
    """只動 core 與 adapter 擁有的部分（owners.json），project 的內容不碰。

    算計畫、套用與失敗即停全部交給 sync_project.py 的 sync／apply_plan（lib），本函式只
    負責把內嵌範本依答案檔填好，放進暫存資料夾當權威版。
    """
    target = pathlib.Path(target)
    path = target / ANSWERS_FILE
    if not path.exists():
        out('FAIL   找不到 %s：這個資料夾不是用 bootstrap.py 裝的，或答案檔被刪了' % ANSWERS_FILE)
        return 2
    data = json.loads(path.read_text(encoding='utf-8'))
    answers = {k: str(v) for k, v in data.get('answers', {}).items()}
    problems = secret_problems(answers)
    if problems:
        for p in problems:
            out('FAIL   ' + p)
        return 2
    rules = eol_rules(kit['templates'].get('.gitattributes', ''))
    with tempfile.TemporaryDirectory(prefix='bootstrap-update-') as tmp:
        gen = pathlib.Path(tmp)
        for rel, text in kit['templates'].items():
            filled = render(rel, text, dict({k: '' for k in KEYS}, **answers))
            (gen / rel).parent.mkdir(parents=True, exist_ok=True)
            (gen / rel).write_bytes(encode(filled, eol_for(rel, rules)))
        plan = lib.sync(target, gen)
    out('骨架 v%s → %s' % (data.get('kit_version', '?'), target))
    for line in plan.msgs:
        out(line)
    if plan.errors:
        out('FAIL   有 %d 個檔算不出來，整個專案零寫入' % len(plan.errors))
        return 2
    if not write:
        out('預演：%d 個檔要改；加 --write 才寫入' % plan.changed)
        return 0
    done, error = lib.apply_plan(plan)
    if error:
        out('FAIL   %s 寫入失敗：%s；已寫入 %s' % (error[0], error[1], '、'.join(done) or '無'))
        return 2
    expected = {rel: text.encode('utf-8') for path, text, rel in plan.writes}
    bad = hash_problems(target, expected)
    for p in bad:
        out('FAIL   ' + p)
    if not bad:
        data['kit_version'] = kit['version']
        write_bytes(path, (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    out('已更新 %d 個檔；逐檔雜湊%s。不 commit、不 push：照 handoff 的模式 B 收尾。'
        % (len(done), '有 %d 個不符' % len(bad) if bad else '全部相符'))
    return 1 if bad else 0


# ── 入口 ────────────────────────────────────────────────────────

def main(argv, kit, lib):
    if sys.version_info < MIN_PY:
        print('需要 Python %d.%d 以上，這台是 %d.%d' % (MIN_PY + sys.version_info[:2]))
        return 2
    for stream in (sys.stdout, sys.stderr):
        if (getattr(stream, 'encoding', '') or '').lower().replace('-', '') != 'utf8':
            try:
                stream.reconfigure(encoding='utf-8', errors='replace')
            except (AttributeError, ValueError):
                pass
    parser = argparse.ArgumentParser(
        prog='bootstrap.py',
        description='AI 協作專案管理骨架 v%s：安裝（預設）或更新。只寫本機檔案，不碰網路。' % kit['version'])
    parser.add_argument('command', nargs='?', choices=('install', 'update'), default='install')
    parser.add_argument('--target', default='.', help='專案資料夾（預設：目前資料夾）')
    parser.add_argument('--answers', help='答案檔（JSON）；有的題目不再問')
    parser.add_argument('--set', action='append', metavar='KEY=VALUE', help='直接給一題的答案，可重複')
    parser.add_argument('--non-interactive', action='store_true', help='不問：沒給的題目用預設，必填題沒有預設就失敗')
    parser.add_argument('--no-git-init', action='store_true', help='不要在目標資料夾 git init')
    parser.add_argument('--write', action='store_true', help='update 用：實際寫入（預設只預演）')
    parser.add_argument('--version', action='version', version=kit['version'])
    args = parser.parse_args(argv)
    target = pathlib.Path(args.target)
    if args.command == 'update':
        return update(target, kit, lib, write=args.write)
    try:
        preset = read_preset(args.answers, args.set)
    except (InstallError, OSError, ValueError) as e:
        print('FAIL   ' + str(e))
        return 2
    problems = target_problems(target)
    if problems:
        for p in problems:
            print('FAIL   ' + p)
        return 2
    interactive = not args.non_interactive and sys.stdin.isatty()
    answers = interview(target, preset, interactive=interactive)
    return install(target, kit, answers, init_git=not args.no_git_init)


# ── 內嵌的部署包 ─────────────────────────────────────────────
OWNERS = {
 ".agents/skills/handoff/SKILL.md": {
  "owner": "adapter",
  "update": "whole"
 },
 ".claude/hooks/codex-hook.cmd": {
  "owner": "adapter",
  "update": "whole"
 },
 ".claude/hooks/git-freshness.sh": {
  "owner": "core",
  "update": "whole"
 },
 ".claude/hooks/pre-push-handoff.sh": {
  "owner": "core",
  "update": "whole"
 },
 ".claude/settings.json": {
  "owner": "adapter",
  "update": "wiring"
 },
 ".claude/skills/handoff/SKILL.md": {
  "owner": "core",
  "update": "whole"
 },
 ".claude/skills/handoff/env.md": {
  "owner": "core",
  "update": "whole"
 },
 ".claude/skills/handoff/mode-0.md": {
  "owner": "core",
  "update": "whole"
 },
 ".claude/skills/handoff/mode-a-stop.md": {
  "owner": "core",
  "update": "whole"
 },
 ".claude/skills/handoff/mode-a.md": {
  "owner": "core",
  "update": "whole"
 },
 ".claude/skills/handoff/mode-b.md": {
  "owner": "core",
  "update": "whole"
 },
 ".claude/skills/handoff/reasons.md": {
  "owner": "core",
  "update": "whole"
 },
 ".codex/hooks.json": {
  "owner": "adapter",
  "update": "wiring"
 },
 ".gitattributes": {
  "owner": "project",
  "update": "seed"
 },
 ".gitignore": {
  "owner": "project",
  "update": "lines"
 },
 "AGENTS.md": {
  "owner": "project",
  "update": "lines"
 },
 "ARCHITECTURE.md": {
  "owner": "project",
  "update": "seed"
 },
 "CLAUDE.md": {
  "owner": "project",
  "update": "lines"
 },
 "HANDOFF.md": {
  "owner": "project",
  "update": "lines"
 },
 "README.md": {
  "owner": "project",
  "update": "seed"
 },
 "docs/ai-notes/roadmap.md": {
  "owner": "project",
  "update": "seed"
 },
 "tools/check_docs.py": {
  "owner": "core",
  "update": "region"
 },
 "tools/verify_state.py": {
  "owner": "project",
  "update": "seed"
 }
}
UPDATES = {rel: entry['update'] for rel, entry in OWNERS.items()}
TEMPLATES = {}
TEMPLATES['.agents/skills/handoff/SKILL.md'] = '---\nname: handoff\ndescription: 指標檔，權威版在 .claude/skills/handoff/SKILL.md——交接制度的參考檔（碰到才讀，不是必讀）：接棒時 git 狀態不正常（落後、領先、分岔、fetch 失敗、來源不明的未提交變更、別人的「工作中」標記）怎麼判讀與處理；交棒時 HANDOFF.md 怎麼覆寫、怎麼安全提交與 push；中途同步；在還沒有這套制度的資料夾裡把骨架建起來（模式 0 建制）；每條規則的理由與事故。規則本身在專案 AGENTS.md 的共用制度一節，衝突時以那裡為準。Triggers on 接手、接棒、交棒、收工、換機器、同步進度、建制、導入這套制度、建立交接機制、幫我建 HANDOFF、新專案骨架、handoff、hand off、resume work、bootstrap project、set up handoff。\n---\n\n<!-- source: PROJECT-BOOTSTRAP.md v2026-11-13 — 本檔只是指標，改內容請改權威版 -->\n\n# 本檔只是指標，請讀權威版\n\n**權威版：[`.claude/skills/handoff/SKILL.md`](../../../.claude/skills/handoff/SKILL.md)**（參考檔入口；碰到才讀。必守的條件在 `AGENTS.md` 的共用制度一節）\n\n那份是純 Markdown，路徑掛在 `.claude/` 下只是因為 Claude Code 會自動載入該位置，內容不限任何工具。\n\n**請勿在此複製內容。** 兩份副本會各自演進並產生矛盾（曾發生：一份已更新成新流程、另一份停在舊版，而入口文件指向舊的那份，照做就失敗）。新知識一律寫進權威版。\n'
TEMPLATES['.claude/hooks/codex-hook.cmd'] = '@echo off\nrem source: PROJECT-BOOTSTRAP.md v2026-11-01.4 - authority is the kit; edit it first, then sync.\nrem Codex Windows launcher. Plumbing only; rules stay in the existing .sh files.\nrem ASCII-only, LF-only, no labels or multiline parenthesised blocks. See section 3.17.\nsetlocal\nif "%~1"=="" >&2 echo [codex-hook] ERROR: missing script argument.\nif "%~1"=="" exit /b 1\nset "BASH="\nfor /f "delims=" %%G in (\'where git 2^>nul\') do if not defined BASH if exist "%%~dpG..\\bin\\bash.exe" set "BASH=%%~dpG..\\bin\\bash.exe"\nif not defined BASH if exist "%ProgramFiles%\\Git\\bin\\bash.exe" set "BASH=%ProgramFiles%\\Git\\bin\\bash.exe"\nif not defined BASH if exist "%ProgramFiles(x86)%\\Git\\bin\\bash.exe" set "BASH=%ProgramFiles(x86)%\\Git\\bin\\bash.exe"\nif not defined BASH if exist "%LOCALAPPDATA%\\Programs\\Git\\bin\\bash.exe" set "BASH=%LOCALAPPDATA%\\Programs\\Git\\bin\\bash.exe"\nif not defined BASH >&2 echo [codex-hook] ERROR: Git Bash not found; hook did not run. Install Git for Windows and retry.\nif not defined BASH exit /b 1\nrem Codex 0.166.0 treats stdout starting with [ as JSON. Keep a plain-text first line.\necho Git status check:\n"%BASH%" "%~dp0%~1"\nexit /b %ERRORLEVEL%\n'
TEMPLATES['.claude/hooks/git-freshness.sh'] = '#!/usr/bin/env bash\n# source: PROJECT-BOOTSTRAP.md v2026-11-16.3 — 權威版在部署包，改這裡之前先改部署包再同步各專案。\n# SessionStart hook：fetch 一次，只報事實，不下指示（需求決策書 v3 第 5 節，D12）。\n# 用 SessionStart JSON 把最多 5 行 [facts] 放進 context；Codex 會把裸的 [facts] 誤認為壞 JSON。只讀：不 pull、不 push、不寫任何檔。\n# 怎麼判讀交給模型與 AGENTS.md 的共用制度；舊版的判讀表、全綠行與工具身分猜測在 2026-11-13 移除，\n# 理由與 E1 對照實測見 project-bootstrap 的 experiments/handoff-ab/RESULTS.md。\n\ncd "$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0\nbranch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || exit 0\nme=${HOSTNAME:-$(hostname 2>/dev/null || uname -n 2>/dev/null)}\n\nfacts=\'\'\nemit() { facts="${facts}${facts:+\n}$1"; }\nfinish() {\n  local py json output\n  [ -n "$facts" ] || return\n  json=\'import json, sys\nprint(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": sys.stdin.read()}}, ensure_ascii=False))\'\n  # Windows 的 python3 可能只是一個 PATH 找得到、實際執行會失敗的別名。\n  for py in python3 python; do\n    if output=$(printf \'%s\' "$facts" | "$py" -X utf8 -c "$json" 2>/dev/null) && [ -n "$output" ]; then\n      printf \'%s\\n\' "$output"\n      return\n    fi\n  done\n  printf \'%s\\n\' \'Git facts unavailable: neither python3 nor python could encode SessionStart JSON\' >&2\n  exit 1\n}\ntrap finish EXIT\n\n# 第 1 行：時間（含 session 名用的 MM.DD.HH，F50）、本機、分支\nemit "[facts] 時間 $(date \'+%Y-%m-%d %H:%M %z\')（session 名用 $(date +%m.%d.%H)）；本機 ${me}；分支 ${branch}"\n\n# 第 2 行：與 origin 的關係\nif ! git fetch --quiet origin 2>/dev/null; then\n  emit "[facts] fetch origin 失敗：不知道本機是不是最新"\n  exit 0\nfi\ncounts=$(git rev-list --left-right --count "origin/${branch}...HEAD" 2>/dev/null)\ndirty=$(git status --porcelain 2>/dev/null | wc -l | tr -d \' \')\nif [ -z "$counts" ]; then\n  emit "[facts] origin 上沒有分支 ${branch}；未提交或未追蹤 ${dirty} 個檔"\n  exit 0\nfi\nbehind=$(echo "$counts" | awk \'{print $1}\')\nahead=$(echo "$counts" | awk \'{print $2}\')\nemit "[facts] 已 fetch：本機落後 origin/${branch} ${behind} 個 commit、領先 ${ahead} 個（origin=$(git rev-parse --short "origin/${branch}" 2>/dev/null)）；未提交或未追蹤 ${dirty} 個檔"\n\n# 第 3 行：origin 那份 HANDOFF 的「工作中」。讀 origin 的、不讀本機的：此刻還沒 pull，本機那份可能是舊的。\n# 照原文印出，不解析、不判讀；有幾列就說幾列，讓重複的欄位看得見。\nremote_handoff=$(git show "origin/${branch}:HANDOFF.md" 2>/dev/null)\nif [ -n "$remote_handoff" ]; then\n  busy=$(printf \'%s\\n\' "$remote_handoff" | grep -F \'**工作中**\')\n  busy_n=$(printf \'%s\\n\' "$busy" | grep -c \'[^[:space:]]\' || true)\n  if [ "$busy_n" -gt 1 ]; then\n    emit "[facts] origin 上的 HANDOFF 有 ${busy_n} 列「工作中」，第一列：$(printf \'%s\\n\' "$busy" | head -1)"\n  else\n    emit "[facts] origin 上的 HANDOFF：${busy:-讀不到「工作中」那一行}"\n  fi\nfi\n\n# 第 4 行（有差異才印）：共用制度的版本與上游不同（F18 提示）。\n# 版本取自 AGENTS.md 共用制度開始標記裡的 source: 標記。抓不到（離線、沒有 curl）就安靜跳過。\n# 結果快取 12 小時。關掉：BOOTSTRAP_VERSION_CHECK=off\nUPSTREAM_VERSION_URL=https://raw.githubusercontent.com/Baliyoho/project-bootstrap/main/VERSION  # fork 的人改這一行\nif [ "${BOOTSTRAP_VERSION_CHECK:-}" != off ] && [ -f AGENTS.md ]; then\n  mine=$(sed -n \'s/.*共用制度開始 source: PROJECT-BOOTSTRAP\\.md v\\([0-9][0-9.-]*\\).*/\\1/p\' AGENTS.md | head -1)\n  cache=.claude/.bootstrap-version\n  # 本 repo 的 origin/main 已在上面成功 fetch；只在它確為權威來源時讀取該 ref。\n  # 其他專案沒有這個 ref，仍沿用 12 小時快取與上游 HTTP。\n  origin_url=$(git remote get-url origin 2>/dev/null)\n  authority=0\n  case "$origin_url" in\n    https://github.com/Baliyoho/project-bootstrap|https://github.com/Baliyoho/project-bootstrap.git|git@github.com:Baliyoho/project-bootstrap|git@github.com:Baliyoho/project-bootstrap.git)\n      authority=1\n      latest=$(git show origin/main:VERSION 2>/dev/null | tr -d \'\\r\\n \\t\') ;;\n  esac\n  if [ "$authority" -eq 1 ]; then\n    if [[ "$latest" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}(\\.[0-9]+)?$ ]]; then\n      printf \'%s\' "$latest" > "$cache" 2>/dev/null\n    else\n      latest=\'\'\n    fi\n  else\n    if [ -n "$(find "$cache" -mmin -720 2>/dev/null)" ]; then\n      latest=$(cat "$cache" 2>/dev/null)\n    else\n      latest=$(curl -fsS --max-time 5 "$UPSTREAM_VERSION_URL" 2>/dev/null | tr -d \'\\r\\n \\t\')\n      if [[ "$latest" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}(\\.[0-9]+)?$ ]]; then\n        printf \'%s\' "$latest" > "$cache" 2>/dev/null\n      fi\n    fi\n  fi\n  [[ "$latest" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}(\\.[0-9]+)?$ ]] || latest=\'\'\n  # 版本號是 YYYY-MM-DD 或 YYYY-MM-DD.N；序號補成三位數後日期與序號能一起比字典序。\n  verkey() {\n    _d=${1%%.*}\n    _n=${1#"$_d"}\n    _n=${_n#.}\n    [ -n "$_n" ] || _n=0\n    case $_n in *[!0-9]*) _n=0 ;; esac\n    printf \'%s.%03d\' "$_d" "$_n"\n  }\n  if [ -n "$mine" ] && [ -n "$latest" ]; then\n    km=$(verkey "$mine")\n    kl=$(verkey "$latest")\n    if [ "$km" != "$kl" ]; then\n      if [ "$(printf \'%s\\n%s\\n\' "$km" "$kl" | sort | head -1)" = "$km" ]; then\n        emit "[facts] 共用制度落後：本機 v${mine}，上游 v${latest}（更新方法見 project-bootstrap 的 README）"\n      else\n        emit "[facts] 共用制度比上游新：本機 v${mine}，上游 v${latest}"\n      fi\n    fi\n  fi\nfi\n\n# 第 5 行（有差異才印）：家目錄的 handoff skill 與專案那份不同。實測 Claude Code 2.1.321 會用家目錄那份\n# 蓋掉專案的同名 skill（決策書 Q28）。逐檔比內容，只有一邊有的檔也算不同。\nhome_skill=${HOME:-}/.claude/skills/handoff\nif [ -f .claude/skills/handoff/SKILL.md ] && [ -n "${HOME:-}" ] && [ -d "$home_skill" ]; then\n  skill_diff=\'\'\n  for f in .claude/skills/handoff/*.md "$home_skill"/*.md; do\n    [ -f "$f" ] || continue\n    name=${f##*/}\n    case " $skill_diff " in *" $name "*) continue ;; esac\n    cmp -s ".claude/skills/handoff/$name" "$home_skill/$name" || skill_diff="$skill_diff $name"\n  done\n  [ -n "$skill_diff" ] && emit "[facts] 家目錄 ~/.claude/skills/handoff/ 與本專案的 handoff skill 不同（${skill_diff# }）；Claude Code 載入的是家目錄那份"\nfi\nexit 0\n'
TEMPLATES['.claude/hooks/pre-push-handoff.sh'] = '#!/usr/bin/env bash\n# PreToolUse hook：AI push 提醒（不是 Git 原生 pre-push／發布保證）\n# 起因：push 完才想起沒寫 HANDOFF，下一棒拿到過期狀態。\n# 只看殼層指令（tool_input.command）裡的字面 git push、目前分支與 origin 追蹤 ref，不解析選項／remote／refspec。\n# GUI／script 可能漏判，指令裡僅提到 git push 也可能誤擋；檢查已提交的 HANDOFF 差異。\n# 其他情況（非 push 指令、非殼層工具、feature 分支中途推進度、判斷不了）一律放行——寧可漏擋，不要誤擋。\n# 退出碼：0＝放行；2＝擋下並把 stderr 交給模型（模型會看到訊息並改走交棒程序）。\n# 臨時停用：HANDOFF_HOOK=off\n# source: PROJECT-BOOTSTRAP.md v2026-11-16.3 — 權威版在部署包，改這裡之前先改部署包再同步各專案。\n\n[ "$HANDOFF_HOOK" = "off" ] && exit 0\n\npayload=$(cat 2>/dev/null)\ncase "$payload" in\n  *\'git push\'*) ;;\n  *) exit 0 ;;\nesac\n# 2026-11-12（決策書 Q27）：只看 "command" 這個欄位，不看整段 payload。Codex 的 PreToolUse\n# 沒有 matcher（3.17），每個工具呼叫都會跑到這裡；舊版拿整段 stdin 比對，編輯工具的內容只要\n# 提到 git push 就被擋，Claude Code（matcher 只放殼層工具）卻不會，兩個工具結果不同。\n# 欄位值可能是 JSON 字串或字串陣列，兩種都收；JSON 字串裡的 \\" 跳脫不會讓比對提早結束。\n# 只用 grep、不另外依賴直譯器：這支會被抄進各專案，Git Bash 只保證有 grep。\nprintf \'%s\' "$payload" \\\n  | grep -oE \'"command"[[:space:]]*:[[:space:]]*("([^"\\\\]|\\\\.)*"|\\[([^]"]|"([^"\\\\]|\\\\.)*")*\\])\' \\\n  | grep -qF \'git push\' || exit 0\n\nroot=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0\ncd "$root" || exit 0\n[ -f HANDOFF.md ] || exit 0                    # 沒有這套交接制度就不管\n\nbranch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || exit 0\nmain=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)\nmain=${main#origin/}\n[ -n "$main" ] || main=main\n[ "$branch" = "$main" ] || exit 0               # feature 分支中途推進度不擋\n\ngit rev-parse --quiet --verify "refs/remotes/origin/$branch" >/dev/null 2>&1 || exit 0\n[ -n "$(git rev-list "origin/$branch..HEAD" 2>/dev/null)" ] || exit 0   # 沒有要推的 commit\ngit diff --name-only "origin/$branch..HEAD" 2>/dev/null | grep -qx \'HANDOFF.md\' && exit 0\n# 2026-11-12（決策書 Q31）：origin 上的「工作中」不是「無（已交棒）」＝有人開工、還沒交棒，\n# 這次 push 是中途安全點，不必更新 HANDOFF。看不出是哪個 session，別台機器的標記也會放行——\n# 那種情況本該在 A2.5 停下，這支只是提醒，寧可漏擋。沒有這一欄或讀不到 origin 的檔都照舊擋。\ngit show "origin/$branch:HANDOFF.md" 2>/dev/null | grep -F \'**工作中**\' | grep -vqF \'無（已交棒）\' && exit 0\n# F06：未提交的 staged／unstaged 修改不會隨 push 上傳，不可據此放行。\n\n>&2 echo "[handoff-check] AI push 提醒：目前 $branch 相對 origin 的已提交差異沒有更新 HANDOFF.md（未提交修改不算）。"\n>&2 echo "[handoff-check] origin 的「工作中」是「無（已交棒）」：中途 push 先照 A5 寫開工標記再推；使用者要求交棒才走 handoff skill 的 B 模式並在 B7 驗最終快照。"\n>&2 echo "[handoff-check] 若真的只是中途推進度：改推 feature 分支，或本次設 HANDOFF_HOOK=off。"\nexit 2\n'
TEMPLATES['.claude/settings.json'] = '{\n  "hooks": {\n    "SessionStart": [\n      {\n        "hooks": [\n          {\n            "type": "command",\n            "command": "bash \\"$(git rev-parse --show-cdup).claude/hooks/git-freshness.sh\\"",\n            "timeout": 30,\n            "statusMessage": "檢查 git 是否與 origin 同步…"\n          }\n        ]\n      }\n    ],\n    "PreToolUse": [\n      {\n        "matcher": "Bash|PowerShell",\n        "hooks": [\n          {\n            "type": "command",\n            "command": "bash \\"$(git rev-parse --show-cdup).claude/hooks/pre-push-handoff.sh\\"",\n            "timeout": 15\n          }\n        ]\n      }\n    ]\n  }\n}\n'
TEMPLATES['.claude/skills/handoff/SKILL.md'] = '---\nname: handoff\ndescription: 交接制度的參考檔（碰到才讀，不是必讀）：接棒時 git 狀態不正常（落後、領先、分岔、fetch 失敗、來源不明的未提交變更、別人的「工作中」標記）怎麼判讀與處理；交棒時 HANDOFF.md 怎麼覆寫、怎麼安全提交與 push；中途同步；在還沒有這套制度的資料夾裡把骨架建起來（模式 0 建制）；每條規則的理由與事故。規則本身在專案 AGENTS.md 的共用制度一節，衝突時以那裡為準。Triggers on 接手、接棒、交棒、收工、換機器、同步進度、建制、導入這套制度、建立交接機制、幫我建 HANDOFF、新專案骨架、handoff、hand off、resume work、bootstrap project、set up handoff。\n---\n\n<!-- source: PROJECT-BOOTSTRAP.md v2026-11-20.2 — 權威版在部署包，改這裡之前先改部署包再同步各專案與全域副本 -->\n\n# 交接與同步程序（參考檔入口）\n\n> **2026-11-13 起（需求決策書 v3 第 5 節）這個目錄是碰到才讀的參考，不是制度成立的前提。** 必守的條件在專案 `AGENTS.md` 的共用制度一節；本目錄的步驟與它衝突時以 `AGENTS.md` 為準，使用者明確指示仍優先。\n>\n> 在程序細節上，**核心優先序：SKILL.md**（含同目錄的模式檔）優先於專案實例。專案自己的 override 寫在 `AGENTS.md` 共用制度標記外的鐵律，只可加嚴；舊專案留著的 `docs/ai-notes/handover-protocol.md`（2026-11-17 起不再部署，v3 Q41）是不同步的專案實例，升級時須人工遷移。不得在單一專案就地修改共用 skill，回部署包修正再同步。模式 0 的權威是 `PROJECT-BOOTSTRAP.md` 部署包。\n\n## 適用判斷（先做這一步）\n\n| 專案根目錄的狀態 | 走哪裡 |\n|---|---|\n| 有 `AGENTS.md` ＋ `HANDOFF.md` | 適用，需要細節時往下找 |\n| 沒有，而且使用者**明講**要導入這套制度（建交接機制／建骨架／bootstrap） | **模式 0 建制** |\n| 沒有，使用者也沒提 | **本程序不適用**。直接做他要的事，**不要憑空建立交接檔案**；最多問一句「要不要導入這套交接制度？」，他說要才走模式 0 |\n\n專案沒有 `tools/verify_state.py`／`tools/check_docs.py` 也能用：對應步驟改為「跳過並在回報寫明沒有該工具」，**不要自己發明驗證**。\n\n## 需要細節時讀哪個檔\n\n| 情況 | 模式 | 讀 |\n|---|---|---|\n| 這個資料夾還沒有這套制度，使用者要求建起來 | **0 建制** | `mode-0.md` |\n| 接棒、續作、換機器；已交棒後又要改檔 | **A 接棒** | `mode-a.md`（正常路徑）；開場 `[facts]` 有不正常的值讀 `mode-a-stop.md` |\n| **使用者要求**交棒／收工／換人接手 | **B 交棒** | `mode-b.md` |\n| 工作告一段落；想拉最新或推一個安全點 | **C 同步** | `mode-b.md` 的 C 節 |\n| 開場沒有 `[facts]`；在 Codex 或 Windows 上：指令跑得久、hook 接線有改、Git 寫不進 `.git` | 任何模式 | `env.md`（依工具、依平台各讀一節） |\n\n- **使用者沒要求就不得自行交棒**：告一段落時自己判斷要不要 commit／push（C），不改 `↗`、不加次數。A5 開工標記與 C 中途安全點都不宣稱交棒。\n- **模式檔與本檔同目錄**：專案有 `.claude/skills/handoff/` 就讀那裡，沒有就讀全域 `~/.claude/skills/handoff/`（Codex 是 `~/.codex/skills/handoff/`）。\n- 要改、質疑或想繞過任何一條規則之前先讀 `reasons.md`。`mode-a.md` 與 `mode-a-stop.md`、`mode-b.md`、`mode-0.md`、`reasons.md` 衝突時以後四者為準；`env.md` 只寫環境差異，不改變共用狀態的判讀；它們全部與 `AGENTS.md` 衝突時以 `AGENTS.md` 為準。\n\n## 全程禁令\n\n🚫 全程禁止：`reset --hard`、`push --force`、自行 `stash`、覆寫他人 commit、刪 branch。\n\n## 必須停下來問使用者（不得自行決定）\n\n- Git 異常：dirty 來源不明、接棒時 ahead-only、fetch 失敗、diverged、不能 fast-forward、遠端意外前進、沒有 upstream\n- origin 上的「工作中」是別人（同一條分支同時兩台＝違反 single writer）\n- `push --force`、`reset --hard`、刪分支、改寫歷史\n- 功能分支要併進 `main`（需使用者驗收；文件／基建分支驗證過可自己併）\n- 憑證缺失，或需要跨機器搬憑證\n- HANDOFF 沒授權的破壞性操作（刪檔、批次改資料、改 schema）\n- **建制（模式 0）**：資料夾不是空的、已有 Git 歷史或 README；要覆蓋既有的 `.gitignore`／`README.md`；建 GitHub repo 與第一次 push\n\n## session 命名（每則訊息都適用）\n\n格式、兩種狀態、何時改與交棒計數的規則在 `AGENTS.md` 共用制度的「session 名稱」一節，這裡不重寫，以免兩份各自演化。時間戳用開場 `[facts]` 第一行印的 `MM.DD.HH`。細則、反例與「為什麼要改名」在 `reasons.md` 的「session 命名」；交棒計數何時加一在 `mode-b.md` 的 B9。\n'
TEMPLATES['.claude/skills/handoff/env.md'] = '<!-- source: PROJECT-BOOTSTRAP.md v2026-11-20.2 — 權威版在部署包，改這裡之前先改部署包再同步各專案與全域副本 -->\n\n# 工具與平台差異（碰到才讀）\n\n本檔只寫環境怪癖與操作提醒，**不改變共用狀態的判讀**。「工作中」標記、`HANDOFF.md`、交棒完成的定義、push 前 hook 的行為，在 Codex／Claude Code × macOS／Windows 四種組合都一樣，照 `AGENTS.md` 的共用制度與模式檔；本檔和它們衝突時以它們為準。\n\n先讀你所在工具的一節，再讀平台的一節。沒寫的就是目前沒有已知差異。\n\n**新增條目的條件**：觀察到重複發生的失敗，寫明工具版本、平台與日期（需求決策書 v3 D10）。只限某工具或平台、會讓交接結果不同的規則（例如只在 Windows 擋下某種推送）不放這裡；它屬於共用制度，要四種組合一起加，並先經 D14 對照與使用者決定（v3 Q35）。\n\n## 開場沒有 [facts] 時依序查\n\n出現症狀才查，不必每次接棒都查版本。查到原因後照實回報，不把缺了開場事實的狀態當成正常。\n\n1. 手動重跑開場 hook（`AGENTS.md` 寫了路徑）。有輸出，表示 hook 本身正常，問題在工具沒有載入接線，往下查；沒有輸出或報錯，看 stderr。\n2. Codex：專案要先被信任。未信任的專案不載入專案的 `.codex/hooks.json`，開場就沒有 `[facts]`（`0.169.0-alpha.11.1` 會在 stderr 印 `Untrusted project-local configuration is disabled`；macOS，2026-11-16 連續兩格重現）。專案信任與 hook 審核是兩件事，兩者都要過，驗收方法見下方「hook 接線有改或同步過」。\n3. Windows：開場 hook 依序用 `python3`、`python` 產生輸出，WindowsApps 的 `python3` 別名可能找得到卻執行失敗（Codex CLI `0.166.0`，2026-11-16）。兩者都失敗時 hook 會在 stderr 報錯，回報使用者需要可執行的 Python。\n4. 回報時寫明工具與版本（例如 `codex --version`）。同一台機器可能有多個版本：2026-11-16 的 Mac 上，Codex App 外掛內附 `0.167.0-alpha.3.2`、ChatGPT App 內附 `0.169.0-alpha.11.1`，`PATH` 上一個都沒有。\n\n## Codex\n\n### 跑得久的指令\n\n驗證仍照專案要求執行；省的是工具往返與輸出，不省檢查。以下是 Codex 桌面 App 2026-11-14 的實測用法，參數上限以當前工具 schema 為準：\n\n- `exec_command` 可先等 30000 ms；有 `session_id` 才用 `write_stdin` 等結果，勿每一兩秒輪詢。若透過 `functions.exec`，外層也要設 `// @exec: {"yield_time_ms": 60000}`，否則內層等 60 秒，外層仍在 30 秒交回。可在同一段 JS 先 `await exec_command`，尚未結束再 `await write_stdin` 等 30000 ms；超過一分鐘仍未完才回報進度並繼續等，不丟棄執行中的 promise。\n- 已在上下文讀過的規則不再整份讀；正常接棒不展開理由與歷史。必要的獨立讀取合併一批；驗證、stage、commit、fetch 比對、push 等有相依的動作維持順序，任一步失敗就停。\n- 成功驗證只回傳摘要與 exit code，完整輸出留本機暫存日誌；FAIL／SKIP 要讀細節。工具提供摘要選項才使用，不猜選項或吞掉結束碼。交棒已取得的結果依 B7 的失效條件決定是否重跑。\n\n### hook 接線有改或同步過\n\n**Codex hook 接線有改或同步過，就重新檢查信任並驗收實際執行。** 在互動 CLI 的 `/hooks` 或桌面 App 的 Hooks 設定審核當前定義，再於新 session 送出一則最小測試訊息；確認 hook 成功、輸出確實進入 context。只看檔案或信任狀態不算驗收：2026-11-01 在 Windows 的真專案上量到 hook 已信任，卻因 PATH 的 `bash` 指向缺少 `/bin/bash` 的 WSL 而 exit 1。模型呼叫仍依專案原有的額度與授權規則，不因這一項自動取得授權。\n\n### 全域 skill 位置\n\n專案沒有 `.claude/skills/handoff/` 時，讀 `~/.codex/skills/handoff/`。\n\n## Claude Code\n\n- 家目錄 `~/.claude/skills/handoff/` 與專案 `.claude/skills/handoff/` 都有時，Skill 工具載入的是家目錄那份（2.1.321，2026-11-12 實測）。專案有這個目錄就改讀專案那份（入口「模式檔與本檔同目錄」那條）。\n\n## Windows\n\n- **開場沒有 `[facts]`**：照上方「開場沒有 [facts] 時依序查」，Windows 特有的是第 3 步的 `python3` 別名。\n- **驗證與測試跑得比 macOS 久**：原生 Windows 上一次完整驗證可能要三到四分鐘，超過指令工具常見的預設等待（120 秒）。2026-11-16 在一台 Windows 11 上連跑三次，分別是 224、234、244 秒，約九成花在子程序密集的測試（真的建 Git repo、起子程序比對），同一套在 macOS 上快得多。做法：提高該次指令的 timeout，或丟到背景再取結果。逾時不是驗證失敗，別把它寫成沒過；也不要為了避開上限只跑一部分就宣稱通過。（數字是在 Claude Code 的指令工具下量的；Codex 的等待設定見上方「跑得久的指令」。）\n- **工作區沙箱下的 Git 更新**：若已授權的 Git 操作被沙箱拒絕寫入 `.git`，用 Codex 的單次命令審核核准該操作，並保留目前的工作區沙箱。推送後核對遠端分支與本機追蹤參照。Windows 實測 HTTP 推送可以在遠端收到 commit 且命令回傳 0 時，仍因無法鎖定 `.git` 而留下舊追蹤參照（Codex CLI `0.166.0`，2026-11-16）。\n\n## macOS\n\n- **指令工具跑在 zsh 上**：macOS 的預設殼層是 zsh，下面三種寫法跟 bash 不同，而且常常不報錯，只是結果不對（zsh 5.9，Claude Code 桌面 App，2026-11-17 踩到）：\n  - 管線的結束碼是 `${pipestatus[1]}`，不是 bash 的 `PIPESTATUS`。提交指令要用 `&&` 綁住驗證的結束碼，不要靠管線之後再讀。\n  - `echo =====` 會被當成 `=` 開頭的檔名展開而失敗；印分隔線改用 `echo ----` 或加引號。\n  - 沒加引號的 `$變數` 不會被拆成多個參數。拿它裝多個 git pathspec，會變成一個比對不到任何檔的 pathspec，結果是「零命中」而不是錯誤；多個參數要逐個寫出或用陣列。\n'
TEMPLATES['.claude/skills/handoff/mode-0.md'] = '<!-- source: PROJECT-BOOTSTRAP.md v2026-11-20.2 — 權威版在部署包，改這裡之前先改部署包再同步各專案與全域副本 -->\n\n# 模式 0：建制\n\n> 2026-11-10 拆分 handoff skill 時逐字搬自單檔 `SKILL.md`。B6、B9 在 `mode-b.md`；「session 命名」見入口 `SKILL.md`。\n>\n> 2026-11-13（需求決策書 v3）：本目錄降為碰到才讀的參考；必守的條件在 `AGENTS.md` 的共用制度一節，衝突時以它為準。文內提到的 `[git-check]` 判讀行、「全綠」行已由只報事實的 `[facts]` 取代。\n>\n> 2026-11-18（需求決策書 v3 Q49）：建制改成「跑安裝程式，再處理第一批工作」。逐檔照抄、換佔位符與刪部署包的步驟拿掉；遠端與工具驗收從部署包第 5 節搬進 0-6。\n\n## 0. 建制（這個資料夾還沒有這套制度）\n\n**這一模式是「跑安裝程式，再處理第一批工作」，不是交接。** 寫檔、換佔位符、比對雜湊與 `git init` 都由 `bootstrap.py` 做；agent 只做需要理解專案的部分，也就是安裝程式寫進 `HANDOFF.md` 的第一批工作。本節只是執行順序與停止判準。\n\n### 0-1 先確認你在對的資料夾、對的情境\n\n```bash\npwd && ls -a && git status -sb\n```\n\n| 看到 | 動作 |\n|---|---|\n| 空資料夾 | 標準情境，往下走 |\n| 已有 `.bootstrap/answers.json` 或 `.claude/skills/handoff/` | **這不是建制**：要接手走模式 A；要升級骨架跑 `python3 bootstrap.py update`（先預演，加 `--write` 才寫入） |\n| 已有程式碼、README 或 Git 歷史 | 可以裝，但**先跟使用者確認**：安裝程式不覆寫任何同名檔，新內容寫到旁邊的 `<路徑>.bootstrap-new`，之後在 0-4 合併 |\n| 這是家目錄、桌面或某個大目錄 | **停**：先確認資料夾。灑錯地方的檔案沒人會逐一刪乾淨（安裝程式也會拒絕家目錄與桌面） |\n\n🚫 使用者點頭之前不要跑安裝程式。\n\n### 0-2 取得安裝程式（沒有它就停）\n\n`bootstrap.py` 是 project-bootstrap repo 根目錄的單一檔，只用 Python 標準函式庫，需要 Python 3.12 以上。手邊沒有就**停下來跟使用者要**，不要從別處找一份來跑。\n\n🔴 **絕對不要憑記憶重刻骨架。** 憑印象生出來的版本，缺的永遠是最貴的那部分——每條規則後面的「為什麼」、hook 的邊界條件、`check_docs.py` 那幾項檢查。看起來像那套制度，實際上擋不住任何事，而且沒有任何跡象；下一棒會以為自己有防護網。\n\n### 0-3 跑安裝程式（訪談由程式問）\n\n```bash\npython3 bootstrap.py --target <專案資料夾>\n```\n\n訪談題目由程式一次問完。拿不到的答案就**留空**，不要自己編一個看起來合理的值——編出來的網址、憑證檔名會被下一棒當成事實，然後照著它去連一個不存在的東西。留空的題目在檔案裡寫成 `<部署後填>`，並列進第一批工作。\n\n不能互動時用答案檔或參數：`--answers <檔案.json>`、`--set KEY=VALUE`（可重複）、`--non-interactive`。答案存在專案的 `.bootstrap/answers.json`，日後 `update` 會用；**答案裡不得有祕密**，程式看到金鑰樣式會拒絕。\n\n安裝程式不碰網路、不 commit、不推送、不建 GitHub repo；不在任何 Git 工作樹裡時會 `git init -b main`（不 add、不 commit），已經在 Git 工作樹裡就不動（`--no-git-init` 可關掉）。**exit 0 才往下**；非 0 照它印的原因回報，不要手動補檔。\n\n### 0-4 第一批工作（寫在 `HANDOFF.md` 的「未完成／下一步」）\n\n安裝程式把「工作中」設成 `無（已交棒）`，第一批工作寫在 `HANDOFF.md`，所以下一棒照平常接棒（模式 A）就會接手。逐項做：\n\n- **合併 `*.bootstrap-new`**：原檔是專案的，新內容是骨架的。比對兩份，把骨架的部分合進原檔：`AGENTS.md` 把共用制度那一段（開始到結束標記）整段放進原檔、標記外的專案內容不動；`.gitignore` 只補缺的行；`.claude/settings.json` 只補骨架那兩支 hook 的接線，專案自己的設定原樣保留。合完刪掉 `.bootstrap-new`。拿不準的停下來問使用者。\n- **補寫需要理解專案的檔**：`ARCHITECTURE.md` 的「專案本體」、`README.md`、`docs/ai-notes/roadmap.md`。\n  `ARCHITECTURE.md` 的「專案本體」這時候通常還是空的，**照實寫「尚未有程式碼」**——不要先畫一個想像中的架構，那會被下一棒當成既成事實去對齊。\n- **填 `tools/verify_state.py` 的檢查項**，依訪談的「一鍵驗證該查什麼」；沒有答案就先問使用者。\n- **回答留空的題目**：問使用者，答案寫回 `.bootstrap/answers.json`，檔案裡的 `<部署後填>` 換成實際值。訪談說的「絕對不能做」寫成 `AGENTS.md` 共用制度標記外的鐵律，附理由與日期。\n- **建 GitHub repo 與首次推送**：照 0-5、0-6。\n\n### 0-5 本機驗收後才首次發布\n\n⚠️ **`.gitignore` 必須先就位再 `git add`**。順序反了祕密就進第一個 commit，之後刪不掉——那是要重建 repo 的等級。\n安裝程式第一個寫的就是 `.gitignore`，但 0-4 合併過的話要再看一次。\n\n```bash\ngit status --porcelain\n```\n\n確認清單裡沒有憑證／運行資料後，**逐檔或逐目錄** `git add <路徑>`，不用 `git add .` 或 `git add -A`，再看 staged 清單：\n\n```bash\ngit diff --cached --name-only\n```\n\n依訪談逐一執行 `git check-ignore -- <憑證或運行路徑>`，必須列出該路徑；不要以檔案還沒建立為理由略過。核對 staged 清單沒有任何憑證或運行資料。關鍵字掃描只能降低風險，不能涵蓋所有祕密格式。接著跑兩個本機檢查：\n\n```bash\npython3 -X utf8 tools/check_docs.py\npython3 -X utf8 tools/verify_state.py\n```\n\n（Windows 上沒有 `python3` 就用 `python`。）文件必須 exit 0；服務 FAIL／ERROR 不得當通過，SKIP／NOT_CONFIGURED 明列原因與待配置事項。`SKILL.md` 前三行必須是 frontmatter，壞掉 skill 就不會被載入，整套自動化靜默失效。核對 `ARCHITECTURE.md` 與 `HANDOFF.md` 是實況。\n\n這些本機驗收全部完成才建立第一個 commit：\n\n```bash\ngit commit -m "chore: bootstrap project management skeleton"\n```\n\n建 GitHub repo 與第一次 push 前**先問使用者確認**（owner／repo 名、public 或 private）：這是外部動作，不是本機檔案操作。\n需先裝好 `gh` 並登入：\n\n```bash\ngh repo create <owner>/<repo> --private --source=. --remote=origin --push\n```\n\n沒有 `gh` 就到 GitHub 網頁開一個空 repo，然後 `git remote add origin <網址>` 與 `git push -u origin main`。最後 `git status -sb` 確認 upstream 有對齊（hook 需要 upstream 才能比對）。遠端與工具注入尚未驗證，留到 0-6，不可預先寫成通過。\n\n### 0-6 遠端與工具驗收\n\n2026-11-18 起從部署包第 5 節原文搬來（Q49）；文內的「3.x」與「開頭那一節」指 project-bootstrap repo 的部署包說明 `src/kit/kit.md`（2026-11-18 以前是生成的 `PROJECT-BOOTSTRAP.md`，Q50）。0-5 已先完成本機驗收。這一節補遠端、runtime 與工具實際注入的驗收；逐項回報，全過或明列不適用／未配置才算交代完整，未驗證不能宣稱通過。\n\n- [ ] `python -X utf8 tools/check_docs.py` → `OK`（一次涵蓋死連結與**殘留佔位符**；佔位符那一項掃 `.md`／`.py`／`.sh`／`.json`／`.gitignore`／`.gitattributes` 的 tracked 檔，所以要先 `git add`）\n- [ ] `python -X utf8 tools/verify_state.py` → 可執行（尚未填檢查項時印 `NOT_CONFIGURED`，正常）\n- [ ] `bash .claude/hooks/git-freshness.sh` → 印出三行 `[facts]`：時間（含 session 名用的 `MM.DD.HH`）與本機、落後 0 領先 0、origin 上「工作中」那一行的原文。印「origin 上沒有分支」表示 0-5 沒做完\n- [ ] **子目錄也要有防護**（2026-11-02／F05）：`cd tools && sh -c \'bash "$(git rev-parse --show-cdup).claude/hooks/git-freshness.sh"\'; cd ..` → 要印出跟在根目錄一樣的 `[facts]`。**要跑的是 `.claude/settings.json`／`.codex/hooks.json` 裡原始的那一串命令**，不是直接拿完整路徑跑腳本——後者在任何 cwd 都會過，測不到入口。hook 的 `command` 以 session 的 cwd 執行，而人會從子目錄開 session（`cd tools && claude`）；舊接線在那裡是 exit 127，而 **SessionStart 失敗跟「檢查過了沒事」在畫面上一模一樣**\n- [ ] **工作中標記看得見**：把 `HANDOFF.md` 的「工作中」改成 `` `假機器名` ／ `Claude Code` ``，commit、push，再跑 `bash .claude/hooks/git-freshness.sh` → 第三行要印出那個值的原文；改回「無（已交棒）」、commit、push 後再跑 → 要印回 `無（已交棒）`。**驗完記得改回來**\n- [ ] **共用制度版本提示**：`printf 2099-01-01 > .claude/.bootstrap-version && bash .claude/hooks/git-freshness.sh` → 要多印一行「共用制度落後」。快取裡放的是**上游最新版**，所以要餵一個比本機**新**的值。**驗完刪掉那個快取檔**（`rm .claude/.bootstrap-version`），否則 12 小時內都會拿到假答案\n- [ ] `.claude/skills/handoff/SKILL.md` 存在，前三行是 `---` / `name: handoff` / `description: ...`（frontmatter 壞掉 skill 就不會被載入）；同目錄有 `mode-a.md`、`mode-a-stop.md`、`mode-b.md`、`mode-0.md`、`reasons.md` 五個檔，六個檔檔頭的 `source:` 版本相同（少一個，入口就會指向不存在的檔）\n- [ ] **`CLAUDE.md` 只有 `@AGENTS.md` 這一行 import**，不是「去讀 AGENTS.md」那種句子——有 `CLAUDE.md` 時 Claude Code 不會自己讀 `AGENTS.md`，而用文字請它去讀不保證它真的開那個檔（理由見開頭「跨工具與跨平台」）。開一個 session 問它「`AGENTS.md` 的鐵律第 1 條是什麼」，答得出來才算接上\n- [ ] `ARCHITECTURE.md` 存在且有「最後更新」標頭（`check_docs.py` 會擋），「專案本體」那節寫的是**實況**——還沒有程式碼就照實寫，不要先畫一個想像中的架構\n- [ ] 在 Claude Code 打 `/handoff` 看得到這個 skill\n- [ ] pre-push hook 會放行無關指令：`echo \'{"tool_input":{"command":"git status"}}\' | bash .claude/hooks/pre-push-handoff.sh; echo $?` → `0`\n- [ ] `git log --stat -1` 確認第一個 commit **沒有**含憑證或運行資料\n- [ ] 關掉 session 重開一次，確認 hook 在對話開頭自動跑\n\n**跨工具（只驗你真的會用的那幾個，用不到的不必建檔）**\n\n- [ ] **可攜層**：`AGENTS.md` 有共用制度一節（開始與結束標記之間 ≤ 40 行）——**這一項不能跳過**，它是唯一不需要任何設定就會被讀到的那一層（**「讀得到」不等於「照做」**，見開頭那一節），其餘都只是輔助\n- [ ] **Codex CLI**：`.codex/hooks.json` 與 `.claude/hooks/codex-hook.cmd` 存在且接線路徑全是相對路徑（`grep -n \':[\\\\/]\' .codex/hooks.json` 應無輸出——絕對路徑在別台機器會靜默失效）；**專案要先被信任**（否則整層 `.codex/` 被跳過）；Windows 的 `commandWindows` 要指向 `.claude/hooks/codex-hook.cmd`，該檔也必須在場；然後**開一次互動式 `codex`**——它開場就會問「Hooks need review」，選 `Trust all and continue`（想一條條看就選 `Review hooks`）。🔴 **這一項不能只看檔案在不在**，而且有三個會讓你誤判的點：①**信任綁 `hooks.json` 的絕對路徑，所以每個專案都要各做一次**，審過一個不會全通；②**在那個 session 裡送出一句話才驗得到**——2026-11-01 實測互動 TUI 開場不跑 `SessionStart`，它跟著第一個 turn 才跑；舊版這裡寫「你按下同意的那個 session 不會跑，要再開一個才算」，那是推論而實測是反的，而且它教人用**保證看不到**的方式驗收（再開一個、然後盯著開場）；③**不要去畫面上找 `[git-check]`**——Codex 把純文字 stdout 當 developer context 餵給模型、不顯示給人，所以要驗就問 agent 一個不必複述的是非題（「只回 YES／NO：你的 context 裡有沒有以 `[git-check]` 開頭的行」），或暫時讓 hook 自己寫一個檔。`codex exec` 從頭到尾不問也不印，**不能拿它當驗收手段**（2026-10-30／31 兩輪實測）\n- [ ] **Codex skill 來源**：`codex debug prompt-input` 會印一張「Skill roots」表，確認裡面有 `~/.codex/skills`（全域副本放這裡）與本專案的 `.agents/skills`。這比問模型「你有哪些 skill」可靠，也不花一次模型呼叫\n- [ ] **Codex 桌面 App**：它**有** hooks（App `26.506` 起有 in-app 信任審核，Settings 裡找 Hooks），而且跟 CLI 共用 `~/.codex`。舊版這裡寫「App 沒有 hooks」是 2026-08-06 的實測，已經過期。全域 skill 仍然放 `~/.codex/skills/handoff/SKILL.md`（2026-10-30 實測 CLI `0.164.0` 仍讀這個路徑，雖然官方文件已經不列它）\n- [ ] **Codex 指標檔**：`.agents/skills/handoff/SKILL.md` 存在，內容只有指標、沒有複製程序內容（見 3.16）\n- [ ] **共通的真正驗收**（不論哪個工具）：在專案裡講一句「我要接手這個專案」，agent 應該先 `git fetch`、讀 `AGENTS.md` ＋ `HANDOFF.md`，回報 3–5 行才動手。它直接開始翻程式碼就是沒接上——改用明講版：「請先讀 `.claude/skills/handoff/SKILL.md`，照 A 模式接棒」\n- [ ] **另一台機器**：clone 後重跑上面「python 可執行」與「hook 自動跑」兩項。`python` 不存在就用 `python3`；Windows 需要 Git for Windows 附的 bash\n- [ ] `HANDOFF.md` 的「本機能力」已填實際狀況\n- [ ] 沒有留下 `*.bootstrap-new`：每一份都已合進原檔並刪掉（0-4）。留著的話，下一棒分不出哪一份才是現行的\n\n### 0-7 回報\n\n建制本身就是第一段工作，所以照 **B6** 覆寫 `HANDOFF.md`（任務目標＝骨架已就緒；做完的第一批工作移到「已完成」，沒做完的留著），再照 B9 收尾。回報 ≤5 行：裝了哪一版、驗收結果、repo 與分支、**還沒填的洞**、下一棒第一件事。\n'
TEMPLATES['.claude/skills/handoff/mode-a-stop.md'] = '<!-- source: PROJECT-BOOTSTRAP.md v2026-11-20.2 — 權威版在部署包，改這裡之前先改部署包再同步各專案與全域副本 -->\n\n# 模式 A：完整判讀與異常處理\n\n> 2026-11-10 拆分 handoff skill 時逐字搬自單檔 `SKILL.md`。`mode-a.md` 是正常路徑的摘要，衝突時以本檔為準。文內的「session 命名」見入口 `SKILL.md` 與 `reasons.md` 的同名節；B 各步驟在 `mode-b.md`。\n>\n> 2026-11-13（需求決策書 v3）：本目錄降為碰到才讀的參考；必守的條件在 `AGENTS.md` 的共用制度一節，衝突時以它為準。文內提到的 `[git-check]` 判讀行、「全綠」行已由只報事實的 `[facts]` 取代。\n\n### A／B／C 狀態轉移（2026-11-02／F11）\n\n| 狀態 | 前提 | 允許操作 | 成功證據 | 失敗處理 |\n|---|---|---|---|---|\n| 待接棒 | 尚未取得寫入資格 | A1 同步、A2 定位分支、A2.5 查占用 | fetch exit 0；乾淨；ahead=0、behind=0；origin 標記可依 A2.5 續行 | fetch 失敗／ahead-only／分岔／未知 dirty：停下回報，等待指示 |\n| 已定位 | A1／A2／A2.5 通過 | A3 讀取、A4 驗證並記錄差異、A5 回報 | 驗證結束碼、FAIL／ERROR／SKIP／NOT_CONFIGURED 與差異已列出 | 未驗證不可寫成通過；只讀記錄，修檔延至 A5 開工成功後 |\n| 開工中 | A5 回報完成且確定要改檔 | 只提交 HANDOFF 開工標記，fetch 確認遠端未意外前進後 push | push exit 0；origin 的工作中欄位是本 session | push 失敗停止修改，詢問是否接受沒有標記保護；遠端意外前進則停下 |\n| 工作中 | A5 開工成功 | 執行已授權任務；C 推安全點走 B7 → B8 | 最終文件檢查 exit 0；push exit 0；本地與 upstream 對齊；origin 仍是本 session 工作中 | 驗證失敗修正或明記風險；fetch／push 失敗不宣稱同步成功 |\n| 待交棒 | B1–B6 已完成 | B7 驗最終快照並安全提交，再走 B8 | 最終文件檢查 exit 0；push exit 0；工作樹乾淨且與 upstream 對齊；origin 標記為無（已交棒） | 最終文件檢查失敗不可發布；fetch／push 失敗不交棒、不加次數 |\n| 已交棒 | B8 成功且遠端標記已清 | B9 改名並增加一次；新訊息依續聊規則恢復活動 | origin 工作中欄位與 session 回報可核對 | 改名失敗如實回報，重試不重複計數；再改檔前重走 A |\n\n**證據的範圍**：驗證工具不存在或專案另有驗證入口時，依 AGENTS.md 執行並明記替代指令／不適用原因；不可把缺工具當成 exit 0。狀態表不把服務 FAIL／SKIP 自動變成通過，也不把工作中標記當成互斥鎖。\n**為什麼要列狀態**：舊程序漏掉 ahead-only／fetch 失敗，切分支後沿用舊檢查，A4 又在 A5 之前叫人修檔；B6 改了快照卻只引用 B4 的舊結果，且所有 push 都被描述成交棒。這些順序互相打架，不能靠接手者自行猜例外。\n\n---\n\n## A. 接棒\n\n### A1 先同步 Git（未同步前不要相信本機任何文件，包括 HANDOFF）\n\n```bash\ngit status -sb && git fetch origin && git status -sb && git log --oneline -3\n```\n\n判讀表——**只有前兩列可以自己往下走**：\n\n| 看到 | 動作 |\n|---|---|\n| 乾淨、落後 origin | `git pull --ff-only` 後繼續 |\n| 乾淨、與 origin 一致 | 直接繼續 |\n| 乾淨但 ahead-only（ahead > 0、behind = 0） | **停**：列出未推送 commit 與來源，等待使用者指示；不得自動 push、reset 或把它當成已同步 |\n| fetch 失敗（非零退出） | **停**：保留錯誤輸出，遠端新鮮度未知；不得用舊 tracking ref 宣稱同步完成 |\n| 有未提交變更，來源不明 | **停**：貼 `git status --porcelain` 與 `git diff --stat`，問使用者這是誰留下的 |\n| 已分岔（同時 ahead＋behind） | **停**：回報落後／領先數與雙方 commit 標題，等指示 |\n| pull 不能 fast-forward | **停**：不要 rebase／merge 到一半才問 |\n| 沒有 upstream | **停**：回報，不要自行 `push -u` 建立 |\n\n🚫 全程禁止：`reset --hard`、`push --force`、自行 `stash`、覆寫他人 commit、刪 branch。\n\nfetch 成功後才判讀；用 `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}` 確認 upstream，再用 `git rev-list --left-right --count HEAD...@{upstream}` 取得 ahead／behind（左／右）。PowerShell 請把 `@{upstream}` 引號包住。pull 成功後重查 `git status --porcelain` 與計數，乾淨且兩者為 0 才進 A2。detached HEAD、無法讀取計數或 upstream 不對應 `origin/<當前分支>` 時停下回報，不猜比較對象。\n\n### A2 站對分支\n\n讀 `HANDOFF.md` 的「待續分支」：\n\n- 寫「無」→ 待在權威分支（通常 `main`）。\n- 指向 `feature/...` → **那條才是主幹，`main` 可能明顯落後**。要續作就 `git switch <branch>`；不要因為 `main` 是預設分支就以為它最新。\n- 要開新分支 → 從**現在的主幹**開，不是從 `main` 開。\n\n**切換到待續分支後重跑 A1**（含 fetch、upstream、dirty 與 ahead／behind 判讀），再讀該分支的 HANDOFF 並走 A2.5；不可沿用切換前的通過結果。切換失敗就停下，禁止自動 stash。\n\n### A2.5 檢查這條分支有沒有人正在工作（跨機器誤接棒防呆）\n\n**本制度支援接力式 single-writer。「工作中」是協調訊號，不是互斥鎖。** 同一工作樹不得同時有兩個 writer；機器／工具／可變 session 標題不是穩定 owner token。A2.5 到 A5 仍有時間窗，Git 的 non-fast-forward 拒絕不能保護共用 index 與未提交檔案。\n**時間戳不代表租約到期，不得自動奪取 writer**；未知是否仍在工作時，保留標記並請使用者確認。原子 claim 尚未實作，也未做並行實驗，不宣稱有並行互斥保證（2026-11-02／F12）。\n\n**站對分支之後、讀文件之前**，看該分支 `HANDOFF.md` 的「工作中」欄位：\n\n```bash\ngit show "origin/$(git rev-parse --abbrev-ref HEAD):HANDOFF.md" | grep -F "**工作中**"\n```\n\n讀 `origin/` 那一份、**不讀本機的**——此刻可能還沒 pull，本機那份是舊快照。\n同時記錄觀測到的 `origin/<當前分支>` SHA，A5 再 fetch 時必須與此值比對；不能只看 ahead／behind 或標記文字。\n\n| 看到 | 動作 |\n|---|---|\n| `無（已交棒）` | 正常，往下走 |\n| 沒有這個欄位 | 這個專案的骨架還沒升級到有這個機制，照舊往下走——但**別把「沒有欄位」當成「沒人在做」**，這一輪沒有防呆，心裡要有數。欄位由 **A5** 寫標記時一併補上，那也就是這個專案的升級點 |\n| 指向**別台**機器 | **停**，見下方三個選項 |\n| 指向**這台**機器，工具欄是**你自己這個工具** | 多半是你自己還開著的另一個 session。核對標記裡的 session 名與開工時間對不對得上你開過的那一個；對不上就照「別台機器」處理 |\n| 指向**這台**機器，工具欄是**別的工具** | **停**，照下方三個選項處理（選項 1 的「回那台機器」換成「回那個工具的 session」）。**這比跨機器更急**：跨機器至少是兩份磁碟，同機器通常就是同一個資料夾，兩個 agent 會即時互相覆寫 |\n| 指向**這台**機器，**沒有工具欄**（舊格式） | 當成「別的工具」處理。分不出來的時候**不要往放行的方向猜** |\n\n**指向別台機器時不要自己決定**，把這三個選項給使用者：\n\n1. **回那台機器走完交棒**（預設建議）——那台的未提交變更只在那台的磁碟上，這裡拿不到\n2. 使用者確認那台已經沒在跑 → 授權在這裡接手，由本 session 清掉舊標記並照 **A6** 回推補交接\n3. 這次只讀不寫 → 不接棒、不寫標記、不動任何檔案\n\n> **工具名的權威是寫標記的那一棒自己填的，不是環境變數。** 模型知道自己是哪個工具，三個平台都一致；\n> 而環境變數在「從一個工具的殼層啟動另一個工具」時會被繼承——Codex 的 session 會自稱 Claude Code\n> （2026-10-31 實測，細節見部署包「工具身分」一節）。所以 hook 的變數偵測只用來**加嚴**：\n> 它看到的工具跟標記不一致就直接 🔴；一致、或認不出來，都只給 🟡 並把「你自己是不是 X」這一句丟回來給你答。\n> **永遠不因為偵測失敗而放行。**\n>\n> **舊版只比機器名**，於是同機器換個工具會落進「大概是你自己另一個視窗」的 🟡，\n> 而那時候叫人去驗的證據是「側欄有沒有 `㊣`」——只有 Claude Code 有側欄。\n> 判準綁在一個工具的介面上，另外三個平面就等於沒有判準。\n\n> **為什麼標記寫在開工而不是收工**：寫在開工的標記不依賴任何人記得收尾——A 沒交棒，標記就留在 origin 上，下一棒一定看得到。\n> 2026-10-30 重查後，這條規則的理由要講得更準：Claude Code 與 Codex **有** `SessionEnd` 事件（Codex 的還會在閒置 30 分鐘時觸發）。但那個事件救不了這件事——它**不能擋下結束**，Claude Code 那邊預設只有 1.5 秒預算，做不完一次 `git push`。所以它最多提醒**離場的那一個人**，擔保仍然只能押在「開工就推上 origin」這一邊。\n> **它救不回什麼**：A 那些未提交的變更仍然只在 A 的磁碟上。標記只讓你知道「有東西在那台機器」，東西還是得回去拿。\n\n### A3 最小讀取\n\n只讀 `AGENTS.md` ＋ `HANDOFF.md`。其他文件等任務真的碰到再讀（`ARCHITECTURE.md` 列了每份檔案的用途）。\n**不要**為了「先了解全貌」把 `docs/` 全讀一遍——那是 token 黑洞，也不會讓你更準。\n\n### A4 一鍵驗證\n\n```bash\npython -X utf8 tools/verify_state.py\n```\n\n（`python` 不存在就用 `python3`；腳本不存在就跳過並在回報寫明。）\n**一律跑**，不是「有憑證才跑」：不需要憑證的本機與公開檢查照樣會動，缺憑證只讓需要它的那幾層記 SKIPPED。舊版寫「有憑證就跑」，整支腳本會被一個不相干的前提擋掉（2026-11-02／F15）。\n與 HANDOFF 的「服務查證與期望快照」比對。不一致時**以實況為準**，此步只記錄差異與結束碼、不修改專案檔案；到 A5 回報且開工標記 push 成功後，才修文件並註記絕對日期。FAIL／ERROR 是待修問題，SKIP／NOT_CONFIGURED 是未驗證，不能寫成通過。\n\n🔴 **標 SKIPPED 前先排除「設定沒帶到」**：連線失敗 ≠ 本機沒有憑證。先確認該機器的憑證路徑／環境變數是不是沒設，是不是暫時性網路錯誤（重試 2–3 次）。確認憑證真的不存在才寫 `SKIPPED（本機未配置）`。**不得**從系統資料庫、其他主機、Git history 或別台機器自行挖取／搬運憑證。\n\n### A5 回報後才動手（3–5 行）\n\n```text\nGit：<分支>、<與 origin 關係>、<待續分支>\n驗證：<verify_state 關鍵值／SKIPPED 與原因>\n現況：<用自己的話講一句現在做到哪>\n下一步：<我打算做的第一件事>\nsession：㊣\u3000<MM.DD.HH｜主題>｜工作中｜交棒<N>次（已改）／不適用：<本工具不能改名>；交棒<N>次\n```\n\n不要重述整份 HANDOFF。有疑問就多一行問題。\n\n**首次接棒回報完就改 session 名稱**成 `㊣\u3000MM.DD.HH｜<主題>｜工作中｜交棒<N>次`（規則見「session 命名」）；**已交棒後續聊在收到新訊息時就先恢復工作中，不等 A5**。然後把實際結果寫進模板最後那行 `session：`——改了就寫改成什麼，工具沒有這個能力就寫 `不適用：<原因>` 並附交棒次數，不必為此停下來問使用者。**那一行不能省**：寫不出來就是沒做，而這是唯一看得出來的地方。這一步跟下面的開工標記是兩件事，**不要等它**。\n\n**確定要動手改東西，才寫開工標記。** 只讀、只問問題的 session 不寫——那會在權威分支的歷史裡堆一堆沒有內容的 commit，而被灌爆的歷史沒人會認真看。\n**開工標記是協調訊號，不是互斥鎖**；先確認同一工作樹只有一個 writer。遠端 SHA 與 A2.5 觀測值不同就停止；失敗的開工不能當一般 merge 衝突合併。push 後重讀 owner 只確認遠端標記內容，不等於取得原子 claim。\n\n1. 把該分支 `HANDOFF.md` 的「工作中」欄位改成本機與本 session。舊專案沒有這一欄，就在「Git 狀態」那節補一列（這就是該專案的升級點，不用另外安排一次升級）：\n\n   ```markdown\n   - **工作中**：`desk-win` ／ `Claude Code` ／ `㊣\u300010.30.09｜匯入格式｜工作中｜交棒0次`，2026-10-30 09:12 (+08) 開工\n   ```\n\n   三欄，用全形斜線 `／` 分隔：**機器** ／ **工具** ／ **session 名**（最後一欄可選，環境沒有 session 名就省略）。\n\n   - **工具欄不能省**（2026-10-31 加）。少了它，同一台機器換個工具就會落進「大概是你自己另一個視窗」的 🟡，\n     而同機器通常就是同一個工作樹——兩個 agent 即時互相覆寫，比跨機器那個洞更貴。`check_docs.py` 第 6 項會擋。\n   - **工具名用慣用寫法**（`Claude Code`／`Codex CLI`）：hook 比的是這個字串，\n     寫同義詞只會讓它多報一次 🔴——那是加嚴的方向，不會放行，但也是噪音。\n   - 記 session 名稱比只記機器名有用——有側欄的工具可以直接拿它把那個 session 點開。\n\n2. **只** stage `HANDOFF.md`，核對 staged 清單後 commit；重新 fetch，確認遠端沒有比 A2.5 觀測值意外前進才 push 到**當前分支**。訊息用 `chore(handoff): <機器> 開工` 這類前綴，之後掃歷史時一眼可略過。這是開工 push 例外，不先走 B6 清標記、不宣稱交棒；push 成功後重讀 origin 的工作中欄位，確認是本 session，才開始任務修改。\n**push 失敗就不是「已標記」**：明確告訴使用者「這次沒有標記保護，別台機器不會知道我在做」，問他要不要在這個狀態下繼續。**不要靜默往下做**——你會以為有保護，實際上沒有。（名稱照樣是 `㊣`——它說的是「這個 session 在做事」，不是「標記已經在 origin 上」。）\n\n規則一句話：**側欄講的是這個 session，HANDOFF 講的是這條分支。** 只有 `↗ 已交棒` 是在宣稱一件 git 的事，所以只有它要等 push 成功。\n\n### A6 回推補交接（只有在 A1 判定「前一輪漏交棒」時才走）\n\n前一輪做完沒交棒，工作樹留著未提交變更，`HANDOFF.md` 停在更早的狀態。\n**這種情況下最貴的損失不是那個 commit，是知識**——理由與取捨會永久消失，\n只有留在磁碟上的東西救得回來。理由與事故的完整記述在同目錄 `reasons.md` 的\n「漏交棒的補救」一節（2026-11-17 起；之前在專案的交接協定裡，v3 Q41）。\n\n1. 先**唯讀**盤點產物：新產出的結果目錄、檔案 mtime、`git reflog`、結果檔裡的\n   費用／參數。算出實際花了多少錢——`HANDOFF.md` 的費用欄多半已經錯了。\n2. 問使用者三件事：**要不要收斂進這條分支**、**有沒有已知該留／該刪的東西**、\n   **要不要補跑未完成的部分**（會花錢的一律等他點頭）。\n3. **先落地知識（B2）再 commit（B7）**，讓知識與產生它的程式碼進同一批 commit。\n4. 回推寫成的段落**一定要標明「這是事後回推、當時無記錄」**，\n   **不要替它補理由**——編出來的理由會變成下一棒眼中的既成事實。\n5. 修掉 `HANDOFF.md` 裡與實況矛盾的陳述，然後照 B 模式正常收工。\n\n> 三層防呆（SessionStart／`hooks.json`／pre-push）擋不住這件事：它們全都掛在\n> 「下一個動作」上。Claude Code 與 Codex 另外有 `SessionEnd`（2026-10-30 查），但它不能擋下\n> 結束、預算只有 1.5 秒，推不了東西上去。所以這仍然是**程序\n> 責任，不是工具責任**。\n'
TEMPLATES['.claude/skills/handoff/mode-a.md'] = '<!-- source: PROJECT-BOOTSTRAP.md v2026-11-20.2 — 權威版在部署包，改這裡之前先改部署包再同步各專案與全域副本 -->\n\n# 模式 A：接棒（正常路徑）\n\n> 碰到才讀的參考。必守的條件在 `AGENTS.md` 的共用制度一節，衝突時以它為準。本檔只寫「一切正常」的走法；任何一步跟這裡寫的不一樣，讀同目錄的 `mode-a-stop.md`（完整判讀表、占用處理、漏交棒補救）。A1–A4 不修改任何檔案。\n\n## A1＋A2.5 同步與占用：讀開場的 [facts]\n\n開場 hook 會 fetch 一次，印出幾行 `[facts]`：時間（含 session 名用的 `MM.DD.HH`）、本機、分支；與 `origin/<當前分支>` 的落後與領先、origin 的短 SHA、未提交檔數；origin 那份 `HANDOFF.md` 的「工作中」原文。只報事實，判讀由你做。\n\n一切正常的樣子：fetch 成功、落後 0、領先 0、未提交 0、「工作中」是 `無（已交棒）`。這時記下 origin 的 SHA（A5 要比對），往下走。\n\n**它是快照，不是通行證。** 下列情況先重跑一次 `bash .claude/hooks/git-freshness.sh`，以新輸出為準：已交棒後續聊要改檔、之後切換過分支、工具沒有跑 hook 或開場找不到 `[facts]`。\n\n任何一個值不是上面那樣（含腳本跑不起來、專案沒有這支 hook）：不要自己判斷「大概沒事」，讀 `mode-a-stop.md` 的 A1 與 A2.5 照表走。\n\n## A2 站對分支\n\n讀 `HANDOFF.md` 的「待續分支」。寫「無」就待在權威分支；指向別條分支就 `git switch <branch>`（切換失敗就停，禁止自動 stash），**切換後重做 A1**。要開新分支，從現在的主幹開，不是從 `main` 開。\n\n## A3 最小讀取\n\n只讀 `AGENTS.md` ＋ `HANDOFF.md`；其他文件等任務真的碰到再讀。\n\n## A4 驗證（只記錄，不修）\n\n```bash\npython -X utf8 tools/verify_state.py\n```\n\n`python` 不存在就用 `python3`；`AGENTS.md` 指定別的驗證入口就照它；沒有工具就在回報寫明。與 HANDOFF 的「服務查證與期望快照」比對，以實況為準，差異留到開工標記推上去之後才修。FAIL／ERROR 是待修問題，SKIP／NOT_CONFIGURED 是未驗證，都不能寫成通過。要把連線失敗標成 SKIPPED 之前，先讀 `mode-a-stop.md` 的 A4。\n\n## A5 回報後才動手\n\n```text\nGit：<分支>、<與 origin 關係>、<待續分支>\n驗證：<verify_state 關鍵值／SKIPPED 與原因>\n現況：<用自己的話講一句現在做到哪>\n下一步：<我打算做的第一件事>\nsession：㊣\u3000<MM.DD.HH｜主題>｜工作中｜交棒<N>次（已改）／不適用：<本工具不能改名>；交棒<N>次\n```\n\n回報完就改 session 名稱（規則在 `AGENTS.md` 的「session 名稱」）。**只讀、只問問題的 session 不寫開工標記。** 確定要改檔才做下面四步，做完才開始改：\n\n1. 把 `HANDOFF.md` 的「工作中」改成本機與本 session（沒有這一欄就在「Git 狀態」補一列）：\n\n   ```markdown\n   - **工作中**：`desk-win` ／ `Claude Code` ／ `㊣\u300010.30.09｜匯入格式｜工作中｜交棒0次`，2026-10-30 09:12 (+08) 開工\n   ```\n\n   用全形斜線 `／` 分三欄：機器 ／ 工具 ／ session 名（第三欄可省）。**工具欄不能省**，寫慣用名（`Claude Code`／`Codex CLI`）。\n2. **只** stage `HANDOFF.md`，核對 staged 清單後 commit，訊息用 `chore(handoff): <機器> 開工`。\n3. 重新 `git fetch origin`。遠端 SHA 跟 A1 記下的不同就停；相同才 push 到當前分支。\n4. push 成功後重讀 origin 的「工作中」，確認是本 session。\n\n**push 失敗就不是「已標記」**：告訴使用者這次沒有標記保護，問要不要在這個狀態下繼續，不要靜默往下做。開工標記是協調訊號，不是互斥鎖；這次 push 是開工例外，不算交棒、不加次數。\n'
TEMPLATES['.claude/skills/handoff/mode-b.md'] = '<!-- source: PROJECT-BOOTSTRAP.md v2026-11-20.2 — 權威版在部署包，改這裡之前先改部署包再同步各專案與全域副本 -->\n\n# 模式 B：交棒；模式 C：中途同步\n\n> 2026-11-10 拆分 handoff skill 時逐字搬自單檔 `SKILL.md`。A／B／C 狀態轉移表與 A 各步驟在 `mode-a-stop.md`；文內的「session 命名」見入口 `SKILL.md` 與 `reasons.md` 的同名節。\n>\n> 2026-11-13（需求決策書 v3）：本目錄降為碰到才讀的參考；必守的條件在 `AGENTS.md` 的共用制度一節，衝突時以它為準。文內提到的 `[git-check]` 判讀行、「全綠」行已由只報事實的 `[facts]` 取代。\n\n### 同一 session 的交棒計數\n\n- **交棒次數的家是該 session 標題尾端的 `｜交棒<N>次`，新 session 從 0 起算。** A5、續聊與模式 C 都保留 N。沒有改名能力的工具，以同一 session 最近一次 `session：` 回報保存 N；上下文壓縮後也要從標題或這一行恢復。HANDOFF 仍是當下快照，不新增逐 session 清單；工作中欄位引用當時的完整 session 名稱即可。\n- **只有 B1–B8 完成且 B8 push 成功，才在 B9 把 N 加 1。** 開工標記、中途安全點、失敗的 push 與重複回報同一次成功交棒都不增加；第幾次 commit 也不是第幾次交棒。同一輪跨多個 repo 收尾，以本 session 的一次 B9 回報計一次，必要的 push 全部成功後才加 1。先保存成功結果與新的 N，再改名並回報，改名失敗後重試仍使用同一個 N。\n- **舊標題沒有次數時，先查本 session 的成功交棒回報，不拿別的 session 或整個 repo 的交棒數代替。** 能確認總數就補上；只知道至少交棒一次而無法還原總數，就寫 `交棒≥1次`，之後成功一次變成 `交棒≥2次`，保留「至少」的語意，不把未知編成精確數字。確定本 session 尚未交棒才填 0。\n- **為什麼（2026-11-02）**：使用者指出 agent 會在任務階段結束時自主交棒；使用者仍在同一 session 對話，側欄卻一直是「已交棒」。只在 A5／B9 改名漏掉了「同一 session 再收到訊息」這個狀態轉換。用 session 自己的計數保留它曾交棒的事實，才能同時表達現在在做事、以前已交棒幾次，又不把 HANDOFF 變成歷史表。\n\n---\n\n## B. 交棒\n\n**只有使用者要求交棒／收工／換人接手才走 B**；agent 自己覺得告一段落時走 C，不得自行交棒（理由見 `reasons.md` 的「交棒由使用者決定」）。\n\n九步，**順序就是執行順序**，做完一步再下一步。\n\n### B1 收斂到安全點\n\n**動任何檔案、提交或推送前先核對占用。** 先 `git fetch origin`，從 origin 上持有開工標記的分支讀取 `HANDOFF.md`，記下該分支的 SHA。用本 session 開工時已確認推送的完整標記比對，含機器、工具、當時的 session 名（有填時）及開工時間。同一台機器、同一工具或使用者請你交棒，都不足以證明標記屬於本 session。\n\n**標記屬於別人、缺失、已釋回或無法確認歸屬就停下**，回報遠端狀態，不改檔、不提交、不推送。fetch 失敗也停下。2026-11-15 的 Codex 占用者探針中，六個新 session 在同機器同工具下都釋回了舊 session 的標記，因此在第一步核對。\n\n**使用者明確確認舊標記與工作屬於自己時，照 `mode-a-stop.md` A2.5 選項 2 接手。** 例如使用者說「上一個 session 斷線了，工作中標記和未提交修改都是我們自己的，請交棒」。本 session 先把「工作中」改成自己、推上並重讀遠端確認，再走 A6 與本程序其餘步驟。只說「請交棒」或只是同機器同工具，不算確認（2026-11-16 使用者決定，需求決策書 v3 Q36）。\n\n未完成的東西二選一：完成並驗證；或 commit／push 到分支並在 HANDOFF 標明風險與已知安全 commit。\n**不留來源不明的工作樹**，也不要把半成品併進 `main`。\n\n**分支模型**（要開分支或併 `main` 時讀；2026-11-17 從專案的交接協定搬來，v3 Q41）：判準是「需不需要使用者驗收」。\n\n| 類型 | 例 | 能不能自己併 `main` |\n|---|---|---|\n| 功能分支（需驗收） | `feature/<ID>-<slug>` | 不能，要使用者驗收通過才併 |\n| 文件／基建分支（不需驗收） | `docs/cleanup`、`chore/…` | 能，驗證通過（`check_docs.py`＋`verify_state.py`）即可併 |\n\n- 文件／基建變更不得被功能驗收阻塞：文件被關在某個功能的驗收閘門後面，接手者「先同步 `main`」就拿到過期文檔集。小型文件修正可直接在 `main`，成批整理才開分支。\n- 功能分支若已成為事實上的主幹（`main` 明顯落後），新分支從該分支開，不要從 `main` 開，否則是在過期基礎上工作，日後必定衝突；開之前先在回報裡說明。\n- 本輪做不完就 push 分支，並在 HANDOFF 記錄分支名、已知安全 commit、未完成內容與風險。\n\n### B2 持久知識落地（今天學到的寫進 repo，不要留在對話裡）\n\n| 你剛剛得到什麼 | 寫進 |\n|---|---|\n| 一條「以後都要這樣做」的規則、一次踩坑 | `AGENTS.md` 鐵律（重大）或 `docs/ai-notes/<主題>.md`（細節） |\n| 做過兩次以上、而且踩過坑的操作步驟 | `.claude/skills/<slug>/SKILL.md` |\n| 還有哪些事沒做、什麼被否決／暫緩及理由 | `docs/ai-notes/roadmap.md` |\n| **專案結構變了**：新增／搬移目錄、換掉一個元件、改變資料流或權威版位置 | `ARCHITECTURE.md`（只有結構變動才動它，而且跟該變動同一個 commit） |\n| 現在做到哪、下一步 | `HANDOFF.md`（B6 才寫） |\n\n規則：**附絕對日期**（寫 `2026-08-05`，不要寫「今天」「上週」）；**每個事實只有一個家**，其他地方只放指標；新開 `docs/ai-notes/` 檔案要回頭在 `ARCHITECTURE.md` 補上一列，否則沒人找得到它（2026-11-17 起，`AGENTS.md` 只留開工必讀，沒有知識庫地圖）。\n\n### B3 服務驗證\n\n```bash\npython -X utf8 tools/verify_state.py\n```\n\n### B4 文檔驗證（動過任何 `.md` 就必跑）\n\n```bash\npython -X utf8 tools/check_docs.py\n```\n\n**exit 2 表示要修**（死連結／過期字串／缺日期標頭）。這些 `verify_state.py` 一項都查不到。\n\n### B5 條件式例行檢查\n\n本專案若有固定流程（部署、版本號 bump、測試、備份），對照 `AGENTS.md` 鐵律：這輪有動到就執行並記錄；沒動到就在 HANDOFF 明記「不適用」。\n**不要靜默略過**——接手者無法分辨「沒做」與「不用做」。\n\n**hook 接線有改或同步過，就驗收實際執行**；Codex 的信任審核與驗收方法見 `env.md` 的「Codex」。\n\n### B6 更新 `HANDOFF.md`（覆寫，≤80 行，不累積歷史）\n\n```markdown\n# HANDOFF — 工作交接狀態\n\n- **交接時間**：YYYY-MM-DD HH:MM（<時區>）\n- **交棒者**：<模型／機器>（主題一句話）\n\n## 任務目標\n<目前目標>\n\n## Git 狀態\n- Repo：`<owner>/<repo>`\n- **待續分支**：<無，或 feature/... @ 已知安全 commit>；若 main 落後主幹要註明\n- **工作中**：無（已交棒）\u3000← 交棒時必須是這個值；開工時由 A5 改成 `機器` ／ `工具` ／ `session 名`\n- 本機能力：<機器；哪些憑證可用／未配置，不寫祕密值>\n\n## 已完成\n- <事項與驗證>\n\n## 未完成／下一步\n1. <可執行步驟>\n\n## 地雷與注意事項\n- <最容易搞砸的事>\n\n## 服務查證與期望快照\n`python -X utf8 tools/verify_state.py`\n<目前實際關鍵輸出；未能查的層級寫 SKIPPED 與原因>\n\n## 懸置事項（AI 勿自行處理）\n- <等使用者決定的事>\n```\n\n⚠️ **不要在 HANDOFF 裡寫它自己的最終 commit hash**——提交 HANDOFF 的當下就過時了。最終 hash 放交棒回覆（B9）。\n⚠️ **「工作中」欄位要改回 `無（已交棒）`。** 這一欄是覆寫時最容易被原封不動抄過去的——交棒了卻還寫著「工作中」，下一棒會被擋在 A2.5，然後回頭去找一台其實已經收工的機器。\n⚠️ 舊內容直接覆寫，不要往下疊成日誌；歷史由 Git 查。\n\n### B7 安全提交\n\n**先驗最終快照**：B6 覆寫完成後，先明確 stage 本次檔案，再執行下列檢查。2026-11-03／R07：檢查器用 Git 檔案集合，先驗再 stage 會漏掉新增文件；部分 stage 又可能讓工作樹的好內容遮住 index 的壞內容。\n\n```bash\ngit diff --check && git status --porcelain\n```\n\n明確 stage 需要的檔案（**不要無腦 `git add -A`**），然後看過清單再 commit：\n\n```bash\ngit diff --cached --name-only && git diff --cached --stat\n```\n\n清單確認後執行 `python -X utf8 tools/check_docs.py --staged`（無 `python` 用 `python3`；專案有替代入口依 AGENTS.md），exit 0 才提交發布。`--staged` 拒絕本次待提交文件或檢查器同時有未暫存變更，不允許部分 stage 驗證依據。其餘驗證用到的程式／設定也須確認 index 與工作樹一致；不能用工作樹結果證明不同的提交內容。之後若改文件內容或 stage 集合，必須重新驗證；缺工具明記不適用原因，不可引用 B4 的舊通過結果。服務程式、設定或驗證依據若在 B3 後改過，連 B3 也重跑；純粹填寫已取得的結果不必重新呼叫外部服務。2026-11-02／F11：先驗 B4 再寫 B6，舊結果不能證明最後那份快照合格。\n\n祕密掃描（有輸出就停下來逐條確認）：\n\n```bash\ngit diff --cached -U0 | grep -nEi "(api[_-]?key|secret|token|passwd|password|BEGIN [A-Z ]*PRIVATE KEY)" | head -20\n```\n\n確認沒有憑證、運行資料、備份、實際業務資料後才 commit。\n\n### B8 發布\n\n推送會釋回標記前，fetch 後比對 B1 的占用分支 SHA 與完整標記。若本 session 在流程中已推送該分支，SHA 以自己推送且已從遠端確認標記仍相同的 commit 為準。兩者任一對不上就停下，不推送。\n\n```bash\ngit fetch origin && git status -sb\n```\n\nfetch 失敗 → **停下**，遠端新鮮度未知。遠端意外前進 → **停下**，禁止 force push，回報並等待使用者指示。正常才 push；push 後 `git status -sb` 必須 clean 且與 upstream 對齊。\n**push 失敗就不是完成交棒**，不要在回覆裡寫「已交棒」。\n\n### B9 收尾與回報（≤5 行）\n\n三件事，**依序做，回報是最後一件**。這一輪 B1–B8 全做對、卻漏掉改名的 session（2026-11-01 量到兩個）漏掉的正是唯一沒有編號的那一步，所以它現在有編號了。\n\n1. **push 成功之後**依「同一 session 的交棒計數」將 N 加 1，把 session 名稱的符號與狀態換成 `↗` 與 `已交棒`，尾端寫 `｜交棒<N>次`，前面的 `MM.DD.HH｜<主題>` 原封不動（見「session 命名」）。push 失敗就不要改、不要加次數——那不算交棒。同一次成功交棒重試改名或重複回報，不再加一次。A5 漏了改名、現在才要補的話，前綴照「session 命名」那條去抄，**不要用現在的時間重算**。\n2. 確認推上去的那一份「工作中」真的已經清掉（本機改對了但沒推上去，下一棒看到的還是舊的）：\n\n   ```bash\n   git show "origin/$(git rev-parse --abbrev-ref HEAD):HANDOFF.md" | grep -F "**工作中**"\n   ```\n\n3. 回報，照這個模板：\n\n   ```text\n   結果：<做完什麼>\n   驗證：<B3／B4 的結果；跳過的項目寫原因>\n   分支／最終 commit：<branch> @ <hash>，已 push／未 push\n   session：↗\u3000<MM.DD.HH｜主題>｜已交棒｜交棒<N>次（已改）／不適用：<本工具不能改名>；交棒<N>次\n   接手最容易搞砸：<一件事>\n   ```\n\n   **`session：` 那一行不能省**——它是改名這條規則唯一的守門人（理由見「session 命名」）。寫不出來就是沒做。\n\n---\n\n## C. 中途同步（還沒要交棒）\n\n- 拉最新：照 A1 判讀表走，異常一樣停。\n- 推安全點：這是中途 push 例外，**時機由 agent 自行判斷**，走 B7 → B8；保留本 session 的「工作中」標記，不走 B6 的釋出標記與 B9 的交棒計數。origin 的「工作中」仍是本 session 時，**不必為這次 push 更新 HANDOFF**；只有做了破壞性或高風險的改動、中途斷線會讓下一棒誤判時，才補一行風險，並照 B7 驗最終文件。成功後重讀 origin 標記仍是本 session。不得把中途同步說成已交棒。\n- **建議交棒（只建議，不動手）**：一段工作做完、回報之前，工具讀得到上下文用量（例如 Claude Code 桌面 App 的 `get_usage`）就讀一次，照實寫出數字；達 70% 在回覆加一行「上下文 <N>%，建議交棒；要交棒請說『交棒』」，然後照常續作或等指示，不自行走 B。同一門檻只提一次，使用者沒要交棒，到 85% 再提一次。讀不到用量就不拿用量當理由，**不要估算**。\n- **換機器前一定要 push，下一台機器一定要先 fetch。**\n- **single writer**：同一時間只有一個 agent／一台機器可以改 `main` 與 `HANDOFF.md`。要換手就先交棒。\n'
TEMPLATES['.claude/skills/handoff/reasons.md'] = '<!-- source: PROJECT-BOOTSTRAP.md v2026-11-20.2 — 權威版在部署包，改這裡之前先改部署包再同步各專案與全域副本 -->\n\n# 理由、事故與細則原文\n\n> 2026-11-10 拆分 handoff skill 時逐字搬自單檔 `SKILL.md`：每條規則的理由、日期與事故，加上 session 命名的完整細則。**不是每輪必讀；要改、質疑或想繞過某條規則之前先讀。** 文內的「本檔」指整個 handoff skill 目錄；A／B／C／0 各步驟分別在 `mode-a-stop.md`、`mode-b.md`、`mode-0.md`。\n>\n> 2026-11-13（需求決策書 v3）：本目錄降為碰到才讀的參考；必守的條件在 `AGENTS.md` 的共用制度一節，衝突時以它為準。文內提到的 `[git-check]` 判讀行、「全綠」行已由只報事實的 `[facts]` 取代。\n\n## 前言原文\n\n> **本檔＝程序**：做什麼、下哪些指令、什麼時候必須停下來問人。\n> override 只可加嚴或填補核心留給專案的設定，不能默默放寬同步、占用、驗證與發布門檻；使用者明確指示仍優先。不得在單一專案就地修改共用 skill，應回部署包修正再同步（2026-11-02／F10：避免舊協定推翻新程序）。\n> **例外是模式 0（建制）**：那一段的權威是 project-bootstrap repo（2026-11-18 起由它的 `bootstrap.py` 寫檔，需求決策書 v3 Q49；之前是 `PROJECT-BOOTSTRAP.md` 部署包，協定檔本身也是它生出來的），衝突時以 project-bootstrap 為準。\n> 純 Markdown，任何模型（Claude／Codex）都應直接讀取，不限某一家工具。\n\n## 適用判斷：為什麼沒人提就不建\n\n最後一列是硬規定：這支 skill 會在使用者只是想改一行程式時被載入，未經同意就在別人的 repo 裡長出十幾個檔案是災難，而且他多半不會逐一刪乾淨——會留下半套制度，比沒有更糟。\n\n## 模式 0 為什麼留在每一份副本裡\n\n> 模式 0 在**已經部署好的專案裡永遠用不到**——這裡有雞生蛋問題：skill 是部署之後才存在於專案的。\n> 它真正會被載入的地方是**全域副本**（`~/.claude/skills/handoff/`、`~/.codex/skills/handoff/`）。\n> 專案內這份仍保留模式 0，是為了讓副本可以整份無腦覆蓋，不必維護兩種版本——分版本就是下一個「同一個事實有多個家」。\n\n---\n\n## session 命名（每輪必做；工具做不到就在回報裡寫「不適用」）\n\n側欄上十幾個 session 全叫「接棒」，要一個個點進去才知道哪個是哪個。**所以每換一次狀態就改一次 session 名稱**——有這個能力才做（例如 Claude Code 桌面版的 `set_session_title`），**沒有就跳過，不要為此停下來問使用者**：Codex CLI 目前沒有對應能力，為一個做不到的步驟回報失敗只是噪音。\n\n🔴 **但「跳過」要說出來，不能安靜跳過**（2026-11-01 加硬）。**A5 與 B9 的回報模板各有一行 `session：`，必填**：改了就寫改成什麼，工具沒有這個能力就寫 `不適用：<原因>`。那一行是這條規則唯一能有的守門人——改名發生在 session 的外殼上，repo 裡不留任何痕跡，`check_docs.py`、`git-freshness.sh`、pre-push 防呆**三層全都看不到它**，所以漏掉是完全無聲的，而無聲的漏跟「沒有這條規則」在畫面上一模一樣。2026-11-01 量到：六個收尾 session（全 Sonnet）裡**只有四個**改了名，六個的 git 結果全部正確——漏的只有命名。**為什麼漏沒有量過**，所以這次不針對某個原因下藥，改的是「有沒有做」看不看得出來。\n\n```text\n<符號>\u3000MM.DD.HH｜<主題>｜<狀態>｜交棒<N>次\n```\n\n| 符號 | 狀態 | 什麼時候改 |\n|---|---|---|\n| `㊣` | 工作中 | 首次接棒在 **A5** 回報完之後；已交棒後續聊在**收到新訊息時先改**，**不等開工標記**——只讀、只掃，或專案根本沒有 `HANDOFF.md` 的時候都寫不了標記，改名照樣要做 |\n| `↗` | 已交棒 | **B9**，而且是 **push 成功之後**（push 失敗不改、不加次數，照 B8 那不算交棒）；**B9 的回報要寫出改成什麼與累計次數** |\n\n範例（同一個 session 兩次交棒，中間收到一則新訊息）：\n\n```text\n㊣\u300011.02.09｜修續聊狀態｜工作中｜交棒0次\n↗\u300011.02.09｜修續聊狀態｜已交棒｜交棒1次\n㊣\u300011.02.09｜修續聊狀態｜工作中｜交棒1次\n↗\u300011.02.09｜修續聊狀態｜已交棒｜交棒2次\n```\n\n### 已交棒後續聊（每則新訊息的入口）\n\n**每則使用者新訊息都先檢查 session 狀態，包含只問問題、補充、更正與致謝，不必等使用者再說「接棒」。** 上次是 `↗ 已交棒`時，先用改名工具恢復 `㊣ 工作中`，再回答或執行任務；必要的標題讀取可先做。**保留原本的 `MM.DD.HH`、主題與交棒次數，不重算時間、不歸零、不另建 session。**\n\n- **只讀續聊不改 HANDOFF、不 commit、不 push，也不為了結束回答再交棒。** 改名已足以表達 session 正在活動，不能為了一句問答新增空的開工／交棒紀錄。\n- **續聊要改檔前重新走 A1–A5，重查 origin 的工作中標記。** 前次交棒已釋出分支，另一個 session 可能已接手；恢復側欄狀態不代表重新取得寫入權。通過 A1–A4 並完成 A5 回報後才寫開工標記，push 失敗照 A5 停下。\n- **續聊回覆必須有 `session：` 一行，列出實際標題與交棒次數。** 沒有改名能力就寫 `不適用：<原因>；交棒<N>次`；有工具但呼叫失敗要如實寫失敗，不能宣稱已改。這是逐訊息的程序義務，SessionStart hook 不會因為同一 session 多一則訊息再跑一次，也不能宣稱只同步 skill 就讓所有舊 session 自動生效。\n\n### 其他命名規則\n\n- **`MM.DD.HH` 取接棒當下的時間，之後永遠不更新。** 交棒時一起改掉的話，同一個 session 在側欄的名字會跳掉，使用者記得的時間點就對不上了。\n- **交棒才要補名字的時候，前綴去抄、不要用現在的時間重算。** A5 那一步漏掉的話，`MM.DD.HH` 從 `HANDOFF.md`「工作中」欄位抄（它記的就是開工時間，新格式連當時的 session 名都在裡面；B6 把它改回「無（已交棒）」之前先讀，已經改掉就 `git show <開工那個 commit>:HANDOFF.md`）。重算會寫出**交棒**的小時，而這個時間戳唯一的用途是讓人在側欄找回開工那一刻——錯了沒有任何徵兆。舊版 B9 只寫「前面的 `MM.DD.HH｜<主題>` 原封不動」，那句話**預設 A5 已經改過名**；沒改過的時候它無從執行，而唯一拿得到的時間正好是錯的那個。\n- **主題 ≤10 字，取自 `HANDOFF.md` 的任務目標，壓成動詞＋受詞。** 不要寫「更新文件」「修 bug」這種放哪個 session 都成立的詞——那會退化回「全部長一樣」，等於沒改。還不知道要做什麼就先寫 `待指派`，第一件事確定後就地改一次。\n- **符號後面接一個全形空格（U+3000）再開始日期。** 半形空格撐不開，`↗` 這種細筆畫的符號會黏在數字上。\n- **符號放最前面**，是因為側欄窄的時候是從尾巴開始截字；狀態是最該被看見的東西，不能放在第一個被截掉的位置。尾綴那幾個字是版面夠寬時的補充，截掉不損失資訊。\n- 同一天同一個主題開第二個 session 才在主題後面加數字（`匯入格式2`），不是每個都編號。\n- **改名的依據是 session 的狀態，不是 git 的結果。** 側欄要回答的是「這個 session 現在在幹嘛」，`HANDOFF.md` 的「工作中」欄位要回答的是「哪台機器握著這條分支」——兩件事、兩個讀者，不要綁在一起。綁住的代價 2026-10-30 在骨架自己的 repo 上現形：舊版 A5 寫「push 成功才改名」，而 project-bootstrap 刻意沒有 `HANDOFF.md`、寫不了開工標記，於是改名那一步永遠到不了，這個 repo 的 session 全部停在「接棒」兩個字，直到交棒才一次拿到名字——那時候它已經不需要被認出來了。唯一的例外是 `↗ 已交棒`：它本身就在宣稱一件 git 的事，所以只有它要等 push。\n- **側欄的 `㊣` 不證明 origin 上有開工標記。** 跨機器防呆看的是 `HANDOFF.md` 的欄位（A2.5），側欄只是給人看的；別拿它當防呆的證據。\n- **模式 C 中途同步不改名**——狀態沒變。\n- 模式 0 建制照 B9 收尾，主題寫 `骨架建制`。\n- **改完這份規則、同步完副本之後，當下開著的 session 不保證自動採用新版。** `SKILL.md` 是 session 載入它的那一刻讀進 context 的快照，之後改磁碟上的檔案不會回溯生效——舊 session 要明確重新讀取新版 skill，或重開 session 才會拿到新版；重新讀取時仍保留原 session 時間與次數。已經寫下的 session 名稱也不會自己更新，要補只能呼叫改名工具。2026-10-24 加上全形空格那條時就是這樣：副本 15:20 全部同步完，一個 15:29 才交棒的 session 名字裡照樣沒有空格——那不是漏同步，查錯方向會白花一輪。\n\n---\n\n## 交棒由使用者決定（2026-11-12／Q31）\n\n- **起因**：舊入口把「工作告一段落」與「準備 `git push`」都導向 B，push 提醒 hook 又在 `main` 沒更新 HANDOFF 時擋下並叫 agent 走 B。結果 agent 每做完一段就跑 B1–B9、覆寫整份 HANDOFF 並改成 `↗`；使用者還在同一個 session 對話，token 卻花在重複的收尾上。2026-11-12 使用者指示：commit／push 時機由 agent 自行判斷，可以主動看上下文用量建議交棒，但沒要求就不能交棒。\n- **中途 push 為什麼可以不更新 HANDOFF**：origin 上的「工作中」仍是本 session，下一棒會在 A2.5 被這個標記擋下，不會拿暫時過期的快照當現況；session 中斷沒交棒時，A2.5／A6 的漏交棒補救本來就以 Git 實況為準。破壞性或高風險改動仍要補一行風險，因為那正是斷線後下一棒最容易誤判的地方。\n- **為什麼門檻是 70%／85%、而且一定要讀數字**：Claude Code 桌面 App 的上下文視窗是 1M tokens，97% 才自動壓縮；70% 留得下一次完整的 B。2026-11-10 有 session 憑感覺說「接近 70%」就收工，實際只有 38%。讀不到就不拿用量當理由；同一門檻只提一次，避免提醒本身又變成消耗。\n- **只建議不動手**：交棒會釋出分支、改 session 狀態，是使用者對「這段工作結束了」的判斷，agent 不代為決定。\n\n## 跑得久的指令為什麼一次等完（2026-11-14）\n\n- **起因**：2026-11-14 一次 Codex 桌面 App 接棒，從開始到推完開工標記約 2 分 40 秒、28 次模型呼叫，累計輸入約 112 萬 tokens。其中驗證腳本跑了兩次，每次約 54 秒；Codex 的指令工具約 1 秒就先交回，模型再每隔約 5 秒呼叫一次去讀輸出，兩次驗證共空等了 15 次呼叫，超過一半。每次呼叫都把整段上下文（當時約 35k–45k tokens）再送一次，累計輸入約有一半來自這些空等。同一份程序在 Claude Code 跑，殼層工具會等到指令結束，沒有這種呼叫。\n- **為什麼寫成「一次等夠久」而不是「別跑驗證」**：驗證的輸出本身仍然要看，省的是等待時重複送出的上下文，不是驗證。等太久的代價只是那一次呼叫晚一點回來；問太勤的代價是每次都重送整段上下文。\n- **沒有量過的部分**：改寫後 Codex 是否真的照做、呼叫次數降到多少，要在 Codex 實際接棒一次才知道；這段寫下時尚未驗收。\n\n2026-11-14 後續實測：v2026-11-14.3 的 Codex 桌面 App 接棒用了 11 次模型呼叫、349,246 input tokens（其中 304,000 cached）、約 147 秒。已比前次少，但仍有兩次外層 `functions.exec` 在 30 秒返回，內層 `write_stdin` 的 60000 ms 並沒有控制外層；驗證完整成功輸出與已注入的 AGENTS 重讀又增加上下文。故改為外層與內層一起設定，單批等待最多一分鐘再回報進度，成功只回摘要，既有規則不重讀。這是同一工具的兩次觀測，非控制變因的模型 A/B；新版是否進一步省模型用量須另次實際交接驗收，不為量測自動呼叫模型。v3 共用入口不增加規則，正常驗證與 B7 staged 檢查保留。\n\n## 反例（真的發生過，別重演）\n\n- ❌ 開工沒 fetch，對著落後數十個 commit 的本機 HANDOFF 工作數小時 → 分岔，收拾一整天。\n- ❌ 連線失敗直接寫「本機未配置」→ 其實只是金鑰環境變數沒設，結論全錯。\n- ❌ 純文件修正卡在功能分支等驗收 → 接手者同步 `main` 拿到過期文檔集。\n- ❌ 知識寫在對話裡或私有記憶 → 換模型、換機器後全部消失。\n- ❌ HANDOFF 愈疊愈長變成日誌 → 接手者要讀 20 分鐘才知道現在做到哪。\n- ❌ push 完才想起沒更新 HANDOFF → 下一棒拿到過期狀態（AI push 提醒只有有限覆蓋，可能漏判；不能當發布保證）。\n- ❌ A 機器沒交棒就關掉，B 機器開 session 看到 `✅ 與 origin 同步` 就接棒 → 那個綠勾只證明「B 沒落後」，**不證明「沒有別台在做」**；A 的未提交變更整批被繞過。這就是「工作中」標記要擋的那件事。\n- ❌ 會花錢的那一輪跑完直接關掉視窗 → 數字還在磁碟上，**當時的判斷與取捨永久消失**；三層防呆全都掛在「下一個動作」上，擋不住這件事（Claude Code 與 Codex 的 `SessionEnd` 也擋不住：它不能阻止結束，也來不及 push）。\n- ❌ 建制時沒拿到部署包，憑印象生一套「差不多的」骨架 → 規則沒了理由、hook 沒了邊界條件，看起來有制度、實際擋不住任何事。\n  2026-11-18 起（Q49）同一個教訓套在安裝程式上：沒有 `bootstrap.py` 就停，不重刻。\n- ❌ 使用者只說「幫我看一下這個 repo」，agent 自作主張把整套骨架灑進去 → 別人的 repo 多出十幾個沒人要的檔案，而且不會被逐一刪乾淨。\n- ❌ 建完沒刪部署包 → 第二份會腐化的副本，下一棒還會以為部署沒做完而重跑一次訪談。\n  2026-11-18 起（Q49）安裝程式不把部署包放進專案，這一條改成：`*.bootstrap-new` 合併完沒刪，下一棒分不出哪一份才是現行的。\n- ❌ session 名稱全部一樣 → 側欄認不出哪個是哪個；主題寫成「更新文件」也一樣，改了名還是分不出來。\n- ❌ 停下來問使用者卻沒改名 → 側欄顯示「工作中」，使用者以為它還在跑，實際上在等他。只把「必須停下來問使用者」那張表當成改名時機也一樣——普通的「要選哪個」同樣是在等人。\n- ❌ 同一台機器上從一個工具換到另一個工具接棒，而標記只寫了機器名 → hook 印 🟡「大概是你自己另一個視窗」，兩個 agent 對著同一個工作樹即時互相覆寫。工具欄就是為這件事加的（2026-10-31）。\n- ❌ 拿環境變數當工具身分的權威 → 在別的工具殼層裡啟動時變數被繼承，Codex 的 session 自稱 Claude Code，於是「同工具」成立、直接放行。變數只能加嚴。\n- ❌ 把改名綁在「開工標記 push 成功」之後 → 這輪只讀、或專案刻意沒有 `HANDOFF.md`，標記寫不了，側欄就永遠停在「接棒」。2026-10-30 在骨架自己的 repo 上發現：三個 session 全是 `↗ 已交棒`，一個 `㊣ 工作中` 都沒有過。\n- ❌ git 全做對、就是沒改 session 名稱 → 2026-11-01 量到六個收尾 session 裡有兩個這樣（全 Sonnet，git 結果全部正確，用的還是派工時給的標題）。**原因沒有量過**，所以別替它補一個；要知道的是**沒有任何檢查看得到這件事**（改名在 repo 外面），所以它只能靠 A5／B9 回報那一行 `session：` 露出來。\n- ❌ 已交棒後收到新訊息，因為使用者沒再說「接棒」就保留 `↗` → 使用者仍在續聊，側欄卻表示已結束；收到訊息就恢復 `㊣`、保留交棒次數，改檔前再跑 A 模式。單純答問不新增一次交棒（2026-11-02）。\n\n## 漏交棒的補救（2026-11-17 從專案的交接協定搬來，v3 Q41）\n\n一輪工作做完就關掉、沒走交棒：工作樹留著未提交變更與整個結果目錄，`HANDOFF.md` 還停在前一輪，寫著與實況矛盾的話（典型的是費用欄寫「本輪未產生費用」）。這件事真的會發生，而且往往隔了好幾週、換了機器或模型才被下一棒發現。\n\n- **代價不是那個沒有的 commit，是知識。** 產物還在磁碟上，數字都查得回來；當時的判斷與取捨永久消失：為什麼選這組參數、哪條路試過但放棄、哪些結果是在非基準組態下取得的。\n- **hook 一個都擋不住**：它們都掛在「下一個動作」上，而直接關掉視窗沒有下一個動作。2026-10-30 重查：Claude Code 與 Codex 有 `SessionEnd`，但它不能擋下結束、預設只有 1.5 秒，做不完一次 `git push`，最多提醒離場的人，救不了下一棒。所以這是程序責任。\n- **開工標記只縮小了洞**（2026-10-30 加）：寫在開工而不是收工，所以「直接關掉視窗」繞不過它。但它救不回 A 機器的未提交變更；A 在開工標記推上去之前就關掉時，origin 上什麼都沒有；A 那一端的 hook 沒真的生效時，只剩程序擔保。\n- **回推寫的是數字，不是理由**：推測一旦寫成當時的理由，就會變成下一棒眼中的既成事實，所以回推的段落一定要標明「事後回推、當時無記錄」。\n- 給交棒者的一句話：會花錢、或會產生無法重現之產物的那一輪，不交棒就等於沒做。補救成本遠高於當場寫 10 行 HANDOFF。\n\n## 規則 → 理由在哪（對照表）\n\n> 2026-11-10（決策書 Q17 (b)）：入口與 `mode-a.md` 不逐條加理由連結，免得吃掉常態必讀的額度；改在這裡列出每個段落的理由在哪。「本段內文」＝理由就寫在那一段裡；「沒有寫下理由」＝拆分前的單檔就沒寫，照實標出來，不補編；「分節標題」＝規則在它底下各步驟。`verify_bootstrap.py` 守：入口與四個模式檔的每個段落標題都列在左欄，右欄指到的段落真的存在。**它不判斷理由寫得對不對。**\n\n| 規則（檔案 § 段落） | 理由在哪 |\n|---|---|\n| SKILL.md § 適用判斷（先做這一步） | reasons.md § 適用判斷：為什麼沒人提就不建<br>reasons.md § 反例（真的發生過，別重演） |\n| SKILL.md § 需要細節時讀哪個檔 | reasons.md § 前言原文<br>reasons.md § 交棒由使用者決定（2026-11-12／Q31）<br>reasons.md § 模式 0 為什麼留在每一份副本裡<br>mode-a-stop.md § A／B／C 狀態轉移（2026-11-02／F11） |\n| SKILL.md § 全程禁令 | 沒有寫下理由 |\n| env.md § 開場沒有 [facts] 時依序查 | 本段內文 |\n| env.md § Codex | 分節標題 |\n| env.md § 跑得久的指令 | reasons.md § 跑得久的指令為什麼一次等完（2026-11-14） |\n| env.md § hook 接線有改或同步過 | 本段內文 |\n| env.md § 全域 skill 位置 | 沒有寫下理由 |\n| env.md § Claude Code | 本段內文 |\n| env.md § Windows | 本段內文 |\n| env.md § macOS | 分節標題 |\n| SKILL.md § 必須停下來問使用者（不得自行決定） | mode-a-stop.md § A1 先同步 Git（未同步前不要相信本機任何文件，包括 HANDOFF）<br>mode-a-stop.md § A2.5 檢查這條分支有沒有人正在工作（跨機器誤接棒防呆）<br>mode-0.md § 0-1 先確認你在對的資料夾、對的情境 |\n| SKILL.md § session 命名（每則訊息都適用） | reasons.md § session 命名（每輪必做；工具做不到就在回報裡寫「不適用」）<br>reasons.md § 已交棒後續聊（每則新訊息的入口）<br>reasons.md § 其他命名規則<br>reasons.md § 反例（真的發生過，別重演） |\n| mode-a.md § A1＋A2.5 同步與占用：讀開場的 [facts] | mode-a-stop.md § A1 先同步 Git（未同步前不要相信本機任何文件，包括 HANDOFF）<br>mode-a-stop.md § A2.5 檢查這條分支有沒有人正在工作（跨機器誤接棒防呆）<br>reasons.md § 反例（真的發生過，別重演） |\n| mode-a.md § A2 站對分支 | mode-a-stop.md § A2 站對分支 |\n| mode-a.md § A3 最小讀取 | mode-a-stop.md § A3 最小讀取 |\n| mode-a.md § A4 驗證（只記錄，不修） | mode-a-stop.md § A4 一鍵驗證<br>reasons.md § 反例（真的發生過，別重演） |\n| mode-a.md § A5 回報後才動手 | mode-a-stop.md § A5 回報後才動手（3–5 行）<br>reasons.md § 反例（真的發生過，別重演） |\n| mode-a-stop.md § A／B／C 狀態轉移（2026-11-02／F11） | 本段內文 |\n| mode-a-stop.md § A. 接棒 | 分節標題 |\n| mode-a-stop.md § A1 先同步 Git（未同步前不要相信本機任何文件，包括 HANDOFF） | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |\n| mode-a-stop.md § A2 站對分支 | 本段內文 |\n| mode-a-stop.md § A2.5 檢查這條分支有沒有人正在工作（跨機器誤接棒防呆） | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |\n| mode-a-stop.md § A3 最小讀取 | 本段內文 |\n| mode-a-stop.md § A4 一鍵驗證 | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |\n| mode-a-stop.md § A5 回報後才動手（3–5 行） | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |\n| mode-a-stop.md § A6 回推補交接（只有在 A1 判定「前一輪漏交棒」時才走） | 本段內文<br>reasons.md § 漏交棒的補救（2026-11-17 從專案的交接協定搬來，v3 Q41） |\n| mode-b.md § 同一 session 的交棒計數 | 本段內文 |\n| mode-b.md § B. 交棒 | reasons.md § 交棒由使用者決定（2026-11-12／Q31） |\n| mode-b.md § B1 收斂到安全點 | 本段內文 |\n| mode-b.md § B2 持久知識落地（今天學到的寫進 repo，不要留在對話裡） | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |\n| mode-b.md § B3 服務驗證 | reasons.md § 反例（真的發生過，別重演） |\n| mode-b.md § B4 文檔驗證（動過任何 `.md` 就必跑） | 本段內文 |\n| mode-b.md § B5 條件式例行檢查 | 本段內文 |\n| mode-b.md § B6 更新 `HANDOFF.md`（覆寫，≤80 行，不累積歷史） | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |\n| mode-b.md § B7 安全提交 | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |\n| mode-b.md § B8 發布 | 本段內文 |\n| mode-b.md § B9 收尾與回報（≤5 行） | 本段內文<br>reasons.md § session 命名（每輪必做；工具做不到就在回報裡寫「不適用」） |\n| mode-b.md § C. 中途同步（還沒要交棒） | reasons.md § 交棒由使用者決定（2026-11-12／Q31）<br>reasons.md § 反例（真的發生過，別重演） |\n| mode-0.md § 0. 建制（這個資料夾還沒有這套制度） | reasons.md § 模式 0 為什麼留在每一份副本裡 |\n| mode-0.md § 0-1 先確認你在對的資料夾、對的情境 | 本段內文<br>reasons.md § 適用判斷：為什麼沒人提就不建<br>reasons.md § 反例（真的發生過，別重演） |\n| mode-0.md § 0-2 取得安裝程式（沒有它就停） | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |\n| mode-0.md § 0-3 跑安裝程式（訪談由程式問） | 本段內文 |\n| mode-0.md § 0-4 第一批工作（寫在 `HANDOFF.md` 的「未完成／下一步」） | 本段內文<br>reasons.md § 反例（真的發生過，別重演） |\n| mode-0.md § 0-5 本機驗收後才首次發布 | 本段內文 |\n| mode-0.md § 0-6 遠端與工具驗收 | 本段內文 |\n| mode-0.md § 0-7 回報 | 本段內文 |\n'
TEMPLATES['.codex/hooks.json'] = '{\n  "hooks": {\n    "SessionStart": [\n      {\n        "hooks": [\n          {\n            "type": "command",\n            "command": "bash \\"$(git rev-parse --show-cdup).claude/hooks/git-freshness.sh\\"",\n            "commandWindows": "cmd /d /c \\"$((git rev-parse --show-cdup) -replace \'/\',\'\\\\\').claude\\\\hooks\\\\codex-hook.cmd\\" git-freshness.sh",\n            "timeout": 30,\n            "statusMessage": "檢查 git 是否與 origin 同步…"\n          }\n        ]\n      }\n    ],\n    "PreToolUse": [\n      {\n        "hooks": [\n          {\n            "type": "command",\n            "command": "bash \\"$(git rev-parse --show-cdup).claude/hooks/pre-push-handoff.sh\\"",\n            "commandWindows": "cmd /d /c \\"$((git rev-parse --show-cdup) -replace \'/\',\'\\\\\').claude\\\\hooks\\\\codex-hook.cmd\\" pre-push-handoff.sh; exit $LASTEXITCODE",\n            "timeout": 15\n          }\n        ]\n      }\n    ]\n  }\n}\n'
TEMPLATES['.gitattributes'] = '# Keep source and documentation consistent across Windows and macOS.\n* text=auto eol=lf\n*.bat text eol=crlf\n'
TEMPLATES['.gitignore'] = '# Credentials (each machine keeps its own local copy)\n.env\n.env.*\n!.env.example\n\n# Runtime state, downloaded backups, and operational data\ndata/\nbackups/\npersist/\narchive/\n\n# Local scratch artefacts\ntmp/\nscratch/\n.claude/settings.local.json\n.claude/.bootstrap-version\n__pycache__/\n*.py[cod]\n*.log\n\n# Editor and operating-system metadata\n.DS_Store\nThumbs.db\n.obsidian/\n\n# Interview-specific rules: one Git ignore pattern per line, no Markdown backticks\n{{SECRETS}}\n{{RUNTIME_DIRS}}\n'
TEMPLATES['AGENTS.md'] = '# AGENTS.md — 這個專案怎麼接續\n\n現在做到哪、下一步是什麼，在 [HANDOFF.md](HANDOFF.md)。使用者用 **{{LANG}}** 溝通。\n> 最後更新：{{TODAY}}（建立）\n\n<!-- 共用制度開始 source: PROJECT-BOOTSTRAP.md v2026-11-20.2 — 到下方的結束標記為止由部署包管理；專案只能加嚴或填空，要改回部署包改再同步 -->\n## 目標\n\n這個專案由不同的 session、模型、機器輪流做。你要讓下一棒不必問任何人，就能從 origin 拿到最新成果、知道現況，而且不會跟別人互相覆寫。怎麼做到由你判斷。\n\n## 你不會自己知道的事\n\n- 本機的檔案可能是舊的。別台機器可能已經推了新東西到 origin，包含更新過的 `HANDOFF.md`。\n- 主幹不一定是 `main`：`HANDOFF.md` 的「待續分支」寫了分支名，就在那條分支上做。\n- 可能有另一個 session 正在同一條分支上工作。唯一的訊號是 origin 上 `HANDOFF.md` 的「工作中」那一行：`無（已交棒）` 表示沒人在做，其他值表示有人。\n- session 開始時會自動 fetch 一次，印出 `[facts]` 開頭的幾行。那是當下的快照，之後會過期。\n- 逐步程序、異常判讀與規則的理由在 [`.claude/skills/handoff/`](.claude/skills/handoff/SKILL.md)，是碰到才讀的參考。\n\n## 不可違反的條件\n\n1. 改任何檔案之前，本機要跟 origin 一致，而且 origin 上的「工作中」要先推成你自己（`機器 ／ 工具 ／ session 名`，加開工時間）。推不上去就不算。只讀、只回答問題的 session 不寫。\n2. origin 上的「工作中」是別人時，不改檔、不推送，停下來告訴使用者。\n3. 使用者要求交棒時才交棒。交棒前先 fetch，確認 origin 上的「工作中」標記確由本 session 推上。無法確認就停下回報，不改檔、不推送。交棒完成的定義：所有成果都在 origin 上；`HANDOFF.md` 整份覆寫成當下狀態（欄位照現有格式，80 行以內，不累積歷史）；「工作中」改回 `無（已交棒）`；本機沒有留下沒推的東西。使用者沒要求就保留你的「工作中」。\n4. `main` 上的測試要一直是過的。沒做完的工作放分支推上去，在 `HANDOFF.md` 的「待續分支」寫明分支名。\n5. 沒驗證過的事不寫成已驗證。\n6. 不提交祕密或金鑰樣式的內容。提交前看 staged 清單，逐檔加入，不用 `git add -A` 或 `git add .`。\n7. 不做這些事：`reset --hard`、force push、改寫已推送的歷史、刪分支、自行 stash、刪除不是你建立的檔案、提交 `.gitignore` 排除的東西。\n8. 遇到本檔沒講、而且做錯無法復原的狀況（歷史分岔、fetch 失敗、來源不明的未提交變更），停下來告訴使用者。\n\n## session 名稱（工具能改名才做）\n\n格式 `<符號>\u3000MM.DD.HH｜<主題>｜<狀態>｜交棒<N>次`，符號後接一個全形空格。兩種狀態：`㊣` 工作中、`↗` 已交棒。\n\n- `MM.DD.HH` 用開場 `[facts]` 印的值，之後不改；主題 ≤10 字，還不知道寫 `待指派`；新 session 的 N 從 0 起算。\n- 開始工作改 `㊣`；交棒的 push 成功後才改 `↗`，N 加 1。是 `↗` 時收到任何新訊息，先改回 `㊣`，時間戳、主題與 N 不變。\n- 接棒與交棒的回覆各寫一行 `session：<實際標題>`；工具不能改名就寫 `session：不適用：<原因>；交棒<N>次`。\n<!-- 共用制度結束 -->\n\n## 專案是什麼\n\n{{ONELINER}}。repo 是 {{GH_VISIBILITY}} GitHub `{{GH_OWNER}}/{{GH_REPO}}`；連線方式與怎麼跑在 [README.md](README.md)，結構與每份檔案的權威在 [ARCHITECTURE.md](ARCHITECTURE.md)，持久待辦在 [docs/ai-notes/roadmap.md](docs/ai-notes/roadmap.md)，碰到才讀。\n\n## 鐵律（違反會造成實際損害）\n\n1. **不提交祕密或運行資料**：{{SECRETS}}、API／SSH private key、{{RUNTIME_DIRS}} 都不可 commit 或 push；{{GH_VISIBILITY}} repository 也不例外。Git 存的是 source 與文件，**不是資料備份**。\n2. **破壞性操作前先備份**：改 schema、批次改資料、刪檔、覆寫設定之前，先產出可還原的副本並說明放在哪。\n3. **憑證原則**：憑證由使用者提供並存於 {{SECRETS}}，直接讀取即可；不從系統檔、其他主機、Git history 自行挖取或搬運憑證。文件裡只寫「key 在 {{SECRETS}} 的哪一項」，不寫值。\n<!-- 4. 專案專屬鐵律寫在這裡：每一條附「為什麼」與發生日期，否則下一棒會繞過它。 -->\n'
TEMPLATES['ARCHITECTURE.md'] = '# ARCHITECTURE — 專案結構\n\n> **本檔＝結構的唯一權威**：這個專案由什麼組成、每樣東西的家在哪、哪一份是權威版。\n> 最後更新：{{TODAY}}（建立）\n>\n> **什麼時候改**：只有**結構**變動才改——新增／刪除／搬移長期存在的目錄或檔案、換掉一個元件、改變資料流向、改變「哪一份是權威版」。\n> 改功能、修 bug、更新進度**都不要動這一份**。它刻意比 [HANDOFF.md](HANDOFF.md) 慢：HANDOFF 每次交棒覆寫，本檔可能好幾個月不動。\n\n## 這一份與其他檔案的分工（同一件事不要有兩個家）\n\n| 你想知道 | 讀哪一份 |\n|---|---|\n| 專案由什麼組成、東西放在哪、誰是權威版 | **本檔** |\n| 開工必守的條件與鐵律 | [AGENTS.md](AGENTS.md) |\n| 這是什麼系統、為什麼做、怎麼連、怎麼跑起來 | [README.md](README.md) |\n| 現在做到哪、下一步 | [HANDOFF.md](HANDOFF.md) |\n| 還有哪些事沒做、什麼被否決 | [docs/ai-notes/roadmap.md](docs/ai-notes/roadmap.md) |\n| 交接怎麼做與為什麼（指令、判讀表、模板、理由） | [.claude/skills/handoff/SKILL.md](.claude/skills/handoff/SKILL.md) |\n\nREADME 不另列檔案結構，只連到本檔；結構的細節與理由只寫在這裡。\n\n## 全貌\n\n```text\n{{GH_REPO}}/\n├─ 管理骨架     跨專案共通，部署時生成（見下表）\n├─ 專案本體     {{STACK_DIRS}}（見下方「專案本體」）\n└─ 不進 Git     {{SECRETS}}、{{RUNTIME_DIRS}}\n```\n\n## 管理骨架（部署時生成，跨專案共通）\n\n| 檔案 | 是什麼 | 權威版在哪 | 什麼時候動 |\n|---|---|---|---|\n| [README.md](README.md) | 專案介紹：是什麼、為什麼做、怎麼連、怎麼跑 | 本專案 | 目的、連線或執行方式改變 |\n| [AGENTS.md](AGENTS.md) | AI 開工時自動讀的條件：共用制度與專案鐵律 | 本專案（共用制度一節由部署包管理） | 多一條鐵律 |\n| [CLAUDE.md](CLAUDE.md) | Claude Code 用 `@AGENTS.md` import | 指向 AGENTS.md | 幾乎不動 |\n| [HANDOFF.md](HANDOFF.md) | 當下狀態（≤80 行、覆寫不累積） | 本專案 | **每次交棒** |\n| 本檔 | 結構 | 本專案 | 只有結構變動 |\n| [docs/ai-notes/roadmap.md](docs/ai-notes/roadmap.md) | 持久待辦與決策記錄 | 本專案 | 有新待辦或決策 |\n| [.claude/skills/handoff/SKILL.md](.claude/skills/handoff/SKILL.md)（入口）＋同目錄的 `mode-a.md`、`mode-a-stop.md`、`mode-b.md`、`mode-0.md`、`reasons.md`、`env.md` | 交接的可執行程序（0 建制／A 接棒／B 交棒／C 同步）；入口每次讀，其餘依模式才讀 | **部署包**（本專案這份是副本，檔頭 `source:` 標記可辨識落後） | 改制度先改部署包，再整份覆蓋下來 |\n| [.claude/hooks/git-freshness.sh](.claude/hooks/git-freshness.sh) | SessionStart：自動 fetch、報告落後／分岔 | 同上 | 同上 |\n| [.claude/hooks/pre-push-handoff.sh](.claude/hooks/pre-push-handoff.sh) | PreToolUse：AI push 提醒（有限覆蓋，見 3.11） | 同上 | 同上 |\n| [.claude/settings.json](.claude/settings.json) | 上面兩個 hook 的接線（進 Git） | 本專案 | 加減 hook |\n| `.claude/settings.local.json` | 各機器本地設定（**不進 Git**） | 各機器自己 | 換機器 |\n| [.codex/hooks.json](.codex/hooks.json) | Codex CLI 的 hook 接線——掛的是上面**同樣那兩個 `.sh`**，不另存一份腳本 | 本專案 | 加減 hook |\n| [.agents/skills/handoff/SKILL.md](.agents/skills/handoff/SKILL.md) | Codex 也讀 `.agents/skills/`：只放指向權威版的指標 | 指向 `.claude/` 那份 | 幾乎不動 |\n| [tools/check_docs.py](tools/check_docs.py) | 文件與交接快照的機械檢查：死連結／過期字串／缺日期標頭／硬編數量／殘留佔位符／交接快照結構 | 部署包（「專案設定」區塊除外，那塊本來就該依專案調） | 專案設定要調 |\n| [tools/verify_state.py](tools/verify_state.py) | 一鍵現況查證，輸出 key=value 事實快照 | 本專案（骨架來自部署包） | 服務或檢查項改變 |\n| [.gitignore](.gitignore)、[.gitattributes](.gitattributes) | 排除祕密與運行資料；行末強制 LF | 本專案 | 新增祕密檔或運行目錄 |\n\n**跨工具的可靠度不一樣**：`AGENTS.md` 與純 Markdown 的程序檔是**可攜層**（Claude Code／Codex 都原生讀得到）；hooks 已接 Claude Code、Codex CLI／桌面 App，而且**帶條件**——Codex 要專案被信任＋hook 經審核。正確性押在可攜層，不押在 hook 上：2026-10-30 在未信任的資料夾實測，`AGENTS.md` 照樣被讀進 prompt，`.codex/hooks.json` 整層被跳過而且沒有任何訊息。\n\n## 專案本體\n\n<還沒有程式碼就照實寫「尚未有程式碼」。**不要先畫一個想像中的架構**——想像的架構會被下一棒當成既成事實去對齊，然後花一整天把程式碼扭成文件的形狀。>\n\n| 目錄／元件 | 職責 | 進入點 | 相依 |\n|---|---|---|---|\n| <{{STACK_DIRS}} 之一> | <做什麼> | <哪個檔或指令> | <依賴誰> |\n\n## 資料流\n\n<一段話講清楚：資料從哪裡進來、經過什麼、存到哪裡、誰讀它。部署後填。>\n\n## 不在 Git 裡的東西\n\n{{SECRETS}}、{{RUNTIME_DIRS}}——各機器保有自己的本地副本。**Git 存的是 source 與文件，不是資料備份。**\n換機器時這些不會跟著過去，所以 `HANDOFF.md` 的「本機能力」要寫明這台有哪些、缺哪些。\n\n## 改本檔的規矩\n\n1. **跟結構變動同一個 commit**。分開改就會出現「文件說有 `foo/`、實際已經搬走」的空窗；接手者照結構圖找不到檔案時，通常不會回頭修文件，只會下次不再相信它。\n2. **附絕對日期**（寫 `2026-09-07`，不要寫「今天」），並更新檔頭的「最後更新」。\n3. **只寫結構，不寫進度**。「正在重構 X」屬於 `HANDOFF.md`；「打算重構 X」屬於 roadmap。\n4. **每個事實只有一個家**：這裡只寫誰是權威版，不要把權威版的內容複製過來。\n'
TEMPLATES['CLAUDE.md'] = '# CLAUDE.md\n\n@AGENTS.md\n\n<!-- 本檔刻意只有上面那一行 import。Claude Code 有 CLAUDE.md 就不會自己去讀 AGENTS.md，\n     而「用文字叫它去讀」不保證它真的會開那個檔。Claude 專屬的細則請放 .claude/rules/，\n     不要寫回這裡——那個目錄不計入上面那個判定，會跟 AGENTS.md 並存。 -->\n'
TEMPLATES['HANDOFF.md'] = '# HANDOFF — 工作交接狀態\n\n- **交接時間**：{{TODAY}} HH:MM（{{TZ}}）\n- **交棒者**：`bootstrap.py`（安裝程式寫完管理骨架；還沒有 commit）\n\n## 任務目標\n\n專案剛建立，管理骨架（AGENTS／HANDOFF／handoff skill／hook／驗證腳本）已由安裝程式寫入，還沒有 commit、還沒有 GitHub repo。下一棒照下面的第一批工作補完需要理解專案的部分，再首次發布。\n\n## Git 狀態\n\n- Repo：{{GH_VISIBILITY}} `{{GH_OWNER}}/{{GH_REPO}}`（尚未建立）；權威分支：`main`。\n- **待續分支**：無。\n- **工作中**：無（已交棒）\n- 本機能力：<作業系統；哪些憑證可用／未配置，不寫祕密值>\n\n## 已完成\n\n- 安裝程式寫入管理骨架：README／AGENTS／ARCHITECTURE／CLAUDE／HANDOFF／roadmap／`handoff` skill／兩個 `.claude` hook／`tools/check_docs.py`／`tools/verify_state.py`，逐檔雜湊相符；訪談答案在 `.bootstrap/answers.json`。\n\n## 未完成／下一步\n\n安裝後的第一批工作，做法在 `.claude/skills/handoff/mode-0.md`（安裝程式會依實際情況重寫這份清單）：\n\n1. 補寫 `ARCHITECTURE.md` 的「專案本體」、`README.md` 與 [docs/ai-notes/roadmap.md](docs/ai-notes/roadmap.md)，照實寫。\n2. 填 `tools/verify_state.py` 要查證的項目。\n3. 建 GitHub repo、本機驗收後首次推送，再跑遠端與工具驗收並回報。\n\n## 地雷與注意事項\n\n- 無。\n\n## 服務查證與期望快照\n\n`python -X utf8 tools/verify_state.py`（沒有 `python` 就用 `python3`）\n<目前實際關鍵輸出；未能查的層級寫 SKIPPED 與原因>\n\n## 懸置事項（AI 勿自行處理）\n\n- <等使用者決定的事>\n'
TEMPLATES['README.md'] = '# {{PROJECT_NAME}}\n\n{{ONELINER}}\n\n> 最後更新：{{TODAY}}（建立）\n\n## 為什麼做\n\n<部署後填：要解決什麼問題、給誰用；刻意不做什麼>\n\n## 快速開始\n\n| 用途 | 網址／指令 | 說明 |\n|---|---|---|\n| <主服務> | <部署後填> | <部署後填> |\n\n| 連線項目 | 值 |\n|---|---|\n| 服務網址 | <部署後填> |\n| 驗證方式 | <部署後填；只寫「key 在 {{SECRETS}} 的 XXX」，不要寫值> |\n| 主要資源 ID | <部署後填> |\n\n## 開發與驗證\n\n```bash\npython -X utf8 tools/verify_state.py\npython -X utf8 tools/check_docs.py\n```\n\n`verify_state.py` 查服務現況，結束碼 0 表示沒有 FAIL／ERROR；`check_docs.py` 查死連結、日期標頭、殘留佔位符與交接快照的格式，`--docs-only` 只查文件。macOS／Linux 常常只有 `python3`，`python` 不存在就改用 `python3`。兩支腳本**需要 Python 3.8 以上**：它們只用到 3.8 就有的 API，這是靜態擔保，不是在 3.8 上實跑過（2026-11-02／F14）。\n\n## 專案結構\n\n結構、每份檔案的用途與哪一份是權威版，在 [ARCHITECTURE.md](ARCHITECTURE.md)。\n\n## 協作方式\n\n這個專案由不同的 AI session、模型與機器輪流做。開工時跟 AI 說「接棒」，收工時說「交棒」；要先讓舊 session 交棒，新 session 才讀得到最新狀態。目前做到哪在 [HANDOFF.md](HANDOFF.md)，在這裡工作要守的規矩在 [AGENTS.md](AGENTS.md)。\n\n## 授權\n\n<部署後填>\n'
TEMPLATES['docs/ai-notes/roadmap.md'] = '# 待辦總表 / Roadmap（未完成工作盤點）\n\n> **本檔＝狀態表**：有哪些事、做到哪、相依、優先、誰能動。\n> **規格與實作細節不寫在這裡**，一律指回專門文件——本檔只記「狀態」與「決策」。\n> 與只描述當下進度的 [HANDOFF.md](../../HANDOFF.md) 分工：roadmap 是持久清單，HANDOFF 是這一輪。\n> 建立：{{TODAY}}。最後更新：{{TODAY}}。優先序為**建議值**，可隨時調整。\n\n**優先**：P1 先做／解鎖其他／高風險 ｜ P2 次要 ｜ P3 之後 ｜ P4 不急\n**誰能動**：🧑 使用者手動 ｜ 🤝 等使用者點頭後 AI 做 ｜ 🤖 AI 可做\n\n## 一、<分類名稱>\n\n| ID | 項目 | 狀態 | 相依 | 優先 | 誰 |\n|---|---|---|---|---|---|\n| R1 | <第一件事> | 未開始 | — | P1 | 🤝 |\n\n## 決策記錄（做過但被否決／暫緩的，寫在這裡免得反覆重提）\n\n| 日期 | 決策 | 理由 |\n|---|---|---|\n| {{TODAY}} | <例：先不做 X> | <理由> |\n\n<!-- 完成的項目用 ~~R1~~ ✅ 標記並保留，狀態欄寫「YYYY-MM-DD 完成」＋指向細節文件的連結。 -->\n'
TEMPLATES['tools/check_docs.py'] = '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""文件與交接快照的機械檢查（交接用）。verify_state.py 查「服務現況」，本腳本查「文件本身」。\n\n**名字講的就是範圍**（2026-11-02 改／查核報告 F08）：它查**機械可判定**的腐化模式，\n不查「文件寫得對不對」。它不是完整的 Markdown 驗證器（連結檢查是 regex，而且刻意\n跳過圍欄與行內程式碼），也**不判斷待辦是否真的完成**——那是交接程序 B6 的事，沒有\n工具代替得了。舊版叫「文檔一致性檢查」，而「一致性」聽起來像它驗過全部，於是\n「通過」被讀成「文件沒問題」。\n\n用法（專案根目錄執行）：\n  python -X utf8 tools/check_docs.py              # 全部檢查\n  python -X utf8 tools/check_docs.py --quiet      # 只印問題與結論\n  python -X utf8 tools/check_docs.py --docs-only   # 只查文件，不查交接快照（第 7 項）\n\n檢查七項（都是實際發生過的腐化模式）：\n  1. 死連結     ——markdown 相對連結指向不存在的檔案（整併文件時最常見）\n  2. 過期字串   ——換了網址／改了名稱後殘留的舊值（見下方 STALE_PATTERNS，依專案調整）\n  3. 缺日期標頭 ——DATED_DIRS 底下每份都要有「最後更新」，否則無法判斷可信度\n  4. 硬編數量   ——「共 N 份」這類會自己過期的寫法\n  5. 殘留佔位符 ——部署訪談沒換掉的洞（2026-08-05 加入：原本是部署自檢清單上一個要人工 grep\n                  的核取方塊，而人工核取方塊遲早會有人跳過；改由工具擋才會自動發生。這一項掃\n                  PLACEHOLDER_GLOBS 的所有檔案，不只 .md——佔位符也會留在 tools/verify_state.py\n                  這種非文件檔裡；比對的是 PLACEHOLDER_NAMES 這份封閉清單，不是雙大括號語法）\n  6. 工作中欄位 ——HANDOFF.md 的「工作中」標記不見了，或標記在工作中卻沒填工具欄（2026-10-30\n                  加入，2026-10-31 補工具欄：這個欄位是跨機器誤接棒防呆的唯一依據，掉了不會有\n                  任何徵兆——下一棒只會看到一切正常然後接棒，正是這套骨架最怕的靜默失效。而\n                  「欄位缺席」與「沒人在做」分不開，所以不接受「沒寫就是沒人」：必須明確寫\n                  「無（已交棒）」。工具欄同理——少了它，同機器換工具的誤接棒會靜默退化成\n                  「大概是你自己另一個視窗」，而退化後的畫面跟「沒這個機制」一模一樣。\n                  沒有 HANDOFF.md 的 repo 整項跳過——那個洞由第 7 項補）\n  7. 交接快照   ——`HANDOFF.md` 必須存在、必要欄位與章節齊備、不超過 80 行\n                  （2026-11-02 加入／查核報告 F08：第 6 項只在「HANDOFF.md 有出現在\n                  輸入清單裡」時才驗，所以**整份被刪掉或改名時它回報乾淨**，而那正好\n                  把跨機器誤接棒防呆連根拔掉。80 行與必要章節是 skill B6 的規則，\n                  在此之前較強的版本只存在於骨架自己的 repo，沒有部署給使用者。\n                  真的只想查文件時用 `--docs-only`）\n\n問題以結束碼 2 回報，乾淨為 0。本工具唯讀，絕不修改任何檔案。\n\nsource: PROJECT-BOOTSTRAP.md v2026-11-03 — 權威版在部署包，改這裡之前先改部署包再同步各專案。\n「專案設定」區塊以外的內容應與權威版一致；副本落後時用這一行辨識。\n"""\nimport argparse\nimport pathlib\nimport re\nimport subprocess\nimport sys\n\n# ── 專案設定（部署後依實際情況調整）────────────────────────────\n# 過期字串：搬遷／改名後不該再出現的東西。留空 list 就跳過這項檢查。\nSTALE_PATTERNS = [\n    # (\'localhost:8080\', \'已遷到正式網域，文件不該再出現本機位址\'),\n]\n# 這些關鍵字出現在同一行時視為「刻意保留的歷史敘述」，不報錯。\nSTALE_OK = (\'已停用\', \'已退役\', \'歷史\', \'勿再啟動\', \'~~\')\n# 這些路徑整份豁免（例如保存歷史決策的文件、已退役的部署設定）。\nSTALE_OK_PATHS = ()\n# 這些路徑下的 .md 必須在前 8 行有「最後更新」。比對的是路徑前綴，所以單一檔案也放得進來。\n# ARCHITECTURE.md 在列，是因為它會被拿來「找檔案」：沒有日期就無法判斷這份結構圖是哪一天的事實，\n# 而過期的結構圖比沒有更糟——照著它找不到檔案的人，通常不會回頭修文件。\nDATED_DIRS = (\'docs/ai-notes/\', \'ARCHITECTURE.md\')\n# 連結檢查的豁免路徑。部署包內嵌各檔範本，範本裡的相對路徑是照「該範本部署後的位置」寫的\n# （例如 docs/ai-notes/ 或 .agents/skills/<slug>/），用部署包自己的位置去解析必然解不到——\n# 那是假警報，不是死連結。沒有這條，自檢清單第 1 項在刪掉部署包之前永遠不可能通過，\n# 而部署者只會學到「這支腳本的 FAIL 可以無視」，之後真的死連結也跟著被無視。\nLINK_OK_PATHS = (\'PROJECT-BOOTSTRAP.md\',)\n# 佔位符檢查掃哪些檔（不只 .md：訪談要填的值也會落在 .gitignore 與 verify_state.py 裡）。\nPLACEHOLDER_GLOBS = (\'*.md\', \'*.py\', \'*.sh\', \'*.json\', \'.gitignore\', \'.gitattributes\')\n# 豁免路徑。部署包本身整份都是佔位符，還沒刪掉時不該報錯（自檢清單最後一項會叫你刪它）。\n# 專案若真的有檔案會用到上面那些名字當樣板變數，把該檔或該目錄加進來。\nPLACEHOLDER_OK_PATHS = (\'PROJECT-BOOTSTRAP.md\',)\n# ── 專案設定結束 ──────────────────────────────────────────────\n# 以上依專案調整，以下與權威版一致。`tools/sync_project.py` 升級本檔時，會把上面這一段\n# 原樣留下、只換掉其餘部分——沒有這個標記它就得用啟發式猜邊界，而猜錯就是把專案自己的\n# 過期字串規則與豁免路徑默默洗掉，然後沒有人會發現。\n\n# 第 7 項要求的欄位與章節。**這是制度的一部分，不是專案設定**——所以放在上面那個\n# 標記之外，`sync_project.py` 升級本檔時會跟著覆蓋。要改就改部署包。\nHANDOFF_FILE = \'HANDOFF.md\'\nHANDOFF_FIELDS = (\'交接時間\', \'交棒者\', \'待續分支\', \'工作中\')\nHANDOFF_SECTIONS = (\'任務目標\', \'Git 狀態\', \'已完成\', \'未完成／下一步\',\n                    \'地雷與注意事項\', \'服務查證與期望快照\', \'懸置事項（AI 勿自行處理）\')\nHANDOFF_MAX_LINES = 80\n\nCOUNT_RE = re.compile(r\'(共|計|全)\\s*\\d+\\s*(份|個|支|條)|\\d+\\s*份(?!量)\')\nCOUNT_CONTEXT = (\'份\', \'個檔\', \'支腳本\', \'知識庫\')\n# 部署訪談會填的佔位符（第 1 節那張表）。這裡刻意用「名字的封閉清單」而不是「任何雙大括號」\n# 或「雙大括號＋全大寫」：專案自己的樣板語法長得一模一樣——verify_state.py 範本裡有 docker 的\n# --format \'{{ .Names }}\'，也遇過專案拿同樣的大寫雙大括號寫法產 HTML——用語法比對兩者都會中。\n# 骨架只會留下下面這幾個洞，列舉它們就抓得完，而且不可能誤傷別人的樣板。\n# 部署包新增佔位符時要同步這份清單（verify_bootstrap.py 會比對，漏了會 FAIL）。\nPLACEHOLDER_NAMES = (\n    \'PROJECT_NAME\', \'ONELINER\', \'GH_OWNER\', \'GH_REPO\', \'GH_VISIBILITY\', \'LANG\',\n    \'TZ\', \'TODAY\', \'SECRETS\', \'RUNTIME_DIRS\', \'STACK_DIRS\', \'VERIFY_TARGETS\',\n)\nPLACEHOLDER_RE = re.compile(r\'\\{\\{(?:\' + \'|\'.join(PLACEHOLDER_NAMES) + r\')\\}\\}\')\n\n\ndef tracked(*globs):\n    # -z 不能拿掉：git ls-files 預設 core.quotepath=true，會把非 ASCII 檔名輸出成加了\n    # 雙引號的八進位跳脫（"\\350\\256\\200..."）。那串原封不動包成 Path，開檔必炸——Windows\n    # 是 OSError errno 22、macOS／Linux 是 FileNotFoundError，兩邊都是 traceback 而不是\n    # FAIL，接手的人很容易判成「環境或 Python 版本問題」而跳過驗證，正好繞開這套骨架\n    # 唯一的文檔關卡。2026-08-05 實際部署時踩到（中文檔名的專案會一直踩）。\n    # -z 另外連「檔名含換行」也一起擋掉，比 -c core.quotepath=false 更完整。\n    out = subprocess.run([\'git\', \'ls-files\', \'-z\', *globs],\n                         capture_output=True, text=True, encoding=\'utf-8\').stdout\n    return [pathlib.Path(p) for p in out.split(\'\\0\') if p]\n\n\ndef tracked_md():\n    return tracked(\'*.md\')\n\n\nFENCE_RE = re.compile(r\'^\\s*(```+|~~~+)\')\nTITLE_RE = re.compile(r\'\\s+["\\\'][^"\\\']*["\\\']\\s*$\')\n\n\ndef strip_code(text):\n    """把圍欄區塊與行內 code span 換成空白（行號不變）。\n\n    為什麼（2026-11-02／查核報告 F08）：文件裡的程式碼與範例常含 `[x](path)` 這種形狀，\n    那不是連結、那個路徑也不該存在。照掃就會**把正確的文件報成死連結**，而「這支腳本的\n    FAIL 可以無視」一旦被學會，真的死連結也跟著被無視——那比沒有這項檢查更糟。\n    """\n    out, fence = [], None\n    for line in text.split(\'\\n\'):\n        m = FENCE_RE.match(line)\n        if fence is not None:\n            out.append(\'\')\n            if m and line.strip().startswith(fence):\n                fence = None\n            continue\n        if m:\n            fence = m.group(1)\n            out.append(\'\')\n            continue\n        out.append(re.sub(r\'`[^`]*`\', lambda s: \' \' * len(s.group(0)), line))\n    return \'\\n\'.join(out)\n\n\ndef link_target(raw):\n    """從 `](...)` 裡取出真正的路徑：去掉 <>、去掉 "title"、去掉 anchor。\n\n    `[x](path "title")` 舊版會拿 `path "title"` 去開檔，必然不存在——又一種假警報。\n    """\n    link = raw.strip()\n    # R09：先去 title，再去 destination 的角括號；兩種合法寫法可以同時出現。\n    link = TITLE_RE.sub(\'\', link).strip()\n    if link.startswith(\'<\') and link.endswith(\'>\'):\n        link = link[1:-1].strip()\n    return link.split(\'#\')[0].strip()\n\n\ndef check_links(files):\n    bad, total = [], 0\n    for md in files:\n        posix = md.as_posix()\n        if any(posix == p or posix.startswith(p) for p in LINK_OK_PATHS):\n            continue\n        body = strip_code(md.read_text(encoding=\'utf-8\'))\n        for m in re.finditer(r\'\\[([^\\]]*)\\]\\(([^)]+)\\)\', body):\n            link = link_target(m.group(2))\n            if not link or link.startswith((\'http://\', \'https://\', \'mailto:\')):\n                continue\n            total += 1\n            if not (md.parent / link).resolve().exists():\n                bad.append(f\'{md.as_posix()} -> {link}\')\n    return total, bad\n\n\ndef check_stale(files):\n    bad = []\n    if not STALE_PATTERNS:\n        return bad\n    for md in files:\n        posix = md.as_posix()\n        if any(posix.startswith(p) or posix == p for p in STALE_OK_PATHS):\n            continue\n        for n, line in enumerate(md.read_text(encoding=\'utf-8\').split(\'\\n\'), 1):\n            for pat, why in STALE_PATTERNS:\n                if pat in line and not any(ok in line for ok in STALE_OK):\n                    bad.append(f\'{posix}:{n}  「{pat}」（{why}）  {line.strip()[:70]}\')\n    return bad\n\n\ndef check_dates(files):\n    bad = []\n    for md in files:\n        if not any(md.as_posix().startswith(d) for d in DATED_DIRS):\n            continue\n        head = \'\\n\'.join(md.read_text(encoding=\'utf-8\').split(\'\\n\')[:8])\n        if \'最後更新\' not in head:\n            bad.append(f\'{md.as_posix()}  前 8 行沒有「最後更新：YYYY-MM-DD」\')\n    return bad\n\n\ndef check_placeholders(files):\n    bad = []\n    for md in files:\n        posix = md.as_posix()\n        if any(posix == p or posix.startswith(p) for p in PLACEHOLDER_OK_PATHS):\n            continue\n        for n, line in enumerate(md.read_text(encoding=\'utf-8\').split(\'\\n\'), 1):\n            for m in PLACEHOLDER_RE.finditer(line):\n                bad.append(f\'{posix}:{n}  「{m.group(0)}」  {line.strip()[:70]}\')\n    return bad\n\n\n# 交棒後「工作中」欄位唯一合法的值。hook 與這支檢查器都只接受它，\n# 不接受任何含「無」的字串（2026-11-02，查核報告 F01）。\nFREE_MARK = \'無（已交棒）\'\n\n\ndef check_busy_field(files):\n    # 第 6 項：HANDOFF.md 的「工作中」欄位必須在。這一欄是 handoff skill A2.5 判斷\n    # 「同一條分支有沒有別人在做」的唯一依據，而它掉了不會有任何徵兆——下一棒\n    # 只會看到一切正常然後接棒。不接受「沒寫就是沒人在做」：那和「忘了寫」分不開。\n    found, bad = False, []\n    for md in files:\n        if md.as_posix() != \'HANDOFF.md\':\n            continue\n        found = True\n        text = md.read_text(encoding=\'utf-8\')\n        if \'**工作中**\' not in text:\n            bad.append(\'HANDOFF.md  「Git 狀態」缺「- **工作中**：無（已交棒）」欄位\'\n                       \'——跨機器誤接棒防呆靠它（見 handoff skill 的 A2.5／A5／B6）\')\n            continue\n        # 2026-10-31 加：標記在「工作中」的時候必須帶工具欄\n        # （`機器` ／ `工具` ／ `session 名`，最後一欄可選）。少了工具名，同一台機器換個\n        # 工具就會落進 hook 的「大概是你自己另一個視窗」🟡，而同機器通常就是同一個工作樹，\n        # 兩個 agent 即時互相覆寫——比跨機器那個洞更貴。新格式少一欄不會壞掉，只會靜默\n        # 退化回舊行為，而退化後的畫面跟「沒這個機制」一模一樣，所以要擋在這裡。\n        # 判別子是 session 名裡的全形豎線：`機器` ／ `工具` 的第二欄不會有它，\n        # `機器` ／ `session 名`（舊格式）的第二欄一定有。\n        # 2026-11-02 改成精確比對（查核報告 F01）。舊版用 `\'無\' in value` 判「已交棒」，\n        # 於是標記寫著別台機器正在做、而 session 主題叫「修無效連結」，整個格式驗證就被\n        # 跳過——兩支 hook 用同一個判準，所以同一個**正常的任務名稱**會讓它們印出錯誤的\n        # 綠燈。現在只有正規化後完整等於「無（已交棒）」才算空閒，其餘一律驗欄位。\n        # 同時擋「欄位重複」：hook 只讀第一列，重複的話判讀結果等於看運氣。\n        rows = [(n, l) for n, l in enumerate(text.splitlines(), 1) if \'**工作中**\' in l]\n        if len(rows) > 1:\n            bad.append(\'HANDOFF.md:%s  有 %d 列「工作中」欄位——這一欄只能有一列，\'\n                       \'hook 只會讀到第一列，其餘的靜默失效（B6 是覆寫，不要往下疊）\'\n                       % (\'、\'.join(str(n) for n, _ in rows), len(rows)))\n        for num, line in rows:\n            # 砍掉「，2026-… (+08) 開工」那段尾註，再去頭尾的半形／全形空白與反引號\n            value = line.split(\'：\', 1)[-1].split(\'，\')[0].strip(\' \\t\\u3000`\').strip()\n            if value == FREE_MARK:\n                continue\n            fields = [f.strip(\' \\t\\u3000`\').strip() for f in value.split(\'／\')]\n            if not fields[0]:\n                bad.append(f\'HANDOFF.md:{num}  「工作中」欄位有值、但解析不出機器欄\'\n                           f\'（讀到：{value[:40]}）——交棒後要正好寫「{FREE_MARK}」，\'\n                           \'開工時寫 `機器` ／ `工具` ／ `session 名`（第三欄可選）\')\n            elif len(fields) < 2 or not fields[1] or \'｜\' in fields[1]:\n                bad.append(f\'HANDOFF.md:{num}  「工作中」標記缺工具欄——格式是 \'\n                           \'`機器` ／ `工具` ／ `session 名`（可選）。少了工具名，\'\n                           \'同機器換工具的誤接棒就擋不住（見 handoff skill 的 A5）\')\n    return found, bad\n\n\ndef check_snapshot(files):\n    """第 7 項：交接快照的結構（存在、必要欄位、必要章節、行數上限）。\n\n    為什麼第 6 項不夠（查核報告 F08）：它是「HANDOFF.md 有出現在輸入清單裡才驗」，\n    所以**整份被刪掉或改名時，它回報乾淨**——而那一刀正好把跨機器誤接棒防呆連根拔掉，\n    一聲不響。欄位唯一性、必要章節與 80 行這幾條是 skill B6 的規則，在 2026-11-02 之前\n    只有骨架自己的 repo 在驗，使用者的專案拿不到。\n\n    天花板：它驗結構，**不驗內容**。待辦是不是真的做完、快照寫得對不對，仍然只能靠 B6\n    逐項核對；這一項全過不代表狀態正確。\n    """\n    bad = []\n    target = [md for md in files if md.as_posix() == HANDOFF_FILE]\n    if not target:\n        return [\'%s 不存在或沒被 git 追蹤——它是這套制度的核心檔，\'\n                \'少了它 A2.5 的跨機器防呆與 B6 的交接快照都沒有依據\'\n                \'（真的只想查文件請用 --docs-only）\' % HANDOFF_FILE]\n    text = target[0].read_text(encoding=\'utf-8\')\n    lines = text.splitlines()\n    if len(lines) > HANDOFF_MAX_LINES:\n        bad.append(\'%s 有 %d 行，超過 %d 行——它是當下快照，不是日誌（歷史查 Git；見 B6）\'\n                   % (HANDOFF_FILE, len(lines), HANDOFF_MAX_LINES))\n    for label in HANDOFF_FIELDS:\n        hits = re.findall(r\'^- \\*\\*\' + re.escape(label) + r\'\\*\\*：(.+)$\', text, re.M)\n        if len(hits) != 1 or not hits[0].strip():\n            bad.append(\'%s 的「%s」欄位要有且只有一列、而且非空（讀到 %d 列）\'\n                       % (HANDOFF_FILE, label, len(hits)))\n    for heading in HANDOFF_SECTIONS:\n        # 比對**開頭**而不是整行：標題後面加註記（`## 已完成（2026-11-01）`）無害，\n        # 真正的病是同一節出現兩次——那就是 B6 禁止的「往下疊成日誌」。2026-11-02 在\n        # 六個專案上實跑時量到：整行相等會把加了日期後綴的那一份判成「缺章節」，\n        # 訊息指著錯的方向，而同一份檔案真的有兩個「已完成」。\n        hits = re.findall(r\'^## \' + re.escape(heading), text, re.M)\n        if len(hits) == 0:\n            bad.append(\'%s 缺少章節「## %s」（B6 的覆寫模板有這一節）\'\n                       % (HANDOFF_FILE, heading))\n        elif len(hits) > 1:\n            bad.append(\'%s 有 %d 個「## %s」——它是當下快照，不要往下疊成日誌\'\n                       \'（歷史查 Git；見 B6）\' % (HANDOFF_FILE, len(hits), heading))\n    return bad\n\n\ndef check_counts(files):\n    bad = []\n    for md in files:\n        for n, line in enumerate(md.read_text(encoding=\'utf-8\').split(\'\\n\'), 1):\n            if line.lstrip().startswith(\'>\') and \'最後更新\' in line:\n                continue\n            m = COUNT_RE.search(line)\n            if m and any(w in line for w in COUNT_CONTEXT):\n                bad.append(f\'{md.as_posix()}:{n}  「{m.group(0)}」 {line.strip()[:70]}\')\n    return bad\n\n\ndef check_staged_consistency():\n    """R07：本次文件／檢查器不得部分 stage，才能用工作樹檢查證明提交內容。"""\n    def names(*args):\n        p = subprocess.run([\'git\', \'diff\', \'--name-only\', \'-z\', *args],\n                           capture_output=True, text=True, encoding=\'utf-8\')\n        if p.returncode:\n            raise RuntimeError(\'無法讀取 Git 提交集合\')\n        return set(filter(None, p.stdout.split(\'\\0\')))\n    staged = names(\'--cached\')\n    dirty = names()\n    return sorted(p for p in staged & dirty if p.endswith(\'.md\') or p == \'tools/check_docs.py\')\n\n\ndef main():\n    ap = argparse.ArgumentParser()\n    ap.add_argument(\'--quiet\', action=\'store_true\')\n    ap.add_argument(\'--staged\', action=\'store_true\', help=\'提交前檢查，拒絕本次文件／檢查器部分 stage\')\n    ap.add_argument(\'--docs-only\', action=\'store_true\',\n                    help=\'只查文件，不查交接快照（第 7 項）\')\n    args = ap.parse_args()\n\n    if args.staged:\n        partial = check_staged_consistency()\n        if partial:\n            print(\'[index] 🔴 本次文件／檢查器有未暫存變更，請先核對並重新 stage：\' + \'、\'.join(partial))\n            return 2\n    files = tracked_md()\n    if not files:\n        print(\'找不到 tracked markdown——請在專案根目錄執行，且檔案已 git add\')\n        return 2\n\n    problems = 0\n    total, dead = check_links(files)\n    if not args.quiet:\n        print(f\'[links]   檢查 {total} 個相對連結\')\n    if dead:\n        problems += len(dead)\n        print(f\'[links]   🔴 {len(dead)} 個死連結：\')\n        for b in dead:\n            print(f\'            {b}\')\n\n    stale = check_stale(files)\n    if stale:\n        problems += len(stale)\n        print(f\'[stale]   🔴 {len(stale)} 處過期字串：\')\n        for b in stale:\n            print(f\'            {b}\')\n\n    undated = check_dates(files)\n    if undated:\n        problems += len(undated)\n        print(f\'[dates]   🔴 {len(undated)} 份缺「最後更新」標頭：\')\n        for b in undated:\n            print(f\'            {b}\')\n    elif not args.quiet:\n        print(\'[dates]   受管目錄全部有「最後更新」標頭\')\n\n    left = check_placeholders(tracked(*PLACEHOLDER_GLOBS))\n    if left:\n        problems += len(left)\n        print(f\'[holes]   🔴 {len(left)} 處殘留佔位符（部署訪談沒填完，照文件做會失敗）：\')\n        for b in left:\n            print(f\'            {b}\')\n    elif not args.quiet:\n        print(\'[holes]   沒有殘留的佔位符\')\n\n    found_handoff, busy = check_busy_field(files)\n    if busy:\n        problems += len(busy)\n        print(f\'[busy]    🔴 {len(busy)} 處「工作中」欄位問題：\')\n        for b in busy:\n            print(f\'            {b}\')\n    elif not args.quiet:\n        print(\'[busy]    HANDOFF.md 的「工作中」欄位在位\' if found_handoff\n              else \'[busy]    沒有 HANDOFF.md，跳過這一項\')\n\n    if args.docs_only:\n        if not args.quiet:\n            print(\'[snap]    --docs-only：跳過交接快照檢查\')\n    else:\n        snap = check_snapshot(files)\n        if snap:\n            problems += len(snap)\n            print(f\'[snap]    🔴 {len(snap)} 處交接快照問題：\')\n            for b in snap:\n                print(f\'            {b}\')\n        elif not args.quiet:\n            print(\'[snap]    交接快照的欄位、章節與行數都合格（內容仍由 B6 核對）\')\n\n    counts = check_counts(files)\n    if counts:\n        print(f\'[counts]  🟡 {len(counts)} 處硬編數量（會自己過期，建議改成不寫數字）：\')\n        for b in counts:\n            print(f\'            {b}\')\n\n    print()\n    if problems:\n        print(f\'FAIL：{problems} 個問題需修正（硬編數量僅提醒，不計入）\')\n        return 2\n    print(\'OK：機械檢查通過（語意與「待辦是否真的完成」仍由交接程序 B6 核對）\')\n    return 0\n\n\nif __name__ == \'__main__\':\n    sys.exit(main())\n'
TEMPLATES['tools/verify_state.py'] = '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""一鍵現況查證（交接用）。把接手查證從 5+ 個 AI 回合壓到 1 個回合（省 token）。\n\n用法（專案根目錄執行）：\n  python -X utf8 tools/verify_state.py\n  python -X utf8 tools/verify_state.py --strict   # 連 SKIP 都算不通過（驗收／CI 用）\n\n輸出＝緊湊 key=value 事實快照 ＋ 最後的彙總行；與 HANDOFF.md「服務查證與期望快照」比對\n即完成查證。腳本不判斷**期望值**（那放 HANDOFF，會隨進度變，避免兩處維護）——但\n**「這一項失敗了」本身就是事實**，所以它一定會反映在結束碼上。\n\n結束碼（2026-11-02 加／查核報告 F04）：\n  0 ＝ 沒有 FAIL／ERROR\n  2 ＝ 有 FAIL 或 ERROR\n  3 ＝ `--strict` 且有非 OPTIONAL 的 SKIP\n舊版**每一種情況都回 0**：在生成的檢查裡放一個 exit 7 的命令，畫面印著 `=rc7`，結束碼\n仍是 0。於是任何「跑 verify_state，exit 0 就算驗過」的下游流程都會誤過關，而畫面上那行\n字沒人會回頭看。`NOT_CONFIGURED` 仍然回 0，那是刻意的（骨架還沒填不是故障），但它跟\n「真的失敗」從此分得開。\n\n每項檢查的狀態只有五種：PASS／FAIL／ERROR／SKIP／NOT_CONFIGURED。\n  FAIL  ＝ 服務回答了，但答得不對（HTTP 非 2xx、命令非零退出、expect 沒出現）\n  ERROR ＝ 根本沒問到（連線失敗、timeout、未預期例外）——不要自己推論成「未配置」\n  SKIP  ＝ 這台機器缺配置（憑證、BASE、執行檔）。**缺配置不等於通過**，所以它獨立列出；\n          必需項的 SKIP 在 `--strict` 下不通過，真正可選的項目寫進 OPTIONAL。\n\nsource: PROJECT-BOOTSTRAP.md v2026-11-03 — 權威版在部署包，改這裡之前先改部署包再同步各專案。\n本檔的 CHECKS 區塊本來就該逐專案填寫；其餘內容應與權威版一致。\n"""\nimport argparse\nimport json\nimport os\nimport subprocess\nimport sys\nimport urllib.error\nimport urllib.request\n\n# ── 專案設定（部署後填這裡）──────────────────────────────────\nBASE = os.environ.get(\'PROJECT_BASE_URL\', \'\')   # 例：https://example.com\nSECRET_FILE = \'.env\'                            # 憑證來源檔\nSECRET_KEY = \'API_KEY\'                          # 檔內的變數名\n\n# (顯示名稱, 相對路徑或完整 URL, 是否需要憑證[, 預期])\n# 第 4 個元素可省；省略＝只要 HTTP 2xx 就算 PASS。填 int＝必須正好是這個狀態碼\n# （例如 401，用來驗「保護真的生效」）；填 str＝這段字必須出現在回應裡。\n# **只把「有回應」當成正常是不夠的**：200 配一個空的錯誤頁照樣會 PASS，所以會\n# 影響交接判斷的那幾項請填 expect（查核報告 F04）。\nHTTP_CHECKS = [\n    # (\'health\', \'/api/health\', False, \'ok\'),\n]\n# (顯示名稱, 命令 list)\nCMD_CHECKS = [\n    # (\'containers\', [\'docker\', \'ps\', \'--format\', \'{{ .Names }}\']),\n]\n# 這些檢查缺配置時算可接受，連 `--strict` 都不會因為它們而非零。\n# 沒列在這裡的項目，缺配置是「這台機器驗不了」，不是「驗過了」。\nOPTIONAL = ()\n# ── 專案設定結束 ──────────────────────────────────────────────\n\nOK_STATUS = range(200, 300)\n_SECRET = None\n\n\ndef read_secret():\n    """從 SECRET_FILE 讀憑證；讀不到回 None（呼叫端標 SKIPPED，不得自行找憑證）。"""\n    try:\n        for line in open(SECRET_FILE, encoding=\'utf-8\'):\n            if line.startswith(SECRET_KEY + \'=\'):\n                return line.split(\'=\', 1)[1].strip()\n    except OSError:\n        pass\n    return None\n\n\ndef mask(text):\n    """把憑證值從要印出來的字串裡遮掉。\n\n    這一層是必要的，因為印出來的東西有兩個來源不在我們控制下：命令的 stdout／stderr，\n    以及例外訊息（urllib 的錯誤字串會帶上整個 URL，而有些服務把 token 放在 query）。\n    交接快照會被貼進 HANDOFF、貼進對話、貼進 issue——祕密只要漏一次就等於洩漏。\n    """\n    if not _SECRET or len(_SECRET) < 4:\n        return text\n    return text.replace(_SECRET, \'***\')\n\n\ndef say(line):\n    print(mask(line))\n\n\ndef http(name, path, key, expect=None):\n    url = path if path.startswith(\'http\') else BASE.rstrip(\'/\') + path\n    req = urllib.request.Request(url)\n    if key:\n        req.add_header(\'Authorization\', f\'Bearer {key}\')\n    try:\n        with urllib.request.urlopen(req, timeout=20) as r:\n            body = r.read(4000).decode(\'utf-8\', \'replace\')\n            try:\n                data = json.loads(body)\n                brief = str(len(data)) + \' items\' if isinstance(data, list) else \'json ok\'\n            except json.JSONDecodeError:\n                brief = f\'{len(body)} bytes\'\n            if isinstance(expect, int) and r.status != expect:\n                say(f\'{name}=FAIL http={r.status} 預期 {expect}\')\n                return \'FAIL\'\n            if isinstance(expect, str) and expect not in body:\n                say(f\'{name}=FAIL http={r.status} 回應裡沒有「{expect}」 {brief}\')\n                return \'FAIL\'\n            if expect is None and r.status not in OK_STATUS:\n                say(f\'{name}=FAIL http={r.status} {brief}\')\n                return \'FAIL\'\n            say(f\'{name}=PASS http={r.status} {brief}\')\n            return \'PASS\'\n    except urllib.error.HTTPError as e:\n        # 4xx／5xx 也是回答。expect 指定了這個碼就算通過（驗「401 保護生效」用）。\n        if isinstance(expect, int) and e.code == expect:\n            say(f\'{name}=PASS http={e.code}（預期）\')\n            return \'PASS\'\n        say(f\'{name}=FAIL http={e.code}\')\n        return \'FAIL\'\n    except Exception as e:                      # 連線層錯誤：印事實，不下「未配置」結論\n        say(f\'{name}=ERROR {type(e).__name__}: {e}\')\n        return \'ERROR\'\n\n\ndef cmd(name, argv):\n    try:\n        p = subprocess.run(argv, capture_output=True, text=True, timeout=60)\n        # R04：先遮罩完整字串，再做換行整理與截斷，否則憑證跨摘要邊界會洩出前綴。\n        out = \' | \'.join(l.strip() for l in mask(p.stdout).strip().split(\'\\n\') if l.strip())\n        tail = out[:300] or mask(p.stderr).strip()[:200]\n        # 非零退出碼**不得被吞掉**：舊版只印 `=rc7` 然後回 0（查核報告 F04）。\n        status = \'PASS\' if p.returncode == 0 else \'FAIL\'\n        say(f\'{name}={status} rc{p.returncode} {tail}\')\n        return status\n    except FileNotFoundError:\n        say(f\'{name}=SKIP（本機沒有 {argv[0]}）\')\n        return \'SKIP\'\n    except Exception as e:\n        say(f\'{name}=ERROR {type(e).__name__}: {e}\')\n        return \'ERROR\'\n\n\ndef main(argv=None):\n    global _SECRET\n    ap = argparse.ArgumentParser()\n    ap.add_argument(\'--strict\', action=\'store_true\',\n                    help=\'非 OPTIONAL 的 SKIP 也算不通過（回 3）\')\n    args = ap.parse_args(argv)\n\n    if not HTTP_CHECKS and not CMD_CHECKS:\n        print(\'verify_state=NOT_CONFIGURED（尚未填 HTTP_CHECKS／CMD_CHECKS，見本檔頂端）\')\n        return 0\n\n    _SECRET = read_secret()\n    results = []\n    for entry in HTTP_CHECKS:\n        name, path, need_key = entry[0], entry[1], entry[2]\n        expect = entry[3] if len(entry) > 3 else None\n        if need_key and not _SECRET:\n            say(f\'{name}=SKIP（{SECRET_FILE} 沒有 {SECRET_KEY}\'\n                \'——先確認是不是設定沒帶到，再下結論）\')\n            results.append((name, \'SKIP\'))\n            continue\n        if not BASE and not path.startswith(\'http\'):\n            say(f\'{name}=SKIP（未設 PROJECT_BASE_URL）\')\n            results.append((name, \'SKIP\'))\n            continue\n        results.append((name, http(name, path, _SECRET if need_key else None, expect)))\n\n    for entry in CMD_CHECKS:\n        results.append((entry[0], cmd(entry[0], entry[1])))\n\n    tally = {}\n    for _, status in results:\n        tally[status] = tally.get(status, 0) + 1\n    print(\'verify_state=\' + \' \'.join(\n        \'%s:%d\' % (s, tally[s]) for s in (\'PASS\', \'FAIL\', \'ERROR\', \'SKIP\') if tally.get(s)))\n\n    bad = [n for n, s in results if s in (\'FAIL\', \'ERROR\')]\n    skipped = [n for n, s in results if s == \'SKIP\' and n not in OPTIONAL]\n    if bad:\n        print(\'FAIL：%d 項沒通過（%s）——exit 0 的下游流程不能把這當驗收\'\n              % (len(bad), \'、\'.join(bad)))\n        return 2\n    if skipped:\n        print(\'SKIP：%d 項這台機器驗不了（%s）。缺配置不等於通過；--strict 會因此非零\'\n              % (len(skipped), \'、\'.join(skipped)))\n        if args.strict:\n            return 3\n    print(\'OK：所有可驗的項目都通過\')\n    return 0\n\n\nif __name__ == \'__main__\':\n    sys.exit(main())\n'
KIT = {'version': '2026-11-20.2', 'owners': OWNERS, 'templates': TEMPLATES}


# ── 以下原樣取自 tools/sync_project.py（update 模式與 sync_project.py 共用同一套合併邏輯）──
def by_update(updates, kind):
    return tuple(rel for rel, update in updates.items() if update == kind)


SKILL_DIR = '.claude/skills/handoff/'


SKILL_ENTRY = SKILL_DIR + 'SKILL.md'


SKILL_PARTS = tuple(rel for rel in by_update(UPDATES, 'whole')
                    if rel.startswith(SKILL_DIR) and rel != SKILL_ENTRY)


WHOLE = SKILL_PARTS + (SKILL_ENTRY,) + tuple(
    rel for rel in by_update(UPDATES, 'whole') if not rel.startswith(SKILL_DIR))


SURGICAL = 'tools/check_docs.py'


SETTINGS_START = '# ── 專案設定（部署後依實際情況調整）'


SETTINGS_END = '# ── 專案設定結束'


WIRING = by_update(UPDATES, 'wiring')


OWNED_SCRIPTS = ('git-freshness.sh', 'pre-push-handoff.sh')


CODEX_WIRING = '.codex/hooks.json'


CODEX_LAUNCHER = '.claude/hooks/codex-hook.cmd'


PARTIAL = by_update(UPDATES, 'lines')


INSTANCE = by_update(UPDATES, 'seed')


BUSY_FIELD = '- **工作中**：無（已交棒）'


GITIGNORE_LINES = ('.claude/.bootstrap-version', '.obsidian/')


CLAUDE_IMPORT = '@AGENTS.md'


SHARED_START = '<!-- 共用制度開始'


SHARED_END = '<!-- 共用制度結束 -->'


LEGACY_HANDOFF_HEADINGS = ('## 開工第一件事', '## 跨模型／跨機器協作規範')


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


def known_hook_commands(script):
    """只承認已發布的命令形狀，不用 shell 解析猜所有權（2026-11-03／R01）。"""
    return {
        'bash .claude/hooks/' + script,
        'bash "$(git rev-parse --show-cdup).claude/hooks/' + script + '"',
        'cmd /d /c "$(git rev-parse --show-cdup).claude/hooks/codex-hook.cmd" ' + script,
        'cmd /d /c "$((git rev-parse --show-cdup) -replace \'/\',\'\\\').claude\\hooks\\codex-hook.cmd" ' + script,
        'cmd /d /c "$((git rev-parse --show-cdup) -replace \'/\',\'\\\').claude\\hooks\\codex-hook.cmd" ' + script + '; exit $LASTEXITCODE',
    }


def handler_scripts(handler):
    """這一個 handler 可確認由骨架擁有哪些腳本。

    `commandWindows` 也要看（2026-11-02）：Codex 的 Windows 接線把腳本名寫在那一欄，
    只看 `command` 的話「只有 Windows 命令」的 handler 會被當成專案自己的，於是骨架
    永遠不更新它，而落後的接線沒有任何徵兆。
    """
    if not isinstance(handler, dict):
        return frozenset()
    if handler.get('type') != 'command':
        return frozenset()
    commands = [handler[k] for k in ('command', 'commandWindows') if k in handler]
    for script in OWNED_SCRIPTS:
        if commands and all(isinstance(cmd, str) and cmd in known_hook_commands(script)
                            for cmd in commands):
            return frozenset((script,))
    return frozenset()


def scripts_in(group):
    """這一組 hook 裡可確認的骨架 handler；僅提到檔名不代表所有權。"""
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
    # 缺 matcher 的預設是全事件，不能當成「沒有設定所以可直接補」（R02）。
    # 其餘組層欄位也保守比較；同組自訂 handler 的語意不得隨骨架升級改變。
    clash = sorted(k for k in set(meta_now) | set(meta_auth)
                   if meta_now.get(k) != meta_auth.get(k))
    if foreign and clash:
        return None, (
            '%s 的「%s」那一組裡有專案自己的 handler（%s），而權威版要改這一組的 %s'
            '（%s → %s）——改下去會連專案那個 handler 的觸發條件一起換掉，不敢猜。'
            '請把專案自己的 handler 搬到另一組，或人工比對'
            % (event, '、'.join(sorted(key)),
               '、'.join(str(h.get('command', h))[:40] for h in foreign),
               '、'.join(clash),
               '、'.join(str(meta_now.get(k, '<未設定>')) for k in clash),
               '、'.join(str(meta_auth.get(k, '<未設定>')) for k in clash)))
    merged = dict(meta_now)
    merged.update(meta_auth)
    merged['hooks'] = ([copy.deepcopy(h) for h in auth_own]
                       + [copy.deepcopy(h) for h in foreign])
    return merged, None


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

    # 僅提到腳本名、同名客製腳本或複合命令均不自動認領，也不另補可能重複的 hook。
    # 回 conflict 保持整份零寫入，讓人明確決定如何拆開（R01）。
    for event, groups in c.get('hooks', {}).items():
        if not isinstance(groups, list):
            return None, None, event + ' 的分組不是陣列，不敢動'
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get('hooks', []), list):
                return None, None, event + ' 的 hook 分組格式不合法，不敢動'
            for handler in group.get('hooks', []):
                if not isinstance(handler, dict):
                    return None, None, event + ' 的 handler 不是物件，不敢動'
                mentions = any(s in str(handler.get(k, '')) for s in OWNED_SCRIPTS
                               for k in ('command', 'commandWindows'))
                if mentions and not handler_scripts(handler):
                    return None, None, event + ' 有提到骨架腳本但無法確認所有權的命令，請人工比對；未改任何接線'

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


def shared_block(text):
    """回傳 (起點, 終點) 或 None（沒有標記）；標記不成對、重複或順序反了就丟 ValueError。

    起點是開始標記那一行的行首，終點是結束標記那一行的行尾（不含換行）。
    """
    starts, ends = text.count(SHARED_START), text.count(SHARED_END)
    if starts == 0 and ends == 0:
        return None
    if starts != 1 or ends != 1:
        raise ValueError('共用制度開始標記 %d 個、結束標記 %d 個，各要剛好 1 個' % (starts, ends))
    a = text.rfind('\n', 0, text.index(SHARED_START)) + 1
    b = text.index(SHARED_END) + len(SHARED_END)
    if b <= a:
        raise ValueError('共用制度結束標記在開始標記前面')
    return a, b


def merge_shared_section(authority, current):
    """AGENTS.md 的共用制度：回傳 (新內容或 None, 說明, 錯誤)。標記外原樣保留。"""
    try:
        span = shared_block(authority)
    except ValueError as e:
        return None, None, '權威版 ' + str(e)
    if span is None:
        return None, None, '權威版 AGENTS.md 沒有共用制度標記'
    block = authority[span[0]:span[1]]
    if '{{' in block:
        return None, None, '權威版共用制度裡有佔位符，不能原樣發出去'
    try:
        mine = shared_block(current)
    except ValueError as e:
        return None, None, str(e) + '；先人工修好標記再同步'
    if mine is not None:
        if current[mine[0]:mine[1]] == block:
            return None, None, None
        return current[:mine[0]] + block + current[mine[1]:], '換成權威版共用制度，標記外原樣保留', None
    lines = current.split('\n')
    at = next((k for k, l in enumerate(lines) if l.startswith('## ')), None)
    if at is None:
        tail = '' if current.endswith('\n') else '\n'
        return current + tail + '\n' + block + '\n', '補上共用制度（檔尾；找不到「## 」標題）', None
    lines[at:at] = block.split('\n') + ['']
    return '\n'.join(lines), '補上共用制度（插在第一個「## 」標題前）', None


def legacy_handoff_sections(text):
    """共用制度以外、舊版部署包留下的交接段落標題。"""
    span = shared_block(text)
    outside = text if span is None else text[:span[0]] + text[span[1]:]
    return [l.strip() for l in outside.split('\n')
            if any(l.startswith(h) for h in LEGACY_HANDOFF_HEADINGS)]


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
            # 2026-11-03：replace 換的是 inode；新暫存檔不會繼承原檔的 x bit。
            # 複製失敗須在替換前停止，否則 hook 內容升級了卻無法直接執行。
            if path.exists():
                shutil.copymode(path, tmp)
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


def sync_shared_section(project, gen, plan):
    """AGENTS.md 共用制度。排在 skill 之前寫：新 skill 指向這一節，不能先有指標後有內容。"""
    rel = 'AGENTS.md'
    dst = project / rel
    cur = read(dst)
    if cur is None:
        plan.skip(rel, '不存在')
        return
    new, note, err = merge_shared_section(read(gen / rel) or '', cur)
    if err:
        plan.fail(rel, err)
        return
    if new is None:
        plan.ok(rel + '（共用制度已是權威版）')
    else:
        plan.update(dst, rel, new, note)
    legacy = legacy_handoff_sections(new if new is not None else cur)
    if legacy:
        plan.msgs.append('  MIGRATE AGENTS.md：標記外還有舊交接段落 %s，可能跟共用制度重疊或矛盾；'
                         '同步不刪，要人工比對' % '、'.join('「%s」' % h for h in legacy))


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
        # 2026-11-17（v3 Q41）起不再部署這一份；已部署的舊實例不改寫也不刪，只提示人工遷移。
        if protocol is not None:
            plan.msgs.append('  MIGRATE docs/ai-notes/handover-protocol.md：已不在部署包（v3 Q41），不改寫也不刪；'
                             '專案 override 搬進 AGENTS.md 鐵律後由使用者決定刪不刪，程序細節以新 skill 核心為準')
        # 2026-11-17：本專案明確不支援 Gemini，部署包不再產出 GEMINI.md；已部署的那一份是
        # 專案自己的檔（原本就是 seed），不改寫也不刪，只提示。
        if (project / 'GEMINI.md').exists():
            plan.msgs.append('  MIGRATE GEMINI.md：已不在部署包（本專案不支援 Gemini），不改寫也不刪；刪不刪由使用者決定')
        sync_shared_section(project, gen, plan)

    for rel in WHOLE:
        if codex_only and rel != CODEX_LAUNCHER:
            continue
        dst, src = project / rel, gen / rel
        cur = read(dst)
        if cur is None:
            # 模式檔是 2026-11-10 才有的：專案有入口就補上，不能因為「原本沒有」而跳過，
            # 否則新入口會指向五個不存在的檔。
            adds_part = rel in SKILL_PARTS and (project / SKILL_ENTRY).is_file()
            adds_launcher = rel == CODEX_LAUNCHER and (project / CODEX_WIRING).exists()
            if not (adds_part or adds_launcher):
                plan.skip(rel, '這個專案沒有這個檔')
                continue
        new = read(src)
        if cur == new:
            plan.ok(rel)
        else:
            plan.update(dst, rel, new)

    if not codex_only and (project / SKILL_DIR).is_dir():
        known = {pathlib.PurePosixPath(rel).name for rel in SKILL_PARTS + (SKILL_ENTRY,)}
        for extra in sorted(p.name for p in (project / SKILL_DIR).iterdir()
                            if p.name not in known and not p.name.endswith('.sync-tmp')):
            plan.msgs.append('  EXTRA  %s%s（骨架不認得的檔，同步不會動它；確認是不是舊版留下或專案就地加的）'
                             % (SKILL_DIR, extra))

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


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:], KIT, sys.modules[__name__]))
