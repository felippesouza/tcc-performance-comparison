package com.tcc.gateway.adapter.gateway;

import com.tcc.gateway.domain.Payment;
import com.tcc.gateway.infrastructure.entity.PaymentEntity;
import org.springframework.stereotype.Component;

@Component
public class PaymentEntityMapper {

    public PaymentEntity toEntity(Payment payment) {
        return new PaymentEntity(
            payment.id(),
            payment.amount(),
            payment.cardNumber(),
            payment.status(),
            payment.externalId(),
            payment.createdAt()
        );
    }

    public Payment toDomain(PaymentEntity entity) {
        return new Payment(
            entity.getId(),
            entity.getAmount(),
            entity.getCardNumber(),
            entity.getStatus(),
            entity.getExternalId(),
            entity.getCreatedAt()
        );
    }
}
