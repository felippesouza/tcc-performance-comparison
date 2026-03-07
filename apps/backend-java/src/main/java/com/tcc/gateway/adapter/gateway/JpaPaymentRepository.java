package com.tcc.gateway.adapter.gateway;

import com.tcc.gateway.domain.Payment;
import com.tcc.gateway.domain.PaymentRepository;
import com.tcc.gateway.infrastructure.entity.SpringDataPaymentRepository;
import org.springframework.stereotype.Component;

import java.util.Optional;

@Component
public class JpaPaymentRepository implements PaymentRepository {

    private final SpringDataPaymentRepository repository;
    private final PaymentEntityMapper mapper;

    public JpaPaymentRepository(SpringDataPaymentRepository repository, PaymentEntityMapper mapper) {
        this.repository = repository;
        this.mapper = mapper;
    }

    @Override
    public Payment save(Payment p) {
        var entity = mapper.toEntity(p);
        var saved = repository.save(entity);
        return mapper.toDomain(saved);
    }

    @Override
    public Optional<Payment> findById(String id) {
        return repository.findById(id).map(mapper::toDomain);
    }
}
