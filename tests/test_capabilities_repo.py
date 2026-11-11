"""P2 slice 4 on this repo: the kit tables are rendered from src/kit/capabilities.json."""

import copy
from pathlib import Path
import sys
import unittest

from project_bootstrap import capabilities as cap

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import build_kit  # noqa: E402


def rows(result):
    return {row['capability']: row for row in result['rows']}


class KitBuildTests(unittest.TestCase):
    def test_build_refuses_an_unexpanded_table(self):
        with self.assertRaises(build_kit.KitError):
            build_kit.build('a\n<!-- kit-table: tools -->\n', {})

    def test_bad_matrix_stops_the_kit_build(self):
        with self.assertRaises(build_kit.KitError):
            build_kit.expand_tables('<!-- kit-table: main -->\n', '{"schema": 2}')


class RepoMatrixTests(unittest.TestCase):
    def setUp(self):
        self.data = cap.read_matrix()

    def test_kit_tables_come_from_the_matrix(self):
        raw, _ = build_kit.load_raw()
        self.assertEqual(raw.count('<!-- kit-table: '), len(self.data['tables']))
        prose, files = build_kit.load_source()
        built = build_kit.build(prose, files)
        self.assertEqual(built, (ROOT / 'PROJECT-BOOTSTRAP.md').read_text(encoding='utf-8'))
        changed = copy.deepcopy(self.data)
        next(c for c in changed['cells'] if c['id'] == 'codex-cli/hooks')['text'] = '✅ 改過'
        self.assertNotEqual(build_kit.build(cap.render_tables(raw, changed), files), built)

    def test_no_surface_is_strict_ready_yet(self):
        for surface in self.data['surfaces']:
            result = cap.report(self.data, surface, '0')
            self.assertFalse(result['strict_ready'], surface)
            self.assertIn('managed-write-gate', result['gaps'])

    def test_antigravity_surfaces_are_not_one_product(self):
        hooks = {s: rows(cap.report(self.data, s, v))['hooks']['state'] for s, v in
                 (('antigravity-cli', '1.4.12'), ('antigravity-2', '2.28.2'),
                  ('antigravity-ide', '1.107.0'), ('antigravity-sdk', None))}
        self.assertEqual(hooks, {'antigravity-cli': 'supported', 'antigravity-2': 'supported',
                                 'antigravity-ide': 'missing', 'antigravity-sdk': 'unverified'})


if __name__ == '__main__':
    unittest.main()
