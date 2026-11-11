"""P2 slice 5 on real kit files: tools/migrate_project.py over Git fixture projects (decision Q25).

Imports tools/, so it is a *_repo test and stays out of mutation groups. The
fixtures are built from this repository's package and from the oldest
published PROJECT-BOOTSTRAP.md, so "known old version" means a version this
repository really published.
"""
import contextlib
import io
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

from project_bootstrap import channel, package, pointer, release as release_module
from project_bootstrap.contracts import Denied

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import build_package  # noqa: E402
import migrate_project  # noqa: E402
import release_package  # noqa: E402
import sync_project as sp  # noqa: E402
import verify_bootstrap  # noqa: E402

HAS_GIT = shutil.which('git') is not None
SIGNS = (platform.system() == 'Darwin' and release_module.VERIFIER.is_file() and HAS_GIT)
HOOK = '.claude/hooks/git-freshness.sh'
SKILL = '.claude/skills/handoff/SKILL.md'
LAUNCHER = '.agents/ag-hook.cmd'
OWNER = '`fixture` ／ `Claude Code` ／ `migrate`'


def git(cwd, *args):
    return subprocess.run(['git', '-C', str(cwd), *args], check=True, capture_output=True,
                          encoding='utf-8').stdout.strip()


def snapshot(folder, skip_git=False):
    out = {}
    for path in sorted(Path(folder).rglob('*')):
        rel = path.relative_to(folder).as_posix()
        if skip_git and (rel == '.git' or rel.startswith('.git/')):
            continue
        st = path.lstat()
        out[rel] = (st.st_mode, st.st_mtime_ns, path.read_bytes() if path.is_file() else None)
    return out


