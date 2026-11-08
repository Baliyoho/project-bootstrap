"""P0 guarded-worker lifecycle and POSIX ticket custody, synthetic fixtures only.

Plans come from the trusted parent, never agent RPC. An unresolved persisted
run blocks replacement; a PID is NOT authority to kill or adopt a process.
The guardian handles parent EOF; arbitrary descendants require OS confinement.
This module does not authenticate a human or recover a lost guardian.
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import queue
import secrets
import stat
import subprocess
import sys
import threading

from experiments.v2.contracts import Denied


class TicketVault:
    """Existing parent-owned 0700 directory, exclusive 0600 private files.

    Same-UID access still requires OS isolation. No automatic permission repair,
    ticket replacement, deletion, renewal or recovery from missing files.
    """
    def __init__(self, directory):
        if os.name != 'posix' or not hasattr(os, 'O_NOFOLLOW'):
            raise Denied('ticket-vault-platform-unverified')
        self.directory = Path(directory)
        self.fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        info = os.fstat(self.fd)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            os.close(self.fd)
            raise Denied('ticket-vault-permissions')

    def close(self):
        os.close(self.fd)

    def check(self):
        info = os.fstat(self.fd)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise Denied('ticket-vault-permissions')
        return info

    @staticmethod
    def valid(value):
        return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)

    def save(self, ticket):
        self.check()
        if not self.valid(ticket):
            raise Denied('invalid-launch-ticket')
        handle = secrets.token_hex(32)
        fd = os.open(handle, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=self.fd)
        try:
            # fdopen handles short writes; close happens even if write/fsync fails.
            with os.fdopen(fd, 'wb') as stream:
                stream.write(ticket.encode('ascii'))
                stream.flush()
                os.fsync(stream.fileno())
            os.fsync(self.fd)
        except BaseException:
            # Keep an incomplete private artifact for explicit recovery; never
            # return its handle as if a ticket had been saved successfully.
            raise
        return handle

    def load(self, handle):
        self.check()
        if not self.valid(handle):
            raise Denied('invalid-ticket-handle')
        fd = os.open(handle, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.fd)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
                raise Denied('ticket-file-permissions-or-alias')
            raw = stream.read(65)
        try:
            ticket = raw.decode('ascii')
        except UnicodeError:
            raise Denied('invalid-ticket-file') from None
        if not self.valid(ticket):
            raise Denied('invalid-ticket-file')
        return ticket

    @staticmethod
    def file_identity(fd):
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
            raise Denied('private-file-permissions-or-alias')
        return f'{info.st_dev}:{info.st_ino}'

    def new_reap_record(self):
        directory = self.check()
        name = 'reap-' + secrets.token_hex(32)
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=self.fd)
        try:
            identity = self.file_identity(fd)
            os.fsync(fd)
            os.fsync(self.fd)
        except BaseException:
            os.close(fd)
            raise
        return fd, (name, f'{directory.st_dev}:{directory.st_ino}', identity)

    def confirm_reap(self, record):
        if record is None:
            raise Denied('worker-reap-unconfirmed')
        name = record['name']
        directory = self.check()
        if (not isinstance(name, str) or not name.startswith('reap-') or not self.valid(name[5:])
                or record['vault'] != f'{directory.st_dev}:{directory.st_ino}'):
            raise Denied('worker-reap-unconfirmed')
        try:
            fd = os.open(name, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.fd)
            try:
                if self.file_identity(fd) != record['identity']:
                    raise Denied('worker-reap-unconfirmed')
                proof = os.read(fd, 128)
                if proof != b'not-started\n':
                    code = int(proof.removeprefix(b'reaped:').strip())
                    if proof != ('reaped:%d\n' % code).encode('ascii'):
                        raise Denied('worker-reap-unconfirmed')
                os.fsync(fd)
            finally:
                os.close(fd)
        except (ValueError, OSError, Denied):
            raise Denied('worker-reap-unconfirmed') from None


@dataclass(frozen=True)
class LaunchPlan:
    argv: tuple
    cwd: str

    def fingerprint(self):
        if (not isinstance(self.argv, tuple) or not self.argv
                or any(not isinstance(arg, str) or '\x00' in arg for arg in self.argv)
                or not Path(self.argv[0]).is_absolute() or not Path(self.cwd).is_absolute()):
            raise Denied('invalid-launch-plan')
        executable = Path(self.argv[0]).resolve(strict=True)
        cwd = Path(self.cwd).resolve(strict=True)
        info = cwd.stat()
        if not cwd.is_dir() or not executable.is_file():
            raise Denied('invalid-launch-plan')
        # Bind fixed argv, executable bytes, and cwd identity. The parent must
        # separately protect scripts/imports/config read by that executable.
        payload = [self.argv, str(executable), hashlib.sha256(executable.read_bytes()).hexdigest(),
                   str(cwd), info.st_dev, info.st_ino]
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


@dataclass
class RunningChild:
    process: object
    channel: object
    reader: object
    lifetime: int
    record: str
    reaped: bool = False


class ProcessLauncher:
    READY = b'bootstrap-v2-ready\n'

    def __init__(self, authority, vault, timeout=2):
        self.authority, self.vault = authority, vault
        self.broker, self.lab = authority.broker, authority.lab
        self.timeout = timeout
        self.children = {}
        self.lab.db.executescript('''
            CREATE TABLE IF NOT EXISTS managed_launches (
                actor TEXT PRIMARY KEY, plan TEXT NOT NULL, state TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS managed_reap_records (
                actor TEXT PRIMARY KEY, name TEXT NOT NULL, vault TEXT NOT NULL, identity TEXT NOT NULL);
        ''')

    def confirm_reap(self, actor, expected=None):
        record = self.lab.db.execute(
            'SELECT * FROM managed_reap_records WHERE actor=?', (actor,)).fetchone()
        if expected is not None and (record is None or record['name'] != expected):
            raise Denied('worker-reap-unconfirmed')
        self.vault.confirm_reap(record)

    def reconcile(self, handle, plan):
        """Explicit restart path. No PID is read, signaled, or trusted."""
        key = self.authority.ticket_hash(self.vault.load(handle))
        with self.broker.lock, self.lab.transaction():
            actor = self.authority.permit(key)['actor']
            if actor in self.children:
                raise Denied('process-still-owned')
            row = self.lab.db.execute('SELECT * FROM managed_launches WHERE actor=?', (actor,)).fetchone()
            if row is None or row['plan'] != plan.fingerprint():
                raise Denied('launch-plan-changed')
            if row['state'] == 'stopped':
                return actor
            if row['state'] not in ('starting', 'running', 'stopping', 'unresolved'):
                raise Denied('invalid-managed-state')
            self.confirm_reap(actor)
            self.state(actor, 'stopped')
            return actor

    def state(self, actor, value):
        with self.lab.transaction():
            self.lab.db.execute('UPDATE managed_launches SET state=? WHERE actor=?', (value, actor))

    def stop(self, actor):
        """Revoke the local pipe first; persist stopped only after actual wait.

        No PIDs are saved/adopted. Restart callers use explicit reconciliation
        before replacing a child whose local ownership was lost.
        """
        with self.broker.lock:
            child = self.children.get(actor)
            if child is None:
                row = self.lab.db.execute('SELECT state FROM managed_launches WHERE actor=?', (actor,)).fetchone()
                if row is not None and row['state'] != 'stopped':
                    raise Denied('unresolved-previous-process')
                return
            if child.channel is not None:
                self.broker.detach(child.channel)
            try:
                journal_error = None
                try:
                    self.state(actor, 'stopping')
                except Exception as error:
                    journal_error = error
                if child.lifetime is not None:
                    os.close(child.lifetime)
                    child.lifetime = None
                # Do not kill a slow guardian: that could orphan its worker.
                child.process.wait(timeout=self.timeout + 2)
                if not child.reaped:
                    self.confirm_reap(actor, child.record)
                    child.reaped = True
                if child.reader is not None:
                    child.reader.join(timeout=self.timeout)
                    if child.reader.is_alive():
                        raise Denied('child-reader-not-stopped')
                if child.process.poll() is None:
                    raise Denied('child-not-stopped')
                for stream in (child.process.stdin, child.process.stdout):
                    stream.close()
                if journal_error is not None:
                    raise journal_error
                self.state(actor, 'stopped')
                del self.children[actor]
            except BaseException:
                # Retain the local object and non-stopped durable state. Never
                # create a replacement after a failed cleanup/journal write.
                raise

    def start(self, handle, plan):
        with self.broker.lock:
            ticket = self.vault.load(handle)
            key = self.authority.ticket_hash(ticket)
            # Read identity even if expired, so an owned old child is stopped
            # before refusing its replacement. No name supplied by the agent.
            row = self.lab.db.execute('SELECT actor FROM launch_permits WHERE ticket_hash=?', (key,)).fetchone()
            if row is None:
                raise Denied('launch-not-authorized')
            actor = row['actor']
            self.stop(actor)
            fingerprint = plan.fingerprint()
            descriptors = []
            try:
                with self.lab.transaction():
                    self.authority.permit(key)
                    previous = self.lab.db.execute('SELECT * FROM managed_launches WHERE actor=?', (actor,)).fetchone()
                    if previous is not None and previous['plan'] != fingerprint:
                        raise Denied('launch-plan-changed')
                    report, record = self.vault.new_reap_record()
                    descriptors.append(report)
                    self.lab.db.execute('INSERT OR REPLACE INTO managed_launches VALUES (?, ?, ?)',
                                        (actor, fingerprint, 'starting'))
                    self.lab.db.execute('INSERT OR REPLACE INTO managed_reap_records VALUES (?, ?, ?, ?)',
                                        (actor, *record))
            except BaseException:
                for fd in descriptors:
                    os.close(fd)
                raise
            try:
                try:
                    watch, lifetime = os.pipe()
                    descriptors.extend((watch, lifetime))
                    command = (sys.executable, '-B', '-I', str(Path(__file__).with_name('guardian.py').resolve()),
                               str(watch), str(report), str(self.timeout), json.dumps(plan.argv))
                    process = subprocess.Popen(command, cwd=plan.cwd, stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, close_fds=True,
                        pass_fds=(watch, report),
                        env={'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1'})
                    child = RunningChild(process, None, None, lifetime, record[0])
                    self.children[actor] = child
                    descriptors.remove(lifetime)
                finally:
                    for fd in descriptors:
                        os.close(fd)
                ready = queue.Queue(maxsize=1)

                def handshake():
                    try:
                        ready.put(process.stdout.readline(len(self.READY) + 1))
                    except OSError:
                        ready.put(None)

                child.reader = threading.Thread(target=handshake, daemon=True)
                child.reader.start()
                try:
                    message = ready.get(timeout=self.timeout)
                except queue.Empty:
                    raise Denied('child-start-timeout') from None
                if message != self.READY or process.poll() is not None:
                    raise Denied('child-not-ready')
                # Expiry/revocation may have happened during startup. Only now
                # rotate identity and give the parent a new broker channel.
                child.channel = self.authority.connect(ticket)
                self.state(actor, 'running')
                process.stdin.write(b'bootstrap-v2-go\n')
                process.stdin.flush()
                return child
            except BaseException:
                if actor in self.children:
                    self.stop(actor)
                else:
                    # Popen did not return ownership: fail closed, since an
                    # unusual spawn failure may leave process state unknown.
                    self.state(actor, 'unresolved')
                raise

    def check(self):
        """Called by the parent event loop; not a background expiry watchdog."""
        with self.broker.lock:
            for actor, child in list(self.children.items()):
                try:
                    with self.lab.transaction():
                        child.channel.authorize(child.channel)
                    if child.process.poll() is not None:
                        raise Denied('child-ended')
                except BaseException:
                    self.stop(actor)
                    raise

    def close(self):
        for actor in list(self.children):
            self.stop(actor)
