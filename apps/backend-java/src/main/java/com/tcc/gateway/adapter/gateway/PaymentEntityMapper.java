package com.tcc.gateway.adapter.gateway;

import com.tcc.gateway.domain.Payment;
import com.tcc.gateway.infrastructure.entity.PaymentEntity;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface PaymentEntityMapper {

    PaymentEntity toEntity(Payment payment);

    Payment toDomain(PaymentEntity entity);
}
