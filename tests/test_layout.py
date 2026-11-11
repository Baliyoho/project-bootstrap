"""P1 slice 1: the development layout agrees with what verify_bootstrap.py reads.

verify_bootstrap.py must run on Python 3.8 without uv, so it reads pyproject.toml
and uv.lock with a small hand-written parser. This test reads both with tomllib
and checks the two views agree, so the simple parser cannot drift unnoticed.
"""
from pathlib import Path
import sys
import tomllib

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))

import verify_bootstrap  # noqa: E402


def load(name):
    return tomllib.loads((ROOT / name).read_text(encoding='utf-8'))


def test_package_imports_from_src():
    import project_bootstrap
    assert Path(project_bootstrap.__file__).parent == ROOT / 'src' / 'project_bootstrap'


def test_simple_parser_matches_tomllib():
    text = (ROOT / 'pyproject.toml').read_text(encoding='utf-8')
    data = load('pyproject.toml')
    licenses = verify_bootstrap.p1_section(text, 'tool.project-bootstrap.licenses')
    assert {k: v.strip('"') for k, v in licenses.items()} == data['tool']['project-bootstrap']['licenses']
    assert verify_bootstrap.p1_section(text, 'project')['requires-python'].strip('"') == \
        data['project']['requires-python']


def test_licenses_cover_exactly_the_locked_registry_packages():
    lock = load('uv.lock')
    registry = {p['name'] for p in lock['package'] if 'registry' in p['source']}
    assert set(load('pyproject.toml')['tool']['project-bootstrap']['licenses']) == registry


def test_every_locked_artifact_has_a_sha256():
    for package in load('uv.lock')['package']:
        if 'registry' not in package['source']:
            continue
        artifacts = package.get('wheels', []) + ([package['sdist']] if 'sdist' in package else [])
        assert artifacts, package['name']
        assert all(a['hash'].startswith('sha256:') for a in artifacts), package['name']


def test_verifier_check_passes_on_this_repo():
    sources = {p.relative_to(ROOT).as_posix(): p.read_text(encoding='utf-8')
               for folder in verify_bootstrap.P1_STDLIB_ONLY
               for p in sorted((ROOT / folder).glob('*.py')) if not p.name.startswith('test_')}
    assert verify_bootstrap.p1_layout_problems(
        (ROOT / 'pyproject.toml').read_text(encoding='utf-8'),
        (ROOT / 'uv.lock').read_text(encoding='utf-8'), sources) == []
