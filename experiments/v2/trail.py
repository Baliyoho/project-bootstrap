"""M2 trail records for F6 (why a rule exists), F7 (routes considered and
rejected) and F8 (the long-term roadmap, not only this round).

Decisions are MADR-like records: id, title, status (accepted, superseded or
rejected), date, the baseline they were taken against, rationale, and the
alternatives considered with each one's outcome and reason. A rule names the
decision that adopted it, so ``why`` can walk from the rule to its rationale
and, if the decision was later replaced, on to the current one while keeping
the old one in view. ``compare`` checks a new snapshot against an older one:
a decision or alternative that disappears is reported, because rewriting the
record so a route looks never considered is exactly what F7 forbids.

The roadmap holds milestones with a goal and status; tasks cite a milestone,
so after a HANDOFF is cleaned up the direction is still found in one place.

These are checks on records the caller keeps; they do not prove a record is
true or complete, and nothing here is wired into the current procedure.
"""
import datetime

STATUSES = {'accepted', 'superseded', 'rejected'}


def _text(value):
    return isinstance(value, str) and value.strip() != ''


def _date(value):
    try:
        datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return True


def _index(items, findings, kind):
    seen = {}
    for item in items:
        iid = item.get('id') if isinstance(item, dict) else None
        if not _text(iid) or iid in seen:
            findings.append((str(iid), kind + '-duplicate-or-missing-id'))
            continue
        seen[iid] = item
    return seen


def check_decisions(decisions):
    findings = []
    by_id = _index(decisions, findings, 'decision')
    for did, d in by_id.items():
        if d.get('status') not in STATUSES:
            findings.append((did, 'decision-status-invalid'))
        for key in ('title', 'rationale', 'baseline'):
            if not _text(d.get(key)):
                findings.append((did, 'decision-missing-' + key))
        if not _date(d.get('date')):
            findings.append((did, 'decision-date-invalid'))
        for alt in d.get('alternatives') or []:
            if not (_text(alt.get('option')) and alt.get('outcome') in ('rejected', 'deferred')
                    and _text(alt.get('reason'))):
                findings.append((did, 'alternative-incomplete'))
        newer = d.get('superseded_by')
        if d.get('status') == 'superseded':
            if newer not in by_id:
                findings.append((did, 'superseded-without-successor'))
            elif by_id[newer].get('supersedes') != did:
                findings.append((did, 'supersession-not-mutual'))
        elif newer is not None:
            findings.append((did, 'successor-on-unsuperseded'))
        older = d.get('supersedes')
        if older is not None and (older not in by_id or by_id[older].get('superseded_by') != did):
            findings.append((did, 'supersedes-unknown-or-not-mutual'))
    return findings, by_id


def check_rules(rules, by_id):
    findings = []
    for rule in rules:
        rid = rule.get('id')
        did = rule.get('decision')
        if did not in by_id:
            findings.append((str(rid), 'rule-without-decision'))
        elif by_id[did].get('status') == 'rejected':
            findings.append((str(rid), 'rule-cites-rejected'))
        elif by_id[did].get('status') == 'superseded':
            findings.append((str(rid), 'rule-cites-superseded'))
    return findings


def why(rule_id, rules, by_id):
    """The rule's decision chain, oldest cited first, ending at the current one."""
    rule = next((r for r in rules if r.get('id') == rule_id), None)
    if rule is None or rule.get('decision') not in by_id:
        return None
    chain, did, seen = [], rule['decision'], set()
    while did in by_id and did not in seen:
        seen.add(did)
        d = by_id[did]
        chain.append({'id': did, 'status': d.get('status'), 'date': d.get('date'),
                      'baseline': d.get('baseline'), 'rationale': d.get('rationale')})
        did = d.get('superseded_by')
    return chain


def rejected_routes(by_id):
    """Every route that was considered and not taken, with where it was decided."""
    routes = []
    for did, d in by_id.items():
        if d.get('status') == 'rejected':
            routes.append({'decision': did, 'option': d.get('title'),
                           'reason': d.get('rationale'), 'outcome': 'rejected'})
        for alt in d.get('alternatives') or []:
            routes.append({'decision': did, 'option': alt.get('option'),
                           'reason': alt.get('reason'), 'outcome': alt.get('outcome')})
    return routes


def compare(old_decisions, new_decisions):
    """Records present before must still be present and keep their rationale: a
    changed reason belongs in a new, superseding decision, not an edit."""
    findings = []
    new = {d.get('id'): d for d in new_decisions if isinstance(d, dict)}
    for d in old_decisions:
        did = d.get('id')
        if did not in new:
            findings.append((str(did), 'decision-erased'))
            continue
        kept = {a.get('option') for a in new[did].get('alternatives') or []}
        for alt in d.get('alternatives') or []:
            if alt.get('option') not in kept:
                findings.append((str(did), 'alternative-erased'))
        if d.get('rationale') != new[did].get('rationale'):
            findings.append((str(did), 'rationale-rewritten'))
    return findings


def check_roadmap(milestones, tasks):
    findings = []
    by_id = _index(milestones, findings, 'milestone')
    if not any(m.get('status') in ('active', 'planned') for m in by_id.values()):
        findings.append(('roadmap', 'no-open-milestone'))
    for mid, m in by_id.items():
        if not _text(m.get('goal')):
            findings.append((mid, 'milestone-missing-goal'))
        if m.get('status') not in ('planned', 'active', 'done', 'dropped'):
            findings.append((mid, 'milestone-status-invalid'))
        if m.get('status') == 'dropped' and not _text(m.get('reason')):
            findings.append((mid, 'dropped-without-reason'))
    for task in tasks:
        tid = str(task.get('id'))
        mid = task.get('milestone')
        if mid not in by_id:
            findings.append((tid, 'task-without-milestone'))
        elif task.get('status') != 'done' and by_id[mid].get('status') in ('done', 'dropped'):
            findings.append((tid, 'open-task-on-closed-milestone'))
    return findings
