// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25 vs Quarkus Native
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2025
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.adapter.gateway;

import com.tcc.gateway.domain.Payment;
import com.tcc.gateway.domain.PaymentRepository;
import com.tcc.gateway.infrastructure.entity.PaymentEntity;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.persistence.EntityManager;
import jakarta.transaction.Transactional;

import java.util.Optional;

@ApplicationScoped
public class JpaPaymentRepository implements PaymentRepository {

    @Inject
    EntityManager em;

    @Override
    @Transactional
    public Payment save(Payment payment) {
        PaymentEntity entity = toEntity(payment);
        em.merge(entity);
        return payment;
    }

    @Override
    public Optional<Payment> findById(String id) {
        PaymentEntity entity = em.find(PaymentEntity.class, id);
        return Optional.ofNullable(entity).map(this::toDomain);
    }

    private PaymentEntity toEntity(Payment p) {
        PaymentEntity e = new PaymentEntity();
        e.id = p.id();
        e.amount = p.amount();
        e.cardNumber = p.cardNumber();
        e.status = p.status();
        e.externalId = p.externalId();
        e.createdAt = p.createdAt();
        return e;
    }

    private Payment toDomain(PaymentEntity e) {
        return new Payment(e.id, e.amount, e.cardNumber, e.status, e.externalId, e.createdAt);
    }
}
