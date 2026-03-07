package com.tcc.gateway.adapter.controller;

import com.tcc.gateway.domain.Payment;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;

@Component
public class PaymentRestMapper {

    public Payment toDomain(PaymentRequest request) {
        return new Payment(null, request.amount(), request.cardNumber(), null, null, null);
    }

    public PaymentResponse toResponse(Payment payment) {
        return new PaymentResponse(payment.id(), payment.status(), payment.externalId());
    }

    record PaymentRequest(BigDecimal amount, String cardNumber) {}
    record PaymentResponse(String id, String status, String externalId) {}
}
