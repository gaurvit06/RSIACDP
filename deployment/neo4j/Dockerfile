FROM neo4j:2026.10.2-trixie AS patched
USER root

# Apply Debian's available security updates, including the fixed zlib1g build.
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# Neo4j 2026.10.2 bundles Jackson 2.22.2. Replace the two scanner-confirmed
# vulnerable jars with their upstream fixed 2.22.3 releases and verify hashes.
RUN set -eux; \
    download_dir="$(mktemp -d)"; \
    curl --fail --silent --show-error --location --retry 3 \
      --output "$download_dir/jackson-core-2.22.3.jar" \
      https://repo.maven.apache.org/maven2/com/fasterxml/jackson/core/jackson-core/2.22.3/jackson-core-2.22.3.jar; \
    curl --fail --silent --show-error --location --retry 3 \
      --output "$download_dir/jackson-databind-2.22.3.jar" \
      https://repo.maven.apache.org/maven2/com/fasterxml/jackson/core/jackson-databind/2.22.3/jackson-databind-2.22.3.jar; \
    echo '8a501126a385b25841915d839508f8a66e2a0dbc8a6709d055ef3b3e852b094c  '"$download_dir/jackson-core-2.22.3.jar" | sha256sum -c -; \
    echo '556db5439e206114346043f68d200497dc96a0bca62a360a81784092ebd0e0a9  '"$download_dir/jackson-databind-2.22.3.jar" | sha256sum -c -; \
    neo4j_home="${NEO4J_HOME:-/var/lib/neo4j}"; \
    test -d "$neo4j_home"; \
    for artifact in jackson-core jackson-databind; do \
      matches="$(find -L "$neo4j_home" -type f -name "$artifact-2.22.2.jar" -print)"; \
      if [ -z "$matches" ]; then \
        echo "Expected vulnerable $artifact 2.22.2 jar not found under $neo4j_home; available versions:" >&2; \
        find -L "$neo4j_home" -type f -name "$artifact-*.jar" -print >&2; \
        exit 1; \
      fi; \
      printf '%s\n' "$matches" | while IFS= read -r old_jar; do \
        jar_dir="$(dirname "$old_jar")"; \
        rm -f "$old_jar"; \
        install -m 0644 "$download_dir/$artifact-2.22.3.jar" "$jar_dir/$artifact-2.22.3.jar"; \
      done; \
    done; \
    rm -rf "$download_dir"

COPY --chmod=755 deployment/neo4j/render-entrypoint.sh /usr/local/bin/render-entrypoint.sh

# Flatten the patched root filesystem so vulnerable jars and Debian packages
# from the upstream image's lower layers are not still visible to image scans.
FROM scratch
COPY --from=patched / /

ENV PATH="/var/lib/neo4j/bin:/opt/java/openjdk/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    JAVA_HOME="/opt/java/openjdk" \
    NEO4J_SHA256="fcbccee832175fd8b873ca7d8228dbde4cb5cce43f9053833cc7517dc4dd6f31" \
    NEO4J_TARBALL="neo4j-community-2026.10.2-unix.tar.gz" \
    NEO4J_EDITION="community" \
    NEO4J_HOME="/var/lib/neo4j" \
    LANG="C.UTF-8"

EXPOSE 7473 7474 7687
VOLUME ["/data", "/logs"]
WORKDIR /var/lib/neo4j
ENTRYPOINT ["tini", "-g", "--", "/usr/local/bin/render-entrypoint.sh"]
CMD ["neo4j"]
USER neo4j
