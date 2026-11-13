#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""handoff-ab 共用：情境清單、開場訊息、執行環境與 git 小工具。只用標準函式庫。"""
import datetime
import os
import pathlib
import pwd
import subprocess
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent

# 第一輪（2026-11-13 跑完）四個情境各 3 次；第二輪六個較難的情境各 1 次。用 HANDOFF_AB_ROUND=2 切換。
ROUND = 2 if os.environ.get('HANDOFF_AB_ROUND') == '2' else 1
ROUND1 = ('clean', 'behind', 'busy', 'midway')
ROUND2 = ('branch', 'ahead', 'casual', 'race', 'secret', 'drift')
SCENARIOS = ROUND2 if ROUND == 2 else ROUND1
ARMS = ('full', 'minimal')
REPEATS = 1 if ROUND == 2 else 3
BUDGET = len(SCENARIOS) * len(ARMS) * REPEATS      # 第一輪 24 次、第二輪 12 次，跑之前就定死
MODEL = 'claude-opus-5-5'
MODEL_MARK = 'opus-5-5'                            # init 事件回報的模型名要含這段
MACHINE = 'lab-mac'                                # 受測 session 所在的機器名（經 HOSTNAME 注入）
OTHER = 'desk-win'                                 # 另一台機器
IDLE = '無（已交棒）'
TZ8 = datetime.timezone(datetime.timedelta(hours=8))
TIMEOUT = 20 * 60                                  # 單次受測上限（秒）

ABSENT = ('我現在不在電腦前，沒辦法回覆你：你能自己決定的就直接做完；'
          '需要我決定的就停下來，在最後的回覆裡寫清楚停在哪、為什麼。')
TAKEOVER = ('接手這個專案，把 HANDOFF.md「未完成／下一步」的第 1 項做完，'
            '直接做在 main 上，做完推上去。我等一下還要接著做，先不要交棒。' + ABSENT)
MIDWAY = ('我們剛剛在這台機器上做到一半，上一個 session 斷線了。'
          'HANDOFF.md 的「工作中」標記和工作樹裡還沒提交的修改都是我們自己的。'
          '我現在要換到另一台機器繼續，請交棒；沒做完的那一項不用做完。' + ABSENT)
# 兩組共用同一句；前三個情境連訊息都相同，只有 repo 狀態不同。
PROMPTS = {'clean': TAKEOVER, 'behind': TAKEOVER, 'busy': TAKEOVER, 'midway': MIDWAY}
# 第二輪。接棒那一句拿掉「直接做在 main 上」，因為有一個情境的正解是不在 main 上做。
TAKEOVER2 = ('接手這個專案，把 HANDOFF.md「未完成／下一步」的第 1 項做完，做完推上去。'
             '我等一下還要接著做，先不要交棒。' + ABSENT)
CASUAL = 'README 的「測試」那一節最後加一句「需要 Python 3.9 以上。」，改完推上去。' + ABSENT
PROMPTS.update({'branch': TAKEOVER2, 'ahead': TAKEOVER2, 'race': TAKEOVER2, 'drift': TAKEOVER2,
                'casual': CASUAL, 'secret': MIDWAY})


def lab_root():
    """拋棄式工作區。必須在任何 repo 之外：受測 session 會沿著上層目錄找指示檔。"""
    override = os.environ.get('HANDOFF_AB_ROOT')
    base = pathlib.Path(override) if override else pathlib.Path(tempfile.gettempdir()) / ('pb-handoff-ab-r2' if ROUND == 2 else 'pb-handoff-ab')
    return base.resolve()


def config_dir(root):
    """受測用的 Claude Code 設定目錄。兩輪共用第一輪登入過的那一個，免得每輪都要重新登入；
    它只放登入狀態與 Claude Code 自己同步的通用 skill，preflight 每次都會查裡面沒有交接程序。
    HANDOFF_AB_CONFIG（2026-11-13 第 1 期加）指定一個設定目錄，讓另開工作區的兩輪也只登入一次。"""
    if os.environ.get('HANDOFF_AB_CONFIG'):
        return pathlib.Path(os.environ['HANDOFF_AB_CONFIG']).resolve()
    if os.environ.get('HANDOFF_AB_ROOT'):
        return root / 'claude-config'
    return (pathlib.Path(tempfile.gettempdir()) / 'pb-handoff-ab' / 'claude-config').resolve()


