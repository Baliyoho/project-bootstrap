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
        # 2026-11-10 (decision Q4, stage 1): the re-audit snapshot became read-on-demand and
        # the incident text moved to AGENTS-reasons.md; neither is a per-session read any more.
        texts = {name: (root / name).read_text(encoding='utf-8') for name in (
            'AGENTS.md', 'HANDOFF.md')}
        # 2026-11-10 (decision Q9): the skill is a directory; a normal pickup reads the entry and
        # mode-a.md only. A missing file must raise here rather than count as zero characters.
        for part in ('SKILL.md', 'mode-a.md'):
            texts['handoff-skill-from-authority/' + part] = (
                target / '.claude/skills/handoff' / part).read_text(encoding='utf-8')
    rows = [{'input': name, 'unicode_characters': len(text),
             'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()} for name, text in texts.items()]
    total = sum(row['unicode_characters'] for row in rows)
    report = {'scope': '常態入口（AGENTS、HANDOFF、skill 入口與 mode-a.md）；skill 取部署包權威範本，非任意全域副本；'
                  '不含任務專屬資料、條件式才讀的複審快照、AGENTS 理由檔、異常才讀的模式檔，'
                  '也不含開場 hook 輸出（2026-11-10 手動量本 repo 約 700 字元）',
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
