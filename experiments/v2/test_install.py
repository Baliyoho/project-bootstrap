"""F17: dry run for empty and existing projects; existing content is never overwritten."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.v2.contracts import Denied
from experiments.v2 import install
from experiments.v2.install import apply, plan

PACKAGE = {'AGENTS.md': b'# AGENTS\n', 'HANDOFF.md': b'# HANDOFF\n',
           '.gitignore': b'.env\n*.key\n', '.claude/hooks/git-freshness.sh': b'echo hi\n'}


class InstallTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='bootstrap-v2-install-')
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.home = self.base / 'home'
        self.home.mkdir()
        self.target = self.base / '新 專案'
        self.target.mkdir()

    def snapshot(self):
        return {str(p.relative_to(self.target)): p.read_bytes()
                for p in self.target.rglob('*') if p.is_file()}

    def denied(self, code, call, *args, **kwargs):
        with self.assertRaises(Denied) as caught:
            call(*args, **kwargs)
        self.assertEqual(str(caught.exception), code)

    def test_empty_folder_dry_run_writes_nothing_then_creates_everything(self):
        result = plan(self.target, PACKAGE, home=self.home)
        self.assertEqual((result['existing_project'], self.snapshot()), (False, {}))
        self.assertEqual({a['action'] for a in result['actions']}, {'create'})
        self.assertEqual(sorted(apply(self.target, PACKAGE, result, home=self.home)), sorted(PACKAGE))
        self.assertEqual(self.snapshot(), PACKAGE)
        again = plan(self.target, PACKAGE, home=self.home)
        self.assertEqual({a['action'] for a in again['actions']}, {'same'})
        self.assertEqual(apply(self.target, PACKAGE, again, home=self.home), [])

    def test_existing_project_keeps_its_files_and_only_appends_ignore_lines(self):
        (self.target / '.git').mkdir()
        (self.target / 'src').mkdir()
        (self.target / 'AGENTS.md').write_bytes(b'# our own rules\n')
        (self.target / '.gitignore').write_bytes(b'node_modules\n.env')
        before = self.snapshot()
        result = plan(self.target, PACKAGE, home=self.home)
        self.assertEqual(self.snapshot(), before)
        self.assertTrue(result['existing_project'])
        self.assertEqual(result['other_entries'], ['.git', 'src'])
        actions = {a['path']: a for a in result['actions']}
        self.assertEqual(actions['AGENTS.md'], {'path': 'AGENTS.md', 'action': 'keep',
                                                'why': 'project-content'})
        self.assertEqual((actions['.gitignore']['action'], actions['.gitignore']['lines']),
                         ('append', ['*.key']))
        apply(self.target, PACKAGE, result, home=self.home)
        after = self.snapshot()
        self.assertEqual(after['AGENTS.md'], b'# our own rules\n')
        self.assertEqual(after['.gitignore'], b'node_modules\n.env\n*.key\n')
        self.assertEqual(after['HANDOFF.md'], PACKAGE['HANDOFF.md'])

    def test_gitignore_that_already_has_every_line_is_same(self):
        (self.target / '.gitignore').write_bytes(b'*.key\nlocal\n.env\n')
        actions = {a['path']: a for a in plan(self.target, PACKAGE, home=self.home)['actions']}
        self.assertEqual(actions['.gitignore']['action'], 'same')

    def test_apply_refuses_a_plan_that_no_longer_matches(self):
        result = plan(self.target, PACKAGE, home=self.home)
        (self.target / 'HANDOFF.md').write_bytes(b'someone else wrote this\n')
        self.denied('plan-changed', apply, self.target, PACKAGE, result, home=self.home)
        self.assertEqual(self.snapshot(), {'HANDOFF.md': b'someone else wrote this\n'})

    def test_home_root_missing_target_and_bad_paths_are_refused(self):
        self.denied('refuse-home-or-root', plan, self.home, PACKAGE, home=self.home)
        self.denied('refuse-home-or-root', plan, Path('/'), PACKAGE, home=self.home)
        self.denied('target-missing', plan, self.base / 'nope', PACKAGE, home=self.home)
        for bad in ('../x', '/abs', 'a//b', 'a\\b', '', './x'):
            with self.subTest(path=bad):
                self.denied('invalid-package-path', plan, self.target, {bad: b'x'}, home=self.home)

    def test_non_regular_entries_are_kept(self):
        (self.target / 'AGENTS.md').mkdir()
        (self.target / 'elsewhere').write_bytes(b'x')
        (self.target / 'HANDOFF.md').symlink_to(self.target / 'elsewhere')
        actions = {a['path']: a for a in plan(self.target, PACKAGE, home=self.home)['actions']}
        self.assertEqual((actions['AGENTS.md']['action'], actions['HANDOFF.md']['action']),
                         ('keep', 'keep'))
        (self.target / 'same').write_bytes(PACKAGE['.gitignore'])
        (self.target / '.gitignore').symlink_to(self.target / 'same')
        (self.target / '.claude').mkdir()
        (self.target / '.claude/hooks').symlink_to(self.base / 'nowhere')
        (self.base / 'nowhere').mkdir()
        (self.base / 'nowhere/git-freshness.sh').symlink_to(self.base / 'dangling')
        actions = {a['path']: a for a in plan(self.target, PACKAGE, home=self.home)['actions']}
        self.assertEqual(actions['.gitignore']['action'], 'keep')
        self.assertEqual(actions['.claude/hooks/git-freshness.sh']['action'], 'keep')

    def test_existing_project_is_flagged_by_git_alone_or_by_other_files_alone(self):
        (self.target / '.git').mkdir()
        self.assertTrue(plan(self.target, PACKAGE, home=self.home)['existing_project'])
        (self.target / '.git').rmdir()
        (self.target / 'main.py').write_bytes(b'print(1)\n')
        self.assertTrue(plan(self.target, PACKAGE, home=self.home)['existing_project'])

    def test_a_file_that_appears_after_the_check_is_not_overwritten(self):
        approved = plan(self.target, PACKAGE, home=self.home)
        (self.target / 'AGENTS.md').write_bytes(b'raced\n')
        with patch.object(install, 'plan', return_value=approved):
            with self.assertRaises(FileExistsError):
                apply(self.target, PACKAGE, approved, home=self.home)
        self.assertEqual((self.target / 'AGENTS.md').read_bytes(), b'raced\n')


if __name__ == '__main__':
    unittest.main()
