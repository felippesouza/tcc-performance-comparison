package com.tcc.gateway.adapter.gateway;

import com.tcc.gateway.domain.Payment;
import com.tcc.gateway.domain.PaymentRepository;
import com.tcc.gateway.infrastructure.entity.PaymentEntity;
import com.tcc.gateway.infrastructure.entity.SpringDataPaymentRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.Optional;

@Component
@RequiredArgsConstructor
public class JpaPaymentRepository implements PaymentRepository {

    private final SpringDataPaymentRepository repository;

    @Override
    public Payment save(Payment p) {
        var entity = new PaymentEntity(p.id(), p.amount(), p.cardNumber(), p.status(), p.externalId(), p.createdAt());
        var saved = repository.save(entity);
        return new Payment(saved.getId(), saved.getAmount(), saved.getCardNumber(), saved.getStatus(), saved.getExternalId(), saved.getCreatedAt());
    }

    @Override
    public Optional<Payment> findById(String id) {
        return repository.findById(id)
            .map(s -> new Payment(s.getId(), s.getAmount(), s.getCardNumber(), s.getStatus(), s.getExternalId(), s.getCreatedAt()));
    }
}
