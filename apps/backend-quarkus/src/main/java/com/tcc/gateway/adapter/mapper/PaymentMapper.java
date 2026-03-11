package com.tcc.gateway.adapter.mapper;

import com.tcc.gateway.adapter.controller.dto.PaymentRequest;
import com.tcc.gateway.adapter.controller.dto.PaymentResponse;
import com.tcc.gateway.domain.Payment;
import jakarta.enterprise.context.ApplicationScoped;

@ApplicationScoped
public class PaymentMapper {

    public Payment toDomain(PaymentRequest request) {
        return new Payment(null, request.amount(), request.cardNumber(), "PENDING", null, null);
    }

    public PaymentResponse toResponse(Payment payment) {
        return new PaymentResponse(payment.id(), payment.status(), payment.externalId());
    }
}
