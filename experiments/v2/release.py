"""M1 whole-package manifest and per-write freshness gate (F18／F32／F33 prototype).

A manifest lists every shipped component with its SHA-256, so a change to a
hook or schema alone changes the package digest even when ``version`` does
not. Before each managed write the client asks a trusted channel endpoint
for a statement signed over a fresh client nonce. A cached statement, an
unreachable endpoint or a replayed answer never authorises a write.

Synthetic fixtures only: the signer is a disposable test key, there is no CI
identity, network transport or atomic install step here.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import tempfile
import time

from experiments.v2.approvals import VERIFIER
from experiments.v2.broker import Broker
from experiments.v2.contracts import Denied

NAMESPACE = 'project-bootstrap-v2-channel'
SIGNER = b'fixture-release-ci'
STATEMENT_FIELDS = {'channel', 'epoch', 'manifest', 'nonce', 'issued', 'expires'}
KINDS = {'formal', 'debug'}


def _file_digest(root, relative):
    # A leading '/' yields an empty first part, so absolute paths fail here too.
    if (not isinstance(relative, str) or not relative
            or '\\' in relative or any(part in ('', '.', '..') for part in relative.split('/'))):
        raise Denied('invalid-component')
    path = Path(root) / relative
    try:
        if path.is_symlink() or not path.is_file():
            raise Denied('invalid-component')
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        raise Denied('invalid-component') from None


def build_manifest(root, paths, version, kind, affects=()):
    """Release pipeline stand-in: digest every component of one source tree."""
    if kind not in KINDS or not isinstance(version, str) or not version:
        raise Denied('invalid-manifest')
    paths = sorted(set(paths))
    if not paths:
        raise Denied('invalid-manifest')
    return {'schema': 1, 'version': version, 'kind': kind,
            'components': {path: _file_digest(root, path) for path in paths},
            'affects': sorted(set(affects))}


def manifest_digest(manifest):
    canonical = json.dumps(manifest, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(canonical.encode('ascii')).hexdigest()


def statement(channel, epoch, manifest, nonce, issued, expires):
    """Bytes the trusted endpoint signs; the client nonce makes it single-use."""
    return json.dumps({'channel': channel, 'epoch': epoch, 'manifest': manifest,
                       'nonce': nonce, 'issued': issued, 'expires': expires},
                      sort_keys=True, separators=(',', ':')).encode('ascii')


class WriteGate:
    """Client side. ``fetch(nonce)`` returns (statement bytes, signature bytes)."""

    def __init__(self, public_key, channel, root, manifest, fetch, clock=time.time):
        if (not isinstance(public_key, bytes)
                or not re.fullmatch(rb'ssh-ed25519 [A-Za-z0-9+/]{68}', public_key)):
            raise Denied('invalid-channel-key')
        self.public_key, self.channel = public_key, channel
        self.root, self.manifest = Path(root), manifest
        self.digest = manifest_digest(manifest)
        self.fetch, self.clock = fetch, clock
        self.highest_epoch = -1

    def _verify(self, document, signature):
        if not isinstance(signature, bytes) or not 1 <= len(signature) <= 2048:
            raise Denied('invalid-channel-signature')
        try:
            with tempfile.TemporaryDirectory(prefix='bootstrap-v2-channel-') as directory:
                signers = Path(directory) / 'signers'
                proof = Path(directory) / 'signature'
                signers.write_bytes(SIGNER + b' ' + self.public_key + b'\n')
                proof.write_bytes(signature)
                result = subprocess.run(
                    [str(VERIFIER), '-Y', 'verify', '-f', str(signers), '-I',
                     SIGNER.decode('ascii'), '-n', NAMESPACE, '-s', str(proof)],
                    input=document, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    env={'PATH': os.defpath}, timeout=3)
        except (OSError, subprocess.TimeoutExpired):
            raise Denied('channel-verifier-unavailable') from None
        if result.returncode:
            raise Denied('invalid-channel-signature')

    def confirm(self, operation):
        """Fresh confirmation bound to one operation, or Denied. Never uses a cache."""
        if not isinstance(operation, str) or not re.fullmatch(r'[0-9a-f]{32}', operation):
            raise Denied('invalid-operation')
        nonce = secrets.token_hex(16)
        try:
            document, signature = self.fetch(nonce)
        except Exception:
            raise Denied('channel-unreachable') from None
        if not isinstance(document, bytes) or not 1 <= len(document) <= 1024:
            raise Denied('invalid-channel-statement')
        self._verify(document, signature)
        try:
            fields = json.loads(document.decode('ascii'), object_pairs_hook=Broker.unique_keys)
        except (ValueError, RecursionError, UnicodeDecodeError):
            raise Denied('invalid-channel-statement') from None
        if (not isinstance(fields, dict) or set(fields) != STATEMENT_FIELDS
                or any(type(fields[key]) is not int for key in ('epoch', 'issued', 'expires'))):
            raise Denied('invalid-channel-statement')
        if fields['channel'] != self.channel:
            raise Denied('wrong-channel')
        if fields['nonce'] != nonce:
            raise Denied('stale-confirmation')
        now = self.clock()
        if not fields['issued'] <= now < fields['expires']:
            raise Denied('stale-confirmation')
        if fields['epoch'] < self.highest_epoch:
            raise Denied('channel-rollback')
        if fields['manifest'] != self.digest:
            raise Denied('release-mismatch')
        if self.manifest.get('kind') != 'formal':
            raise Denied('debug-release')
        for path, expected in self.manifest['components'].items():
            if _file_digest(self.root, path) != expected:
                raise Denied('component-drift')
        self.highest_epoch = fields['epoch']
        return {'operation': operation, 'epoch': fields['epoch'], 'manifest': self.digest}
