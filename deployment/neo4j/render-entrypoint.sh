#!/usr/bin/env bash
set -Eeuo pipefail
if [[ -n "${NEO4J_PASSWORD:-}" ]]; then
    neo4j_password="$NEO4J_PASSWORD"
    if [[ "${NEO4J_PASSWORD_SLASH_SAFE:-false}" == "1" || "${NEO4J_PASSWORD_SLASH_SAFE:-false}" == "true" ]]; then
        neo4j_password="$(printf '%s' "$neo4j_password" | sed 's:/:_:g')"
    fi
    export NEO4J_AUTH="${NEO4J_USER:-neo4j}/$neo4j_password"
fi
: "${NEO4J_AUTH:?Set NEO4J_AUTH or NEO4J_PASSWORD before starting Neo4j}"
exec /startup/docker-entrypoint.sh "$@"
