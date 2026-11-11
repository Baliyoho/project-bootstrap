"""M2: the JSON Schemas accept the real index and spec and reject broken shapes.

Needs jsonschema: A4 (verify_v2) leaves this file out and lists it; `uv run pytest` runs it.
"""
import copy
import json
from pathlib import Path
import unittest

try:
    from project_bootstrap.schema_check import TARGETS, schema_errors
except ImportError as exc:  # jsonschema missing
    raise unittest.SkipTest('needs jsonschema (uv run pytest): %s' % exc)


def load(name):
    return json.loads(Path(TARGETS[name]).read_text(encoding='utf-8'))


class SchemaTests(unittest.TestCase):
    def test_real_files_fit(self):
        self.assertEqual(schema_errors('status', load('status')), [])
        self.assertEqual(schema_errors('mutants', load('mutants')), [])

    def test_status_index_rejects_broken_rows(self):
        base = load('status')
        row = base['requirements'][0]

        def broken(change):
            data = copy.deepcopy(base)
            change(data, data['requirements'][0])
            return schema_errors('status', data)
        cases = {
            'unknown result': lambda d, r: r.update(result='大概通過'),
            'missing next': lambda d, r: r.pop('next'),
            'extra key': lambda d, r: r.update(owner='me'),
            'bad id': lambda d, r: r.update(id='X1'),
            'absolute evidence path': lambda d, r: r.update(evidence=[{'path': '/etc/x', 'scope': 's'}]),
            'evidence without scope': lambda d, r: r.update(evidence=[{'path': 'a.py'}]),
            'bad date': lambda d, r: d.update(updated='11/11/2026'),
            'schema version': lambda d, r: d.update(schema=2),
            'part without scope': lambda d, r: r.update(parts={'a': {'result': '未驗證'}}),
        }
        self.assertTrue(row['id'])
        for name, change in cases.items():
            with self.subTest(case=name):
                self.assertNotEqual(broken(change), [])

    def test_mutation_spec_rejects_broken_groups(self):
        base = load('mutants')
        cases = {
            'repo test in a group': lambda g: g['tests'].append('tests.test_trail_repo'),
            'old module name': lambda g: g['tests'].append('experiments.v2.test_x'),
            'file outside the package': lambda g: g['mutants'][0].update(file='tools/verify_bootstrap.py'),
            'empty old text': lambda g: g['mutants'][0].update(old=''),
            'missing new': lambda g: g['mutants'][0].pop('new'),
            'no mutants': lambda g: g.update(mutants=[]),
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                data = copy.deepcopy(base)
                change(data['groups'][0])
                self.assertNotEqual(schema_errors('mutants', data), [])


if __name__ == '__main__':
    unittest.main()
