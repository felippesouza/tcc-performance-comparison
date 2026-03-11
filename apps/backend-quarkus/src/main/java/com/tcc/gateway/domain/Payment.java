// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25 vs Quarkus Native
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
    public Payment {
        if (amount == null || amount.compareTo(new BigDecimal("0.01")) < 0)
            throw new DomainException("Amount must be >= 0.01");
        if (cardNumber == null || cardNumber.isBlank() || cardNumber.length() < 13 || cardNumber.length() > 19)
            throw new DomainException("Card number must be 13-19 digits");
    }

    public Payment withStatus(String newStatus, String newExternalId) {
        return new Payment(id, amount, cardNumber, newStatus, newExternalId, createdAt);
    }
}
