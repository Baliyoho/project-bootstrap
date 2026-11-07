"""Read-cost measurement; no authority to skip the existing A4 procedure."""
import hashlib
import importlib.util
import platform
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def fingerprint(root):
    paths = sorted(set(subprocess.run(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=root,
        check=True, capture_output=True, text=True).stdout.splitlines()))
    result = hashlib.sha256()
    for path in paths:
        target = root / path
        if target.is_file():
            result.update(path.encode('utf-8') + b'\0' + hashlib.sha256(target.read_bytes()).digest())
        else:
            result.update(path.encode('utf-8') + b'\0MISSING')
    return result.hexdigest()


def measure(root, run_verifier=False):
    spec = importlib.util.spec_from_file_location('legacy_bootstrap', root / 'tools/verify_bootstrap.py')
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    with tempfile.TemporaryDirectory(prefix='bootstrap-v2-baseline-') as directory:
        target = Path(directory)
        legacy.extract(target)
        texts = {name: (root / name).read_text(encoding='utf-8') for name in (
            'AGENTS.md', 'HANDOFF.md', 'project-bootstrap-reaudit-2026-11-03.md')}
        texts['handoff-skill-from-authority'] = (
            target / '.claude/skills/handoff/SKILL.md').read_text(encoding='utf-8')
    rows = [{'input': name, 'unicode_characters': len(text),
             'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()} for name, text in texts.items()]
    total = sum(row['unicode_characters'] for row in rows)
    report = {'scope': '常態四份入口；skill 取部署包權威範本，非任意全域副本；不含任務專屬資料',
        'inputs': rows, 'unicode_characters': total, 'limit': 12000,
        'reading_result': '通過' if total <= 12000 else '不通過',
        'tokens': '未量測，不以字元冒充 token',
        'full_handoff_seconds': None,
        'full_handoff_result': '未驗證；單一驗證器時間不等於完整接棒時間',
        'environment': {'os': platform.system(), 'release': platform.release(),
                        'python': platform.python_version()},
        'candidate_digest': fingerprint(root)}
    if run_verifier:
        started = time.monotonic()
        result = subprocess.run([sys.executable, '-X', 'utf8', str(root / 'tools/verify_bootstrap.py')],
                                cwd=root, capture_output=True, timeout=300)
        report['verifier'] = {'seconds': round(time.monotonic() - started, 3),
            'exit_code': result.returncode,
            'ok': result.stdout.count(b'[  ok  ]'),
            'skip': result.stdout.count(b'[ skip ]'),
            'output_sha256': hashlib.sha256(result.stdout + result.stderr).hexdigest()}
        report['inputs_unchanged'] = fingerprint(root) == report['candidate_digest']
    return report
