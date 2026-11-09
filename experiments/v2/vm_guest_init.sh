#!/usr/bin/sh
BB=/usr/bin/busybox
$BB mount -t proc proc /proc
$BB mount -t sysfs sysfs /sys
$BB mount -t devtmpfs devtmpfs /dev
$BB mkdir -p /mnt/probe
$BB modprobe virtiofs
if ! $BB mount -t virtiofs probe /mnt/probe; then
    echo GUEST_MOUNT_FAILED >/dev/hvc0
    while :; do $BB sleep 1; done
fi
PROBE_ID=
for arg in $($BB cat /proc/cmdline); do
    case "$arg" in probe_id=*) PROBE_ID=${arg#probe_id=} ;; esac
done
export PROBE_ID
echo GUEST_MOUNTED >/dev/hvc0
echo GUEST_PROBE_ID=$PROBE_ID >/dev/hvc0
$BB setsid $BB flock -x /mnt/probe/lock $BB sh -c 'while :; do echo tick >> "/mnt/probe/heartbeat-$PROBE_ID"; /usr/bin/busybox sleep 0.2; done' </dev/null >/dev/hvc0 2>&1 &
child=$!
echo GUEST_CHILD_PID=$child >/dev/hvc0
$BB sleep 1
if $BB flock -n /mnt/probe/lock $BB true; then echo GUEST_LOCK_NOT_HELD >/dev/hvc0; else echo GUEST_LOCK_HELD >/dev/hvc0; fi
set -- $($BB cat /proc/$child/stat)
echo GUEST_CHILD_SESSION=$6 >/dev/hvc0
if ! exec 3<>/dev/hvc1; then
    echo GUEST_CHANNEL_FAILED >/dev/hvc0
    while :; do $BB sleep 1; done
fi
if ! $BB stty raw -echo <&3; then
    echo GUEST_CHANNEL_TERMIOS_FAILED >/dev/hvc0
    while :; do $BB sleep 1; done
fi
echo GUEST_CHANNEL_READY >/dev/hvc0
while read -r request_id epoch factor value <&3; do
    case "$request_id:$epoch:$factor:$value" in
        *[!0123456789abcdef:-]* | *::* | :* | *:) echo GUEST_BAD_REQUEST >/dev/hvc0; continue ;;
    esac
    echo GUEST_COMPUTED=$request_id >/dev/hvc0
    $BB printf '%s %s %s\n' "$request_id" "$epoch" "$((factor * value))" >&3
done
echo GUEST_CHANNEL_CLOSED >/dev/hvc0
