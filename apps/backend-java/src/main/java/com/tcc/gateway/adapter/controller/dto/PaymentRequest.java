// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.adapter.controller.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;

@Schema(description = "Dados para criação de um novo pagamento")
public record PaymentRequest(
    @Schema(description = "Valor da transação", example = "150.50", minimum = "0.01")
    @NotNull(message = "O valor é obrigatório")
    @DecimalMin(value = "0.01", message = "O valor mínimo é 0.01")
    BigDecimal amount,

    @Schema(description = "Número do cartão de crédito", example = "1234-5678-9012-3456", minLength = 13, maxLength = 19)
    @NotBlank(message = "O número do cartão é obrigatório")
    @Size(min = 13, max = 19, message = "O cartão deve ter entre 13 e 19 dígitos")
    String cardNumber
) {}
