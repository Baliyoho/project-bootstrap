#!/usr/bin/env python3
"""F29／F49: rerunnable mutation checks for the v2 guards.

``mutants.json`` lists, per group of test modules, guard edits that remove or
weaken one check. Each mutant is applied to a fresh copy of ``experiments/``
in a temporary directory, the group's tests run, and the result is:

- killed: the tests fail, so the guard is really exercised;
- survived: the tests still pass, so the guard is untested or redundant;
- stale: the original text no longer occurs exactly once, so the spec must be
  updated before it proves anything.

Only an all-killed run exits 0. The working tree is never modified. This is
slow (one test run per mutant) and therefore not part of verify_v2 by default.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent.parent


def run(spec, source_root=ROOT, python=sys.executable, only=None):
    results = []
    with tempfile.TemporaryDirectory(prefix='bootstrap-v2-mutants-') as directory:
        work = Path(directory)
        shutil.copytree(source_root / 'experiments', work / 'experiments',
                        ignore=shutil.ignore_patterns('__pycache__'))
        env = {'PATH': os.environ.get('PATH', os.defpath), 'PYTHONDONTWRITEBYTECODE': '1',
               'HOME': directory}
        for group in spec['groups']:
            if only and not set(only) & set(group['tests']):
                continue
            for mutant in group['mutants']:
                target = work / mutant['file']
                row = {'file': mutant['file'], 'old': mutant['old'], 'tests': group['tests']}
                try:
                    original = target.read_text(encoding='utf-8')
                except OSError:
                    row['outcome'] = 'stale'
                    results.append(row)
                    continue
                if original.count(mutant['old']) != 1:
                    row['outcome'] = 'stale'
                    results.append(row)
                    continue
                target.write_text(original.replace(mutant['old'], mutant['new'], 1),
                                  encoding='utf-8')
                try:
                    done = subprocess.run([python, '-m', 'unittest', *group['tests']], cwd=work,
                                          env=env, capture_output=True, timeout=600)
                    row['outcome'] = 'killed' if done.returncode else 'survived'
                except subprocess.TimeoutExpired:
                    row['outcome'] = 'killed-timeout'
                finally:
                    target.write_text(original, encoding='utf-8')
                results.append(row)
    counts = {}
    for row in results:
        counts[row['outcome']] = counts.get(row['outcome'], 0) + 1
    ok = bool(results) and all(row['outcome'].startswith('killed') for row in results)
    return {'ok': ok, 'counts': counts, 'results': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', default=str(Path(__file__).with_name('mutants.json')))
    parser.add_argument('--only', action='append', help='test module to limit the run to')
    args = parser.parse_args()
    spec = json.loads(Path(args.spec).read_text(encoding='utf-8'))
    report = run(spec, only=args.only)
    for row in report['results']:
        if not row['outcome'].startswith('killed'):
            first = row['old'].strip().splitlines()[0][:70]
            print(f"{row['outcome'].upper()}: {row['file']}: {first}")
    print('結果：' + ('全部擋下' if report['ok'] else '有存活或過期的 mutant'),
          json.dumps(report['counts'], sort_keys=True))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
