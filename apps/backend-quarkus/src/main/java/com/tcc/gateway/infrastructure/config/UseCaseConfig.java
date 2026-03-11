package com.tcc.gateway.infrastructure.config;

import com.tcc.gateway.adapter.gateway.JpaPaymentRepository;
import com.tcc.gateway.adapter.gateway.HttpExternalGateway;
import com.tcc.gateway.usecase.ProcessPaymentInteractor;
import com.tcc.gateway.usecase.ProcessPaymentUseCase;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.inject.Produces;
import jakarta.inject.Inject;

@ApplicationScoped
public class UseCaseConfig {

    @Inject
    JpaPaymentRepository repository;

    @Inject
    HttpExternalGateway externalGateway;

    @Produces
    @ApplicationScoped
    public ProcessPaymentUseCase processPaymentUseCase() {
        return new ProcessPaymentInteractor(repository, externalGateway);
    }
}
