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
