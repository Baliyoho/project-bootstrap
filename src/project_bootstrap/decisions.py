"""M2 records for F44 (pending decisions) and F34 (declared exceptions).

F44: a question waiting for the user is a registered decision with a
question, affected IDs and options, and it is listed where the next reader
looks. The AI may settle a decision only inside a delegation the user granted
(with a recorded source), and then must record why; a decision inside such a
delegation must not be parked as "waiting for the user" either. A blocked task
that says it waits for a decision must point at a registered, still pending
one, so the question cannot hide in a task field or in chat.

F34: a declared exception names what is exempted, who authorised it and where,
its scope, reason and recheck condition, and is always printed. Being declared
is not passing: the listing says so, and a due recheck is flagged.
"""
import datetime


def _text(value):
    return isinstance(value, str) and value.strip() != ''


def _ids(value):
    return isinstance(value, list) and value and all(_text(item) for item in value)


def _covering(decision, valid):
    affects = set(decision.get('affects'))
    return [d for d in valid if affects <= set(d['scope'])]


def check_decisions(decisions, delegations, tasks=()):
    findings, ids, valid = [], set(), []
    for delegation in delegations:
        if (delegation.get('granted_by') == 'user' and _text(delegation.get('source'))
                and _ids(delegation.get('scope'))):
            valid.append(delegation)
        else:
            findings.append((str(delegation.get('id')), 'delegation-invalid'))
    for decision in decisions:
        did = decision.get('id')
        if not _text(did) or did in ids:
            findings.append((str(did), 'duplicate-or-missing-id'))
            continue
        ids.add(did)
        if not (_text(decision.get('question')) and _ids(decision.get('affects'))):
            findings.append((did, 'decision-incomplete'))
            continue
        covered = _covering(decision, valid)
        status = decision.get('status')
        if status == 'pending':
            if not _ids(decision.get('options')):
                findings.append((did, 'pending-without-options'))
            if covered:
                findings.append((did, 'delegated-but-waiting-for-user'))
        elif status == 'decided':
            by = decision.get('decided_by')
            if by == 'ai':
                if not covered:
                    findings.append((did, 'ai-decided-without-delegation'))
                elif not _text(decision.get('rationale')):
                    findings.append((did, 'delegated-without-rationale'))
            elif by != 'user':
                findings.append((did, 'decider-unknown'))
            if not _text(decision.get('source')):
                findings.append((did, 'decided-without-source'))
        else:
            findings.append((did, 'decision-status-invalid'))
    pending = {d['id'] for d in decisions if isinstance(d, dict) and d.get('status') == 'pending'}
    for task in tasks:
        waits = task.get('waits_for_decision')
        if waits is None:
            continue
        if waits not in ids:
            findings.append((str(task.get('id')), 'waits-for-unregistered-decision'))
        elif waits not in pending:
            findings.append((str(task.get('id')), 'waits-for-settled-decision'))
    return findings


def check_exceptions(exceptions, today):
    findings, ids = [], set()
    for item in exceptions:
        eid = item.get('id')
        if not _text(eid) or eid in ids:
            findings.append((str(eid), 'duplicate-or-missing-id'))
            continue
        ids.add(eid)
        for key in ('what', 'authorized_by', 'source', 'scope', 'reason'):
            if not _text(item.get(key)):
                findings.append((eid, 'exception-missing-' + key))
        recheck = item.get('recheck')
        if not isinstance(recheck, dict) or not (_text(recheck.get('when'))
                                                  or _text(recheck.get('until'))):
            findings.append((eid, 'exception-missing-recheck'))
        elif _text(recheck.get('until')):
            try:
                due = datetime.date.fromisoformat(recheck['until'])
            except ValueError:
                findings.append((eid, 'exception-recheck-invalid'))
            else:
                if due <= today:
                    findings.append((eid, 'exception-recheck-due'))
    return findings


def render(decisions, exceptions, findings):
    notes = {}
    for where, code in findings:
        notes.setdefault(where, []).append(code)

    def note(where):
        return f'（⚠ {"、".join(notes[where])}）' if where in notes else ''

    lines = ['## 懸置事項（AI 勿自行處理）', '']
    pending = [d for d in decisions if isinstance(d, dict) and d.get('status') == 'pending']
    if not pending:
        lines.append('無登記中的待決事項。')
    for d in pending:
        lines.append(f"- {d.get('id')}：{d.get('question')}（影響 {'、'.join(d.get('affects') or [])}；"
                     f"選項 {' ／ '.join(d.get('options') or [])}）{note(d.get('id'))}")
    lines += ['', '## 已宣告例外（宣告不等於通過）', '']
    if not exceptions:
        lines.append('無。')
    for e in exceptions:
        recheck = e.get('recheck') or {}
        when = recheck.get('until') or recheck.get('when')
        lines.append(f"- {e.get('id')}：{e.get('what')}；授權 {e.get('authorized_by')}（{e.get('source')}）；"
                     f"範圍 {e.get('scope')}；理由 {e.get('reason')}；重檢 {when}{note(e.get('id'))}")
    return '\n'.join(lines) + '\n'
