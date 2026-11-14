#!/usr/bin/sh
BB=/usr/bin/busybox
# Numbers must be plain decimal integers. The earlier character-class check
# also let through "1-2" (evaluated as an expression), "-" (a shell error that
# ended this script) and "010" (octal); found by the offline tests, 2026-11-10.
is_uint() {
    case "$1" in '' | *[!0123456789]* | 0?*) return 1 ;; esac
    [ "${#1}" -le 6 ]
}
is_int() { is_uint "${1#-}"; }
$BB mount -t proc proc /proc
$BB mount -t sysfs sysfs /sys
$BB mount -t devtmpfs devtmpfs /dev
PROBE_ID=
PROBE_SHARE=1
for arg in $($BB cat /proc/cmdline); do
    case "$arg" in
        probe_id=*) PROBE_ID=${arg#probe_id=} ;;
        probe_share=*) PROBE_SHARE=${arg#probe_share=} ;;
    esac
done
export PROBE_ID
echo GUEST_PROBE_ID=$PROBE_ID >/dev/hvc0
if [ "$PROBE_SHARE" = 1 ]; then
    $BB mkdir -p /mnt/probe
    $BB modprobe virtiofs
    if ! $BB mount -t virtiofs probe /mnt/probe; then
        echo GUEST_MOUNT_FAILED >/dev/hvc0
        while :; do $BB sleep 1; done
    fi
    echo GUEST_MOUNTED >/dev/hvc0
    $BB setsid $BB flock -x /mnt/probe/lock $BB sh -c 'while :; do echo tick >> "/mnt/probe/heartbeat-$PROBE_ID"; /usr/bin/busybox sleep 0.2; done' </dev/null >/dev/hvc0 2>&1 &
    child=$!
    echo GUEST_CHILD_PID=$child >/dev/hvc0
    $BB sleep 1
    if $BB flock -n /mnt/probe/lock $BB true; then echo GUEST_LOCK_NOT_HELD >/dev/hvc0; else echo GUEST_LOCK_HELD >/dev/hvc0; fi
    set -- $($BB cat /proc/$child/stat)
    echo GUEST_CHILD_SESSION=$6 >/dev/hvc0
elif [ "$PROBE_SHARE" = 0 ]; then
    $BB mkdir -p /mnt/probe
    $BB modprobe virtiofs
    if $BB mount -t virtiofs probe /mnt/probe 2>/dev/null; then
        echo GUEST_UNEXPECTED_SHARED_DIRECTORY >/dev/hvc0
        while :; do $BB sleep 1; done
    fi
    echo GUEST_NO_SHARED_DIRECTORY >/dev/hvc0
else
    echo GUEST_INVALID_SHARE_MODE >/dev/hvc0
    while :; do $BB sleep 1; done
fi
if ! exec 3<>/dev/hvc1; then
    echo GUEST_CHANNEL_FAILED >/dev/hvc0
    while :; do $BB sleep 1; done
fi
if ! $BB stty raw -echo <&3; then
    echo GUEST_CHANNEL_TERMIOS_FAILED >/dev/hvc0
    while :; do $BB sleep 1; done
fi
echo GUEST_CHANNEL_READY >/dev/hvc0
if [ "$PROBE_SHARE" = 0 ]; then
    exec /usr/local/bin/v2-managed-worker <&3 >&3
fi
while read -r first second third fourth fifth sixth <&3; do
    if [ "$first" = W ]; then
        request_id=$second; epoch=$third; factor=$fourth; value=$fifth; sequence=$sixth
    else
        request_id=$first; epoch=$second; factor=$third; value=$fourth; sequence=
        if [ -n "$fifth$sixth" ]; then echo GUEST_BAD_REQUEST >/dev/hvc0; continue; fi
    fi
    case "$request_id" in '' | *[!0123456789abcdef]*) echo GUEST_BAD_REQUEST >/dev/hvc0; continue ;; esac
    if ! is_uint "$epoch" || ! is_int "$factor" || ! is_int "$value"; then
        echo GUEST_BAD_REQUEST >/dev/hvc0
        continue
    fi
    if [ "$first" = W ]; then
        if ! is_uint "$sequence"; then echo GUEST_BAD_REQUEST >/dev/hvc0; continue; fi
        echo GUEST_WRITE_REQUEST=$request_id >/dev/hvc0
        $BB printf '%s {"id":%s,"method":"write","resource":"note","base":null,"text":"%s","epoch":%s}\n' \
            "$request_id" "$sequence" "$((factor * value))" "$epoch" >&3
        continue
    fi
    echo GUEST_COMPUTED=$request_id >/dev/hvc0
    $BB printf '%s %s %s\n' "$request_id" "$epoch" "$((factor * value))" >&3
done
echo GUEST_CHANNEL_CLOSED >/dev/hvc0
