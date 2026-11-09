"""F20: document claims checked against a real Git checkout; unknown is never agreement."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from experiments.v2.facts import ADAPTERS, check_claims, handoff_claims

HANDOFF = '''# HANDOFF

## Git 狀態

- **待續分支**：`line-a`（從 main 建立）
- **骨架版本**：`2026-11-03`
'''
ALL = set(ADAPTERS)


class FactTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='bootstrap-v2-facts-')
        self.addCleanup(directory.cleanup)
        self.repo = Path(directory.name) / 'repo'
        (Path(directory.name) / 'home').mkdir()
        (Path(directory.name) / 'outside.txt').write_text('2026-11-03')
        self.env = {'PATH': os.environ.get('PATH', ''), 'HOME': str(Path(directory.name) / 'home'),
                    'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                    'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@example.invalid',
                    'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@example.invalid'}
        self.git('init', '--quiet', '--initial-branch=line-a', str(self.repo))
        (self.repo / 'VERSION').write_text('2026-11-03\n')
        (self.repo / 'HANDOFF.md').write_text(HANDOFF, encoding='utf-8')
        self.git('-C', str(self.repo), 'add', '-A')
        self.git('-C', str(self.repo), 'commit', '--quiet', '-m', 'init')

    def git(self, *args):
        subprocess.run(['git', *args], env=self.env, check=True, capture_output=True)

    def check(self, claims, allowed=ALL):
        return check_claims(self.repo, claims, allowed, env=self.env)

    def test_handoff_that_matches_reality_is_consistent(self):
        claims = handoff_claims(HANDOFF)
        self.assertEqual([c['proposition'] for c in claims],
                         ['骨架版本是 2026-11-03', '待續分支是 line-a'])
        result = self.check(claims + [{'doc': 'AGENTS.md', 'proposition': '工作樹乾淨',
                                       'fact': 'git.clean', 'expected': True}])
        self.assertEqual(result['overall'], '一致')

    def test_mismatch_names_document_proposition_and_observed_value(self):
        (self.repo / 'VERSION').write_text('2026-11-08\n')
        self.git('-C', str(self.repo), 'switch', '--quiet', '-c', 'other')
        result = self.check(handoff_claims(HANDOFF))
        self.assertEqual(result['overall'], '不一致')
        self.assertEqual([(r['doc'], r['proposition'], r['expected'], r['observed'], r['state'])
                          for r in result['rows']],
                         [('HANDOFF.md', '骨架版本是 2026-11-03', '2026-11-03', '2026-11-08',
                           '不一致'),
                          ('HANDOFF.md', '待續分支是 line-a', 'line-a', 'other', '不一致')])
        dirty = self.check([{'doc': 'd', 'proposition': 'p', 'fact': 'git.clean',
                             'expected': True}])
        self.assertEqual(dirty['rows'][0]['observed'], False)

    def test_cannot_or_may_not_check_is_unknown_not_agreement(self):
        version = handoff_claims(HANDOFF)[0]
        unauthorized = self.check([version], allowed={'git.branch'})
        self.assertEqual((unauthorized['overall'], unauthorized['rows'][0]['reason']),
                         ('未知', 'not-authorized'))
        self.assertEqual(self.check([dict(version, fact='service.http')])['rows'][0]['reason'],
                         'no-adapter')
        # Paths outside the repository are refused even when the file exists and matches.
        for path in ('../outside.txt', str(self.repo.parent / 'outside.txt'), ''):
            with self.subTest(path=path):
                row = self.check([dict(version, args={'path': path})])['rows'][0]
                self.assertEqual((row['state'], row['reason']), ('未知', 'query-failed'))
        (self.repo / 'VERSION').unlink()
        self.assertEqual(self.check([version])['rows'][0]['reason'], 'query-failed')
        self.assertEqual(self.check([dict(version, args={})])['rows'][0]['reason'],
                         'query-failed')
        (self.repo / 'VERSION').write_bytes(b'\xff\xfe')
        self.assertEqual(self.check([version])['rows'][0]['reason'], 'query-failed')
        self.git('-C', str(self.repo), 'switch', '--quiet', '--detach')
        branch = handoff_claims(HANDOFF)[1]
        self.assertEqual(self.check([branch])['rows'][0]['reason'], 'query-failed')
        self.assertEqual(self.check([])['overall'], '未知')
        # One mismatch outranks unknowns.
        mixed = self.check([dict(branch, fact='nope'), {'fact': 'file.exists',
                            'args': {'path': 'HANDOFF.md'}, 'expected': False}])
        self.assertEqual(mixed['overall'], '不一致')

    def test_checking_does_not_rewrite_the_index(self):
        index = self.repo / '.git' / 'index'
        before = index.read_bytes()
        later = os.stat(self.repo / 'VERSION').st_mtime + 5
        os.utime(self.repo / 'VERSION', (later, later))  # stale stat: status would refresh
        clean = {'doc': 'd', 'proposition': 'p', 'fact': 'git.clean', 'expected': True}
        self.assertEqual(self.check([clean])['overall'], '一致')
        self.assertEqual(index.read_bytes(), before)

    def test_missing_fields_yield_no_claims(self):
        self.assertEqual(handoff_claims('# HANDOFF\n- **骨架版本**：2026-11-03\n'), [])
        self.assertEqual(len(handoff_claims(HANDOFF.replace('待續分支', '分支'))), 1)


if __name__ == '__main__':
    unittest.main()
