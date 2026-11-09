"""F35: a source package leaves only after it passed verification (blocking).

``publish`` writes the package to the release directory only when all of this
holds, and otherwise raises Denied with nothing written:

- the verification report (``evidence.resolve`` output) is 通過 and every
  row was checked this round; reuse, unverified, SKIP or FAIL refuse. A
  debug package gets no exemption: an unverified debug build is not shipped;
- a CI attestation signs the manifest digest and the report digest together,
  so a report edited after signing, or a report for a different package,
  refuses as a forged result;
- the attestation verifies against the CI signer identity only. A key that is
  not the configured CI key, or the right key under another identity or
  namespace, refuses as a non-CI release.

Synthetic: the CI key is a disposable test key and there is no real CI
identity or transport; whoever controls that key can still publish.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from experiments.v2.contracts import Denied
from experiments.v2.release import KINDS, manifest_digest

VERIFIER = Path('/usr/bin/ssh-keygen')
NAMESPACE = 'project-bootstrap-v2-publish'
CI_SIGNER = 'fixture-ci'
ATTESTATION_FIELDS = {'manifest', 'report'}


def report_digest(report):
    canonical = json.dumps(report, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(canonical.encode('ascii')).hexdigest()


def attestation(manifest, report):
    """Bytes CI signs: the package and the verification result it shipped with."""
    return json.dumps({'manifest': manifest_digest(manifest), 'report': report_digest(report)},
                      sort_keys=True, separators=(',', ':')).encode('ascii')


def _verified_this_round(report):
    if not isinstance(report, dict):
        return False
    rows = report.get('rows')
    if report.get('overall') != '通過' or not isinstance(rows, list) or not rows:
        return False
    return all(isinstance(r, dict) and r.get('state') == '本輪實查' for r in rows)


def _verify(ci_key, document, signature):
    if not isinstance(signature, bytes) or not 1 <= len(signature) <= 2048:
        raise Denied('invalid-attestation-signature')
    try:
        with tempfile.TemporaryDirectory(prefix='bootstrap-v2-publish-') as directory:
            signers = Path(directory) / 'signers'
            proof = Path(directory) / 'signature'
            signers.write_bytes(CI_SIGNER.encode('ascii') + b' ' + ci_key + b'\n')
            proof.write_bytes(signature)
            result = subprocess.run(
                [str(VERIFIER), '-Y', 'verify', '-f', str(signers), '-I', CI_SIGNER,
                 '-n', NAMESPACE, '-s', str(proof)],
                input=document, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                env={'PATH': os.defpath}, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        raise Denied('attestation-verifier-unavailable') from None
    if result.returncode:
        raise Denied('not-signed-by-ci')


def publish(ci_key, manifest, report, document, signature, package, release_dir):
    """Copy ``package`` bytes into ``release_dir`` only after every check passed."""
    if (not isinstance(ci_key, bytes)
            or not re.fullmatch(rb'ssh-ed25519 [A-Za-z0-9+/]{68}', ci_key)):
        raise Denied('invalid-ci-key')
    if (not isinstance(manifest, dict) or manifest.get('kind') not in KINDS
            or not re.fullmatch(r'[0-9A-Za-z][0-9A-Za-z.-]{0,63}', str(manifest.get('version')))):
        raise Denied('invalid-manifest')
    if not _verified_this_round(report):
        raise Denied('unverified-source')
    if not isinstance(document, bytes) or not 1 <= len(document) <= 1024:
        raise Denied('invalid-attestation')
    _verify(ci_key, document, signature)
    try:
        fields = json.loads(document.decode('ascii'))
    except (ValueError, UnicodeDecodeError):
        raise Denied('invalid-attestation') from None
    if not isinstance(fields, dict) or set(fields) != ATTESTATION_FIELDS:
        raise Denied('invalid-attestation')
    if fields['manifest'] != manifest_digest(manifest) or fields['report'] != report_digest(report):
        raise Denied('forged-or-mismatched-result')
    target = Path(release_dir) / f"{manifest['version']}-{manifest['kind']}.pkg"
    if target.exists():
        raise Denied('already-published')
    target.write_bytes(package)
    return target
