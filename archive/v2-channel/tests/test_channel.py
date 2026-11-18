"""P2 slice 3a: signed releases, key chain and Git-tag channel, against a local bare repository."""
import json
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from project_bootstrap import channel, package, pointer, release
from project_bootstrap.contracts import Denied

PROSE = '# kit\n\n> 版本：**2026-11-11.5**（測試）\n'
FILES = {
    '.claude/skills/handoff/SKILL.md': 'skill v1\n',
    '.claude/hooks/check.sh': '#!/bin/sh\necho v1\n',
    'AGENTS.md': '# agents\n',
}
OWNERS = {
    '.claude/skills/handoff/SKILL.md': {'owner': 'core', 'update': 'whole'},
    '.claude/hooks/check.sh': {'owner': 'adapter', 'update': 'whole'},
    'AGENTS.md': {'owner': 'project', 'update': 'seed'},
}
REPORT = {'overall': '通過', 'rows': [{'id': 'F18', 'state': '本輪實查'}]}
OP = 'a' * 32
NOW = 1_794_000_000
YESTERDAY = time.strftime('%Y-%m-%d', time.gmtime(NOW - 86400))
TODAY = time.strftime('%Y-%m-%d', time.gmtime(NOW))
SUPPORTED = platform.system() == 'Darwin' and release.VERIFIER.is_file() and shutil.which('git')


def needs_signer(test):
    """Without ssh-keygen, check verification fails closed instead of skipping (no skips in A4)."""
    def run(self):
        if SUPPORTED:
            return test(self)
        folder, _ = package.build(PROSE, FILES, OWNERS, 'kit')
        self.addCleanup(shutil.rmtree, folder, True)
        with patch.object(channel, 'VERIFIER', self.root / 'unavailable'):
            with self.assertRaises(Denied) as caught:
                channel.install(self.root / 'cache', folder, b'{}', b'sig', ['ssh-ed25519 ' + 'A' * 68])
        self.assertEqual(str(caught.exception), 'release-verifier-unavailable')
    run.__name__, run.__doc__ = test.__name__, test.__doc__
    return run


class ChannelTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='channel-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        if not SUPPORTED:
            return
        self.cache = self.root / 'cache'
        self.project = self.root / 'project'
        self.source = self.root / 'source.git'
        self.git('init', '-q', '--bare', str(self.source))
        self.blob = self.git('-C', str(self.source), 'hash-object', '-w', '--stdin', input=b'channel\n')
        self.k1, self.p1 = self.keypair('k1')
        self.k2, self.p2 = self.keypair('k2')
        self.k3, self.p3 = self.keypair('k3')
        self.now = NOW
        self.calls = 0
        folder, doc, sig, tag = self.make_release(FILES, epoch=1, next_keys=[self.p2], key=self.k1)
        self.first = channel.install(self.cache, folder, doc, sig, [self.p1])
        self.installed = self.first['manifest']
        self.tag(tag)
        for path, text in FILES.items():
            (self.project / path).parent.mkdir(parents=True, exist_ok=True)
            (self.project / path).write_text(text)
        self.write_pointer()

    # helpers
    def git(self, *args, input=None):
        return subprocess.run(['git', *args], input=input, capture_output=True, check=True,
                              timeout=10).stdout.decode().strip()

    def keypair(self, name):
        key = self.root / name
        subprocess.run([str(release.VERIFIER), '-q', '-t', 'ed25519', '-N', '', '-f', str(key)],
                       check=True, timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return key, ' '.join(key.with_suffix('.pub').read_text().split()[:2])

    def signer(self, key, namespace=channel.NAMESPACE):
        def sign(document):
            return subprocess.run([str(release.VERIFIER), '-Y', 'sign', '-f', str(key), '-n', namespace],
                                  input=document, capture_output=True, check=True, timeout=3).stdout
        return sign

    def debug(self, files=FILES):
        folder, _ = package.build(PROSE, files, OWNERS, 'kit')
        self.addCleanup(shutil.rmtree, folder, True)
        return folder

    def make_release(self, files, epoch, next_keys, key, report=REPORT):
        folder, doc, sig, tag = channel.release(self.debug(files), report, 'stable', epoch, next_keys,
                                                self.signer(key))
        self.addCleanup(shutil.rmtree, str(Path(folder).parent), True)
        return folder, doc, sig, tag

    def tag(self, name):
        self.git('-C', str(self.source), 'update-ref', name, self.blob)

    def write_pointer(self, **changes):
        data = {'schema': 1, 'channel': 'stable', 'installed': self.installed, 'exception': None,
                'source': str(self.source)}
        data.update(changes)
        data = {k: v for k, v in data.items() if v is not ...}
        path = self.project / pointer.POINTER
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding='utf-8')

    def counting_run(self, *args, **kwargs):
        self.calls += 1
        return subprocess.run(*args, **kwargs)

    def check(self, run=None):
        return channel.GitWriteCheck(self.project, self.cache, run=run or self.counting_run,
                                     clock=lambda: self.now)

    def denied(self, code, call, *args):
        with self.assertRaises(Denied) as caught:
            call(*args)
        self.assertEqual(str(caught.exception), code)

    def upgrade(self, epoch=2, key=None, files=None):
        files = files or dict(FILES, **{'.claude/hooks/check.sh': '#!/bin/sh\necho v%d\n' % epoch})
        folder, doc, sig, tag = self.make_release(files, epoch, [self.p2], key or self.k2)
        return folder, doc, sig, tag

    # release (CI side)
    @needs_signer
    def test_release_output(self):
        folder, doc, sig, tag = self.make_release(FILES, 3, [self.p2, self.p1], self.k1)
        manifest = json.loads((Path(folder) / package.MANIFEST).read_text(encoding='utf-8'))
        self.assertEqual(manifest['kind'], 'formal')
        self.assertEqual(package.check(folder), [])
        fields = channel.parse_record(doc)
        self.assertEqual(fields['manifest'], package.digest(manifest))
        self.assertEqual(fields['next_keys'], sorted([self.p1, self.p2]))
        self.assertEqual(fields['report'], channel.report_digest(REPORT))
        self.assertEqual(tag, 'refs/tags/channel/stable/3-' + fields['manifest'])
        channel._verify(doc, sig, [self.p1])

    @needs_signer
    def test_release_refuses(self):
        sign = self.signer(self.k1)
        unverified = [{'overall': '不通過', 'rows': [{'state': '本輪實查'}]},
                      {'overall': '通過', 'rows': [{'state': '沿用'}]},
                      {'overall': '通過', 'rows': []}, None]
        for report in unverified:
            with self.subTest(report=report):
                self.denied('unverified-source', channel.release, self.debug(), report, 'stable', 1, [self.p1], sign)
        for bad in ('Stable', '', None):
            self.denied('invalid-channel', channel.release, self.debug(), REPORT, bad, 1, [self.p1], sign)
        for bad in (0, True, '1', 1_000_000_000):
            self.denied('invalid-epoch', channel.release, self.debug(), REPORT, 'stable', bad, [self.p1], sign)
        for bad in ([], ['ssh-rsa AAAA'], 'ssh-ed25519 ' + 'A' * 68):
            self.denied('invalid-keys', channel.release, self.debug(), REPORT, 'stable', 1, bad, sign)
        formal, _, _, _ = self.make_release(FILES, 1, [self.p1], self.k1)
        self.denied('not-a-debug-build', channel.release, formal, REPORT, 'stable', 2, [self.p1], sign)
        broken = self.debug()
        (Path(broken) / 'AGENTS.md').write_text('edited\n')
        self.denied('bad-package:digest:AGENTS.md', channel.release, broken, REPORT, 'stable', 1, [self.p1], sign)

    # install (client side)
    @needs_signer
    def test_install_checks_signature_and_record(self):
        folder, doc, sig, _ = self.upgrade()
        self.denied('not-signed-by-trusted-key', channel.install, self.cache, folder, doc, sig, [self.p1])
        self.denied('not-signed-by-trusted-key', channel.install, self.cache, folder,
                    doc.replace(b'"epoch":2', b'"epoch":9'), sig, [self.p2])
        other_ns = self.signer(self.k2, namespace='other')(doc)
        self.denied('not-signed-by-trusted-key', channel.install, self.cache, folder, doc, other_ns, [self.p2])
        self.denied('invalid-release-signature', channel.install, self.cache, folder, doc, b'', [self.p2])
        self.denied('invalid-keys', channel.install, self.cache, folder, doc, sig, [])
        damaged = Path(tempfile.mkdtemp(dir=self.root)) / 'p'
        shutil.copytree(folder, damaged)
        (damaged / 'AGENTS.md').write_text('edited\n')
        self.denied('bad-package:digest:AGENTS.md', channel.install, self.cache, damaged, doc, sig, [self.p2])
        _, other_doc, other_sig, _ = self.upgrade(epoch=3)
        self.denied('release-mismatch', channel.install, self.cache, folder, other_doc, other_sig, [self.p2])
        fields = channel.install(self.cache, folder, doc, sig, [self.p2])
        self.assertEqual(fields['epoch'], 2)
        self.assertEqual(package.check(self.cache / fields['manifest']), [])

    @needs_signer
    def test_install_refuses_debug_and_malformed_records(self):
        sign = self.signer(self.k1)
        debug = self.debug()
        manifest = json.loads((Path(debug) / package.MANIFEST).read_text(encoding='utf-8'))
        doc = channel.record_bytes('stable', 1, package.digest(manifest), 'r', [self.p1])
        self.denied('debug-release', channel.install, self.cache, debug, doc, sign(doc), [self.p1])
        bad_docs = [
            b'{"channel":"stable"}',
            json.dumps({'channel': 'stable', 'epoch': 1, 'manifest': 'a' * 64, 'report': 'r',
                        'next_keys': [self.p1]}).encode('ascii'),  # not canonical
            channel.record_bytes('stable', 1, 'a' * 64, 'r', [self.p1]).replace(b'"epoch":1', b'"epoch":0'),
            channel.record_bytes('stable', 1, 'a' * 64, 'r', [self.p1]).replace(b'"epoch":1', b'"epoch":"1"'),
            channel.record_bytes('stable', 1, 'A' * 64, 'r', [self.p1]),
            channel.record_bytes('BAD', 1, 'a' * 64, 'r', [self.p1]),
            b'{"channel":"stable","channel":"stable"}',
            b'\xff',
        ]
        for doc in bad_docs:
            with self.subTest(doc=doc[:40]):
                self.denied('invalid-release-record', channel.install, self.cache, debug, doc, sign(doc), [self.p1])

    @needs_signer
    def test_key_rotation_follows_the_chain(self):
        self.assertEqual(channel.trusted_after(self.cache, self.installed), [self.p2])
        old_key = self.upgrade(epoch=2, key=self.k1)
        self.denied('not-signed-by-trusted-key', channel.install, self.cache, *old_key[:3],
                    channel.trusted_after(self.cache, self.installed))
        stranger = self.upgrade(epoch=2, key=self.k3)
        self.denied('not-signed-by-trusted-key', channel.install, self.cache, *stranger[:3],
                    channel.trusted_after(self.cache, self.installed))
        folder, doc, sig, _ = self.upgrade(epoch=2, key=self.k2)
        fields = channel.install(self.cache, folder, doc, sig, channel.trusted_after(self.cache, self.installed))
        self.assertEqual(channel.trusted_after(self.cache, fields['manifest']), [self.p2])

    @needs_signer
    def test_installed_record_problems(self):
        path = self.cache / (self.installed + channel.RECORD_SUFFIX)
        good = path.read_text(encoding='utf-8')
        path.write_text('{', encoding='utf-8')
        self.denied('invalid-release-record', channel.installed_record, self.cache, self.installed)
        path.write_text(json.dumps({'document': 'x', 'signature': '***'}), encoding='utf-8')
        self.denied('invalid-release-record', channel.installed_record, self.cache, self.installed)
        path.write_text(good, encoding='utf-8')
        shutil.copy(path, self.cache / ('b' * 64 + channel.RECORD_SUFFIX))
        self.denied('invalid-release-record', channel.installed_record, self.cache, 'b' * 64)
        path.unlink()
        self.denied('release-record-missing', channel.installed_record, self.cache, self.installed)

    # per-write check against the channel tags
    @needs_signer
    def test_matching_channel_lets_writes_on_and_asks_every_time(self):
        gate = self.check()
        result = gate.confirm(OP, 'docs/a.md')
        self.assertEqual(result, {'operation': OP, 'target': 'docs/a.md', 'epoch': 1,
                                  'version': '2026-11-11.5', 'installed': self.installed,
                                  'latest': self.installed, 'installed_epoch': 1, 'pinned': False})
        gate.confirm(OP, 'docs/a.md')
        self.assertEqual(self.calls, 2)
        (self.project / 'AGENTS.md').write_text('# ours\n')
        gate.confirm(OP, 'AGENTS.md')

    @needs_signer
    def test_unrelated_tags_are_ignored(self):
        self.tag('refs/tags/v1.0')
        self.tag('refs/tags/channel/beta/7-' + 'c' * 64)
        self.tag('refs/tags/channel/stable-old/9-' + 'c' * 64)
        self.check().confirm(OP, 'x.md')

    @needs_signer
    def test_offline_refuses(self):
        shutil.rmtree(self.source)
        self.denied('channel-unreachable', self.check().confirm, OP, 'x.md')

        def broken(*args, **kwargs):
            raise subprocess.TimeoutExpired('git', 1)
        self.denied('channel-unreachable', self.check(broken).confirm, OP, 'x.md')

    @needs_signer
    def test_newer_release_stops_old_projects(self):
        _, _, _, tag = self.upgrade()
        self.tag(tag)
        self.denied('release-mismatch', self.check().confirm, OP, 'x.md')

    @needs_signer
    def test_declared_exception_pins_the_installed_release(self):
        _, _, _, tag = self.upgrade()
        self.tag(tag)
        exception = {'pin': self.installed, 'paths': ['docs'], 'reason': 'r', 'declared_by': 'me',
                     'review_by': TODAY}
        self.write_pointer(exception=exception)
        self.assertTrue(self.check().confirm(OP, 'docs/a.md')['pinned'])
        self.denied('exception-out-of-scope', self.check().confirm, OP, 'src/a.md')
        self.write_pointer(exception=dict(exception, review_by=YESTERDAY))
        self.denied('exception-expired', self.check().confirm, OP, 'docs/a.md')

    @needs_signer
    def test_rollback_and_forged_tags(self):
        folder, doc, sig, tag = self.upgrade()
        fields = channel.install(self.cache, folder, doc, sig, [self.p2])
        self.installed = fields['manifest']
        self.write_pointer()
        shutil.copy(Path(folder) / '.claude/hooks/check.sh', self.project / '.claude/hooks/check.sh')
        self.denied('channel-rollback', self.check().confirm, OP, 'x.md')  # only epoch 1 is tagged
        self.tag(tag)
        self.check().confirm(OP, 'x.md')
        self.tag('refs/tags/channel/stable/9-' + self.installed)
        self.denied('channel-epoch-mismatch', self.check().confirm, OP, 'x.md')

    @needs_signer
    def test_forged_higher_epoch_to_old_release_does_not_unlock_it(self):
        _, _, _, tag = self.upgrade()
        self.tag(tag)
        self.tag('refs/tags/channel/stable/9-' + self.installed)
        self.denied('channel-epoch-mismatch', self.check().confirm, OP, 'x.md')

    @needs_signer
    def test_conflicting_and_malformed_tags(self):
        self.tag('refs/tags/channel/stable/1-' + 'c' * 64)
        self.denied('channel-conflict', self.check().confirm, OP, 'x.md')
        self.git('-C', str(self.source), 'update-ref', '-d', 'refs/tags/channel/stable/1-' + self.installed)
        self.denied('channel-conflict', self.check().confirm, OP, 'x.md')
        self.git('-C', str(self.source), 'update-ref', '-d', 'refs/tags/channel/stable/1-' + 'c' * 64)
        self.denied('channel-empty', self.check().confirm, OP, 'x.md')
        for name in ('refs/tags/channel/stable/01-' + self.installed,
                     'refs/tags/channel/stable/2-' + 'C' * 64,
                     'refs/tags/channel/stable/latest'):
            with self.subTest(name=name):
                self.tag(name)
                self.denied('invalid-channel-tag', self.check().confirm, OP, 'x.md')
                self.git('-C', str(self.source), 'update-ref', '-d', name)

    @needs_signer
    def test_installed_epoch_survives_a_new_process(self):
        folder, doc, sig, _ = self.upgrade()
        self.installed = channel.install(self.cache, folder, doc, sig, [self.p2])['manifest']
        self.write_pointer()
        shutil.copy(Path(folder) / '.claude/hooks/check.sh', self.project / '.claude/hooks/check.sh')
        for _ in range(2):
            self.denied('channel-rollback', self.check().confirm, OP, 'x.md')

    @needs_signer
    def test_pointer_cache_and_project_problems(self):
        self.write_pointer(source=...)
        self.denied('no-source', self.check().confirm, OP, 'x.md')
        self.write_pointer(channel='beta')
        self.denied('wrong-channel', self.check().confirm, OP, 'x.md')
        self.write_pointer()
        (self.project / '.claude/hooks/check.sh').write_text('#!/bin/sh\necho edited\n')
        self.denied('component-drift:.claude/hooks/check.sh', self.check().confirm, OP, 'x.md')
        (self.project / '.claude/hooks/check.sh').write_text(FILES['.claude/hooks/check.sh'])
        (self.cache / (self.installed + channel.RECORD_SUFFIX)).unlink()
        self.denied('release-record-missing', self.check().confirm, OP, 'x.md')
        self.denied('invalid-operation', self.check().confirm, 'x', 'x.md')
        self.denied('invalid-target', self.check().confirm, OP, '../x')
        self.assertEqual(self.calls, 0)

    @needs_signer
    def test_debug_package_in_cache_refused(self):
        debug = self.debug()
        manifest = json.loads((Path(debug) / package.MANIFEST).read_text(encoding='utf-8'))
        digest = package.digest(manifest)
        shutil.copytree(debug, self.cache / digest)
        self.write_pointer(installed=digest)
        self.denied('debug-release', self.check().confirm, OP, 'x.md')

    @needs_signer
    def test_list_channel_problems(self):
        class Result:
            def __init__(self, code, out):
                self.returncode, self.stdout = code, out
        self.denied('channel-unreachable', channel.list_channel, 'x', 'stable', lambda *a, **k: Result(128, b''))
        self.denied('invalid-channel-tag', channel.list_channel, 'x', 'stable', lambda *a, **k: Result(0, b'\xff\n'))

        def missing(*args, **kwargs):
            raise OSError('no git')
        self.denied('channel-unreachable', channel.list_channel, 'x', 'stable', missing)
        self.assertEqual(channel.list_channel(str(self.source), 'stable'), [(1, self.installed)])

    def test_record_size_and_type(self):
        keys = ['ssh-ed25519 ' + 'A' * 64 + '%04d' % i for i in range(60)]
        big = channel.record_bytes('stable', 1, 'a' * 64, 'r', keys)
        self.assertGreater(len(big), 4096)
        for document in (big, b'', 'text'):
            with self.subTest(size=len(document)):
                self.denied('invalid-release-record', channel.parse_record, document)

    def test_tag_name_and_newest(self):
        self.assertEqual(channel.tag_name('stable', 4, 'a' * 64), 'refs/tags/channel/stable/4-' + 'a' * 64)
        for args in (('Stable', 1, 'a' * 64), ('stable', 0, 'a' * 64), ('stable', 1, 'A' * 64)):
            with self.subTest(args=args):
                self.denied('invalid-tag', channel.tag_name, *args)
        self.assertEqual(channel.newest([(1, 'a'), (3, 'b'), (2, 'c')]), (3, 'b'))
        self.assertEqual(channel.newest([(3, 'b'), (3, 'b')]), (3, 'b'))
        self.denied('channel-conflict', channel.newest, [(3, 'b'), (3, 'c'), (1, 'a')])
        self.denied('channel-empty', channel.newest, [])


class PointerSourceTests(unittest.TestCase):
    BASE = {'schema': 1, 'channel': 'stable', 'installed': 'a' * 64, 'exception': None}

    def test_source_field(self):
        for good in ('https://github.com/o/r.git', '/tmp/source.git', 'file:///tmp/source.git'):
            self.assertEqual(pointer.parse(json.dumps(dict(self.BASE, source=good)))['source'], good)
        for bad in ('-uhack', 'ssh://x', 'http://x', '', 5, 'https://a b', '/x\n'):
            with self.subTest(bad=bad), self.assertRaises(Denied) as caught:
                pointer.parse(json.dumps(dict(self.BASE, source=bad)))
            self.assertEqual(str(caught.exception), 'invalid-pointer:source')
        with self.assertRaises(Denied):
            pointer.parse(json.dumps(dict(self.BASE, source='/x', other=1)))


if __name__ == '__main__':
    unittest.main()
