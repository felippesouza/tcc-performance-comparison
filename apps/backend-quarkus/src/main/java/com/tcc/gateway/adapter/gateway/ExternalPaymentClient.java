// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25 vs Quarkus Native
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.adapter.gateway;

import io.quarkus.runtime.annotations.RegisterForReflection;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.core.MediaType;
import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;

@RegisterRestClient(configKey = "external-api")
@Path("/process-payment")
public interface ExternalPaymentClient {

    @POST
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    ExternalPaymentResponse process(ExternalPaymentRequest request);

    @RegisterForReflection
    record ExternalPaymentRequest(String paymentId, java.math.BigDecimal amount, String cardNumber) {}

    @RegisterForReflection
    record ExternalPaymentResponse(String externalId, boolean approved) {}
}
