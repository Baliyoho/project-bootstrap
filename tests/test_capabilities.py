"""P2 slice 4 (F47): the capability matrix reports per surface and version, never substitutes."""

import json
import unittest

from project_bootstrap import capabilities as cap
from project_bootstrap.capabilities import MatrixError

SECRET = 'SYNTHETIC_probe_detail_do_not_print'


def synthetic():
    return {
        'schema': 1,
        'surfaces': {'a-cli': {'tool': 'A', 'label': 'A CLI'},
                     'a-app': {'tool': 'A', 'label': 'A App'},
                     'b': {'tool': 'B', 'label': 'B'}},
        'capabilities': {
            'hooks': {'label': 'Hooks', 'strict': False, 'impact': 'no reminder', 'alternative': 'do it by hand'},
            'docs-only': {'label': 'Docs', 'strict': False, 'impact': 'x', 'alternative': 'y'},
            'gate': {'label': 'Gate', 'strict': True, 'impact': 'cannot block', 'alternative': 'compat mode'}},
        'cells': [
            {'id': 'a-cli/hooks', 'capability': 'hooks', 'surfaces': ['a-cli'], 'status': 'supported',
             'basis': 'tested', 'tested': ['1.2.0'], 'text': 'yes', 'evidence': 'measured'},
            {'id': 'a/hooks-summary', 'capability': 'hooks', 'surfaces': ['a-cli', 'a-app'],
             'summary': True, 'text': 'CLI yes, App untested'},
            {'id': 'a/docs-only', 'capability': 'docs-only', 'surfaces': ['a-cli', 'a-app'],
             'status': 'supported', 'basis': 'docs', 'since': '1.1', 'text': 'docs say yes'},
            {'id': 'b/hooks', 'capability': 'hooks', 'surfaces': ['b'], 'status': 'missing',
             'basis': 'docs', 'text': 'no'},
            {'id': 'a-cli/gate', 'capability': 'gate', 'surfaces': ['a-cli'], 'status': 'supported',
             'basis': 'tested', 'tested': ['1.2.0']},
        ],
        'tables': {
            'main': {'header': ['', {'surface': 'a-cli'}, 'A'],
                     'rows': [[{'capability': 'hooks'}, {'cell': 'a-cli/hooks'}, {'cell': 'a/hooks-summary'}],
                              [{'capability': 'docs-only'}, {'cell': 'a/docs-only'}, {'cell': 'b/hooks'}]]},
            'evidence': {'header': ['Surface', 'Proof'],
                         'rows': [['A CLI', {'cell': 'a-cli/hooks', 'field': 'evidence'}]]}},
    }


def rows(result):
    return {row['capability']: row for row in result['rows']}


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.data = cap.validate(synthetic())

    def test_exact_surface_and_version_only(self):
        same = rows(cap.report(self.data, 'a-cli', '1.2.0'))
        self.assertEqual(same['hooks']['state'], 'supported')
        newer = rows(cap.report(self.data, 'a-cli', '1.3.0'))
        self.assertEqual((newer['hooks']['state'], newer['hooks']['declared']), ('unverified', 'other-version'))
        none = rows(cap.report(self.data, 'a-cli'))
        self.assertEqual(none['hooks']['state'], 'unverified')
        # The summary cell names a-app, but it is prose, not evidence.
        app = rows(cap.report(self.data, 'a-app', '1.2.0'))
        self.assertEqual((app['hooks']['state'], app['hooks']['declared']), ('unverified', 'no-evidence'))
        self.assertNotIn('cell', app['hooks'])

    def test_docs_never_count_as_verified(self):
        later = rows(cap.report(self.data, 'a-cli', '1.5'))
        self.assertEqual((later['docs-only']['state'], later['docs-only']['declared']), ('unverified', 'documented'))
        older = rows(cap.report(self.data, 'a-cli', '1.0.9'))
        self.assertEqual(older['docs-only']['state'], 'missing')
        odd = rows(cap.report(self.data, 'a-cli', 'nightly'))
        self.assertEqual(odd['docs-only']['state'], 'unverified')
        self.assertEqual(rows(cap.report(self.data, 'b'))['hooks']['state'], 'missing')

    def test_gaps_say_impact_and_alternative(self):
        result = cap.report(self.data, 'b')
        self.assertEqual(result['gaps'], ['hooks', 'docs-only', 'gate'])
        hooks = rows(result)['hooks']
        self.assertEqual((hooks['impact'], hooks['alternative']), ('no reminder', 'do it by hand'))
        supported = rows(cap.report(self.data, 'a-cli', '1.2.0'))['hooks']
        self.assertNotIn('impact', supported)

    def test_strict_needs_a_passing_probe_this_run(self):
        declared = cap.report(self.data, 'a-cli', '1.2.0')
        self.assertEqual(rows(declared)['gate']['state'], 'unverified')
        self.assertFalse(declared['strict_ready'])
        passed = cap.report(self.data, 'a-cli', '1.2.0', {'gate': lambda: True})
        self.assertTrue(passed['strict_ready'])
        self.assertEqual(rows(passed)['gate']['state'], 'supported')
        for probe in (lambda: False, lambda: 'yes', lambda: 1):
            result = cap.report(self.data, 'a-cli', '1.2.0', {'gate': probe})
            self.assertFalse(result['strict_ready'])
            self.assertEqual(rows(result)['gate']['state'], 'missing')

    def test_probe_failure_overrides_the_matrix(self):
        def boom():
            raise RuntimeError(SECRET)
        result = cap.report(self.data, 'a-cli', '1.2.0', {'hooks': boom, 'gate': lambda: True})
        hooks = rows(result)['hooks']
        self.assertEqual((hooks['state'], hooks['probe']), ('missing', 'error'))
        self.assertNotIn(SECRET, json.dumps(result))
        self.assertTrue(result['strict_ready'])

    def test_unknown_surface_or_probe_is_refused(self):
        with self.assertRaises(MatrixError):
            cap.report(self.data, 'c')
        with self.assertRaises(MatrixError):
            cap.report(self.data, 'a-cli', '1.2.0', {'nope': lambda: True})


