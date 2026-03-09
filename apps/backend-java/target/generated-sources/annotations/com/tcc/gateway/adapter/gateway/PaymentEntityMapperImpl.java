package com.tcc.gateway.adapter.gateway;

import com.tcc.gateway.domain.Payment;
import com.tcc.gateway.infrastructure.entity.PaymentEntity;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import javax.annotation.processing.Generated;
import org.springframework.stereotype.Component;

@Generated(
    value = "org.mapstruct.ap.MappingProcessor",
    date = "2026-03-09T10:11:19-0300",
    comments = "version: 1.6.3, compiler: javac, environment: Java 25.0.2 (Oracle Corporation)"
)
@Component
public class PaymentEntityMapperImpl implements PaymentEntityMapper {

    @Override
    public PaymentEntity toEntity(Payment payment) {
        if ( payment == null ) {
            return null;
        }

        PaymentEntity paymentEntity = new PaymentEntity();

        paymentEntity.setId( payment.id() );
        paymentEntity.setAmount( payment.amount() );
        paymentEntity.setCardNumber( payment.cardNumber() );
        paymentEntity.setStatus( payment.status() );
        paymentEntity.setExternalId( payment.externalId() );
        paymentEntity.setCreatedAt( payment.createdAt() );

        return paymentEntity;
    }

    @Override
    public Payment toDomain(PaymentEntity entity) {
        if ( entity == null ) {
            return null;
        }

        String id = null;
        BigDecimal amount = null;
        String cardNumber = null;
        String status = null;
        String externalId = null;
        LocalDateTime createdAt = null;

        id = entity.getId();
        amount = entity.getAmount();
        cardNumber = entity.getCardNumber();
        status = entity.getStatus();
        externalId = entity.getExternalId();
        createdAt = entity.getCreatedAt();

        Payment payment = new Payment( id, amount, cardNumber, status, externalId, createdAt );

        return payment;
    }
}
