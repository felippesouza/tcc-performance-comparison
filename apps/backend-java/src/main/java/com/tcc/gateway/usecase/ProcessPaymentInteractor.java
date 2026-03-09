package com.tcc.gateway.usecase;

import com.tcc.gateway.domain.ExternalGateway;
import com.tcc.gateway.domain.Payment;
import com.tcc.gateway.domain.PaymentRepository;

import java.time.LocalDateTime;
import java.util.UUID;

public class ProcessPaymentInteractor implements ProcessPaymentUseCase {

    private final PaymentRepository repository;
    private final ExternalGateway externalGateway;

    public ProcessPaymentInteractor(PaymentRepository repository, ExternalGateway externalGateway) {
        this.repository = repository;
        this.externalGateway = externalGateway;
    }

    @Override
    public Payment execute(Payment request) {
        Payment payment = new Payment(
            UUID.randomUUID().toString(),
            request.amount(),
            request.cardNumber(),
            "PENDING",
            null,
            LocalDateTime.now()
        );
        repository.save(payment);

        var response = externalGateway.process(payment);

        String finalStatus = response.approved() ? "APPROVED" : "REJECTED";
        Payment updatedPayment = payment.withStatus(finalStatus, response.externalId());
        
        return repository.save(updatedPayment);
    }
}
