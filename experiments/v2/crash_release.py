"""Release a guest run whose parent crashed (P0 prototype, decision Q1 (a)).

Two things must both hold, or the run stays blocked (Q1 falls back to (c)):

1. Host-side stop evidence: the runner's own stderr log, at the path the
   parent recorded before boot, ends with the stop marker the runner prints
   right before exit(0). Guest console output is never read.
2. A person at the host's local terminal types a fresh challenge. The prompt
   goes to /dev/tty, not stdin, so a piped agent cannot answer it; SSH
   sessions are refused.

Boundaries: the log is writable by any process with the same UID, and a
same-UID program can allocate its own pseudo-terminal. This raises the bar
against an agent answering for the user; it is not proof of a human. A
signing-key approval (Q1 (b)) is the planned replacement.

Usage, from the repo root:
    python3 -X utf8 -m experiments.v2.crash_release DB RUN_ID
Exit 0 released, 1 refused (nothing changed), 2 usage error.
"""
import datetime
import hashlib
import os
from pathlib import Path
import secrets
import stat
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.v2.contracts import Denied, Lab
from experiments.v2.guest_runs import STOP_MARKER, GuestRunLedger

# Exactly the lines the runner prints on a clean unshared run, in order.
# Anything else (start or stop errors, a shared directory) proves no stop.
HOST_LINES = ('HOST_NO_SHARED_DIRECTORY', 'HOST_CONFIG_VALID', 'HOST_STARTED', STOP_MARKER)
REMOTE_ENV = ('SSH_CONNECTION', 'SSH_CLIENT', 'SSH_TTY')
MAX_LOG = 64 * 1024
MAX_ANSWER = 200


def host_evidence(path, probe_id):
    """Read the runner log itself; refuse anything short of a clean host stop."""
    if not isinstance(path, str) or not os.path.isabs(path):
        raise Denied('crash-release-unconfirmed')
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as error:
        raise Denied('crash-release-unconfirmed') from error
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise Denied('crash-release-unconfirmed')
        data = os.read(fd, MAX_LOG + 1)
    finally:
        os.close(fd)
    if len(data) > MAX_LOG:
        raise Denied('crash-release-unconfirmed')
    try:
        lines = [line for line in data.decode('ascii').splitlines() if line]
    except UnicodeDecodeError as error:
        raise Denied('crash-release-unconfirmed') from error
    if lines != list(HOST_LINES):
        raise Denied('crash-release-unconfirmed')
    return {'probe_id': probe_id, 'stop_marker': STOP_MARKER, 'host_log': path,
            'host_log_sha256': hashlib.sha256(data).hexdigest()}


class Terminal:
    """The process's controlling terminal, opened directly (never stdin)."""

    def __init__(self, fd):
        self.fd = fd
        self.name = os.ttyname(fd)

    def write(self, text):
        os.write(self.fd, text.encode('utf-8'))

    def discard_pending(self):
        """Drop anything typed or injected before the challenge was shown."""
        import termios
        termios.tcflush(self.fd, termios.TCIFLUSH)

    def read_line(self):
        data = b''
        while not data.endswith(b'\n') and len(data) <= MAX_ANSWER:
            chunk = os.read(self.fd, 1)
            if not chunk:
                break
            data += chunk
        return data.decode('utf-8', errors='replace').strip()

    def close(self):
        os.close(self.fd)


def open_local_terminal(env=None, open_tty=None):
    env = os.environ if env is None else env
    if any(env.get(name) for name in REMOTE_ENV):
        raise Denied('crash-release-not-local')
    open_tty = open_tty or (lambda: os.open('/dev/tty', os.O_RDWR))
    try:
        fd = open_tty()
    except OSError as error:
        raise Denied('crash-release-no-terminal') from error
    if not os.isatty(fd):
        os.close(fd)
        raise Denied('crash-release-no-terminal')
    return Terminal(fd)


def local_confirmation(terminal, run, evidence, actor, challenge=None, now=None):
    """Show what will be released and require the person to type a fresh code."""
    challenge = challenge or secrets.token_hex(3)
    expected = f"release {run['run_id'][:8]} {challenge}"
    terminal.discard_pending()
    terminal.write(
        'Crash release: this marks a guest run as stopped and lets the actor start again.\n'
        f"  run      {run['run_id']}\n  actor    {actor}\n  epoch    {run['epoch']}\n"
        f"  probe    {evidence['probe_id']}\n  host log {evidence['host_log']}\n"
        f"  sha256   {evidence['host_log_sha256']}\n"
        'Check that no VM for this run is still running, then type exactly:\n'
        f'  {expected}\n> ')
    if terminal.read_line() != expected:
        terminal.write('Not released.\n')
        raise Denied('crash-release-not-approved')
    now = now or datetime.datetime.now(datetime.timezone.utc)
    return {'method': 'local-terminal', 'run_id': run['run_id'], 'tty': terminal.name,
            'confirmed_at': now.isoformat(timespec='seconds')}


def release(db, run_id, terminal_opener=open_local_terminal):
    """Evidence first: with no host proof the person is never even asked."""
    lab = Lab(db)
    try:
        ledger = GuestRunLedger(lab)
        row = ledger._row(run_id)
        run = next((item for item in ledger.unretired(row['actor'])
                    if item['run_id'] == run_id), None)
        if run is None:
            raise Denied('vm-run-not-current')
        path = ledger.host_log(run_id)
        if path is None:
            raise Denied('crash-release-unavailable')
        evidence = host_evidence(path, run['identity']['probe_id'])
        terminal = terminal_opener()
        try:
            confirmation = local_confirmation(terminal, run, evidence, row['actor'])
        finally:
            terminal.close()
        ledger.release_crashed(run_id, evidence, confirmation)
        return evidence, confirmation
    finally:
        lab.close()


def main(argv):
    if len(argv) != 2:
        print('usage: python3 -X utf8 -m experiments.v2.crash_release DB RUN_ID',
              file=sys.stderr)
        return 2
    try:
        evidence, confirmation = release(Path(argv[0]), argv[1])
    except Denied as error:
        print(f'refused: {error}', file=sys.stderr)
        return 1
    print(f"released {argv[1]} from {evidence['host_log']} via {confirmation['tty']}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
