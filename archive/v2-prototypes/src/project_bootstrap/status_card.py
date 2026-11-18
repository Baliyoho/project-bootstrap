"""F22／F23 prototype: a short read-only status card for a handoff repo (P1 slice 4).

Efficiency plan section 4.2: one command that gathers the Git root, branch,
upstream, dirty files, ahead／behind, remote SHA, the local and remote "工作中"
marker and the last recorded verification, and prints a short card. Normal
output is a few lines; anything abnormal lists the reason and where the
procedure says to go next.

It changes nothing except remote-tracking refs when it fetches, and it says
whether that fetch worked. It never stashes, rebases, merges, clears a marker,
commits or pushes, and it does not guess that another session has ended.
It is a prototype: the current procedure (handoff skill A1–A5) is unchanged
and still has to be followed; this card does not replace it.

Usage, from the repo root:  PYTHONPATH=src python3 -X utf8 -m project_bootstrap.status_card [--no-fetch] [REPO]
"""
import argparse
from pathlib import Path
import subprocess
import sys

from project_bootstrap.gitclaim import IDLE, owner_field, owner_parts

MARKER_FILE = 'HANDOFF.md'
EVIDENCE_HEAD = '## 服務查證與期望快照'


def _git(repo, *args, timeout=60):
    try:
        result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.decode('utf-8', 'replace').strip()


def _marker(text):
    if text is None:
        return {'state': 'missing-file'}
    value = owner_field(text)
    if value is None:
        return {'state': 'unreadable'}
    if value == IDLE:
        return {'state': 'idle', 'value': value}
    parts = owner_parts(value)
    return {'state': 'busy' if parts else 'malformed', 'value': value,
            'parts': parts}


def _last_evidence(text):
    if text is None or EVIDENCE_HEAD not in text:
        return None
    section = text.split(EVIDENCE_HEAD, 1)[1].split('\n## ', 1)[0]
    rows = [line[2:].strip() for line in section.split('\n') if line.startswith('- ')]
    return rows[0] if rows else None


