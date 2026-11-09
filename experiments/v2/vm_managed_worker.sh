#!/usr/bin/sh
# Synthetic managed tool. It owns its loaded premise for one VM lifetime.
# The host sends only a value and sequence after loading the context.
BB=/usr/bin/busybox
loaded=0
while read -r opcode nonce first second extra; do
    case "$nonce" in
        '' | *[!0123456789abcdef]*) echo GUEST_TOOL_BAD_NONCE >/dev/hvc0; continue ;;
    esac
    if [ "${#nonce}" -ne 32 ]; then
        echo GUEST_TOOL_BAD_REQUEST >/dev/hvc0
        continue
    fi
    case "$opcode" in
        L)
            if [ -n "$extra" ]; then echo GUEST_TOOL_BAD_CONTEXT >/dev/hvc0; continue; fi
            if [ "$loaded" -ne 0 ]; then echo GUEST_TOOL_ALREADY_LOADED >/dev/hvc0; continue; fi
            case "$first:$second" in *[!0123456789:-]* | *::* | :* | *:) echo GUEST_TOOL_BAD_CONTEXT >/dev/hvc0; continue ;; esac
            epoch=$first
            factor=$second
            loaded=1
            $BB printf '%s %s %s READY\n' "$nonce" "$epoch" "$factor"
            ;;
        W)
            if [ "$loaded" -ne 1 ]; then echo GUEST_TOOL_NOT_LOADED >/dev/hvc0; continue; fi
            case "$first:$second" in *[!0123456789:-]* | *::* | :* | *:) echo GUEST_TOOL_BAD_REQUEST >/dev/hvc0; continue ;; esac
            value=$first
            sequence=$second
            case "$extra" in
                null) base=null ;;
                *[!0123456789abcdef]* | '') echo GUEST_TOOL_BAD_BASE >/dev/hvc0; continue ;;
                *)
                    if [ "${#extra}" -ne 64 ]; then echo GUEST_TOOL_BAD_BASE >/dev/hvc0; continue; fi
                    base="\"$extra\""
                    ;;
            esac
            echo GUEST_TOOL_WRITE_REQUEST=$nonce >/dev/hvc0
            $BB printf '%s {"id":%s,"method":"write","resource":"note","base":%s,"text":"%s","epoch":%s}\n' \
                "$nonce" "$sequence" "$base" "$((factor * value))" "$epoch"
            ;;
        *) echo GUEST_TOOL_BAD_REQUEST >/dev/hvc0 ;;
    esac
done
echo GUEST_TOOL_CHANNEL_CLOSED >/dev/hvc0
