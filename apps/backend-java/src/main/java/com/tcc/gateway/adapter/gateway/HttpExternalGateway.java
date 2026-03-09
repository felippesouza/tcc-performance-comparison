package com.tcc.gateway.adapter.gateway;

import com.tcc.gateway.domain.ExternalGateway;
import com.tcc.gateway.domain.Payment;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class HttpExternalGateway implements ExternalGateway {

    private final RestClient restClient;
    private final String apiPath;

    public HttpExternalGateway(
            RestClient.Builder restClientBuilder, 
            @Value("${external.api.base-url}") String baseUrl,
            @Value("${external.api.path}") String apiPath) {
        
        this.restClient = restClientBuilder.baseUrl(baseUrl).build();
        this.apiPath = apiPath;
    }

    @Override
    public ExternalGateway.PaymentResponse process(Payment payment) {
        // Chamada síncrona que será gerenciada pelas Virtual Threads
        return restClient.post()
            .uri(apiPath)
            .body(payment)
            .retrieve()
            .body(ExternalGateway.PaymentResponse.class);
    }
}
