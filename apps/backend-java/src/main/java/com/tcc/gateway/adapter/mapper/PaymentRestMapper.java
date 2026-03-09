package com.tcc.gateway.adapter.mapper;

import com.tcc.gateway.adapter.controller.dto.PaymentRequest;
import com.tcc.gateway.adapter.controller.dto.PaymentResponse;
import com.tcc.gateway.domain.Payment;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface PaymentRestMapper {

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "status", ignore = true)
    @Mapping(target = "externalId", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    Payment toDomain(PaymentRequest request);

    PaymentResponse toResponse(Payment payment);
}
