"""P0 transactional model, using synthetic content only.

The administrator and agent APIs intentionally share one Python process for
contract testing. They are NOT an OS security boundary or real identity proof.
Do not put real credentials/content here or expose this object to agents.
"""
import hashlib
import secrets
import sqlite3
import time
import math
from contextlib import contextmanager
from datetime import datetime, timezone


class Denied(Exception):
    """Safe fixed-code rejection; no submitted content in the message."""


def digest(content):
    return hashlib.sha256(content).hexdigest()


class Lab:
    def __init__(self, path, clock=None, authority_clock=None):
        self.clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
        self.authority_clock = authority_clock or time.time
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS sessions (
                capability TEXT PRIMARY KEY, actor TEXT NOT NULL UNIQUE);
            CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, content BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS writes (
                seq INTEGER PRIMARY KEY, event TEXT NOT NULL UNIQUE,
                actor TEXT NOT NULL, at TEXT NOT NULL, path TEXT NOT NULL,
                before BLOB, after BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS state (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                epoch INTEGER NOT NULL, pending INTEGER, change TEXT);
            INSERT OR IGNORE INTO state VALUES (1, 0, NULL, NULL);
            CREATE TABLE IF NOT EXISTS notices (
                actor TEXT, epoch INTEGER, change TEXT NOT NULL, acknowledged INTEGER NOT NULL,
                PRIMARY KEY(actor, epoch));
            CREATE TABLE IF NOT EXISTS operations (
                ticket TEXT PRIMARY KEY, actor TEXT NOT NULL,
                epoch INTEGER NOT NULL, status TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS grants (
                id TEXT PRIMARY KEY, actor TEXT NOT NULL, kind TEXT NOT NULL,
                resource TEXT NOT NULL, remaining INTEGER NOT NULL,
                source TEXT NOT NULL, revoked INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS effects (
                seq INTEGER PRIMARY KEY, actor TEXT, kind TEXT, resource TEXT, grant_id TEXT);
            CREATE TABLE IF NOT EXISTS receipts (
                actor TEXT, request_id INTEGER, digest TEXT NOT NULL, response BLOB NOT NULL,
                PRIMARY KEY(actor, request_id));
            CREATE TABLE IF NOT EXISTS write_epochs (event TEXT PRIMARY KEY, epoch INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS grant_deadlines (
                grant_id TEXT PRIMARY KEY, issued REAL NOT NULL, expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS signed_effect_policy (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1), audience TEXT NOT NULL,
                signer_digest TEXT NOT NULL, verifier_digest TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS signed_effect_approvals (
                id TEXT PRIMARY KEY, document BLOB NOT NULL, signature BLOB NOT NULL,
                grant_id TEXT NOT NULL UNIQUE, epoch INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS authority_time (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1), latest REAL NOT NULL);
        ''')

    @contextmanager
    def transaction(self):
        """Nest mutations without committing an enclosing request receipt early."""
        nested = self.db.in_transaction
        savepoint = 'sp_' + secrets.token_hex(8)
        self.db.execute('SAVEPOINT ' + savepoint if nested else 'BEGIN IMMEDIATE')
        try:
            yield
        except BaseException:
            if nested:
                self.db.execute('ROLLBACK TO ' + savepoint)
                self.db.execute('RELEASE ' + savepoint)
            else:
                self.db.rollback()
            raise
        else:
            try:
                if nested:
                    self.db.execute('RELEASE ' + savepoint)
                else:
                    self.db.commit()
            except BaseException:
                if nested:
                    self.db.execute('ROLLBACK TO ' + savepoint)
                    self.db.execute('RELEASE ' + savepoint)
                else:
                    self.db.rollback()
                raise

    def close(self):
        self.db.close()

    def authority_now(self):
        """Trusted wall clock; reject rollback below a committed watermark.

        Call within a transaction. This is not a trusted hardware clock: an
        unobserved/rolled-back clock check or restored DB needs external recovery.
        """
        now = self.authority_clock()
        latest = self.db.execute('SELECT latest FROM authority_time').fetchone()
        if (type(now) not in (int, float) or not math.isfinite(now)
                or (latest is not None and now < latest[0])):
            raise Denied('invalid-authority-clock')
        self.db.execute('INSERT OR REPLACE INTO authority_time VALUES (1, ?)', (now,))
        return now

    def register(self, actor):
        """Trusted launcher stand-in; never an agent-supplied actor parameter."""
        capability = secrets.token_hex(32)
        with self.transaction():
            self.db.execute('INSERT INTO sessions VALUES (?, ?)', (capability, actor))
            state = self.db.execute('SELECT * FROM state').fetchone()
            if state['pending'] is not None:
                self.db.execute('INSERT INTO notices VALUES (?, ?, ?, 0)',
                                (actor, state['pending'], state['change']))
        return capability

    def resume(self, actor):
        """Trusted launcher only: rotate capability; retain actor-scoped receipts."""
        capability = secrets.token_hex(32)
        with self.transaction():
            changed = self.db.execute('UPDATE sessions SET capability=? WHERE actor=?', (capability, actor))
            if changed.rowcount != 1:
                raise Denied('unknown-resume-principal')
        return capability

    def actor(self, capability):
        row = self.db.execute('SELECT actor FROM sessions WHERE capability=?',
                              (capability,)).fetchone()
        if row is None:
            raise Denied('unknown-session')
        return row['actor']

    def require_epoch(self, epoch):
        """Call inside the mutation transaction, never before BEGIN IMMEDIATE."""
        state = self.db.execute('SELECT epoch, pending FROM state').fetchone()
        if type(epoch) is not int or epoch != state['epoch'] or state['pending'] is not None:
            raise Denied('premise-not-current')

    def write(self, capability, path, expected, content, epoch=None):
        """Journal and content commit together; concurrent stale bases are rejected.

        This is the broker-owned content store. The optional materializer tracks
        disk application separately; accepting this event is not a disk receipt.
        """
        actor = self.actor(capability)
        if not isinstance(content, bytes):
            raise Denied('bytes-required')
        event = secrets.token_hex(16)
        with self.transaction():
            if epoch is not None:
                self.require_epoch(epoch)
            row = self.db.execute('SELECT content FROM files WHERE path=?', (path,)).fetchone()
            before = None if row is None else row['content']
            if expected != (None if before is None else digest(before)):
                raise Denied('stale-base')
            self.db.execute('INSERT INTO writes(event, actor, at, path, before, after) '
                            'VALUES (?, ?, ?, ?, ?, ?)',
                            (event, actor, self.clock(), path, before, content))
            self.db.execute('INSERT OR REPLACE INTO files VALUES (?, ?)', (path, content))
            current = self.db.execute('SELECT epoch FROM state').fetchone()[0]
            self.db.execute('INSERT INTO write_epochs VALUES (?, ?)', (event, current))
        return event

    def event(self, event_id):
        row = self.db.execute('SELECT * FROM writes WHERE event=?', (event_id,)).fetchone()
        return None if row is None else dict(row)

    def begin(self, capability, epoch):
        actor = self.actor(capability)
        ticket = secrets.token_hex(16)
        with self.transaction():
            state = self.db.execute('SELECT * FROM state').fetchone()
            if state['pending'] is not None or epoch != state['epoch']:
                raise Denied('premise-not-current')
            self.db.execute('INSERT INTO operations VALUES (?, ?, ?, ?)',
                            (ticket, actor, epoch, 'running'))
        return ticket

    def propose(self, change):
        """Persist the notification and invalidate work in one transaction.

        All registered sessions are recipients, including unknown dependencies.
        The durable inbox is not a push transport or a model context reset.
        """
        with self.transaction():
            state = self.db.execute('SELECT * FROM state').fetchone()
            if state['pending'] is not None:
                raise Denied('change-already-pending')
            pending = state['epoch'] + 1
            self.db.execute('UPDATE state SET pending=?, change=?', (pending, change))
            self.db.execute('INSERT INTO notices SELECT actor, ?, ?, 0 FROM sessions',
                            (pending, change))
            self.db.execute("UPDATE operations SET status='invalid' WHERE status='running'")
        return pending

    def inbox(self, capability):
        actor = self.actor(capability)
        return [dict(row) for row in self.db.execute(
            'SELECT epoch, change, acknowledged FROM notices WHERE actor=? ORDER BY epoch',
            (actor,))]

    def acknowledge(self, capability, epoch, change, application=False):
        actor = self.actor(capability)
        if application is not True:
            raise Denied('transport-ack-is-not-application-ack')
        with self.transaction():
            row = self.db.execute('SELECT change FROM notices WHERE actor=? AND epoch=?',
                                  (actor, epoch)).fetchone()
            if row is None or row['change'] != change:
                raise Denied('wrong-notice')
            self.db.execute('UPDATE notices SET acknowledged=1 WHERE actor=? AND epoch=?',
                            (actor, epoch))

    def activate(self):
        with self.transaction():
            state = self.db.execute('SELECT * FROM state').fetchone()
            if state['pending'] is None:
                raise Denied('no-pending-change')
            if self.db.execute('SELECT 1 FROM notices WHERE epoch=? AND acknowledged=0',
                               (state['pending'],)).fetchone():
                raise Denied('unacknowledged-line')
            self.db.execute('UPDATE state SET epoch=pending, pending=NULL, change=NULL')

    def complete(self, capability, ticket):
        actor = self.actor(capability)
        with self.transaction():
            op = self.db.execute('SELECT * FROM operations WHERE ticket=?', (ticket,)).fetchone()
            state = self.db.execute('SELECT * FROM state').fetchone()
            if (op is None or op['actor'] != actor or op['status'] != 'running'
                    or state['pending'] is not None or op['epoch'] != state['epoch']):
                raise Denied('invalid-operation')
            self.db.execute("UPDATE operations SET status='completed' WHERE ticket=?", (ticket,))

    def grant(self, actor, kind, resource, uses, source, expires_at=None):
        """Human authorization stand-in; outside the agent API in a real broker."""
        if type(uses) is not int or uses < 1 or not source:
            raise Denied('invalid-grant')
        grant_id = secrets.token_hex(16)
        with self.transaction():
            now = self.authority_now()
            if expires_at is not None and (type(expires_at) not in (int, float)
                    or not math.isfinite(expires_at) or not math.isfinite(now) or expires_at <= now):
                raise Denied('invalid-grant-deadline')
            self.db.execute('INSERT INTO grants VALUES (?, ?, ?, ?, ?, ?, 0)',
                            (grant_id, actor, kind, resource, uses, source))
            if expires_at is not None:
                self.db.execute('INSERT INTO grant_deadlines VALUES (?, ?, ?)',
                                (grant_id, now, expires_at))
        return grant_id

    def revoke(self, grant_id):
        with self.transaction():
            self.db.execute('UPDATE grants SET revoked=1 WHERE id=?', (grant_id,))

    def effect(self, capability, kind, resource, epoch=None):
        """Record a synthetic effect only; no paid or destructive action executes."""
        actor = self.actor(capability)
        with self.transaction():
            if epoch is not None:
                self.require_epoch(epoch)
            now = self.authority_now()
            grant = self.db.execute('SELECT g.* FROM grants g LEFT JOIN grant_deadlines d '
                'ON d.grant_id=g.id LEFT JOIN signed_effect_approvals a ON a.grant_id=g.id '
                'LEFT JOIN signed_effect_policy p ON p.singleton=1 CROSS JOIN state s '
                'WHERE actor=? AND kind=? '
                'AND resource=? AND revoked=0 AND remaining>0 '
                'AND ((p.singleton IS NULL AND a.grant_id IS NULL) '
                'OR (p.singleton=1 AND s.pending IS NULL AND a.epoch=s.epoch)) '
                'AND (d.grant_id IS NULL OR (d.issued<=? AND ?<d.expires)) ORDER BY g.id LIMIT 1',
                (actor, kind, resource, now, now)).fetchone()
            if grant is None:
                raise Denied('not-authorized')
            self.db.execute('UPDATE grants SET remaining=remaining-1 WHERE id=?', (grant['id'],))
            self.db.execute('INSERT INTO effects(actor, kind, resource, grant_id) VALUES (?, ?, ?, ?)',
                            (actor, kind, resource, grant['id']))


def scan_snapshot(files, message, forbidden):
    """Freeze and scan ALL candidates before any caller writes Git objects.

    This is a known-value fixture scanner, not Gitleaks or a semantic detector.
    Returns immutable bytes; the caller must never reopen mutable source files.
    """
    if not forbidden or any(not isinstance(value, bytes) or not value for value in forbidden):
        raise Denied('missing-scanner-policy')
    snapshot = tuple((name, bytes(content)) for name, content in sorted(files.items()))
    for name, content in snapshot:
        if not name or name.startswith('/') or '..' in name.split('/') or '\\' in name:
            raise Denied('invalid-path')
        if any(value in name.encode('utf-8') or value in content for value in forbidden):
            raise Denied('sensitive-candidate')
    if any(value in message.encode('utf-8') for value in forbidden):
        raise Denied('sensitive-message')
    return snapshot


def mask_summary(content, forbidden, limit):
    for value in sorted(forbidden, key=len, reverse=True):
        content = content.replace(value, b'***')
    return content[:limit]
