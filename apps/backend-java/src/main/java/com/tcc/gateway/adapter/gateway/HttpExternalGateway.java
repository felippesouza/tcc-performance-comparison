// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.adapter.gateway;

import com.tcc.gateway.domain.ExternalGateway;
import com.tcc.gateway.domain.Payment;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class HttpExternalGateway implements ExternalGateway {

    private final RestClient restClient;
    private final String apiPath;

    public HttpExternalGateway(
            RestClient.Builder restClientBuilder, 
            @Value("${external.api.base-url}") String baseUrl,
            @Value("${external.api.path}") String apiPath) {
        
        this.restClient = restClientBuilder.baseUrl(baseUrl).build();
        this.apiPath = apiPath;
    }

    @Override
    public ExternalGateway.PaymentResponse process(Payment payment) {
        // Chamada síncrona que será gerenciada pelas Virtual Threads.
        // Usa um DTO dedicado para não expor campos internos da entidade de domínio
        // (status, createdAt) no payload enviado à adquirente — equivalente ao
        // externalPaymentRequest do Go.
        var request = new ExternalPaymentRequest(payment.id(), payment.amount(), payment.cardNumber());
        return restClient.post()
            .uri(apiPath)
            .body(request)
            .retrieve()
            .body(ExternalGateway.PaymentResponse.class);
    }

    // DTO privado para a chamada externa: expõe apenas os campos necessários à adquirente.
    private record ExternalPaymentRequest(String paymentId, java.math.BigDecimal amount, String cardNumber) {}
}
