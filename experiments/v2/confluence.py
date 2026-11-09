"""M2／M4 merging of findings from parallel lines for F26.

Each line reports findings: the question it answers (``key``), the value it
found, whether it is verified (in the F3 sense) or only claimed, and, as F40
asks, its source, acquisition time and scope (the conditions it holds under,
e.g. ``{"os": "macOS"}``). ``merge`` puts them in one place without letting
anything become a shared basis by accident:

- a finding missing source, time or scope is kept but marked incomplete and
  never shared;
- claimed findings are kept as unconfirmed, never shared;
- verified findings with the same value and the same scope become shared,
  carrying every source;
- verified findings whose scopes differ stay as conditional conclusions, each
  with its own scope. Different scopes are not a conflict and nothing is
  discarded;
- verified findings that disagree under the same or overlapping scope are a
  conflict and none of them is shared until someone resolves it.

Scopes overlap when no condition they both name has different values; an
empty scope means "everywhere" and overlaps every other. This only compares
what lines declared; it cannot tell that two differently worded keys are the
same question.
"""
import datetime


def _text(value):
    return isinstance(value, str) and value.strip() != ''


def _complete(finding):
    if not all(_text(finding.get(k)) for k in ('line', 'key', 'source')):
        return False
    try:
        datetime.datetime.fromisoformat(finding.get('obtained_at'))
    except (TypeError, ValueError):
        return False
    return isinstance(finding.get('scope'), dict) and finding.get('status') in ('verified', 'claimed')


def _overlap(a, b):
    return all(a[k] == b[k] for k in set(a) & set(b))


def _cite(finding):
    return {k: finding.get(k) for k in ('line', 'source', 'obtained_at', 'scope', 'value')}


def merge(findings):
    out = {'shared': [], 'conditional': [], 'unconfirmed': [], 'incomplete': [], 'conflicts': []}
    verified = {}
    for finding in findings:
        if not isinstance(finding, dict) or not _complete(finding):
            out['incomplete'].append(finding)
        elif finding['status'] == 'claimed':
            out['unconfirmed'].append(_cite(finding))
        else:
            verified.setdefault(finding['key'], []).append(finding)
    for key, group in sorted(verified.items()):
        clashing = set()
        for i, a in enumerate(group):
            for j in range(i + 1, len(group)):
                b = group[j]
                if a.get('value') != b.get('value') and _overlap(a['scope'], b['scope']):
                    clashing.update((i, j))
        if clashing:
            out['conflicts'].append({'key': key,
                                     'findings': [_cite(group[i]) for i in sorted(clashing)]})
        rest = [f for i, f in enumerate(group) if i not in clashing]
        buckets = {}
        for finding in rest:
            scope = tuple(sorted(finding['scope'].items()))
            buckets.setdefault((scope, repr(finding.get('value'))), []).append(finding)
        whole = len(buckets) == 1 and not clashing
        for (scope, _), same in sorted(buckets.items()):
            entry = {'key': key, 'value': same[0].get('value'), 'scope': dict(scope),
                     'sources': [_cite(f) for f in same]}
            out['shared' if whole else 'conditional'].append(entry)
    return out


def basis(merged, key, scope):
    """What a line may rely on for ``key`` under ``scope``: shared or a conditional
    whose scope covers it. A conflict on the key blocks it; anything else is None."""
    if any(c['key'] == key for c in merged['conflicts']):
        return None
    for entry in merged['shared'] + merged['conditional']:
        if entry['key'] == key and all(scope.get(k) == v for k, v in entry['scope'].items()):
            return entry
    return None
