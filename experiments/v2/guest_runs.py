"""Durable ledger for synthetic unshared guest runs (P0 prototype only).

The trusted parent records each guest before it boots, then its host-side stop
evidence. A reopened database can only check that ledger: it never infers a
stop from a stale PID, wall-clock time or guest-written logs. Any run that is
not durably retired keeps the actor blocked. The identity below names the
images and scripts the parent chose; it is not attestation that the guest ran
them, and the run id is a parent-issued label, not a VM identity proof.

Each running guest is bound to one broker channel capability (stored only as a
digest). Retirement rotates that actor's capability in the same transaction,
so the retired guest's channel is refused by the broker itself.

A parent that dies before retirement leaves the run blocked. The only way out
is release_crashed: host-side stop evidence read from the runner log path the
parent recorded before boot, plus a confirmation typed at the host's local
terminal (gathered by crash_release.py, never by this object). Without both
the run stays blocked, which is decision Q1 (a) falling back to (c).

A whole-host crash kills the runner too, so its stop line is never written.
For that case (decision Q15 (a)) the parent also records the host's boot
session id (macOS kern.bootsessionuuid) before boot. If the id read at release
time differs, the host has rebooted since, so that VM process is gone; this
still needs the same local confirmation. The id is not a clock or a PID and a
same-UID process cannot set it, but the recorded copy lives in this database,
which a same-UID process can edit like everything else here.

A ledger file that is deleted or emptied would otherwise read exactly like a
first start. A parent that passes anchor= gets a second record outside the
database: the first open writes a random ledger id to the anchor file (fsynced,
directory fsynced) before storing the same id in the database. Afterwards the
ledger opens only when both exist and match; a lost, emptied or swapped
database with the anchor still present is refused, and so is a database whose
anchor is gone. Keep the anchor in a different directory from the database.
The anchor is only as durable as the filesystem, and a same-UID process can
delete both; it catches accidental loss, not a forger. Clearing a refusal is a
human step: confirm no guest of that ledger can still be running, then remove
the anchor file by hand.
"""
import hashlib
import json
import os
import re
import secrets
import stat
import subprocess

from experiments.v2.contracts import Denied

STOP_MARKER = 'HOST_STOPPED state=0'
IDENTITY_DIGESTS = ('runner', 'guest_init', 'tool', 'kernel', 'ramdisk')
_HEX64 = re.compile(r'[0-9a-f]{64}')
_PROBE_ID = re.compile(r'[A-Za-z0-9_-]{1,64}')
BOOT_SESSION = re.compile(r'[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}')
SYSCTL = '/usr/sbin/sysctl'
_ANCHOR = re.compile(rb'GUEST_LEDGER ([0-9a-f]{32})\n')
MAX_ANCHOR = 64


