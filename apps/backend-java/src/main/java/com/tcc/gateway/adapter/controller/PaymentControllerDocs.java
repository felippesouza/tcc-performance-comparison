package com.tcc.gateway.adapter.controller;

import com.tcc.gateway.adapter.controller.dto.PaymentRequest;
import com.tcc.gateway.adapter.controller.dto.PaymentResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestBody;

@Tag(name = "Payment Gateway", description = "Endpoints para processamento de pagamentos concorrentes")
public interface PaymentControllerDocs {

    @Operation(summary = "Processar um novo pagamento", 
               description = "Este endpoint recebe os dados de um cartão, valida a transação e consulta a adquirente externa.")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "201", description = "Pagamento processado com sucesso",
                     content = @Content(schema = @Schema(implementation = PaymentResponse.class))),
        @ApiResponse(responseCode = "400", description = "Dados da requisição inválidos ou falha de negócio",
                     content = @Content),
        @ApiResponse(responseCode = "500", description = "Erro interno no servidor ou timeout da adquirente",
                     content = @Content)
    })
    ResponseEntity<PaymentResponse> create(@Valid @RequestBody PaymentRequest request);
}
