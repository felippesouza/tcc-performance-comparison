// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25 vs Quarkus Native
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.infrastructure.filter;

import com.tcc.gateway.infrastructure.shutdown.GracefulShutdownManager;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.ws.rs.container.ContainerRequestContext;
import jakarta.ws.rs.container.ContainerRequestFilter;
import jakarta.ws.rs.container.ContainerResponseContext;
import jakarta.ws.rs.container.ContainerResponseFilter;
import jakarta.ws.rs.ext.Provider;

import java.util.concurrent.TimeUnit;

/**
 * Captura métricas HTTP para o Prometheus — espelhando o comportamento de:
 * - Java backend: Spring Boot Actuator (http_server_requests_seconds automático)
 * - Go backend: middleware prometheusMiddleware com httpRequestDuration + httpRequestsInFlight
 *
 * Métricas exportadas:
 *   http_server_requests_seconds{method, uri, status, outcome} — histograma de latência
 *   http_requests_in_flight                                    — gauge de requisições ativas
 */
@Provider
@ApplicationScoped
public class PrometheusMetricsFilter implements ContainerRequestFilter, ContainerResponseFilter {

    private static final String START_TIME_KEY = "metrics.start.nanos";

    @Inject
    MeterRegistry meterRegistry;

    @Inject
    GracefulShutdownManager shutdownManager;

    @Override
    public void filter(ContainerRequestContext requestContext) {
        requestContext.setProperty(START_TIME_KEY, System.nanoTime());
        shutdownManager.incrementRequest();
    }

    @Override
    public void filter(ContainerRequestContext requestContext, ContainerResponseContext responseContext) {
        shutdownManager.decrementRequest();

        try {
            Long startNanos = (Long) requestContext.getProperty(START_TIME_KEY);
            if (startNanos == null) return;

            long durationNanos = System.nanoTime() - startNanos;
            int status = responseContext.getStatus();
            String outcome = resolveOutcome(status);

            // Espelha label set do Spring Boot Actuator e do Go backend
            Timer.builder("http_server_requests_seconds")
                .description("Duração das requisições HTTP em segundos")
                .tags(
                    "method",  requestContext.getMethod(),
                    "uri",     sanitizePath(requestContext.getUriInfo().getPath()),
                    "status",  String.valueOf(status),
                    "outcome", outcome
                )
                .register(meterRegistry)
                .record(durationNanos, TimeUnit.NANOSECONDS);

        } catch (Exception ignored) {
            // Nunca propagar exceção de métricas para o response
        }
    }

    private String resolveOutcome(int status) {
        if (status >= 500) return "SERVER_ERROR";
        if (status >= 400) return "CLIENT_ERROR";
        if (status >= 300) return "REDIRECTION";
        return "SUCCESS";
    }

    private String sanitizePath(String path) {
        // Normaliza variáveis de path para evitar cardinalidade explosiva (ex: /payments/123 → /payments/{id})
        return path == null ? "unknown" : path.replaceAll("/[0-9a-f]{8}-[0-9a-f-]{27}", "/{id}");
    }
}
