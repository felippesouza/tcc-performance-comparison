// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25 vs Quarkus Native
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.infrastructure.entity;

import io.quarkus.runtime.annotations.RegisterForReflection;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "payments")
@RegisterForReflection
public class PaymentEntity {

    @Id
    @Column(length = 36)
    public String id;

    @Column(nullable = false, precision = 10, scale = 2)
    public BigDecimal amount;

    @Column(name = "card_number", nullable = false, length = 19)
    public String cardNumber;

    @Column(nullable = false, length = 20)
    public String status;

    @Column(name = "external_id", length = 50)
    public String externalId;

    @Column(name = "created_at", nullable = false)
    public LocalDateTime createdAt;
}
