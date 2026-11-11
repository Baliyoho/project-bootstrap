"""F16a: a clean second machine finds the procedure in the repository, not in private copies."""

from pathlib import Path
import subprocess
import tempfile
import unittest

from project_bootstrap.resume import check, clone

SKILL = '---\nname: handoff\n---\n\n<!-- source: PACKAGE.md v{v} -->\n# procedure\n'


def entry(body, heading='## 開工第一件事'):
    return f'# AGENTS\n\n{heading}\n\n{body}\n\n## 其他\n\n見 [包](PACKAGE.md)。\n'


class ResumeTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='bootstrap-v2-resume-')
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.root = self.base / '第一 機'
        self.root.mkdir()
        self.home = self.base / 'home'
        self.home.mkdir()

    def write(self, relative, text, base=None):
        path = (base or self.root) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def git(self, *args):
        subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)

    def test_home_only_procedure_fails_on_a_clean_machine(self):
        self.write('AGENTS.md', entry('程序在 `~/.claude/skills/handoff/SKILL.md`。'))
        result = check(self.root, self.home)
        self.assertEqual((result['result'], result['reasons'], result['procedures']),
                         ('不通過', ['procedure-not-in-repo'], []))

    def test_home_copy_present_still_requires_an_in_repo_source(self):
        self.write('AGENTS.md', entry('程序在 `~/.claude/skills/handoff/SKILL.md`。'))
        self.write('.claude/skills/handoff/SKILL.md', SKILL.format(v='1'), base=self.home)
        result = check(self.root, self.home)
        self.assertEqual(result['reasons'], ['procedure-not-in-repo'])
        self.assertEqual(result['procedures'], [{'kind': 'home', 'path':
                         '~/.claude/skills/handoff/SKILL.md', 'source': 'PACKAGE.md v1'}])

    def test_linked_package_in_repo_passes_with_empty_home(self):
        self.write('AGENTS.md', entry('沒有全域副本時讀 [部署包](PACKAGE.md#38) 3.8 節。'))
        self.write('PACKAGE.md', '# 包\n<!-- source: PACKAGE.md v0 -->\n' + SKILL.format(v='2'))
        result = check(self.root, self.home)
        self.assertEqual(result['result'], '通過')
        self.assertEqual(result['procedures'], [{'kind': 'repo', 'path': 'PACKAGE.md',
                                                 'source': 'PACKAGE.md v2'}])

    def test_package_linked_only_outside_the_section_does_not_count(self):
        self.write('AGENTS.md', entry('程序在 `~/.claude/skills/handoff/SKILL.md`。'))
        self.write('PACKAGE.md', SKILL.format(v='1'))
        self.assertEqual(check(self.root, self.home)['reasons'], ['procedure-not-in-repo'])

    def test_linked_file_without_the_marker_is_not_a_procedure(self):
        self.write('AGENTS.md', entry('讀 [說明](README.md)。'))
        self.write('README.md', '# readme\nname: handoffs\n')
        self.assertEqual(check(self.root, self.home)['reasons'], ['procedure-not-in-repo'])

    def test_missing_required_link_and_private_attachment_are_told_apart(self):
        self.write('AGENTS.md', entry('讀 [包](PACKAGE.md)、[報告](probe.md)、[快照](gone.md)、'
                                      '[目錄](docs/)、[外站](https://example.com/x.md)、[本節](#x)。'))
        self.write('PACKAGE.md', SKILL.format(v='1'))
        self.write('docs/a.md', 'a\n')
        self.git('init', '-q', '-b', 'main')
        self.git('add', 'AGENTS.md', 'PACKAGE.md', 'docs/a.md')
        self.git('-c', 'user.name=t', '-c', 'user.email=t@example.com', 'commit', '-qm', 'x')
        self.write('probe.md', 'kept only on the first machine\n')
        second = clone(self.root, self.base / '第二 機', 'main')
        self.assertFalse((second / 'probe.md').exists())
        result = check(second, self.home, first=self.root)
        self.assertEqual((result['result'], result['reasons'], result['missing'], result['private']),
                         ('不通過', ['required-missing', 'private-attachment'], ['gone.md'],
                          ['probe.md']))
        without_first = check(second, self.home)
        self.assertEqual((without_first['missing'], without_first['private']),
                         (['probe.md', 'gone.md'], []))

    def test_differing_source_markers_are_reported_as_drift(self):
        self.write('AGENTS.md', entry('程序在 `~/.claude/skills/handoff/SKILL.md`，'
                                      '沒有就讀 [包](PACKAGE.md)。'))
        self.write('.claude/skills/handoff/SKILL.md', SKILL.format(v='1'), base=self.home)
        self.write('PACKAGE.md', SKILL.format(v='2'))
        result = check(self.root, self.home)
        self.assertEqual((result['result'], result['drift']),
                         ('通過', ['PACKAGE.md v1', 'PACKAGE.md v2']))
        self.write('PACKAGE.md', SKILL.format(v='1'))
        self.assertEqual(check(self.root, self.home)['drift'], [])

    def test_unreadable_entry_or_missing_section_is_unknown(self):
        self.assertEqual(check(self.root, self.home)['reasons'], ['entry-unreadable'])
        self.write('AGENTS.md', entry('讀 [包](PACKAGE.md)。', heading='## 別的標題'))
        self.write('PACKAGE.md', SKILL.format(v='1'))
        self.assertEqual(check(self.root, self.home), {'result': '未知',
                                                       'reasons': ['section-missing']})

    def test_section_ends_at_the_next_heading_of_same_depth_only(self):
        self.write('AGENTS.md', '# A\n\n## 開工第一件事\n\n### 細節\n\n讀 [包](PACKAGE.md)。\n'
                                '\n## 下一節\n\n`~/x/SKILL.md`\n')
        self.write('PACKAGE.md', SKILL.format(v='1'))
        self.write('x/SKILL.md', SKILL.format(v='9'), base=self.home)
        result = check(self.root, self.home)
        self.assertEqual(([p['path'] for p in result['procedures']], result['drift']),
                         (['PACKAGE.md'], []))


if __name__ == '__main__':
    unittest.main()
