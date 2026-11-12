FROM postgres:18.4-alpine3.24 AS patched

RUN apk upgrade --no-cache \
    && apk add --no-cache su-exec \
    && rm -f /usr/local/bin/gosu \
    && ln -s "$(command -v su-exec)" /usr/local/bin/gosu \
    && gosu postgres true

# Copy the merged filesystem into a fresh image so the vulnerable upstream
# gosu bytes are not retained in a hidden parent layer. Preserve the official
# PostgreSQL image's runtime contract below.
FROM scratch
COPY --from=patched / /

ENV PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    GOSU_VERSION="1.19" \
    LANG="en_US.utf8" \
    PG_MAJOR="16" \
    PG_VERSION="16.15" \
    PG_SHA256="c1575341fa7bd40f5274ea465b34390f4dc64cdd0770af327005caaeb9f6b7ed" \
    DOCKER_PG_LLVM_DEPS="llvm21-dev clang21" \
    PGDATA="/var/lib/postgresql/data"

EXPOSE 5432
VOLUME ["/var/lib/postgresql/data"]
WORKDIR /
STOPSIGNAL SIGINT
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["postgres"]
