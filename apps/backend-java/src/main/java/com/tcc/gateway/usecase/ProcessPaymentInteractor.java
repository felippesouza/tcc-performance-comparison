package com.tcc.gateway.usecase;

import com.tcc.gateway.domain.ExternalGateway;
import com.tcc.gateway.domain.Payment;
import com.tcc.gateway.domain.PaymentRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.UUID;

@Service
public class ProcessPaymentInteractor implements ProcessPaymentUseCase {

    private final PaymentRepository repository;
    private final ExternalGateway externalGateway;

    public ProcessPaymentInteractor(PaymentRepository repository, ExternalGateway externalGateway) {
        this.repository = repository;
        this.externalGateway = externalGateway;
    }

    @Override
    @Transactional
    public Payment execute(Payment request) {
        // 1. Persistir pagamento inicial (PENDENTE)
        Payment payment = new Payment(
            UUID.randomUUID().toString(),
            request.amount(),
            request.cardNumber(),
            "PENDING",
            null,
            LocalDateTime.now()
        );
        repository.save(payment);

        // 2. Chamar Gateway Externo (Este é o I/O que as Virtual Threads gerenciam)
        var response = externalGateway.process(payment);

        // 3. Atualizar status baseado na resposta externa
        String finalStatus = response.approved() ? "APPROVED" : "REJECTED";
        Payment updatedPayment = payment.withStatus(finalStatus, response.externalId());
        
        return repository.save(updatedPayment);
    }
}
