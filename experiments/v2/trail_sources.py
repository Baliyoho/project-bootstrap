"""F6／F7／F8 on this repo's own documents, read in place.

The documents stay the single home of each fact; these adapters only lift
records out of them so ``trail`` can check them:

- ``decisions_from_book``: each numbered item of the decision book's section
  7 is an accepted decision, ``理由：`` separates what was decided from why,
  the dated heading gives the date and the ``決策版本`` line the baseline;
- ``routes_from_plan``: the implementation plan's route table (section 3.4)
  is one decision whose recommended row is the choice and whose other rows
  are the alternatives, each with its cost as the reason;
- ``roadmap_from_plan``: the plan's phase table (section 7) gives the
  milestones; their status comes from the caller, because the plan holds
  estimates, not progress;
- ``absences_from_architect``: each bullet of ARCHITECT's "deliberately
  absent" section whose bold lead says something is not installed is an
  accepted decision; the rest of the bullet is its rationale and the last
  date in the bold lead (else the first in the bullet) its date. A bullet
  with no date yields an empty date, which ``check_decisions`` reports.
- ``rules_from_agents``: each "why" link in AGENTS.md is a rule citing the
  AGENTS-reasons.md section it points to; each section is an accepted
  decision dated by the earliest date written in it.
- ``questions_from_book``: each decided item of the decision book's section 6,
  with its indented 採用理由／未選／暫緩 sub-bullets as rationale and alternatives;
- ``nongoals_from_plan``: each non-goal of the efficiency plan's section 3.2 is
  a rejected route, the text after ``理由：`` its reason.

A document whose expected section is missing yields no records, which the
checks then report (a decision without rationale, a roadmap with no open
milestone) instead of passing.
"""
import re


def _section(text, heading):
    match = re.search(r'^(#{2,3}) ' + heading + r'.*$', text, re.MULTILINE)
    if not match:
        return '', None
    level = len(match.group(1))
    rest = text[match.end():]
    end = re.search(r'^#{2,%d} ' % level, rest, re.MULTILINE)
    return (rest[:end.start()] if end else rest), match.group(0)


def _rows(block):
    """Rows of the first table in ``block``, header dropped."""
    rows, started = [], False
    for line in block.splitlines():
        if not line.startswith('|'):
            if started:
                break
            continue
        started = True
        if not re.match(r'^\|[\s|:-]+\|$', line):
            rows.append([cell.strip() for cell in line.strip('|').split('|')])
    return rows[1:]


def decisions_from_book(text):
    body, heading = _section(text, r'7\. ')
    date = re.search(r'(\d{4}-\d{2}-\d{2})', heading or '')
    version = re.search(r'決策版本：(\d+)', text)
    baseline = f'決策書決策版本 {version.group(1)}' if version else ''
    decisions = []
    for number, item in re.findall(r'^(\d+)\. (.+)$', body, re.MULTILINE):
        title, _, rationale = item.partition('理由：')
        decisions.append({'id': f'book-7.{number}', 'title': title.strip(), 'status': 'accepted',
                          'date': date.group(1) if date else '', 'baseline': baseline,
                          'rationale': rationale.strip()})
    return decisions


def routes_from_plan(text, date):
    body, _ = _section(text, r'3\.4 ')
    rows = [r for r in _rows(body) if len(r) == 4]
    chosen = [r for r in rows if r[3].startswith('推薦')]
    if len(chosen) != 1:
        return []
    route, gain, cost, verdict = chosen[0]
    return [{'id': 'plan-3.4', 'title': route, 'status': 'accepted', 'date': date,
             'baseline': '實現規劃第 3.4 節', 'rationale': verdict,
             'alternatives': [{'option': r[0], 'outcome': 'rejected', 'reason': f'{r[2]}；{r[3]}'}
                              for r in rows if r is not chosen[0]]}]


_ABSENT = re.compile(r'沒有|不裝|刻意不')
_DAY = re.compile(r'\d{4}-\d{2}-\d{2}')


def absences_from_architect(text):
    body, _ = _section(text, r'這個 repo 刻意沒有的東西')
    decisions = []
    for item in re.findall(r'^- \*\*(.+)$', body, re.MULTILINE):
        lead, _, rest = item.partition('**')
        if not _ABSENT.search(lead):
            continue
        days = _DAY.findall(lead) or _DAY.findall(rest)[:1]
        decisions.append({'id': f'architect-absent-{len(decisions) + 1}',
                          'title': lead.strip(), 'status': 'accepted',
                          'date': days[-1] if days else '',
                          'baseline': 'ARCHITECT「這個 repo 刻意沒有的東西」',
                          'rationale': rest.strip()})
    return decisions


def roadmap_from_plan(text, status):
    body, _ = _section(text, r'7\. ')
    milestones = []
    for row in _rows(body):
        phase = re.match(r'(P\d)\s', row[0] + ' ')
        if phase and len(row) == 4:
            milestones.append({'id': phase.group(1), 'goal': row[1], 'exit': row[2],
                               'status': status.get(phase.group(1), 'planned')})
    return milestones


