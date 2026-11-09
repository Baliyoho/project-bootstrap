"""One managed-write preflight over the M3 Git gate and the M1 release gate.

``assess_start`` answers "may this checkout take the claim"; it needs a clean
tree. A write happens after the claim, while work is uncommitted, so it needs
a different question: does the remote still name exactly this session, is the
checkout not behind or diverged, and is the installed package the current
formal release. Each call fetches and asks the channel again; nothing is
cached between writes.

Coordination check only: another writer can still push between this check
and the write. Synthetic fixtures only.
"""
from experiments.v2.contracts import Denied
from experiments.v2.gitclaim import (IDLE, GitGateDenied, _busy_code, _counts, _fetch, _locate,
                                     _out, _remote_owner, owner_parts)


class WriteDenied(Exception):
    """Code is ``<layer>:<code>`` so the report says which gate refused."""


def assess_write(repo, owner, env=None, marker_path='HANDOFF.md'):
    """Facts proving this session still holds the line, or GitGateDenied(code).

    Uncommitted work and local commits not yet pushed are expected here; only
    a remote that moved underneath (behind or diverged) or a marker that no
    longer names this exact session stops the write.
    """
    if not isinstance(owner, str) or len(owner_parts(owner.strip()) or ()) != 3:
        raise GitGateDenied('invalid-owner')
    owner = owner.strip()
    branch, remote, upstream = _locate(repo, env)
    _fetch(repo, env, remote)
    ahead, behind = _counts(repo, env)
    if ahead and behind:
        raise GitGateDenied('diverged')
    if behind:
        raise GitGateDenied('behind-pull-required')
    remote_owner = _remote_owner(repo, env, upstream, marker_path)
    if remote_owner is None:
        raise GitGateDenied('owner-unknown')
    if remote_owner == IDLE:
        raise GitGateDenied('not-claimed')
    if remote_owner != owner:
        raise GitGateDenied(_busy_code(remote_owner, owner))
    return {'branch': branch, 'upstream': upstream,
            'remote_sha': _out(repo, env, 'rev-parse', upstream),
            'head': _out(repo, env, 'rev-parse', 'HEAD')}


class ManagedWrite:
    """``gate`` is a release.WriteGate for the package installed in this checkout."""

    def __init__(self, repo, owner, gate, env=None, marker_path='HANDOFF.md'):
        self.repo, self.owner, self.gate = repo, owner, gate
        self.env, self.marker_path = env, marker_path

    def check(self, operation):
        """Both gates, freshly, for one operation; WriteDenied names the layer.

        Git runs first because it is local and needs no channel round trip; a
        refused claim never spends a release confirmation.
        """
        try:
            facts = assess_write(self.repo, self.owner, env=self.env,
                                 marker_path=self.marker_path)
        except GitGateDenied as error:
            raise WriteDenied('git:' + str(error)) from None
        try:
            confirmed = self.gate.confirm(operation)
        except Denied as error:
            raise WriteDenied('release:' + str(error)) from None
        return {'operation': confirmed['operation'], 'epoch': confirmed['epoch'],
                'manifest': confirmed['manifest'], 'branch': facts['branch'],
                'remote_sha': facts['remote_sha'], 'head': facts['head']}
