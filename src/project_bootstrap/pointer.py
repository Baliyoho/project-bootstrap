"""P2 slice 2: the project pointer and the per-write check over a package (D3／D4／D5, F18／F32／F33).

A project keeps a pointer, not a copy of the system. ``.bootstrap/pointer.json``
names the channel and the digest of the installed package; the package itself
lives in a cache folder outside the project, one folder per manifest digest,
as built by ``package.py``.

``WriteCheck.confirm`` runs before every managed write and caches nothing:

1. read the pointer again (an edited pointer takes effect at once);
2. take the installed package from the cache and check it against its
   manifest; the manifest digest must equal the pointer, and it must be formal;
3. ask the channel for a statement signed over a fresh nonce (unreachable,
   replayed, expired, wrong channel, rolled back or unsigned all refuse);
4. if the channel's current package is not the installed one, refuse, unless
   the pointer declares a D4 exception that pins the installed package, has
   not passed its review date and covers the path being written;
5. compare the project's copies of the whole core／adapter files with the
   manifest. Project-owned files (AGENTS.md, HANDOFF.md, ...) are not
   compared, so a project editing its own files is never refused for it.

``status`` is the read-only view: it reports the installed version and digest
without asking the channel, and says the freshness is unconfirmed (D5: reads
go on, with the limit stated).

Prototype limits: the signer and key are test stand-ins until slice 3; the
highest seen epoch is kept per ``WriteCheck`` object, not on disk; the
``region``／``wiring``／``key`` parts of mixed files are not compared yet; who
declared an exception is a recorded name, not a verified identity.
"""
import hashlib
import json
from pathlib import Path
import re
import secrets
import time

from project_bootstrap import package
from project_bootstrap.broker import Broker
from project_bootstrap.contracts import Denied
from project_bootstrap.release import STATEMENT_FIELDS, WriteGate

POINTER = '.bootstrap/pointer.json'
FIELDS = {'schema', 'channel', 'installed', 'exception'}
EXCEPTION_FIELDS = {'pin', 'paths', 'reason', 'declared_by', 'review_by'}
DIGEST_RE = re.compile(r'[0-9a-f]{64}')
CHANNEL_RE = re.compile(r'[a-z][a-z0-9-]{0,31}')
DATE_RE = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}')


def _relative(path):
    if (not isinstance(path, str) or not path or '\\' in path
            or any(part in ('', '.', '..') for part in path.split('/'))):
        return False
    return True


def parse(text):
    """Pointer text to a dict, or Denied('invalid-pointer…')."""
    try:
        data = json.loads(text, object_pairs_hook=Broker.unique_keys)
    except (ValueError, RecursionError):
        raise Denied('invalid-pointer') from None
    if not isinstance(data, dict) or set(data) != FIELDS or data['schema'] != 1:
        raise Denied('invalid-pointer')
    if not isinstance(data['channel'], str) or not CHANNEL_RE.fullmatch(data['channel']):
        raise Denied('invalid-pointer:channel')
    if not isinstance(data['installed'], str) or not DIGEST_RE.fullmatch(data['installed']):
        raise Denied('invalid-pointer:installed')
    exception = data['exception']
    if exception is not None:
        if not isinstance(exception, dict) or set(exception) != EXCEPTION_FIELDS:
            raise Denied('invalid-pointer:exception')
        if exception['pin'] != data['installed']:
            raise Denied('invalid-pointer:pin')
        paths = exception['paths']
        if not isinstance(paths, list) or not paths or not all(_relative(p) for p in paths):
            raise Denied('invalid-pointer:paths')
        for key in ('reason', 'declared_by'):
            if not isinstance(exception[key], str) or not exception[key].strip():
                raise Denied('invalid-pointer:' + key)
        if not isinstance(exception['review_by'], str) or not DATE_RE.fullmatch(exception['review_by']):
            raise Denied('invalid-pointer:review_by')
    return data


def _covers(paths, target):
    return any(target == p or target.startswith(p + '/') for p in paths)


def _today(now):
    return time.strftime('%Y-%m-%d', time.gmtime(now))