def card(repo, fetch=True):
    """Gather the facts; never decide on the user's behalf."""
    repo = Path(repo)
    facts = {'repo': None, 'problems': []}
    root = _git(repo, 'rev-parse', '--show-toplevel')
    if root is None:
        facts['problems'].append('not-a-git-repo')
        return facts
    root = Path(root)
    facts['repo'] = str(root)
    facts['branch'] = _git(root, 'symbolic-ref', '--quiet', '--short', 'HEAD')
    if facts['branch'] is None:
        facts['problems'].append('detached-head')
    upstream = _git(root, 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{upstream}')
    facts['upstream'] = upstream
    if fetch:
        remote = upstream.split('/', 1)[0] if upstream else 'origin'
        facts['fetch'] = 'ok' if _git(root, 'fetch', '--quiet', remote, timeout=120) is not None else 'failed'
    else:
        facts['fetch'] = 'skipped'
    if facts['fetch'] != 'ok':
        facts['problems'].append('fetch-' + facts['fetch'])
    status = _git(root, 'status', '--porcelain', '--untracked-files=all')
    facts['dirty'] = [] if status is None else [line for line in status.split('\n') if line]
    if status is None:
        facts['problems'].append('status-failed')
    elif facts['dirty']:
        facts['problems'].append('dirty')
    facts['head'] = _git(root, 'rev-parse', 'HEAD')
    local_text = None
    try:
        local_text = (root / MARKER_FILE).read_text(encoding='utf-8')
    except OSError:
        pass
    facts['local_marker'] = _marker(local_text)
    facts['last_evidence'] = _last_evidence(local_text)
    if upstream is None:
        facts['problems'].append('no-upstream')
        facts['remote_marker'] = {'state': 'unknown'}
        return facts
    facts['remote_sha'] = _git(root, 'rev-parse', upstream)
    counts = _git(root, 'rev-list', '--left-right', '--count', 'HEAD...' + upstream)
    if counts is None:
        facts['problems'].append('ahead-behind-unknown')
    else:
        ahead, behind = (int(n) for n in counts.split())
        facts['ahead'], facts['behind'] = ahead, behind
        if ahead and behind:
            facts['problems'].append('diverged')
        elif ahead:
            facts['problems'].append('ahead')
        elif behind:
            facts['problems'].append('behind')
    facts['remote_marker'] = _marker(_git(root, 'show', upstream + ':' + MARKER_FILE))
    state = facts['remote_marker']['state']
    if state == 'busy':
        facts['problems'].append('remote-busy')
    elif state != 'idle':
        facts['problems'].append('remote-marker-' + state)
    return facts


NEXT = {
    'not-a-git-repo': '不在 Git repo 裡；handoff 程序不適用或路徑給錯',
    'detached-head': 'HEAD 不在分支上；讀 HANDOFF 的待續分支，切換前先停下問',
    'fetch-failed': 'fetch 失敗：遠端狀態未知，照 mode-a-stop.md 的 A1 停下回報',
    'fetch-skipped': '沒有 fetch（--no-fetch）：遠端欄位是上次 fetch 的快照，不能當 A1 通過',
    'status-failed': 'git status 失敗：工作樹狀態未知',
    'dirty': '工作樹有未提交變更：來源不明就停下問，不要 stash',
    'no-upstream': '沒有 upstream：照 mode-a-stop.md 停下問',
    'ahead-behind-unknown': '算不出與 upstream 的領先／落後',
    'diverged': '與 upstream 分岔：停下問，不要 rebase 或 force',
    'ahead': '本機領先 upstream（接棒時 ahead-only 要停下問）',
    'behind': '本機落後 upstream：照 A1 判讀表 fast-forward',
    'remote-busy': 'origin 的「工作中」不是空閒：照 A2.5 判斷是否本 session，不是就停下問',
}


def render(facts):
    if facts.get('repo') is None:
        return '狀態卡：' + NEXT['not-a-git-repo']
    ahead = facts.get('ahead', '?')
    behind = facts.get('behind', '?')
    lines = [
        '狀態卡（只讀；只有 fetch 會更新遠端追蹤分支）',
        '分支：%s → %s；fetch：%s' % (facts.get('branch') or '（detached）', facts.get('upstream') or '（無 upstream）',
                                   facts['fetch']),
        '本機 %s／遠端 %s；領先 %s、落後 %s；未提交 %d 個' % (
            (facts.get('head') or '?')[:7], (facts.get('remote_sha') or '?')[:7], ahead, behind,
            len(facts.get('dirty', []))),
        '工作中：本機 %s；origin %s' % (
            facts['local_marker'].get('value', facts['local_marker']['state']),
            facts['remote_marker'].get('value', facts['remote_marker']['state'])),
    ]
    if facts.get('last_evidence'):
        evidence = facts['last_evidence']
        lines.append('HANDOFF 記的最近驗證（上一輪紀錄，不是本輪結果）：' +
                     (evidence if len(evidence) <= 120 else evidence[:119] + '…'))
    if facts['problems']:
        lines.append('不是全綠：')
        lines += ['- ' + NEXT.get(code, code) for code in facts['problems']]
    else:
        lines.append('全綠：與 upstream 一致、工作樹乾淨、origin 的工作中是空閒。這只是快照，A1–A5 照走。')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Read-only handoff status card (prototype).')
    parser.add_argument('repo', nargs='?', default='.')
    parser.add_argument('--no-fetch', action='store_true', help='do not fetch; remote fields may be stale')
    args = parser.parse_args(argv)
    facts = card(args.repo, fetch=not args.no_fetch)
    print(render(facts))
    return 0 if not facts['problems'] else 1


if __name__ == '__main__':
    sys.exit(main())