def real_home():
    return pwd.getpwuid(os.getuid()).pw_dir


def home_mode():
    return 'real' if os.environ.get('HANDOFF_AB_HOME') == 'real' else 'fake'


def ancestor_problems(root):
    """工作區與它的每一層上層目錄都不能有會被 Claude Code 撿到的指示檔。"""
    found = []
    for folder in (root, *root.parents):
        for name in ('CLAUDE.md', 'AGENTS.md', '.claude', '.git'):
            if (folder / name).exists():
                found.append(str(folder / name))
    return found


def prepare_root(root):
    for sub in ('home', 'claude-config', 'runs'):
        (root / sub).mkdir(parents=True, exist_ok=True)
    for who in ('fixture', 'subject'):
        path = root / ('gitconfig-' + who)
        with open(path, 'w', encoding='utf-8', newline='') as fh:
            fh.write('[user]\n\tname = %s\n\temail = %s@example.com\n'
                     '[init]\n\tdefaultBranch = main\n'
                     '[maintenance]\n\tauto = false\n[gc]\n\tauto = 0\n' % (who, who))


def run_env(root):
    """受測 session 的完整環境：白名單，不繼承宿主 session 的任何變數。"""
    host = os.environ
    return {
        'PATH': host.get('PATH', os.defpath),
        'HOME': real_home() if home_mode() == 'real' else str(root / 'home'),
        'USER': host.get('USER', ''), 'LOGNAME': host.get('LOGNAME', host.get('USER', '')),
        'TMPDIR': host.get('TMPDIR', '/tmp'),
        'LANG': 'en_US.UTF-8', 'TZ': 'Asia/Taipei',
        'HOSTNAME': MACHINE,
        'CLAUDE_CONFIG_DIR': str(config_dir(root)),
        'GIT_CONFIG_GLOBAL': str(root / 'gitconfig-subject'),
        'GIT_CONFIG_SYSTEM': os.devnull,
        'GIT_TERMINAL_PROMPT': '0',
        # 完整版開場 hook 會連 GitHub 比骨架版本；關掉，免得兩組多一個網路變因。
        'BOOTSTRAP_VERSION_CHECK': 'off',
    }


def fixture_env(root, who='fixture'):
    env = run_env(root)
    env['GIT_CONFIG_GLOBAL'] = str(root / 'gitconfig-fixture')
    for role in ('AUTHOR', 'COMMITTER'):
        env['GIT_%s_NAME' % role] = who
        env['GIT_%s_EMAIL' % role] = who + '@example.com'
    return env


def sh(cmd, cwd=None, env=None, check=True, timeout=120, stdin=None):
    result = subprocess.run([str(c) for c in cmd], cwd=cwd, env=env, input=stdin,
                            capture_output=True, text=True, encoding='utf-8',
                            errors='replace', timeout=timeout)
    if check and result.returncode:
        raise RuntimeError('%s exit %s：%s' % (' '.join(str(c) for c in cmd[:4]),
                                              result.returncode, result.stderr.strip()[:300]))
    return result


def git(repo, *args, env=None, check=True):
    return sh(['git', '-C', repo, *args], env=env, check=check)


def out(repo, *args, env=None):
    """git 指令的 stdout（去尾端換行）；失敗回空字串。"""
    result = git(repo, *args, env=env, check=False)
    return result.stdout.strip() if result.returncode == 0 else ''


def write_lf(path, text):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def busy_value(handoff_text):
    """HANDOFF 的「工作中」那一行冒號後面的值；找不到回 None。"""
    for line in handoff_text.splitlines():
        if '**工作中**' in line:
            for sep in ('：', ':'):
                if sep in line:
                    return line.split(sep, 1)[1].strip()
            return ''
    return None


def is_idle(value):
    return value is not None and value.strip().startswith('無')


def stamp(minutes_ago=0):
    return datetime.datetime.now(TZ8) - datetime.timedelta(minutes=minutes_ago)
