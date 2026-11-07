"""macOS OS-boundary feasibility probe, NOT a supported production launcher.

Uses the host's deprecated sandbox-exec to compare a confined child against
the same-UID bypass counterexample. No desktop App/MCP process is reconfigured.
The profile is intentionally a narrow experimental boundary, not an escape
audit. Unsupported hosts return unverified, never a manufactured pass.
"""
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tempfile


PROFILE = '''(version 1)
(allow default)
(deny file-write*)
(allow file-write* (subpath (param "SCRATCH")))
(deny file-read* (subpath (param "VAULT")))
(deny network*)
'''

CHILD = '''import json, pathlib, subprocess, sys
vault, repo, scratch = map(pathlib.Path, sys.argv[1:4])
out = {}
try:
    (vault / 'private').read_bytes()
    out['private_read_blocked'] = False
except PermissionError:
    out['private_read_blocked'] = True
try:
    (repo / 'note').write_bytes(b'outside-write')
    out['direct_write_blocked'] = False
except PermissionError:
    out['direct_write_blocked'] = True
result = subprocess.run(['git', '-C', str(repo), 'hash-object', '-w', '--stdin'],
    input=b'SYNTHETIC_FORBIDDEN_IN_GIT', capture_output=True)
out['git_write_blocked'] = result.returncode != 0
result = subprocess.run(['/bin/sh', '-c', 'printf changed > "$1"', 'fixture', str(repo / 'note')],
    capture_output=True)
out['indirect_write_blocked'] = result.returncode != 0
(scratch / 'allowed').write_bytes(b'scratch-only')
out['scratch_allowed'] = True
import socket
try:
    with socket.create_connection(('127.0.0.1', int(sys.argv[4])), timeout=2):
        out['network_blocked'] = False
except PermissionError:
    out['network_blocked'] = True
print(json.dumps(out))
'''


def probe_isolation():
    launcher = Path('/usr/bin/sandbox-exec')
    if platform.system() != 'Darwin' or not launcher.is_file():
        return {'result': '未驗證', 'reason': '本探針限 macOS sandbox-exec；其他 OS 尚無 adapter'}
    with tempfile.TemporaryDirectory(prefix='bootstrap-v2-isolation-') as directory:
        root = Path(directory).resolve()
        vault, repo, scratch = (root / name for name in ('vault', 'repo', 'scratch'))
        for path in (vault, repo, scratch):
            path.mkdir()
        (vault / 'private').write_bytes(b'SYNTHETIC_PRIVATE_CAPABILITY')
        (repo / 'note').write_bytes(b'original')
        subprocess.run(['git', 'init', '-q', str(repo)], check=True, capture_output=True)
        objects = repo / '.git' / 'objects'
        before = sorted(str(path.relative_to(objects)) for path in objects.rglob('*'))
        with socket.socket() as server:
            server.bind(('127.0.0.1', 0))
            server.listen(1)
            result = subprocess.run([str(launcher), '-D', 'SCRATCH=' + str(scratch),
                '-D', 'VAULT=' + str(vault), '-p', PROFILE, sys.executable, '-B', '-c', CHILD,
                str(vault), str(repo), str(scratch), str(server.getsockname()[1])],
                env={'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1'}, capture_output=True, timeout=30)
        if result.returncode:
            return {'result': '不通過', 'reason': '隔離子程序未完成；不將啟動失敗當成已阻擋',
                    'exit_code': result.returncode}
        checks = json.loads(result.stdout)
        checks['protected_content_unchanged'] = (repo / 'note').read_bytes() == b'original'
        checks['objects_unchanged'] = before == sorted(str(path.relative_to(objects)) for path in objects.rglob('*'))
        checks['scratch_content_correct'] = (scratch / 'allowed').read_bytes() == b'scratch-only'
        return {'result': '通過' if all(value is True for value in checks.values()) else '不通過',
                'scope': '單一受包覆 macOS 子程序、繼承 sandbox 的 shell/Git；非目前桌面 App 或全部 MCP',
                'checks': checks,
                'unknown': 'deprecated launcher 只驗 OS 機制；未做逃逸審查／可信 launcher／真實工具與跨平台整合'}
