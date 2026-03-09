package com.tcc.gateway.adapter.controller;

import com.tcc.gateway.domain.Payment;
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
public class PaymentRestMapperImpl implements PaymentRestMapper {

    @Override
    public Payment toDomain(PaymentRestMapper.PaymentRequest request) {
        if ( request == null ) {
            return null;
        }

        BigDecimal amount = null;
        String cardNumber = null;

        amount = request.amount();
        cardNumber = request.cardNumber();

        String id = null;
        String status = null;
        String externalId = null;
        LocalDateTime createdAt = null;

        Payment payment = new Payment( id, amount, cardNumber, status, externalId, createdAt );

        return payment;
    }

    @Override
    public PaymentRestMapper.PaymentResponse toResponse(Payment payment) {
        if ( payment == null ) {
            return null;
        }

        String id = null;
        String status = null;
        String externalId = null;

        id = payment.id();
        status = payment.status();
        externalId = payment.externalId();

        PaymentRestMapper.PaymentResponse paymentResponse = new PaymentRestMapper.PaymentResponse( id, status, externalId );

        return paymentResponse;
    }
}
