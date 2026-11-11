"""F3／F40: real verifier output becomes evidence; unparsable or inconsistent output is never a pass."""

import hashlib
from pathlib import Path
import tempfile
import unittest

from project_bootstrap.evidence import file_probe, resolve
from project_bootstrap.ingest import from_bootstrap, from_v2

ICON = {'OK': '  ok  ', 'FAIL': ' FAIL ', 'SKIP': ' skip '}


def real_lines(*rows):
    """Same format as verify_bootstrap's ``record``; test_ingest_format pins that."""
    return ''.join(f"[{ICON[row[0]]}] {row[1]}{('  — ' + row[2]) if len(row) > 2 and row[2] else ''}\n"
                   for row in rows)


class IngestTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='bootstrap-v2-ingest-')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / 'PROJECT-BOOTSTRAP.md').write_text('pack v1\n')
        digest = hashlib.sha256(b'pack v1\n').hexdigest()
        self.meta = {'round': 'r2', 'command': 'python3 -X utf8 tools/verify_bootstrap.py',
                     'commit': 'abc1234', 'acquired_at': '2026-11-10T12:00:00+08:00',
                     'scope': 'macOS 本機', 'depends': {'file:PROJECT-BOOTSTRAP.md': digest}}
        self.probe = file_probe(self.root, environ={})

    def test_real_format_lines_become_one_record_each_plus_overall(self):
        text = real_lines(('OK', '骨架檔案清單', '22 檔'), ('OK', '跨平台防呆'))
        records = from_bootstrap(text + '\nOK：部署包驗證全數通過\n', 0, self.meta)
        self.assertEqual([(r['claim'], r['result']) for r in records],
                         [('verify_bootstrap:骨架檔案清單', 'PASS'),
                          ('verify_bootstrap:跨平台防呆', 'PASS'), ('verify_bootstrap', 'PASS')])
        self.assertEqual(records[0]['detail'], '22 檔')
        self.assertEqual(records[0]['source'], 'python3 -X utf8 tools/verify_bootstrap.py @ abc1234')
        claims = [r['claim'] for r in records]
        self.assertEqual(resolve(claims, records, self.probe, 'r2')['overall'], '通過')

    def test_fail_and_skip_lines_keep_their_meaning(self):
        text = real_lines(('OK', 'a'), ('FAIL', 'b', 'why'), ('SKIP', 'c'))
        records = from_bootstrap(text, 2, self.meta)
        self.assertEqual([r['result'] for r in records], ['PASS', 'FAIL', 'SKIP', 'FAIL'])
        skip_only = from_bootstrap(real_lines(('OK', 'a'), ('SKIP', 'c')), 1, self.meta)
        self.assertEqual(skip_only[-1]['result'], 'SKIP')
        resolved = resolve(['verify_bootstrap'], skip_only, self.probe, 'r2')
        self.assertEqual(resolved['overall'], '未驗證')

    def test_exit_code_that_disagrees_with_the_lines_fails_overall(self):
        ok_lines = real_lines(('OK', 'a'))
        self.assertEqual(from_bootstrap(ok_lines, 2, self.meta)[-1]['result'], 'FAIL')
        self.assertEqual(from_bootstrap(ok_lines, 1, self.meta)[-1]['result'], 'FAIL')
        skip = real_lines(('SKIP', 'c'))
        self.assertEqual(from_bootstrap(skip, 0, self.meta)[-1]['result'], 'FAIL')
        self.assertEqual(from_bootstrap(skip + real_lines(('FAIL', 'd')), 1, self.meta)[-1]['result'],
                         'FAIL')

    def test_unparsable_duplicate_or_empty_output_is_not_a_pass(self):
        broken = from_bootstrap('[ ok   ] squeezed\n[index] staged 提交候選與工作樹一致\n'
                                + real_lines(('OK', 'a'), ('OK', 'a')), 0, self.meta)
        self.assertEqual([(r['claim'], r['result']) for r in broken],
                         [('verify_bootstrap:unparsed-line-1', 'ERROR'),
                          ('verify_bootstrap:a', 'PASS'), ('verify_bootstrap:a:duplicate', 'ERROR'),
                          ('verify_bootstrap', 'FAIL')])
        empty = from_bootstrap('crashed before printing\n', 0, self.meta)
        self.assertEqual([(r['claim'], r['result']) for r in empty], [('verify_bootstrap', 'FAIL')])

    def test_reused_record_expires_when_an_input_changes(self):
        records = from_bootstrap(real_lines(('OK', 'a')), 0, self.meta)
        self.assertEqual(resolve(['verify_bootstrap'], records, self.probe, 'r3')['rows'][0]['state'],
                         '沿用')
        (self.root / 'PROJECT-BOOTSTRAP.md').write_text('pack v2\n')
        row = resolve(['verify_bootstrap'], records, self.probe, 'r3')['rows'][0]
        self.assertEqual((row['state'], row['reason']),
                         ('未驗證', 'expired:file:PROJECT-BOOTSTRAP.md'))

    def test_v2_json_report_maps_to_four_claims(self):
        report = {'tests': {'run': 294, 'failed': 0, 'errors': 0, 'skipped': 0},
                  'registry_errors': [], 'harness_passed': True, 'strict_ready': False}
        records = from_v2(report, 0, self.meta)
        self.assertEqual([(r['claim'], r['result']) for r in records],
                         [('verify_v2:tests', 'PASS'), ('verify_v2:registry', 'PASS'),
                          ('verify_v2:harness', 'PASS'), ('verify_v2:strict_ready', 'FAIL')])
        self.assertEqual(records[0]['detail'], '294 run, 0 failed, 0 errors, 0 skipped')

    def test_v2_failures_skips_and_bad_reports(self):
        base = {'registry_errors': [], 'harness_passed': True, 'strict_ready': True}
        def results(tests, exit_code=0, **extra):
            return [r['result'] for r in from_v2(dict(base, tests=tests, **extra), exit_code, self.meta)]
        good = {'run': 3, 'failed': 0, 'errors': 0, 'skipped': 0}
        self.assertEqual(results(good), ['PASS'] * 4)
        self.assertEqual(results(dict(good, failed=1))[0], 'FAIL')
        self.assertEqual(results(dict(good, errors=1))[0], 'FAIL')
        self.assertEqual(results(dict(good, run=0))[0], 'FAIL')
        self.assertEqual(results(dict(good, skipped=2))[0], 'SKIP')
        self.assertEqual(results(good, registry_errors=['x'])[1], 'FAIL')
        self.assertEqual(results(good, registry_errors=None)[1], 'FAIL')
        self.assertEqual(results(good, exit_code=1)[2], 'FAIL')
        self.assertEqual(results(good, harness_passed='yes')[2], 'FAIL')
        for bad in (None, {}, {'tests': {'run': '3', 'failed': 0, 'errors': 0, 'skipped': 0}}):
            with self.subTest(report=bad):
                self.assertEqual([(r['claim'], r['result']) for r in from_v2(bad, 0, self.meta)],
                                 [('verify_v2', 'ERROR')])


if __name__ == '__main__':
    unittest.main()
