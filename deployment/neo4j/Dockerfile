FROM neo4j:5.26.33-community-trixie
USER root
COPY --chmod=755 deployment/neo4j/render-entrypoint.sh /usr/local/bin/render-entrypoint.sh
ENTRYPOINT ["tini", "-g", "--", "/usr/local/bin/render-entrypoint.sh"]
CMD ["neo4j"]
