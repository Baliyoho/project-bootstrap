"""P2 slice 4: the capability matrix (F47, and the matrix part of F14).

``src/kit/capabilities.json`` is the only home for what each tool surface can
do. ``tools/build_kit.py`` renders the deployment package's cross-tool tables
from it, so the tables are a view, not a second copy.

Each fact is one cell: which capability, which surfaces it speaks for, whether
it is supported or missing, and on what basis:

- ``tested``: measured on the listed versions only;
- ``docs``: read in vendor documentation, optionally ``since`` a version;
- ``design``: what this project has built (or not) on its side.

``report`` answers for one surface at one version. A cell for another surface
or another tested version is never used in its place, documentation is never
promoted to verified, and a capability marked ``strict`` counts only when a
self-test probe passed in this run. ``strict_ready`` is true only when every
strict capability did. Summary cells are prose for the table and are never
read as evidence.

Standard library only and Python 3.8 compatible: build_kit.py imports it.
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
MATRIX = ROOT / 'src' / 'kit' / 'capabilities.json'
STATUSES = ('supported', 'missing')
BASES = ('tested', 'docs', 'design')
TABLE_RE = re.compile(r'^<!-- kit-table: (\S+) -->$')
VERSION_RE = re.compile(r'^\d+(\.\d+)*$')
CELL_KEYS = {'id', 'capability', 'surfaces', 'status', 'basis', 'tested', 'since',
             'summary', 'text', 'evidence', 'note'}


class MatrixError(Exception):
    pass


def _need(condition, message):
    if not condition:
        raise MatrixError(message)


def _text(value, where):
    _need(isinstance(value, str) and value.strip(), where + ' must be non-empty text')
    _need('\n' not in value and '|' not in value, where + ' cannot hold a newline or |')
    return value


def _version(value, where):
    _need(isinstance(value, str) and VERSION_RE.match(value), where + ' must be a dotted version')
    return value


def validate(data):
    """Check the matrix shape and cross references; return it unchanged."""
    _need(isinstance(data, dict) and data.get('schema') == 1, 'schema must be 1')
    _need(set(data) == {'schema', 'surfaces', 'capabilities', 'cells', 'tables'},
          'top-level keys must be schema, surfaces, capabilities, cells, tables')
    surfaces, caps = data['surfaces'], data['capabilities']
    _need(isinstance(surfaces, dict) and surfaces, 'surfaces must be a non-empty object')
    for name, row in surfaces.items():
        _need(isinstance(row, dict) and set(row) == {'tool', 'label'}, 'surface %s needs tool and label' % name)
        _text(row['tool'], 'surface %s tool' % name)
        _text(row['label'], 'surface %s label' % name)
    _need(isinstance(caps, dict) and caps, 'capabilities must be a non-empty object')
    for name, row in caps.items():
        _need(isinstance(row, dict) and set(row) == {'label', 'strict', 'impact', 'alternative'},
              'capability %s needs label, strict, impact, alternative' % name)
        _need(row['strict'] is True or row['strict'] is False, 'capability %s strict must be true or false' % name)
        for key in ('label', 'impact', 'alternative'):
            _text(row[key], 'capability %s %s' % (name, key))
    _need(any(row['strict'] for row in caps.values()), 'at least one capability must be strict')

    cells, covered = {}, {}
    _need(isinstance(data['cells'], list), 'cells must be a list')
    for cell in data['cells']:
        _need(isinstance(cell, dict) and set(cell) <= CELL_KEYS, 'cell has unknown keys: %r' % (cell,))
        cid = cell.get('id')
        _need(isinstance(cid, str) and cid and cid not in cells, 'cell id missing or repeated: %r' % (cid,))
        cells[cid] = cell
        _need(cell.get('capability') in caps, 'cell %s names an unknown capability' % cid)
        names = cell.get('surfaces')
        _need(isinstance(names, list) and names and len(set(names)) == len(names)
              and all(n in surfaces for n in names), 'cell %s surfaces must be known and distinct' % cid)
        for key in ('text', 'evidence', 'note'):
            if key in cell:
                _text(cell[key], 'cell %s %s' % (cid, key))
        if cell.get('summary'):
            _need(cell['summary'] is True, 'cell %s summary must be true' % cid)
            _need(set(cell) == {'id', 'capability', 'surfaces', 'summary', 'text'},
                  'summary cell %s carries only text, no status or evidence' % cid)
            continue
        _need(cell.get('status') in STATUSES, 'cell %s status must be one of %s' % (cid, STATUSES))
        basis = cell.get('basis')
        _need(basis in BASES, 'cell %s basis must be one of %s' % (cid, BASES))
        if basis == 'tested':
            tested = cell.get('tested')
            _need(isinstance(tested, list) and tested, 'tested cell %s must list the versions it was tested on' % cid)
            for v in tested:
                _version(v, 'cell %s tested version' % cid)
        else:
            _need('tested' not in cell, '%s cell %s cannot list tested versions' % (basis, cid))
        if 'since' in cell:
            _need(basis == 'docs', 'only a docs cell can say since')
            _version(cell['since'], 'cell %s since' % cid)
        for name in names:
            key = (name, cell['capability'])
            _need(key not in covered, 'two cells speak for %s / %s: %s and %s' % (name, key[1], covered.get(key), cid))
            covered[key] = cid

    tables = data['tables']
    _need(isinstance(tables, dict) and tables, 'tables must be a non-empty object')
    rendered = []
    for name, table in tables.items():
        _need(isinstance(table, dict) and set(table) == {'header', 'rows'}, 'table %s needs header and rows' % name)
        width = len(table['header'])
        _need(width >= 2, 'table %s needs at least two columns' % name)
        _need(isinstance(table['rows'], list) and table['rows'], 'table %s has no rows' % name)
        for row in [table['header']] + table['rows']:
            _need(isinstance(row, list) and len(row) == width, 'table %s rows must have %d items' % (name, width))
            for item in row:
                _item_text(data, item, name)
                if isinstance(item, dict) and 'cell' in item:
                    rendered.append((item['cell'], item.get('field', 'text')))
    for cid, cell in cells.items():
        for key in ('text', 'evidence'):
            if key in cell:
                count = rendered.count((cid, key))
                _need(count == 1, 'cell %s %s is rendered %d times, must be once' % (cid, key, count))
    return data


def _item_text(data, item, table):
    if isinstance(item, str):
        _need('\n' not in item and '|' not in item, 'table %s literal cannot hold a newline or |' % table)
        return item
    _need(isinstance(item, dict) and len(item) in (1, 2), 'table %s has a bad item: %r' % (table, item))
    if 'surface' in item and len(item) == 1:
        _need(item['surface'] in data['surfaces'], 'table %s names unknown surface %r' % (table, item['surface']))
        return data['surfaces'][item['surface']]['label']
    if 'capability' in item and len(item) == 1:
        _need(item['capability'] in data['capabilities'], 'table %s names unknown capability %r' % (table, item['capability']))
        return data['capabilities'][item['capability']]['label']
    _need('cell' in item and set(item) <= {'cell', 'field'}, 'table %s has a bad item: %r' % (table, item))
    field = item.get('field', 'text')
    _need(field in ('text', 'evidence'), 'table %s field must be text or evidence' % table)
    cell = next((c for c in data['cells'] if c['id'] == item['cell']), None)
    _need(cell is not None, 'table %s names unknown cell %r' % (table, item['cell']))
    _need(field in cell, 'table %s: cell %s has no %s' % (table, item['cell'], field))
    return cell[field]


def load(text):
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise MatrixError('capabilities.json is not JSON: %s' % exc)
    return validate(data)


def render_table(data, name):
    """Markdown lines for one table, in the deployment package's spacing."""
    _need(name in data['tables'], 'no table named ' + name)
    table = data['tables'][name]

    def line(items):
        return '|' + '|'.join(' %s ' % t if t else ' ' for t in items) + '|'
    out = [line([_item_text(data, item, name) for item in table['header']]),
           '|' + '|'.join('---' for _ in table['header']) + '|']
    out += [line([_item_text(data, item, name) for item in row]) for row in table['rows']]
    return out


