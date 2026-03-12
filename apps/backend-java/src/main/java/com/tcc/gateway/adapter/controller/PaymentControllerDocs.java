// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.adapter.controller;

import com.tcc.gateway.adapter.controller.dto.PaymentRequest;
import com.tcc.gateway.adapter.controller.dto.PaymentResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.enums.ParameterIn;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;

@Tag(name = "Payment Gateway", description = "Endpoints para processamento de pagamentos concorrentes")
public interface PaymentControllerDocs {

    @Operation(
        summary = "Processar um novo pagamento",
        description = "Recebe os dados do cartão, valida a transação e consulta a adquirente externa. " +
                      "Suporta idempotência via header X-Idempotency-Key para evitar cobranças duplicadas em retries."
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "201", description = "Pagamento processado com sucesso",
                     content = @Content(schema = @Schema(implementation = PaymentResponse.class))),
        @ApiResponse(responseCode = "400", description = "Dados da requisição inválidos ou falha de negócio",
                     content = @Content),
        @ApiResponse(responseCode = "500", description = "Erro interno no servidor ou timeout da adquirente",
                     content = @Content)
    })
    ResponseEntity<PaymentResponse> create(
        @Parameter(description = "Chave única para idempotência. Se enviada, requisições repetidas com a mesma chave retornam o resultado original sem reprocessar o pagamento.",
                   in = ParameterIn.HEADER, example = "req-uuid-1234")
        @RequestHeader(value = "X-Idempotency-Key", required = false) String idempotencyKey,
        @Valid @RequestBody PaymentRequest request
    );
}
