// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25 vs Quarkus Native
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2025
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.adapter.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tcc.gateway.adapter.cache.IdempotencyCache;
import com.tcc.gateway.adapter.controller.dto.PaymentRequest;
import com.tcc.gateway.adapter.controller.dto.PaymentResponse;
import com.tcc.gateway.adapter.mapper.PaymentMapper;
import com.tcc.gateway.domain.Payment;
import com.tcc.gateway.usecase.ProcessPaymentUseCase;
import jakarta.inject.Inject;
import jakarta.validation.Valid;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.HeaderParam;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.eclipse.microprofile.openapi.annotations.Operation;
import org.eclipse.microprofile.openapi.annotations.media.Content;
import org.eclipse.microprofile.openapi.annotations.media.Schema;
import org.eclipse.microprofile.openapi.annotations.parameters.Parameter;
import org.eclipse.microprofile.openapi.annotations.responses.APIResponse;
import org.eclipse.microprofile.openapi.annotations.responses.APIResponses;
import org.eclipse.microprofile.openapi.annotations.tags.Tag;
import org.jboss.logging.Logger;

@Path("/payments")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
@Tag(name = "Payment Gateway", description = "Endpoints para processamento de pagamentos concorrentes")
public class PaymentController {

    private static final Logger LOG = Logger.getLogger(PaymentController.class);

    @Inject
    ProcessPaymentUseCase useCase;

    @Inject
    PaymentMapper mapper;

    @Inject
    IdempotencyCache idempotencyCache;

    @Inject
    ObjectMapper objectMapper;

    @POST
    @Operation(
        summary = "Processar um novo pagamento",
        description = "Recebe os dados do cartão, valida a transação e consulta a adquirente externa. " +
                      "Suporta idempotência via header X-Idempotency-Key para evitar cobranças duplicadas em retries."
    )
    @APIResponses({
        @APIResponse(
            responseCode = "201",
            description = "Pagamento processado com sucesso",
            content = @Content(schema = @Schema(implementation = PaymentResponse.class))
        ),
        @APIResponse(responseCode = "400", description = "Dados da requisição inválidos ou falha de negócio"),
        @APIResponse(responseCode = "500", description = "Erro interno no servidor ou timeout da adquirente")
    })
    public Response create(
        @Parameter(
            description = "Chave única para idempotência. Requisições repetidas com a mesma chave retornam " +
                          "o resultado original sem reprocessar o pagamento.",
            example = "req-uuid-1234"
        )
        @HeaderParam("X-Idempotency-Key") String idempotencyKey,
        @Valid PaymentRequest request
    ) throws Exception {
        // Idempotency check
        if (idempotencyKey != null && !idempotencyKey.isBlank()) {
            var cached = idempotencyCache.get(idempotencyKey);
            if (cached.isPresent()) {
                LOG.debugf("Idempotency hit for key: %s", idempotencyKey);
                PaymentResponse cachedResponse = objectMapper.readValue(cached.get(), PaymentResponse.class);
                return Response.status(Response.Status.CREATED).entity(cachedResponse).build();
            }
        }

        Payment domain = mapper.toDomain(request);
        Payment result = useCase.execute(domain);
        PaymentResponse response = mapper.toResponse(result);

        // Store in cache
        if (idempotencyKey != null && !idempotencyKey.isBlank()) {
            try {
                idempotencyCache.put(idempotencyKey, objectMapper.writeValueAsString(response));
            } catch (Exception e) {
                LOG.warnf("Failed to cache idempotency response: %s", e.getMessage());
            }
        }

        return Response.status(Response.Status.CREATED).entity(response).build();
    }
}
