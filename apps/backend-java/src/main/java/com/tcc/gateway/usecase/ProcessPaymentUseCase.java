package com.tcc.gateway.usecase;

import com.tcc.gateway.domain.Payment;

public interface ProcessPaymentUseCase {
    Payment execute(Payment request);
}
