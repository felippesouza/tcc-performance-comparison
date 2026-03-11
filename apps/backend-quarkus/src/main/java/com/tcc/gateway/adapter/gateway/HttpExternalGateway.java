package com.tcc.gateway.adapter.gateway;

import com.tcc.gateway.domain.ExternalGateway;
import com.tcc.gateway.domain.Payment;
import jakarta.enterprise.context.ApplicationScoped;
import org.eclipse.microprofile.rest.client.inject.RestClient;

@ApplicationScoped
public class HttpExternalGateway implements ExternalGateway {

    @RestClient
    ExternalPaymentClient client;

    @Override
    public PaymentResponse process(Payment payment) {
        var request = new ExternalPaymentClient.ExternalPaymentRequest(
            payment.id(), payment.amount(), payment.cardNumber()
        );
        ExternalPaymentClient.ExternalPaymentResponse response = client.process(request);
        return new PaymentResponse(response.externalId(), response.approved());
    }
}
