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
    // Compact constructor: valida invariantes do dominio na criacao da entidade.
    // Garante que regras de negocio sao aplicadas independente da camada HTTP.
    // Simetrico ao metodo Validate() do Payment.go no backend Go.
    public Payment {
        if (amount == null || amount.compareTo(BigDecimal.valueOf(0.01)) < 0) {
            throw new DomainException("O valor do pagamento deve ser maior que zero");
        }
        if (cardNumber == null || cardNumber.isBlank() || cardNumber.length() < 13 || cardNumber.length() > 19) {
            throw new DomainException("O numero do cartao deve ter entre 13 e 19 caracteres");
        }
    }

    public Payment withStatus(String newStatus, String extId) {
        return new Payment(id, amount, cardNumber, newStatus, extId, createdAt);
    }
}
