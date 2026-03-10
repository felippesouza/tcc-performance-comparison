# Stage 1: Build
FROM eclipse-temurin:25-jdk-alpine AS builder

# Instalar Maven (já que a imagem oficial maven-25 pode não estar pronta)
RUN apk add --no-cache maven

WORKDIR /app
COPY pom.xml ./
# Baixa as dependências para aproveitar o cache
RUN mvn dependency:go-offline

COPY src ./src
# Build do jar ignorando testes para ser mais rápido
RUN mvn clean package -DskipTests

# Stage 2: Runtime
FROM eclipse-temurin:25-jre-alpine

WORKDIR /app
COPY --from=builder /app/target/backend-java-0.0.1-SNAPSHOT.jar app.jar

# Variáveis de ambiente padrão
ENV SPRING_PROFILES_ACTIVE=prod
ENV SERVER_PORT=8081

EXPOSE 8081

# Executa o Java habilitando flags recomendadas para Virtual Threads (ZGC Generacional)
# Flags de performance e observabilidade para Virtual Threads:
# -XX:+UseZGC -XX:+ZGenerational → GC de baixa latência, recomendado com Loom
# -Djdk.tracePinnedThreads=full  → Loga no stdout quando uma Virtual Thread fica "pinned"
#                                   (presa na carrier thread por synchronized/native).
#                                   CRÍTICO para a pesquisa: detecta se Hibernate/JDBC
#                                   cancela o benefício das Virtual Threads.
ENTRYPOINT ["java", \
  "-XX:+UseZGC", \
  "-XX:+ZGenerational", \
  "-Djdk.tracePinnedThreads=full", \
  "-jar", "app.jar"]