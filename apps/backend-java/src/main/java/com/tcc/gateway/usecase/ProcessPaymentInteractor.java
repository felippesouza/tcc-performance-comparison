// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
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

    // Nota arquitetural sobre propagação de contexto (Go vs Java):
    // Em Go, o `ctx` da requisição HTTP percorre toda a cadeia (usecase → repository → gateway).
    // Se o cliente desconectar, o ctx é cancelado e todas as operações são interrompidas.
    // Em Java com Virtual Threads, não há contexto explícito: o cancelamento é gerenciado via
    // timeout na camada de infraestrutura (RestClient readTimeout=5s) e interrupção de thread.
    // Ambas as abordagens garantem que a thread não fique presa indefinidamente — apenas pelo mecanismo diferente.
    @Override
    public Payment execute(Payment request) {
        Payment payment = new Payment(
            UUID.randomUUID().toString(),
            request.amount(),
            request.cardNumber(),
            "PENDING",
            null,
            LocalDateTime.now()
        );
        repository.save(payment);

        var response = externalGateway.process(payment);

        String finalStatus = response.approved() ? "APPROVED" : "REJECTED";
        Payment updatedPayment = payment.withStatus(finalStatus, response.externalId());

        return repository.save(updatedPayment);
    }
}
