"""F47 on this repo: the real package carries the matrix, and a project seeded from it passes every install check."""

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from project_bootstrap import capabilities, package, pointer, selftest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import build_package  # noqa: E402


class RepoSelftestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        folder, cls.manifest = build_package.build_once()
        cls.digest = package.digest(cls.manifest)
        package.install(folder, cls.tmp / 'cache' / cls.digest)
        cls.project = cls.tmp / 'project'
        source = cls.tmp / 'cache' / cls.digest
        for relative in cls.manifest['components']:
            target = cls.project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / relative, target)
        (cls.project / pointer.POINTER).parent.mkdir(parents=True)
        (cls.project / pointer.POINTER).write_text(json.dumps(
            {'schema': 1, 'channel': 'beta', 'installed': cls.digest, 'exception': None}), encoding='utf-8')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def test_package_carries_the_source_matrix(self):
        self.assertEqual(capabilities.from_manifest(self.manifest), capabilities.read_matrix())
        self.assertEqual(package.check(self.tmp / 'cache' / self.digest), [])

    def test_every_surface_with_wiring_passes_on_a_seeded_project(self):
        home = self.tmp / 'empty-home'
        for surface, platform in [(s, p) for s in selftest.SKILLS for p in selftest.PLATFORMS]:
            result = selftest.run(surface, self.project, self.tmp / 'cache', version='0', home=home,
                                  platform=platform)
            self.assertEqual(result['matrix'], 'installed ' + self.digest)
            failed = {r['capability']: r['why'] for r in result['rows'] if r['check'] == 'fail'}
            self.assertEqual(failed, {}, surface)
            self.assertFalse(result['strict_ready'], surface)
            self.assertNotIn('checks_without_capability', result)

    def test_this_repo_is_the_declared_exception(self):
        # AGENTS.md: this repo wires its own repo-*.sh and has no project skill. The
        # self-test says so instead of reading the global skill as the kit's wiring.
        checks = selftest.install_checks('claude-code', ROOT, self.tmp / 'empty-home')
        self.assertEqual((checks['hooks']['ok'], checks['loads-skill']['ok']), (False, False))
        self.assertTrue(checks['reads-agents-md']['ok'])


if __name__ == '__main__':
    unittest.main()
