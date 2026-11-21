"""F16a on this repository and on a project generated from its package:
with an empty home, the entry file still leads to the procedure."""

from pathlib import Path
import sys
import tempfile
import unittest

from project_bootstrap.resume import check

ROOT = Path(__file__).resolve().parents[1]


class ResumeRepoTests(unittest.TestCase):
    def test_empty_home_finds_the_procedure_in_the_package(self):
        with tempfile.TemporaryDirectory(prefix='bootstrap-resume-home-') as home:
            # 2026-11-21 (decision v3 Q58): what differs from a deployed project is now
            # written as this repo's own rules ("本 repo 沒有 X，改用 Y").
            result = check(ROOT, home, heading='專用規則')
        self.assertEqual((result['result'], result['reasons'], result['missing']),
                         ('通過', [], []))
        # 2026-11-18 (decision v3 Q50): the fallback is the skill template in src/kit, not the retired package.
        self.assertIn('src/kit/files/.claude/skills/handoff/SKILL.md.tmpl', [p['path'] for p in result['procedures']])
        version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        self.assertTrue(all(p['source'] for p in result['procedures']))
        # The procedure's marker follows its own edits, so it may be ahead of VERSION, not behind.
        self.assertGreaterEqual(result['procedures'][0]['source'].split(' v')[1], version)


    def test_generated_project_finds_its_procedure_with_an_empty_home(self):
        sys.path.insert(0, str(ROOT / 'tools'))
        try:
            import verify_bootstrap
        finally:
            sys.path.remove(str(ROOT / 'tools'))
        with tempfile.TemporaryDirectory(prefix='bootstrap-resume-gen-') as directory:
            project, home = Path(directory) / 'project', Path(directory) / 'home'
            home.mkdir()
            verify_bootstrap.extract(project)
            # 2026-11-13 (decision v3 D12): the generated AGENTS.md has no start-of-work
            # section; since 2026-11-21 (v3 Q58) a shared rule links the reference procedure.
            heading = "共用規則"
            result = check(project, home, heading=heading)
            self.assertEqual((result['result'], result['reasons'], result['missing']),
                             ('通過', [], []))
            self.assertEqual([p['path'] for p in result['procedures']],
                             ['.claude/skills/handoff/SKILL.md'])
            # Without the deployed copy a new machine has nothing to follow.
            (project / '.claude/skills/handoff/SKILL.md').unlink()
            result = check(project, home, heading=heading)
            self.assertEqual(result['result'], '不通過')
            self.assertIn('procedure-not-in-repo', result['reasons'])

if __name__ == '__main__':
    unittest.main()
