"""M1 manifest and per-write freshness gate, with a disposable ssh-keygen signer."""

import json
from pathlib import Path
import platform
import subprocess
import tempfile
from unittest import TestCase
from unittest.mock import patch

from experiments.v2 import release
from experiments.v2.contracts import Denied
from experiments.v2.release import WriteGate, build_manifest, manifest_digest, statement

PATHS = ('SKILL.md', 'hooks/git-freshness.sh', 'schema/settings.json')
OP = 'a' * 32


class ReleaseGateTests(TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='bootstrap-v2-release-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.now = 1000
        self.installed = self.root / 'installed'
        for path, text in zip(PATHS, ('skill v1\n', 'echo hook v1\n', '{"v":1}\n')):
            (self.installed / path).parent.mkdir(parents=True, exist_ok=True)
            (self.installed / path).write_text(text)
        self.manifest = build_manifest(self.installed, PATHS, '2026-11-09', 'formal', ['F33'])
        self.supported = platform.system() == 'Darwin' and release.VERIFIER.is_file()
        if self.supported:
            self.key, self.public = self.keypair('ci')
        self.channel_manifest = manifest_digest(self.manifest)
        self.channel_epoch = 5
        self.offline = False
        self.replay = None
        self.fetched = []

    def keypair(self, name):
        key = self.root / name
        subprocess.run([str(release.VERIFIER), '-q', '-t', 'ed25519', '-N', '', '-f', str(key)],
                       check=True, timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return key, b' '.join(key.with_suffix('.pub').read_bytes().split()[:2])

    def sign(self, document, key=None, namespace=release.NAMESPACE):
        return subprocess.run([str(release.VERIFIER), '-Y', 'sign', '-f', str(key or self.key),
                               '-n', namespace], input=document, capture_output=True,
                              check=True, timeout=3).stdout

    def endpoint(self, nonce):
        """Trusted channel stand-in. Offline and replay modes are failure inputs."""
        if self.offline:
            raise ConnectionError('synthetic outage')
        if self.replay is not None:
            return self.replay
        document = statement('stable', self.channel_epoch, self.channel_manifest, nonce,
                             self.now - 5, self.now + 60)
        answer = (document, self.sign(document))
        self.fetched.append(answer)
        return answer

    def gate(self, manifest=None, fetch=None):
        return WriteGate(self.public, 'stable', self.installed, manifest or self.manifest,
                         fetch or self.endpoint, clock=lambda: self.now)

    def denied(self, code, call, *args):
        with self.assertRaises(Denied) as caught:
            call(*args)
        self.assertEqual(str(caught.exception), code)

    def test_fresh_formal_release_confirms_each_operation(self):
        if not self.supported:
            return self.unsupported()
        gate = self.gate()
        first = gate.confirm(OP)
        self.assertEqual(first, {'operation': OP, 'epoch': 5, 'manifest': self.channel_manifest})
        gate.confirm('b' * 32)
        self.assertEqual(len(self.fetched), 2)  # every write asks again
        self.denied('invalid-operation', gate.confirm, 'not-an-op')

    def test_f33_old_confirmation_never_replaces_a_fresh_one(self):
        if not self.supported:
            return self.unsupported()
        gate = self.gate()
        gate.confirm(OP)
        self.offline = True
        self.denied('channel-unreachable', gate.confirm, OP)
        self.offline = False
        self.replay = self.fetched[-1]  # a perfectly valid, signed, cached answer
        self.denied('stale-confirmation', gate.confirm, OP)
        self.replay = None
        self.now += 120
        self.channel_epoch = 6
        gate.confirm(OP)
        self.replay = self.fetched[-1]
        self.denied('stale-confirmation', gate.confirm, OP)

    def test_f32_content_change_without_version_change_is_found_by_digest(self):
        if not self.supported:
            return self.unsupported()
        (self.installed / 'SKILL.md').write_text('skill v1 edited in place\n')
        self.denied('component-drift', self.gate().confirm, OP)
        (self.installed / 'SKILL.md').write_text('skill v1\n')
        self.gate().confirm(OP)
        (self.installed / 'SKILL.md').unlink()
        (self.installed / 'SKILL.md').symlink_to(self.root / 'ci')
        self.denied('invalid-component', self.gate().confirm, OP)

    def test_f18_hook_or_schema_only_release_stops_old_clients(self):
        if not self.supported:
            return self.unsupported()
        for path in ('hooks/git-freshness.sh', 'schema/settings.json'):
            with self.subTest(changed=path):
                source = self.root / ('source-' + path.replace('/', '-'))
                for name in PATHS:
                    (source / name).parent.mkdir(parents=True, exist_ok=True)
                    (source / name).write_bytes((self.installed / name).read_bytes())
                (source / path).write_text('changed only here\n')
                new = build_manifest(source, PATHS, self.manifest['version'], 'formal')
                self.assertEqual(new['version'], self.manifest['version'])
                self.assertEqual(new['components']['SKILL.md'],
                                 self.manifest['components']['SKILL.md'])
                self.channel_manifest = manifest_digest(new)
                self.denied('release-mismatch', self.gate().confirm, OP)

    def test_signature_channel_epoch_expiry_and_kind_are_enforced(self):
        if not self.supported:
            return self.unsupported()
        other_key, other_public = self.keypair('attacker')
        document = statement('stable', 5, self.channel_manifest, 'n' * 32, 995, 1060)

        def answer(doc, signature):
            return lambda nonce: (doc.replace(b'n' * 32, nonce.encode()), signature)

        forged = lambda nonce: (statement('stable', 5, self.channel_manifest, nonce, 995, 1060),
                                self.sign(statement('stable', 5, self.channel_manifest,
                                                    nonce, 995, 1060), key=other_key))
        self.denied('invalid-channel-signature', self.gate(fetch=forged).confirm, OP)
        wrong_namespace = lambda nonce: (
            statement('stable', 5, self.channel_manifest, nonce, 995, 1060),
            self.sign(statement('stable', 5, self.channel_manifest, nonce, 995, 1060),
                      namespace='project-bootstrap-v2-effect'))
        self.denied('invalid-channel-signature', self.gate(fetch=wrong_namespace).confirm, OP)
        tampered = answer(document, self.sign(document))
        self.denied('invalid-channel-signature', self.gate(fetch=tampered).confirm, OP)

        def signed(**fields):
            def fetch(nonce):
                values = dict(channel='stable', epoch=5, manifest=self.channel_manifest,
                              nonce=nonce, issued=995, expires=1060)
                values.update(fields)
                doc = statement(**values)
                return doc, self.sign(doc)
            return fetch
        self.denied('wrong-channel', self.gate(fetch=signed(channel='beta')).confirm, OP)
        self.denied('stale-confirmation', self.gate(fetch=signed(expires=1000)).confirm, OP)
        self.denied('stale-confirmation', self.gate(fetch=signed(issued=1001)).confirm, OP)
        self.denied('invalid-channel-statement', self.gate(fetch=signed(epoch='5')).confirm, OP)
        gate = self.gate()
        self.channel_epoch = 9
        gate.confirm(OP)
        self.channel_epoch = 8
        self.denied('channel-rollback', gate.confirm, OP)
        debug = dict(self.manifest, kind='debug')
        self.channel_manifest = manifest_digest(debug)
        self.denied('debug-release', self.gate(manifest=debug).confirm, OP)

    def test_statement_shape_and_key_format_are_checked_even_when_signed(self):
        if not self.supported:
            return self.unsupported()
        for key in (b'ssh-rsa ' + self.public.split()[1], self.public + b' extra', b'', 'text'):
            with self.subTest(key=key):
                with self.assertRaises(Denied) as caught:
                    WriteGate(key, 'stable', self.installed, self.manifest, self.endpoint)
                self.assertEqual(str(caught.exception), 'invalid-channel-key')

        def signed_document(build):
            def fetch(nonce):
                doc = build(nonce)
                return doc, self.sign(doc)
            return fetch
        base = lambda nonce: dict(channel='stable', epoch=5, manifest=self.channel_manifest,
                                  nonce=nonce, issued=995, expires=1060)
        extra = signed_document(lambda nonce: json.dumps(dict(base(nonce), note='x'),
                                                         sort_keys=True).encode())
        self.denied('invalid-channel-statement', self.gate(fetch=extra).confirm, OP)
        # A valid, signed statement padded past the size limit is still refused.
        oversized = signed_document(lambda nonce: statement(**base(nonce)) + b' ' * 1024)
        self.denied('invalid-channel-statement', self.gate(fetch=oversized).confirm, OP)

    def test_manifest_inputs_are_validated(self):
        outside = self.root / 'outside.txt'
        outside.write_text('not part of the package\n')
        (self.installed / 'hooks' / 'nested.txt').write_text('x\n')
        # Every escaping path names a file that really exists.
        for paths in (('../outside.txt',), (str(outside),), ('hooks//nested.txt',),
                      ('hooks/../SKILL.md',), ('./SKILL.md',), ('missing.txt',), ()):
            with self.subTest(paths=paths):
                with self.assertRaises(Denied):
                    build_manifest(self.installed, paths, 'v', 'formal')
        with self.assertRaises(Denied):
            build_manifest(self.installed, PATHS, 'v', 'nightly')
        same = build_manifest(self.installed, reversed(PATHS), '2026-11-09', 'formal', ['F33'])
        self.assertEqual(manifest_digest(same), manifest_digest(self.manifest))

    def unsupported(self):
        with patch.object(release, 'VERIFIER', self.root / 'unavailable'):
            gate = WriteGate(b'ssh-ed25519 ' + b'A' * 68, 'stable', self.installed,
                             self.manifest, lambda nonce: (b'{}', b'sig'))
            self.denied('channel-verifier-unavailable', gate.confirm, OP)
