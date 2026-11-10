"""Candidate probe: can this Mac gate a signature on the user being present?

Background: crash release (decision Q1 (a)) asks a person at the local
terminal, which a same-UID program can fake with its own pseudo-terminal. The
user wants a signing key later (Q1 (b)). This probe only measures whether the
operating system offers a building block for that: a Secure Enclave key whose
every use requires user presence (Touch ID or the login password, asked by a
system dialog, not by this process).

What it does, without ever showing a dialog (interaction is disallowed):
- control: an ungated Secure Enclave key signs and verifies;
- presence: a key gated on `.userPresence` can be created, and signing with
  it is refused because interaction is required;
- biometry: the same with `.biometryCurrentSet` (no password fallback).

What it does NOT show: that a real person approving works end to end (nobody
is asked), what the dialog tells the person about the content being signed
(the requesting program supplies that text), key storage, rotation or
revocation, behaviour over SSH or with the lid closed, or any other OS. A
"candidate" result is never a pass and changes no gate in this repository.

Usage, from the repo root:  python3 -X utf8 -m experiments.v2.presence_probe
Exit 0 candidate observed, 1 counterexample or failure, 2 not applicable here.
"""
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

SWIFT = r'''
import CryptoKit
import Foundation
import LocalAuthentication
import Security

guard SecureEnclave.isAvailable else { print("ENCLAVE unavailable"); exit(0) }
print("ENCLAVE available")
let message = Data("synthetic approval".utf8)
func probe(_ name: String, _ flags: SecAccessControlCreateFlags) {
    var failure: Unmanaged<CFError>?
    guard let access = SecAccessControlCreateWithFlags(
        nil, kSecAttrAccessibleWhenUnlockedThisDeviceOnly, flags, &failure) else {
        print("\(name) access-control-error")
        return
    }
    let context = LAContext()
    context.interactionNotAllowed = true
    let key: SecureEnclave.P256.Signing.PrivateKey
    do {
        key = try SecureEnclave.P256.Signing.PrivateKey(
            accessControl: access, authenticationContext: context)
    } catch {
        print("\(name) key-error \((error as NSError).domain) \((error as NSError).code)")
        return
    }
    do {
        let signature = try key.signature(for: message)
        let valid = key.publicKey.isValidSignature(signature, for: message)
        print("\(name) signed \(valid ? "valid" : "invalid")")
    } catch {
        print("\(name) refused \((error as NSError).domain) \((error as NSError).code)")
    }
}
probe("CONTROL", [.privateKeyUsage])
probe("PRESENCE", [.privateKeyUsage, .userPresence])
probe("BIOMETRY", [.privateKeyUsage, .biometryCurrentSet])
'''

# LAError.notInteractive: the system wanted to ask the user and was not allowed to.
INTERACTION_REQUIRED = 'refused com.apple.LocalAuthentication -1004'


def assess(output):
    """Turn the helper's lines into a result that can never read as a pass."""
    lines = dict(line.split(' ', 1) for line in output.splitlines() if ' ' in line)
    observed = {name: lines.get(name) for name in ('ENCLAVE', 'CONTROL', 'PRESENCE', 'BIOMETRY')}
    if set(lines) - set(observed) or len(lines) != len([l for l in output.splitlines() if l]):
        return {'result': '未驗證', 'reason': 'unexpected helper output', 'observed': observed}
    if observed['ENCLAVE'] == 'unavailable' and len(lines) == 1:
        return {'result': '無法使用', 'reason': 'no Secure Enclave', 'observed': observed}
    if observed['ENCLAVE'] != 'available':
        return {'result': '未驗證', 'reason': 'helper did not report the enclave',
                'observed': observed}
    gated = [observed['PRESENCE'], observed['BIOMETRY']]
    if any(value is not None and value.startswith('signed') for value in gated):
        return {'result': '反例', 'reason': 'a gated key signed with interaction disallowed',
                'observed': observed}
    if observed['CONTROL'] != 'signed valid':
        return {'result': '未驗證', 'reason': 'the ungated control key did not sign',
                'observed': observed}
    if observed['PRESENCE'] != INTERACTION_REQUIRED:
        return {'result': '未驗證', 'reason': 'presence-gated signing was not refused for '
                'lack of interaction', 'observed': observed}
    return {'result': '候選可用但未驗收',
            'reason': 'gated signing needs user interaction; no person was asked',
            'biometry_only': observed['BIOMETRY'] == INTERACTION_REQUIRED,
            'observed': observed}


def probe_presence():
    if platform.system() != 'Darwin':
        return {'result': '未驗證', 'reason': 'macOS only', 'observed': {}}
    if shutil.which('xcrun') is None:
        return {'result': '未驗證', 'reason': 'missing xcrun', 'observed': {}}
    with tempfile.TemporaryDirectory(prefix='project-bootstrap-presence-') as directory:
        source = Path(directory) / 'presence.swift'
        helper = Path(directory) / 'presence'
        source.write_text(SWIFT, encoding='utf-8')
        built = subprocess.run(['xcrun', 'swiftc', '-o', str(helper), str(source)],
                               capture_output=True, text=True, timeout=300)
        if built.returncode:
            return {'result': '未驗證', 'reason': 'helper did not compile', 'observed': {}}
        ran = subprocess.run([str(helper)], stdin=subprocess.DEVNULL, capture_output=True,
                             text=True, timeout=60)
        if ran.returncode:
            return {'result': '未驗證', 'reason': f'helper exit {ran.returncode}', 'observed': {}}
        report = assess(ran.stdout)
    report['host'] = f'{platform.system()} {platform.mac_ver()[0]} {platform.machine()}'
    return report


def main():
    report = probe_presence()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if report['result'] == '候選可用但未驗收':
        print('PRESENCE_PROBE_CANDIDATE: no person was asked; this is not an approval mechanism yet')
        return 0
    return 1 if report['result'] == '反例' else 2


if __name__ == '__main__':
    sys.exit(main())
