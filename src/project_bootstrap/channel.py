"""P2 slice 3a: formal releases, a key chain, and a channel read from Git tags (Q20 (a)(a)(a)).

The channel is a set of tags in the source repository::

    refs/tags/channel/<name>/<epoch>-<manifest digest>

``git ls-remote`` lists them without a local clone or any write, so every
managed write can ask the source repository directly. Freshness comes from
that live connection, not from signing a nonce: a CI job cannot answer
requests, and Q20 chose not to run a signing service. Who may create those
tags is enforced on the server (GitHub rulesets, slice 3b), so the client
also refuses any tag whose epoch and digest are not the pair CI signed.

``release`` is the CI side. It takes a debug package from ``package.py`` and
the verification report, refuses unless every report row was checked this
round (``publish._verified_this_round``), marks the package formal and
returns the bytes CI signs: channel, epoch, formal manifest digest, report
digest, and ``next_keys``, the keys allowed to sign the next release.

``install`` is the client side. It accepts a release only if the signature
verifies with a key the previously installed release listed in its
``next_keys`` (or, for the very first install, a root key the person gave).
Rotating the key therefore needs one release signed by the old key that names
the new one. The package and its signed record go into the cache folder.

``GitWriteCheck.confirm`` replaces the nonce statement of ``pointer.WriteCheck``:
it lists the channel tags and lets the write on only when the newest tag is
exactly the installed record's (epoch, digest). A newer epoch is handled like
any moved channel (refused unless a D4 exception covers it); an older epoch,
the same digest under another epoch, two tags for one epoch or an unreadable
tag name all refuse. The installed epoch lives in the signed record in the
cache, so a fresh process cannot be fed an older channel.

Limits: the CI key is a test key here; rulesets, the workflow and the first
real release are slice 3b. Anyone who can create channel tags can still stop
every writer (fail closed), and the cache is writable by the same user (P3).
"""
import base64
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

from project_bootstrap import package, pointer
from project_bootstrap.approvals import VERIFIER
from project_bootstrap.broker import Broker
from project_bootstrap.contracts import Denied
from project_bootstrap.publish import _verified_this_round, report_digest

NAMESPACE = 'project-bootstrap-v2-release'
SIGNER = 'release-ci'
TAG_PREFIX = 'refs/tags/channel/'
TAG_RE = re.compile(r'refs/tags/channel/([a-z][a-z0-9-]{0,31})/([1-9][0-9]{0,8})-([0-9a-f]{64})')
KEY_RE = re.compile(r'ssh-ed25519 [A-Za-z0-9+/]{68}')
RECORD_FIELDS = {'channel', 'epoch', 'manifest', 'report', 'next_keys'}
RECORD_SUFFIX = '.release.json'
LS_REMOTE_TIMEOUT = 20


def tag_name(channel, epoch, digest):
    name = '%s%s/%d-%s' % (TAG_PREFIX, channel, epoch, digest)
    if not TAG_RE.fullmatch(name):
        raise Denied('invalid-tag')
    return name


def _keys(keys):
    if (not isinstance(keys, list) or not keys
            or not all(isinstance(k, str) and KEY_RE.fullmatch(k) for k in keys)):
        raise Denied('invalid-keys')
    return sorted(set(keys))


def record_bytes(channel, epoch, manifest_digest, report_hash, next_keys):
    """The exact bytes CI signs for one release."""
    return json.dumps({'channel': channel, 'epoch': epoch, 'manifest': manifest_digest,
                       'report': report_hash, 'next_keys': _keys(next_keys)},
                      sort_keys=True, separators=(',', ':')).encode('ascii')


