"""Mac-only synthetic VM termination probe. No project data enters the guest.

The pinned Alpine netboot images are cached outside the repository. The runner
shares only a fresh temporary directory with the guest and configures no network
device. This is an experiment, not a general-purpose sandbox or P0 acceptance.
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


def heartbeat_count(share: Path, probe_id: str) -> int:
    heartbeat = share / ("heartbeat-" + probe_id)
    return heartbeat.read_bytes().count(b"tick\n") if heartbeat.exists() else 0


def check_guest(log: Path, share: Path, process: subprocess.Popen[bytes], probe_id: str) -> int:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        output = log.read_text(errors="replace")
        pid = re.search(r"GUEST_CHILD_PID=(\d+)", output)
        session = re.search(r"GUEST_CHILD_SESSION=(\d+)", output)
        if ("GUEST_LOCK_HELD" in output and f"GUEST_PROBE_ID={probe_id}" in output
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


def launch(runner: Path, kernel: Path, ramdisk: Path, share: Path, seconds: int,
           log: Path, probe_id: str) -> tuple[subprocess.Popen[bytes], object, object]:
    output = log.open("wb")
    control_read, control_write = os.pipe()
    try:
        process = subprocess.Popen(
            [str(runner), str(kernel), str(ramdisk), str(share), str(seconds),
             probe_id, str(control_read)],
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
            pass_fds=(control_read,),
        )
    except BaseException:
        os.close(control_write)
        output.close()
        raise
    finally:
        os.close(control_read)
    return process, output, os.fdopen(control_write, "wb", buffering=0)


class VMRetirementGate:
    """One live guest whose verified stop gates a synthetic epoch change.

    The host parent owns this object. If it dies before persisting retirement,
    managed_fixture deliberately cannot reconstruct proof from a stale PID.
    """

    def __init__(self, runner: Path, kernel: Path, ramdisk: Path,
                 share: Path, log: Path, probe_id: str, stop_after: int = 0):
        self.runner, self.kernel, self.ramdisk = runner, kernel, ramdisk
        self.share, self.log, self.probe_id = share, log, probe_id
        self.stop_after = stop_after
        self.process = self.output = self.control = None

    def start(self) -> None:
        self.share.mkdir()
        self.process, self.output, self.control = launch(
            self.runner, self.kernel, self.ramdisk, self.share, self.stop_after,
            self.log, self.probe_id,
        )
        check_guest(self.log, self.share, self.process, self.probe_id)

    def retire(self) -> dict:
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("VM was not live at retirement")
        self.control.write(b"S")
        self.control.close()
        result = self.process.wait(timeout=15)
        self.output.close()
        output = self.log.read_text(errors="replace")
        if result != 0 or "HOST_STOPPED state=0" not in output:
            raise RuntimeError(f"VM stop was not confirmed: {output[-2000:]}")
        final = stable_after_exit(self.share, self.probe_id)
        return {"probe_id": self.probe_id, "final_heartbeat": final,
                "stop_marker": "HOST_STOPPED state=0"}

    def close(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=15)
        if self.control is not None:
            self.control.close()
        if self.output is not None:
            self.output.close()


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
            if mode == "stop" and (result != 0 or "HOST_STOPPED state=0" not in log.read_text(errors="replace")):
                raise RuntimeError(f"VM stop failed: {log.read_text(errors='replace')[-2000:]}")
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
                    restart_output.close()
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            control.close()
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
        if process.wait(timeout=15) != 0 or "HOST_STOPPED state=0" not in log.read_text(errors="replace"):
            raise RuntimeError("VM did not stop after control owner disappeared")
        stable_after_exit(share, "owner-eof")
        print("owner_eof: VM stopped after control pipe closed; heartbeat stable")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        control.close()
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
        while "HOST_STOPPED state=0" not in log.read_text(errors="replace"):
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
        fixture.begin(7)
        stale_id = fixture.stage_result()
        interrupted = fixture.begin(8)
        fixture.change(3)
        row = fixture.lab.db.execute(
            'SELECT epoch, state, evidence FROM managed_vm_runs').fetchone()
        evidence = json.loads(row['evidence']) if row['evidence'] else {}
        if (tuple(row[:2]) != (0, 'retired') or evidence.get('stop_marker') != 'HOST_STOPPED state=0'
                or evidence.get('final_heartbeat', 0) < 3
                or not old_worker.reaped or old_worker.process.poll() is None):
            raise RuntimeError("managed VM retirement evidence was not persisted")
        stale = fixture.send()
        old_status = fixture.lab.db.execute(
            'SELECT status FROM operations WHERE ticket=?', (interrupted,)).fetchone()[0]
        if (stale != {'id': stale_id, 'code': 'premise-not-current'}
                or old_status != 'invalid' or (repo / 'managed.txt').exists()):
            raise RuntimeError("old epoch effect crossed the managed barrier")
        fixture.begin(7)
        fresh_id = fixture.stage_result()
        fresh = fixture.send()
        if (fresh.get('id') != fresh_id or fresh.get('code') != 'ok'
                or (repo / 'managed.txt').read_bytes() != b'21'):
            raise RuntimeError("fresh epoch effect was not materialized")
        if heartbeat_count(gate.share, gate.probe_id) != evidence['final_heartbeat']:
            raise RuntimeError("old guest wrote after the new epoch was activated")
        print("managed_vm_switch: old guest stop persisted before epoch 1; "
              "old outbox denied; only epoch 1 content materialized")


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
        print(f"probe SHA-256: runner={digest(HERE / 'vm_runner.swift')}, guest_init={digest(HERE / 'vm_guest_init.sh')}")
        with tempfile.TemporaryDirectory(prefix="project-bootstrap-vm-") as directory:
            work = Path(directory)
            raw_kernel, guest_ramdisk = prepare_guest(work, kernel, ramdisk)
            runner = build_runner(work)
            probe(work, runner, raw_kernel, guest_ramdisk)
            probe_cross_vm(work, runner, raw_kernel, guest_ramdisk)
            probe_owner_eof(work, runner, raw_kernel, guest_ramdisk)
            probe_managed_switch(work, runner, raw_kernel, guest_ramdisk)
            probe_parent_crash_fail_closed(work, runner, raw_kernel, guest_ramdisk)
        print("VM_PROBE_OK: synthetic guest only; P0 remains unverified")
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError, zlib.error) as error:
        print(f"VM_PROBE_FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
