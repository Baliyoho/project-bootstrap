"""F31 prototype: which requirements, tests and projects a change touches.

The component → requirement map is read from the status index evidence
(each evidence path is tied to the IDs it supports), so there is no second
hand-kept map to drift. A test file supporting a requirement is a re-check
point for every component tied to that requirement. Projects declare which
released components they installed.

A changed path that no requirement or project claims is unclassified, and
any unclassified change widens the answer to everything: all tests, all
projects. The report says so instead of returning an empty, reassuring set.
"""


def graph_from_status(status):
    components = {}
    for row in status.get('requirements', []):
        items = [row] + list(row.get('parts', {}).values())
        for item in items:
            for evidence in item.get('evidence', []):
                path = evidence.get('path')
                if path:
                    components.setdefault(path, set()).add(row['id'])
    return components


def _is_test(path):
    return path.rsplit('/', 1)[-1].startswith('test_')


def impact(changed, components, projects):
    """``projects``: {name: set of component paths installed there}."""
    all_tests = {path for path in components if _is_test(path)}
    unclassified = sorted(path for path in changed
                          if path not in components
                          and not any(path in installed for installed in projects.values()))
    if unclassified:
        return {'scope': 'full', 'unclassified': unclassified,
                'requirements': sorted({i for ids in components.values() for i in ids}),
                'tests': sorted(all_tests), 'projects': sorted(projects)}
    requirements = set()
    for path in changed:
        requirements |= components.get(path, set())
    tests = {path for path in all_tests if components[path] & requirements}
    affected = sorted(name for name, installed in projects.items()
                      if any(path in installed for path in changed))
    return {'scope': 'targeted', 'unclassified': [], 'requirements': sorted(requirements),
            'tests': sorted(tests), 'projects': affected}
