#!/usr/bin/env python3
"""This repo's test entry: the status index check and the whole unittest suite.

Exit 0 means the status index (docs/status.json) matches the decision book's
requirement IDs and every test passed. verify_bootstrap.py runs it on every
round (A4), so it needs plain Python only: test files that need a locked
third-party package start with NEEDS_UV_MARKER, are left out here and listed in
the report; ``uv run pytest`` runs them.

2026-11-18 (decision v3 Q46): renamed from verify_v2.py. The v2 prototype
report fields (strict_ready, the archive location, the ssh-keygen fingerprint
and the read-cost baseline) went with the archived v2 code.
"""
import argparse
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))

from project_bootstrap.registry import validate  # noqa: E402

NEEDS_UV_MARKER = "raise unittest.SkipTest('needs "
BOOK = 'project-bootstrap-requirements-decision-v3.md'
INDEX = 'docs/status.json'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--json', action='store_true', help='print the structured report')
    args = parser.parse_args(argv)
    data = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    errors = validate(data, (ROOT / BOOK).read_text(encoding='utf-8'), ROOT)
    stream = io.StringIO()
    needs_uv, suite = [], unittest.TestSuite()
    for path in sorted((ROOT / 'tests').glob('test_*.py')):
        if NEEDS_UV_MARKER in path.read_text(encoding='utf-8'):
            needs_uv.append('tests/' + path.name)
        else:
            suite.addTests(unittest.defaultTestLoader.loadTestsFromName('tests.' + path.stem))
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    passed = not errors and result.wasSuccessful()
    report = {'schema': 2, 'acquired_at': datetime.now(timezone.utc).isoformat(),
              'passed': passed, 'registry_errors': errors,
              'tests': {'run': result.testsRun, 'failed': len(result.failures),
                        'errors': len(result.errors), 'skipped': len(result.skipped),
                        'needs_uv': needs_uv}}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(stream.getvalue().rstrip())
        for error in errors:
            print('ERROR:', error)
        print('測試套件與現況索引：' + ('通過' if passed else '不通過'))
    if not passed:
        if args.json:
            print(stream.getvalue(), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