def render_tables(prose, data):
    """Replace each ``<!-- kit-table: name -->`` line; every table is used exactly once."""
    out, used = [], []
    for line in prose.split('\n'):
        match = TABLE_RE.match(line)
        if not match:
            out.append(line)
            continue
        name = match.group(1)
        _need(name not in used, 'kit-table used twice: ' + name)
        used.append(name)
        out.extend(render_table(data, name))
    unused = sorted(set(data['tables']) - set(used))
    _need(not unused, 'tables not used by kit.md: ' + ', '.join(unused))
    return '\n'.join(out)


def _parts(version):
    return tuple(int(p) for p in version.split('.'))


def _declared(cell, version):
    """What the matrix says for this exact surface and version, before any probe."""
    if cell is None:
        return 'no-evidence', '矩陣沒有這個 surface 的紀錄'
    if cell['basis'] == 'design':
        return cell['status'], cell.get('note', '本專案這一側還沒有')
    if cell['basis'] == 'tested':
        if version is not None and version in cell['tested']:
            return cell['status'], '在這個版本實測：%s' % ('有' if cell['status'] == 'supported' else '沒有')
        return 'other-version', '只在 %s 實測過，不代用' % '、'.join(cell['tested'])
    if cell['status'] == 'missing':
        return 'missing', '官方文件說沒有'
    since = cell.get('since')
    if since is None:
        return 'documented', '官方文件說有，沒有在任何版本實測'
    if version is None or not VERSION_RE.match(version):
        return 'other-version', '官方文件說 %s 起才有，沒有給可比較的版本' % since
    if _parts(version) < _parts(since):
        return 'missing', '官方文件說 %s 起才有' % since
    return 'documented', '官方文件說 %s 起有，沒有在這個版本實測' % since