class WriteCheck:
    """``fetch(nonce)`` returns (statement bytes, signature bytes) from the trusted channel."""

    def __init__(self, project, cache, public_key, fetch, clock=time.time):
        self.project, self.cache = Path(project), Path(cache)
        # WriteGate validates the key and holds the one signature verifier we use.
        self.verifier = WriteGate(public_key, '', self.project, {}, fetch)
        self.fetch, self.clock = fetch, clock
        self.highest_epoch = -1

    def _pointer(self):
        try:
            text = (self.project / POINTER).read_text(encoding='utf-8')
        except FileNotFoundError:
            raise Denied('no-pointer') from None
        except (OSError, UnicodeDecodeError):
            raise Denied('invalid-pointer') from None
        return parse(text)

    def _installed(self, digest):
        folder = self.cache / digest
        if not (folder / package.MANIFEST).is_file():
            raise Denied('package-not-cached')
        problems = package.check(folder)
        if problems:
            raise Denied('package-damaged:' + ','.join(problems))
        manifest = json.loads((folder / package.MANIFEST).read_text(encoding='utf-8'))
        if package.digest(manifest) != digest:
            raise Denied('package-mismatch')
        return manifest

    def _statement(self, channel):
        nonce = secrets.token_hex(16)
        try:
            document, signature = self.fetch(nonce)
        except Exception:
            raise Denied('channel-unreachable') from None
        if not isinstance(document, bytes) or not 1 <= len(document) <= 1024:
            raise Denied('invalid-channel-statement')
        self.verifier._verify(document, signature)
        try:
            fields = json.loads(document.decode('ascii'), object_pairs_hook=Broker.unique_keys)
        except (ValueError, RecursionError, UnicodeDecodeError):
            raise Denied('invalid-channel-statement') from None
        if (not isinstance(fields, dict) or set(fields) != STATEMENT_FIELDS
                or any(type(fields[key]) is not int for key in ('epoch', 'issued', 'expires'))
                or not isinstance(fields['manifest'], str)):
            raise Denied('invalid-channel-statement')
        if fields['channel'] != channel:
            raise Denied('wrong-channel')
        if fields['nonce'] != nonce:
            raise Denied('stale-confirmation')
        now = self.clock()
        if not fields['issued'] <= now < fields['expires']:
            raise Denied('stale-confirmation')
        if fields['epoch'] < self.highest_epoch:
            raise Denied('channel-rollback')
        return fields, now

    def confirm(self, operation, target):
        """Fresh check for writing ``target`` (a project-relative path); Denied otherwise."""
        if not isinstance(operation, str) or not re.fullmatch(r'[0-9a-f]{32}', operation):
            raise Denied('invalid-operation')
        if not _relative(target):
            raise Denied('invalid-target')
        pointer = self._pointer()
        installed = pointer['installed']
        manifest = self._installed(installed)
        if manifest.get('kind') != 'formal':
            raise Denied('debug-release')
        fields, now = self._statement(pointer['channel'])
        latest = fields['manifest']
        pinned = False
        if latest != installed:
            exception = pointer['exception']
            if exception is None:
                raise Denied('release-mismatch')
            if _today(now) > exception['review_by']:
                raise Denied('exception-expired')
            if not _covers(exception['paths'], target):
                raise Denied('exception-out-of-scope')
            pinned = True
        for path in sorted(package.whole_owned(manifest)):
            try:
                data = (self.project / path).read_bytes()
            except FileNotFoundError:
                raise Denied('component-missing:' + path) from None
            except OSError:
                raise Denied('component-unreadable:' + path) from None
            if hashlib.sha256(data).hexdigest() != manifest['components'][path]:
                raise Denied('component-drift:' + path)
        self.highest_epoch = fields['epoch']
        return {'operation': operation, 'target': target, 'epoch': fields['epoch'],
                'version': manifest['version'], 'installed': installed, 'latest': latest,
                'pinned': pinned}


def status(project, cache):
    """Read-only report; never asks the channel, so freshness is always unconfirmed."""
    project, cache = Path(project), Path(cache)
    try:
        pointer = parse((project / POINTER).read_text(encoding='utf-8'))
    except FileNotFoundError:
        return {'state': 'no-pointer', 'fresh': 'unconfirmed'}
    except (OSError, UnicodeDecodeError, Denied) as error:
        return {'state': 'invalid-pointer', 'detail': str(error), 'fresh': 'unconfirmed'}
    report = {'state': 'ok', 'channel': pointer['channel'], 'installed': pointer['installed'],
              'exception': pointer['exception'], 'fresh': 'unconfirmed'}
    folder = cache / pointer['installed']
    try:
        manifest = json.loads((folder / package.MANIFEST).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        report['state'] = 'package-not-cached'
        return report
    if package.check(folder) or package.digest(manifest) != pointer['installed']:
        report['state'] = 'package-damaged'
        return report
    report['version'], report['kind'] = manifest['version'], manifest['kind']
    return report
