package com.tcc.gateway.domain;

public interface ExternalGateway {
    record PaymentResponse(String externalId, boolean approved) {}
    PaymentResponse process(Payment payment);
}
