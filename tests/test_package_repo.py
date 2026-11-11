"""P2 slice 1 on this repo: owners.json agrees with src/kit and with sync_project.py.

Until sync_project.py becomes the migrator (P2 slice 5) it keeps its own file
lists. This test keeps the two views from drifting apart.
"""
from pathlib import Path
import shutil
import sys
import unittest

from project_bootstrap import package

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import build_kit  # noqa: E402
import sync_project  # noqa: E402


def owners():
    return package.load_owners((ROOT / 'src' / 'kit' / 'owners.json').read_text(encoding='utf-8'))


class RepoPackageTests(unittest.TestCase):
    def test_owners_cover_every_template(self):
        _, files = build_kit.load_source()
        self.assertEqual(set(owners()), set(files))

    def test_owners_agree_with_sync_project(self):
        expected = {}
        for path in sync_project.WHOLE:
            expected[path] = 'whole'
        expected[sync_project.SURGICAL] = 'region'
        for path in sync_project.WIRING:
            expected[path] = 'wiring'
        expected[sync_project.AG_WIRING] = 'key'
        for path in sync_project.PARTIAL:
            expected[path] = 'lines'
        for path in sync_project.INSTANCE:
            expected[path] = 'seed'
        self.assertEqual({path: entry['update'] for path, entry in owners().items()}, expected)

    def test_skill_and_hook_scripts_are_core(self):
        table = owners()
        for path in sync_project.SKILL_PARTS + (sync_project.SKILL_ENTRY,):
            self.assertEqual(table[path]['owner'], 'core', path)
        for script in sync_project.OWNED_SCRIPTS:
            self.assertEqual(table['.claude/hooks/' + script]['owner'], 'core', script)

    def test_repo_package_builds_clean_and_matches_version(self):
        prose, files = build_kit.load_source()
        folder, manifest = package.build(prose, files, owners(), build_kit.build(prose, files))
        try:
            self.assertEqual(package.check(folder), [])
        finally:
            shutil.rmtree(folder, ignore_errors=True)
        self.assertEqual(manifest['version'], (ROOT / 'VERSION').read_text(encoding='utf-8').strip())


if __name__ == '__main__':
    unittest.main()
