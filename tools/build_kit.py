#!/usr/bin/env python3
"""Build PROJECT-BOOTSTRAP.md from its source in src/kit/ (P1 slice 3, 2026-11-11).

Source layout:
- src/kit/kit.md: the deployment package's prose. Inside a section 3.x fenced
  block, a single line ``<!-- kit-file: <deploy path> -->`` stands for the body.
- src/kit/files/<deploy path>.tmpl: one template file per deployed file. The
  .tmpl suffix keeps a template .gitignore, .gitattributes, skill or hook config
  from taking effect inside this repo.

PROJECT-BOOTSTRAP.md stays committed: projects copy it, and sync_project.py
reads it and its Git history. It is a build output; edit the source and rerun:

    python3 -X utf8 tools/build_kit.py            # write PROJECT-BOOTSTRAP.md
    python3 -X utf8 tools/build_kit.py --check    # exit 1 if it is out of date

Standard library only (Python 3.8+), like verify_bootstrap.py.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'src' / 'kit'
PROSE = SOURCE / 'kit.md'
FILES = SOURCE / 'files'
OUTPUT = ROOT / 'PROJECT-BOOTSTRAP.md'
SUFFIX = '.tmpl'
DIRECTIVE_RE = re.compile(r'^<!-- kit-file: (\S+) -->$')
HEAD_RE = re.compile(r'^### 3\.\d+ ')
FENCE_RE = re.compile(r'^(`{3,})(\w*)\s*$')


class KitError(Exception):
    pass


def read_lf(path):
    with open(path, encoding='utf-8', newline='') as handle:
        return handle.read().replace('\r\n', '\n')


def write_lf(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as handle:
        handle.write(text)


def section_blocks(lines):
    """Yield (paths, [(open, close) line indexes]) per section 3.x, the way extract() reads it."""
    heads = [i for i, line in enumerate(lines) if HEAD_RE.match(line)]
    for n, i in enumerate(heads):
        end = heads[n + 1] if n + 1 < len(heads) else len(lines)
        paths = [p for p in re.findall(r'`([^`]+)`', lines[i]) if '.' in p or '/' in p]
        blocks, j = [], i
        while j < end:
            match = FENCE_RE.match(lines[j])
            if not match:
                j += 1
                continue
            k = j + 1
            while k < end and lines[k].rstrip() != match.group(1):
                k += 1
            blocks.append((j, k))
            j = k + 1
        yield paths, blocks


def split(kit):
    """Turn a built PROJECT-BOOTSTRAP.md into (prose, {deploy path: content})."""
    lines = kit.split('\n')
    files, replace = {}, {}
    for paths, blocks in section_blocks(lines):
        if not paths or not blocks:
            continue
        if len(blocks) < len(paths):
            raise KitError('section has fewer blocks than files: %s' % ', '.join(paths))
        for path, (start, end) in zip(paths, blocks):
            if path in files:
                raise KitError('file appears twice: ' + path)
            files[path] = '\n'.join(lines[start + 1:end]) + '\n'
            replace[start] = (end, path)
    out, i = [], 0
    while i < len(lines):
        out.append(lines[i])
        if i in replace:
            end, path = replace[i]
            out.append('<!-- kit-file: %s -->' % path)
            out.append(lines[end])
            i = end
        i += 1
    return '\n'.join(out), files


def build(prose, files):
    """Inverse of split: put every template back into its fenced block."""
    lines = prose.split('\n')
    out, used, fence = [], [], None
    for line in lines:
        match = FENCE_RE.match(line)
        directive = DIRECTIVE_RE.match(line)
        if directive:
            path = directive.group(1)
            if fence is None:
                raise KitError('kit-file outside a fenced block: ' + path)
            if path in used:
                raise KitError('kit-file used twice: ' + path)
            if path not in files:
                raise KitError('kit-file has no template: ' + path)
            body = files[path]
            if not body.endswith('\n'):
                raise KitError('template must end with a newline: ' + path)
            if any(row.rstrip() == fence for row in body[:-1].split('\n')):
                raise KitError('template contains its own closing fence: ' + path)
            used.append(path)
            out.append(body[:-1])
            continue
        if match and fence is None:
            fence = match.group(1)
        elif fence is not None and line.rstrip() == fence:
            fence = None
        out.append(line)
    unused = sorted(set(files) - set(used))
    if unused:
        raise KitError('templates not used by kit.md: ' + ', '.join(unused))
    return '\n'.join(out)


def load_source(source=SOURCE):
    files = {}
    root = source / 'files'
    for path in sorted(root.rglob('*')):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            if not rel.endswith(SUFFIX):
                raise KitError('template without %s suffix: %s' % (SUFFIX, rel))
            files[rel[:-len(SUFFIX)]] = read_lf(path)
    return read_lf(source / 'kit.md'), files


def write_source(prose, files, source=SOURCE):
    write_lf(source / 'kit.md', prose)
    for rel, text in files.items():
        write_lf(source / 'files' / (rel + SUFFIX), text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--check', action='store_true', help='exit 1 if PROJECT-BOOTSTRAP.md is out of date')
    args = parser.parse_args(argv)
    try:
        built = build(*load_source())
    except (KitError, OSError) as exc:
        print('build_kit: ' + str(exc))
        return 2
    current = read_lf(OUTPUT) if OUTPUT.exists() else None
    if args.check:
        if built != current:
            print('build_kit: PROJECT-BOOTSTRAP.md 與 src/kit 不一致；改來源後跑 python3 -X utf8 tools/build_kit.py')
            return 1
        print('build_kit: PROJECT-BOOTSTRAP.md 與 src/kit 一致')
        return 0
    if built != current:
        write_lf(OUTPUT, built)
        print('build_kit: 已重生 PROJECT-BOOTSTRAP.md')
    else:
        print('build_kit: PROJECT-BOOTSTRAP.md 已是最新')
    return 0


if __name__ == '__main__':
    sys.exit(main())
