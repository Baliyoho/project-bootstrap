"""Batch report over many targets (F30 prototype on top of gitclaim).

Every requested target appears exactly once in the report. A target the
caller marked archived is listed as excluded, never silently dropped; a
missing, duplicate or refused active target is a failure, and one failure
makes the batch not ok. Exceptions inside one target never stop the others.
"""
from pathlib import Path

from experiments.v2.gitclaim import GitGateDenied, assess_start


def assess_many(targets, owner, env=None):
    """``targets``: iterable of (path, state) with state 'active' or 'archived'."""
    results, seen = [], set()
    for path, state in targets:
        key = str(Path(path).resolve())
        row = {'target': str(path), 'state': state}
        if key in seen:
            row.update(outcome='failed', code='duplicate-target')
        elif state == 'archived':
            row.update(outcome='excluded', code='archived')
        elif state != 'active':
            row.update(outcome='failed', code='invalid-target-state')
        elif not Path(path).is_dir():
            row.update(outcome='failed', code='missing-target')
        else:
            try:
                facts = assess_start(path, owner, env=env)
                row.update(outcome='eligible', code='ok', remote_sha=facts['remote_sha'])
            except GitGateDenied as error:
                row.update(outcome='failed', code=str(error))
            except Exception:
                row.update(outcome='failed', code='target-error')
        seen.add(key)
        results.append(row)
    counts = {name: sum(row['outcome'] == name for row in results)
              for name in ('eligible', 'excluded', 'failed')}
    return {'ok': counts['failed'] == 0 and counts['eligible'] > 0,
            'counts': counts, 'results': results}


def summary(report):
    """One line that never claims success for targets it did not process."""
    c = report['counts']
    head = 'ALL ELIGIBLE' if report['ok'] else 'NOT OK'
    return (f"{head}: {c['eligible']} eligible, {c['failed']} failed, "
            f"{c['excluded']} excluded of {len(report['results'])} listed")
