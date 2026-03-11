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
 * Loga a configuração do pool de conexões na inicialização.
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

    void onStart(@Observes StartupEvent ev) {
        LOG.infof("Pool de conexões configurado — max=%d, min=%d, acquisition-timeout=%s",
            maxPoolSize, minPoolSize, acquisitionTimeout);
    }
}
