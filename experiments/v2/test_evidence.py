"""F3／F40: fresh, reused, unverified and failed evidence never merge into one pass."""

import hashlib
from pathlib import Path
import tempfile
import unittest

from experiments.v2.evidence import file_probe, report, resolve

ROUND = 'r2'


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='bootstrap-v2-evidence-')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / 'tools').mkdir()
        (self.root / 'tools' / 'check.py').write_text('v1')
        (self.root / 'notes.md').write_text('unrelated')
        self.probe = file_probe(self.root, {'PYVER': '3.15'})
        self.reused = {'id': 'e1', 'claim': 'docs', 'result': 'PASS', 'round': 'r1',
                       'source': 'verify_bootstrap.py', 'acquired_at': '2026-11-08T10:00+08',
                       'scope': 'macOS 本機', 'depends': {'file:tools/check.py': sha('v1'),
                                                          'env:PYVER': sha('3.15')}}
        self.fresh = {'id': 'e2', 'claim': 'git', 'result': 'PASS', 'round': ROUND}

    def resolve(self, claims, records, revoked=()):
        return resolve(claims, records, self.probe, ROUND, revoked)

    def test_fresh_and_valid_reuse_pass_but_are_shown_apart(self):
        result = self.resolve(['git', 'docs'], [self.fresh, self.reused])
        self.assertEqual(result['overall'], '通過')
        self.assertEqual([(r['claim'], r['state']) for r in result['rows']],
                         [('git', '本輪實查'), ('docs', '沿用')])
        text = report(result)
        self.assertIn('本輪實查（1）\n- git：PASS', text)
        self.assertIn('沿用（1）\n- docs：PASS；來源 verify_bootstrap.py，取得 '
                      '2026-11-08T10:00+08，範圍 macOS 本機', text)
        self.assertIn('未驗證（0）', text)
        # Renaming an unrelated file does not expire the reuse.
        (self.root / 'notes.md').rename(self.root / 'renamed.md')
        self.assertEqual(self.resolve(['docs'], [self.reused])['overall'], '通過')

    def test_f3_one_claim_without_evidence_stops_the_whole_report(self):
        result = self.resolve(['git', 'docs', 'service'], [self.fresh, self.reused])
        self.assertEqual(result['overall'], '未驗證')
        self.assertEqual(result['rows'][-1], {'claim': 'service', 'state': '未驗證',
                                              'reason': 'no-evidence'})
        for status, state in (('SKIP', '未驗證'), ('NOT_CONFIGURED', '未驗證'),
                              ('FAIL', '不通過'), ('ERROR', '不通過')):
            with self.subTest(status=status):
                bad = dict(self.fresh, result=status)
                result = self.resolve(['git', 'docs'], [bad, self.reused])
                self.assertEqual((result['overall'], result['rows'][0]['state']), (state, state))
        failed_and_missing = self.resolve(['git', 'x'], [dict(self.fresh, result='FAIL')])
        self.assertEqual(failed_and_missing['overall'], '不通過')
        self.assertEqual(self.resolve([], [])['overall'], '未驗證')
        for bad in ({'claim': 'git', 'result': 'OK', 'round': ROUND}, 'PASS'):
            with self.subTest(record=bad):
                rows = self.resolve(['git'], [bad])['rows']
                self.assertEqual(rows[0]['state'], '未驗證')

    def test_f40_reuse_needs_source_time_scope_and_dependencies(self):
        for key in ('source', 'acquired_at', 'scope'):
            for value in (None, '  '):
                with self.subTest(key=key, value=value):
                    record = dict(self.reused, **{key: value})
                    row = self.resolve(['docs'], [record])['rows'][0]
                    self.assertEqual((row['state'], row['reason']), ('未驗證', 'reuse-incomplete'))
        for depends in (None, {}, 'file:tools/check.py'):
            with self.subTest(depends=depends):
                row = self.resolve(['docs'], [dict(self.reused, depends=depends)])['rows'][0]
                self.assertEqual(row['reason'], 'reuse-without-dependencies')

    def test_f40_changed_or_unreadable_input_expires_reuse(self):
        (self.root / 'tools' / 'check.py').write_text('v2')
        row = self.resolve(['docs'], [self.reused])['rows'][0]
        self.assertEqual((row['state'], row['reason']), ('未驗證', 'expired:file:tools/check.py'))
        (self.root / 'tools' / 'check.py').write_text('v1')
        probe = file_probe(self.root, {'PYVER': '3.16'})
        row = resolve(['docs'], [self.reused], probe, ROUND)['rows'][0]
        self.assertEqual(row['reason'], 'expired:env:PYVER')
        (self.root / 'tools' / 'check.py').rename(self.root / 'tools' / 'moved.py')
        row = self.resolve(['docs'], [self.reused])['rows'][0]
        self.assertEqual(row['reason'], 'dependency-unreadable:file:tools/check.py')
        for name in ('file:../x', 'file:/etc/hosts', 'other:x', 'env:MISSING', 'file:'):
            with self.subTest(name=name):
                self.assertIsNone(self.probe(name))
        # Escaping paths name files that really exist.
        inner = file_probe(self.root / 'tools', {})
        self.assertIsNone(inner('file:../notes.md'))
        self.assertIsNone(inner('file:' + str(self.root / 'notes.md')))
        self.assertIsNotNone(inner('file:moved.py'))
        # A fresh record needs no dependency list: it was just measured.
        self.assertEqual(self.resolve(['git'], [self.fresh])['overall'], '通過')

    def test_f40_user_revocation_and_latest_record_is_not_silently_swapped(self):
        row = self.resolve(['docs'], [self.reused], revoked=['e1'])['rows'][0]
        self.assertEqual((row['state'], row['reason']), ('未驗證', 'revoked'))
        # A newer invalid record is reported as such; an older pass is not resurrected.
        newer = dict(self.reused, id='e3', source='')
        row = self.resolve(['docs'], [self.reused, newer])['rows'][0]
        self.assertEqual((row['reason'], row['evidence']), ('reuse-incomplete', 'e3'))


if __name__ == '__main__':
    unittest.main()
