package com.tcc.gateway.adapter.controller;

import com.tcc.gateway.domain.Payment;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

import java.math.BigDecimal;

@Mapper(componentModel = "spring")
public interface PaymentRestMapper {

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "status", ignore = true)
    @Mapping(target = "externalId", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    Payment toDomain(PaymentRequest request);

    PaymentResponse toResponse(Payment payment);

    record PaymentRequest(BigDecimal amount, String cardNumber) {}
    record PaymentResponse(String id, String status, String externalId) {}
}