class ValidateTests(unittest.TestCase):
    def broken(self, change):
        data = synthetic()
        change(data)
        with self.assertRaises(MatrixError):
            cap.validate(data)

    def cell(self, data, cid):
        return next(c for c in data['cells'] if c['id'] == cid)

    def test_synthetic_is_valid(self):
        cap.validate(synthetic())

    def test_two_cells_for_one_surface(self):
        def change(d):
            extra = dict(self.cell(d, 'b/hooks'), id='b/hooks-2')
            del extra['text']
            d['cells'].append(extra)
        self.broken(change)

    def test_unknown_references(self):
        self.broken(lambda d: self.cell(d, 'b/hooks').update(surfaces=['z']))
        self.broken(lambda d: self.cell(d, 'b/hooks').update(capability='z'))
        self.broken(lambda d: d['tables']['main']['header'].__setitem__(1, {'surface': 'z'}))
        self.broken(lambda d: d['tables']['main']['rows'][0].__setitem__(1, {'cell': 'z'}))

    def test_basis_rules(self):
        self.broken(lambda d: self.cell(d, 'a-cli/hooks').update(tested=[]))
        self.broken(lambda d: self.cell(d, 'a-cli/hooks').update(tested=['latest']))
        self.broken(lambda d: self.cell(d, 'a-cli/hooks').update(since='1.0'))
        self.broken(lambda d: self.cell(d, 'b/hooks').update(tested=['1.0']))
        self.broken(lambda d: self.cell(d, 'b/hooks').update(basis='guess'))
        self.broken(lambda d: self.cell(d, 'b/hooks').update(status='maybe'))
        self.broken(lambda d: self.cell(d, 'a/hooks-summary').update(status='supported'))
        self.broken(lambda d: self.cell(d, 'a/hooks-summary').update(summary='yes'))

    def test_every_fact_rendered_once(self):
        self.broken(lambda d: d['tables']['main']['rows'][1].__setitem__(2, 'literal'))
        self.broken(lambda d: d['tables']['evidence']['rows'].append(['again', {'cell': 'a-cli/hooks', 'field': 'evidence'}]))
        self.broken(lambda d: d['tables']['main']['rows'][0].append('extra column'))
        self.broken(lambda d: self.cell(d, 'b/hooks').update(text='a | b'))

    def test_one_strict_capability_is_required(self):
        self.broken(lambda d: d['capabilities']['gate'].update(strict=False))
        self.broken(lambda d: d['capabilities']['gate'].update(strict='true'))

    def test_unknown_keys(self):
        self.broken(lambda d: self.cell(d, 'b/hooks').update(verified=True))
        self.broken(lambda d: d.update(extra=1))


class RenderTests(unittest.TestCase):
    def test_table_spacing(self):
        lines = cap.render_table(cap.validate(synthetic()), 'main')
        self.assertEqual(lines, ['| | A CLI | A |', '|---|---|---|',
                                 '| Hooks | yes | CLI yes, App untested |',
                                 '| Docs | docs say yes | no |'])

    def test_every_table_used_once(self):
        data = cap.validate(synthetic())
        prose = 'x\n<!-- kit-table: main -->\ny\n<!-- kit-table: evidence -->\n'
        self.assertIn('| A CLI | measured |', cap.render_tables(prose, data))
        with self.assertRaises(MatrixError):
            cap.render_tables('<!-- kit-table: main -->\n', data)
        with self.assertRaises(MatrixError):
            cap.render_tables(prose + '<!-- kit-table: main -->\n', data)

if __name__ == '__main__':
    unittest.main()
