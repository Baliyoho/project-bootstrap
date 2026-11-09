"""M2 evidence ledger for F3／F40: this round, reused, unverified and failed stay apart.

Each claim the report wants to make is resolved from evidence records:

- a fresh record (acquired this round) gives its own result;
- a reused record must carry its source, acquisition time and scope, and the
  digest of every input it depended on must still match now; a changed or
  unreadable input expires it, a user revocation removes it;
- SKIP／NOT_CONFIGURED／no record is unverified, FAIL／ERROR is failed.

The overall line says 通過 only when every claim is verified this round or by
valid reuse. One claim without evidence keeps the whole report from passing.
Dependencies are named inputs with digests, so renaming an unrelated file
does not expire anything, while editing a dependency does.
"""

import hashlib
import os
from pathlib import Path

RESULTS = {'PASS', 'FAIL', 'ERROR', 'SKIP', 'NOT_CONFIGURED'}


def file_probe(root, environ=None):
    """Digest ``file:<relative path>`` and ``env:<NAME>`` inputs; anything else is None."""
    environ = os.environ if environ is None else environ

    def probe(name):
        kind, _, value = name.partition(':')
        if kind == 'file' and value and not value.startswith('/') and '..' not in value.split('/'):
            try:
                return hashlib.sha256((Path(root) / value).read_bytes()).hexdigest()
            except OSError:
                return None
        if kind == 'env' and value in environ:
            return hashlib.sha256(environ[value].encode('utf-8', 'surrogateescape')).hexdigest()
        return None
    return probe


def _resolve(record, probe, revoked, round_id):
    if not isinstance(record, dict) or record.get('result') not in RESULTS:
        return '未驗證', 'record-invalid'
    if record.get('id') in revoked:
        return '未驗證', 'revoked'
    fresh = record.get('round') == round_id
    if not fresh:
        if not all(isinstance(record.get(key), str) and record.get(key).strip()
                   for key in ('source', 'acquired_at', 'scope')):
            return '未驗證', 'reuse-incomplete'
        depends = record.get('depends')
        if not isinstance(depends, dict) or not depends:
            return '未驗證', 'reuse-without-dependencies'
        for name, digest in sorted(depends.items()):
            current = probe(name)
            if current is None:
                return '未驗證', 'dependency-unreadable:' + name
            if current != digest:
                return '未驗證', 'expired:' + name
    result = record['result']
    if result in ('FAIL', 'ERROR'):
        return '不通過', result
    if result in ('SKIP', 'NOT_CONFIGURED'):
        return '未驗證', result
    return ('本輪實查', 'PASS') if fresh else ('沿用', 'PASS')


def resolve(claims, records, probe, round_id, revoked=()):
    """``claims``: claim names the report asserts. ``probe(name)`` digests an input now.

    Returns one row per claim, in order, plus the overall verdict. The last
    record for a claim wins only if it is valid; otherwise the claim is shown
    with the reason it could not be used, never silently replaced.
    """
    revoked = set(revoked)
    by_claim = {}
    for record in records:
        if isinstance(record, dict) and isinstance(record.get('claim'), str):
            by_claim.setdefault(record['claim'], []).append(record)
    rows = []
    for claim in claims:
        candidates = by_claim.get(claim, [])
        if not candidates:
            rows.append({'claim': claim, 'state': '未驗證', 'reason': 'no-evidence'})
            continue
        state, reason = _resolve(candidates[-1], probe, revoked, round_id)
        row = {'claim': claim, 'state': state, 'reason': reason,
               'evidence': candidates[-1].get('id')}
        if state == '沿用':
            row.update(source=candidates[-1]['source'],
                       acquired_at=candidates[-1]['acquired_at'],
                       scope=candidates[-1]['scope'])
        rows.append(row)
    states = {row['state'] for row in rows}
    if not rows:
        overall = '未驗證'
    elif '不通過' in states:
        overall = '不通過'
    elif '未驗證' in states:
        overall = '未驗證'
    else:
        overall = '通過'
    return {'overall': overall, 'rows': rows}


def report(resolved):
    """Text with the four groups always separate; empty groups say so."""
    lines = [f"整體：{resolved['overall']}"]
    for group in ('本輪實查', '沿用', '未驗證', '不通過'):
        rows = [row for row in resolved['rows'] if row['state'] == group]
        lines.append(f'{group}（{len(rows)}）')
        for row in rows:
            extra = (f"；來源 {row['source']}，取得 {row['acquired_at']}，範圍 {row['scope']}"
                     if group == '沿用' else '')
            lines.append(f"- {row['claim']}：{row['reason']}{extra}")
    return '\n'.join(lines) + '\n'
