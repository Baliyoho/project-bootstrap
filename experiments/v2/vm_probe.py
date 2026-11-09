"""Mac-only synthetic VM termination probe. No project data enters the guest.

The pinned Alpine netboot images are cached outside the repository. The runner
shares a fresh temporary directory only in legacy heartbeat cases. The managed
tool case has no directory share or network device. This is not P0 acceptance.
"""

from __future__ import annotations

from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import secrets
import select
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen
import zlib


HERE = Path(__file__).resolve().parent
BASE_URL = "https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/aarch64/netboot/"
IMAGES = {
    "vmlinuz-virt": "cd05fed9e617b5df93dc62ece9b78c422fd94e9b432a2f7c092714b139d5eef4",
    "initramfs-virt": "189402937646965374ef2df5d37f76467135179ae168c88175df2fe3e264a0b0",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def image(cache: Path, name: str) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / name
    expected = IMAGES[name]
    if target.exists() and digest(target) == expected:
        return target
    temporary = cache / (name + ".download")
    try:
        with urlopen(BASE_URL + name, timeout=30) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output)
        actual = digest(temporary)
        if actual != expected:
            raise RuntimeError(f"{name} SHA-256 mismatch: {actual}")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def prepare_guest(work: Path, kernel: Path, ramdisk: Path) -> tuple[Path, Path]:
    # Alpine's aarch64 vmlinuz is a gzip-compressed Image wrapped in an EFI stub.
    # VZLinuxBootLoader rejected that wrapper on this host; the raw ARM64 Image boots.
    packed = kernel.read_bytes()
    gzip_offset = packed.find(b"\x1f\x8b\x08")
    if gzip_offset < 0:
        raise RuntimeError("pinned kernel has no gzip payload")
    raw = zlib.decompress(packed[gzip_offset:], wbits=31)
    if raw[56:60] != b"ARMd":
        raise RuntimeError("decompressed kernel is not an ARM64 Image")
    raw_kernel = work / "Image"
    raw_kernel.write_bytes(raw)

    root = work / "rootfs"
    root.mkdir()
    unpack = subprocess.run(
        ["cpio", "-id", "--quiet"], input=gzip.decompress(ramdisk.read_bytes()),
        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    if unpack.stderr:
        raise RuntimeError(f"cpio extraction warning: {unpack.stderr.decode(errors='replace')}")
    init = root / "init"
    init.write_bytes((HERE / "vm_guest_init.sh").read_bytes())
    init.chmod(0o755)
    tool = root / "usr/local/bin/v2-managed-worker"
    tool.parent.mkdir(parents=True, exist_ok=True)
    tool.write_bytes((HERE / "vm_managed_worker.sh").read_bytes())
    tool.chmod(0o755)
    paths = subprocess.check_output(["find", ".", "-print"], cwd=root)
    archive = subprocess.run(
        ["cpio", "-o", "-H", "newc", "--quiet"], input=paths,
        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    if archive.stderr:
        raise RuntimeError(f"cpio archive warning: {archive.stderr.decode(errors='replace')}")
    probe_ramdisk = work / "initramfs-probe.gz"
    probe_ramdisk.write_bytes(gzip.compress(archive.stdout, compresslevel=1))
    return raw_kernel, probe_ramdisk


def build_runner(work: Path) -> Path:
    runner = work / "vm_runner"
    entitlements = work / "entitlements.plist"
    entitlements.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<plist version="1.0"><dict><key>com.apple.security.virtualization</key>'
        '<true/></dict></plist>\n', encoding="utf-8",
    )
    subprocess.run(
        ["xcrun", "swiftc", "-framework", "Virtualization", "-o", str(runner),
         str(HERE / "vm_runner.swift")], check=True,
    )
    subprocess.run(
        ["codesign", "--force", "--sign", "-", "--entitlements", str(entitlements), str(runner)],
        check=True,
    )
    return runner


STOP_MARKER = "HOST_STOPPED state=0"


def host_log(log: Path) -> Path:
    """Runner stderr only. The guest console never reaches this file."""
    return log.with_name(log.name + ".host")


def host_text(log: Path) -> str:
    path = host_log(log)
    return path.read_text(errors="replace") if path.exists() else ""


def host_stopped(log: Path) -> bool:
    return STOP_MARKER in host_text(log).splitlines()


def both_logs(log: Path) -> str:
    guest = log.read_text(errors="replace") if log.exists() else ""
    return f"[host]\n{host_text(log)[-1000:]}\n[guest]\n{guest[-1000:]}"


class _Logs:
    def __init__(self, guest, host):
        self.guest, self.host = guest, host

    def close(self) -> None:
        self.guest.close()
        self.host.close()


def heartbeat_count(share: Path, probe_id: str) -> int:
    heartbeat = share / ("heartbeat-" + probe_id)
    return heartbeat.read_bytes().count(b"tick\n") if heartbeat.exists() else 0


def check_guest(log: Path, share: Path | None, process: subprocess.Popen[bytes], probe_id: str) -> int:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        output = log.read_text(errors="replace")
        if share is None:
            if ("HOST_NO_SHARED_DIRECTORY" in host_text(log).splitlines()
                    and "GUEST_NO_SHARED_DIRECTORY" in output
                    and "GUEST_CHANNEL_READY" in output
                    and f"GUEST_PROBE_ID={probe_id}" in output
                    and "GUEST_MOUNTED" not in output
                    and "GUEST_UNEXPECTED_SHARED_DIRECTORY" not in output):
                return 0
            if process.poll() is not None:
                raise RuntimeError(f"VM exited before unshared guest was ready: {both_logs(log)}")
            time.sleep(0.1)
            continue
        pid = re.search(r"GUEST_CHILD_PID=(\d+)", output)
        session = re.search(r"GUEST_CHILD_SESSION=(\d+)", output)
        if ("GUEST_LOCK_HELD" in output and "GUEST_CHANNEL_READY" in output
                and f"GUEST_PROBE_ID={probe_id}" in output
                and pid and session and heartbeat_count(share, probe_id) >= 3):
            if pid.group(1) != session.group(1):
                raise RuntimeError("guest child did not create its own session")
            first = heartbeat_count(share, probe_id)
            time.sleep(0.6)
            second = heartbeat_count(share, probe_id)
            if second <= first:
                raise RuntimeError("guest heartbeat did not advance while running")
            return second
        if process.poll() is not None:
            raise RuntimeError(f"VM exited before guest was ready: {output[-2000:]}")
        time.sleep(0.1)
    raise RuntimeError(f"guest never became ready: {log.read_text(errors='replace')[-2000:]}")


def stable_after_exit(share: Path, probe_id: str) -> int:
    first = heartbeat_count(share, probe_id)
    time.sleep(1.0)
    second = heartbeat_count(share, probe_id)
    if second != first:
        raise RuntimeError(f"guest effect continued after host exit: {first} -> {second}")
    return second


def launch(runner: Path, kernel: Path, ramdisk: Path, share: Path | None, seconds: int,
           log: Path, probe_id: str) -> tuple[subprocess.Popen[bytes], object, object]:
    output = _Logs(log.open("wb"), host_log(log).open("wb"))
    control_read, control_write = os.pipe()
    request_read, request_write = os.pipe()
    reply_read, reply_write = os.pipe()
    try:
        process = subprocess.Popen(
            [str(runner), str(kernel), str(ramdisk), str(share) if share else "-", str(seconds),
             probe_id, str(control_read), str(request_read), str(reply_write)],
            stdin=subprocess.DEVNULL, stdout=output.guest, stderr=output.host,
            pass_fds=(control_read, request_read, reply_write),
        )
    except BaseException:
        os.close(control_write)
        os.close(request_write)
        os.close(reply_read)
        output.close()
        raise
    finally:
        os.close(control_read)
        os.close(request_read)
        os.close(reply_write)
    process.guest_request = os.fdopen(request_write, "wb", buffering=0)
    process.guest_reply = os.fdopen(reply_read, "rb", buffering=0)
    return process, output, os.fdopen(control_write, "wb", buffering=0)


def close_guest_channel(process: subprocess.Popen[bytes]) -> None:
    process.guest_request.close()
    process.guest_reply.close()


def read_guest_line(process: subprocess.Popen[bytes], limit: int, deadline: float) -> bytes:
    raw = bytearray()
    while b"\n" not in raw:
        if process.poll() is not None:
            raise RuntimeError("VM exited during computation")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError("guest operation timed out")
        if not select.select([process.guest_reply], [], [], min(0.1, remaining))[0]:
            continue
        chunk = os.read(process.guest_reply.fileno(), limit + 1 - len(raw))
        if not chunk:
            raise RuntimeError("guest capability channel closed")
        raw.extend(chunk)
        if len(raw) > limit:
            raise RuntimeError("invalid guest result")
    return bytes(raw)


def read_guest_result(process: subprocess.Popen[bytes], request_id: str,
                      epoch: int, deadline: float) -> int:
    """Read one bounded reply from this VM's private serial port, not virtiofs."""
    raw = read_guest_line(process, 128, deadline)
    if not re.fullmatch(rb"[0-9a-f]{32} [0-9]+ -?[0-9]+\n", raw):
        raise RuntimeError("invalid guest result")
    observed_id, observed_epoch, observed_value = raw.decode("ascii").split()
    if observed_id != request_id or int(observed_epoch) != epoch:
        raise RuntimeError("wrong guest result identity or epoch")
    return int(observed_value)


def read_guest_write_request(process: subprocess.Popen[bytes], request_id: str,
                             epoch: int, sequence: int, deadline: float,
                             expected_base: str | None = None) -> bytes:
    """Bind a fixed guest-originated broker request to this serial exchange."""
    raw = read_guest_line(process, 256, deadline)
    match = re.fullmatch(
        rb'([0-9a-f]{32}) (\{"id":[0-9]+,"method":"write","resource":"note",'
        rb'"base":(?:null|"[0-9a-f]{64}"),"text":"-?[0-9]+","epoch":[0-9]+\})\n', raw)
    if match is None or match[1].decode('ascii') != request_id:
        raise RuntimeError("invalid guest broker request")
    request = json.loads(match[2])
    if (request['id'] != sequence or request['epoch'] != epoch
            or request['base'] != expected_base):
        raise RuntimeError("wrong guest broker request identity or epoch")
    return match[2] + b'\n'


def read_guest_context_ack(process: subprocess.Popen[bytes], request_id: str,
                           epoch: int, factor: int, deadline: float) -> None:
    raw = read_guest_line(process, 128, deadline)
    expected = f"{request_id} {epoch} {factor} READY\n".encode('ascii')
    if raw != expected:
        raise RuntimeError("guest tool did not confirm loaded context")


class VMRetirementGate:
    """One live guest whose verified stop gates a synthetic epoch change.

    The host parent owns this object. If it dies before persisting retirement,
    managed_fixture deliberately cannot reconstruct proof from a stale PID.
    """

    def __init__(self, runner: Path, kernel: Path, ramdisk: Path,
                 share: Path | None, log: Path, probe_id: str, stop_after: int = 0):
        self.runner, self.kernel, self.ramdisk = runner, kernel, ramdisk
        self.share, self.log, self.probe_id = share, log, probe_id
        self.stop_after = stop_after
        self.process = self.output = self.control = None

    def start(self) -> None:
        if self.share is not None:
            self.share.mkdir()
        self.process, self.output, self.control = launch(
            self.runner, self.kernel, self.ramdisk, self.share, self.stop_after,
            self.log, self.probe_id,
        )
        check_guest(self.log, self.share, self.process, self.probe_id)

    def compute(self, epoch: int, factor: int, value: int) -> int:
        """Run one bounded synthetic operation over this guest's serial port."""
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("VM is not live for computation")
        if (type(epoch) is not int or not 0 <= epoch <= 1000
                or any(type(item) is not int or abs(item) > 1000 for item in (factor, value))):
            raise ValueError("invalid guest operation")
        request_id = secrets.token_hex(16)
        try:
            self.process.guest_request.write(
                f"{request_id} {epoch} {factor} {value}\n".encode("ascii"))
        except BrokenPipeError as error:
            raise RuntimeError("guest capability channel closed") from error
        return read_guest_result(self.process, request_id, epoch, time.monotonic() + 8)

    def write_request(self, epoch: int, factor: int, value: int, sequence: int) -> bytes:
        """Ask the guest to create one fixed synthetic broker write request."""
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("VM is not live for computation")
        if (type(sequence) is not int or not 1 <= sequence <= 1000
                or type(epoch) is not int or not 0 <= epoch <= 1000
                or any(type(item) is not int or abs(item) > 1000 for item in (factor, value))):
            raise ValueError("invalid guest operation")
        request_id = secrets.token_hex(16)
        try:
            self.process.guest_request.write(
                f"W {request_id} {epoch} {factor} {value} {sequence}\n".encode("ascii"))
        except BrokenPipeError as error:
            raise RuntimeError("guest capability channel closed") from error
        return read_guest_write_request(
            self.process, request_id, epoch, sequence, time.monotonic() + 8)

    def load_context(self, epoch: int, factor: int) -> None:
        if self.share is not None or self.process is None or self.process.poll() is not None:
            raise RuntimeError("unshared guest tool is not live")
        if (type(epoch) is not int or not 0 <= epoch <= 1000
                or type(factor) is not int or abs(factor) > 1000):
            raise ValueError("invalid guest context")
        request_id = secrets.token_hex(16)
        self.process.guest_request.write(f"L {request_id} {epoch} {factor}\n".encode('ascii'))
        read_guest_context_ack(self.process, request_id, epoch, factor,
                               time.monotonic() + 8)

    def managed_write_request(self, epoch: int, value: int, sequence: int,
                              base: str | None = None) -> bytes:
        if self.share is not None or self.process is None or self.process.poll() is not None:
            raise RuntimeError("unshared guest tool is not live")
        if (type(epoch) is not int or not 0 <= epoch <= 1000
                or type(value) is not int or abs(value) > 1000
                or type(sequence) is not int or not 1 <= sequence <= 1000):
            raise ValueError("invalid guest operation")
        if base is not None and (not isinstance(base, str) or
                                 not re.fullmatch(r'[0-9a-f]{64}', base)):
            raise ValueError("invalid guest base")
        request_id = secrets.token_hex(16)
        self.process.guest_request.write(
            f"W {request_id} {value} {sequence} {base or 'null'}\n".encode('ascii'))
        return read_guest_write_request(self.process, request_id, epoch, sequence,
                                        time.monotonic() + 8, expected_base=base)

    def retire(self) -> dict:
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("VM was not live at retirement")
        self.control.write(b"S")
        self.control.close()
        result = self.process.wait(timeout=15)
        self.output.close()
        close_guest_channel(self.process)
        if result != 0 or not host_stopped(self.log):
            raise RuntimeError(f"VM stop was not confirmed: {both_logs(self.log)}")
        evidence = {"probe_id": self.probe_id, "stop_marker": STOP_MARKER,
                    "host_exit": result}
        if self.share is not None:
            evidence["final_heartbeat"] = stable_after_exit(self.share, self.probe_id)
        return evidence

    def identity(self) -> dict:
        """Digests of the exact files this parent hands to the runner."""
        return {"probe_id": self.probe_id, "share": None,
                "runner": digest(self.runner), "kernel": digest(self.kernel),
                "ramdisk": digest(self.ramdisk),
                "guest_init": digest(HERE / "vm_guest_init.sh"),
                "tool": digest(HERE / "vm_managed_worker.sh")}

    def close(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=15)
        if self.control is not None:
            self.control.close()
        if self.output is not None:
            self.output.close()
        if self.process is not None:
            close_guest_channel(self.process)


def probe(work: Path, runner: Path, kernel: Path, ramdisk: Path) -> None:
    for mode in ("stop", "host_kill"):
        share = work / (mode + "-share")
        share.mkdir()
        log = work / (mode + ".log")
        process, output, control = launch(runner, kernel, ramdisk, share,
                                          5 if mode == "stop" else 0, log, mode)
        try:
            during = check_guest(log, share, process, mode)
            if mode == "host_kill":
                process.kill()
            result = process.wait(timeout=15)
            output.close()
            if mode == "stop" and (result != 0 or not host_stopped(log)):
                raise RuntimeError(f"VM stop failed: {both_logs(log)}")
            if mode == "host_kill" and result != -9:
                raise RuntimeError(f"VM host was not killed: exit {result}")
            after = stable_after_exit(share, mode)
            print(f"{mode}: guest own session and guest lock verified; heartbeat {during}->{after}, stable after exit; host exit {result}")
            if mode == "host_kill":
                restart_log = work / "restart.log"
                restart, restart_output, restart_control = launch(
                    runner, kernel, ramdisk, share, 4, restart_log, "restart")
                try:
                    resumed = check_guest(restart_log, share, restart, "restart")
                    if resumed <= 0 or heartbeat_count(share, mode) != after:
                        raise RuntimeError("replacement VM did not resume guest effects")
                    if restart.wait(timeout=15) != 0:
                        raise RuntimeError(f"replacement VM failed: {restart_log.read_text(errors='replace')[-2000:]}")
                    restart_output.close()
                    stable_after_exit(share, "restart")
                    if heartbeat_count(share, mode) != after:
                        raise RuntimeError("old guest wrote after replacement boot")
                    print(f"restart: new guest heartbeat={resumed}; old guest remained at {after}; stopped cleanly")
                finally:
                    if restart.poll() is None:
                        restart.kill()
                        restart.wait()
                    restart_control.close()
                    close_guest_channel(restart)
                    restart_output.close()
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            control.close()
            close_guest_channel(process)
            output.close()


def probe_cross_vm(work: Path, runner: Path, kernel: Path, ramdisk: Path) -> None:
    """Observe whether a guest flock coordinates two independent VM instances."""
    share = work / "two-vms-share"
    share.mkdir()
    first, first_output, first_control = launch(
        runner, kernel, ramdisk, share, 0, work / "first.log", "first")
    second = None
    second_output = second_control = None
    try:
        check_guest(work / "first.log", share, first, "first")
        second, second_output, second_control = launch(
            runner, kernel, ramdisk, share, 0, work / "second.log", "second")
        try:
            check_guest(work / "second.log", share, second, "second")
            if heartbeat_count(share, "first") < 3:
                raise RuntimeError("first VM stopped writing during overlap")
            print("cross_vm_flock: NOT_COORDINATED; two guests each reported lock held and wrote concurrently")
        except RuntimeError:
            output = (work / "second.log").read_text(errors="replace")
            if "GUEST_LOCK_NOT_HELD" not in output:
                raise
            print("cross_vm_flock: second guest blocked in this run; no general coordination guarantee")
    finally:
        for process, output, control in ((second, second_output, second_control),
                                         (first, first_output, first_control)):
            if process is not None:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=5)
                control.close()
                close_guest_channel(process)
                output.close()


