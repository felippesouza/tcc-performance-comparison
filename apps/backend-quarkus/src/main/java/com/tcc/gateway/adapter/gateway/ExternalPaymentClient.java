package com.tcc.gateway.adapter.gateway;

import io.quarkus.runtime.annotations.RegisterForReflection;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.core.MediaType;
import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;

@RegisterRestClient(configKey = "external-api")
@Path("/process-payment")
public interface ExternalPaymentClient {

    @POST
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    ExternalPaymentResponse process(ExternalPaymentRequest request);

    @RegisterForReflection
    record ExternalPaymentRequest(String paymentId, java.math.BigDecimal amount, String cardNumber) {}

    @RegisterForReflection
    record ExternalPaymentResponse(String externalId, boolean approved) {}
}
