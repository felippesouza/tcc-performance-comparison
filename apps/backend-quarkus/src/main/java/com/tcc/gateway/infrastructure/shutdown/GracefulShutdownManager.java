// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25 vs Quarkus Native
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.infrastructure.shutdown;

import io.micrometer.core.instrument.MeterRegistry;
import io.quarkus.runtime.ShutdownEvent;
import io.quarkus.runtime.StartupEvent;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import jakarta.inject.Inject;
import org.jboss.logging.Logger;

import java.util.concurrent.atomic.AtomicInteger;

/**
 * Gerencia o shutdown gracioso do servidor, drenando requisições em andamento.
 *
 * Espelha o comportamento de:
 * - Java backend: server.shutdown=graceful + timeout-per-shutdown-phase=30s (Spring Boot)
 * - Go backend:   signal.Notify + srv.Shutdown(ctx) com timeout de 30s
 *
 * Também registra o gauge http_requests_in_flight no Prometheus —
 * espelhando o httpRequestsInFlight do backend Go.
 */
@ApplicationScoped
public class GracefulShutdownManager {

    private static final Logger LOG = Logger.getLogger(GracefulShutdownManager.class);
    private static final long SHUTDOWN_TIMEOUT_MS = 30_000L;
    private static final int  POLL_INTERVAL_MS    = 100;

    private final AtomicInteger inFlightRequests = new AtomicInteger(0);

    @Inject
    MeterRegistry meterRegistry;

    void onStart(@Observes StartupEvent ev) {
        // Registra o AtomicInteger como gauge — atualizado em tempo real pelo PrometheusMetricsFilter
        meterRegistry.gauge("http_requests_in_flight",
            inFlightRequests,
            AtomicInteger::get);

        LOG.info("GracefulShutdownManager inicializado — gauge http_requests_in_flight registrado");
    }

    public void incrementRequest() {
        inFlightRequests.incrementAndGet();
    }

    public void decrementRequest() {
        inFlightRequests.decrementAndGet();
    }

    void onShutdown(@Observes ShutdownEvent ev) {
        LOG.info("Shutdown gracioso iniciado — aguardando requisições em andamento...");

        long deadline = System.currentTimeMillis() + SHUTDOWN_TIMEOUT_MS;
        while (System.currentTimeMillis() < deadline) {
            int remaining = inFlightRequests.get();
            if (remaining <= 0) {
                LOG.info("Todas as requisições concluídas. Shutdown completo.");
                return;
            }
            LOG.debugf("Aguardando %d requisição(ões) em andamento...", remaining);
            try {
                Thread.sleep(POLL_INTERVAL_MS);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }

        int remaining = inFlightRequests.get();
        if (remaining > 0) {
            LOG.warnf("Timeout de shutdown atingido com %d requisição(ões) ainda em andamento", remaining);
        }
    }
}
