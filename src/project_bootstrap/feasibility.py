"""Executable disproofs of strong claims about an ordinary same-UID broker.

Every path is an isolated TemporaryDirectory; no live repo, credentials,
network, paid API or model is used. Expected counterexamples make the harness
pass, but the associated requirements remain NOT MET.
"""
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading

from project_bootstrap.contracts import Denied, Lab


def run_probes():
    findings = []
    with tempfile.TemporaryDirectory(prefix='bootstrap-v2-feasibility-') as directory:
        root = Path(directory)
        db = root / 'private.sqlite'
        lab = Lab(db)
        try:
            cap = lab.register('synthetic-agent')
            lab.write(cap, 'note', None, b'broker-content')
            # File mode 0600 does not separate two processes with the same UID.
            db.chmod(0o600)
            subprocess.run([sys.executable, '-c',
                "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); "
                "c.execute(\"UPDATE files SET content=? WHERE path='note'\", (b'outside-write',)); "
                "c.commit()", str(db)], check=True, capture_output=True, timeout=15)
            changed = lab.db.execute('SELECT content FROM files').fetchone()[0] == b'outside-write'
            journal_count = lab.db.execute('SELECT count(*) FROM writes').fetchone()[0]
            findings.append({'id': 'same-uid-journal-bypass', 'requirements': ['F11(b)', 'F42', 'F48'],
                'counterexample_observed': changed and journal_count == 1,
                'requirement_result': '不通過',
                'scope': '同 UID 子程序直接修改合成內容庫，未產生對應事件；0600 無法隔離同 UID',
                'next': '代理與 agent 分權或經驗收的 OS sandbox；不可把此 API 原型當安全邊界'})

            git_dir = root / 'repo'
            subprocess.run(['git', 'init', '-q', str(git_dir)], check=True, capture_output=True)
            synthetic = b'SYNTHETIC_FORBIDDEN_IN_GIT'
            hashed = subprocess.run(['git', '-C', str(git_dir), 'hash-object', '-w', '--stdin'],
                input=synthetic, capture_output=True, check=True, timeout=15).stdout.strip()
            read = subprocess.run(['git', '-C', str(git_dir), 'cat-file', 'blob', hashed.decode()],
                capture_output=True, check=True, timeout=15).stdout
            findings.append({'id': 'direct-git-object-bypass', 'requirements': ['F43(a)'],
                'counterexample_observed': read == synthetic,
                'requirement_result': '不通過',
                'scope': '受信掃描函式之外的 Git 可直接寫入合成禁入值，無需 commit 或 hook',
                'next': '在寫入 object database 之前隔離直接 Git、GUI、MCP 與其他可寫入口'})

            ticket = lab.begin(cap, 0)
            # A real ongoing process has already loaded the old premise.
            worker = subprocess.Popen([sys.executable, '-u', '-c',
                "import sys; premise='old-premise'; print('loaded', flush=True); "
                "sys.stdin.readline(); print('used:'+premise, flush=True)"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                loaded = queue.Queue()
                reader = threading.Thread(target=lambda: loaded.put(worker.stdout.readline()), daemon=True)
                reader.start()
                if loaded.get(timeout=15) != 'loaded\n':
                    raise RuntimeError('fixture-worker-not-ready')
                reader.join(timeout=1)
                lab.propose('new-premise')
                output, _ = worker.communicate('continue\n', timeout=15)
                blocked = False
                try:
                    lab.complete(cap, ticket)
                except Denied:
                    blocked = True
                findings.append({'id': 'running-context-still-uses-old-premise', 'requirements': ['F28'],
                    'counterexample_observed': output.splitlines() == ['used:old-premise'] and blocked,
                    'requirement_result': '不通過',
                    'scope': '已啟動子程序仍以舊前提計算；代理拒絕完成不等於使用前已得知',
                    'next': '可暫停及重建上下文的執行介面，另驗即時推送、排空與斷線重連'})
            finally:
                if worker.poll() is None:
                    worker.kill()
                    worker.communicate()
        finally:
            lab.close()
    return findings
