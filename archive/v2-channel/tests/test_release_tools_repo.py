"""P2 slice 3b prep: tools/release_package.py → tools/install_package.py end to end.

Imports tools/, so it is a *_repo test and stays out of mutation groups. The
verifier run and the git cleanliness check are injected: running the real
verifier here would take minutes and the working tree is often dirty while
developing. The real kit in src/kit is built and released.
"""
import contextlib
import hashlib
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

from project_bootstrap import channel, pointer, release as release_module
from project_bootstrap.contracts import Denied

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import install_package  # noqa: E402
import release_package  # noqa: E402

SUPPORTED = (platform.system() == 'Darwin' and release_module.VERIFIER.is_file()
             and shutil.which('git') is not None)
OK_RUN = ('[  ok  ] alpha\n[  ok  ] beta\n', 0)


class ReleaseToolTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='release-tools-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        if not SUPPORTED:
            return
        self.source = self.root / 'source.git'
        subprocess.run(['git', 'init', '-q', '--bare', str(self.source)], check=True)
        self.blob = subprocess.run(['git', '-C', str(self.source), 'hash-object', '-w', '--stdin'],
                                   input=b'x', capture_output=True, check=True).stdout.decode().strip()
        self.key = self.root / 'ci'
        subprocess.run([str(release_module.VERIFIER), '-q', '-t', 'ed25519', '-N', '', '-f', str(self.key)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.public = ' '.join(self.key.with_suffix('.pub').read_text().split()[:2])
        self.keys_file = self.root / 'release-keys.txt'
        self.keys_file.write_text('# test\n' + self.public + '\n')
        patcher = mock.patch.object(release_package, 'KEYS', self.keys_file)
        patcher.start()
        self.addCleanup(patcher.stop)

    def fake_git(self, dirty=''):
        def git(*args):
            if args[0] == 'status':
                return dirty
            if args[0] == 'rev-parse':
                return 'f' * 40
            raise AssertionError(args)
        return mock.patch.object(release_package, 'git', git)

    def release(self, verify=OK_RUN, dirty='', channel_name='beta', out='out'):
        args = types.SimpleNamespace(channel=channel_name, source=str(self.source),
                                     signing_key=str(self.key), out=str(self.root / out))
        output = io.StringIO()
        with self.fake_git(dirty), contextlib.redirect_stdout(output):
            result = release_package.release(args, verify=lambda: verify, now=lambda: 0)
        self.printed = output.getvalue()
        return result

    def publish(self, result):
        subprocess.run(['git', '-C', str(self.source), 'update-ref', result['tag'], self.blob], check=True)

    def install(self, result, project, seed=True, check=True, channel_name='beta'):
        archive, record, signature, _ = result['assets']
        args = types.SimpleNamespace(project=str(project), cache=str(self.root / 'cache'),
                                     archive=archive, record=record, signature=signature,
                                     channel=channel_name, source=str(self.source), seed=seed, check=check)
        return install_package.install(args, root_keys_text=self.keys_file.read_text())

    def denied(self, code, call, *args, **kwargs):
        with self.assertRaises(Denied) as caught:
            call(*args, **kwargs)
        self.assertEqual(str(caught.exception), code)

    def test_release_then_install_into_an_empty_project(self):
        if not SUPPORTED:
            return self.fails_closed_without_signer()
        first = self.release()
        self.assertTrue(first['tag'].startswith('refs/tags/channel/beta/1-'))
        self.assertEqual(first['epoch'], 1)
        self.assertEqual([Path(a).name.split('.', 1)[1] for a in first['assets']],
                         ['tar.gz', 'record.json', 'sig', 'report.json'])
        self.assertIn('[  ok  ] alpha\n[  ok  ] beta\n', self.printed)
        self.assertIn('verify_bootstrap.py exit 0', self.printed)
        record = channel.parse_record(Path(first['assets'][1]).read_bytes())
        report_file = Path(first['assets'][3]).read_bytes()
        self.assertEqual(hashlib.sha256(report_file).hexdigest(), record['report'])
        self.assertEqual(json.loads(report_file)['overall'], '通過')
        self.publish(first)
        project = self.root / 'project'
        result = self.install(first, project)
        self.assertEqual(result['keys'], 'root')
        self.assertEqual(result['check']['installed'], first['digest'])
        self.assertFalse(result['check']['pinned'])
        self.assertTrue((project / '.claude/skills/handoff/SKILL.md').is_file())
        self.assertEqual(pointer.parse((project / pointer.POINTER).read_text())['source'], str(self.source))

    def test_second_release_upgrades_along_the_chain(self):
        if not SUPPORTED:
            return self.fails_closed_without_signer()
        first = self.release(out='one')
        self.publish(first)
        project = self.root / 'project'
        self.install(first, project)
        second = self.release(out='two')
        self.assertEqual(second['epoch'], 2)
        self.publish(second)
        gate = channel.GitWriteCheck(project, self.root / 'cache')
        self.denied('channel-epoch-mismatch', gate.confirm, 'a' * 32, 'x.md')  # same content, new epoch
        upgraded = self.install(second, project, seed=False)
        self.assertEqual(upgraded['keys'], 'chain')
        self.assertEqual(upgraded['epoch'], 2)

    def test_release_refusals(self):
        if not SUPPORTED:
            return self.fails_closed_without_signer()
        self.denied('checkout-not-clean', self.release, dirty=' M x')
        self.denied('unverified-source:verify_bootstrap:gamma,verify_bootstrap', self.release,
                    verify=('[  ok  ] alpha\n[ FAIL ] gamma\n', 2))
        self.denied('unverified-source:verify_bootstrap:gamma,verify_bootstrap', self.release,
                    verify=('[  ok  ] alpha\n[ skip ] gamma\n', 1))
        self.denied('invalid-channel', self.release, channel_name='Beta')
        self.keys_file.write_text('# no key yet\n')
        self.denied('no-release-keys', self.release)

    def test_install_refusals(self):
        if not SUPPORTED:
            return self.fails_closed_without_signer()
        first = self.release()
        self.publish(first)
        self.denied('wrong-channel', self.install, first, self.root / 'p1', channel_name='stable')
        self.assertFalse((self.root / 'cache').exists())
        busy = self.root / 'busy'
        busy.mkdir()
        (busy / 'README.md').write_text('mine\n')
        self.denied('project-not-empty', self.install, first, busy)
        self.assertFalse((busy / pointer.POINTER).exists())
        other = self.root / 'other'
        subprocess.run([str(release_module.VERIFIER), '-q', '-t', 'ed25519', '-N', '', '-f', str(other)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.keys_file.write_text(' '.join(other.with_suffix('.pub').read_text().split()[:2]) + '\n')
        self.denied('not-signed-by-trusted-key', self.install, first, self.root / 'p2')

    def test_main_reports_refusal(self):
        if not SUPPORTED:
            return self.fails_closed_without_signer()
        self.keys_file.write_text('')
        with self.fake_git(), mock.patch('builtins.print') as printed:
            code = release_package.main(['--channel', 'beta', '--source', str(self.source),
                                         '--signing-key', str(self.key), '--out', str(self.root / 'o')])
        self.assertEqual(code, 1)
        self.assertIn('no-release-keys', printed.call_args[0][0])

    def fails_closed_without_signer(self):
        with mock.patch.object(channel, 'VERIFIER', self.root / 'missing'):
            with self.assertRaises(Denied) as caught:
                channel._verify(b'{}', b'sig', ['ssh-ed25519 ' + 'A' * 68])
        self.assertEqual(str(caught.exception), 'release-verifier-unavailable')


if __name__ == '__main__':
    unittest.main()