def read_anchor(path):
    """Ledger id in the anchor file, or None when no file is there; odd files are refused."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return None
    except OSError:
        raise Denied('ledger-anchor-unreadable') from None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise Denied('ledger-anchor-unreadable')
        data = os.read(fd, MAX_ANCHOR + 1)
    finally:
        os.close(fd)
    match = _ANCHOR.fullmatch(data)
    if match is None:
        raise Denied('ledger-anchor-unreadable')
    return match.group(1).decode('ascii')


def write_anchor(path, ledger_id):
    """Create the anchor durably; never replaces an existing one."""
    temporary = f'{path}.{secrets.token_hex(8)}.tmp'
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, f'GUEST_LEDGER {ledger_id}\n'.encode('ascii'))
        os.fsync(fd)
    finally:
        os.close(fd)
    try:
        os.link(temporary, path)
    except FileExistsError:
        raise Denied('ledger-anchor-conflict') from None
    finally:
        os.unlink(temporary)
    directory = os.open(os.path.dirname(path), os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def read_boot_session(run=subprocess.run):
    """This host's boot session id (macOS kern.bootsessionuuid), or None if unreadable."""
    try:
        result = run([SYSCTL, '-n', 'kern.bootsessionuuid'], capture_output=True,
                     text=True, timeout=5, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip() if isinstance(result.stdout, str) else ''
    return value if result.returncode == 0 and BOOT_SESSION.fullmatch(value) else None


def guest_identity(probe_id, digests):
    """Canonical identity for one planned guest: probe id plus fixed digests."""
    if not isinstance(probe_id, str) or not _PROBE_ID.fullmatch(probe_id):
        raise Denied('invalid-guest-identity')
    if not isinstance(digests, dict) or set(digests) != set(IDENTITY_DIGESTS):
        raise Denied('invalid-guest-identity')
    for name in IDENTITY_DIGESTS:
        if not isinstance(digests[name], str) or not _HEX64.fullmatch(digests[name]):
            raise Denied('invalid-guest-identity')
    return {'probe_id': probe_id, 'share': None, **{k: digests[k] for k in IDENTITY_DIGESTS}}


class GuestRunLedger:
    """Parent-only API. Agents and guests must never reach this object."""

    def __init__(self, lab, anchor=None):
        self.lab = lab
        self.lab.db.execute('''CREATE TABLE IF NOT EXISTS guest_runs (
            run_id TEXT PRIMARY KEY, actor TEXT NOT NULL, epoch INTEGER NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('starting', 'running', 'retired')),
            identity TEXT NOT NULL, channel TEXT, evidence TEXT, host_log TEXT,
            boot_session TEXT)''')
        columns = {row['name'] for row in self.lab.db.execute('PRAGMA table_info(guest_runs)')}
        if 'host_log' not in columns:
            self.lab.db.execute('ALTER TABLE guest_runs ADD COLUMN host_log TEXT')
        if 'boot_session' not in columns:
            self.lab.db.execute('ALTER TABLE guest_runs ADD COLUMN boot_session TEXT')
        self.lab.db.execute('''CREATE TABLE IF NOT EXISTS guest_ledger_anchor (
            singleton INTEGER PRIMARY KEY CHECK(singleton=1), ledger_id TEXT NOT NULL)''')
        if anchor is not None:
            self._check_anchor(anchor)

    def _check_anchor(self, anchor):
        """Open only the ledger the anchor names; the first open writes the anchor first."""
        if (not isinstance(anchor, str) or not os.path.isabs(anchor)
                or os.path.normpath(anchor) != anchor):
            raise Denied('invalid-ledger-anchor')
        with self.lab.transaction():
            recorded = read_anchor(anchor)
            row = self.lab.db.execute('SELECT ledger_id FROM guest_ledger_anchor').fetchone()
            stored = row['ledger_id'] if row is not None else None
            if recorded is None and stored is None:
                ledger_id = secrets.token_hex(16)
                write_anchor(anchor, ledger_id)
                self.lab.db.execute('INSERT INTO guest_ledger_anchor VALUES (1, ?)',
                                    (ledger_id,))
            elif recorded is None:
                raise Denied('ledger-anchor-missing')
            elif stored is None:
                raise Denied('ledger-lost')
            elif recorded != stored:
                raise Denied('ledger-replaced')

    def _row(self, run_id):
        if not isinstance(run_id, str) or not re.fullmatch(r'[0-9a-f]{32}', run_id):
            raise Denied('unknown-guest-run')
        row = self.lab.db.execute('SELECT * FROM guest_runs WHERE run_id=?',
                                  (run_id,)).fetchone()
        if row is None:
            raise Denied('unknown-guest-run')
        return row

    def _unretired(self, actor, except_run=None):
        return self.lab.db.execute(
            "SELECT 1 FROM guest_runs WHERE actor=? AND state!='retired' AND run_id IS NOT ? "
            'LIMIT 1', (actor, except_run)).fetchone() is not None

    def open_run(self, actor, epoch, identity, host_log=None, boot_session=None):
        """Record the run before boot so a crash during start is visible later.

        Only the active epoch (no change pending) or the pending epoch may get
        a guest, and only after every earlier guest of this actor is retired.
        host_log is where the runner's stderr will go; without it a crashed
        run can never be released. boot_session is read_boot_session() taken
        now; without it a run cut off by a host crash can never be released.
        """
        if host_log is not None and (not isinstance(host_log, str)
                                     or not os.path.isabs(host_log)
                                     or os.path.normpath(host_log) != host_log):
            raise Denied('invalid-host-log')
        if boot_session is not None and (not isinstance(boot_session, str)
                                         or not BOOT_SESSION.fullmatch(boot_session)):
            raise Denied('invalid-boot-session')
        canonical = guest_identity(identity.get('probe_id') if isinstance(identity, dict)
                                   else None,
                                   {k: identity.get(k) for k in IDENTITY_DIGESTS}
                                   if isinstance(identity, dict) else None)
        if identity != canonical:
            raise Denied('invalid-guest-identity')
        run_id = secrets.token_hex(16)
        with self.lab.transaction():
            if self.lab.db.execute('SELECT 1 FROM sessions WHERE actor=?',
                                   (actor,)).fetchone() is None:
                raise Denied('unknown-guest-actor')
            state = self.lab.db.execute('SELECT * FROM state').fetchone()
            allowed = state['pending'] if state['pending'] is not None else state['epoch']
            if type(epoch) is not int or epoch != allowed:
                raise Denied('premise-not-current')
            if self._unretired(actor):
                raise Denied('vm-retirement-unconfirmed')
            if self.lab.db.execute('SELECT 1 FROM guest_runs WHERE actor=? AND epoch>=? LIMIT 1',
                                   (actor, epoch)).fetchone():
                raise Denied('vm-run-already-recorded')
            self.lab.db.execute(
                "INSERT INTO guest_runs (run_id, actor, epoch, state, identity, host_log, "
                "boot_session) VALUES (?, ?, ?, 'starting', ?, ?, ?)",
                (run_id, actor, epoch, json.dumps(canonical, sort_keys=True), host_log,
                 boot_session))
        return run_id

    @staticmethod
    def _channel(capability):
        return hashlib.sha256(str(capability).encode('utf-8')).hexdigest()

    def mark_running(self, run_id, start_evidence, capability):
        """Accept host-checked boot evidence and bind the run to one channel."""
        with self.lab.transaction():
            row = self._row(run_id)
            if self.lab.actor(capability) != row['actor']:
                raise Denied('guest-channel-mismatch')
            identity = json.loads(row['identity'])
            if (not isinstance(start_evidence, dict)
                    or start_evidence.get('probe_id') != identity['probe_id']
                    or start_evidence.get('shared_directory') is not False):
                raise Denied('guest-start-unconfirmed')
            updated = self.lab.db.execute(
                "UPDATE guest_runs SET state='running', channel=? "
                "WHERE run_id=? AND state='starting'",
                (self._channel(capability), run_id))
            if updated.rowcount != 1:
                raise Denied('vm-run-not-current')

    def retire(self, run_id, evidence):
        """Persist host-side stop evidence; guest output is not accepted here."""
        with self.lab.transaction():
            row = self._row(run_id)
            identity = json.loads(row['identity'])
            if (not isinstance(evidence, dict)
                    or set(evidence) != {'probe_id', 'stop_marker', 'host_exit'}
                    or evidence['probe_id'] != identity['probe_id']
                    or evidence['stop_marker'] != STOP_MARKER
                    or evidence['host_exit'] != 0 or type(evidence['host_exit']) is not int):
                raise Denied('vm-retirement-unconfirmed')
            updated = self.lab.db.execute(
                "UPDATE guest_runs SET state='retired', evidence=? "
                "WHERE run_id=? AND state IN ('starting', 'running')",
                (json.dumps(evidence, sort_keys=True), run_id))
            if updated.rowcount != 1:
                raise Denied('vm-run-not-current')
            # The retired guest's channel must die with it, not only by convention.
            self.lab.resume(row['actor'])

    def release_crashed(self, run_id, evidence, confirmation):
        """Retire a run whose parent died, from host evidence plus a local confirmation.

        evidence is either the host log recorded before boot, or a host reboot
        (basis 'host-reboot': the boot session recorded before boot and a
        different one now). confirmation must come from
        crash_release.local_confirmation. This object cannot tell a real
        terminal or a real sysctl read from a forged dict, so only the release
        tool may call it.
        """
        with self.lab.transaction():
            row = self._row(run_id)
            identity = json.loads(row['identity'])
            if isinstance(evidence, dict) and evidence.get('basis') == 'host-reboot':
                self._check_reboot(row, identity, evidence)
            else:
                self._check_host_log(row, identity, evidence)
            if (not isinstance(confirmation, dict)
                    or set(confirmation) != {'method', 'run_id', 'tty', 'confirmed_at'}
                    or confirmation['method'] != 'local-terminal'
                    or confirmation['run_id'] != run_id
                    or not isinstance(confirmation['tty'], str)
                    or not confirmation['tty'].startswith('/dev/')
                    or not isinstance(confirmation['confirmed_at'], str)):
                raise Denied('crash-release-not-approved')
            record = {'kind': 'crash-release', 'host': evidence, 'confirmation': confirmation}
            updated = self.lab.db.execute(
                "UPDATE guest_runs SET state='retired', evidence=? "
                "WHERE run_id=? AND state IN ('starting', 'running')",
                (json.dumps(record, sort_keys=True), run_id))
            if updated.rowcount != 1:
                raise Denied('vm-run-not-current')
            self.lab.resume(row['actor'])

    @staticmethod
    def _check_host_log(row, identity, evidence):
        if row['host_log'] is None:
            raise Denied('crash-release-unavailable')
        if (not isinstance(evidence, dict)
                or set(evidence) != {'probe_id', 'stop_marker', 'host_log', 'host_log_sha256'}
                or evidence['probe_id'] != identity['probe_id']
                or evidence['stop_marker'] != STOP_MARKER
                or evidence['host_log'] != row['host_log']
                or not isinstance(evidence['host_log_sha256'], str)
                or not _HEX64.fullmatch(evidence['host_log_sha256'])):
            raise Denied('crash-release-unconfirmed')

    @staticmethod
    def _check_reboot(row, identity, evidence):
        if row['boot_session'] is None:
            raise Denied('crash-release-unavailable')
        if (set(evidence) != {'probe_id', 'basis', 'boot_session_recorded', 'boot_session_now'}
                or evidence['probe_id'] != identity['probe_id']
                or evidence['boot_session_recorded'] != row['boot_session']
                or not isinstance(evidence['boot_session_now'], str)
                or not BOOT_SESSION.fullmatch(evidence['boot_session_now'])
                or evidence['boot_session_now'] == row['boot_session']):
            raise Denied('crash-release-unconfirmed')

    def host_log(self, run_id):
        """The runner log path the parent recorded before boot, or None."""
        return self._row(run_id)['host_log']

    def boot_session(self, run_id):
        """The host boot session id the parent recorded before boot, or None."""
        return self._row(run_id)['boot_session']

    def unretired(self, actor):
        return [run for run in self.runs(actor) if run['state'] != 'retired']

    def require_live(self, run_id, capability, epoch, pending=False):
        """A run may act only on its own channel and epoch while it is the sole live run."""
        actor = self.lab.actor(capability)
        row = self._row(run_id)
        state = self.lab.db.execute('SELECT * FROM state').fetchone()
        current = state['pending'] if pending else state['epoch']
        if (row['actor'] != actor or row['state'] != 'running' or row['epoch'] != epoch
                or row['channel'] != self._channel(capability)
                or epoch != current or (not pending and state['pending'] is not None)
                or self._unretired(actor, except_run=run_id)):
            raise Denied('guest-run-not-live')

    def acknowledge(self, capability, run_id, epoch, change):
        """Application ACK only from the identified live guest of the pending epoch."""
        with self.lab.transaction():
            self.require_live(run_id, capability, epoch, pending=True)
            self.lab.acknowledge(capability, epoch, change, application=True)

    def require_quiescent(self, actor):
        """Restart gate: refuse while any recorded guest lacks durable retirement."""
        if self._unretired(actor):
            raise Denied('vm-retirement-unconfirmed')

    def runs(self, actor):
        return [{'run_id': row['run_id'], 'epoch': row['epoch'], 'state': row['state'],
                 'identity': json.loads(row['identity']),
                 'evidence': json.loads(row['evidence']) if row['evidence'] else None}
                for row in self.lab.db.execute(
                    'SELECT * FROM guest_runs WHERE actor=? ORDER BY epoch', (actor,))]
