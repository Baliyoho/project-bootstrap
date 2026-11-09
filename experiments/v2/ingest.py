"""F3／F40: turn real verifier output into evidence records.

``from_bootstrap`` reads the text ``tools/verify_bootstrap.py`` prints (one
``[  ok  ]``／``[ FAIL ]``／``[ skip ]`` line per check) together with the exit
code, and yields one record per check plus an overall record. ``from_v2``
reads ``tools/verify_v2.py --json``. Every record carries the round, the
command, the commit, the acquisition time, the scope and the digests of the
declared inputs, so ``evidence.resolve`` can tell this round from reuse and
expire a reused record when an input changed.

What cannot be read is never a pass: a line that does not parse is kept as an
ERROR record, an exit code that disagrees with the lines makes the overall
record FAIL, and output with no check line at all yields only a failed
overall record. Parsing proves the record matches the output; it does not
prove the output was not forged.
"""
import re

# A check line has a six-character status token; other bracketed lines such as
# ``[index] ...`` are informational and not checks.
CANDIDATE = re.compile(r'^\[[^\]]{6}\] ')
LINE = re.compile(r'^\[(  ok  | FAIL | skip )\] (.+?)(?:  — (.*))?$')
RESULT = {'  ok  ': 'PASS', ' FAIL ': 'FAIL', ' skip ': 'SKIP'}


def _record(claim, result, meta, detail=''):
    return {'id': f"{meta['round']}:{claim}", 'claim': claim, 'result': result,
            'round': meta['round'], 'source': f"{meta['command']} @ {meta['commit']}",
            'acquired_at': meta['acquired_at'], 'scope': meta['scope'],
            'depends': dict(meta['depends']), 'detail': detail}


def from_bootstrap(text, exit_code, meta):
    records, seen = [], set()
    for number, line in enumerate(text.splitlines(), 1):
        if not CANDIDATE.match(line):
            continue
        match = LINE.match(line)
        if not match:
            records.append(_record(f'verify_bootstrap:unparsed-line-{number}', 'ERROR', meta, line))
            continue
        claim = 'verify_bootstrap:' + match.group(2).strip()
        if claim in seen:
            records.append(_record(claim + ':duplicate', 'ERROR', meta, line))
            continue
        seen.add(claim)
        records.append(_record(claim, RESULT[match.group(1)], meta, match.group(3) or ''))
    results = {r['result'] for r in records}
    if not records:
        overall = 'FAIL'
    elif exit_code == 0 and results == {'PASS'}:
        overall = 'PASS'
    elif exit_code == 1 and 'SKIP' in results and results <= {'PASS', 'SKIP'}:
        overall = 'SKIP'
    else:
        overall = 'FAIL'
    records.append(_record('verify_bootstrap', overall, meta, f'exit {exit_code}'))
    return records


def from_v2(report, exit_code, meta):
    tests = report.get('tests') if isinstance(report, dict) else None
    if not isinstance(tests, dict) or not all(isinstance(tests.get(k), int)
                                              for k in ('run', 'failed', 'errors', 'skipped')):
        return [_record('verify_v2', 'ERROR', meta, 'unreadable report')]
    if tests['failed'] or tests['errors'] or not tests['run']:
        test_result = 'FAIL'
    elif tests['skipped']:
        test_result = 'SKIP'
    else:
        test_result = 'PASS'
    registry = 'PASS' if report.get('registry_errors') == [] else 'FAIL'
    harness = 'PASS' if report.get('harness_passed') is True and exit_code == 0 else 'FAIL'
    strict = 'PASS' if report.get('strict_ready') is True else 'FAIL'
    detail = f"{tests['run']} run, {tests['failed']} failed, {tests['errors']} errors, {tests['skipped']} skipped"
    return [_record('verify_v2:tests', test_result, meta, detail),
            _record('verify_v2:registry', registry, meta),
            _record('verify_v2:harness', harness, meta, f'exit {exit_code}'),
            _record('verify_v2:strict_ready', strict, meta, '嚴格模式未就緒時照實記 FAIL')]
