// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25 vs Quarkus Native
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2025
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.infrastructure.startup;

import io.quarkus.runtime.StartupEvent;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.jboss.logging.Logger;

/**
 * Loga a configuração de pools e threads na inicialização.
 *
 * Espelha o log do backend Go:
 *   slog.Info("Pool de conexões configurado", "max_conns", maxConns)
 */
@ApplicationScoped
public class DatabaseStartupLog {

    private static final Logger LOG = Logger.getLogger(DatabaseStartupLog.class);

    @ConfigProperty(name = "quarkus.datasource.jdbc.max-size", defaultValue = "200")
    int maxPoolSize;

    @ConfigProperty(name = "quarkus.datasource.jdbc.min-size", defaultValue = "5")
    int minPoolSize;

    @ConfigProperty(name = "quarkus.datasource.jdbc.acquisition-timeout", defaultValue = "5S")
    String acquisitionTimeout;

    @ConfigProperty(name = "quarkus.thread-pool.max-threads", defaultValue = "600")
    int maxThreads;

    @ConfigProperty(name = "quarkus.redis.max-pool-size", defaultValue = "200")
    int redisMaxPoolSize;

    void onStart(@Observes StartupEvent ev) {
        LOG.infof("Pool de conexões configurado — max=%d, min=%d, acquisition-timeout=%s",
            maxPoolSize, minPoolSize, acquisitionTimeout);
        LOG.infof("Thread pool configurado — max-threads=%d", maxThreads);
        LOG.infof("Redis pool configurado — max-pool-size=%d", redisMaxPoolSize);
    }
}
