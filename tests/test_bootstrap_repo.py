"""End-to-end checks of the built bootstrap.py (decision v3 Q49).

Runs the committed file as a subprocess in temporary folders: an empty folder,
a folder that already has AGENTS.md, .gitignore and .claude/settings.json, an
update over project-owned edits, a CRLF checkout, and the two hooks inside the
deployed repo. Needs tools/ and the repo root, so mutation runs leave it out.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / 'bootstrap.py'
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'src'))

from project_bootstrap import installer  # noqa: E402

ANSWERS = {'PROJECT_NAME': '端到端測試', 'ONELINER': '', 'GH_OWNER': 'example-owner',
           'GH_REPO': 'example-repo', 'GH_VISIBILITY': 'private', 'LANG': '繁體中文',
           'TZ': 'Asia/Taipei', 'SECRETS': '.env', 'RUNTIME_DIRS': 'data/', 'STACK_DIRS': '',
           'VERIFY_TARGETS': '', 'FORBIDDEN_OPS': ''}
GIT_ENV = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.invalid',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.invalid',
               BOOTSTRAP_VERSION_CHECK='off')


def owners():
    return json.loads((ROOT / 'src/kit/owners.json').read_text(encoding='utf-8'))['files']


@unittest.skipIf(sys.version_info < installer.MIN_PY, 'bootstrap.py needs Python 3.12+')
class BootstrapRepoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.answers = self.base / 'answers.json'
        self.answers.write_text(json.dumps(ANSWERS, ensure_ascii=False), encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def bootstrap(self, *args, cwd=None):
        return subprocess.run([sys.executable, '-X', 'utf8', str(BOOTSTRAP), *args], cwd=cwd,
                              capture_output=True, text=True, encoding='utf-8', env=GIT_ENV)

    def install(self, name, *extra):
        target = self.base / name
        target.mkdir(exist_ok=True)
        done = self.bootstrap('--target', str(target), '--answers', str(self.answers),
                              '--non-interactive', *extra)
        return target, done

    def git(self, cwd, *args, check=True):
        done = subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, env=GIT_ENV)
        if check and done.returncode:
            raise AssertionError('git %s: %s' % (' '.join(args), done.stderr))
        return done

    def test_bootstrap_py_is_the_current_build(self):
        import build_kit
        prose, files = build_kit.load_source()
        self.assertEqual(BOOTSTRAP.read_text(encoding='utf-8'), build_kit.load_bootstrap(files),
                         'run python3 -X utf8 tools/build_kit.py')

    def test_python_floor_matches_pyproject(self):
        text = (ROOT / 'pyproject.toml').read_text(encoding='utf-8')
        floor = re.search(r'requires-python\s*=\s*">=(\d+)\.(\d+)"', text).groups()
        self.assertEqual(tuple(int(n) for n in floor), installer.MIN_PY)

    def test_empty_folder_matches_owners_and_target_shape(self):
        target, done = self.install('empty')
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        written = {p.relative_to(target).as_posix() for p in target.rglob('*')
                   if p.is_file() and '.git' not in p.relative_to(target).parts}
        self.assertEqual(written, set(owners()) | {installer.ANSWERS_FILE})
        self.assertIn('@AGENTS.md', (target / 'CLAUDE.md').read_text(encoding='utf-8').split('\n'))
        agents = (target / 'AGENTS.md').read_text(encoding='utf-8')
        start, end = agents.index('<!-- 共用制度開始'), agents.index('<!-- 共用制度結束 -->')
        self.assertLessEqual(agents[start:end].count('\n'), 40)
        self.assertLessEqual(agents.count('\n'), 100)
        self.assertLessEqual((target / 'HANDOFF.md').read_text(encoding='utf-8').count('\n'), 80)
        self.assertTrue((target / '.git').is_dir())
        self.assertEqual(self.git(target, 'status', '--porcelain', '--', '.git').stdout, '')
        self.assertEqual(self.git(target, 'symbolic-ref', 'HEAD').stdout.strip(), 'refs/heads/main')
        self.assertEqual(self.git(target, 'rev-list', '--all').stdout, '', 'the installer must not commit')
        self.assertIn('全部相符', done.stdout)

    def test_existing_files_go_to_sidecars(self):
        target = self.base / 'busy'
        mine = {'AGENTS.md': '# mine\n', '.gitignore': 'node_modules/\n',
                '.claude/settings.json': '{"permissions": {"allow": []}}\n'}
        for rel, text in mine.items():
            (target / rel).parent.mkdir(parents=True, exist_ok=True)
            (target / rel).write_text(text, encoding='utf-8')
        target, done = self.install('busy')
        self.assertEqual(done.returncode, 0, done.stdout)
        for rel, text in mine.items():
            self.assertEqual((target / rel).read_text(encoding='utf-8'), text)
            self.assertTrue((target / (rel + '.bootstrap-new')).is_file())
        written = {p.relative_to(target).as_posix() for p in target.rglob('*')
                   if p.is_file() and '.git' not in p.relative_to(target).parts}
        self.assertEqual(written, set(owners()) | {installer.ANSWERS_FILE}
                         | {rel + '.bootstrap-new' for rel in mine})

    def test_git_init_is_skipped_inside_an_existing_work_tree(self):
        outer = self.base / 'outer'
        outer.mkdir()
        self.git(outer, 'init', '-q')
        target, done = self.install('outer/inner')
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertFalse((target / '.git').exists())
        self.assertIn('已經在 Git 工作樹裡', done.stdout)

    def test_update_restores_core_and_keeps_project_content(self):
        target, done = self.install('update')
        self.assertEqual(done.returncode, 0, done.stdout)
        edits = {
            'AGENTS.md': lambda t: t + '\n## 專案自己的段落\n\n- 不准動\n',
            'README.md': lambda t: t + '\n專案自己寫的 README\n',
            'HANDOFF.md': lambda t: t.replace('## 地雷與注意事項', '## 地雷與注意事項\n\n- 專案自己的地雷'),
            '.gitignore': lambda t: t + 'project-only/\n',
            'tools/verify_state.py': lambda t: t + '\n# project checks\n',
        }
        for rel, edit in edits.items():
            path = target / rel
            path.write_text(edit(path.read_text(encoding='utf-8')), encoding='utf-8')
        settings = json.loads((target / '.claude/settings.json').read_text(encoding='utf-8'))
        settings['permissions'] = {'allow': ['Bash(ls)']}
        (target / '.claude/settings.json').write_text(json.dumps(settings), encoding='utf-8')
        mode_a = target / '.claude/skills/handoff/mode-a.md'
        pristine = mode_a.read_bytes()
        mode_a.write_text('drifted\n', encoding='utf-8')
        before = {rel: (target / rel).read_text(encoding='utf-8') for rel in edits}

        preview = self.bootstrap('update', '--target', str(target))
        self.assertEqual(preview.returncode, 0, preview.stdout)
        self.assertEqual(mode_a.read_text(encoding='utf-8'), 'drifted\n')
        done = self.bootstrap('update', '--target', str(target), '--write')
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual(mode_a.read_bytes(), pristine)
        for rel, text in before.items():
            self.assertEqual((target / rel).read_text(encoding='utf-8'), text, rel)
        merged = json.loads((target / '.claude/settings.json').read_text(encoding='utf-8'))
        self.assertEqual(merged['permissions'], {'allow': ['Bash(ls)']})

    def test_update_over_a_crlf_checkout(self):
        """A Windows checkout with core.autocrlf: same text, CRLF bytes. Update must not churn it."""
        target, done = self.install('crlf')
        self.assertEqual(done.returncode, 0, done.stdout)
        agents = target / 'AGENTS.md'
        agents.write_text(agents.read_text(encoding='utf-8') + '\n- 專案的 CRLF 規則\n', encoding='utf-8')
        for path in target.rglob('*'):
            if path.is_file() and '.git' not in path.relative_to(target).parts:
                path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
        skill = target / '.claude/skills/handoff/SKILL.md'
        crlf = skill.read_bytes()
        preview = self.bootstrap('update', '--target', str(target))
        self.assertIn('預演：0 個檔要改', preview.stdout)
        mode_a = target / '.claude/skills/handoff/mode-a.md'
        mode_a.write_bytes(b'drifted\r\n')
        done = self.bootstrap('update', '--target', str(target), '--write')
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn('全部相符', done.stdout)
        self.assertTrue(skill.read_bytes() == crlf, 'an unchanged CRLF file was rewritten')
        self.assertFalse(b'\r\n' in mode_a.read_bytes(), 'a rewritten core file is not LF')
        self.assertIn('專案的 CRLF 規則', agents.read_text(encoding='utf-8'))

    def test_update_refuses_a_secret_in_the_answers_file(self):
        target, done = self.install('secret')
        path = target / installer.ANSWERS_FILE
        data = json.loads(path.read_text(encoding='utf-8'))
        data['answers']['ONELINER'] = 'AKIA' + 'A' * 16
        path.write_text(json.dumps(data), encoding='utf-8')
        self.assertEqual(self.bootstrap('update', '--target', str(target), '--write').returncode, 2)

    @unittest.skipIf(not shutil.which('bash'), 'needs bash for the hooks')
    def test_hooks_run_in_the_deployed_repo(self):
        target, done = self.install('hooks')
        self.assertEqual(done.returncode, 0, done.stdout)
        for rel in sorted(owners()) + [installer.ANSWERS_FILE]:
            self.git(target, 'add', '--', rel)
        self.git(target, 'commit', '-qm', 'bootstrap')
        remote = self.base / 'origin.git'
        self.git(self.base, 'init', '-q', '--bare', str(remote))
        self.git(target, 'remote', 'add', 'origin', str(remote))
        self.git(target, 'push', '-qu', 'origin', 'main')
        bash = shutil.which('bash')
        facts = subprocess.run([bash, '.claude/hooks/git-freshness.sh'], cwd=target, capture_output=True,
                               text=True, encoding='utf-8', env=GIT_ENV)
        self.assertEqual(facts.returncode, 0, facts.stderr)
        context = json.loads(facts.stdout)['hookSpecificOutput']['additionalContext']
        self.assertIn('落後 origin/main 0 個 commit、領先 0 個', context)
        self.assertIn('無（已交棒）', context)

        def pre_push(command):
            payload = json.dumps({'tool_name': 'Bash', 'tool_input': {'command': command}})
            return subprocess.run([bash, '.claude/hooks/pre-push-handoff.sh'], cwd=target, input=payload,
                                  capture_output=True, text=True, encoding='utf-8', env=GIT_ENV)
        self.assertEqual(pre_push('git status').returncode, 0)
        (target / 'README.md').write_text('changed\n', encoding='utf-8')
        self.git(target, 'commit', '-qam', 'work without a marker')
        self.assertEqual(pre_push('git push').returncode, 2)


if __name__ == '__main__':
    unittest.main()
