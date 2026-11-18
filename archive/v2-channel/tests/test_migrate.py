"""P2 slice 5: the migrator's decisions (decision Q25), on synthetic observations."""
import unittest

from project_bootstrap import migrate
from project_bootstrap.contracts import Denied

A, B, OLD, CUSTOM = 'a' * 64, 'b' * 64, 'c' * 64, 'd' * 64
PACKAGE = {'skill.md': A, 'hook.sh': B}
KNOWN = {'skill.md': {OLD, A}, 'hook.sh': {B}}
DIGEST = 'f' * 64


def row(observed, pointer=DIGEST, problems=(), merges=0, name='p'):
    return migrate.target(name, observed, PACKAGE, KNOWN, DIGEST, pointer, problems, merges)


def denied(test, code, call, *args):
    with test.assertRaises(Denied) as caught:
        call(*args)
    test.assertEqual(str(caught.exception), code)


class ClassifyTests(unittest.TestCase):
    def test_states(self):
        self.assertEqual(migrate.classify(('digest', A), A, {OLD}), 'current')
        self.assertEqual(migrate.classify(('digest', OLD), A, {OLD}), 'known')
        self.assertEqual(migrate.classify(('digest', CUSTOM), A, {OLD}), 'customised')
        self.assertEqual(migrate.classify('missing', A, {OLD}), 'missing')
        self.assertEqual(migrate.classify('unreadable', A, {OLD}), 'unreadable')

    def test_malformed_observations_are_refused(self):
        for bad in (None, 'gone', ('digest',), ('digest', A, 1), ('hash', A), ('eol', A), ('digest', 1),
                    ['digest', A]):
            denied(self, 'invalid-observation', migrate.classify, bad, A, set())


class TargetTests(unittest.TestCase):
    def test_known_and_missing_files_migrate(self):
        r = row({'skill.md': ('digest', OLD), 'hook.sh': 'missing'}, pointer=None, merges=2)
        self.assertEqual(r['action'], 'migrate')
        self.assertEqual((r['replace'], r['add'], r['merges']), (['skill.md'], ['hook.sh'], 2))
        self.assertEqual(r['files'], {'hook.sh': 'missing', 'skill.md': 'known'})
        self.assertNotIn('compare', r)

    def test_current_files_are_left_alone(self):
        r = row({'skill.md': ('digest', OLD), 'hook.sh': ('digest', B)})
        self.assertEqual((r['action'], r['replace'], r['add']), ('migrate', ['skill.md'], []))

    def test_a_customised_file_stops_the_project(self):
        r = row({'skill.md': ('digest', CUSTOM), 'hook.sh': ('digest', 'e' * 64)}, pointer=None)
        self.assertEqual(r['action'], 'manual')
        self.assertEqual(r['compare'], ['hook.sh', 'skill.md'])
        self.assertNotIn('replace', r)
        self.assertNotIn('add', r)

    def test_one_customised_file_among_known_ones_still_stops(self):
        r = row({'skill.md': ('digest', OLD), 'hook.sh': ('digest', CUSTOM)}, pointer=None)
        self.assertEqual((r['action'], r['compare']), ('manual', ['hook.sh']))

    def test_current_needs_every_file_no_merge_and_the_same_pointer(self):
        same = {'skill.md': ('digest', A), 'hook.sh': ('digest', B)}
        self.assertEqual(row(same)['action'], 'current')
        self.assertEqual(row(same, pointer=None)['action'], 'migrate')
        self.assertEqual(row(same, pointer='0' * 64)['action'], 'migrate')
        self.assertEqual(row(same, merges=1)['action'], 'migrate')
        self.assertEqual(row({'skill.md': ('digest', OLD), 'hook.sh': ('digest', B)})['action'], 'migrate')

    def test_problems_and_unreadable_files_fail(self):
        r = row({'skill.md': ('digest', A), 'hook.sh': ('digest', B)}, problems=['merge:x'])
        self.assertEqual((r['action'], r['problems']), ('failed', ['merge:x']))
        r = row({'skill.md': 'unreadable', 'hook.sh': ('digest', CUSTOM)})
        self.assertEqual((r['action'], r['problems']), ('failed', ['unreadable:skill.md']))
        self.assertEqual(r['compare'], ['hook.sh'])

    def test_observations_must_cover_the_package_exactly(self):
        denied(self, 'observation-mismatch', row, {'skill.md': ('digest', A)})
        denied(self, 'observation-mismatch', row,
               {'skill.md': ('digest', A), 'hook.sh': ('digest', B), 'x': 'missing'})


class ReportTests(unittest.TestCase):
    def twenty(self):
        same = {'skill.md': ('digest', A), 'hook.sh': ('digest', B)}
        rows, names = [], ['p%02d' % i for i in range(20)]
        for i, name in enumerate(names):
            if i < 12:
                rows.append(row({'skill.md': ('digest', OLD), 'hook.sh': ('digest', B)}, name=name))
            elif i < 15:
                rows.append(row(same, name=name))
            elif i < 17:
                rows.append(row({'skill.md': ('digest', CUSTOM), 'hook.sh': ('digest', B)}, name=name))
            elif i < 19:
                rows.append(migrate.excluded(name, 'archived'))
            else:
                rows.append(migrate.failed(name, 'not-found'))
        return names, rows

    def test_twenty_targets_each_listed_once(self):
        names, rows = self.twenty()
        result = migrate.report(names, rows)
        self.assertEqual([r['target'] for r in result['results']], names)
        self.assertEqual(result['targets'], 20)
        self.assertEqual(result['totals'], {'current': 3, 'migrate': 12, 'manual': 2,
                                            'failed': 1, 'excluded': 2})
        self.assertEqual(result['manual_prompts'], 2)
        self.assertFalse(result['ok'])

    def test_ok_only_without_failures_or_manual_work(self):
        names, rows = self.twenty()
        result = migrate.report(names[:15] + names[17:19], rows[:15] + rows[17:19])
        self.assertTrue(result['ok'])
        manual = migrate.report(names[:17], rows[:17])
        self.assertEqual((manual['ok'], manual['totals']['failed']), (False, 0))
        failed = migrate.report(names[19:], rows[19:])
        self.assertEqual((failed['ok'], failed['totals']['manual']), (False, 0))

    def test_missing_repeated_and_unrequested_targets_fail(self):
        names, rows = self.twenty()
        result = migrate.report(names[:3] + ['p00', 'ghost'], rows[:3] + [rows[0], row(
            {'skill.md': ('digest', A), 'hook.sh': ('digest', B)}, name='extra')])
        actions = [(r['target'], r['action'], r['problems']) for r in result['results']]
        self.assertEqual(actions[1:], [
            ('p01', 'migrate', []), ('p02', 'migrate', []),
            ('p00', 'failed', ['duplicate-target']), ('ghost', 'failed', ['no-result']),
            ('extra', 'failed', ['not-requested'])])
        self.assertEqual(actions[0], ('p00', 'failed', ['several-results']))
        self.assertEqual(result['targets'], 6)
        self.assertFalse(result['ok'])

    def test_rows_must_have_a_known_action(self):
        denied(self, 'invalid-row', migrate.report, ['p'], [{'target': 'p', 'action': 'skipped'}])


if __name__ == '__main__':
    unittest.main()
