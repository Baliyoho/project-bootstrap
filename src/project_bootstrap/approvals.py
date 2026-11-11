"""Detached approvals for synthetic effects. No effect contacts a real service."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import tempfile

from project_bootstrap.broker import Broker, EFFECT_KINDS
from project_bootstrap.contracts import Denied


VERIFIER = Path('/usr/bin/ssh-keygen')
NAMESPACE = 'project-bootstrap-v2-effect'
SIGNER = b'fixture-authorizer'
FIELDS = {'audience', 'id', 'actor', 'kind', 'resource', 'uses', 'funding', 'issued', 'expires', 'epoch'}
FUNDING = {'extra-model': 'subscription', 'paid-api': 'fixture-credit', 'cloud-resource': 'fixture-credit'}


class SignedEffectApprovals:
    """Parent holds the public policy only; test signer holds a disposable key."""
    def __init__(self, authority, public_key):
        if not isinstance(public_key, bytes) or not re.fullmatch(rb'ssh-ed25519 [A-Za-z0-9+/]{68}', public_key):
            raise Denied('invalid-approval-public-key')
        algorithm = b'\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20'
        if not base64.b64decode(public_key.split()[1]).startswith(algorithm):
            raise Denied('invalid-approval-public-key')
        self.authority, self.lab = authority, authority.lab
        self.public_key = public_key
        self.signer_digest = hashlib.sha256(public_key).hexdigest()
        self.verifier_digest = self.verifier_fingerprint()
        with self.authority.broker.lock, self.lab.transaction():
            policy = self.lab.db.execute('SELECT * FROM signed_effect_policy').fetchone()
            if policy is None:
                if self.lab.db.execute('SELECT 1 FROM grants LIMIT 1').fetchone():
                    raise Denied('legacy-effect-grants-present')
                self.audience = secrets.token_hex(32)
                self.lab.db.execute('INSERT INTO signed_effect_policy VALUES (1, ?, ?, ?)',
                                    (self.audience, self.signer_digest, self.verifier_digest))
            else:
                self.audience = policy['audience']
                self.check_policy(policy)

    @staticmethod
    def verifier_fingerprint():
        try:
            return hashlib.sha256(VERIFIER.read_bytes()).hexdigest()
        except OSError:
            raise Denied('approval-verifier-unavailable') from None

    def check_policy(self, policy):
        if (policy is None or policy['audience'] != self.audience
                or policy['signer_digest'] != self.signer_digest or policy['verifier_digest'] != self.verifier_digest):
            raise Denied('approval-policy-changed')

    def verify(self, document, signature):
        if self.verifier_fingerprint() != self.verifier_digest:
            raise Denied('approval-verifier-changed')
        if not isinstance(signature, bytes) or not 1 <= len(signature) <= 2048:
            raise Denied('invalid-approval-signature')
        try:
            with tempfile.TemporaryDirectory(prefix='bootstrap-v2-approval-') as directory:
                signers = Path(directory) / 'signers'
                proof = Path(directory) / 'signature'
                signers.write_bytes(SIGNER + b' ' + self.public_key + b'\n')
                proof.write_bytes(signature)
                result = subprocess.run([str(VERIFIER), '-Y', 'verify', '-f', str(signers),
                    '-I', SIGNER.decode('ascii'), '-n', NAMESPACE, '-s', str(proof)],
                    input=document, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    env={'PATH': os.defpath}, timeout=3)
        except (OSError, subprocess.TimeoutExpired):
            raise Denied('approval-verifier-unavailable') from None
        if result.returncode:
            raise Denied('invalid-approval-signature')

    @staticmethod
    def parse(document):
        if not isinstance(document, bytes) or not 1 <= len(document) <= 4096:
            raise Denied('invalid-approval-document')
        try:
            fields = json.loads(document.decode('utf-8'), object_pairs_hook=Broker.unique_keys)
        except (ValueError, RecursionError):
            raise Denied('invalid-approval-document') from None
        if not isinstance(fields, dict) or set(fields) != FIELDS:
            raise Denied('invalid-approval-document')
        for key, length in (('audience', 64), ('actor', 64), ('id', 32)):
            if not isinstance(fields[key], str) or not re.fullmatch('[0-9a-f]{%d}' % length, fields[key]):
                raise Denied('invalid-approval-document')
        kind = fields['kind']
        if (not isinstance(kind, str) or kind not in EFFECT_KINDS or fields['funding'] != FUNDING.get(kind)
                or not isinstance(fields['resource'], str) or not fields['resource']
                or type(fields['uses']) is not int or not 1 <= fields['uses'] <= 32
                or any(type(fields[key]) is not int or not 0 <= fields[key] <= 2**53
                       for key in ('issued', 'expires', 'epoch'))):
            raise Denied('invalid-approval-scope')
        return fields

    def approve(self, ticket, document, signature):
        fields = self.parse(document)
        self.verify(document, signature)
        with self.authority.broker.lock, self.lab.transaction():
            self.check_policy(self.lab.db.execute('SELECT * FROM signed_effect_policy').fetchone())
            permit, now = self.authority.timed_permit(self.authority.ticket_hash(ticket))
            if fields['audience'] != self.audience or fields['actor'] != permit['actor']:
                raise Denied('approval-principal-mismatch')
            if not fields['issued'] <= now < fields['expires']:
                raise Denied('approval-not-current')
            self.lab.require_epoch(fields['epoch'])
            source = 'signed-effect:' + fields['id']
            previous = self.lab.db.execute('SELECT a.document, a.grant_id, g.id FROM signed_effect_approvals a '
                                           'LEFT JOIN grants g ON g.id=a.grant_id WHERE a.id=?',
                                           (fields['id'],)).fetchone()
            if previous is not None:
                if previous['document'] != document:
                    raise Denied('approval-id-reused')
                if previous['id'] is None:
                    raise Denied('approval-grant-missing')
                return previous['grant_id']
            if self.lab.db.execute('SELECT 1 FROM grants WHERE source=?', (source,)).fetchone():
                raise Denied('approval-record-missing')
            grant = self.authority._grant(permit, fields['kind'], fields['resource'], fields['uses'],
                                          source, fields['expires'])
            self.lab.db.execute('INSERT INTO signed_effect_approvals VALUES (?, ?, ?, ?, ?)',
                                (fields['id'], document, signature, grant, fields['epoch']))
            return grant
