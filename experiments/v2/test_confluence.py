"""F26: findings from lines merge in one place; unconfirmed or differently scoped ones are not shared."""

import unittest

from experiments.v2.confluence import basis, merge


def finding(line, value, status='verified', scope=None, key='hook-cwd', **extra):
    item = {'line': line, 'key': key, 'value': value, 'status': status,
            'source': f'{line}:verify', 'obtained_at': '2026-11-10T09:00:00+08:00',
            'scope': {} if scope is None else scope}
    item.update(extra)
    return item


class ConfluenceTests(unittest.TestCase):
    def test_agreeing_verified_findings_become_shared_with_every_source(self):
        merged = merge([finding('a', 'repo-root'), finding('b', 'repo-root')])
        self.assertEqual(len(merged['shared']), 1)
        shared = merged['shared'][0]
        self.assertEqual(([s['line'] for s in shared['sources']], shared['value']),
                         (['a', 'b'], 'repo-root'))
        self.assertEqual(basis(merged, 'hook-cwd', {'os': 'macOS'})['value'], 'repo-root')

    def test_claimed_findings_are_kept_but_never_shared(self):
        merged = merge([finding('a', 'repo-root', status='claimed')])
        self.assertEqual((merged['shared'], len(merged['unconfirmed'])), ([], 1))
        self.assertEqual(merged['unconfirmed'][0]['source'], 'a:verify')
        self.assertIsNone(basis(merged, 'hook-cwd', {}))

    def test_different_scopes_stay_conditional_and_nothing_is_dropped(self):
        merged = merge([finding('a', 'session-cwd', scope={'tool': 'Claude Code'}),
                        finding('b', '.agents', scope={'tool': 'Antigravity'})])
        self.assertEqual((merged['shared'], merged['conflicts']), ([], []))
        self.assertEqual(sorted((c['scope']['tool'], c['value']) for c in merged['conditional']),
                         [('Antigravity', '.agents'), ('Claude Code', 'session-cwd')])
        self.assertEqual(basis(merged, 'hook-cwd', {'tool': 'Antigravity', 'os': 'macOS'})['value'],
                         '.agents')
        self.assertIsNone(basis(merged, 'hook-cwd', {'tool': 'Codex CLI'}))
        self.assertIsNone(basis(merged, 'hook-cwd', {}))

    def test_same_value_under_different_scopes_is_not_promoted_to_everywhere(self):
        merged = merge([finding('a', 'ok', scope={'os': 'macOS'}),
                        finding('b', 'ok', scope={'os': 'Windows'})])
        self.assertEqual((merged['shared'], len(merged['conditional'])), ([], 2))
        self.assertIsNone(basis(merged, 'hook-cwd', {'os': 'Linux'}))

    def test_disagreement_under_overlapping_scope_is_a_conflict_and_blocks_use(self):
        merged = merge([finding('a', 'repo-root', scope={'os': 'macOS'}),
                        finding('b', 'session-cwd', scope={'tool': 'Claude Code'}),
                        finding('c', 'x', key='other')])
        self.assertEqual(len(merged['conflicts']), 1)
        self.assertEqual([f['line'] for f in merged['conflicts'][0]['findings']], ['a', 'b'])
        self.assertIsNone(basis(merged, 'hook-cwd', {'os': 'macOS', 'tool': 'Claude Code'}))
        self.assertEqual(basis(merged, 'other', {})['value'], 'x')

    def test_conflict_keeps_the_uninvolved_findings_as_conditional(self):
        merged = merge([finding('a', 'p', scope={'os': 'macOS'}),
                        finding('b', 'q', scope={'os': 'macOS'}),
                        finding('c', 'r', scope={'os': 'Windows'})])
        self.assertEqual([f['line'] for f in merged['conflicts'][0]['findings']], ['a', 'b'])
        self.assertEqual([c['value'] for c in merged['conditional']], ['r'])
        # Until the conflict is resolved the key is blocked, even where only r applies.
        self.assertIsNone(basis(merged, 'hook-cwd', {'os': 'Windows'}))
        self.assertEqual(merged['shared'], [])

    def test_disjoint_scopes_with_different_values_do_not_conflict(self):
        merged = merge([finding('a', 'p', scope={'os': 'macOS'}),
                        finding('b', 'q', scope={'os': 'Windows'})])
        self.assertEqual(merged['conflicts'], [])

    def test_findings_missing_source_time_or_scope_are_incomplete(self):
        bad = [finding('a', 'v', source=' '), finding('b', 'v', obtained_at='昨天'),
               dict(finding('c', 'v'), scope=None), finding('d', 'v', status='maybe'),
               finding('', 'v'), 'not-a-dict', finding('e', 'v', obtained_at=None)]
        merged = merge(bad)
        self.assertEqual(len(merged['incomplete']), 7)
        self.assertEqual(merged['shared'] + merged['conditional'] + merged['unconfirmed'], [])
        self.assertIsNone(basis(merged, 'hook-cwd', {}))


if __name__ == '__main__':
    unittest.main()
