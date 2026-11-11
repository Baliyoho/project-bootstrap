"""P2 slice 1: package format, ownership and package checks on synthetic sources."""
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from project_bootstrap import package
from project_bootstrap.contracts import Denied

PROSE = '# kit\n\n> 版本：**2026-11-11.3**（測試）\n'
FILES = {
    '.claude/skills/handoff/SKILL.md': 'skill\n',
    '.claude/hooks/check.sh': '#!/bin/sh\necho ok\n',
    '.claude/settings.json': '{}\n',
    'tools/check_docs.py': 'print(1)\n',
    'AGENTS.md': '# agents\n',
    'HANDOFF.md': '# handoff\n',
}
OWNERS = {
    '.claude/skills/handoff/SKILL.md': {'owner': 'core', 'update': 'whole'},
    '.claude/hooks/check.sh': {'owner': 'adapter', 'update': 'whole'},
    '.claude/settings.json': {'owner': 'adapter', 'update': 'wiring'},
    'tools/check_docs.py': {'owner': 'core', 'update': 'region'},
    'AGENTS.md': {'owner': 'project', 'update': 'seed'},
    'HANDOFF.md': {'owner': 'project', 'update': 'lines'},
}


def owners_text(files=None, schema=1):
    return json.dumps({'schema': schema, 'files': OWNERS if files is None else files})


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.made = []

    def tearDown(self):
        for folder in self.made:
            shutil.rmtree(folder, ignore_errors=True)

    def build(self, files=FILES, owners=OWNERS, prose=PROSE):
        folder, manifest = package.build(prose, files, owners, 'kit text')
        self.made.append(folder)
        return folder, manifest

    def scratch(self):
        folder = tempfile.mkdtemp(prefix='package-test-')
        self.made.append(folder)
        return Path(folder)

    def test_build_is_checked_and_reproducible(self):
        folder, manifest = self.build()
        self.assertEqual(package.check(folder), [])
        self.assertEqual(manifest['kind'], 'debug')
        self.assertEqual(manifest['version'], '2026-11-11.3')
        self.assertEqual(set(manifest['components']), set(FILES))
        self.assertEqual(manifest['owners'], OWNERS)
        self.assertEqual(manifest['executable'], ['.claude/hooks/check.sh'])
        self.assertEqual(len(manifest['kit']), 64)
        on_disk = json.loads((Path(folder) / package.MANIFEST).read_text(encoding='utf-8'))
        self.assertEqual(on_disk, manifest)
        _, again = self.build()
        self.assertEqual(package.digest(again), package.digest(manifest))

    def test_modes(self):
        folder, _ = self.build()
        self.assertEqual(os.stat(folder).st_mode & 0o777, 0o755)
        self.assertEqual(os.stat(Path(folder) / '.claude/hooks/check.sh').st_mode & 0o777, 0o755)
        self.assertEqual(os.stat(Path(folder) / 'AGENTS.md').st_mode & 0o777, 0o644)

    def test_changing_only_a_hook_changes_the_digest(self):
        _, before = self.build()
        changed = dict(FILES, **{'.claude/hooks/check.sh': '#!/bin/sh\necho changed\n'})
        _, after = self.build(files=changed)
        self.assertEqual(before['version'], after['version'])
        self.assertNotEqual(package.digest(before), package.digest(after))

    def test_ownership_change_changes_the_digest(self):
        _, before = self.build()
        owners = dict(OWNERS, **{'AGENTS.md': {'owner': 'project', 'update': 'lines'}})
        _, after = self.build(owners=owners)
        self.assertNotEqual(package.digest(before), package.digest(after))

    def test_kit_text_is_recorded(self):
        _, one = self.build()
        folder, other = package.build(PROSE, FILES, OWNERS, 'other kit text')
        self.made.append(folder)
        self.assertNotEqual(one['kit'], other['kit'])

    def test_unknown_ownership_stops(self):
        files = dict(FILES, **{'NEW.md': 'new\n'})
        with self.assertRaisesRegex(Denied, '^unknown-owner:NEW.md$'):
            package.build(PROSE, files, OWNERS, '')
        owners = dict(OWNERS, **{'GONE.md': {'owner': 'project', 'update': 'seed'}})
        with self.assertRaisesRegex(Denied, '^owner-without-file:GONE.md$'):
            package.build(PROSE, FILES, owners, '')

    def test_reserved_manifest_path(self):
        files = dict(FILES, **{package.MANIFEST: '{}\n'})
        owners = dict(OWNERS, **{package.MANIFEST: {'owner': 'project', 'update': 'seed'}})
        with self.assertRaisesRegex(Denied, '^reserved-path:'):
            package.build(PROSE, files, owners, '')

    def test_missing_version_line(self):
        with self.assertRaisesRegex(Denied, '^no-version-line$'):
            package.build('# kit\n版本：2026-11-11\n', FILES, OWNERS, '')

    def test_load_owners(self):
        self.assertEqual(package.load_owners(owners_text()), OWNERS)
        bad = [
            'not json',
            json.dumps([]),
            owners_text(schema=2),
            json.dumps({'schema': 1, 'files': OWNERS, 'extra': 1}),
            owners_text(files={}),
            owners_text(files=[]),
        ]
        for text in bad:
            with self.subTest(text=text[:40]), self.assertRaisesRegex(Denied, '^invalid-owners$'):
                package.load_owners(text)
        entries = [
            {'owner': 'project', 'update': 'whole'},
            {'owner': 'core', 'update': 'seed'},
            {'owner': 'adapter', 'update': 'region'},
            {'owner': 'core', 'update': 'wiring'},
            {'owner': 'vendor', 'update': 'whole'},
            {'owner': 'core'},
            {'owner': 'core', 'update': 'whole', 'note': 'x'},
            'core',
        ]
        for entry in entries:
            with self.subTest(entry=entry), self.assertRaisesRegex(Denied, '^invalid-owner:A$'):
                package.load_owners(owners_text(files={'A': entry}))

    def test_check_finds_broken_packages(self):
        cases = {
            'digest:AGENTS.md': lambda root: (root / 'AGENTS.md').write_text('edited\n'),
            'missing:AGENTS.md': lambda root: (root / 'AGENTS.md').unlink(),
            'extra:stray.txt': lambda root: (root / 'stray.txt').write_text('x'),
            'mode:.claude/hooks/check.sh': lambda root: (root / '.claude/hooks/check.sh').chmod(0o644),
            'mode:AGENTS.md': lambda root: (root / 'AGENTS.md').chmod(0o755),
            'symlink:link': lambda root: (root / 'link').symlink_to(root / 'AGENTS.md'),
        }
        for expected, damage in cases.items():
            with self.subTest(expected=expected):
                folder, _ = self.build()
                damage(Path(folder))
                self.assertIn(expected, package.check(folder))

    def test_check_finds_bad_manifests(self):
        folder, manifest = self.build()
        path = Path(folder) / package.MANIFEST
        path.write_text('{', encoding='utf-8')
        self.assertEqual(package.check(folder), ['manifest-unreadable'])
        path.write_text('[]', encoding='utf-8')
        self.assertEqual(package.check(folder), ['manifest-invalid'])
        dropped = dict(manifest, owners={k: v for k, v in manifest['owners'].items() if k != 'AGENTS.md'})
        path.write_text(json.dumps(dropped), encoding='utf-8')
        self.assertIn('owners-mismatch', package.check(folder))
        wrong = dict(manifest, owners=dict(manifest['owners'], **{'AGENTS.md': {'owner': 'core', 'update': 'seed'}}))
        path.write_text(json.dumps(wrong), encoding='utf-8')
        self.assertIn('invalid-owner:AGENTS.md', package.check(folder))
        unlisted = dict(manifest, components=dict(manifest['components'], **{'AGENTS.md': '0' * 64}))
        path.write_text(json.dumps(unlisted), encoding='utf-8')
        self.assertIn('digest:AGENTS.md', package.check(folder))

    def test_install_into_absent_and_over_earlier_package(self):
        out = self.scratch() / 'nested' / 'package'
        folder, manifest = self.build()
        package.install(folder, out)
        self.assertFalse(Path(folder).exists())
        self.assertEqual(package.check(out), [])
        (out / 'AGENTS.md').write_text('edited earlier package\n')
        newer, _ = self.build()
        package.install(newer, out)
        self.assertEqual(package.check(out), [])

    def test_install_refuses(self):
        base = self.scratch()
        plain = base / 'plain'
        plain.mkdir()
        (plain / 'keep.txt').write_text('mine')
        foreign = base / 'foreign'
        folder, _ = self.build()
        package.install(folder, foreign)
        (foreign / 'notes.txt').write_text('mine')
        link = base / 'link'
        link.symlink_to(plain)
        cases = {plain: '^out-not-a-package$', foreign: '^out-has-other-files$', link: '^out-is-symlink$'}
        for out, error in cases.items():
            with self.subTest(out=out.name):
                folder, _ = self.build()
                with self.assertRaisesRegex(Denied, error):
                    package.install(folder, out)
                self.assertTrue(Path(folder).exists())
        self.assertEqual((plain / 'keep.txt').read_text(), 'mine')
        self.assertEqual((foreign / 'notes.txt').read_text(), 'mine')

    def test_install_refuses_a_broken_package(self):
        folder, _ = self.build()
        (Path(folder) / 'AGENTS.md').write_text('edited\n')
        out = self.scratch() / 'out'
        with self.assertRaisesRegex(Denied, '^bad-package:digest:AGENTS.md$'):
            package.install(folder, out)
        self.assertFalse(out.exists())

    def test_whole_owned(self):
        _, manifest = self.build()
        self.assertEqual(package.whole_owned(manifest), {
            '.claude/skills/handoff/SKILL.md': 'core', '.claude/hooks/check.sh': 'adapter'})


if __name__ == '__main__':
    unittest.main()
