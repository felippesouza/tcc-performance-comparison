// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.infrastructure.config;

import com.tcc.gateway.domain.ExternalGateway;
import com.tcc.gateway.domain.PaymentRepository;
import com.tcc.gateway.usecase.ProcessPaymentInteractor;
import com.tcc.gateway.usecase.ProcessPaymentUseCase;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class UseCaseConfig {

    @Bean
    public ProcessPaymentUseCase processPaymentUseCase(
            PaymentRepository repository,
            ExternalGateway externalGateway) {
        return new ProcessPaymentInteractor(repository, externalGateway);
    }
}
