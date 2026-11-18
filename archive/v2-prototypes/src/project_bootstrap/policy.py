"""F36／F37／F38 prototype: who owns each file, and project overrides that only tighten.

F36 ``plan_update``: a release lists every path it ships as ``core`` or
``adapter``; anything else under the managed roots must be declared ``project``
by the project. An update replaces released files only where the local copy
still equals the old release, keeps project files untouched, and stops on a
locally edited released file or a path whose owner nobody declared.

F37 ``merge``: the core policy is read-only; a project override may only fill
declared slots, in the declared direction. Unknown keys, a value that loosens,
a slot whose effect was never confirmed as restrictive, and any attempt to
switch off a mandatory rule are refused, so no effective policy is produced.

F38 ``check_schema``／``describe``: the schema states each slot's type,
direction and effect, and a direction that would let an override loosen (an
add-only list of *permissions*) is rejected at schema level: a legal position
is not assumed to be a tightening. ``describe`` prints the fillable slots and
the parts with no override entry at all.
"""
from project_bootstrap.contracts import Denied

RELEASED = {'core', 'adapter'}
DIRECTIONS = {'add-only': list, 'at-least': int, 'at-most': int, 'true-only': bool}
# Which direction tightens depends on what the slot does; only these pairs are coherent.
COHERENT = {('add-only', 'restrict'), ('at-least', 'restrict'), ('at-most', 'restrict'),
            ('true-only', 'restrict')}


def plan_update(old, new, local, project_owned, managed_roots):
    """Return {path: action}; raise Denied when ownership is unknown or core was edited.

    ``old``／``new``: {path: {'owner': 'core'|'adapter', 'sha256': ...}}.
    ``local``: {path: sha256} for every file now under ``managed_roots``.
    """
    for manifest in (old, new):
        if any(entry.get('owner') not in RELEASED for entry in manifest.values()):
            raise Denied('manifest-owner-invalid')
    plan = {}
    for path in sorted(set(local) | set(new)):
        if not any(path == root or path.startswith(root.rstrip('/') + '/')
                   for root in managed_roots):
            continue
        if path in project_owned:
            if path in new or path in old:
                raise Denied('ownership-conflict:' + path)
            plan[path] = 'keep-project'
        elif path in new:
            if path in local and path in old and local[path] != old[path]['sha256']:
                raise Denied('released-file-edited:' + path)
            if path in local and path not in old and local[path] != new[path]['sha256']:
                raise Denied('ownership-unknown:' + path)
            plan[path] = 'unchanged' if local.get(path) == new[path]['sha256'] else 'replace'
        elif path in old:
            if local[path] != old[path]['sha256']:
                raise Denied('released-file-edited:' + path)
            plan[path] = 'remove-released'
        else:
            raise Denied('ownership-unknown:' + path)
    return plan


def check_schema(schema):
    """Every slot must have a known direction whose type and effect cohere."""
    problems = []
    for name, slot in sorted(schema.get('slots', {}).items()):
        direction, effect = slot.get('direction'), slot.get('effect')
        if direction not in DIRECTIONS:
            problems.append((name, 'direction-unknown'))
        elif effect not in ('restrict', 'permit'):
            problems.append((name, 'effect-unconfirmed'))
        elif (direction, effect) not in COHERENT:
            problems.append((name, 'direction-loosens'))
    for name in schema.get('mandatory', ()):
        if name in schema.get('slots', {}):
            problems.append((name, 'mandatory-has-override-slot'))
    return problems


def merge(core, override, schema):
    """Effective policy, or Denied. ``core`` is never modified."""
    if check_schema(schema):
        raise Denied('schema-invalid')
    slots, mandatory = schema.get('slots', {}), set(schema.get('mandatory', ()))
    effective = dict(core)
    for key, value in override.items():
        if key in mandatory:
            raise Denied('mandatory-not-overridable:' + key)
        if key not in slots:
            raise Denied('unknown-field:' + key)
        direction = slots[key]['direction']
        kind = DIRECTIONS[direction]
        base = core.get(key, slots[key].get('default'))
        if type(value) is not kind or type(base) is not kind:
            raise Denied('type-mismatch:' + key)
        if direction == 'add-only':
            missing = [item for item in base if item not in value]
            if missing:
                raise Denied('loosens:' + key)
        elif direction == 'at-least' and value < base:
            raise Denied('loosens:' + key)
        elif direction == 'at-most' and value > base:
            raise Denied('loosens:' + key)
        elif direction == 'true-only' and base and not value:
            raise Denied('loosens:' + key)
        effective[key] = value
    return effective


def describe(schema):
    lines = ['可填的空位（只能往加嚴方向）：']
    for name, slot in sorted(schema.get('slots', {}).items()):
        lines.append(f"- {name}：{slot.get('direction')}，預設 {slot.get('default')!r}；{slot.get('doc', '')}")
    lines.append('不可改的部分（沒有覆寫入口）：')
    lines += [f'- {name}' for name in sorted(schema.get('mandatory', ()))]
    return '\n'.join(lines) + '\n'
