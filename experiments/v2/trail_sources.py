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
  estimates, not progress.

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


def roadmap_from_plan(text, status):
    body, _ = _section(text, r'7\. ')
    milestones = []
    for row in _rows(body):
        phase = re.match(r'(P\d)\s', row[0] + ' ')
        if phase and len(row) == 4:
            milestones.append({'id': phase.group(1), 'goal': row[1], 'exit': row[2],
                               'status': status.get(phase.group(1), 'planned')})
    return milestones
