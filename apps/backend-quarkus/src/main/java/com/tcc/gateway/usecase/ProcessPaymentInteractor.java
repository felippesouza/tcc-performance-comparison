// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25 vs Quarkus Native
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2025
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.usecase;

import com.tcc.gateway.domain.ExternalGateway;
import com.tcc.gateway.domain.Payment;
import com.tcc.gateway.domain.PaymentRepository;

import java.time.LocalDateTime;
import java.util.UUID;

public class ProcessPaymentInteractor implements ProcessPaymentUseCase {

    private final PaymentRepository repository;
    private final ExternalGateway externalGateway;

    public ProcessPaymentInteractor(PaymentRepository repository, ExternalGateway externalGateway) {
        this.repository = repository;
        this.externalGateway = externalGateway;
    }

    @Override
    public Payment execute(Payment request) {
        Payment pending = new Payment(
            UUID.randomUUID().toString(),
            request.amount(),
            request.cardNumber(),
            "PENDING",
            null,
            LocalDateTime.now()
        );
        repository.save(pending);

        ExternalGateway.PaymentResponse response = externalGateway.process(pending);
        String finalStatus = response.approved() ? "APPROVED" : "REJECTED";

        Payment updated = pending.withStatus(finalStatus, response.externalId());
        return repository.save(updated);
    }
}
