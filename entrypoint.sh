#!/bin/sh
set -e

mkdir -p /moyan/data/uploads /moyan/data/thumbs /moyan/data/temp
chown -R moyan:moyan /moyan/data

if [ "$(id -u)" = "0" ]; then
    exec setpriv --reuid=moyan --regid=moyan --init-groups "$@"
fi

exec "$@"
