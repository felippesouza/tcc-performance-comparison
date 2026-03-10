// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2025
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.domain;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record Payment(
    String id,
    BigDecimal amount,
    String cardNumber,
    String status,
    String externalId,
    LocalDateTime createdAt
) {
    public Payment withStatus(String newStatus, String extId) {
        return new Payment(id, amount, cardNumber, newStatus, extId, createdAt);
    }
}
