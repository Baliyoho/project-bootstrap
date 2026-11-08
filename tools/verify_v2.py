#!/usr/bin/env python3
"""P0 experiment runner, not a replacement for verify_bootstrap.py.

Default exit 0 means regression tests and expected counterexamples reproduced.
--require-ready additionally rejects unmet architectural gates (expected exit 2).
No model, paid service, installation, live project or remote mutation is used.
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

from experiments.v2.approvals import VERIFIER as SIGNATURE_VERIFIER
from experiments.v2.baseline import measure
from experiments.v2.broker_fixture import SANDBOX_EXEC, probe_broker
from experiments.v2.feasibility import run_probes
from experiments.v2.isolation import probe_isolation
from experiments.v2.lifecycle import guardian_inputs
from experiments.v2.managed_fixture import probe_managed
from experiments.v2.registry import validate
from experiments.v2.supervisor import run_supervisor_probe


def runtime_artifacts():
    interpreter, guardian = guardian_inputs()
    result = {}
    for name, path in (('python-executable', interpreter), ('guardian-script', guardian),
                       ('sandbox-exec', SANDBOX_EXEC), ('ssh-keygen', SIGNATURE_VERIFIER)):
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
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'experiments/v2'), pattern='test_*.py',
                                               top_level_dir=str(ROOT / 'experiments'))
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    findings = run_probes()
    isolation = probe_isolation()
    supervisor = run_supervisor_probe()
    broker = probe_broker()
    managed = probe_managed()
    baseline = measure(ROOT, args.baseline)
    counterexamples = all(row['counterexample_observed'] for row in findings)
    baseline_valid = ('verifier' not in baseline or
                      (baseline['verifier']['exit_code'] == 0 and baseline['inputs_unchanged']))
    passed = (not errors and result.wasSuccessful() and counterexamples and baseline_valid
              and supervisor['result'] == '通過' and isolation['result'] != '不通過'
              and broker['result'] != '不通過' and managed['result'] != '不通過')
    report = {'schema': 1, 'acquired_at': datetime.now(timezone.utc).isoformat(),
        'scope': 'P0 合成原型；不是現行程序切換或真實 surface 驗收',
        'harness_passed': passed, 'strict_ready': False,
        'registry_errors': errors, 'tests': {'run': result.testsRun,
            'failed': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped)},
        'findings': findings, 'isolation_probe': isolation, 'supervisor_probe': supervisor,
        'broker_probe': broker, 'managed_probe': managed, 'baseline': baseline,
        'runtime_artifacts': artifacts,
        'unverified': ['Windows/Linux', '真實工具與可信 session 隔離', '即時推送與模型上下文重建',
                       'Gitleaks/簽章/正式發布', '候選套件鎖定及授權清單', '20 專案容量']}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(stream.getvalue().rstrip())
        for error in errors:
            print('ERROR:', error)
        for finding in findings:
            print(f'{finding["id"]}: 反例重現={finding["counterexample_observed"]}；'
                  f'需求={finding["requirement_result"]}')
        print(f'F22 必讀量：{baseline["unicode_characters"]} / 12000 字元；{baseline["reading_result"]}')
        print('OS 隔離探針：' + isolation['result'] + '（僅所列範圍，不代表 strict ready）')
        print('執行中上下文替換：' + supervisor['result'] + '（固定合成子程序，非真實模型）')
        print('管道身分／管理分權：' + broker['result'] + '（受隔離合成 agent，非正式工具接線）')
        print('受管前提切換／outbox：' + managed['result'] + '（macOS 單一合成 worker）')
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
