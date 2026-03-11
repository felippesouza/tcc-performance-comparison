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
        if (status == null || status.isBlank())
            throw new DomainException("Status is required");
    }

    public Payment withStatus(String newStatus, String newExternalId) {
        return new Payment(id, amount, cardNumber, newStatus, newExternalId, createdAt);
    }
}