def _probe(probe):
    try:
        return 'pass' if probe() is True else 'fail'
    except Exception:
        return 'error'


def report(data, surface, version=None, probes=None):
    """Capability rows for one surface at one version.

    ``probes``: {capability: callable() -> bool}, the install/startup self-test.
    A probe that returns anything but ``True`` or raises makes the capability
    missing for this run, whatever the matrix says.
    """
    _need(surface in data['surfaces'], 'unknown surface: %r' % (surface,))
    probes = probes or {}
    unknown = sorted(set(probes) - set(data['capabilities']))
    _need(not unknown, 'probes for unknown capabilities: ' + ', '.join(unknown))
    cells = {}
    for cell in data['cells']:
        if surface in cell['surfaces'] and not cell.get('summary'):
            cells[cell['capability']] = cell
    rows = []
    for name, cap in data['capabilities'].items():
        declared, why = _declared(cells.get(name), version)
        live = _probe(probes[name]) if name in probes else 'not-run'
        if live in ('fail', 'error'):
            state, why = 'missing', '本次自測%s' % ('沒通過' if live == 'fail' else '出錯')
        elif live == 'pass':
            state, why = 'supported', '本次自測通過'
        elif declared == 'missing':
            state = 'missing'
        elif declared == 'supported' and not cap['strict']:
            state = 'supported'
        else:
            state = 'unverified'
            if declared == 'supported':
                why = '必要能力只認本次自測；' + why
        row = {'capability': name, 'label': cap['label'], 'strict': cap['strict'],
               'state': state, 'declared': declared, 'probe': live, 'why': why}
        if cells.get(name) is not None:
            row['cell'] = cells[name]['id']
        if state != 'supported':
            row['impact'] = cap['impact']
            row['alternative'] = cap['alternative']
        rows.append(row)
    strict_ready = all(row['state'] == 'supported' and row['probe'] == 'pass'
                       for row in rows if row['strict'])
    return {'surface': surface, 'tool': data['surfaces'][surface]['tool'],
            'version': version, 'strict_ready': strict_ready,
            'gaps': [row['capability'] for row in rows if row['state'] != 'supported'],
            'rows': rows}


def read_matrix(path=MATRIX):
    with open(path, encoding='utf-8', newline='') as handle:
        return load(handle.read())


def main(argv=None):
    parser = argparse.ArgumentParser(description='Report one surface from the capability matrix (no probes are run).')
    parser.add_argument('surface')
    parser.add_argument('--version')
    args = parser.parse_args(argv)
    try:
        result = report(read_matrix(), args.surface, args.version)
    except (MatrixError, OSError) as exc:
        print('capabilities: %s' % exc, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['strict_ready'] else 1


if __name__ == '__main__':
    sys.exit(main())
