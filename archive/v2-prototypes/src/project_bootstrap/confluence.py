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

A conflict is handled by a resolution a person records: who decided, when,
why, under which scope, and which conflicting findings (by line and source) it
weighed. It must pick the value of one of the findings it cites, so a decision
cannot invent a value without evidence. It settles the conflict only when it
cites every finding in it; a conflicting finding that arrived afterwards
reopens the conflict instead of being silently overruled. The overruled
findings stay in the record with the decision.

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


def _ident(finding):
    return (finding.get('line'), finding.get('source'))


def _resolution_error(resolution, group):
    """Why a resolution cannot be used, or None."""
    if not isinstance(resolution, dict) or not all(
            _text(resolution.get(k)) for k in ('decided_by', 'reason')):
        return 'resolution-incomplete'
    try:
        datetime.datetime.fromisoformat(resolution.get('decided_at'))
    except (TypeError, ValueError):
        return 'resolution-incomplete'
    cites = resolution.get('cites')
    if not isinstance(resolution.get('scope'), dict) or not isinstance(cites, list) or not cites:
        return 'resolution-incomplete'
    if not all(isinstance(c, dict) for c in cites):
        return 'resolution-incomplete'
    known = {_ident(f): f for f in group}
    cited = [known.get((c.get('line'), c.get('source'))) for c in cites]
    if None in cited:
        return 'resolution-cites-unknown'
    if 'value' not in resolution or all(f.get('value') != resolution['value'] for f in cited):
        return 'resolution-value-unsupported'
    return None


def merge(findings, resolutions=()):
    out = {'shared': [], 'conditional': [], 'unconfirmed': [], 'incomplete': [], 'conflicts': [],
           'resolved': [], 'invalid_resolutions': []}
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
        settled = None
        for resolution in [r for r in resolutions if isinstance(r, dict) and r.get('key') == key]:
            error = _resolution_error(resolution, group)
            if error:
                out['invalid_resolutions'].append({'key': key, 'code': error})
                continue
            cited = {(c['line'], c['source']) for c in resolution['cites']}
            if clashing and {_ident(group[i]) for i in clashing} <= cited:
                settled = resolution
        if clashing and settled is None:
            # A decision exists for this key but no longer covers every conflicting finding.
            reopened = any(r.get('key') == key for r in resolutions if isinstance(r, dict))
            out['conflicts'].append({'key': key, 'reopened': reopened,
                                     'findings': [_cite(group[i]) for i in sorted(clashing)]})
        rest = [f for i, f in enumerate(group) if i not in clashing]
        buckets = {}
        if settled is not None:
            kept = [group[i] for i in sorted(clashing) if group[i].get('value') == settled['value']]
            overruled = [group[i] for i in sorted(clashing)
                         if group[i].get('value') != settled['value']]
            decision = {k: settled[k] for k in ('decided_by', 'decided_at', 'reason')}
            out['resolved'].append({'key': key, 'value': settled['value'],
                                    'scope': dict(settled['scope']), 'decision': decision,
                                    'kept': [_cite(f) for f in kept],
                                    'overruled': [_cite(f) for f in overruled]})
            scope = tuple(sorted(settled['scope'].items()))
            # Sources keep their own scope; the entry's scope is the decision's.
            buckets[(scope, repr(settled['value']))] = kept
        for finding in rest:
            scope = tuple(sorted(finding['scope'].items()))
            buckets.setdefault((scope, repr(finding.get('value'))), []).append(finding)
        whole = len(buckets) == 1 and (not clashing or settled is not None)
        for (scope, value), same in sorted(buckets.items()):
            entry = {'key': key, 'value': same[0].get('value'), 'scope': dict(scope),
                     'sources': [_cite(f) for f in same]}
            if settled is not None and (scope, value) == (
                    tuple(sorted(settled['scope'].items())), repr(settled['value'])):
                # Whoever relies on it can see it rests on a decision, not on agreement.
                entry['decision'] = out['resolved'][-1]['decision']
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
