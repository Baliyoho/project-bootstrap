import json
from pathlib import Path
import platform
import sqlite3
import subprocess
import tempfile
from unittest import TestCase
from unittest.mock import patch

from experiments.v2 import approvals, broker_fixture, managed_fixture
from experiments.v2.broker import Broker
from experiments.v2.contracts import Denied, Lab
from experiments.v2.launcher import LaunchAuthority, RequestJournal


class SignedApprovalTests(TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='bootstrap-v2-approval-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.now = 1000
        self.lab = Lab(self.root / 'private.sqlite', authority_clock=lambda: self.now)
        self.addCleanup(self.lab.close)
        self.authority = LaunchAuthority(Broker(self.lab))
        self.ticket = self.authority.issue(('budget', 'data'), 'synthetic-parent', 1200)
        self.channel = self.authority.connect(self.ticket)
        self.supported = platform.system() == 'Darwin' and approvals.VERIFIER.is_file()
        if self.supported:
            self.signing_key, self.public = self.keypair('fixture-signer')
            self.policy = approvals.SignedEffectApprovals(self.authority, self.public)
            self.fields = {'audience': self.policy.audience, 'id': '1' * 32,
                           'actor': self.lab.actor(self.channel.capability), 'kind': 'extra-model',
                           'resource': 'budget', 'uses': 1, 'funding': 'subscription',
                           'issued': 995, 'expires': 1100, 'epoch': 0}

    def keypair(self, name):
        key = self.root / name
        subprocess.run([str(approvals.VERIFIER), '-q', '-t', 'ed25519', '-N', '', '-f', str(key)],
                       check=True, timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        public = b' '.join(key.with_suffix('.pub').read_bytes().split()[:2])
        return key, public

    def document(self, **changes):
        return json.dumps(dict(self.fields, **changes), sort_keys=True).encode()

    def sign(self, document, key=None, namespace=approvals.NAMESPACE):
        result = subprocess.run([str(approvals.VERIFIER), '-Y', 'sign', '-f', str(key or self.signing_key),
                                 '-n', namespace], input=document, capture_output=True, check=True, timeout=3)
        return result.stdout

    def unsupported(self):
        # Match other P0 probes: this check explicitly exercises unsupported
        # mode when no Darwin verifier is being measured.
        with patch.object(approvals, 'VERIFIER', self.root / 'unavailable'):
            with self.assertRaisesRegex(Denied, 'approval-verifier-unavailable'):
                approvals.SignedEffectApprovals(self.authority,
                    b'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')

    def effect(self, **changes):
        journal = RequestJournal(self.authority, self.channel)
        fields = dict(method='effect', kind='extra-model', resource='budget', epoch=0)
        journal.prepare(dict(fields, **changes))
        return json.loads(journal.send())['code']

    def test_detached_approval_binds_action_and_does_not_replenish_on_replay(self):
        if not self.supported:
            return self.unsupported()
        document = self.document()
        signature = self.sign(document)
        self.assertEqual(self.effect(), 'not-authorized')
        grant = self.policy.approve(self.ticket, document, signature)
        self.assertEqual(self.effect(kind='paid-api'), 'not-authorized')
        self.assertEqual(self.effect(resource='data'), 'not-authorized')
        self.assertEqual(self.effect(), 'ok')
        self.assertEqual(self.policy.approve(self.ticket, document, signature), grant)
        self.assertEqual(self.effect(), 'not-authorized')
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM effects').fetchone()[0], 1)
        self.assertEqual(tuple(self.lab.db.execute('SELECT document, signature, grant_id FROM '
            'signed_effect_approvals').fetchone()), (document, signature, grant))

    def test_tampering_wrong_signer_namespace_or_changed_verifier_is_denied(self):
        if not self.supported:
            return self.unsupported()
        document = self.document()
        foreign_key, _ = self.keypair('foreign-signer')
        for changed, signature in ((self.document(uses=2), self.sign(document)),
                                   (document, self.sign(document, foreign_key)),
                                   (document, self.sign(document, namespace='other-fixture'))):
            with self.assertRaisesRegex(Denied, 'invalid-approval-signature'):
                self.policy.approve(self.ticket, changed, signature)
        signature = self.sign(document)
        with patch.object(self.policy, 'verifier_fingerprint', return_value='changed'):
            with self.assertRaisesRegex(Denied, 'approval-verifier-changed'):
                self.policy.approve(self.ticket, document, signature)
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM grants').fetchone()[0], 0)

    def test_even_valid_signatures_cannot_expand_identity_scope_or_deadline(self):
        if not self.supported:
            return self.unsupported()
        another = self.authority.issue(('budget',), 'synthetic-parent', 1200)
        for ticket, document, reason in (
                (another, self.document(), 'approval-principal-mismatch'),
                (self.ticket, self.document(audience='0' * 64), 'approval-principal-mismatch'),
                (self.ticket, self.document(resource='outside-scope'), 'resource-not-authorized'),
                (self.ticket, self.document(expires=1201), 'invalid-grant-deadline'),
                (self.ticket, self.document(issued=1001), 'approval-not-current'),
                (self.ticket, self.document(expires=1000), 'approval-not-current'),
                (self.ticket, self.document(funding='paid-api'), 'invalid-approval-scope'),
                (self.ticket, self.document(uses=True), 'invalid-approval-scope')):
            with self.subTest(reason=reason), self.assertRaisesRegex(Denied, reason):
                self.policy.approve(ticket, document, self.sign(document))
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM grants').fetchone()[0], 0)

    def test_pending_and_changed_premise_blocks_old_approvals_and_unused_grants(self):
        if not self.supported:
            return self.unsupported()
        document = self.document()
        signature = self.sign(document)
        self.policy.approve(self.ticket, document, signature)
        epoch = self.lab.propose('synthetic changed premise')
        with self.assertRaisesRegex(Denied, 'premise-not-current'):
            self.policy.approve(self.ticket, document, signature)
        self.assertEqual(self.effect(), 'premise-not-current')
        self.lab.acknowledge(self.channel.capability, epoch, 'synthetic changed premise', application=True)
        self.lab.activate()
        self.assertEqual(self.effect(epoch=epoch), 'not-authorized')
        with self.assertRaisesRegex(Denied, 'premise-not-current'):
            self.policy.approve(self.ticket, document, signature)
        fresh = self.document(id='2' * 32, epoch=epoch)
        self.policy.approve(self.ticket, fresh, self.sign(fresh))
        self.assertEqual(self.effect(epoch=epoch), 'ok')

    def test_lost_approval_record_does_not_enable_or_reissue_a_grant(self):
        if not self.supported:
            return self.unsupported()
        document = self.document(uses=2)
        signature = self.sign(document)
        self.policy.approve(self.ticket, document, signature)
        self.assertEqual(self.effect(), 'ok')
        self.lab.db.execute('DELETE FROM signed_effect_approvals')
        self.lab.db.commit()
        self.assertEqual(self.effect(), 'not-authorized')
        with self.assertRaisesRegex(Denied, 'approval-record-missing'):
            self.policy.approve(self.ticket, document, signature)
        self.assertEqual(self.lab.db.execute('SELECT count(*) FROM effects').fetchone()[0], 1)

    def test_policy_persists_and_receipt_failure_rolls_back_grant(self):
        if not self.supported:
            return self.unsupported()
        reopened = LaunchAuthority(Broker(self.lab))
        with self.assertRaisesRegex(Denied, 'signed-effect-approval-required'):
            reopened.grant(self.ticket, 'delete', 'data', 1, 'unverified-label', 1100)
        _, foreign_public = self.keypair('foreign-signer')
        with self.assertRaisesRegex(Denied, 'approval-policy-changed'):
            approvals.SignedEffectApprovals(reopened, foreign_public)
        gate = approvals.SignedEffectApprovals(reopened, self.public)
        document = self.document(kind='delete', resource='data', funding=None)
        signature = self.sign(document)
        self.lab.db.execute("""CREATE TRIGGER reject_approval BEFORE INSERT ON signed_effect_approvals
            BEGIN SELECT RAISE(ABORT, 'synthetic-receipt-failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            gate.approve(self.ticket, document, signature)
        self.assertEqual(self.effect(kind='delete', resource='data'), 'not-authorized')
        self.lab.db.execute('DROP TRIGGER reject_approval')
        gate.approve(self.ticket, document, signature)
        self.assertEqual(self.effect(kind='delete', resource='data'), 'ok')
        changed = self.document(kind='delete', resource='data', funding=None, uses=2)
        with self.assertRaisesRegex(Denied, 'approval-id-reused'):
            gate.approve(self.ticket, changed, self.sign(changed))
        self.assertEqual(self.effect(kind='delete', resource='data'), 'not-authorized')

    def test_document_shape_is_rejected_before_any_signature_check(self):
        parse = approvals.SignedEffectApprovals.parse
        good = self.document() if self.supported else json.dumps(dict(
            audience='a' * 64, id='1' * 32, actor='b' * 64, kind='extra-model', resource='budget',
            uses=1, funding='subscription', issued=995, expires=1100, epoch=0)).encode()
        self.assertEqual(parse(good)['uses'], 1)
        fields = json.loads(good)
        cases = [(b'', 'invalid-approval-document'), (good + b' ' * 4096, 'invalid-approval-document'),
                 (json.dumps(dict(fields, note='x')).encode(), 'invalid-approval-document')]
        for key, bad in (('audience', 'A' * 64), ('actor', 'b' * 63), ('id', 'g' * 32)):
            cases.append((json.dumps(dict(fields, **{key: bad})).encode(), 'invalid-approval-document'))
        for change in ({'resource': ''}, {'resource': 5}, {'uses': 0}, {'uses': 33},
                       {'issued': -1}, {'expires': 2**53 + 1}, {'epoch': 1.0}):
            cases.append((json.dumps(dict(fields, **change)).encode(), 'invalid-approval-scope'))
        for document, code in cases:
            with self.subTest(document=document[:60]), self.assertRaisesRegex(Denied, code):
                parse(document)

    def test_key_signature_policy_and_grant_records_are_checked(self):
        if not self.supported:
            return self.unsupported()
        for key in (b'ssh-rsa ' + self.public.split()[1], self.public + b' x',
                    b'ssh-ed25519 ' + b'A' * 68):
            with self.subTest(key=key), self.assertRaisesRegex(Denied, 'invalid-approval-public-key'):
                approvals.SignedEffectApprovals(self.authority, key)
        document = self.document()
        # Empty or oversized signatures never reach the verifier process.
        with patch.object(approvals.subprocess, 'run', side_effect=AssertionError('ran')):
            for signature in (b'', b'x' * 2049):
                with self.assertRaisesRegex(Denied, 'invalid-approval-signature'):
                    self.policy.approve(self.ticket, document, signature)
        # The verifier binary recorded at first use is part of the persisted policy.
        self.lab.db.execute("UPDATE signed_effect_policy SET verifier_digest='0'")
        self.lab.db.commit()
        with self.assertRaisesRegex(Denied, 'approval-policy-changed'):
            approvals.SignedEffectApprovals(self.authority, self.public)
        with self.assertRaisesRegex(Denied, 'approval-policy-changed'):
            self.policy.approve(self.ticket, document, self.sign(document))
        self.lab.db.execute('UPDATE signed_effect_policy SET verifier_digest=?',
                            (self.policy.verifier_digest,))
        self.lab.db.commit()
        grant = self.policy.approve(self.ticket, document, self.sign(document))
        self.lab.db.execute('DELETE FROM grants WHERE id=?', (grant,))
        self.lab.db.commit()
        with self.assertRaisesRegex(Denied, 'approval-grant-missing'):
            self.policy.approve(self.ticket, document, self.sign(document))

    def test_existing_unsigned_grants_block_installing_the_signed_policy(self):
        if not self.supported:
            return self.unsupported()
        lab = Lab(self.root / 'legacy.sqlite', authority_clock=lambda: self.now)
        self.addCleanup(lab.close)
        authority = LaunchAuthority(Broker(lab))
        ticket = authority.issue(('budget',), 'synthetic-parent', 1200)
        authority.grant(ticket, 'extra-model', 'budget', 1, 'legacy-label', 1100)
        with self.assertRaisesRegex(Denied, 'legacy-effect-grants-present'):
            approvals.SignedEffectApprovals(authority, self.public)

    def test_confined_agent_uses_signed_grant_through_its_existing_broker_pipe(self):
        if not self.supported:
            return self.unsupported()
        if not managed_fixture.supported():
            self.assertEqual(broker_fixture.probe_broker()['result'], '未驗證')
            return

        def grant_effect(authority, ticket):
            gate = approvals.SignedEffectApprovals(authority, self.public)
            with authority.lab.transaction():
                permit, now = authority.timed_permit(authority.ticket_hash(ticket))
            document = self.document(audience=gate.audience, actor=permit['actor'],
                kind='paid-api', funding='fixture-credit', issued=int(now), expires=int(permit['expires']))
            gate.approve(ticket, document, self.sign(document))

        result = broker_fixture.probe_broker(grant_effect)
        self.assertEqual(result['result'], '通過', result)
        self.assertTrue(result['checks']['grant_and_replay_scoped'])
