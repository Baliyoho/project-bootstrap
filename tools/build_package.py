#!/usr/bin/env python3
"""Build the formal package folder from src/kit (P2 slice 1, 2026-11-11).

The package is one file per deployed path plus manifest.json, which lists
each file's SHA-256, owner (core／adapter／project) and how an update may touch
it. The ownership table is src/kit/owners.json; a template without an entry
stops the build. Output goes to dist/package/ (ignored by Git), because the
package is a build output like PROJECT-BOOTSTRAP.md, but not one projects copy.

    python3 -X utf8 tools/build_package.py            # build dist/package/
    python3 -X utf8 tools/build_package.py --check    # build twice, compare, write nothing

Builds are always debug. A formal package only comes from the publish step
(P2 slice 3); there is deliberately no flag for it here.
"""
import argparse
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tools'))

import build_kit  # noqa: E402
from project_bootstrap import package  # noqa: E402
from project_bootstrap.contracts import Denied  # noqa: E402

OWNERS = ROOT / 'src' / 'kit' / 'owners.json'
OUT = ROOT / 'dist' / 'package'


def build_once():
    prose, files = build_kit.load_source()
    kit_text = build_kit.build(prose, files)
    owners = package.load_owners(build_kit.read_lf(OWNERS))
    return package.build(prose, files, owners, kit_text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--check', action='store_true', help='build twice and compare; write nothing')
    parser.add_argument('--out', default=str(OUT), help='output folder (default dist/package)')
    args = parser.parse_args(argv)
    folders = []
    try:
        first, manifest = build_once()
        folders.append(first)
        problems = package.check(first)
        if problems:
            print('build_package: 包與 manifest 不符：' + ', '.join(problems))
            return 1
        if args.check:
            second, again = build_once()
            folders.append(second)
            if package.digest(again) != package.digest(manifest):
                print('build_package: 同一份來源建兩次 digest 不同')
                return 1
            print('build_package: 可重現，%d 個檔，digest %s' % (
                len(manifest['components']), package.digest(manifest)))
            return 0
        target = package.install(first, args.out)
        folders.remove(first)
        print('build_package: 已建 %s（%s 版、%s、%d 個檔），digest %s' % (
            target, manifest['version'], manifest['kind'], len(manifest['components']),
            package.digest(manifest)))
        return 0
    except (build_kit.KitError, Denied, OSError) as exc:
        print('build_package: ' + str(exc))
        return 2
    finally:
        for folder in folders:
            shutil.rmtree(folder, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
