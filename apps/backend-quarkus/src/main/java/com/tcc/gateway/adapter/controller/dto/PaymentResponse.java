package com.tcc.gateway.adapter.controller.dto;

import io.quarkus.runtime.annotations.RegisterForReflection;

@RegisterForReflection
public record PaymentResponse(String id, String status, String externalId) {}
