"""M2 prototype for F1／F2／F5: project state as data, HANDOFF sections as a view.

The state names the goal (requirement IDs, the decision version it was set
against, the human decision source), tasks with status and evidence, the
ordered next steps, and risks typed as broken／unknown／risk／healthy.
``check`` returns findings; ``render`` writes the HANDOFF sections from the
same data, showing every finding next to the item it concerns, so the view
cannot list a done task as next or show an untested area as healthy.

Non-empty is not correct: a goal that cites an unknown ID or an older
decision version is unverified, not merely incomplete. Evidence paths must
exist, but existing evidence is not proof the claim is true (F3／F20 own that).
Stdlib only; no schema library has been chosen yet.
"""
from pathlib import Path
import re

from experiments.v2.registry import requirement_ids

TASK_STATES = {'done', 'open', 'blocked'}
RISK_KINDS = {'broken', 'unknown', 'risk', 'healthy'}


def decision_version(text):
    match = re.search(r'^> 決策版本：(\d+)。', text, re.MULTILINE)
    return int(match.group(1)) if match else None


def _evidence_findings(item, root, where):
    found = []
    evidence = item.get('evidence', [])
    if not isinstance(evidence, list):
        return [(where, 'evidence-invalid')]
    for path in evidence:
        if (not isinstance(path, str) or not path or path.startswith('/')
                or '..' in path.split('/')):
            found.append((where, 'evidence-invalid'))
        elif not (Path(root) / path).is_file():
            found.append((where, 'evidence-missing'))
    return found


def check(state, decision_text, root):
    """Findings as (location, code); an empty list is the only consistent state."""
    findings = []
    goal = state.get('goal')
    if not isinstance(goal, dict) or not str(goal.get('text', '')).strip():
        findings.append(('goal', 'goal-missing'))
    else:
        known = set(requirement_ids(decision_text))
        ids = goal.get('requirement_ids')
        if not isinstance(ids, list) or not ids:
            findings.append(('goal', 'goal-without-ids'))
        elif any(i not in known for i in ids):
            findings.append(('goal', 'goal-unknown-id'))
        current = decision_version(decision_text)
        if current is None:
            findings.append(('goal', 'decision-version-unreadable'))
        elif goal.get('decision_version') != current:
            findings.append(('goal', 'goal-stale-version'))
        source = goal.get('source')
        if not isinstance(source, str) or not source or not (Path(root) / source).is_file():
            findings.append(('goal', 'goal-source-missing'))

    tasks, seen = {}, set()
    for task in state.get('tasks', []):
        tid = task.get('id') if isinstance(task, dict) else None
        if not isinstance(tid, str) or not tid or tid in seen:
            findings.append((str(tid), 'duplicate-or-missing-id'))
            continue
        seen.add(tid)
        tasks[tid] = task
        if task.get('status') not in TASK_STATES:
            findings.append((tid, 'task-status-invalid'))
        findings += _evidence_findings(task, root, tid)
        if task.get('status') == 'done' and not task.get('evidence'):
            findings.append((tid, 'done-without-evidence'))
        if task.get('status') == 'blocked' and not str(task.get('blocked_on', '')).strip():
            findings.append((tid, 'blocked-without-reason'))
    for tid in state.get('next', []):
        if tid not in tasks:
            findings.append((str(tid), 'next-unknown-task'))
        elif tasks[tid].get('status') == 'done':
            findings.append((tid, 'done-listed-as-next'))
    if len(set(state.get('next', []))) != len(state.get('next', [])):
        findings.append(('next', 'next-duplicate'))
    open_ids = {tid for tid, task in tasks.items() if task.get('status') == 'open'}
    for tid in sorted(open_ids - set(state.get('next', []))):
        findings.append((tid, 'open-not-scheduled'))

    for risk in state.get('risks', []):
        rid = risk.get('id') if isinstance(risk, dict) else None
        if not isinstance(rid, str) or not rid or rid in seen:
            findings.append((str(rid), 'duplicate-or-missing-id'))
            continue
        seen.add(rid)
        if risk.get('kind') not in RISK_KINDS:
            findings.append((rid, 'risk-kind-invalid'))
        findings += _evidence_findings(risk, root, rid)
        if risk.get('kind') in ('healthy', 'broken') and not risk.get('evidence'):
            findings.append((rid, risk['kind'] + '-without-evidence'))
    return findings


LABELS = {'broken': '已知壞掉', 'unknown': '未知', 'risk': '風險', 'healthy': '已知正常'}


def shown_kind(risk, codes):
    """A claim of known state without evidence is shown as unknown."""
    if risk.get('kind') in ('healthy', 'broken') and (
            f"{risk['kind']}-without-evidence" in codes or 'evidence-missing' in codes):
        return 'unknown'
    return risk.get('kind')


def render(state, findings):
    by_where = {}
    for where, code in findings:
        by_where.setdefault(where, []).append(code)

    def note(where):
        codes = by_where.get(where)
        return f'（⚠ {"、".join(codes)}）' if codes else ''

    goal = state.get('goal') or {}
    lines = ['## 任務目標', '']
    if by_where.get('goal') and ('goal-missing' in by_where['goal']):
        lines.append('未驗證：沒有目標' + note('goal'))
    else:
        status = '未驗證' if by_where.get('goal') else '已核對'
        lines.append(f"{goal.get('text', '').strip()}（{status}："
                     f"{'、'.join(goal.get('requirement_ids') or [])}；決策版本 "
                     f"{goal.get('decision_version')}；來源 {goal.get('source')}）{note('goal')}")
    tasks = {}
    for task in state.get('tasks', []):
        # First entry wins, as in check(); a later duplicate never hides it.
        if isinstance(task, dict) and 'id' in task:
            tasks.setdefault(task['id'], task)
    lines += ['', '## 已完成', '']
    lines += [f"- {t.get('title', tid)}{note(tid)}" for tid, t in tasks.items()
              if t.get('status') == 'done']
    lines += ['', '## 未完成／下一步', '']
    # Done tasks are never listed here, whatever ``next`` says.
    number = 0
    for tid in state.get('next', []):
        task = tasks.get(tid)
        if task is None or task.get('status') == 'done':
            continue
        number += 1
        blocked = f"（卡在：{task.get('blocked_on')}）" if task.get('status') == 'blocked' else ''
        lines.append(f"{number}. {task.get('title', tid)}{blocked}{note(tid)}")
    unscheduled = [tid for tid, task in tasks.items() if task.get('status') != 'done'
                   and tid not in state.get('next', [])]
    if unscheduled:
        lines += ['', '未排入下一步：']
        lines += [f"- {tasks[tid].get('title', tid)}{note(tid)}" for tid in unscheduled]
    lines += ['', '## 地雷與注意事項', '']
    for risk in state.get('risks', []):
        if not isinstance(risk, dict) or 'id' not in risk:
            continue
        kind = shown_kind(risk, by_where.get(risk['id'], []))
        lines.append(f"- [{LABELS.get(kind, '未知')}] {risk.get('text', '')}{note(risk['id'])}")
    # Findings not attached to a shown item (unknown next IDs, bad IDs) still appear.
    shown = set(tasks) | {'goal'} | {r.get('id') for r in state.get('risks', [])
                                     if isinstance(r, dict)}
    other = [f'{where}:{code}' for where, code in findings if where not in shown]
    if other:
        lines += ['', '⚠ 其他狀態問題：' + '、'.join(other)]
    return '\n'.join(lines) + '\n'
