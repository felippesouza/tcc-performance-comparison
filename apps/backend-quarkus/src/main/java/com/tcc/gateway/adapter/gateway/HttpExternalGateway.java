// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25 vs Quarkus Native
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.adapter.gateway;

import com.tcc.gateway.domain.ExternalGateway;
import com.tcc.gateway.domain.Payment;
import jakarta.enterprise.context.ApplicationScoped;
import org.eclipse.microprofile.rest.client.inject.RestClient;

@ApplicationScoped
public class HttpExternalGateway implements ExternalGateway {

    @RestClient
    ExternalPaymentClient client;

    @Override
    public PaymentResponse process(Payment payment) {
        var request = new ExternalPaymentClient.ExternalPaymentRequest(
            payment.id(), payment.amount(), payment.cardNumber()
        );
        ExternalPaymentClient.ExternalPaymentResponse response = client.process(request);
        return new PaymentResponse(response.externalId(), response.approved());
    }
}
