#!/usr/bin/env python3
"""P0 experiment runner, not a replacement for verify_bootstrap.py.

Default exit 0 means the status index validates and the regression tests pass.
--require-ready additionally rejects unmet architectural gates (expected exit 2).
No model, paid service, installation, live project or remote mutation is used.

2026-11-14 (decision v3 Q33): the execution-barrier modules, their probes and the
same-UID counterexamples moved to archive/v2-barrier/ and are no longer run here.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))

from project_bootstrap.approvals import VERIFIER as SIGNATURE_VERIFIER
from project_bootstrap.baseline import measure
from project_bootstrap.registry import validate


NEEDS_UV_MARKER = "raise unittest.SkipTest('needs "


def runtime_artifacts():
    result = {}
    for name, path in (('python-executable', Path(sys.executable)), ('ssh-keygen', SIGNATURE_VERIFIER)):
        try:
            result[name] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        except OSError:
            result[name] = {'result': '未驗證', 'reason': '無法讀取本機檔案'}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', action='store_true', help='also time the complete legacy verifier')
    parser.add_argument('--require-ready', action='store_true', help='reject incomplete strict-mode gates')
    parser.add_argument('--json', action='store_true', help='print reproducible structured evidence')
    args = parser.parse_args()
    artifacts = runtime_artifacts()
    data = json.loads((ROOT / 'experiments/v2/status.json').read_text(encoding='utf-8'))
    errors = validate(data, (ROOT / 'project-bootstrap-requirements-decision.md').read_text(encoding='utf-8'), ROOT)
    stream = io.StringIO()
    # P1 slice 4: test files that need a locked third-party package start with
    # NEEDS_UV_MARKER (verify_bootstrap.py enforces it). A4 runs on plain Python, so
    # they are left out here and listed in the report, not counted as skipped.
    needs_uv, suite = [], unittest.TestSuite()
    for path in sorted((ROOT / 'tests').glob('test_*.py')):
        if NEEDS_UV_MARKER in path.read_text(encoding='utf-8'):
            needs_uv.append('tests/' + path.name)
        else:
            suite.addTests(unittest.defaultTestLoader.loadTestsFromName('tests.' + path.stem))
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    baseline = measure(ROOT, args.baseline)
    baseline_valid = ('verifier' not in baseline or
                      (baseline['verifier']['exit_code'] == 0 and baseline['inputs_unchanged']))
    passed = not errors and result.wasSuccessful() and baseline_valid
    report = {'schema': 1, 'acquired_at': datetime.now(timezone.utc).isoformat(),
        'scope': 'P0 合成原型；不是現行程序切換或真實 surface 驗收',
        'harness_passed': passed, 'strict_ready': False,
        'registry_errors': errors, 'tests': {'run': result.testsRun,
            'failed': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
            'needs_uv': needs_uv},
        'archived': 'archive/v2-barrier/（v3 Q33，2026-11-14）：執行屏障模組、探針與同 UID 反例不再執行',
        'baseline': baseline,
        'runtime_artifacts': artifacts,
        'unverified': ['Windows/Linux', '真實工具與可信 session 隔離', '即時推送與模型上下文重建',
                       'Gitleaks/簽章/正式發布', '候選套件鎖定及授權清單', '20 專案容量']}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(stream.getvalue().rstrip())
        for error in errors:
            print('ERROR:', error)
        print(f'F22 必讀量：{baseline["unicode_characters"]} / 12000 字元；{baseline["reading_result"]}')
        print('執行屏障模組與探針：已封存於 archive/v2-barrier/（v3 Q33），不在這裡執行')
        if 'verifier' in baseline:
            print('既有驗證器：', json.dumps(baseline['verifier'], ensure_ascii=False))
        print('P0 實驗回歸：' + ('通過' if passed else '不通過'))
        print('嚴格模式：未就緒；不可部署或宣稱必要強保障已達標')
    if not passed:
        if args.json:
            print(stream.getvalue(), file=sys.stderr)
        return 1
    return 2 if args.require_ready else 0


if __name__ == '__main__':
    sys.exit(main())