def probe_owner_eof(work: Path, runner: Path, kernel: Path, ramdisk: Path) -> None:
    """Closing the parent's control pipe must retire the VM without a PID signal."""
    share = work / "owner-eof-share"
    share.mkdir()
    log = work / "owner-eof.log"
    process, output, control = launch(runner, kernel, ramdisk, share, 0, log, "owner-eof")
    try:
        check_guest(log, share, process, "owner-eof")
        control.close()
        if process.wait(timeout=15) != 0 or not host_stopped(log):
            raise RuntimeError("VM did not stop after control owner disappeared")
        stable_after_exit(share, "owner-eof")
        print("owner_eof: VM stopped after control pipe closed; heartbeat stable")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        control.close()
        close_guest_channel(process)
        output.close()


CRASH_PARENT = '''from pathlib import Path
import sys
from experiments.v2.managed_fixture import open_managed
from experiments.v2.vm_probe import VMRetirementGate
root, runner, kernel, ramdisk, share, log = map(Path, sys.argv[1:])
with open_managed(root) as (fixture, _):
    fixture.start(2)
    gate = VMRetirementGate(runner, kernel, ramdisk, share, log, 'crash-epoch', stop_after=12)
    fixture.attach_vm_gate(gate)
    print(fixture.handle, flush=True)
    sys.stdin.read()
'''


