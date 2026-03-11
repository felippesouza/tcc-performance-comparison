package com.tcc.gateway.adapter.controller.dto;

import io.quarkus.runtime.annotations.RegisterForReflection;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;

@RegisterForReflection
public record PaymentRequest(
    @NotNull @DecimalMin("0.01") BigDecimal amount,
    @NotNull @Size(min = 13, max = 19) String cardNumber
) {}
