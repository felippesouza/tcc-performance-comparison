# -- Stage 1: Native build --------------------------------------------------
FROM quay.io/quarkus/ubi-quarkus-mandrel-builder-image:jdk-21 AS builder

USER quarkus
WORKDIR /home/quarkus/app

COPY --chown=quarkus:quarkus pom.xml .
COPY --chown=quarkus:quarkus src ./src

RUN mvn package -Pnative -DskipTests -q

# -- Stage 2: Minimal runtime -----------------------------------------------
FROM debian:bookworm-slim

WORKDIR /work
COPY --from=builder /home/quarkus/app/target/*-runner /work/application

RUN chmod +x /work/application

EXPOSE 8083

ENTRYPOINT ["/work/application", "-Dquarkus.http.host=0.0.0.0"]