_ANCHOR = re.compile(r'^<a id="([a-z0-9-]+)"></a>\n', re.MULTILINE)
_WHY = re.compile(r'\[為什麼\]\(AGENTS-reasons\.md#([a-z0-9-]+)\)')


def rules_from_agents(agents, reasons):
    """AGENTS.md rules and the AGENTS-reasons.md sections their "why" links name.

    Every ``[為什麼](AGENTS-reasons.md#x)`` link in AGENTS is one rule citing
    decision ``reasons#x``. Every ``<a id="x">`` section of the reasons file is
    one accepted decision: its heading is the title, the rest its rationale,
    and its date the earliest one written in it (the first time the reason
    was recorded). A section with no date yields an empty date, which
    ``check_decisions`` reports; a link to a missing section is reported by
    ``check_rules``.
    """
    parts = _ANCHOR.split(reasons)
    decisions = []
    for anchor, body in zip(parts[1::2], parts[2::2]):
        heading = re.match(r'\s*## (.+)\n', body)
        rationale = body[heading.end():].strip() if heading else body.strip()
        days = sorted(_DAY.findall(rationale))
        decisions.append({'id': 'reasons#' + anchor,
                          'title': heading.group(1).strip() if heading else '',
                          'status': 'accepted', 'date': days[0] if days else '',
                          'baseline': 'AGENTS-reasons.md', 'rationale': rationale})
    rules = [{'id': 'agents#' + anchor, 'decision': 'reasons#' + anchor}
             for anchor in _WHY.findall(agents)]
    return rules, decisions


_QUESTION = re.compile(r'^- \*\*(Q\d+)\*\*(.*)$')
_TRADEOFF = re.compile(r'^  - (採用理由|未選|暫緩)(?: (.+?))?：(.+)$')
_LETTER = re.compile(r'\(([a-z])\) ')
_CHOSEN = re.compile(r'[採選](?: AI 建議)? \(([a-z])\)')


def questions_from_book(text):
    """Decided items of the decision book's section 6 (2026-11-10, Q7 (b)).

    Each ``- **Qn**`` item whose ``狀態：`` starts with ``已決`` is an accepted
    decision dated by the first date in its status. Its indented sub-bullets
    hold the trade-off: ``採用理由：`` is the rationale, ``未選 <option>：`` a
    rejected alternative and ``暫緩 <option>：`` a deferred one. A lettered
    option that was neither chosen nor given a sub-bullet becomes an
    alternative with an empty reason, which ``check_decisions`` reports, so a
    route cannot drop out of the record by being left unmentioned.
    """
    body, _ = _section(text, r'6\. ')
    items = []
    for line in body.splitlines():
        head = _QUESTION.match(line)
        if head:
            items.append([head.group(1), head.group(2), []])
        elif items and line.startswith('  - '):
            items[-1][2].append(line)
    decisions = []
    for qid, head, subs in items:
        options, _, status = head.partition('狀態：')
        if not status.startswith('已決'):
            continue
        day = _DAY.search(status)
        title = re.search(r'）：(.+?？)', options)
        rationale, alternatives = status.partition('理由：')[2].rstrip('）'), []
        for sub in subs:
            kind = _TRADEOFF.match(sub)
            if not kind:
                continue
            if kind.group(1) == '採用理由':
                rationale = kind.group(3)
            else:
                alternatives.append({'option': kind.group(2) or '',
                                     'outcome': 'rejected' if kind.group(1) == '未選' else 'deferred',
                                     'reason': kind.group(3)})
        listed = options.partition('選項：')[2]
        named = {a['option'][1] for a in alternatives if re.match(r'\([a-z]\)', a['option'])}
        for letter in sorted(set(_LETTER.findall(listed)) - set(_CHOSEN.findall(status)) - named):
            alternatives.append({'option': '(%s)' % letter, 'outcome': 'rejected', 'reason': ''})
        decisions.append({'id': 'book-' + qid,
                          'title': title.group(1) if title else options.strip(),
                          'status': 'accepted', 'date': day.group(0) if day else '',
                          'baseline': '決策書第 6 節', 'rationale': rationale.strip(),
                          'alternatives': alternatives})
    return decisions


def nongoals_from_plan(text, date):
    """Each bullet of the efficiency plan's section 3.2 is a route the plan
    rejected; the text after ``理由：`` is why (2026-11-10, Q7 (b))."""
    body, _ = _section(text, r'3\.2 ')
    decisions = []
    for item in re.findall(r'^- (.+)$', body, re.MULTILINE):
        title, _, rationale = item.partition('理由：')
        decisions.append({'id': 'plan-nongoal-%d' % (len(decisions) + 1),
                          'title': title.strip(), 'status': 'rejected', 'date': date,
                          'baseline': '效率計畫第 3.2 節', 'rationale': rationale.strip()})
    return decisions
