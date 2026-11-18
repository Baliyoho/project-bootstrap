"""P2 slice 1 on this repo: owners.json agrees with src/kit, and sync_project.py reads it.

Since P2 slice 5 sync_project.py has no file lists of its own; they come from
owners.json. The kinds with a dedicated handler (region, key, lines, wiring)
must match what the handlers know, or the tool refuses to start.
"""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import types
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
        for path in sync_project.PARTIAL:
            expected[path] = 'lines'
        for path in sync_project.INSTANCE:
            expected[path] = 'seed'
        self.assertEqual({path: entry['update'] for path, entry in owners().items()}, expected)

    def test_sync_project_refuses_an_owner_entry_it_cannot_handle(self):
        source = (ROOT / 'tools' / 'sync_project.py').read_text(encoding='utf-8')
        line = "OWNERS_FILE = ROOT / 'src' / 'kit' / 'owners.json'"
        self.assertEqual(source.count(line), 1)
        data = json.loads((ROOT / 'src' / 'kit' / 'owners.json').read_text(encoding='utf-8'))
        variants = {
            'extra lines file': ('NOTES.md', {'owner': 'project', 'update': 'lines'}),
            'region moved': ('tools/check_docs.py', {'owner': 'core', 'update': 'whole'}),
            'skill entry gone': ('.claude/skills/handoff/SKILL.md', None),
        }
        with tempfile.TemporaryDirectory() as folder:
            for label, (path, entry) in variants.items():
                files = dict(data['files'])
                if entry is None:
                    del files[path]
                else:
                    files[path] = entry
                owners_file = Path(folder) / 'owners.json'
                owners_file.write_text(json.dumps({'schema': 1, 'files': files}), encoding='utf-8')
                module = types.ModuleType('sync_variant')
                module.__file__ = str(ROOT / 'tools' / 'sync_project.py')
                text = source.replace(line, 'OWNERS_FILE = pathlib.Path(%r)' % str(owners_file))
                with self.assertRaises(SystemExit, msg=label):
                    exec(compile(text, module.__file__, 'exec'), module.__dict__)

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