def release(folder, report, channel, epoch, next_keys, sign):
    """CI side: a checked debug package plus a fully fresh report becomes a signed formal release.

    Returns (formal folder, record bytes, signature bytes, tag name). ``sign``
    receives the record bytes and returns an ssh-keygen signature.
    """
    if not isinstance(channel, str) or not pointer.CHANNEL_RE.fullmatch(channel):
        raise Denied('invalid-channel')
    if type(epoch) is not int or not 1 <= epoch <= 999_999_999:
        raise Denied('invalid-epoch')
    problems = package.check(folder)
    if problems:
        raise Denied('bad-package:' + ','.join(problems))
    manifest = json.loads((Path(folder) / package.MANIFEST).read_text(encoding='utf-8'))
    if manifest.get('kind') != 'debug':
        raise Denied('not-a-debug-build')
    if not _verified_this_round(report):
        raise Denied('unverified-source')
    formal = tempfile.mkdtemp(prefix='bootstrap-release-')
    try:
        os.chmod(formal, 0o755)
        target = Path(formal) / 'package'
        shutil.copytree(folder, target, symlinks=True)
        manifest['kind'] = 'formal'
        (target / package.MANIFEST).write_bytes(package._dump(manifest))
        digest = package.digest(manifest)
        document = record_bytes(channel, epoch, digest, report_digest(report), next_keys)
        signature = sign(document)
    except BaseException:
        shutil.rmtree(formal, ignore_errors=True)
        raise
    return str(target), document, signature, tag_name(channel, epoch, digest)


