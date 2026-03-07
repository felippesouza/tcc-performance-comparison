package com.tcc.gateway.domain;

public interface ExternalGateway {
    PaymentResponse process(Payment payment);

    record PaymentResponse(String externalId, boolean approved) {}
}
