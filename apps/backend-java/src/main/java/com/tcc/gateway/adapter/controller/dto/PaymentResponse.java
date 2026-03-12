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

@Schema(description = "Resposta do processamento de pagamento")
public record PaymentResponse(
    @Schema(description = "ID interno da transação", example = "550e8400-e29b-41d4-a716-446655440000")
    String id,
    
    @Schema(description = "Status atual da transação", example = "APPROVED")
    String status,
    
    @Schema(description = "ID retornado pela adquirente externa", example = "ext_987654321")
    String externalId
) {}
