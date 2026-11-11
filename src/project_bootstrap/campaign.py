"""F24: one system update across many projects, with a bounded number of
human confirmations and every target accounted for.

Input is a batch report (``batch.assess_many``) and the targets the change
affects (``impact``'s project list mapped to the report's target strings; the
string ``'all'`` when impact fell back to a full run). Machines may check
every project; people should not have to confirm per project. The plan
groups the human work into prompts:

1. approve the release once, if anything will be updated;
2. approve the whole list of targets to update, in one prompt;
3. review every failed and excluded-for-cause target, in one prompt;
4. one more prompt per target whose customised content drifted, because a
   person must compare that project by hand.

The plan is within budget only when the prompts are at most ``budget``
(default 3, decision book F24). Over budget is reported, never hidden by
merging per-project comparisons into one prompt. Every input target appears
exactly once with an action; an unaffected target is listed as skipped, not
dropped. A plan with any failure or over budget is not ok.
"""

MANUAL_CODES = {'release:component-drift'}


def plan(report, affected, budget=3):
    rows, seen, problems = [], set(), []
    every = affected == 'all'
    affected = set() if every else set(affected)
    for row in report['results']:
        target = row['target']
        if target in seen:
            problems.append((target, 'listed-twice'))
            continue
        seen.add(target)
        outcome, code = row.get('outcome'), row.get('code')
        if outcome == 'eligible':
            action = 'update' if every or target in affected else 'skip-unaffected'
        elif outcome == 'excluded':
            action = 'excluded'
        elif code in MANUAL_CODES:
            action = 'compare-by-hand'
        elif outcome == 'failed':
            action = 'failed'
        else:
            action = 'failed'
            code = 'unknown-outcome'
        rows.append({'target': target, 'action': action, 'code': code})
    for target in sorted(affected - seen):
        problems.append((target, 'affected-but-not-assessed'))
        rows.append({'target': target, 'action': 'failed', 'code': 'not-assessed'})
    updates = [r['target'] for r in rows if r['action'] == 'update']
    review = [r['target'] for r in rows if r['action'] == 'failed']
    by_hand = [r['target'] for r in rows if r['action'] == 'compare-by-hand']
    prompts = []
    if updates:
        prompts.append({'kind': 'approve-release'})
        prompts.append({'kind': 'approve-targets', 'targets': updates})
    if review:
        prompts.append({'kind': 'review-failures', 'targets': review})
    prompts += [{'kind': 'compare-by-hand', 'targets': [t]} for t in by_hand]
    within = len(prompts) <= budget
    counts = {}
    for r in rows:
        counts[r['action']] = counts.get(r['action'], 0) + 1
    ok = within and not review and not by_hand and not problems
    return {'ok': ok, 'within_budget': within, 'prompts': prompts, 'rows': rows,
            'counts': counts, 'problems': problems, 'budget': budget}


def summary(result):
    """One line naming the human prompts and every non-update count."""
    head = 'OK' if result['ok'] else 'NOT OK'
    parts = ', '.join(f'{n} {a}' for a, n in sorted(result['counts'].items()))
    budget = (f"{len(result['prompts'])} human prompts (budget {result['budget']}"
              f"{'' if result['within_budget'] else ', OVER'})")
    return f"{head}: {parts}; {budget}"
