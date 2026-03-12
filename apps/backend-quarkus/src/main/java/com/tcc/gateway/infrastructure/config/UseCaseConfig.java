// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25 vs Quarkus Native
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.infrastructure.config;

import com.tcc.gateway.adapter.gateway.JpaPaymentRepository;
import com.tcc.gateway.adapter.gateway.HttpExternalGateway;
import com.tcc.gateway.usecase.ProcessPaymentInteractor;
import com.tcc.gateway.usecase.ProcessPaymentUseCase;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.inject.Produces;
import jakarta.inject.Inject;

@ApplicationScoped
public class UseCaseConfig {

    @Inject
    JpaPaymentRepository repository;

    @Inject
    HttpExternalGateway externalGateway;

    @Produces
    @ApplicationScoped
    public ProcessPaymentUseCase processPaymentUseCase() {
        return new ProcessPaymentInteractor(repository, externalGateway);
    }
}
