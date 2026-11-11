"""P1: the development layout agrees with what verify_bootstrap.py reads.

verify_bootstrap.py must run on Python 3.8 without uv, so it reads pyproject.toml
and uv.lock with a small hand-written parser. This test reads both with tomllib
and checks the two views agree, so the simple parser cannot drift unnoticed.
It is a unittest case so tools/verify_v2.py (stdlib only, run by A4) runs it too.
"""
from pathlib import Path
import sys
import unittest

try:
    import tomllib
except ImportError:  # Python < 3.11: verify_bootstrap.py still supports it
    tomllib = None

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import verify_bootstrap  # noqa: E402


def text(name):
    return (ROOT / name).read_text(encoding='utf-8')


@unittest.skipIf(tomllib is None, 'tomllib needs Python 3.11+')
class LayoutTests(unittest.TestCase):
    def load(self, name):
        return tomllib.loads(text(name))

    def test_package_imports_from_src(self):
        import project_bootstrap
        self.assertEqual(Path(project_bootstrap.__file__).parent, ROOT / 'src' / 'project_bootstrap')

    def test_simple_parser_matches_tomllib(self):
        data = self.load('pyproject.toml')
        licenses = verify_bootstrap.p1_section(text('pyproject.toml'), 'tool.project-bootstrap.licenses')
        self.assertEqual({k: v.strip('"') for k, v in licenses.items()},
                         data['tool']['project-bootstrap']['licenses'])
        self.assertEqual(verify_bootstrap.p1_section(text('pyproject.toml'), 'project')['requires-python']
                         .strip('"'), data['project']['requires-python'])

    def test_licenses_cover_exactly_the_locked_registry_packages(self):
        registry = {p['name'] for p in self.load('uv.lock')['package'] if 'registry' in p['source']}
        self.assertEqual(set(self.load('pyproject.toml')['tool']['project-bootstrap']['licenses']), registry)

    def test_every_locked_artifact_has_a_sha256(self):
        for package in self.load('uv.lock')['package']:
            if 'registry' not in package['source']:
                continue
            artifacts = package.get('wheels', []) + ([package['sdist']] if 'sdist' in package else [])
            self.assertTrue(artifacts, package['name'])
            self.assertTrue(all(a['hash'].startswith('sha256:') for a in artifacts), package['name'])

    def test_verifier_check_passes_on_this_repo(self):
        sources = {p.relative_to(ROOT).as_posix(): p.read_text(encoding='utf-8')
                   for folder in verify_bootstrap.P1_STDLIB_ONLY
                   for p in sorted((ROOT / folder).glob('*.py')) if not p.name.startswith('test_')}
        tests = {p.relative_to(ROOT).as_posix(): p.read_text(encoding='utf-8')
                 for p in sorted((ROOT / 'tests').glob('test_*.py'))}
        self.assertEqual(verify_bootstrap.p1_layout_problems(
            text('pyproject.toml'), text('uv.lock'), sources, tests), [])


if __name__ == '__main__':
    unittest.main()
