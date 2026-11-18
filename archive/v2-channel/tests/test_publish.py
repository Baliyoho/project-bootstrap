"""F35: unverified, forged or non-CI releases are refused and nothing is written."""

import copy
from pathlib import Path
import platform
import subprocess
import tempfile
from unittest import TestCase
from unittest.mock import patch

from project_bootstrap import publish as pub
from project_bootstrap.contracts import Denied
from project_bootstrap.release import build_manifest

ROW = {'claim': 'verify_bootstrap', 'state': '本輪實查', 'reason': 'PASS', 'evidence': 'e1'}
REPORT = {'overall': '通過', 'rows': [ROW, dict(ROW, claim='verify_v2', evidence='e2')]}


class PublishGateTests(TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='bootstrap-v2-publish-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / 'src').mkdir()
        (self.root / 'src/SKILL.md').write_text('skill\n')
        (self.root / 'out').mkdir()
        self.out = self.root / 'out'
        self.manifest = build_manifest(self.root / 'src', ['SKILL.md'], '2026-11-10', 'formal')
        self.supported = platform.system() == 'Darwin' and pub.VERIFIER.is_file()
        if self.supported:
            self.key, self.public = self.keypair('ci')

    def keypair(self, name):
        key = self.root / name
        subprocess.run([str(pub.VERIFIER), '-q', '-t', 'ed25519', '-N', '', '-f', str(key)],
                       check=True, timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return key, b' '.join(key.with_suffix('.pub').read_bytes().split()[:2])

    def sign(self, document, key=None, namespace=pub.NAMESPACE):
        return subprocess.run([str(pub.VERIFIER), '-Y', 'sign', '-f', str(key or self.key),
                               '-n', namespace], input=document, capture_output=True,
                              check=True, timeout=3).stdout

    def attempt(self, manifest=None, report=None, document=None, signature=None, key=None):
        manifest = manifest or self.manifest
        report = REPORT if report is None else report
        document = pub.attestation(manifest, report) if document is None else document
        signature = signature if signature is not None else self.sign(document)
        return pub.publish(key or self.public, manifest, report, document, signature,
                           b'package', self.out)

    def refused(self, code, **kwargs):
        with self.assertRaises(Denied) as caught:
            self.attempt(**kwargs)
        self.assertEqual(str(caught.exception), code)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_verified_ci_signed_release_is_published_once(self):
        if not self.supported:
            return self.unsupported()
        target = self.attempt()
        self.assertEqual((target.name, target.read_bytes()), ('2026-11-10-formal.pkg', b'package'))
        with self.assertRaises(Denied) as caught:
            self.attempt()
        self.assertEqual(str(caught.exception), 'already-published')

    def test_fail_skip_reuse_or_empty_reports_are_refused_for_any_kind(self):
        if not self.supported:
            return self.unsupported()
        debug = build_manifest(self.root / 'src', ['SKILL.md'], '2026-11-10', 'debug')
        bad = [{'overall': '不通過', 'rows': [dict(ROW, state='不通過')]},
               {'overall': '未驗證', 'rows': [dict(ROW, state='未驗證')]},
               {'overall': '通過', 'rows': [dict(ROW, state='沿用')]},
               {'overall': '通過', 'rows': [ROW, dict(ROW, state='未驗證')]},
               {'overall': '通過', 'rows': []}, {'overall': '通過'}, ['通過'],
               {'overall': '未驗證', 'rows': [ROW]},
               {'overall': '通過', 'rows': ['x']}]
        for report in bad:
            for manifest in (self.manifest, debug):
                with self.subTest(report=report, kind=manifest['kind']):
                    self.refused('unverified-source', manifest=manifest, report=report)
        self.assertEqual(self.attempt(manifest=debug).name, '2026-11-10-debug.pkg')

    def test_forged_or_mismatched_results_are_refused(self):
        if not self.supported:
            return self.unsupported()
        signed = pub.attestation(self.manifest, REPORT)
        edited = copy.deepcopy(REPORT)
        edited['rows'][0]['evidence'] = 'other'
        self.refused('forged-or-mismatched-result', report=edited, document=signed)
        other = build_manifest(self.root / 'src', ['SKILL.md'], '2026-11-11', 'formal')
        self.refused('forged-or-mismatched-result', manifest=other, document=signed)
        self.refused('not-signed-by-ci', document=signed, signature=self.sign(b'other'))
        self.refused('invalid-attestation-signature', signature=b'')
        for document in (b'not json', b'{"manifest":"x"}', b'[]', b''):
            with self.subTest(document=document):
                self.refused('invalid-attestation', document=document,
                             signature=self.sign(document) if document else b'sig')

    def test_non_ci_signers_are_refused(self):
        if not self.supported:
            return self.unsupported()
        developer, _ = self.keypair('developer')
        document = pub.attestation(self.manifest, REPORT)
        self.refused('not-signed-by-ci', signature=self.sign(document, key=developer))
        self.refused('not-signed-by-ci', signature=self.sign(document, namespace='other'))
        self.refused('invalid-ci-key', key=b'ssh-rsa AAAA')

    def test_bad_manifest_is_refused_before_anything_else(self):
        if not self.supported:
            return self.unsupported()
        for manifest in (dict(self.manifest, kind='nightly'), dict(self.manifest, version='../x'),
                         dict(self.manifest, version='')):
            with self.subTest(manifest=manifest):
                self.refused('invalid-manifest', manifest=manifest,
                             document=pub.attestation(self.manifest, REPORT))

    def unsupported(self):
        with patch.object(pub, 'VERIFIER', self.root / 'unavailable'):
            fake = b'ssh-ed25519 ' + b'A' * 68
            with self.assertRaises(Denied) as caught:
                pub.publish(fake, self.manifest, REPORT, pub.attestation(self.manifest, REPORT),
                            b'sig', b'package', self.out)
        self.assertEqual(str(caught.exception), 'attestation-verifier-unavailable')
        self.assertEqual(list(self.out.iterdir()), [])
