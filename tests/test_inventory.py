"""F39: in-place edits are found per project; unknown is not clean; nothing is overwritten."""

from pathlib import Path
import tempfile
import unittest

from project_bootstrap.inventory import scan
from project_bootstrap.release import build_manifest

FILES = {'SKILL.md': b'skill\n', 'hook.sh': b'echo\n', 'notes.md': b'mine\n'}
OWNERS = {'SKILL.md': 'core', 'hook.sh': 'adapter', 'notes.md': 'project'}


class InventoryTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='bootstrap-v2-inventory-')
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.projects = {}
        for name in ('clean', 'edited', 'missing', 'project-only', 'unknown', 'unreadable'):
            root = self.base / name
            root.mkdir()
            for relative, data in FILES.items():
                (root / relative).write_bytes(data)
            self.projects[name] = (root, 'v1')
        self.manifest = build_manifest(self.base / 'clean', list(FILES), 'v1', 'formal')
        (self.base / 'edited/SKILL.md').write_bytes(b'loosened\n')
        (self.base / 'missing/hook.sh').unlink()
        (self.base / 'project-only/notes.md').write_bytes(b'changed is fine\n')
        self.projects['unknown'] = (self.base / 'unknown', 'v0')
        (self.base / 'unreadable/hook.sh').unlink()
        (self.base / 'unreadable/hook.sh').mkdir()

    def test_each_project_gets_a_state_and_per_file_detail(self):
        before = {p: p.read_bytes() for p in self.base.rglob('*') if p.is_file()}
        report = {row['project']: row for row in scan(self.projects, {'v1': self.manifest}, OWNERS)}
        self.assertEqual({k: v['state'] for k, v in report.items()},
                         {'clean': 'clean', 'edited': 'edited', 'missing': 'incomplete',
                          'project-only': 'clean', 'unknown': 'unknown-manifest',
                          'unreadable': 'incomplete'})
        self.assertEqual(report['edited']['files'], {'SKILL.md': 'edited', 'hook.sh': 'ok'})
        self.assertEqual(report['missing']['files']['hook.sh'], 'missing')
        self.assertEqual(report['unreadable']['files']['hook.sh'], 'unreadable')
        self.assertNotIn('notes.md', report['clean']['files'])
        self.assertEqual({p: p.read_bytes() for p in self.base.rglob('*') if p.is_file()}, before)

    def test_edit_wins_over_missing_and_empty_release_is_not_clean(self):
        (self.base / 'edited/hook.sh').unlink()
        row = scan({'e': self.projects['edited']}, {'v1': self.manifest}, OWNERS)[0]
        self.assertEqual(row['state'], 'edited')
        none = scan({'c': self.projects['clean']}, {'v1': self.manifest}, {})[0]
        self.assertEqual(none['state'], 'nothing-to-check')


if __name__ == '__main__':
    unittest.main()
