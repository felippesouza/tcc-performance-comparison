// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2025
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.adapter.gateway;

import com.tcc.gateway.adapter.mapper.PaymentEntityMapper;
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
