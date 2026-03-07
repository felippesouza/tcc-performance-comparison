package com.tcc.gateway.infrastructure.entity;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface SpringDataPaymentRepository extends JpaRepository<PaymentEntity, String> {
}
