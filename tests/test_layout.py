"""The development layout agrees with what verify_bootstrap.py reads.

verify_bootstrap.py reads pyproject.toml and uv.lock with tomllib (Python 3.12+,
the same floor as the installer). It is a unittest case so tools/run_tests.py
(stdlib only, run by A4) runs it too.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import verify_bootstrap  # noqa: E402


def text(name):
    return (ROOT / name).read_text(encoding='utf-8')


class LayoutTests(unittest.TestCase):
    def test_package_imports_from_src(self):
        import project_bootstrap
        self.assertEqual(Path(project_bootstrap.__file__).parent, ROOT / 'src' / 'project_bootstrap')

    def test_verifier_check_passes_on_this_repo(self):
        sources = {p.relative_to(ROOT).as_posix(): p.read_text(encoding='utf-8')
                   for folder in verify_bootstrap.DEV_STDLIB_ONLY
                   for p in sorted((ROOT / folder).glob('*.py')) if not p.name.startswith('test_')}
        tests = {p.relative_to(ROOT).as_posix(): p.read_text(encoding='utf-8')
                 for p in sorted((ROOT / 'tests').glob('test_*.py'))}
        self.assertEqual(verify_bootstrap.dev_layout_problems(
            text('pyproject.toml'), text('uv.lock'), sources, tests), [])


if __name__ == '__main__':
    unittest.main()
