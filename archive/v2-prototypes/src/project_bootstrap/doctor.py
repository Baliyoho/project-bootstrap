"""M2 doctor for F16b: what this machine lacks, without reading secret values.

Three kinds of gap are kept apart because they need different fixes:
missing tool (install it), missing configuration (set the variable or file),
and connection failure (the tool and config exist but the call failed). A
connection is only attempted when its tool and configuration are present,
so an unset key is never reported as an outage. Variable values are never
read into the report; only whether the name is set and non-empty.
"""
import shutil


def diagnose(tools, configs, connections, environ, which=shutil.which):
    """``connections``: {name: (needs_tools, needs_configs, probe)}; probe() -> bool."""
    rows = []
    for name in tools:
        rows.append({'item': name, 'kind': 'tool',
                     'state': 'ok' if which(name) else 'missing-tool'})
    for name in configs:
        # Presence only: the value is looked at for emptiness and never stored.
        present = bool(environ.get(name, '').strip())
        rows.append({'item': name, 'kind': 'config',
                     'state': 'ok' if present else 'missing-config'})
    for name, (needs_tools, needs_configs, probe) in connections.items():
        missing = ([t for t in needs_tools if not which(t)]
                   + [c for c in needs_configs if not environ.get(c, '').strip()])
        if missing:
            state = 'not-attempted'
        else:
            try:
                state = 'ok' if probe() is True else 'connection-failed'
            except Exception:
                state = 'connection-failed'
        row = {'item': name, 'kind': 'connection', 'state': state}
        if missing:
            row['because'] = sorted(missing)
        rows.append(row)
    return {'ok': all(row['state'] == 'ok' for row in rows), 'rows': rows}
