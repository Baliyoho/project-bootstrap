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


def resolution(value, *lines, scope=None, key='hook-cwd', **extra):
    item = {'key': key, 'value': value, 'scope': {} if scope is None else scope,
            'decided_by': 'user', 'decided_at': '2026-11-10T10:00:00+08:00',
            'reason': 'b reran the probe from a subdirectory',
            'cites': [{'line': line, 'source': f'{line}:verify'} for line in lines]}
    item.update(extra)
    return item


class ConflictResolutionTests(unittest.TestCase):
    CONFLICT = [finding('a', 'repo-root', scope={'os': 'macOS'}),
                finding('b', 'session-cwd', scope={'os': 'macOS'}),
                finding('c', 'session-cwd', scope={'os': 'macOS'}),
                finding('d', '.agents', scope={'os': 'Windows'})]

    def test_recorded_decision_settles_the_conflict_and_keeps_the_overruled_finding(self):
        merged = merge(self.CONFLICT, [resolution('session-cwd', 'a', 'b', 'c',
                                                  scope={'os': 'macOS'})])
        self.assertEqual((merged['conflicts'], merged['invalid_resolutions']), ([], []))
        done = merged['resolved'][0]
        self.assertEqual(([f['line'] for f in done['kept']], [f['line'] for f in done['overruled']]),
                         (['b', 'c'], ['a']))
        self.assertEqual(done['decision'], {'decided_by': 'user',
                                            'decided_at': '2026-11-10T10:00:00+08:00',
                                            'reason': 'b reran the probe from a subdirectory'})
        relied = basis(merged, 'hook-cwd', {'os': 'macOS', 'tool': 'Codex CLI'})
        self.assertEqual((relied['value'], [s['line'] for s in relied['sources']]),
                         ('session-cwd', ['b', 'c']))
        self.assertEqual(relied['decision']['decided_by'], 'user')
        # The uninvolved finding is still usable where it applies, and carries no decision.
        windows = basis(merged, 'hook-cwd', {'os': 'Windows'})
        self.assertEqual(windows['value'], '.agents')
        self.assertNotIn('decision', windows)
        self.assertEqual(merged['shared'], [])

    def test_decision_scope_replaces_the_findings_scope_and_whole_key_can_become_shared(self):
        merged = merge(self.CONFLICT[:2], [resolution('session-cwd', 'a', 'b')])
        self.assertEqual(merged['shared'][0]['scope'], {})
        self.assertEqual(basis(merged, 'hook-cwd', {'os': 'Linux'})['value'], 'session-cwd')

    def test_a_conflicting_finding_that_arrived_later_reopens_the_conflict(self):
        later = self.CONFLICT + [finding('e', 'repo-root', scope={'os': 'macOS'})]
        merged = merge(later, [resolution('session-cwd', 'a', 'b', 'c')])
        self.assertEqual(merged['resolved'], [])
        self.assertEqual((merged['conflicts'][0]['reopened'],
                          [f['line'] for f in merged['conflicts'][0]['findings']]),
                         (True, ['a', 'b', 'c', 'e']))
        self.assertIsNone(basis(merged, 'hook-cwd', {'os': 'macOS'}))
        self.assertFalse(merge(self.CONFLICT)['conflicts'][0]['reopened'])

    def test_decisions_cannot_invent_values_or_cite_unknown_findings(self):
        cases = {
            'resolution-value-unsupported': resolution('somewhere-else', 'a', 'b', 'c'),
            'resolution-cites-unknown': resolution('session-cwd', 'a', 'b', 'c', 'z'),
            'resolution-incomplete': resolution('session-cwd', 'a', 'b', 'c', reason=' '),
        }
        incomplete = [resolution('session-cwd', 'a', 'b', 'c', decided_by=''),
                      resolution('session-cwd', 'a', 'b', 'c', decided_at='剛剛'),
                      dict(resolution('session-cwd', 'a', 'b', 'c'), scope=None),
                      resolution('session-cwd'), dict(resolution('x', 'a'), cites=['a'])]
        for code, bad in cases.items():
            with self.subTest(code=code):
                merged = merge(self.CONFLICT, [bad])
                self.assertEqual(merged['invalid_resolutions'], [{'key': 'hook-cwd', 'code': code}])
                self.assertEqual(len(merged['conflicts']), 1)
                self.assertEqual(merged['resolved'], [])
        for bad in incomplete:
            with self.subTest(bad=bad):
                merged = merge(self.CONFLICT, [bad])
                self.assertEqual(merged['invalid_resolutions'][0]['code'], 'resolution-incomplete')
                self.assertIsNone(basis(merged, 'hook-cwd', {'os': 'macOS'}))
        no_value = resolution('session-cwd', 'a', 'b', 'c')
        del no_value['value']
        self.assertEqual(merge(self.CONFLICT, [no_value])['invalid_resolutions'][0]['code'],
                         'resolution-value-unsupported')

    def test_resolutions_for_other_keys_or_without_conflict_change_nothing(self):
        plain = merge(self.CONFLICT)
        other = merge(self.CONFLICT, [resolution('session-cwd', 'a', 'b', 'c', key='other'),
                                      'not-a-dict'])
        self.assertEqual(plain, other)
        agreeing = [finding('a', 'v'), finding('b', 'v')]
        self.assertEqual(merge(agreeing, [resolution('v', 'a', 'b')])['resolved'], [])


if __name__ == '__main__':
    unittest.main()