def _verify(document, signature, keys):
    """Denied unless one of ``keys`` signed ``document`` in the release namespace."""
    keys = _keys(keys)
    if not isinstance(signature, bytes) or not 1 <= len(signature) <= 2048:
        raise Denied('invalid-release-signature')
    try:
        with tempfile.TemporaryDirectory(prefix='bootstrap-release-verify-') as directory:
            signers = Path(directory) / 'signers'
            proof = Path(directory) / 'signature'
            signers.write_text(''.join('%s %s\n' % (SIGNER, key) for key in keys), encoding='ascii')
            proof.write_bytes(signature)
            result = subprocess.run(
                [str(VERIFIER), '-Y', 'verify', '-f', str(signers), '-I', SIGNER,
                 '-n', NAMESPACE, '-s', str(proof)],
                input=document, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                env={'PATH': os.defpath}, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        raise Denied('release-verifier-unavailable') from None
    if result.returncode:
        raise Denied('not-signed-by-trusted-key')


def parse_record(document):
    if not isinstance(document, bytes) or not 1 <= len(document) <= 4096:
        raise Denied('invalid-release-record')
    try:
        fields = json.loads(document.decode('ascii'), object_pairs_hook=Broker.unique_keys)
    except (ValueError, RecursionError, UnicodeDecodeError):
        raise Denied('invalid-release-record') from None
    if (not isinstance(fields, dict) or set(fields) != RECORD_FIELDS
            or type(fields['epoch']) is not int or fields['epoch'] < 1
            or not isinstance(fields['channel'], str) or not pointer.CHANNEL_RE.fullmatch(fields['channel'])
            or not isinstance(fields['manifest'], str) or not pointer.DIGEST_RE.fullmatch(fields['manifest'])):
        raise Denied('invalid-release-record')
    if document != record_bytes(fields['channel'], fields['epoch'], fields['manifest'],
                                fields['report'], fields['next_keys']):
        raise Denied('invalid-release-record')
    return fields


def install(cache, folder, document, signature, trusted_keys):
    """Client side: verify a release against the keys trusted now and put it in the cache.

    ``trusted_keys`` is the ``next_keys`` of the installed release (see
    ``trusted_after``), or the root key for a first install.
    """
    _verify(document, signature, trusted_keys)
    fields = parse_record(document)
    problems = package.check(folder)
    if problems:
        raise Denied('bad-package:' + ','.join(problems))
    manifest = json.loads((Path(folder) / package.MANIFEST).read_text(encoding='utf-8'))
    if manifest.get('kind') != 'formal':
        raise Denied('debug-release')
    digest = package.digest(manifest)
    if digest != fields['manifest']:
        raise Denied('release-mismatch')
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / digest
    if not target.exists():
        staging = Path(tempfile.mkdtemp(prefix='bootstrap-install-', dir=str(cache)))
        try:
            shutil.copytree(folder, staging / 'package', symlinks=True)
            package.install(staging / 'package', target)
        finally:
            shutil.rmtree(staging, ignore_errors=True)
    elif package.check(target):
        raise Denied('cache-damaged')
    record = {'document': document.decode('ascii'),
              'signature': base64.b64encode(signature).decode('ascii')}
    (cache / (digest + RECORD_SUFFIX)).write_text(json.dumps(record, sort_keys=True), encoding='utf-8')
    return fields


def installed_record(cache, digest):
    """The signed record stored with a cached package; Denied if missing or malformed."""
    try:
        data = json.loads((Path(cache) / (digest + RECORD_SUFFIX)).read_text(encoding='utf-8'))
        document = data['document'].encode('ascii')
        signature = base64.b64decode(data['signature'], validate=True)
    except FileNotFoundError:
        raise Denied('release-record-missing') from None
    except (OSError, ValueError, KeyError, TypeError, AttributeError, UnicodeEncodeError):
        raise Denied('invalid-release-record') from None
    fields = parse_record(document)
    if fields['manifest'] != digest:
        raise Denied('invalid-release-record')
    return fields, document, signature


def trusted_after(cache, digest):
    """Keys allowed to sign the release after the installed one."""
    return installed_record(cache, digest)[0]['next_keys']


def list_channel(source, channel, run=subprocess.run):
    """[(epoch, digest)] of the channel's tags, read live; Denied when the source cannot be reached."""
    try:
        result = run(['git', 'ls-remote', '--tags', '--refs', source],
                     capture_output=True, timeout=LS_REMOTE_TIMEOUT,
                     env=dict(os.environ, GIT_TERMINAL_PROMPT='0'))
    except (OSError, subprocess.TimeoutExpired):
        raise Denied('channel-unreachable') from None
    if result.returncode:
        raise Denied('channel-unreachable')
    try:
        lines = result.stdout.decode('utf-8').splitlines()
    except UnicodeDecodeError:
        raise Denied('invalid-channel-tag') from None
    prefix = TAG_PREFIX + channel + '/'
    tags = []
    for line in lines:
        _, _, ref = line.partition('\t')
        if not ref.startswith(prefix):
            continue
        match = TAG_RE.fullmatch(ref)
        if not match or match.group(1) != channel:
            raise Denied('invalid-channel-tag')
        tags.append((int(match.group(2)), match.group(3)))
    return tags


def newest(tags):
    if not tags:
        raise Denied('channel-empty')
    top = max(epoch for epoch, _ in tags)
    digests = {digest for epoch, digest in tags if epoch == top}
    if len(digests) != 1:
        raise Denied('channel-conflict')
    return top, digests.pop()


class GitWriteCheck(pointer.WriteCheck):
    """Per-write check against the channel tags of the pointer's source repository."""

    def __init__(self, project, cache, run=subprocess.run, clock=time.time):
        self.project, self.cache = Path(project), Path(cache)
        self.run, self.clock = run, clock

    def confirm(self, operation, target):
        pointer.check_request(operation, target)
        current = self._pointer()
        if 'source' not in current:
            raise Denied('no-source')
        installed = current['installed']
        manifest = self._installed(installed)
        if manifest.get('kind') != 'formal':
            raise Denied('debug-release')
        record, _, _ = installed_record(self.cache, installed)
        if record['channel'] != current['channel']:
            raise Denied('wrong-channel')
        # Local checks first: a write refused here never spends a round trip.
        pointer.check_components(self.project, manifest)
        epoch, latest = newest(list_channel(current['source'], current['channel'], self.run))
        now = self.clock()
        pinned = False
        if epoch < record['epoch']:
            raise Denied('channel-rollback')
        if epoch == record['epoch'] and latest != installed:
            raise Denied('channel-conflict')
        if epoch > record['epoch']:
            if latest == installed:
                raise Denied('channel-epoch-mismatch')
            pinned = pointer.exception_allows(current['exception'], now, target)
        return {'operation': operation, 'target': target, 'epoch': epoch,
                'version': manifest['version'], 'installed': installed, 'latest': latest,
                'installed_epoch': record['epoch'], 'pinned': pinned}
