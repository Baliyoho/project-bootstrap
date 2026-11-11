#!/usr/bin/env python3
"""Build, verify, sign and pack one release (P2 slice 3b, run by CI; decision Q21).

    python3 -X utf8 tools/release_package.py --channel beta \\
        --source https://github.com/OWNER/REPO.git --signing-key KEY --out DIR \\
        [--github-output FILE]

Steps, each of which stops the release on failure:

1. the checkout must be clean, so the report belongs to exactly HEAD;
2. build the debug package from src/kit (tools/build_package.py);
3. run tools/verify_bootstrap.py; every check must pass this round;
4. read the channel tags from --source and take the next epoch;
5. sign with --signing-key; next_keys come from src/kit/release-keys.txt;
6. write the package tar.gz, the signed record and the signature to --out,
   and print the channel tag to create (also to --github-output for the
   workflow). This script creates no tag and uploads nothing.
"""
import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import time
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tools'))

import build_package  # noqa: E402
from project_bootstrap import channel, distribute  # noqa: E402
from project_bootstrap.approvals import VERIFIER  # noqa: E402
from project_bootstrap.contracts import Denied  # noqa: E402

KEYS = ROOT / 'src' / 'kit' / 'release-keys.txt'


def git(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True,
                          check=True, timeout=60).stdout.strip()


def run_verifier():
    result = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'tools' / 'verify_bootstrap.py')],
                            capture_output=True, text=True, cwd=str(ROOT), timeout=1800)
    return result.stdout + result.stderr, result.returncode


def signer(key_path):
    def sign(document):
        return subprocess.run([str(VERIFIER), '-Y', 'sign', '-f', str(key_path), '-n', channel.NAMESPACE],
                              input=document, capture_output=True, check=True, timeout=10).stdout
    return sign


def release(args, verify=run_verifier, list_tags=channel.list_channel, now=time.time):
    if git('status', '--porcelain', '--untracked-files=normal'):
        raise Denied('checkout-not-clean')
    commit = git('rev-parse', 'HEAD')
    keys = distribute.load_keys(KEYS.read_text(encoding='utf-8'))
    folder, _ = build_package.build_once()
    try:
        text, code = verify()
        report = distribute.report_from_verifier(text, code, commit, uuid.uuid4().hex, now())
        if report['overall'] != '通過':
            failing = [row['claim'] for row in report['rows'] if row['state'] != '本輪實查']
            raise Denied('unverified-source:' + ','.join(failing))
        epoch = distribute.next_epoch(list_tags(args.source, args.channel))
        formal, document, signature, tag = channel.release(
            folder, report, args.channel, epoch, keys, signer(args.signing_key))
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    try:
        fields = channel.parse_record(document)
        names = distribute.asset_names(args.channel, epoch, fields['manifest'])
        out = pathlib.Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        distribute.pack(formal, out / names['package'])
        (out / names['record']).write_bytes(document)
        (out / names['signature']).write_bytes(signature)
    finally:
        shutil.rmtree(str(pathlib.Path(formal).parent), ignore_errors=True)
    return {'tag': tag, 'epoch': epoch, 'commit': commit, 'digest': fields['manifest'],
            'assets': [str(out / names[k]) for k in ('package', 'record', 'signature')]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--channel', required=True)
    parser.add_argument('--source', required=True, help='repository whose channel tags to read')
    parser.add_argument('--signing-key', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--github-output', help='append tag=… and assets=… for the workflow')
    args = parser.parse_args(argv)
    try:
        result = release(args)
    except (Denied, OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print('release_package: 拒絕：' + str(exc))
        return 1
    print('release_package: %s（commit %s，epoch %d）' % (result['tag'], result['commit'], result['epoch']))
    for asset in result['assets']:
        print('  ' + asset)
    if args.github_output:
        with open(args.github_output, 'a', encoding='utf-8') as handle:
            handle.write('tag=%s\nassets=%s\n' % (result['tag'], ' '.join(result['assets'])))
    return 0


if __name__ == '__main__':
    os.umask(0o022)
    sys.exit(main())
