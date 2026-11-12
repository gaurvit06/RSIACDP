#!/bin/sh
set -eu

value=${MAX_UPLOAD_BYTES:-10485760}
case "$value" in
    ''|*[!0-9]*) echo "MAX_UPLOAD_BYTES must be an integer" >&2; exit 1 ;;
esac
while [ "${value#0}" != "$value" ]; do value=${value#0}; done
[ -n "$value" ] || value=0
if [ "${#value}" -gt 8 ]; then
    echo "MAX_UPLOAD_BYTES must be between 1 and 52428800" >&2
    exit 1
fi
if [ "$value" -lt 1 ] || [ "$value" -gt 52428800 ]; then
    echo "MAX_UPLOAD_BYTES must be between 1 and 52428800" >&2
    exit 1
fi

# Allow the configured file size plus bounded multipart/form overhead.
MAX_REQUEST_BODY_KIB=$(((value + 65536 + 1023) / 1024))
export MAX_REQUEST_BODY_KIB
exec /docker-entrypoint.sh "$@"
