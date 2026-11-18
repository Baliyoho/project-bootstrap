#!/usr/bin/env python3
"""Install one downloaded release into the cache and point a project at it (P2 slice 3b, Q21).

    python3 -X utf8 tools/install_package.py --project DIR --cache DIR \\
        --archive X.tar.gz --record X.record.json --signature X.sig \\
        --channel beta --source https://github.com/OWNER/REPO.git \\
        [--seed] [--check]

Which keys may sign this release: the next_keys of the release the project
has installed now; for a project without a pointer, the root keys in
src/kit/release-keys.txt (decision Q21 (a): the public key is committed and
its fingerprint is in the README). --seed copies the package into an empty
project folder. --check then runs one per-write check against --source.

This script downloads nothing and changes no other project file.
"""
import argparse
import json
import pathlib
import secrets
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

from project_bootstrap import channel, distribute, pointer  # noqa: E402
from project_bootstrap.contracts import Denied  # noqa: E402

KEYS = ROOT / 'src' / 'kit' / 'release-keys.txt'


def trusted_keys(project, cache, root_keys_text):
    path = pathlib.Path(project) / pointer.POINTER
    if not path.exists():
        return distribute.load_keys(root_keys_text), 'root'
    current = pointer.parse(path.read_text(encoding='utf-8'))
    return channel.trusted_after(cache, current['installed']), 'chain'


def install(args, root_keys_text=None, run=None):
    if root_keys_text is None:
        root_keys_text = KEYS.read_text(encoding='utf-8')
    keys, basis = trusted_keys(args.project, args.cache, root_keys_text)
    document = pathlib.Path(args.record).read_bytes()
    signature = pathlib.Path(args.signature).read_bytes()
    if channel.parse_record(document)['channel'] != args.channel:
        raise Denied('wrong-channel')
    work = tempfile.mkdtemp(prefix='bootstrap-install-')
    try:
        folder = distribute.unpack(args.archive, work)
        fields = channel.install(args.cache, folder, document, signature, keys)
        seeded = distribute.seed(args.project, folder) if args.seed else []
    finally:
        shutil.rmtree(work, ignore_errors=True)
    distribute.write_pointer(args.project, args.channel, fields['manifest'], args.source)
    result = {'installed': fields['manifest'], 'epoch': fields['epoch'], 'keys': basis,
              'seeded': len(seeded)}
    if args.check:
        gate = channel.GitWriteCheck(args.project, args.cache, **({'run': run} if run else {}))
        result['check'] = gate.confirm(secrets.token_hex(16), 'HANDOFF.md')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    for name in ('project', 'cache', 'archive', 'record', 'signature', 'channel', 'source'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--seed', action='store_true', help='copy the package into an empty project')
    parser.add_argument('--check', action='store_true', help='run one per-write check afterwards')
    args = parser.parse_args(argv)
    try:
        result = install(args)
    except (Denied, OSError) as exc:
        print('install_package: 拒絕：' + str(exc))
        return 1
    print('install_package: ' + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