@unittest.skipUnless(HAS_GIT, 'needs git')
class MigrateRepoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='migrate-repo-')
        cls.root = Path(cls.temp.name)
        folder, cls.manifest = build_package.build_once()
        cls.current = cls.root / 'current'
        shutil.move(folder, cls.current)
        oldest = sp.git_output(ROOT, 'log', '--format=%H', '--', 'PROJECT-BOOTSTRAP.md').split()[-1]
        cls.old = cls.root / 'old'
        cls.old.mkdir()
        verify_bootstrap.extract(cls.old, sp.git_output(ROOT, 'show', oldest + ':PROJECT-BOOTSTRAP.md') + '\n')
        old_hook = (cls.old / HOOK).read_bytes()
        assert old_hook != (cls.current / HOOK).read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.work = Path(tempfile.mkdtemp(dir=self.root))
        self.addCleanup(shutil.rmtree, self.work, True)

    def project(self, name, old_hook=True, origin=False, tweak=None):
        project = self.work / name
        for rel in self.manifest['components']:
            target = project / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.current / rel, target)
        if old_hook:
            (project / HOOK).write_bytes((self.old / HOOK).read_bytes())
        if tweak:
            tweak(project)
        git(project.parent, 'init', '-q', '-b', 'main', str(project))
        git(project, 'config', 'user.email', 'fixture@example.invalid')
        git(project, 'config', 'user.name', 'fixture')
        git(project, 'config', 'core.autocrlf', 'false')
        git(project, 'add', '-A')
        git(project, 'commit', '-qm', 'fixture')
        if origin:
            bare = self.work / (name + '.git')
            git(self.work, 'init', '-q', '--bare', str(bare))
            git(project, 'remote', 'add', 'origin', str(bare))
            git(project, 'push', '-q', '-u', 'origin', 'main')
        return project

    def run_main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = migrate_project.main([str(a) for a in argv])
        return code, out.getvalue()

    def test_twenty_target_dry_run_reports_each_once_and_writes_nothing(self):
        digest = package.digest(self.manifest)

        def current(project):
            (project / HOOK).write_bytes((self.current / HOOK).read_bytes())
            (project / '.bootstrap').mkdir()
            (project / pointer.POINTER).write_text(json.dumps(
                {'schema': 1, 'channel': 'beta', 'installed': digest, 'exception': None}))

        def customised(project):
            with open(project / SKILL, 'a', encoding='utf-8') as handle:
                handle.write('\nproject rule\n')

        def crlf(project):
            data = (self.current / LAUNCHER).read_bytes()
            (project / LAUNCHER).write_bytes(data.replace(b'\n', b'\r\n'))

        def missing(project):
            (project / LAUNCHER).unlink()

        entries = []
        for i in range(20):
            name = 'p%02d' % i
            status = 'active'
            if i < 11:
                self.project(name)
            elif i < 13:
                self.project(name, tweak=current)
            elif i < 15:
                self.project(name, tweak=customised)
            elif i == 15:
                self.project(name, old_hook=False, tweak=crlf)
            elif i == 16:
                self.project(name, tweak=missing)
            elif i == 17:
                self.project(name)
                status = 'archived'
            elif i == 18:
                pass  # listed active but not there
            else:
                (self.work / name).mkdir()  # a folder without the system
            entries.append({'path': name, 'status': status})
        inventory = self.work / 'inventory.json'
        inventory.write_text(json.dumps(entries))
        before = snapshot(self.work)
        report_file = self.root / ('report-%s.json' % self.work.name)
        code, printed = self.run_main('--inventory', inventory, '--json', report_file)
        self.assertEqual(snapshot(self.work), before, 'dry run changed a project')
        self.assertEqual(code, 1)
        result = json.loads(report_file.read_text(encoding='utf-8'))
        rows = {Path(r['target']).name: r for r in result['results']}
        self.assertEqual(sorted(rows), ['p%02d' % i for i in range(20)])
        self.assertEqual(result['targets'], 20)
        self.assertEqual(result['totals'], {'current': 2, 'migrate': 12, 'manual': 3,
                                            'failed': 2, 'excluded': 1})
        self.assertEqual(result['manual_prompts'], 3)
        self.assertEqual(rows['p00']['replace'], [HOOK])
        self.assertEqual(rows['p00']['add'], [])
        self.assertEqual(rows['p13']['compare'], [SKILL])
        self.assertEqual(rows['p15']['eol'], [LAUNCHER])
        self.assertEqual(rows['p16']['add'], [LAUNCHER])
        self.assertTrue(rows['p18']['problems'][0].startswith('inventory active'))
        self.assertTrue(rows['p19']['problems'][0].startswith('inventory active'))
        self.assertIn('NOT ok', printed)

    def test_merge_counts_mixed_files(self):
        def own_hook(project):
            settings = json.loads((self.old / '.claude/settings.json').read_text(encoding='utf-8'))
            settings['permissions'] = {'allow': ['Bash(ls)']}
            (project / '.claude/settings.json').write_text(json.dumps(settings))
            (project / '.gitignore').write_text('build/\n')
        project = self.project('mixed', tweak=own_hook)
        code, _ = self.run_main(project, '--json', self.work / 'r.json')
        row = json.loads((self.work / 'r.json').read_text(encoding='utf-8'))['results'][0]
        self.assertEqual((code, row['action']), (0, 'migrate'))
        self.assertEqual(row['merges'], 2)

    def test_the_authority_repo_is_refused(self):
        code, printed = self.run_main(ROOT)
        self.assertEqual(code, 1)
        self.assertIn('authority-repo', printed)

    # --- write mode, with a real signed release -------------------------------------------

    def signed_release(self):
        source = self.work / 'source.git'
        git(self.work, 'init', '-q', '--bare', str(source))
        key = self.work / 'ci'
        subprocess.run([str(release_module.VERIFIER), '-q', '-t', 'ed25519', '-N', '', '-f', str(key)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        keys = self.work / 'release-keys.txt'
        keys.write_text('# test\n' + ' '.join(key.with_suffix('.pub').read_text().split()[:2]) + '\n')
        fake = {'status': '', 'rev-parse': 'f' * 40}
        args = types.SimpleNamespace(channel='beta', source=str(source), signing_key=str(key),
                                     out=str(self.work / 'out'))
        with mock.patch.object(release_package, 'KEYS', keys), \
                mock.patch.object(release_package, 'git', lambda *a: fake[a[0]]), \
                contextlib.redirect_stdout(io.StringIO()):
            result = release_package.release(args, verify=lambda: ('[  ok  ] a\n', 0), now=lambda: 0)
        blob = subprocess.run(['git', '-C', str(source), 'hash-object', '-w', '--stdin'], input=b'x',
                              capture_output=True, check=True).stdout.decode().strip()
        git(source, 'update-ref', result['tag'], blob)
        return source, keys, result

    def claim(self, project):
        handoff = project / 'HANDOFF.md'
        text = handoff.read_text(encoding='utf-8').replace('- **工作中**：無（已交棒）', '- **工作中**：' + OWNER)
        handoff.write_text(text, encoding='utf-8')
        git(project, 'commit', '-qam', 'claim')
        git(project, 'push', '-q')

    def write_args(self, project, source, result, owner=OWNER):
        archive, record, signature, _ = result['assets']
        return types.SimpleNamespace(project=str(project), owner=owner, archive=archive, record=record,
                                     signature=signature, channel='beta', source=str(source),
                                     cache=str(self.work / 'cache'))

    @unittest.skipUnless(SIGNS, 'needs ssh-keygen on macOS like the release tests')
    def test_write_migrates_one_project_and_the_write_check_passes(self):
        source, keys, result = self.signed_release()
        def own(project):
            with open(project / '.gitignore', 'a', encoding='utf-8') as handle:
                handle.write('local/\n')
            settings = json.loads((self.old / '.claude/settings.json').read_text(encoding='utf-8'))
            settings['permissions'] = {'allow': ['Bash(ls)']}
            (project / '.claude/settings.json').write_text(json.dumps(settings))
            (project / LAUNCHER).unlink()
        project = self.project('target', origin=True, tweak=own)
        self.claim(project)
        with mock.patch.object(migrate_project.install_package, 'KEYS', keys):
            row = migrate_project.write_one(self.write_args(project, source, result))
        self.assertEqual(row['action'], 'migrate')
        self.assertEqual(sorted(row['applied']), sorted([HOOK, LAUNCHER, '.claude/settings.json']))
        settings = json.loads((project / '.claude/settings.json').read_text(encoding='utf-8'))
        self.assertEqual(settings['permissions'], {'allow': ['Bash(ls)']})
        self.assertEqual(settings['hooks'], json.loads(
            (self.current / '.claude/settings.json').read_text(encoding='utf-8'))['hooks'])
        self.assertEqual(row['pointer'], result['digest'])
        self.assertEqual((project / HOOK).read_bytes(), (self.current / HOOK).read_bytes())
        self.assertTrue((project / '.gitignore').read_text(encoding='utf-8').endswith('local/\n'))
        gate = channel.GitWriteCheck(project, self.work / 'cache')
        self.assertEqual(gate.confirm('a' * 32, 'HANDOFF.md')['installed'], result['digest'])
        changed = {tuple(line.split()) for line in git(project, 'status', '--porcelain').splitlines()}
        self.assertEqual(changed, {('M', HOOK), ('M', '.claude/settings.json'), ('??', LAUNCHER),
                                   ('??', '.bootstrap/')})

    @unittest.skipUnless(SIGNS, 'needs ssh-keygen on macOS like the release tests')
    def test_write_refusals_leave_the_project_unchanged(self):
        source, keys, result = self.signed_release()
        def customised(project):
            with open(project / SKILL, 'a', encoding='utf-8') as handle:
                handle.write('\nproject rule\n')
        cases = [('custom', customised, OWNER, 'manual:' + SKILL),
                 ('owner', None, '`other` ／ `Codex CLI`', None)]
        for name, tweak, owner, code in cases:
            project = self.project(name, origin=True, tweak=tweak)
            self.claim(project)
            before = snapshot(project, skip_git=True)
            with mock.patch.object(migrate_project.install_package, 'KEYS', keys):
                with self.assertRaises(Denied) as caught:
                    migrate_project.write_one(self.write_args(project, source, result, owner))
            if code:
                self.assertEqual(str(caught.exception), code)
            else:
                self.assertTrue(str(caught.exception).startswith('owner:'), caught.exception)
            self.assertEqual(snapshot(project, skip_git=True), before, name)
            self.assertFalse((project / pointer.POINTER).exists())


if __name__ == '__main__':
    unittest.main()
