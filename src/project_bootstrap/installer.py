"""bootstrap.py 的安裝與更新邏輯（需求決策書 v3 Q49）。

這一份是原始碼，不是給人直接跑的。`tools/build_kit.py` 把它、`src/kit/` 的範本與
`owners.json`，以及 `tools/sync_project.py` 的合併函式（原樣搬過去，不另寫一套）組成
單一檔 `bootstrap.py`。測試直接 import 本模組，用 `load_kit()` 從 `src/kit/` 讀範本。

只用標準函式庫。不碰網路、不推送、不建 GitHub repo；這些留給安裝後接手的 agent。
"""
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
    tasks = ['補寫 `ARCHITECT.md` 的「專案本體」、`README.md` 與 `docs/ai-notes/roadmap.md`，照實寫；'
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
