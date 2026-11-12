#!/usr/bin/env bash
set -Eeuo pipefail
: "${NEO4J_PASSWORD:?Set NEO4J_PASSWORD in the Render shared environment group}"
neo4j_password="$(printf '%s' "$NEO4J_PASSWORD" | sed 's:/:_:g')"
export NEO4J_AUTH="${NEO4J_USER:-neo4j}/$neo4j_password"
exec /startup/docker-entrypoint.sh "$@"
