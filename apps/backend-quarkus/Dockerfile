# ============================================================
# TCC — Quarkus Native Backend
# Runtime: GraalVM Mandrel (AOT, sem JVM em execução)
# Nota científica: diferentemente de backend-java (Java 25 + Virtual Threads + ZGC),
# o binário nativo não usa JVM — não há Virtual Threads, JIT, nem GC heap.
# O footprint de RAM esperado é ~120-200 MB (vs ~1.2 GB do JVM backend).
# ============================================================

# -- Stage 1: Native build --------------------------------------------------
FROM quay.io/quarkus/ubi-quarkus-mandrel-builder-image:jdk-21 AS builder

COPY --chown=quarkus:quarkus mvnw .
COPY --chown=quarkus:quarkus .mvn .mvn
COPY --chown=quarkus:quarkus pom.xml .

USER quarkus

COPY --chown=quarkus:quarkus src src

RUN ./mvnw package -Pnative -DskipTests -q

# -- Stage 2: Minimal runtime -----------------------------------------------
FROM debian:bookworm-slim

WORKDIR /work
COPY --from=builder /project/target/*-runner /work/application

RUN chmod +x /work/application

EXPOSE 8083

ENTRYPOINT ["/work/application", "-Dquarkus.http.host=0.0.0.0"]
