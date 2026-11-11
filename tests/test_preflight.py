"""Managed-write preflight: real Git checkouts plus a disposable release signer."""

import os
from pathlib import Path
import platform
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from project_bootstrap import batch, release
from project_bootstrap.batch import assess_many
from project_bootstrap.gitclaim import IDLE, GitGateDenied
from project_bootstrap.preflight import ManagedWrite, WriteDenied, assess_write
from project_bootstrap.release import WriteGate, build_manifest, manifest_digest, statement

ME = '`mac` ／ `Claude Code` ／ `㊣　26110923｜寫入檢查｜工作中｜交棒0次`'
OTHER = '`win` ／ `Codex CLI` ／ `㊣　26110901｜別人｜工作中｜交棒0次`'
PACKAGE = ('.claude/skills/handoff/SKILL.md', '.claude/hooks/git-freshness.sh')
OP = 'c' * 32


def handoff(owner):
    return f'# HANDOFF\n\n## Git 狀態\n- **工作中**：{owner}\n'


class Fixture(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='bootstrap-v2-preflight-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'home').mkdir()
        self.env = {'PATH': os.environ.get('PATH', ''), 'HOME': str(self.root / 'home'),
                    'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                    'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@example.invalid',
                    'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@example.invalid',
                    'LC_ALL': 'C'}
        self.supported = platform.system() == 'Darwin' and release.VERIFIER.is_file()
        if self.supported:
            self.key = self.root / 'ci'
            subprocess.run([str(release.VERIFIER), '-q', '-t', 'ed25519', '-N', '', '-f',
                            str(self.key)], check=True, timeout=3,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.public = b' '.join(self.key.with_suffix('.pub').read_bytes().split()[:2])
        self.now = 1000
        self.offline = False
        self.calls = 0

    def git(self, cwd, *args):
        result = subprocess.run(['git', *args], cwd=cwd, env=self.env, capture_output=True)
        if result.returncode:
            raise AssertionError(result.stderr.decode())
        return result.stdout.decode().strip()

    def project(self, name, owner=IDLE):
        origin = self.root / (name + '.git')
        work = self.root / name
        self.git(self.root, 'init', '--quiet', '--bare', '--initial-branch=main', str(origin))
        self.git(self.root, 'clone', '--quiet', str(origin), str(work))
        for path in PACKAGE:
            (work / path).parent.mkdir(parents=True, exist_ok=True)
            (work / path).write_text(f'{path} v1\n', encoding='utf-8')
        (work / 'HANDOFF.md').write_text(handoff(owner), encoding='utf-8')
        self.git(work, 'add', '-A')
        self.git(work, 'commit', '--quiet', '-m', 'init')
        self.git(work, 'push', '--quiet', '-u', 'origin', 'main')
        return work

    def commit(self, repo, name, text):
        (repo / name).write_text(text, encoding='utf-8')
        self.git(repo, 'add', name)
        self.git(repo, 'commit', '--quiet', '-m', f'edit {name}')

    def claim(self, repo, owner=ME):
        self.commit(repo, 'HANDOFF.md', handoff(owner))
        self.git(repo, 'push', '--quiet')

    def endpoint(self, manifest):
        digest = manifest_digest(manifest)

        def fetch(nonce):
            self.calls += 1
            if self.offline:
                raise ConnectionError('synthetic outage')
            document = statement('stable', 1, digest, nonce, self.now - 5, self.now + 60)
            signed = subprocess.run([str(release.VERIFIER), '-Y', 'sign', '-f', str(self.key),
                                     '-n', release.NAMESPACE], input=document,
                                    capture_output=True, check=True, timeout=3).stdout
            return document, signed
        return fetch

    def gate(self, repo, manifest=None):
        manifest = manifest or build_manifest(repo, PACKAGE, '2026-11-09', 'formal')
        return WriteGate(self.public, 'stable', repo, manifest, self.endpoint(manifest),
                         clock=lambda: self.now)

    def denied(self, exception, code, call, *args, **kwargs):
        with self.assertRaises(exception) as caught:
            call(*args, **kwargs)
        self.assertEqual(str(caught.exception), code)


class WriteGitTests(Fixture):
    """The Git half needs no signer, so it runs everywhere Git does."""

    def test_holder_may_write_with_uncommitted_and_unpushed_work(self):
        work = self.project('p')
        self.claim(work)
        (work / 'draft.txt').write_text('in progress')
        self.commit(work, 'safe.txt', 'local only')
        facts = assess_write(work, ME, env=self.env)
        self.assertEqual(facts['head'], self.git(work, 'rev-parse', 'HEAD'))
        self.assertNotEqual(facts['head'], facts['remote_sha'])

    def test_idle_other_owner_and_unreadable_marker_stop_the_write(self):
        work = self.project('p')
        # Idle is fine for starting but never for writing: the claim was not taken.
        self.denied(GitGateDenied, 'not-claimed', assess_write, work, ME, env=self.env)
        self.claim(work, OTHER)
        self.denied(GitGateDenied, 'busy-other-machine', assess_write, work, ME, env=self.env)
        same_tool_old = '`mac` ／ `Claude Code` ／ `㊣　26110800｜舊的｜工作中｜交棒0次`'
        self.claim(work, same_tool_old)
        self.denied(GitGateDenied, 'busy-same-tool-other-session', assess_write, work, ME,
                    env=self.env)
        self.commit(work, 'HANDOFF.md', '# HANDOFF\n')
        self.git(work, 'push', '--quiet')
        self.denied(GitGateDenied, 'owner-unknown', assess_write, work, ME, env=self.env)
        for bad in (IDLE, '`mac` ／ `Claude Code`', ''):
            self.denied(GitGateDenied, 'invalid-owner', assess_write, work, bad, env=self.env)

    def test_remote_taken_over_after_claim_is_seen_on_the_next_write(self):
        work = self.project('p')
        self.claim(work)
        assess_write(work, ME, env=self.env)
        other = self.root / 'other'
        self.git(self.root, 'clone', '--quiet', str(self.root / 'p.git'), str(other))
        self.claim(other, OTHER)
        # The local HANDOFF still names this session; only a fresh fetch shows it.
        self.assertIn(ME, (work / 'HANDOFF.md').read_text(encoding='utf-8'))
        self.denied(GitGateDenied, 'behind-pull-required', assess_write, work, ME, env=self.env)
        self.commit(work, 'mine.txt', 'x')
        self.denied(GitGateDenied, 'diverged', assess_write, work, ME, env=self.env)

    def test_offline_never_answers_from_the_cached_tracking_ref(self):
        work = self.project('p')
        self.claim(work)
        (self.root / 'p.git').rename(self.root / 'moved.git')
        self.denied(GitGateDenied, 'fetch-failed', assess_write, work, ME, env=self.env)
        self.git(work, 'switch', '--quiet', '--detach')
        self.denied(GitGateDenied, 'detached-head', assess_write, work, ME, env=self.env)


class ManagedWriteTests(Fixture):
    def test_both_gates_pass_and_every_write_asks_again(self):
        if not self.supported:
            return self.skipTest('ssh-keygen signer unavailable')
        work = self.project('p')
        self.claim(work)
        writer = ManagedWrite(work, ME, self.gate(work), env=self.env)
        receipt = writer.check(OP)
        self.assertEqual((receipt['operation'], receipt['branch'], receipt['epoch']),
                         (OP, 'main', 1))
        writer.check('d' * 32)
        self.assertEqual(self.calls, 2)

    def test_layer_is_named_and_git_refusal_spends_no_confirmation(self):
        if not self.supported:
            return self.skipTest('ssh-keygen signer unavailable')
        work = self.project('p')
        writer = ManagedWrite(work, ME, self.gate(work), env=self.env)
        self.denied(WriteDenied, 'git:not-claimed', writer.check, OP)
        self.assertEqual(self.calls, 0)
        self.claim(work)
        self.offline = True
        self.denied(WriteDenied, 'release:channel-unreachable', writer.check, OP)
        self.offline = False
        (work / PACKAGE[1]).write_text('hook edited in place\n', encoding='utf-8')
        self.denied(WriteDenied, 'release:component-drift', writer.check, OP)
        (work / PACKAGE[1]).write_text(f'{PACKAGE[1]} v1\n', encoding='utf-8')
        writer.check(OP)
        self.denied(WriteDenied, 'release:invalid-operation', writer.check, 'x')

    def test_batch_reports_release_drift_as_a_failure_not_eligible(self):
        if not self.supported:
            return self.skipTest('ssh-keygen signer unavailable')
        good = self.project('good')
        drift = self.project('drift')
        gates = {good: self.gate(good), drift: self.gate(drift)}
        # Committed and pushed, so Git is clean and aligned; only the package drifted.
        self.commit(drift, PACKAGE[0], 'skill edited in place\n')
        self.git(drift, 'push', '--quiet')
        report = assess_many([(good, 'active'), (drift, 'active')], ME, env=self.env,
                             confirm=lambda path: gates[Path(path)].confirm(OP))
        self.assertFalse(report['ok'])
        rows = {Path(row['target']).name: row for row in report['results']}
        self.assertEqual((rows['good']['outcome'], rows['good']['manifest']),
                         ('eligible', gates[good].digest))
        self.assertEqual((rows['drift']['outcome'], rows['drift']['code']),
                         ('failed', 'release:component-drift'))
        self.assertNotIn('manifest', rows['drift'])

    def test_batch_confirm_crash_is_a_target_error(self):
        good = self.project('good')

        def crash(path):
            raise RuntimeError('synthetic')
        report = assess_many([(good, 'active')], ME, env=self.env, confirm=crash)
        self.assertEqual((report['ok'], report['results'][0]['code']), (False, 'target-error'))
        # Without confirm the batch behaves as before.
        self.assertTrue(assess_many([(good, 'active')], ME, env=self.env)['ok'])
        with patch.object(batch, 'assess_start', side_effect=GitGateDenied('fetch-failed')):
            called = []
            report = assess_many([(good, 'active')], ME, env=self.env,
                                 confirm=lambda path: called.append(path))
        self.assertEqual((called, report['results'][0]['code']), ([], 'fetch-failed'))


if __name__ == '__main__':
    unittest.main()
