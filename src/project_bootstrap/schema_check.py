"""M2 prototype: JSON Schema for the v2 status index and the mutation spec (P1 slice 4).

Needs the third-party ``jsonschema`` package (locked in uv.lock), so it is not
imported by anything A4 runs; ``uv run pytest`` runs its tests. Schema-valid
means the structure is right, not that the content is true: registry.validate
still checks IDs against the decision document and that evidence paths exist,
and mutants.py still has to run each mutant. Format keywords are not enforced.

Usage, from the repo root:  uv run python -X utf8 -m project_bootstrap.schema_check
"""
import json
from pathlib import Path
import sys

import jsonschema

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TARGETS = {'status': ROOT / 'experiments/v2/status.json', 'mutants': HERE / 'mutants.json'}


def schema(name):
    data = json.loads((HERE / (name + '.schema.json')).read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator.check_schema(data)
    return data


def schema_errors(name, data):
    """Return 'path: message' strings, sorted, empty when the data fits the schema."""
    validator = jsonschema.Draft202012Validator(schema(name))
    errors = []
    for error in validator.iter_errors(data):
        where = '/'.join(str(part) for part in error.absolute_path) or '(root)'
        errors.append('%s: %s' % (where, error.message))
    return sorted(errors)


def main():
    bad = 0
    for name, path in TARGETS.items():
        errors = schema_errors(name, json.loads(path.read_text(encoding='utf-8')))
        print('%s：%s' % (path.relative_to(ROOT).as_posix(), '符合 schema' if not errors else '；'.join(errors[:5])))
        bad += bool(errors)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
