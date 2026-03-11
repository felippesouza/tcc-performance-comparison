package com.tcc.gateway.adapter.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tcc.gateway.adapter.cache.IdempotencyCache;
import com.tcc.gateway.adapter.controller.dto.PaymentRequest;
import com.tcc.gateway.adapter.controller.dto.PaymentResponse;
import com.tcc.gateway.adapter.mapper.PaymentMapper;
import com.tcc.gateway.domain.Payment;
import com.tcc.gateway.usecase.ProcessPaymentUseCase;
import jakarta.inject.Inject;
import jakarta.validation.Valid;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.HeaderParam;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.jboss.logging.Logger;

@Path("/payments")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class PaymentController {

    private static final Logger LOG = Logger.getLogger(PaymentController.class);

    @Inject
    ProcessPaymentUseCase useCase;

    @Inject
    PaymentMapper mapper;

    @Inject
    IdempotencyCache idempotencyCache;

    @Inject
    ObjectMapper objectMapper;

    @POST
    public Response create(
        @HeaderParam("X-Idempotency-Key") String idempotencyKey,
        @Valid PaymentRequest request
    ) throws Exception {
        // Idempotency check
        if (idempotencyKey != null && !idempotencyKey.isBlank()) {
            var cached = idempotencyCache.get(idempotencyKey);
            if (cached.isPresent()) {
                LOG.debugf("Idempotency hit for key: %s", idempotencyKey);
                PaymentResponse cachedResponse = objectMapper.readValue(cached.get(), PaymentResponse.class);
                return Response.status(Response.Status.CREATED).entity(cachedResponse).build();
            }
        }

        Payment domain = mapper.toDomain(request);
        Payment result = useCase.execute(domain);
        PaymentResponse response = mapper.toResponse(result);

        // Store in cache
        if (idempotencyKey != null && !idempotencyKey.isBlank()) {
            try {
                idempotencyCache.put(idempotencyKey, objectMapper.writeValueAsString(response));
            } catch (Exception e) {
                LOG.warnf("Failed to cache idempotency response: %s", e.getMessage());
            }
        }

        return Response.status(Response.Status.CREATED).entity(response).build();
    }
}