def probe_parent_crash_fail_closed(work: Path, runner: Path, kernel: Path,
                                   ramdisk: Path) -> None:
    """Kill the trusted parent and reject resume without a durable VM stop."""
    if str(HERE.parents[1]) not in sys.path:
        sys.path.insert(0, str(HERE.parents[1]))
    from experiments.v2.contracts import Denied
    from experiments.v2.managed_fixture import open_managed

    root = work / "crash-managed"
    root.mkdir()
    share = work / "crash-vm-share"
    log = work / "crash-vm.log"
    parent = subprocess.Popen(
        [sys.executable, "-B", "-u", "-c", CRASH_PARENT, str(root), str(runner),
         str(kernel), str(ramdisk), str(share), str(log)],
        cwd=HERE.parents[1], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        if not select.select([parent.stdout], [], [], 20)[0]:
            raise RuntimeError("crash fixture did not start")
        handle = parent.stdout.readline().decode().strip()
        if not re.fullmatch(r"[0-9a-f]{64}", handle):
            raise RuntimeError("crash fixture gave no ticket handle")
        parent.kill()
        parent.wait(timeout=5)
        deadline = time.monotonic() + 8
        while not host_stopped(log):
            if time.monotonic() >= deadline:
                raise RuntimeError("VM did not retire after parent SIGKILL")
            time.sleep(0.05)
        stable_after_exit(share, "crash-epoch")
        with open_managed(root, handle) as (fixture, _):
            deadline = time.monotonic() + 5
            while True:
                try:
                    fixture.resume()
                except Denied as error:
                    if str(error) == "worker-reap-unconfirmed" and time.monotonic() < deadline:
                        time.sleep(0.02)
                        continue
                    if str(error) != "vm-retirement-unconfirmed":
                        raise RuntimeError(f"unexpected resume result: {error}") from error
                    break
                raise RuntimeError("resume accepted a VM with no persisted retirement")
        print("parent_sigkill: guest stopped on control EOF; resume blocked by missing durable VM proof")
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.wait(timeout=5)
        for stream in (parent.stdin, parent.stdout, parent.stderr):
            stream.close()


def probe_managed_switch(work: Path, runner: Path, kernel: Path, ramdisk: Path) -> None:
    """Gate a real managed epoch switch on a live synthetic VM retirement."""
    if str(HERE.parents[1]) not in sys.path:
        sys.path.insert(0, str(HERE.parents[1]))
    from experiments.v2.managed_fixture import open_managed

    root = work / "managed"
    root.mkdir()
    gate = VMRetirementGate(runner, kernel, ramdisk, work / "managed-vm-share",
                            work / "managed-vm.log", "old-epoch")
    with open_managed(root) as (fixture, repo):
        fixture.start(2)
        fixture.attach_vm_gate(gate)
        old_worker = fixture.child
        fixture.begin(5)
        first_id = fixture.stage_result()
        first = fixture.send()
        if (first.get('id') != first_id or first.get('code') != 'ok'
                or (repo / 'managed.txt').read_bytes() != b'10'
                or 'GUEST_COMPUTED=' not in gate.log.read_text(errors='replace')):
            raise RuntimeError("guest computation did not pass through the broker")
        fixture.begin(7)
        stale_id = fixture.stage_result(base=first['digest'])
        interrupted = fixture.begin(8)
        fixture.change(3)
        row = fixture.lab.db.execute(
            'SELECT epoch, state, evidence FROM managed_vm_runs WHERE epoch=0').fetchone()
        evidence = json.loads(row['evidence']) if row['evidence'] else {}
        if (tuple(row[:2]) != (0, 'retired') or evidence.get('stop_marker') != 'HOST_STOPPED state=0'
                or evidence.get('final_heartbeat', 0) < 3
                or not old_worker.reaped or old_worker.process.poll() is None):
            raise RuntimeError("managed VM retirement evidence was not persisted")
        stale = fixture.send()
        old_status = fixture.lab.db.execute(
            'SELECT status FROM operations WHERE ticket=?', (interrupted,)).fetchone()[0]
        if (stale != {'id': stale_id, 'code': 'premise-not-current'}
                or old_status != 'invalid' or (repo / 'managed.txt').read_bytes() != b'10'):
            raise RuntimeError("old epoch effect crossed the managed barrier")
        replacement = VMRetirementGate(
            runner, kernel, ramdisk, work / "replacement-vm-share",
            work / "replacement-vm.log", "new-epoch")
        fixture.attach_vm_gate(replacement)
        fixture.begin(7)
        fresh_id = fixture.stage_result(base=first['digest'])
        fresh = fixture.send()
        if (fresh.get('id') != fresh_id or fresh.get('code') != 'ok'
                or (repo / 'managed.txt').read_bytes() != b'21'
                or 'GUEST_COMPUTED=' not in replacement.log.read_text(errors='replace')):
            raise RuntimeError("fresh epoch effect was not materialized")
        if heartbeat_count(gate.share, gate.probe_id) != evidence['final_heartbeat']:
            raise RuntimeError("old guest wrote after the new epoch was activated")
        fixture.change(4)
        runs = list(fixture.lab.db.execute(
            'SELECT epoch, state, evidence FROM managed_vm_runs ORDER BY epoch'))
        if (len(runs) != 2 or [(row['epoch'], row['state']) for row in runs]
                != [(0, 'retired'), (1, 'retired')]
                or any(not json.loads(row['evidence']).get('stop_marker') for row in runs)):
            raise RuntimeError(f"both guest retirements were not retained: "
                               f"{[(row['epoch'], row['state'], row['evidence']) for row in runs]}")
        print("managed_vm_switch: guest computed in epochs 0 and 1; broker applied "
              "both results; old guest retired before new guest; stale outbox denied")


GUEST_CRASH_PARENT = '''from pathlib import Path
import sys
from experiments.v2.contracts import Lab
from experiments.v2.guest_runs import GuestRunLedger
from experiments.v2.vm_probe import VMRetirementGate
db, runner, kernel, ramdisk, log = map(Path, sys.argv[1:])
lab = Lab(db)
capability = lab.register('guest-crash-parent')
ledger = GuestRunLedger(lab)
gate = VMRetirementGate(runner, kernel, ramdisk, None, log, 'guest-crash', stop_after=12)
run = ledger.open_run('guest-crash-parent', 0, gate.identity())
gate.start()
ledger.mark_running(run, {'probe_id': gate.probe_id, 'shared_directory': False}, capability)
gate.load_context(0, 2)
print(run, flush=True)
sys.stdin.read()
'''


def probe_guest_parent_crash(work: Path, runner: Path, kernel: Path, ramdisk: Path) -> None:
    """SIGKILL the parent of an unshared guest; reopening the ledger must block."""
    if str(HERE.parents[1]) not in sys.path:
        sys.path.insert(0, str(HERE.parents[1]))
    from experiments.v2.contracts import Denied, Lab
    from experiments.v2.guest_runs import GuestRunLedger

    db = work / "guest-crash.sqlite"
    log = work / "guest-crash.log"
    parent = subprocess.Popen(
        [sys.executable, "-B", "-u", "-c", GUEST_CRASH_PARENT, str(db), str(runner),
         str(kernel), str(ramdisk), str(log)],
        cwd=HERE.parents[1], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        if not select.select([parent.stdout], [], [], 25)[0]:
            raise RuntimeError("guest crash fixture did not start: "
                               + parent.stderr.read1(4000).decode(errors="replace"))
        run_id = parent.stdout.readline().decode().strip()
        if not re.fullmatch(r"[0-9a-f]{32}", run_id):
            raise RuntimeError("guest crash fixture gave no run id")
        parent.kill()
        parent.wait(timeout=5)
        deadline = time.monotonic() + 8
        while not host_stopped(log):
            if time.monotonic() >= deadline:
                raise RuntimeError("unshared VM did not stop after parent SIGKILL")
            time.sleep(0.05)
        lab = Lab(db)
        try:
            ledger = GuestRunLedger(lab)
            runs = ledger.runs("guest-crash-parent")
            if [(run["run_id"], run["state"]) for run in runs] != [(run_id, "running")]:
                raise RuntimeError(f"crashed guest run was not durable: {runs}")
            for call in (lambda: ledger.require_quiescent("guest-crash-parent"),
                         lambda: ledger.open_run("guest-crash-parent", 0,
                                                 runs[0]["identity"])):
                try:
                    call()
                except Denied as error:
                    if str(error) != "vm-retirement-unconfirmed":
                        raise RuntimeError(f"unexpected restart result: {error}") from error
                else:
                    raise RuntimeError("restart accepted a guest with no durable retirement")
        finally:
            lab.close()
        print("guest_parent_sigkill: unshared guest stopped on control EOF; reopened "
              "ledger keeps the run unretired and blocks restart")
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.wait(timeout=5)
        for stream in (parent.stdin, parent.stdout, parent.stderr):
            stream.close()


def probe_guest_broker(work: Path, runner: Path, kernel: Path, ramdisk: Path) -> None:
    """Run the synthetic tool inside two unshared guests, not a host worker."""
    if str(HERE.parents[1]) not in sys.path:
        sys.path.insert(0, str(HERE.parents[1]))
    from experiments.v2.broker import Broker
    from experiments.v2.contracts import Denied, Lab, digest as content_digest
    from experiments.v2.guest_runs import GuestRunLedger
    from experiments.v2.launcher import LaunchAuthority, RequestJournal
    from experiments.v2.materializer import Materializer

    def expect_denied(code, call):
        try:
            call()
        except Denied as error:
            if str(error) != code:
                raise RuntimeError(f"expected {code}, got {error}") from error
        else:
            raise RuntimeError(f"ledger accepted a call it must deny ({code})")

    root = work / "guest-broker"
    root.mkdir()
    repo = root / "repo"
    repo.mkdir()
    db = root / "private.sqlite"
    lab = Lab(db)
    old_gate = VMRetirementGate(runner, kernel, ramdisk, None,
                                work / "guest-broker-old.log", "guest-broker-old")
    new_gate = VMRetirementGate(runner, kernel, ramdisk, None,
                                work / "guest-broker-new.log", "guest-broker-new")
    try:
        authority = LaunchAuthority(Broker(lab, Materializer(lab, repo, {'note': 'managed.txt'})))
        ledger = GuestRunLedger(lab)
        ticket = authority.issue(("note",), "synthetic-vm-parent", time.time() + 60)
        old_channel = authority.connect(ticket)
        actor = lab.actor(old_channel.capability)
        old_journal = RequestJournal(authority, old_channel)
        old_run = ledger.open_run(actor, 0, old_gate.identity())
        old_gate.start()
        ledger.mark_running(old_run, {'probe_id': old_gate.probe_id, 'shared_directory': False},
                            old_channel.capability)
        old_gate.load_context(0, 2)
        first_op = lab.begin(old_channel.capability, 0)
        first_raw = old_gate.managed_write_request(0, 5, 1)
        lab.complete(old_channel.capability, first_op)
        ledger.require_live(old_run, old_channel.capability, 0)
        old_journal.prepare_raw(first_raw)
        first = json.loads(old_journal.send())
        recorded = lab.db.execute(
            "SELECT raw, completed FROM client_requests WHERE actor=? AND request_id=1",
            (actor,)).fetchone()
        if (first.get('code') != 'ok' or (repo / 'managed.txt').read_bytes() != b'10'
                or recorded is None or tuple(recorded) != (first_raw, 1)):
            raise RuntimeError('guest tool write was not materialized')
        interrupted = lab.begin(old_channel.capability, 0)
        pending_epoch = lab.propose('{"factor":3}')
        stale_raw = old_gate.managed_write_request(0, 7, 2, first['digest'])
        expect_denied('guest-run-not-live',
                      lambda: ledger.require_live(old_run, old_channel.capability, 0))
        # The broker must refuse on its own as well, so send it anyway.
        old_journal.prepare_raw(stale_raw)
        stale = json.loads(old_journal.send())
        old_status = lab.db.execute('SELECT status FROM operations WHERE ticket=?',
                                    (interrupted,)).fetchone()[0]
        if (stale != {'id': 2, 'code': 'premise-not-current'}
                or old_status != 'invalid' or (repo / 'managed.txt').read_bytes() != b'10'):
            raise RuntimeError('old guest crossed the premise barrier')
        expect_denied('vm-retirement-unconfirmed',
                      lambda: ledger.open_run(actor, pending_epoch, new_gate.identity()))
        ledger.retire(old_run, old_gate.retire())
        late_raw = b'{"id":3,"method":"write","resource":"note","base":null,"text":"99","epoch":0}\n'
        try:
            old_journal.prepare_raw(late_raw)
            old_journal.send()
        except Denied as error:
            if str(error) != 'unknown-session':
                raise RuntimeError(f'retired channel gave {error}') from error
        else:
            raise RuntimeError('retired guest channel still reached the broker')
        if (repo / 'managed.txt').read_bytes() != b'10':
            raise RuntimeError('retired guest channel changed the work tree')
        new_run = ledger.open_run(actor, pending_epoch, new_gate.identity())
        new_gate.start()
        new_channel = authority.connect(ticket)
        ledger.mark_running(new_run, {'probe_id': new_gate.probe_id, 'shared_directory': False},
                            new_channel.capability)
        new_gate.load_context(pending_epoch, 3)
        expect_denied('guest-run-not-live', lambda: ledger.acknowledge(
            new_channel.capability, old_run, pending_epoch, '{"factor":3}'))
        ledger.acknowledge(new_channel.capability, new_run, pending_epoch, '{"factor":3}')
        lab.activate()
        fresh_op = lab.begin(new_channel.capability, pending_epoch)
        fresh_raw = new_gate.managed_write_request(pending_epoch, 7, 3,
                                                    content_digest(b'10'))
        lab.complete(new_channel.capability, fresh_op)
        ledger.require_live(new_run, new_channel.capability, pending_epoch)
        journal = RequestJournal(authority, new_channel)
        journal.prepare_raw(fresh_raw)
        fresh = json.loads(journal.send())
        events = [tuple(row) for row in lab.db.execute(
            'SELECT w.actor, w.after, e.epoch FROM writes w '
            'JOIN write_epochs e USING(event) ORDER BY w.seq')]
        requests = [tuple(row) for row in lab.db.execute(
            'SELECT raw, completed FROM client_requests WHERE actor=? ORDER BY request_id',
            (actor,))]
        if (fresh.get('code') != 'ok' or (repo / 'managed.txt').read_bytes() != b'21'
                or events != [(actor, b'10', 0), (actor, b'21', 1)]
                or requests != [(first_raw, 1), (stale_raw, 1), (fresh_raw, 1)]):
            raise RuntimeError('new guest tool write or attribution failed')
        ledger.retire(new_run, new_gate.retire())
        authority.revoke(ticket)
        lab.close()
        lab = Lab(db)
        reopened = GuestRunLedger(lab)
        reopened.require_quiescent(actor)
        runs = reopened.runs(actor)
        if ([(run['run_id'], run['epoch'], run['state']) for run in runs]
                != [(old_run, 0, 'retired'), (new_run, 1, 'retired')]
                or runs[0]['identity'] != old_gate.identity()
                or runs[1]['identity'] != new_gate.identity()
                or any(run['evidence'] != {'probe_id': run['identity']['probe_id'],
                                           'stop_marker': 'HOST_STOPPED state=0',
                                           'host_exit': 0} for run in runs)):
            raise RuntimeError(f'guest run ledger did not survive reopen: {runs}')
        print('guest_broker: unshared guest tool loaded two epoch contexts; retired channel refused; '
              'old request denied; new scoped write materialized and attributed; '
              'both runs durably retired with identity after reopen')
    finally:
        new_gate.close()
        old_gate.close()
        lab.close()


def main() -> int:
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        print("UNVERIFIED: this probe requires an Apple silicon Mac", file=sys.stderr)
        return 2
    for command in ("xcrun", "codesign", "cpio", "find"):
        if shutil.which(command) is None:
            print(f"UNVERIFIED: missing {command}", file=sys.stderr)
            return 2
    cache = Path(tempfile.gettempdir()) / "project-bootstrap-vm-cache"
    try:
        kernel = image(cache, "vmlinuz-virt")
        ramdisk = image(cache, "initramfs-virt")
        print(f"acquired_at={datetime.now(timezone.utc).isoformat()} host={platform.platform()}")
        print(f"Alpine 3.24.4 aarch64 netboot SHA-256: kernel={digest(kernel)}, initramfs={digest(ramdisk)}")
        print(f"probe SHA-256: runner={digest(HERE / 'vm_runner.swift')}, "
              f"guest_init={digest(HERE / 'vm_guest_init.sh')}, "
              f"managed_tool={digest(HERE / 'vm_managed_worker.sh')}")
        with tempfile.TemporaryDirectory(prefix="project-bootstrap-vm-") as directory:
            work = Path(directory)
            raw_kernel, guest_ramdisk = prepare_guest(work, kernel, ramdisk)
            runner = build_runner(work)
            probe(work, runner, raw_kernel, guest_ramdisk)
            probe_cross_vm(work, runner, raw_kernel, guest_ramdisk)
            probe_owner_eof(work, runner, raw_kernel, guest_ramdisk)
            probe_managed_switch(work, runner, raw_kernel, guest_ramdisk)
            probe_guest_broker(work, runner, raw_kernel, guest_ramdisk)
            probe_parent_crash_fail_closed(work, runner, raw_kernel, guest_ramdisk)
            probe_guest_parent_crash(work, runner, raw_kernel, guest_ramdisk)
        print("VM_PROBE_OK: synthetic guest only; P0 remains unverified")
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError, zlib.error) as error:
        print(f"VM_PROBE_FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
