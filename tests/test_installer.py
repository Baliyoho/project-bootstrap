"""Install-mode guards of src/project_bootstrap/installer.py (decision v3 Q49).

Reads the templates from src/kit/ with load_kit(), so mutation runs, which copy
only src/ and tests/, exercise the same code bootstrap.py embeds. Update mode
needs tools/sync_project.py and is tested on the built file in
test_bootstrap_repo.
"""
import datetime
import json
from pathlib import Path
import tempfile
import unittest

from project_bootstrap import installer

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime.datetime(2026, 11, 18, 21, 5)


def answers(**over):
    base = {'PROJECT_NAME': '測試專案', 'ONELINER': '測試用', 'GH_OWNER': 'example-owner',
            'GH_REPO': 'example-repo', 'GH_VISIBILITY': 'private', 'LANG': '繁體中文',
            'TZ': 'Asia/Taipei', 'SECRETS': '.env、keys/測試 key.pem', 'RUNTIME_DIRS': 'data/',
            'STACK_DIRS': 'src/', 'VERIFY_TARGETS': '', 'FORBIDDEN_OPS': '', 'TODAY': '2026-11-18'}
    base.update(over)
    return base


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.kit = installer.load_kit(ROOT / 'src' / 'kit')
        self.tmp = tempfile.TemporaryDirectory()
        self.target = Path(self.tmp.name) / 'project'
        self.target.mkdir()
        self.lines = []

    def tearDown(self):
        self.tmp.cleanup()

    def run_install(self, **over):
        return installer.install(self.target, self.kit, answers(**over), now=NOW,
                                 init_git=False, out=self.lines.append)

    def test_empty_folder_gets_every_owned_file_without_placeholders(self):
        self.assertEqual(self.run_install(), 0)
        for rel in self.kit['owners']:
            text = (self.target / rel).read_text(encoding='utf-8')
            self.assertIsNone(installer.PLACEHOLDER_RE.search(text), rel)
        saved = json.loads((self.target / installer.ANSWERS_FILE).read_text(encoding='utf-8'))
        self.assertEqual(saved['answers']['GH_REPO'], 'example-repo')
        self.assertEqual(saved['kit_version'], self.kit['version'])

    def test_gitignore_gets_one_pattern_per_line_and_markdown_gets_backticks(self):
        self.run_install()
        ignore = (self.target / '.gitignore').read_text(encoding='utf-8').split('\n')
        self.assertIn('keys/測試 key.pem', ignore)
        self.assertIn('data/', ignore)
        agents = (self.target / 'AGENTS.md').read_text(encoding='utf-8')
        self.assertIn('`.env`、`keys/測試 key.pem`', agents)

    def test_existing_files_are_never_overwritten(self):
        mine = {'AGENTS.md': '# mine\n', '.gitignore': 'node_modules/\n',
                '.claude/settings.json': '{"permissions": {}}\n'}
        for rel, text in mine.items():
            (self.target / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.target / rel).write_text(text, encoding='utf-8')
        self.assertEqual(self.run_install(), 0)
        for rel, text in mine.items():
            self.assertEqual((self.target / rel).read_text(encoding='utf-8'), text, rel)
            self.assertTrue((self.target / (rel + installer.SIDECAR)).is_file(), rel)
        handoff = (self.target / 'HANDOFF.md').read_text(encoding='utf-8')
        self.assertIn('`AGENTS.md`', handoff.split('## 未完成', 1)[1])

    def test_handoff_is_released_and_lists_the_first_batch(self):
        self.run_install(ONELINER='', FORBIDDEN_OPS='不能直接改正式資料庫')
        handoff = (self.target / 'HANDOFF.md').read_text(encoding='utf-8')
        self.assertIn('- **工作中**：無（已交棒）', handoff)
        self.assertIn('21:05', handoff)
        todo = handoff.split('## 未完成', 1)[1].split('\n## ', 1)[0]
        for needle in ('ARCHITECTURE.md', 'verify_state.py', 'ONELINER', '不能直接改正式資料庫', 'GitHub repo'):
            self.assertIn(needle, todo)

    def test_written_bytes_follow_gitattributes(self):
        rules = installer.eol_rules('* text=auto eol=lf\n*.bat text eol=crlf\n')
        self.assertEqual(installer.eol_for('x/run.bat', rules), 'crlf')
        self.assertEqual(installer.eol_for('AGENTS.md', rules), 'lf')
        self.assertEqual(installer.encode('a\r\nb\n', 'crlf'), b'a\r\nb\r\n')
        self.run_install()
        self.assertNotIn(b'\r\n', (self.target / 'AGENTS.md').read_bytes())

    def test_hash_check_catches_a_changed_file(self):
        self.run_install()
        rel = 'CLAUDE.md'
        data = (self.target / rel).read_bytes()
        self.assertEqual(installer.hash_problems(self.target, {rel: data}), [])
        (self.target / rel).write_bytes(data.replace(b'\n', b'\r\n'))
        self.assertNotEqual(installer.hash_problems(self.target, {rel: data}), [])

    def test_secrets_and_bad_answers_are_refused_before_writing(self):
        for over in ({'ONELINER': 'token ghp_' + 'a' * 36}, {'SECRETS': '!.env'},
                     {'GH_VISIBILITY': 'open'}, {'PROJECT_NAME': ''}, {'TODAY': '18/11'}):
            self.assertEqual(self.run_install(**over), 2, over)
            self.assertEqual(list(self.target.iterdir()), [], over)

    def test_second_install_and_leftover_sidecars_are_refused(self):
        self.assertEqual(self.run_install(), 0)
        self.assertEqual(self.run_install(), 2)
        other = Path(self.tmp.name) / 'other'
        other.mkdir()
        (other / ('README.md' + installer.SIDECAR)).write_text('x', encoding='utf-8')
        self.assertTrue(installer.target_problems(other))

    def test_home_folder_is_refused(self):
        self.assertTrue(installer.target_problems(Path.home()))

    def test_every_template_placeholder_is_an_interview_question(self):
        used = set()
        for text in self.kit['templates'].values():
            used |= set(installer.PLACEHOLDER_RE.findall(text))
        self.assertLessEqual(used, set(installer.KEYS))

    def test_unknown_placeholder_stops_the_render(self):
        with self.assertRaises(installer.InstallError):
            installer.render('x.md', '{{NOT_ASKED}}', answers())

    def test_preset_rejects_unknown_questions(self):
        with self.assertRaises(installer.InstallError):
            installer.read_preset(None, ['NOPE=1'])
        self.assertEqual(installer.read_preset(None, ['TZ=Asia/Taipei']), {'TZ': 'Asia/Taipei'})

    def test_non_interactive_interview_uses_defaults(self):
        got = installer.interview(self.target, {'TZ': 'Asia/Taipei'}, interactive=False)
        self.assertEqual(got['GH_REPO'], 'project')
        self.assertEqual(got['GH_VISIBILITY'], 'private')
        self.assertEqual(installer.check_answers(got), [])

    def test_interactive_interview_asks_again_after_a_bad_answer(self):
        replies = iter(['open', 'public'])
        preset = {k: v for k, v in answers().items() if k not in ('GH_VISIBILITY', 'TODAY')}
        got = installer.interview(self.target, preset, ask=lambda prompt: next(replies), out=self.lines.append)
        self.assertEqual(got['GH_VISIBILITY'], 'public')
        self.assertTrue(any('GH_VISIBILITY' in line for line in self.lines))
        preset.pop('GH_REPO')
        replies = iter([''])
        got = installer.interview(self.target, dict(preset, GH_VISIBILITY='private'),
                                  ask=lambda prompt: next(replies), out=self.lines.append)
        self.assertEqual(got['GH_REPO'], 'project')


if __name__ == '__main__':
    unittest.main()
